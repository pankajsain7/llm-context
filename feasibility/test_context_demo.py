import random

import pytest

import context_demo as cd


def numbered(n):
    return "\n".join(f"int v{i} = f{i}(x);" for i in range(1, n + 1))


@pytest.mark.parametrize("n", range(0, 121))
def test_chunk_covers_every_line(n):
    covered = set()
    for d in cd.chunk("A.java", numbered(n)):
        assert d["end"] - d["start"] + 1 <= 40
        covered.update(range(d["start"], d["end"] + 1))
    assert covered == set(range(1, n + 1))


def test_chunk_strips_license_header_but_keeps_line_numbers():
    (d,) = cd.chunk("A.java", "/* license */\n/* more */\npackage a;\nclass A {}")
    assert (d["start"], d["end"]) == (3, 4)
    assert d["body"].startswith("package a;")


def test_bm25_does_not_index_the_path_header():
    docs = [*cd.chunk("pkg/Foo.java", "package p;\nint bar;"), *cd.chunk("pkg/Baz.java", "package p;\nint qux;")]
    _, scores = cd.bm25_rank("foo", docs)
    assert scores == [0.0, 0.0]


def test_fill_returns_nothing_when_no_window_matches():
    docs = [*cd.chunk("A.java", "package a;\nint alpha;"), *cd.chunk("B.java", "package b;\nint beta;")]
    order, scores = cd.bm25_rank("gamma", docs)
    assert cd.fill(order, docs, 2000, scores) == ([], 0, "no_hits")


def one_line_doc(path, line):
    return {"path": path, "start": 1, "end": 1, "body": line, "text": f"// {path} lines 1-1\n{line}"}


def test_fill_skips_an_unfittable_single_line_and_tries_the_next_snippet():
    # External audit reproduction: a 4,505-token one-line window ranked first used to end filling with nothing.
    huge = one_line_doc("Big.java", " ".join(f"w{i}" for i in range(2300)))
    small = one_line_doc("Small.java", "int x;")
    assert cd.count_tokens(huge["text"]) > 1000
    picked, used, status = cd.fill([0, 1], [huge, small], 1000)
    assert [d["path"] for d in picked] == ["Small.java"]
    assert used == cd.count_tokens(cd.render(picked)) > 0
    assert status == "line_limit"


def test_fill_reports_short_when_the_pool_is_exhausted_without_size_failures():
    picked, used, status = cd.fill([0], [one_line_doc("A.java", "int x;")], 1000)
    assert len(picked) == 1 and status == "short"


def test_fill_skips_zero_score_windows():
    docs = [*cd.chunk("A.java", "package a;\nint alpha;"), *cd.chunk("B.java", "package b;\nint beta;")]
    order, scores = cd.bm25_rank("alpha", docs)
    picked, _, status = cd.fill(order, docs, 2000, scores)
    assert [d["path"] for d in picked] == ["A.java"]
    assert status == "short"


@pytest.mark.parametrize("target", [500, 1000, 2000, 4000])
def test_fill_reaches_target_within_two_percent(target):
    docs = [d for name in "ABCD" for d in cd.chunk(f"{name}.java", f"package {name.lower()};\n" + numbered(300))]
    order = list(range(len(docs)))
    random.Random(0).shuffle(order)
    picked, used, status = cd.fill(order, docs, target)
    assert status == "ok"
    assert target * 0.98 <= used <= target
    assert used == cd.count_tokens(cd.render(picked))
    spans = {}
    for d in picked:
        assert all(d["end"] < s or d["start"] > e for s, e in spans.get(d["path"], []))
        spans.setdefault(d["path"], []).append((d["start"], d["end"]))
