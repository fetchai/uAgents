# Test inventory and validation

## Scope and result

The prototype suite passes all 16 unittest methods. One method additionally
exercises 27 clock-rate/delay combinations; these are subcases, not 27 additional
top-level tests. Tests run deterministically in memory with virtual time.

These are simulated peer tests. They do not start real uAgents, exchange signed
envelopes, use local dispatch or HTTP, or test durable filesystem recovery.
Passing them supports the proposed model only, not production readiness.

## Complete executed test inventory

Names below are methods in `test_lease_simulation.py::LeaseTests`.

| Test method | Behavior checked |
| --- | --- |
| `test_different_preferences_and_offsets` | Preferences of 60 and 30 seconds select 30 despite different clock offsets. |
| `test_successful_renewal` | An acknowledged renewal extends both peers' active leases. |
| `test_lost_ack_does_not_extend_initiator` | A lost acknowledgment leaves the initiator's old deadline unchanged while the responder may retain a longer lease. |
| `test_delayed_initial_ack_is_rejected` | An initial acknowledgment arriving after the conservative deadline cannot activate the initiator. |
| `test_late_renewal_ack_cannot_revive_expired_initiator` | Renewal acknowledgment after the old deadline does not revive the initiator. |
| `test_expired_responder_rejects_renewal` | A renewal delivered after responder expiry is rejected. |
| `test_duplicate_renewal_does_not_extend_deadline` | Replaying a renewal does not extend the responder deadline twice. |
| `test_duplicate_offer_does_not_extend_deadline` | Replaying an initial offer does not reset the lease. |
| `test_restart_rejects_replayed_session` | Simulated restart clears leases and rejects old-session offers and renewals. |
| `test_stale_ack_does_not_acknowledge_new_renewal` | An old acknowledgment does not satisfy a pending newer renewal. |
| `test_serialized_restart_requires_and_allows_fresh_negotiation` | JSON checkpoint/restore rejects an old session and permits negotiation of a fresh session. |
| `test_remote_restart_is_not_instantly_known_by_initiator` | Explicitly demonstrates the limitation that the initiator cannot instantly detect responder restart. |
| `test_wrong_session_ack_does_not_activate_peer` | An acknowledgment for another session does not activate the initiator. |
| `test_unsupported_peer_explicitly_refuses` | A simulated protocol-aware unsupported peer refuses negotiation. |
| `test_silent_old_peer_never_activates_initiator` | Absence of a reply never activates the initiator; this does not test a real legacy agent or a bounded retry loop. |
| `test_conservative_deadlines_with_bounded_clock_drift` | Initiator real-time expiry is no later than responder expiry for 3 initiator rates x 3 responder rates x 3 delays, within the model's assumptions. |

## Commands and other checks

From the repository root with Python and Ruff available:

```shell
python -m unittest discover -s proposals/dialogue-timeout -v
python proposals/dialogue-timeout/lease_simulation.py
ruff check proposals/dialogue-timeout
ruff format --check proposals/dialogue-timeout
git diff --check
```

The unittest suite, demo, Ruff lint, Ruff formatting, and whitespace checks passed.
The demo negotiates 30 seconds from preferences of 60 and 30 seconds, then drops
a renewal acknowledgment. At virtual t=30 the initiator is inactive while the
responder is still active. This disagreement is expected, not a claim of exact
simultaneous expiry. The validation environment is Windows with the repository's
existing Python virtual environment; no cross-platform test claim is made.

## Separate evidence for the local fix

PR #942 was validated separately with 119 passing pytest tests (including 12
dialogue tests), targeted Ruff checks, and whitespace checks. Four selected
regression cases failed when run against the prior upstream dialogue implementation.
Its local test cases cover three cleanup frequencies, active/expired restart,
unlimited and empty sessions, repeatable cleanup, expired inbound rejection,
late handler sends during cleanup, active/unlimited sends, expired raw sends,
expired-session reuse, and normal reply/history/deadline behavior.

That result belongs to #942, not this independent prototype branch. The production
suite was not rerun for the documentation-only update, and its passing result does
not validate peer synchronization. GitHub CI results are separate from these local
checks and are not asserted here.

## Not yet tested

Real two-uAgents integration; signed control envelopes; local and remote message
dispatch; application messages crossing deadlines; mixed-version real peers;
OS process crashes and atomic persistence; adversarial wire input; clock jumps;
multi-peer concurrency; resource exhaustion; or production retry budgets.
See [integration requirements](INTEGRATION.md) for the acceptance plan.
