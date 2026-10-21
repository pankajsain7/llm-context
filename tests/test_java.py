from types import SimpleNamespace

from conftest import FOO
from jitctx import java
from jitctx.java import enclosing_context, enclosing_lines, first_code_line, split_lines


def test_split_lines_matches_git_numbering():
    assert split_lines("a\r\nb\x0cc\nd\n") == ["a", "b\x0cc", "d"]  # form feed is not a line break for Git
    assert split_lines("") == []
    assert split_lines("x") == ["x"]


def test_first_code_line_is_the_package_line():
    assert first_code_line(split_lines(FOO)) == 2
    assert first_code_line(["class A {}"]) == 1


def test_default_package_file_still_loses_its_license_header():
    assert first_code_line(["/*", " * Licensed ...", " */", "", "// note", "import a.B;", "class A {}"]) == 6
    assert first_code_line(["/* one line */", "class A {}"]) == 2
    assert first_code_line(["// only comments"]) == 1


def test_enclosing_method():
    assert enclosing_lines(FOO, {16}) == set(range(14, 19))


def test_enclosing_constructor_static_and_instance_initializers():
    assert enclosing_lines(FOO, {11}) == set(range(10, 13))
    assert enclosing_lines(FOO, {21}) == set(range(20, 23))
    assert enclosing_lines(FOO, {24}) == {24}


def test_innermost_method_of_an_anonymous_class():
    assert enclosing_lines(FOO, {29}) == set(range(28, 31))


def test_change_outside_methods_gives_class_header_and_fields():
    assert enclosing_lines(FOO, {7}) == {6, 7, 8}


def test_change_outside_any_type_gives_nothing():
    assert enclosing_lines(FOO, {4}) == set()


def test_parser_recovery_is_not_reported_as_a_reliable_enclosing_method():
    result = enclosing_context(FOO.replace("count += y;", "count += @;"), {16})
    assert result.status == "recovered_error" and result.lines == set()
    assert result.error_nodes + result.missing_nodes > 0


def test_missing_nodes_also_trigger_the_fallback():
    result = enclosing_context("class A { int value }", {1})
    assert result.status == "recovered_error" and result.lines == set()
    assert result.missing_nodes > 0


def test_parser_exception_is_categorized(monkeypatch):
    def fail(_):
        raise RuntimeError("synthetic parser failure")

    monkeypatch.setattr(java, "_PARSER", SimpleNamespace(parse=fail))
    result = enclosing_context(FOO, {16})
    assert result.status == "parse_exception" and result.lines == set()
    assert result.error == "RuntimeError: synthetic parser failure"
