import unittest
from enum import Enum
from typing import List, Literal, Optional

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

        # target_digest = (
        #     "model:21e34819ee8106722968c39fdafc104bab0866f1c73c71fd4d2475be285605e9"
        # )  # old V1 digest
        target_digest = (
            "model:fd73f6b4c36014cbdcc22a6b95b7634f8291c3a7eb48c66e4f22ae2180c10cd4"
        )

        result = Model.build_schema_digest(SuperImportantCheck)

        self.assertEqual(result, target_digest, "Digest mismatch")

    def test_calculate_nested_digest_backcompat(self):
        """
        Test the digest calculation of nested models.
        """

        class UAgentResponseType(Enum):
            FINAL = "final"
            ERROR = "error"
            VALIDATION_ERROR = "validation_error"
            SELECT_FROM_OPTIONS = "select_from_options"
            FINAL_OPTIONS = "final_options"

        class KeyValue(Model):
            key: str
            value: str

        class UAgentResponse(Model):
            version: Literal["v1"] = "v1"
            type: UAgentResponseType
            request_id: Optional[str]
            agent_address: Optional[str]
            message: Optional[str]
            options: Optional[List[KeyValue]]
            verbose_message: Optional[str]
            verbose_options: Optional[List[KeyValue]]

        # target_digest = (
        #     "model:cf0d1367c5f9ed8a269de559b2fbca4b653693bb8315d47eda146946a168200e"
        # )  # old V1 digest
        target_digest = (
            "model:c8244f673a8abae66e10ed807a4a37c5647f80fd954f5bdfa0a2eb1c8c3f6ab4"
        )

        result = Model.build_schema_digest(UAgentResponse)

        self.assertEqual(result, target_digest, "Digest mismatch")


if __name__ == "__main__":
    unittest.main()
