"""Java source helpers: Git-compatible line splitting, license-header stripping, enclosing declarations."""
import tree_sitter_java
from tree_sitter import Language, Node, Parser

_PARSER = Parser(Language(tree_sitter_java.language()))
CALLABLE = {"method_declaration", "constructor_declaration", "compact_constructor_declaration", "static_initializer"}
TYPE_DECL = {"class_declaration", "interface_declaration", "enum_declaration", "record_declaration",
             "annotation_type_declaration"}
BODY = {"class_body", "interface_body", "enum_body", "annotation_type_body", "enum_body_declarations"}
MEMBER_FIELDS = {"field_declaration", "constant_declaration", "enum_constant"}


def split_lines(text: str) -> list[str]:
    """Lines numbered as Git numbers them: split on LF only (not form feeds), CR removed."""
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return [line.removesuffix("\r") for line in lines]


def first_code_line(lines: list[str]) -> int:
    """1-based number of the `package` line, i.e. the first line kept after stripping the license header."""
    return next((i + 1 for i, line in enumerate(lines) if line.startswith("package ")), 1)


def _rows(node: Node) -> range:
    return range(node.start_point.row + 1, node.end_point.row + 2)


def _is_callable(node: Node, parent: Node) -> bool:
    # an instance initializer is a bare block directly inside a class body
    return node.type in CALLABLE or (node.type == "block" and parent.type == "class_body")


def _children(node: Node) -> list[Node]:
    # Node.children crashed (access violation) with tree-sitter 0.26 on Windows; child(i) does not
    return [node.child(i) for i in range(node.child_count)]


def _innermost(root: Node, line: int, accept) -> Node | None:
    found, node = None, root
    while True:
        child = next((c for c in _children(node) if c.start_point.row + 1 <= line <= c.end_point.row + 1), None)
        if child is None:
            return found
        if accept(child, node):
            found = child
        node = child


def _type_outline(decl: Node) -> set[int]:
    """Header lines of a type declaration (up to its body's opening line) plus its field declarations."""
    body = decl.child_by_field_name("body")
    lines = set(range(decl.start_point.row + 1, (body.start_point.row if body else decl.end_point.row) + 2))
    stack = [body] if body else []
    while stack:
        for c in _children(stack.pop()):
            if c.type in MEMBER_FIELDS:
                lines.update(_rows(c))
            elif c.type == "enum_body_declarations":
                stack.append(c)
    return lines


def enclosing_lines(source: str, anchors: set[int]) -> set[int]:
    """Lines of the innermost method, constructor, or initializer containing each anchor line; for anchors
    outside any of these, the enclosing type's header and field declarations (design §5.2)."""
    tree = _PARSER.parse(source.encode("utf-8"))
    # tree-sitter rows count LF only, consistent with split_lines
    out: set[int] = set()
    for line in sorted(anchors):
        if (node := _innermost(tree.root_node, line, _is_callable)) is not None:
            out.update(_rows(node))
        elif (decl := _innermost(tree.root_node, line, lambda n, _: n.type in TYPE_DECL)) is not None:
            out.update(_type_outline(decl))
    return out
