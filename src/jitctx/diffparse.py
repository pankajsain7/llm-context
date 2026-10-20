"""Parse Git unified diffs into per-file hunks, by counting hunk lines rather than trusting line prefixes."""
import re
from dataclasses import dataclass, field

HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


@dataclass
class Hunk:
    old_start: int
    old_len: int
    new_start: int
    new_len: int
    lines: list[str] = field(default_factory=list)


@dataclass
class FileDiff:
    old_path: str | None = None
    new_path: str | None = None
    hunks: list[Hunk] = field(default_factory=list)


def _path(rest: str) -> str | None:
    rest = rest.rstrip("\t")  # Git appends a tab when the name contains a space
    return None if rest == "/dev/null" else rest[2:]


def parse(diff: str) -> list[FileDiff]:
    files: list[FileDiff] = []
    cur, old_left, new_left = None, 0, 0
    for line in diff.split("\n"):
        if old_left or new_left:
            tag = line[:1]
            cur.hunks[-1].lines.append(line)
            if tag in " -":
                old_left -= 1
            if tag in " +":
                new_left -= 1
            continue
        if line.startswith("diff --git "):
            cur = FileDiff()
            files.append(cur)
        elif cur is None or line.startswith("\\"):
            continue
        elif line.startswith("--- "):
            cur.old_path = _path(line[4:])
        elif line.startswith("+++ "):
            cur.new_path = _path(line[4:])
        elif line.startswith("rename from "):
            cur.old_path = line[12:]
        elif line.startswith("rename to "):
            cur.new_path = line[10:]
        elif m := HUNK.match(line):
            old_len = int(m[2]) if m[2] is not None else 1
            new_len = int(m[4]) if m[4] is not None else 1
            cur.hunks.append(Hunk(int(m[1]), old_len, int(m[3]), new_len))
            old_left, new_left = old_len, new_len
    return files


def shown_old_lines(f: FileDiff) -> set[int]:
    """Parent-side line numbers the diff displays (context and deleted lines); these are masked in C1."""
    return {n for h in f.hunks for n in range(h.old_start, h.old_start + h.old_len)}


def change_anchors(f: FileDiff) -> set[int]:
    """Parent-side lines that a change touches: deleted lines, and both parent neighbours of a pure insertion."""
    anchors = set()
    for h in f.hunks:
        nxt = h.old_start if h.old_len else h.old_start + 1
        deleted_in_block = False
        for line in h.lines:
            tag = line[:1]
            if tag == " ":
                nxt += 1
                deleted_in_block = False
            elif tag == "-":
                anchors.add(nxt)
                nxt += 1
                deleted_in_block = True
            elif tag == "+" and not deleted_in_block:
                anchors.update(n for n in (nxt - 1, nxt) if n >= 1)
    return anchors


def changed_text(files: list[FileDiff]) -> str:
    """Content of added and deleted lines without their prefix: the BM25 query source (design §5.4)."""
    return "\n".join(line[1:] for f in files for h in f.hunks for line in h.lines if line[:1] in "+-")
