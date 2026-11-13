"""Deterministic, in-memory dialogue lease experiment. No network or SDK imports."""

import heapq
import json
from dataclasses import dataclass, field
from itertools import count


@dataclass(frozen=True)
class Message:
    kind: str
    session: str
    seq: int
    duration: float
    version: int = 1


@dataclass
class Peer:
    name: str
    cap: float
    offset: float = 0
    rate: float = 1
    drift_bound: float = 0.01
    supported: bool = True
    session: str | None = None
    role: str | None = None
    deadline: float | None = None
    duration: float | None = None
    pending: tuple[int, float] | None = None
    seq: int = 0
    seen: set[str] = field(default_factory=set)
    responses: dict[int, Message] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not 0 <= self.drift_bound < 1:
            raise ValueError("Invalid drift bound")
        if not 1 - self.drift_bound <= self.rate <= 1 + self.drift_bound:
            raise ValueError("Clock rate exceeds assumed drift bound")
        if self.cap <= 0:
            raise ValueError("Prototype requires a finite positive timeout")

    def clock(self, now):
        return self.offset + now * self.rate

    def active(self, now):
        return self.deadline is not None and self.clock(now) < self.deadline

    def start(self, session, now):
        if self.session is not None or session in self.seen:
            raise ValueError("Use a fresh peer/session for a new dialogue")
        self.session, self.role = session, "initiator"
        self.seen.add(session)
        self.pending = (0, self.clock(now))
        return Message("offer", session, 0, self.cap)

    def renew(self, now):
        if self.role != "initiator" or not self.active(now) or self.pending:
            raise ValueError(
                "Renewal requires an active initiator with no pending request"
            )
        self.seq += 1
        self.pending = (self.seq, self.clock(now))
        return Message("renew", self.session, self.seq, self.duration)

    def receive(self, msg, now):
        """Return an optional reply; transport identity/authentication is assumed."""
        if not self.supported or msg.version != 1:
            self.events.append("unsupported")
            return Message("unsupported", msg.session, msg.seq, 0)
        if msg.kind == "unsupported":
            if (
                msg.session != self.session
                or self.role != "initiator"
                or not self.pending
            ):
                return None
            self.events.append("negotiation refused: unsupported peer")
            self.pending = None
            self.deadline = None
            return None
        if msg.kind == "offer":
            if msg.session == self.session and self.role == "responder":
                # Retrying an offer must not move the lease's deadline.
                return self.responses.get(0) if self.active(now) else None
            if (
                self.session is not None
                or msg.session in self.seen
                or msg.duration <= 0
            ):
                return None
            self.session, self.role = msg.session, "responder"
            self.seen.add(msg.session)
            self.duration = min(msg.duration, self.cap)
            self.deadline = self.clock(now) + self.duration * (1 + self.drift_bound)
            reply = Message("ack", self.session, 0, self.duration)
            self.responses[0] = reply
            return reply
        if msg.session != self.session:
            return None
        if msg.kind == "renew" and self.role == "responder":
            if not self.active(now):
                self.events.append("renewal rejected: expired")
                return None
            if msg.seq in self.responses:
                return self.responses[msg.seq]
            if msg.seq != self.seq + 1 or msg.duration != self.duration:
                return None
            self.seq = msg.seq
            self.deadline = self.clock(now) + self.duration * (1 + self.drift_bound)
            reply = Message("ack", self.session, msg.seq, self.duration)
            self.responses[msg.seq] = reply
            return reply
        if msg.kind == "ack" and self.role == "initiator" and self.pending:
            seq, sent_at = self.pending
            if msg.seq != seq or not 0 < msg.duration <= self.cap:
                return None
            if self.duration is not None and msg.duration != self.duration:
                return None
            # An ACK must arrive before the conservative new deadline AND,
            # for renewal, before the old acknowledged lease expires.
            deadline = sent_at + msg.duration * (1 - self.drift_bound)
            if self.clock(now) >= deadline or (seq > 0 and not self.active(now)):
                self.events.append("ack rejected: late")
                self.pending = None
                return None
            self.duration, self.deadline = msg.duration, deadline
            self.pending = None
        return None

    def restart(self):
        """Discard process-local clock leases; retain durable replay protection.

        Production would persist the session ID before accepting the offer.
        This prototype deliberately requires renegotiation after restart.
        """
        self.deadline = None
        self.pending = None
        self.responses.clear()
        self.events.append("restart: session closed; fresh session required")

    def checkpoint(self):
        """Serialize only durable identity/configuration and retired session IDs."""
        return json.dumps(
            {
                "name": self.name,
                "cap": self.cap,
                "offset": self.offset,
                "rate": self.rate,
                "drift_bound": self.drift_bound,
                "supported": self.supported,
                "seen": sorted(self.seen),
            }
        )

    @classmethod
    def restore(cls, checkpoint):
        data = json.loads(checkpoint)
        data["seen"] = set(data["seen"])
        return cls(**data)


class Simulation:
    def __init__(self):
        self.now = 0.0
        self.queue = []
        self.order = count()

    def send(self, source, target, message, delay=0, reply_delay=0, drop_reply=False):
        if delay < 0 or reply_delay < 0:
            raise ValueError("Delays must be nonnegative")
        heapq.heappush(
            self.queue,
            (
                self.now + delay,
                next(self.order),
                source,
                target,
                message,
                reply_delay,
                drop_reply,
            ),
        )

    def advance(self, until):
        if until < self.now:
            raise ValueError("Simulation time cannot go backwards")
        while self.queue and self.queue[0][0] <= until:
            when, _, source, target, message, reply_delay, drop = heapq.heappop(
                self.queue
            )
            self.now = when
            reply = target.receive(message, when)
            if reply is not None and not drop:
                # Replies are delivered once, without generating reply loops.
                heapq.heappush(
                    self.queue,
                    (
                        when + reply_delay,
                        next(self.order),
                        target,
                        source,
                        reply,
                        0,
                        True,
                    ),
                )
        self.now = until


if __name__ == "__main__":
    sim = Simulation()
    alice = Peer("Alice", 60, offset=3600)
    bob = Peer("Bob", 30, offset=-7200)
    sim.send(alice, bob, alice.start("demo", 0), delay=2, reply_delay=2)
    sim.advance(4)
    print(f"Negotiated duration: {alice.duration}s (preferences: 60s and 30s)")
    print(f"At t=4s: Alice active={alice.active(4)}, Bob active={bob.active(4)}")
    sim.advance(10)
    sim.send(alice, bob, alice.renew(10), delay=1, drop_reply=True)
    sim.advance(30)
    print(
        f"Lost renewal ACK, t=30s: Alice active={alice.active(30)}, "
        f"Bob active={bob.active(30)}"
    )
    print("Alice stopped safely; exact simultaneous expiry is not guaranteed.")
