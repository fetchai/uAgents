import unittest

from uagents import Model


class TestModelDigest(unittest.TestCase):
    def test_calculate_digest_backcompat(self):
        """
        Test that the digest calculation is consistent with the result from
        previous versions to ensure backwards compatibility.
        """

        class SuperImportantCheck(Model):
            """Plus random docstring"""

            check: bool
            message: str
            counter: int

        target_digest = (
            "model:21e34819ee8106722968c39fdafc104bab0866f1c73c71fd4d2475be285605e9"
        )

        result = Model.build_schema_digest(SuperImportantCheck)

        self.assertEqual(result, target_digest, "Digest mismatch")


if __name__ == "__main__":
    unittest.main()
