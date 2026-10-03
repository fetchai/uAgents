# Dialogue timeout negotiation experiment

This standalone simulation explores the peer-synchronization part of
[fetchai/uAgents #413](https://github.com/fetchai/uAgents/issues/413).
It is not integrated with uAgents and does not change PR #942. No network,
blockchain transactions, dependencies, or real agents are required.

## Draft status and review material

This is a design-review draft, not a merge-ready production fix. Maintainers
have not approved the wire protocol and compatibility choices, and the model
has not been integrated into real uAgents or exercised over their transports.
Issue #413 must remain open for the peer-synchronization work.

- [Test inventory and validation results](TESTING.md): every executed simulation
  test, reproduction commands, limitations, and separate evidence from #942.
- [Real-peer integration requirements](INTEGRATION.md): implementation decisions,
  missing tests, and criteria for a production implementation.

## Relationship to the existing fix

Issue #413 describes two problems: local expiry is not enforced by the dialogue
engine, and peers do not agree on their timeout policy.

[PR #942](https://github.com/fetchai/uAgents/pull/942) implements the first part:
it checks local expiry before incoming handlers and handler-context sends,
removes expired persisted sessions on restart, and clears history and state
during cleanup. That change was validated with 119 passing tests at submission.
It does not synchronize peer deadlines.

This proposal covers the second part with an independent executable model.
It contains no production runtime changes and does not incorporate #942's code.
The proposed lease protocol is not an applied production fix and does not close
#413. The two-agent tests below use simulated peers, not real uAgents instances.

## Run

From this directory, using Python 3.10 or newer:

```powershell
python -m unittest -v
python lease_simulation.py
```

## Proposed semantics

Use an opt-in, versioned control protocol for finite renewable session leases.
This is a candidate design, not a negotiated standard or a production fix.

1. The initiator sends an offer containing a fresh session ID, version, sequence
   zero, and its maximum lease duration. It records its local send time.
2. The responder selects the smaller positive duration of the two preferences,
   records a local deadline, and acknowledges the duration and sequence.
3. The initiator accepts a matching acknowledgment only while the conservative
   deadline computed from its original send time is still in the future.
4. The initiator can request renewal before its acknowledged lease expires.
   Only one request is outstanding. Both sides retain the chosen duration.
   The responder must still be active; the initiator must receive the reply
   before both its old deadline and its proposed new deadline.
5. Duplicate requests return the cached acknowledgment without extending the
   deadline again. Unrelated sessions and stale acknowledgment sequences are
   ignored. A late message cannot revive an expired lease.

The virtual scheduler controls delivery delay and acknowledgment loss. Each
peer has a separate clock with its own offset and constant rate. The scheduler's
global time is for simulation only; peers do not exchange or rely on it.

## What the timing rule guarantees

Let the agreed duration be L and the shared maximum fractional clock drift be d.
The initiator's local deadline is `request_send_time + L * (1-d)`; the responder's
is `request_receive_time + L * (1+d)`. Clock offsets can be arbitrary.

Assuming honest peers, nonnegative network delay, no clock jumps, clock rates
within `[1-d, 1+d]`, and no restart or loss of responder state, an acknowledged
initiator lease ends no later in real time than the corresponding responder
lease. The initiator's longest real interval is L; the responder's shortest
real interval is L, beginning no earlier than request delivery.

The tests exercise all nine endpoint/nominal clock-rate combinations at three
network delays (27 cases within one test). The default 1% drift margin is an
illustrative simulation parameter, not a recommended production setting.

This does **not** promise simultaneous expiry, mutual knowledge of acceptance,
or successful delivery of an application message sent just before expiry. A
responder may retain state longer after a lost acknowledgment. A crash can
invalidate a responder's state before the initiator learns about it. Explicit
tests preserve these limitations rather than hiding them.

## Restart and legacy behavior

`checkpoint()` serializes preferences and previously used session IDs to JSON.
`restore()` reconstructs a peer without reusing any process-local lease deadline.
Both peers must negotiate a fresh session after restart. Old-session offers and
renewals are rejected. The tests perform a JSON round trip and fresh negotiation.
Production requires durable, atomic recording of session IDs before acceptance;
this in-memory prototype does not simulate disk failure or atomicity.

A protocol-aware peer that does not support this version explicitly refuses.
A silent older peer never activates the initiator's lease. There is no automatic
fallback claiming synchronization. Production needs a bounded handshake wait
with a user-visible failure and an explicit choice to use legacy local timeouts.

## Integration proposal for maintainers

- Introduce distinct versioned offer/acknowledgment/renewal control models and
  capability detection. Bind them to authenticated sender, peer, and session.
  The simulator assumes an authenticated, correctly routed two-peer channel;
  it does not implement cryptographic verification or adversarial input validation.
- Keep legacy dialogue models and digests unchanged by default. A new opt-in
  protocol would have its own digest. Do not add fields to existing application
  messages without a migration decision.
- Enforce the negotiated lease on both application send and receive paths,
  reusing the local expiry guard concept from PR #942. This experiment models
  control messages only; it does not dispatch application messages.
- Decide how activity requests renewal. The prototype uses explicit renewals,
  not independent idle resets on each message. Renewal timing, retry budgets,
  and possible piggybacking need design and integration tests.
- Define errors for expired/unknown sessions and transport failures. Never
  silently reopen an old session. Do not automatically restart a dialogue whose
  application side effects might already have occurred.
- Decide whether fresh-session recovery is acceptable. Seamless resume would
  require a separate authenticated recovery exchange and durable state design.
- Add timeout-input validation (including nonfinite values), negotiated drift
  assumptions, bounded session replay records and ACK caches, overload limits,
  and crash/persistence fault tests before production use.
- Decide unlimited-timeout semantics explicitly. This prototype rejects zero
  and negative preferences instead of changing uAgents' existing zero behavior.

## Result

The experiment supplies a concrete, testable negotiation policy and exposes its
failure cases. It is evidence for a design discussion, not grounds to close #413.
Maintainer agreement on the control protocol and compatibility/recovery choices
should precede a production integration PR.

## Validation and acceptance gates

The standalone suite contains 16 tests, including a 27-case clock-rate/delay
matrix. It checks negotiation, successful renewal, lost and late acknowledgments,
duplicate requests, stale/wrong-session responses, expiry, JSON restart recovery,
and unsupported or silent peers. It also verifies the expected disagreements
after acknowledgment loss and a remote restart. All tests are deterministic and
use virtual time; there are no sleeps or live network calls.

Before this can become a runtime PR:

1. Agree on lease versus idle-timeout semantics, control-message schemas,
   initiator authority, drift assumptions, and legacy/unlimited-timeout behavior.
2. Integrate authenticated control messages and application send/receive guards
   into two real uAgents, with versioned capability negotiation.
3. Test both local dispatch and serialized transport with delayed, dropped,
   duplicated and reordered control/application messages, including transport
   failures, differing preferences, and mixed-version peers.
4. Test process restart and durable storage failure; decide whether a fresh
   dialogue is acceptable or implement an explicit recovery protocol.
5. Define retry/resource limits and validate malformed/untrusted inputs. Run
   the relevant context/protocol tests, full suite, and repository checks.

The open design questions above are the review request for this draft. Passing
the simulation is not evidence that these integration gates have been met.
