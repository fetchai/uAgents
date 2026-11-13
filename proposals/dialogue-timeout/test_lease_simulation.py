import unittest

from lease_simulation import Message, Peer, Simulation


class LeaseTests(unittest.TestCase):
    def pair(self, **kwargs):
        sim = Simulation()
        alice = Peer("Alice", 60, **kwargs)
        bob = Peer("Bob", 30, offset=-5000)
        sim.send(alice, bob, alice.start("session", 0), delay=1, reply_delay=1)
        sim.advance(2)
        return sim, alice, bob

    def test_different_preferences_and_offsets(self):
        _, alice, bob = self.pair(offset=90000)
        self.assertEqual(alice.duration, 30)
        self.assertEqual(bob.duration, 30)
        self.assertTrue(alice.active(2) and bob.active(2))
        self.assertFalse(alice.active(30))

    def test_successful_renewal(self):
        sim, alice, bob = self.pair()
        sim.advance(10)
        sim.send(alice, bob, alice.renew(10), delay=1, reply_delay=1)
        sim.advance(12)
        self.assertTrue(alice.active(35) and bob.active(35))

    def test_lost_ack_does_not_extend_initiator(self):
        sim, alice, bob = self.pair()
        old = alice.deadline
        sim.advance(10)
        sim.send(alice, bob, alice.renew(10), delay=1, drop_reply=True)
        sim.advance(30)
        self.assertEqual(alice.deadline, old)
        self.assertFalse(alice.active(30))
        self.assertTrue(bob.active(30))  # Deliberate, documented disagreement.

    def test_delayed_initial_ack_is_rejected(self):
        sim = Simulation()
        alice, bob = Peer("a", 10), Peer("b", 10)
        sim.send(alice, bob, alice.start("s", 0), reply_delay=20)
        sim.advance(20)
        self.assertFalse(alice.active(20))
        self.assertIn("ack rejected: late", alice.events)

    def test_late_renewal_ack_cannot_revive_expired_initiator(self):
        sim, alice, bob = self.pair()
        sim.advance(20)
        sim.send(alice, bob, alice.renew(20), reply_delay=11)
        sim.advance(31)
        self.assertFalse(alice.active(31))
        self.assertIn("ack rejected: late", alice.events)

    def test_expired_responder_rejects_renewal(self):
        sim, alice, bob = self.pair()
        sim.advance(20)
        sim.send(alice, bob, alice.renew(20), delay=20)
        sim.advance(40)
        self.assertIn("renewal rejected: expired", bob.events)

    def test_duplicate_renewal_does_not_extend_deadline(self):
        sim, alice, bob = self.pair()
        msg = alice.renew(10)
        bob.receive(msg, 11)
        deadline = bob.deadline
        bob.receive(msg, 20)
        self.assertEqual(bob.deadline, deadline)

    def test_duplicate_offer_does_not_extend_deadline(self):
        _, _, bob = self.pair()
        deadline = bob.deadline
        bob.receive(Message("offer", "session", 0, 60), 10)
        self.assertEqual(bob.deadline, deadline)

    def test_restart_rejects_replayed_session(self):
        _, alice, bob = self.pair()
        alice.restart()
        bob.restart()
        self.assertFalse(alice.active(3) or bob.active(3))
        self.assertIsNone(bob.receive(Message("offer", "session", 0, 60), 3))
        self.assertIsNone(bob.receive(Message("renew", "session", 1, 30), 3))

    def test_stale_ack_does_not_acknowledge_new_renewal(self):
        _, alice, _ = self.pair()
        alice.renew(10)
        alice.receive(Message("ack", "session", 0, 30), 11)
        self.assertEqual(alice.pending[0], 1)

    def test_serialized_restart_requires_and_allows_fresh_negotiation(self):
        sim, alice, bob = self.pair()
        alice = Peer.restore(alice.checkpoint())
        bob = Peer.restore(bob.checkpoint())
        self.assertFalse(alice.active(2) or bob.active(2))
        self.assertIsNone(bob.receive(Message("offer", "session", 0, 60), 2))
        sim.send(alice, bob, alice.start("new-session", 2), delay=1, reply_delay=1)
        sim.advance(4)
        self.assertTrue(alice.active(4) and bob.active(4))

    def test_remote_restart_is_not_instantly_known_by_initiator(self):
        _, alice, bob = self.pair()
        bob.restart()
        self.assertTrue(alice.active(3))
        self.assertFalse(bob.active(3))
        # A timeout protocol cannot guarantee knowledge of a remote crash.

    def test_wrong_session_ack_does_not_activate_peer(self):
        alice = Peer("a", 30)
        alice.start("expected", 0)
        alice.receive(Message("ack", "wrong", 0, 30), 1)
        self.assertFalse(alice.active(1))

    def test_unsupported_peer_explicitly_refuses(self):
        sim = Simulation()
        alice, bob = Peer("a", 30), Peer("b", 30, supported=False)
        sim.send(alice, bob, alice.start("s", 0))
        sim.advance(1)
        self.assertFalse(alice.active(1))
        self.assertIn("negotiation refused: unsupported peer", alice.events)

    def test_silent_old_peer_never_activates_initiator(self):
        alice = Peer("a", 30)
        alice.start("s", 0)
        self.assertFalse(alice.active(100))

    def test_conservative_deadlines_with_bounded_clock_drift(self):
        for a_rate in (0.99, 1, 1.01):
            for b_rate in (0.99, 1, 1.01):
                for delay in (0, 1, 5):
                    with self.subTest(a=a_rate, b=b_rate, delay=delay):
                        sim = Simulation()
                        a = Peer("a", 30, offset=1000, rate=a_rate)
                        b = Peer("b", 30, offset=-1000, rate=b_rate)
                        sim.send(a, b, a.start("s", 0), delay=delay, reply_delay=delay)
                        sim.advance(2 * delay)
                        a_expiry = (a.deadline - a.offset) / a.rate
                        b_expiry = (b.deadline - b.offset) / b.rate
                        self.assertLessEqual(a_expiry, b_expiry + 1e-9)


if __name__ == "__main__":
    unittest.main()
