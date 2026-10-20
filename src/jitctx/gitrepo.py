"""Read-only Git access. All code comes from object storage at a given revision; nothing is checked out."""
import shutil
import subprocess
from pathlib import Path

GIT = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"
JAVA_SCOPE = ("--", "*.java", ":(exclude)*package-info.java")  # JIT-Defect4J's la/ld scope (docs/02-datasets.md §2)


def git(repo: Path, *args: str, data: bytes = b"") -> bytes:
    return subprocess.run([GIT, "-c", "core.quotePath=false", *args], cwd=repo, input=data,
                          capture_output=True, check=True).stdout


def decode(raw: bytes) -> str:
    return raw.decode("utf-8", errors="replace")


def parent_of(repo: Path, sha: str) -> str:
    return decode(git(repo, "rev-parse", f"{sha}^")).strip()


def java_diff(repo: Path, parent: str, sha: str) -> str:
    """The C0 diff (decision D7)."""
    return decode(git(repo, "diff", "-U3", "-M", "--no-color", "--no-ext-diff", parent, sha, *JAVA_SCOPE))


def touched_paths(repo: Path, parent: str, sha: str) -> set[str]:
    """Every path the commit touches, any file type, old and new names (no rename pairing)."""
    out = decode(git(repo, "diff", "--name-only", "--no-renames", "-z", parent, sha))
    return {p for p in out.split("\0") if p}


def java_files(repo: Path, rev: str) -> list[str]:
    out = decode(git(repo, "ls-tree", "-r", "--name-only", "-z", rev))
    return sorted(p for p in out.split("\0") if p.endswith(".java"))


def read_blobs(repo: Path, rev: str, paths: list[str]) -> dict[str, str]:
    """Contents of `paths` at `rev` via one `git cat-file --batch` process; missing paths are omitted."""
    if not paths:
        return {}
    data = "".join(f"{rev}:{p}\n" for p in paths).encode()
    out = git(repo, "cat-file", "--batch", data=data)
    blobs, pos = {}, 0
    for p in paths:
        end = out.index(b"\n", pos)
        header = out[pos:end].split()
        pos = end + 1
        if len(header) == 3 and header[1] == b"blob":
            size = int(header[2])
            blobs[p] = decode(out[pos:pos + size])
            pos += size + 1
    return blobs


def head_revision(repo: Path) -> str:
    """HEAD, with "-dirty" if the builder's code or configuration differs from it (then HEAD does not identify it)."""
    try:
        rev = decode(git(repo, "rev-parse", "HEAD")).strip()
        dirty = git(repo, "status", "--porcelain", "--", "src", "configs").strip()
        return rev + ("-dirty" if dirty else "")
    except subprocess.CalledProcessError:
        return "unknown"
