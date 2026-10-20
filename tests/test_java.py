from conftest import FOO
from jitctx.java import enclosing_lines, first_code_line, split_lines


def test_split_lines_matches_git_numbering():
    assert split_lines("a\r\nb\x0cc\nd\n") == ["a", "b\x0cc", "d"]  # form feed is not a line break for Git
    assert split_lines("") == []
    assert split_lines("x") == ["x"]


def test_first_code_line_is_the_package_line():
    assert first_code_line(split_lines(FOO)) == 2
    assert first_code_line(["class A {}"]) == 1


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
