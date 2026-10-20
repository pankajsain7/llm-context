"""Snippet selection under a token budget counted on the rendered block (design §5.1, §5.3-5.5)."""
from collections import defaultdict
from dataclasses import dataclass

from .java import first_code_line, split_lines
from .tokens import count_tokens, line_tokens

SLACK = 4  # tokens a join can save through BPE merges; only used to skip hopeless exact counts


@dataclass(frozen=True)
class Window:
    path: str
    start: int  # 1-based line number in the parent file
    lines: tuple[str, ...]
    oversized: bool = False  # a single line longer than the window token bound

    @property
    def end(self) -> int:
        return self.start + len(self.lines) - 1


@dataclass(frozen=True)
class Snippet:
    path: str
    start: int
    lines: tuple[str, ...]
    rank: int  # position in the selection order (0 = first choice)
    truncated: bool = False

    @property
    def end(self) -> int:
        return self.start + len(self.lines) - 1

    @property
    def text(self) -> str:
        return f"// {self.path} lines {self.start}-{self.end}\n" + "\n".join(self.lines)


@dataclass
class FillResult:
    snippets: list[Snippet]
    tokens: int  # tokens of render(snippets)
    status: str  # ok | short | line_limit | no_hits | empty_pool
    target: int
    n_truncated: int = 0
    n_skipped_size: int = 0


def windows(path: str, text: str, max_lines: int = 40, stride: int = 20, max_tokens: int = 500) -> list[Window]:
    """Windows of at most `max_lines` lines and (unless a single line is longer) `max_tokens` code tokens.

    Line token sums approximate the window's tokens; the exact budget check happens on the rendered block.
    Consecutive windows overlap by half their length (at most `stride` lines apart), and the last window
    ends at the file's last line, so every line after the license header is covered.
    """
    lines = split_lines(text)
    first = first_code_line(lines)
    code = lines[first - 1:]
    cost = [line_tokens(line) + 1 for line in code]
    out, s, n = [], 0, len(code)
    while s < n:
        e, used = s, 0
        while e < n and e - s < max_lines and (e == s or used + cost[e] <= max_tokens):
            used += cost[e]
            e += 1
        out.append(Window(path, first + s, tuple(code[s:e]), oversized=e - s == 1 and cost[s] > max_tokens))
        if e == n:
            break
        s += max(1, min(stride, (e - s) // 2))
    return out


def render_cross_file(snippets: list[Snippet]) -> str:
    """Grouped by file, files ordered so that the best-ranked snippet comes last (next to the diff)."""
    by_file = defaultdict(list)
    for s in snippets:
        by_file[s.path].append(s)
    files = sorted(by_file, key=lambda p: (-min(s.rank for s in by_file[p]), p))
    return "\n".join(s.text for p in files for s in sorted(by_file[p], key=lambda s: s.start))


def _cut(s: Snippet, k: int) -> Snippet:
    return Snippet(s.path, s.start, s.lines[:k], s.rank, truncated=True)


def fill(order: list[int], pool: list[Window], target: int, tol: float = 0.02) -> FillResult:
    """Add windows in `order`, skipping overlaps with selected windows of the same file. A window that does
    not fit is cut at a line boundary; if not even its first line fits, it is skipped and the next window
    is tried. Status: ok (within `tol` below target), short (eligible windows exhausted), line_limit (below
    target and at least one window could not be fitted)."""
    picked: list[Snippet] = []
    used, spans = 0, defaultdict(list)
    res = FillResult([], 0, "short", target)
    if target <= 0:
        return res

    def fits(cand: Snippet) -> bool:
        return count_tokens(render_cross_file(picked + [cand])) <= target

    for rank, i in enumerate(order):
        w = pool[i]
        if any(not (w.end < a or w.start > b) for a, b in spans[w.path]):
            continue
        cand = Snippet(w.path, w.start, w.lines, rank)
        if not (used + count_tokens(cand.text) <= target + SLACK and fits(cand)):
            if count_tokens(_cut(cand, 1).text) > target - used + SLACK or not fits(_cut(cand, 1)):
                res.n_skipped_size += 1
                continue
            lo, hi = 1, len(cand.lines) - 1
            while lo < hi:
                mid = (lo + hi + 1) // 2
                lo, hi = (mid, hi) if fits(_cut(cand, mid)) else (lo, mid - 1)
            if lo < len(cand.lines):
                cand = _cut(cand, lo)
                res.n_truncated += 1
        picked.append(cand)
        spans[w.path].append((cand.start, cand.end))
        used = count_tokens(render_cross_file(picked))
        if used >= target * (1 - tol):
            res.status = "ok"
            break
    else:
        res.status = "line_limit" if res.n_skipped_size else "short"
    res.snippets, res.tokens = picked, used
    return res
