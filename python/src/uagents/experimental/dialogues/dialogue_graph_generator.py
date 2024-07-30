import graphviz
from uagents.experimental.dialogues import Dialogue


def generate_graph(dialogue: Dialogue):
    """Create a graphviz diagram of the Dialogue's state graph to visually verify it

    Note requires local installation of Graphviz,
    e.g. `brew install graphviz` on macOS"""

    dot = graphviz.Digraph(comment=dialogue.name)

    for node in dialogue.nodes:
        dot.node(node.name, str(node.name))

    for edge in dialogue.edges:
        dot.edge(str(edge.parent.name), str(edge.child.name), str(edge.name))

    # the dot source gives a nice text based summary of the edges and nodes
    print(dot.source)

    # rendering the graph creates a pdf file in the current directory and
    # opens it automatically. If you omit the `view=True` parameter, it
    # just creates the file without auto opening it.
    dot.render(f"{dialogue.name.lower()}.gv", view=True)
