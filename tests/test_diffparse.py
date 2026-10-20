from conftest import FOO
from jitctx import gitrepo
from jitctx.diffparse import change_anchors, changed_text, parse, shown_old_lines


def diff_of(repo, sha):
    return gitrepo.java_diff(repo.path, gitrepo.parent_of(repo.path, sha), sha)


def test_modified_file_hunks_masks_and_anchors(repo):
    repo.commit({"src/Foo.java": FOO})
    sha = repo.commit({"src/Foo.java": FOO.replace("count += y;", "count -= y;")})
    (f,) = parse(diff_of(repo, sha))
    assert f.old_path == f.new_path == "src/Foo.java"
    assert shown_old_lines(f) == set(range(13, 20))
    assert change_anchors(f) == {16}
    assert changed_text([f]) == "        count += y;\n        count -= y;"


def test_insertion_anchors_both_parent_neighbours(repo):
    repo.commit({"Foo.java": FOO})
    sha = repo.commit({"Foo.java": FOO.replace("        return count;\n", "        log();\n        return count;\n")})
    (f,) = parse(diff_of(repo, sha))
    assert change_anchors(f) == {16, 17}


def test_deleted_line_that_looks_like_a_header(repo):
    repo.commit({"Bar.java": "package p;\nclass Bar {\n void f(int i) {\n--i;\n }\n}\n"})
    sha = repo.commit({"Bar.java": "package p;\nclass Bar {\n void f(int i) {\n }\n}\n"})
    diff = diff_of(repo, sha)
    assert "\n---i;\n" in diff
    (f,) = parse(diff)
    assert changed_text([f]) == "--i;"
    assert change_anchors(f) == {4}


def test_added_deleted_renamed_and_scope(repo):
    repo.commit({"a/Old.java": FOO, "a/Gone.java": "package a;\nclass Gone {}\n", "a/package-info.java": "package a;\n",
                 "README.md": "x\n"})
    new = "package a;\n\n/** A new interface. */\npublic interface New {\n    void run();\n    int size();\n}\n"
    sha = repo.commit(write={"a/New.java": new, "a/package-info.java": "/** doc */\npackage a;\n",
                             "README.md": "y\n", "b/Moved.java": FOO.replace("int y = x + 1;", "int y = x + 2;")},
                      delete=["a/Gone.java", "a/Old.java"])
    files = {(f.old_path, f.new_path): f for f in parse(diff_of(repo, sha))}
    assert set(files) == {(None, "a/New.java"), ("a/Gone.java", None), ("a/Old.java", "b/Moved.java")}
    assert shown_old_lines(files[("a/Gone.java", None)]) == {1, 2}
    assert gitrepo.touched_paths(repo.path, gitrepo.parent_of(repo.path, sha), sha) == {
        "a/New.java", "a/Gone.java", "a/Old.java", "b/Moved.java", "a/package-info.java", "README.md"}


def test_pure_rename_has_no_hunks(repo):
    repo.commit({"A.java": FOO})
    sha = repo.commit(move=[("A.java", "B.java")])
    (f,) = parse(diff_of(repo, sha))
    assert (f.old_path, f.new_path, f.hunks) == ("A.java", "B.java", [])


def test_missing_final_newline(repo):
    repo.commit({"A.java": "package p;\nclass A {}"})
    sha = repo.commit({"A.java": "package p;\nclass A { }"})
    (f,) = parse(diff_of(repo, sha))
    assert [line[:1] for line in f.hunks[0].lines] == [" ", "-", "\\", "+"]
    assert changed_text([f]) == "class A {}\nclass A { }"
