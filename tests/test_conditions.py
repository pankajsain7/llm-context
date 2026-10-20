import inspect
import re
from pathlib import Path

import jitctx
from conftest import FOO
from jitctx import gitrepo
from jitctx.conditions import Config, build_commit, c3_order
from jitctx.prompt import build_prompt
from test_local import BIG


def project(repo):
    files = {f"src/p/Util{i}.java": f"package p;\n\npublic class Util{i} {{\n" + "".join(
        f"    public int add{i}_{j}(int count, int y) {{\n        return count + y * {j};\n    }}\n" for j in range(40))
        + "}\n" for i in range(6)}
    files["src/p/Foo.java"] = FOO
    files["src/p/Big.java"] = BIG
    files["src/p/Data.java"] = "package p;\nclass Data {\n  String s = \"" + "count add " * 3000 + "\";\n}\n"
    files["src/p/package-info.java"] = "package p;\n"
    repo.commit(files)
    return repo.commit({"src/p/Foo.java": FOO.replace("count += y;", "count += add(y);"),
                        "src/p/Neu.java": "package p;\nclass Neu { int count; }\n"},
                       move=[("src/p/Big.java", "src/q/Big.java")])


def records(repo, sha, **cfg):
    parent = gitrepo.parent_of(repo.path, sha)
    return {r["condition"]: r for r in build_commit(repo.path, sha, parent, Config(**cfg), with_prompts=True)}


def test_all_conditions_share_the_diff_and_template(repo):
    sha = project(repo)
    recs = records(repo, sha, extra_budgets=(1000, 8000))
    assert set(recs) == {"C0", "C1", "C2", "C3", "C2@1000", "C3@1000", "C2@8000", "C3@8000"}
    diffs = {r["prompt"]["user"].split("### Code change", 1)[1] for r in recs.values()}
    systems = {r["prompt"]["system"] for r in recs.values()}
    assert len(diffs) == 1 and len(systems) == 1
    assert "(none)" in recs["C0"]["prompt"]["user"] and recs["C0"]["context_tokens"] == 0


def test_cross_file_context_excludes_every_touched_path_and_is_verbatim(repo):
    sha = project(repo)
    parent = gitrepo.parent_of(repo.path, sha)
    touched = gitrepo.touched_paths(repo.path, parent, sha)
    recs = records(repo, sha)
    for cond in ("C2", "C3"):
        r = recs[cond]
        assert r["sources"] and not {s["path"] for s in r["sources"]} & touched
        blobs = gitrepo.read_blobs(repo.path, parent, [s["path"] for s in r["sources"]])
        for s in r["sources"]:
            lines = blobs[s["path"]].split("\n")[s["start"] - 1:s["end"]]
            assert f"// {s['path']} lines {s['start']}-{s['end']}\n" + "\n".join(lines) in r["prompt"]["user"]


def test_budgets_and_matching(repo):
    sha = project(repo)
    recs = records(repo, sha, extra_budgets=(1000, 8000))
    for suffix, b in (("", 2000), ("@1000", 1000), ("@8000", 8000)):
        c2, c3 = recs["C2" + suffix], recs["C3" + suffix]
        assert c2["context_tokens"] <= b and c3["context_tokens"] <= c2["context_tokens"]
        assert c3["target_tokens"] == c2["context_tokens"]
        if c3["status"] == "ok":
            assert abs(c3["match_error"]) <= 0.02
    assert recs["C1"]["context_tokens"] <= 2000


def test_local_context_comes_from_changed_files_only(repo):
    sha = project(repo)
    r = records(repo, sha)["C1"]
    assert {s["path"] for s in r["sources"]} <= {"src/p/Foo.java", "src/p/Big.java"}


def test_rebuild_is_deterministic_and_seed_changes_c3(repo):
    sha = project(repo)
    a, b = records(repo, sha), records(repo, sha)
    assert all(a[c]["prompt_sha256"] == b[c]["prompt_sha256"] for c in a)
    other = records(repo, sha, seed=1)
    assert other["C3"]["context_sha256"] != a["C3"]["context_sha256"]
    assert other["C2"]["context_sha256"] == a["C2"]["context_sha256"]
    assert c3_order("abc", 0, 50) == c3_order("abc", 0, 50) != c3_order("abc", 1, 50)


def test_no_hits_gives_empty_c2_and_c3(repo):
    repo.commit({"A.java": "package a;\nclass A { int alpha; }\n", "B.java": "package a;\nclass B { int beta; }\n"})
    sha = repo.commit({"A.java": "package a;\nclass A { int gamma; }\n"})
    recs = records(repo, sha)
    assert recs["C2"]["status"] == recs["C3"]["status"] == "no_hits"
    assert recs["C2"]["context_tokens"] == recs["C3"]["context_tokens"] == 0
    assert "(none)" in recs["C2"]["prompt"]["user"]


def test_empty_cross_file_pool(repo):
    repo.commit({"A.java": "package a;\nclass A { int alpha; }\n"})
    sha = repo.commit({"A.java": "package a;\nclass A { int alpha2; }\n"})
    assert records(repo, sha)["C2"]["status"] == "empty_pool"


def test_prompt_template_renders_none_for_empty_context():
    assert "(none)" in build_prompt("", "diff")["user"]


def test_context_builder_never_touches_label_sources():
    """Only manifest.py may open the benchmark pickles; nothing may read JIT-Defect-Extended or JIT-LSM files."""
    pkg = Path(inspect.getfile(jitctx)).parent
    for src in pkg.glob("*.py"):
        text = src.read_text(encoding="utf-8")
        assert not re.search(r"jitext|JIT-Defect-Extended|JIT_LSM|added_buggy|buggy_line", text), src.name
        if src.name != "manifest.py":
            assert not re.search(r"pickle|is_buggy_commit|features_|changes_", text), src.name
    cli = (pkg / "cli.py").read_text(encoding="utf-8")
    assert "from .manifest import build" in cli and not re.search(r"^from \.manifest", cli, re.MULTILINE)
