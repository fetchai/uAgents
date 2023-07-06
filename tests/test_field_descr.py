# pylint: disable=function-redefined
import unittest
from pydantic import Field
from uagents import Model, Protocol


protocol_no_descr = Protocol(name="test", version="1.1.1")
protocol_with_descr = Protocol(name="test", version="1.1.1")


def create_message_no_descr():
    class Message(Model):
        message: str

    return Message


def create_message_with_descr():
    class Message(Model):
        message: str = Field(description="message field description")

    return Message


def get_digests(protocol: Protocol):
    model_digest = next(iter(protocol.models))
    proto_digest = protocol.digest
    return (model_digest, proto_digest)


class TestFieldDescr(unittest.TestCase):
    def setUp(self) -> None:
        self.protocol_no_descr = protocol_no_descr
        self.protocol_with_descr = protocol_with_descr
        return super().setUp()

    def test_schema_json(self):
        class Message(Model):
            message: str
            id: str

        self.assertEqual(
            Message.schema_json(indent=None, sort_keys=True),
            Message.schema_json_no_descriptions(),
        )

        class Message(Model):
            message: str = Field(description="message field description")
            id: str = Field(description="id field description")

        self.assertNotEqual(
            Message.schema_json(indent=None, sort_keys=True),
            Message.schema_json_no_descriptions(),
        )

        class MessageArgs(Model):
            arg: str = Field(description="arg field description")

        class Message(Model):
            message: str = Field(description="message field description")
            id: str = Field(description="id field description")
            args: MessageArgs

        self.assertNotEqual(
            Message.schema_json(indent=None, sort_keys=True),
            Message.schema_json_no_descriptions(),
        )

    def test_model_digest(self):
        model_digest_no_descr = Model.build_schema_digest(create_message_no_descr())
        model_digest_with_descr = Model.build_schema_digest(create_message_with_descr())

        self.assertEqual(model_digest_no_descr, model_digest_with_descr)

    def test_protocol(self):
        @self.protocol_no_descr.on_message(create_message_no_descr())
        def _(_ctx, _sender, _msg):
            pass

        self.assertEqual(len(self.protocol_no_descr.models), 1)
        self.assertNotIn(
            "description",
            self.protocol_no_descr.manifest()["models"][0]["schema"]["properties"][
                "message"
            ],
        )
        (model_digest_no_descr, proto_digest_no_descr) = get_digests(
            self.protocol_no_descr
        )

        @self.protocol_with_descr.on_message(create_message_with_descr())
        def _(_ctx, _sender, _msg):
            pass

        self.assertEqual(len(self.protocol_with_descr.models), 1)
        self.assertEqual(
            self.protocol_with_descr.manifest()["models"][0]["schema"]["properties"][
                "message"
            ]["description"],
            "message field description",
        )
        (model_digest_with_descr, proto_digest_with_descr) = get_digests(
            self.protocol_with_descr
        )

        self.assertEqual(model_digest_no_descr, model_digest_with_descr)
        self.assertEqual(proto_digest_no_descr, proto_digest_with_descr)

    def test_compute_digest(self):
        protocol = Protocol(name="test", version="1.1.1")

        @protocol.on_message(create_message_with_descr())
        def _(_ctx, _sender, _msg):
            pass

        computed_digest = Protocol.compute_digest(protocol.manifest())
        self.assertEqual(protocol.digest, computed_digest)


if __name__ == "__main__":
    unittest.main()
