import random

import pytest

from jitctx.select import Window, fill, render_cross_file, windows
from jitctx.tokens import count_tokens


def numbered(n):
    return "\n".join(f"int v{i} = f{i}(x);" for i in range(1, n + 1))


@pytest.mark.parametrize("n", range(121))
def test_windows_cover_every_line(n):
    covered = set()
    for w in windows("A.java", numbered(n)):
        assert len(w.lines) <= 40
        covered.update(range(w.start, w.end + 1))
    assert covered == set(range(1, n + 1))


def test_windows_respect_the_token_bound_and_still_cover_everything():
    text = "package p;\n" + "\n".join(("x" * 300 + " ") * 4 if i % 7 == 0 else f"int a{i};" for i in range(200))
    ws = windows("A.java", text, max_tokens=500)
    covered = set()
    for w in ws:
        covered.update(range(w.start, w.end + 1))
        if not w.oversized:
            assert sum(count_tokens(line) + 1 for line in w.lines) <= 500
    assert covered == set(range(1, 202))


def test_a_single_huge_line_becomes_one_oversized_window():
    huge = " ".join(f"w{i}" for i in range(3000))
    ws = windows("A.java", f"package p;\n{huge}\nint z;", max_tokens=500)
    assert any(w.oversized and w.lines == (huge,) for w in ws)


def test_windows_strip_license_header_but_keep_line_numbers():
    (w,) = windows("A.java", "/* license */\n/* more */\npackage a;\nclass A {}")
    assert (w.start, w.end, w.lines[0]) == (3, 4, "package a;")


def one_line(path, line):
    return Window(path, 1, (line,))


def test_unfittable_first_window_is_skipped_and_the_next_is_used():
    # External-audit reproduction: 4,505-token first snippet, 7-token second snippet, budget 1,000.
    huge = one_line("Big.java", " ".join(f"w{i}" for i in range(2300)))
    small = one_line("Small.java", "int x;")
    res = fill([0, 1], [huge, small], 1000)
    assert [s.path for s in res.snippets] == ["Small.java"]
    assert res.status == "line_limit" and res.n_skipped_size == 1
    assert res.tokens == count_tokens(render_cross_file(res.snippets))


def test_short_when_pool_is_exhausted_without_size_failures():
    res = fill([0], [one_line("A.java", "int x;")], 1000)
    assert res.status == "short" and len(res.snippets) == 1


def test_zero_target_selects_nothing():
    res = fill([0], [one_line("A.java", "int x;")], 0)
    assert res.snippets == [] and res.tokens == 0


def test_tiny_targets_never_overshoot():
    pool = windows("A.java", "package a;\n" + numbered(50))
    for target in (1, 5, 13, 37):
        res = fill(list(range(len(pool))), pool, target)
        assert res.tokens == count_tokens(render_cross_file(res.snippets)) <= target


@pytest.mark.parametrize("target", [500, 1000, 2000, 4000, 8000])
def test_fill_counts_the_rendered_block_and_meets_the_tolerance(target):
    pool = [w for name in "ABCD" for w in windows(f"{name}.java", f"package {name.lower()};\n" + numbered(400))]
    order = list(range(len(pool)))
    random.Random(target).shuffle(order)
    res = fill(order, pool, target)
    assert res.tokens == count_tokens(render_cross_file(res.snippets)) <= target
    assert res.status == "ok" and res.tokens >= 0.98 * target
    spans = {}
    for s in res.snippets:
        assert all(s.end < a or s.start > b for a, b in spans.get(s.path, []))
        spans.setdefault(s.path, []).append((s.start, s.end))


def test_render_groups_by_file_and_puts_the_best_ranked_file_last():
    pool = [Window("A.java", 1, ("int a;",)), Window("B.java", 1, ("int b;",)), Window("A.java", 5, ("int c;",))]
    res = fill([1, 2, 0], pool, 1000)
    text = render_cross_file(res.snippets)
    assert text.index("A.java lines 1-1") < text.index("A.java lines 5-5") < text.index("B.java")


def test_snippet_text_is_exactly_the_window_lines():
    pool = windows("A.java", "package a;\n" + numbered(100))
    res = fill(list(range(len(pool))), pool, 300)
    for s in res.snippets:
        assert s.text.split("\n", 1)[1] == "\n".join(s.lines)
        assert s.text.startswith(f"// A.java lines {s.start}-{s.end}\n")
