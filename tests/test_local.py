import re

from jitctx import gitrepo
from jitctx.diffparse import parse
from jitctx.local import fill_local, local_files, render_local, runs
from jitctx.tokens import count_tokens

BIG = "package p;\n\npublic class Big {\n" + "".join(
    f"    int f{i}() {{\n" + "".join(f"        int v{j} = {i} * {j};\n" for j in range(12)) + "        return 0;\n    }\n\n"
    for i in range(30)) + "}\n"


def setup(repo, before, after, path="Big.java"):
    repo.commit({path: before})
    sha = repo.commit({path: after})
    parent = gitrepo.parent_of(repo.path, sha)
    files = parse(gitrepo.java_diff(repo.path, parent, sha))
    blobs = gitrepo.read_blobs(repo.path, parent, [f.old_path for f in files if f.old_path])
    return local_files(files, blobs)


def rendered_code_lines(text):
    """(path, line number, content) for every code line in a C1 block; marker lines are skipped."""
    out, path, n = [], None, 0
    for line in text.split("\n"):
        m = re.fullmatch(r"// (\S+) lines (\d+)-(\d+)(: shown in the diff)?", line)
        if m:
            path, n = (None, 0) if m[4] else (m[1], int(m[2]))
        elif path:
            out.append((path, n, line))
            n += 1
    return out


def test_masked_lines_never_appear_and_code_is_verbatim(repo):
    after = BIG.replace("int v5 = 10 * 5;", "int v5 = 10 * 6;")
    (lf,) = setup(repo, BIG, after)
    res, sel = fill_local([lf], 4000)
    text = render_local([lf], sel)
    assert res.tokens == count_tokens(text) <= 4000 and res.status == "ok"
    code = rendered_code_lines(text)
    assert code and all(n not in lf.masked and lf.lines[n - 1] == content for _, n, content in code)


def test_enclosing_method_comes_first(repo):
    after = BIG.replace("int v5 = 10 * 5;", "int v5 = 10 * 6;")
    (lf,) = setup(repo, BIG, after)
    assert lf.enclosing and not (lf.enclosing & lf.masked)
    res, sel = fill_local([lf], 400)
    assert lf.enclosing <= sel[0] and res.status == "ok"
    rest = sel[0] - lf.enclosing
    nearest = {n: min(abs(n - m) for m in lf.masked) for n in lf.pool() if n not in lf.enclosing}
    assert rest and max(nearest[n] for n in rest) <= min(d for n, d in nearest.items() if n not in rest)


def test_markers_border_selected_lines(repo):
    after = BIG.replace("int v5 = 10 * 5;", "int v5 = 10 * 6;")
    (lf,) = setup(repo, BIG, after)
    _, sel = fill_local([lf], 300)
    text = render_local([lf], sel)
    (a, b), = lf.masked_runs
    assert f"// Big.java lines {a}-{b}: shown in the diff" in text


def test_new_file_has_no_local_pool(repo):
    repo.commit({"Other.java": "package p;\nclass Other {}\n"})
    sha = repo.commit({"New.java": BIG})
    parent = gitrepo.parent_of(repo.path, sha)
    files = parse(gitrepo.java_diff(repo.path, parent, sha))
    lfs = local_files(files, gitrepo.read_blobs(repo.path, parent, [f.old_path for f in files if f.old_path]))
    res, sel = fill_local(lfs, 2000)
    assert lfs == [] and res.status == "empty_pool" and sel == {}


def test_deleted_file_is_fully_masked(repo):
    repo.commit({"Big.java": "/* license */\n" + BIG, "Keep.java": "package p;\nclass Keep {}\n"})
    sha = repo.commit(delete=["Big.java"])
    parent = gitrepo.parent_of(repo.path, sha)
    files = parse(gitrepo.java_diff(repo.path, parent, sha))
    lfs = local_files(files, gitrepo.read_blobs(repo.path, parent, [f.old_path for f in files if f.old_path]))
    res, _ = fill_local(lfs, 2000)
    assert res.status == "empty_pool"


def test_small_pool_is_short(repo):
    small = "package p;\nclass S {\n  int a;\n  int b;\n  int c;\n  int d;\n  int e;\n  int f;\n  int g;\n}\n"
    (lf,) = setup(repo, small, small.replace("int e;", "int e2;"), "S.java")
    res, sel = fill_local([lf], 2000)
    assert res.status == "short" and set().union(*sel.values()) == set(lf.pool())


def test_runs():
    assert runs({5, 1, 2, 3, 7}) == [(1, 3), (5, 5), (7, 7)]
