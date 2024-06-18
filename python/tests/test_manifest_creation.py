import unittest

from pydantic import Field
from uagents import Context, Model, Protocol
from uagents.experimental.dialogues import Dialogue, Edge, Node

FIELD_DESCRIPTION = "This description will show up in the schemas properties"
DOCSTRING = """This docstring will show up as description in the schema"""
NODE_METADATA = "This description will show up as node attribute"
EDGE_METADATA = "This description will show up as edge attribute"


class MsgWrapperNormal:
    class Ping(Model):
        field: str
        number: int


class MsgWrapperField:
    class Ping(Model):
        field: str = Field(description=FIELD_DESCRIPTION)
        number: int


class MsgWrapperDocstring:
    class Ping(Model):
        """This docstring will show up as description in the schema"""

        field: str
        number: int


class MsgWrapperReverse:
    class Ping(Model):
        number: int
        field: str


class Pong(Model):
    name: str
    notdescription: bool


class DialogueWrapperA:
    class TestDialogue(Dialogue):
        node_1 = Node("first node", "First test node", True)
        node_2 = Node("second node", "Second test node")
        node_3 = Node("third node", "Third test node")

        edge_1 = Edge("first edge", "First test edge", node_1, node_2)
        edge_2 = Edge("second edge", "Second test edge", node_2, node_3)

        def __init__(self) -> None:
            super().__init__(
                name="TestDialogue",
                version="0.1.0",
                nodes=[self.node_1, self.node_2, self.node_3],
                edges=[self.edge_1, self.edge_2],
            )

        def edge_handler_1(self, model: type[Model]):
            return super()._on_state_transition(self.edge_1.name, model)

        def edge_handler_2(self, model: type[Model]):
            return super()._on_state_transition(self.edge_2.name, model)


class DialogueWrapperB:
    class TestDialogue(Dialogue):
        node_1 = Node(
            "first node",
            "First test node",
            True,
            metadata={"nodemetadata": NODE_METADATA},
        )
        node_2 = Node("second node", "Second test node with a different description")
        node_3 = Node("third node", "Third test node")

        edge_1 = Edge(
            "first edge",
            "First test edge",
            node_1,
            node_2,
            metadata={"edgemetadata": EDGE_METADATA},
        )
        edge_2 = Edge("second edge", "Second test edge", node_2, node_3)

        def __init__(self) -> None:
            super().__init__(
                name="TestDialogue",
                version="0.1.0",
                nodes=[self.node_1, self.node_2, self.node_3],
                edges=[self.edge_1, self.edge_2],
            )

        def edge_handler_1(self, model: type[Model]):
            return super()._on_state_transition(self.edge_1.name, model)

        def edge_handler_2(self, model: type[Model]):
            return super()._on_state_transition(self.edge_2.name, model)


class TestProtocolManifest(unittest.TestCase):
    def setUp(self) -> None:
        self.test_proto_1 = Protocol(name="ping", version="0.1.0")
        self.test_proto_2 = Protocol(name="ping", version="0.1.0")
        self.test_proto_3 = Protocol(name="ping", version="0.1.0")
        self.test_proto_4 = Protocol(name="ping", version="0.1.0")

        @self.test_proto_1.on_message(model=MsgWrapperNormal.Ping, replies=Pong)
        @self.test_proto_2.on_message(model=MsgWrapperField.Ping, replies=Pong)
        @self.test_proto_3.on_message(model=MsgWrapperDocstring.Ping, replies=Pong)
        @self.test_proto_4.on_message(model=MsgWrapperReverse.Ping, replies=Pong)
        async def _(_ctx, _sender, _msg):
            pass

    def test_manifest_equality(self):
        self.assertEqual(
            self.test_proto_1.manifest()["metadata"]["digest"],
            self.test_proto_2.manifest()["metadata"]["digest"],
        )
        self.assertEqual(
            self.test_proto_1.manifest()["metadata"]["digest"],
            self.test_proto_3.manifest()["metadata"]["digest"],
        )
        self.assertEqual(
            self.test_proto_1.manifest()["metadata"]["digest"],
            self.test_proto_4.manifest()["metadata"]["digest"],
        )

    def test_metadata(self):
        self.assertEqual(
            self.test_proto_2.manifest()["metadata"]["models"]["Ping"]["properties"][
                "field"
            ]["description"],
            FIELD_DESCRIPTION,
        )
        self.assertEqual(
            self.test_proto_3.manifest()["metadata"]["models"]["Ping"]["description"],
            DOCSTRING,
        )


# TODO add transition handlers incl model definitions
class TestDialogueManifest(unittest.TestCase):
    def setUp(self) -> None:
        self.dialogueA = DialogueWrapperA.TestDialogue()
        self.dialogueB = DialogueWrapperB.TestDialogue()

        @self.dialogueA.edge_handler_1(MsgWrapperNormal.Ping)
        @self.dialogueB.edge_handler_1(MsgWrapperDocstring.Ping)
        async def _1(_ctx: Context, _sender, _msg):
            pass

        @self.dialogueA.edge_handler_2(Pong)
        @self.dialogueB.edge_handler_2(Pong)
        async def _2(_ctx, _sender, _msg):
            pass

        return super().setUp()

    def test_dialogue_manifest(self):
        self.assertEqual(
            self.dialogueA.manifest()["metadata"]["digest"],
            self.dialogueB.manifest()["metadata"]["digest"],
        )

    def test_dialogue_metadata(self):
        self.assertEqual(
            self.dialogueB.manifest()["metadata"]["nodes"][0]["metadata"][
                "nodemetadata"
            ],
            NODE_METADATA,
        )
