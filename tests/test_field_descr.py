import unittest
from pydantic import Field


from uagents import Model, Protocol


protocol_no_descriptions = Protocol(name="field descriptions", version="1.1.1")
protocol_with_descriptions = Protocol(name="field descriptions", version="1.1.1")


class TestFieldDescr(unittest.TestCase):
    def setUp(self) -> None:
        self.protocol_no_descr = protocol_no_descriptions
        self.protocol_with_descr = protocol_with_descriptions
        return super().setUp()

    def test_field_description(self):
        class Message(Model):
            message: str = Field(description="message field description")

        Model.build_schema_digest(Message)

        message_field_info = Message.__fields__["message"].field_info
        self.assertTrue(message_field_info is not None)
        self.assertTrue(
            message_field_info.description is not None
            and message_field_info.description == "message field description"
        )

    def test_model_digest(self):
        class Message(Model):
            message: str

        model_digest_no_descr = Model.build_schema_digest(Message)

        class Message(Model):
            message: str = Field(description="message field description")

        model_digest_with_descr = Model.build_schema_digest(Message)

        self.assertEqual(model_digest_no_descr, model_digest_with_descr)

    def test_proto_digest(self):
        class Message(Model):
            message: str

        @self.protocol_no_descr.on_query(Message)
        def _(_ctx, _sender, _msg):
            pass

        proto_digest_no_descr = self.protocol_no_descr.digest

        class Message(Model):
            message: str = Field(description="message field description")

        @self.protocol_with_descr.on_query(Message)
        def _(_ctx, _sender, _msg):
            pass

        proto_digest_with_descr = self.protocol_with_descr.digest

        self.assertEqual(len(self.protocol_no_descr.models), 1)
        self.assertEqual(len(self.protocol_with_descr.models), 1)
        model_digest_no_descr = next(iter(self.protocol_no_descr.models))
        model_digest_with_descr = next(iter(self.protocol_with_descr.models))
        self.assertEqual(model_digest_no_descr, model_digest_with_descr)
        self.assertEqual(proto_digest_no_descr, proto_digest_with_descr)


if __name__ == "__main__":
    unittest.main()
