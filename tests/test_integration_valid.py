"""Integration checks on real JIT-Defect4J validation commits (Gate 2). Skipped without the scratch data.

The sample is drawn label-blind from the manifest, plus edge cases chosen from manifest columns and Git:
the largest eligible diff, the most files changed, a commit that adds files, and one that renames a file.
"""
import csv
import random
import re

import pytest

from conftest import SCRATCH
from jitctx import gitrepo
from jitctx.conditions import Config, build_commit
from jitctx.diffparse import parse

pytestmark = pytest.mark.integration
MANIFEST = SCRATCH / "manifest.csv"


def valid_sample(n=20, seed=7):
    if not MANIFEST.exists():
        pytest.skip(f"no manifest at {MANIFEST}; run `python -m jitctx build-manifest`")
    with open(MANIFEST, encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["split"] == "valid" and r["eligible"] == "True"]
    rng = random.Random(seed)
    picked = rng.sample(sorted(rows, key=lambda r: r["commit"]), n)
    picked.append(max(rows, key=lambda r: int(float(r["t_c0"]))))
    picked.append(max(rows, key=lambda r: int(float(r["n_java_files"]))))
    for kind in ("A", "R"):
        for r in rng.sample(rows, 300):
            status = gitrepo.decode(gitrepo.git(SCRATCH / "repos" / r["project"], "diff", "--name-status", "-M",
                                                r["parent"], r["commit"], *gitrepo.JAVA_SCOPE))
            if re.search(rf"^{kind}", status, re.MULTILINE):
                picked.append(r)
                break
    return picked


@pytest.fixture(scope="module")
def built():
    out = []
    for r in valid_sample():
        repo = SCRATCH / "repos" / r["project"]
        recs = {x["condition"]: x for x in build_commit(repo, r["commit"], r["parent"], Config(), with_prompts=True)}
        out.append((r, repo, recs))
    return out


def test_sample_covers_the_edge_cases(built):
    assert len(built) >= 22


def test_identical_diff_and_template_in_every_condition(built):
    for r, _, recs in built:
        tails = {x["prompt"]["user"].split("### Code change", 1)[1] for x in recs.values()}
        assert len(tails) == 1, r["commit"]
        assert recs["C0"]["t_c0"] == int(float(r["t_c0"])), r["commit"]


def test_local_context_is_masked_and_verbatim(built):
    for r, repo, recs in built:
        files = parse(gitrepo.java_diff(repo, r["parent"], r["commit"]))
        blobs = gitrepo.read_blobs(repo, r["parent"], [f.old_path for f in files if f.old_path])
        shown = {(f.old_path, n) for f in files for h in f.hunks for n in range(h.old_start, h.old_start + h.old_len)}
        for s in recs["C1"]["sources"]:
            lines = blobs[s["path"]].split("\n")
            for a, b in s["runs"]:
                assert not any((s["path"], n) in shown for n in range(a, b + 1)), r["commit"]
                block = f"// {s['path']} lines {a}-{b}\n" + "\n".join(x.removesuffix("\r") for x in lines[a - 1:b])
                assert block in recs["C1"]["prompt"]["user"], (r["commit"], s["path"], a)
        assert recs["C1"]["context_tokens"] <= 2000


def test_cross_file_context_is_from_other_files_at_the_parent(built):
    for r, repo, recs in built:
        touched = gitrepo.touched_paths(repo, r["parent"], r["commit"])
        for cond in ("C2", "C3"):
            srcs = recs[cond]["sources"]
            assert not {s["path"] for s in srcs} & touched, (r["commit"], cond)
            blobs = gitrepo.read_blobs(repo, r["parent"], [s["path"] for s in srcs])
            for s in srcs:
                lines = [x.removesuffix("\r") for x in blobs[s["path"]].split("\n")[s["start"] - 1:s["end"]]]
                assert f"// {s['path']} lines {s['start']}-{s['end']}\n" + "\n".join(lines) in recs[cond]["prompt"]["user"]


def test_budget_and_token_match(built):
    for r, _, recs in built:
        c2, c3 = recs["C2"], recs["C3"]
        assert c2["context_tokens"] <= 2000 and c3["context_tokens"] <= c2["context_tokens"], r["commit"]
        assert c2["status"] in {"ok", "short", "line_limit", "no_hits", "empty_pool"}
        if c3["status"] == "ok":
            assert abs(c3["match_error"]) <= 0.02, r["commit"]
        else:
            assert c3["status"] in {"short", "line_limit", "no_hits", "empty_pool"}, r["commit"]


def test_prompt_fits_the_planned_window(built):
    for r, _, recs in built:
        assert max(x["prompt_tokens"] for x in recs.values()) <= 16000 + 2000 + 400, r["commit"]


def test_rebuild_is_deterministic(built):
    r, repo, recs = built[0]
    again = {x["condition"]: x for x in build_commit(repo, r["commit"], r["parent"], Config())}
    assert {c: x["prompt_sha256"] for c, x in recs.items()} == {c: x["prompt_sha256"] for c, x in again.items()}
