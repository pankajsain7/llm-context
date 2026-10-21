"""Synthetic checks of human-audit blinding, fixed identities, blanks and overwrite safety."""
import csv
import hashlib
import json
import random

import gate2_checks as gate
import label_audit as label
import pytest


def manifest(path, n, split="valid"):
    rows = [{"project": "example", "commit": f"{i:010x}{i:030x}", "parent": f"{i + 100:040x}", "split": split}
            for i in range(1, n + 1)]
    label.write_csv(path, rows, list(rows[0]))
    return rows


def files(path):
    return {p.relative_to(path).as_posix(): p.read_bytes() for p in path.rglob("*") if p.is_file()}


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def expected_commits(manifest):
    return {r["commit"] for r in read_csv(manifest)}


def test_existing30_is_preserved_with_blank_independent10(tmp_path, monkeypatch):
    m = tmp_path / "manifest.csv"
    rows = manifest(m, 30)
    source = tmp_path / "label_audit"
    source.mkdir()
    cases = [{"project": r["project"], "bic": r["commit"], "keys": "ISSUE-1"} for r in reversed(rows)]
    label.write_csv(source / "audit.csv", cases, list(cases[0]))
    for r in cases:
        (source / f"{r['project']}_{r['bic'][:10]}.md").write_text("# Existing evidence\n", encoding="utf-8")
    before = files(source)
    monkeypatch.setattr(label, "git", lambda repo, *args, **kw: ("f" * 40 + "\n")
                        if args[0] == "rev-parse" else "diff --git a/F.java b/F.java\n")
    out = tmp_path / "prepared"
    label.prepare_human(tmp_path, m, out)
    primary = read_csv(out / "primary30" / "ratings.csv")
    second = read_csv(out / "independent10" / "ratings.csv")
    assert len(primary) == 30 and len(second) == 10
    assert {r["case_id"] for r in second} == {f"L{i + 1:02d}" for i in random.Random(2027).sample(range(30), 10)}
    assert all(not r[k] for r in primary + second for k in ("category", "rater_id", "rater_role", "rationale"))
    for r in second:
        assert files(out / "primary30" / r["case_id"]) == files(out / "independent10" / r["case_id"])
    assert files(source) == before
    (out / "primary30" / "ratings.csv").write_text("human work", encoding="utf-8")
    with pytest.raises(FileExistsError):
        label.prepare_human(tmp_path, m, out)
    assert (out / "primary30" / "ratings.csv").read_text(encoding="utf-8") == "human work"


def context_input(tmp_path):
    m, c = tmp_path / "manifest.csv", tmp_path / "contexts.jsonl"
    rs = manifest(m, 60)
    records = []
    for r in reversed(rs):
        for cond in ("C3", "C0", "C2"):
            block = {"C0": "(none)", "C2": "// src/Dependency.java lines 1-1\nint first;",
                     "C3": "// src/Other.java lines 1-1\nint second;"}[cond]
            user = (f"### Additional code from the repository\n{block}\n\n"
                    "### Code change (unified diff)\n--- a/F.java\n+++ b/F.java\n-int a;\n+int b;\n\n"
                    "### Answer\nAnswer YES or NO.")
            records.append({**r, "condition": cond, "budget": 0 if cond == "C0" else 2000,
                            "prompt": {"system": "task", "user": user},
                            "context_sha256": hashlib.sha256(block.encode()).hexdigest(), "prompt_sha256": "p"})
    c.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")
    return m, c


def test_relevance_packets_are_identical_blinded_complete_and_reproducible(tmp_path):
    m, c = context_input(tmp_path)
    first, second = tmp_path / "one", tmp_path / "two"
    gate.prepare_relevance(c, m, first, expected_commits(m))
    gate.prepare_relevance(c, m, second, expected_commits(m))
    assert files(first) == files(second)
    assert files(first / "rater1") == files(first / "rater2")
    ratings = read_csv(first / "rater1" / "ratings.csv")
    key = read_csv(first / "coordinator_only" / "key.csv")
    assert len(ratings) == len(key) == 40
    assert len({r["commit"] for r in key}) == 20
    for r in ratings:
        assert not any(r[k] for k in ("rating", "rater_id", "rater_role", "rationale"))
    for content in files(first / "rater1").values():
        assert not any(s.encode() in content for s in ("C2", "C3", "condition", "is_buggy_commit", "prompt_sha256"))
    for case in {r["case_id"] for r in key}:
        text = (first / "rater1" / f"{case}.md").read_text(encoding="utf-8")
        assert text.count("int first;") == text.count("int second;") == 1
        assert "--- a/F.java\n+++ b/F.java\n-int a;\n+int b;" in text
        assert "### Answer" not in text
    with pytest.raises(FileExistsError):
        gate.prepare_relevance(c, m, first, expected_commits(m))


@pytest.mark.parametrize("change", ["test", "label", "diff", "budget", "missing"])
def test_relevance_rejects_invalid_inputs_before_writing(tmp_path, change):
    m, c = context_input(tmp_path)
    records = [json.loads(x) for x in c.read_text(encoding="utf-8").splitlines()]
    if change == "test":
        records[0]["split"] = "test"
    elif change == "label":
        records[0]["is_buggy_commit"] = 1
    elif change == "diff":
        records[0]["prompt"]["user"] = records[0]["prompt"]["user"].replace("+int b;", "+int changed;")
    elif change == "budget":
        records[0]["budget"] = 1000
    else:
        records.pop()
    c.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")
    out = tmp_path / "out"
    with pytest.raises(ValueError):
        gate.prepare_relevance(c, m, out, expected_commits(m))
    assert not out.exists()


def test_relevance_rejects_a_different_same_size_validation_pool(tmp_path):
    m, c = context_input(tmp_path)
    expected = expected_commits(m)
    expected.remove(min(expected))
    expected.add("f" * 40)
    out = tmp_path / "out"
    with pytest.raises(ValueError, match="frozen60"):
        gate.prepare_relevance(c, m, out, expected)
    assert not out.exists()
