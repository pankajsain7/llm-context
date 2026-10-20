import os
import subprocess
from pathlib import Path

import pytest

from jitctx.gitrepo import GIT

SCRATCH = Path(os.environ.get("THESIS_SCRATCH", r"C:\Users\psain\thesis-scratch"))


class Repo:
    """A throwaway Git repository for end-to-end tests of the context builder."""

    def __init__(self, path: Path):
        self.path = path
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@example.org")
        self.git("config", "user.name", "test")
        self.git("config", "core.autocrlf", "false")

    def git(self, *args) -> str:
        return subprocess.run([GIT, *args], cwd=self.path, capture_output=True, text=True, check=True).stdout

    def commit(self, write=None, delete=(), move=()) -> str:
        for old, new in move:
            (self.path / new).parent.mkdir(parents=True, exist_ok=True)
            self.git("mv", old, new)
        for p in delete:
            self.git("rm", "-q", p)
        for p, text in (write or {}).items():
            f = self.path / p
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(text.encode("utf-8"))
            self.git("add", p)
        self.git("commit", "-q", "--allow-empty", "-m", "c")
        return self.git("rev-parse", "HEAD").strip()


@pytest.fixture
def repo(tmp_path):
    return Repo(tmp_path)


FOO = """/* Licensed to the Apache Software Foundation */
package p;

import java.util.List;

public class Foo {
    private int count;
    static final String NAME = "foo";

    public Foo() {
        count = 0;
    }

    public int add(int x) {
        int y = x + 1;
        count += y;
        return count;
    }

    static {
        System.out.println("init");
    }

    { count = 5; }

    public void other() {
        Runnable r = new Runnable() {
            public void run() {
                helper();
            }
        };
    }
}
"""
