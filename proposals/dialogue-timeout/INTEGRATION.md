# Why this is a draft and what remains

## Current situation

Issue #413 combines local expiry enforcement with unsynchronized peer timeouts.
PR #942 addresses local enforcement, cleanup, and restart behavior. This draft
provides an independent proposal and executable model for the remaining peer
negotiation problem. No production peer-synchronization fix is applied here.

It remains a draft because the protocol choices need maintainer review and the
simulation bypasses real uAgents contexts, identity validation, serialization,
transport, scheduling, and durable storage. Those layers can invalidate assumptions
that hold in an in-memory model. Simulation success alone cannot establish that
real application messages are blocked or accepted at the correct time.

The proposed guarantee is deliberately limited: within the stated drift and
state-retention assumptions, an acknowledged initiator lease expires no later
than the corresponding responder lease. It does not guarantee simultaneous expiry,
delivery near a deadline, or instantaneous detection of a remote crash.

## Decisions requiring review

- Choose explicit renewable leases versus the existing activity-based idle
  timeout, and determine which application activity should request renewal.
- Agree on initiator authority, control-message schemas, protocol version/digest,
  authenticated peer/session binding, and capability negotiation.
- Define unsupported and silent peer behavior, unlimited timeout semantics,
  drift bounds, handshake deadlines, and retry limits.
- Decide whether fresh-session recovery is acceptable after restart. Seamless
  recovery requires additional durable state and an authenticated recovery exchange.
- Define replay-record retention and cache bounds, expiry errors, and handling
  of application side effects when a connection or session is lost.

## Real-peer implementation and acceptance tests

| Required work | Acceptance evidence |
| --- | --- |
| Wire models and identity checks | Two real uAgents negotiate the same policy using serialized, authenticated control messages; mismatched peer/session/version and malformed inputs are rejected. |
| Runtime guards | Both application send and receive paths enforce the negotiated lease, including handlers waiting across expiry and messages delivered near or after expiry. |
| Transport coverage | Demonstrate both local dispatch and separate-process transport, with delays, dropped acknowledgments, duplicates, reordered messages, and endpoint failures. |
| Compatibility | Exercise a real legacy peer and an upgraded peer; show an explicit refusal or deliberately selected legacy mode, without claiming synchronized fallback. |
| Clock behavior | Test supported drift assumptions and define behavior for unsupported jumps or suspend/resume conditions. |
| Recovery | Restart each real process independently and together; test replayed traffic, durable checkpoint loading, interrupted writes, and fresh-session recovery. |
| Operational bounds | Verify bounded retry/caches, invalid timeout handling, concurrent sessions, cancellation, and application errors without accidental session revival. |
| Regression coverage | Run relevant context/protocol tests and the full suite on the integration branch; retain the deterministic model tests and document supported environments. |

These are pending criteria, not completed tests. The exact implementation may
change following maintainer review.

## How to advance the work

1. Review this draft's model and limitations and agree on the protocol decisions.
2. Decide whether to merge the proposal as documentation only or keep it as a
   reference for a separate implementation PR. A documentation merge would not
   resolve #413 or deliver synchronization to users.
3. Implement and run the real-peer acceptance tests above on a separate runtime
   branch, coordinating with the local guards in #942.
4. Publish implementation results and compatibility notes before representing the
   synchronization work as production-ready or asking to close #413.
