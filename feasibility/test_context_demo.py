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
    assert used == sum(cd.count_tokens(d["text"]) for d in picked)
    spans = {}
    for d in picked:
        assert all(d["end"] < s or d["start"] > e for s, e in spans.get(d["path"], []))
        spans.setdefault(d["path"], []).append((d["start"], d["end"]))
