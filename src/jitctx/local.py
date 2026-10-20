"""C1: same-file context from the parent versions of the changed files, with diff lines masked (design §5.2)."""
from bisect import bisect_left
from collections import defaultdict
from dataclasses import dataclass, field

from .diffparse import FileDiff, change_anchors, shown_old_lines
from .java import enclosing_lines, first_code_line, split_lines
from .select import SLACK, FillResult
from .tokens import count_tokens, line_tokens

MARKER = "shown in the diff"


@dataclass
class LocalFile:
    path: str  # parent-side path
    lines: list[str]
    masked: set[int]
    enclosing: set[int]
    first: int  # first line after the license header
    masked_runs: list[tuple[int, int]] = field(default_factory=list)

    def pool(self) -> list[int]:
        return [n for n in range(self.first, len(self.lines) + 1) if n not in self.masked]


def runs(numbers) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for n in sorted(numbers):
        if out and n == out[-1][1] + 1:
            out[-1] = (out[-1][0], n)
        else:
            out.append((n, n))
    return out


def local_files(files: list[FileDiff], blobs: dict[str, str]) -> list[LocalFile]:
    """One entry per changed file that exists at the parent; added files have no parent version."""
    out = []
    for f in files:
        if f.old_path is None or f.old_path not in blobs:
            continue
        text = blobs[f.old_path]
        lines = split_lines(text)
        masked = {n for n in shown_old_lines(f) if 1 <= n <= len(lines)}
        anchors = {n for n in change_anchors(f) if 1 <= n <= len(lines)}
        enclosing = enclosing_lines(text, anchors) - masked
        out.append(LocalFile(f.old_path, lines, masked, enclosing, first_code_line(lines), runs(masked)))
    return out


def render_local(files: list[LocalFile], selected: dict[int, set[int]]) -> str:
    """Per file in diff order: runs of selected lines with a `// path lines a-b` header, and one marker line
    for each masked run that borders a selected line."""
    parts = []
    for i, f in enumerate(files):
        sel = selected.get(i)
        if not sel:
            continue
        items = [(a, b, False) for a, b in runs(sel)]
        items += [(a, b, True) for a, b in f.masked_runs if a - 1 in sel or b + 1 in sel]
        for a, b, is_marker in sorted(items):
            if is_marker:
                parts.append(f"// {f.path} lines {a}-{b}: {MARKER}")
            else:
                parts.append(f"// {f.path} lines {a}-{b}\n" + "\n".join(f.lines[a - 1:b]))
    return "\n".join(parts)


def rank_lines(files: list[LocalFile]) -> list[tuple[int, int]]:
    """Enclosing lines first, then by distance to the nearest masked line, then file order, then line."""
    keyed = []
    for i, f in enumerate(files):
        masked = sorted(f.masked)
        for n in f.pool():
            if masked:
                j = bisect_left(masked, n)
                dist = min(abs(n - masked[k]) for k in (j - 1, j) if 0 <= k < len(masked))
            else:
                dist = float("inf")
            keyed.append(((n not in f.enclosing, dist, i, n), (i, n)))
    return [item for _, item in sorted(keyed)]


def fill_local(files: list[LocalFile], target: int, tol: float = 0.02) -> tuple[FillResult, dict[int, set[int]]]:
    """Add lines in rank order; a line that does not fit is skipped and the next one tried. Below 90% of the
    target a conservative estimate (each new run costs a header and two markers) replaces exact counting;
    above it every addition is checked on the rendered block."""
    res = FillResult([], 0, "short", target)
    selected: dict[int, set[int]] = defaultdict(set)
    if not any(f.pool() for f in files):
        res.status = "empty_pool"
        return res, {}
    run_cost = {i: count_tokens(f"// {f.path} lines 100000-100000: {MARKER}") * 3 + 3 for i, f in enumerate(files)}
    header = {i: count_tokens(f"// {f.path} lines 1-1") for i, f in enumerate(files)}
    exact, est = 0, 0
    for i, n in rank_lines(files):
        sel = selected[i]
        adjacent = n - 1 in sel or n + 1 in sel
        tokens = line_tokens(files[i].lines[n - 1]) + 1
        cost = tokens + (0 if adjacent else run_cost[i])
        if est + cost <= 0.9 * target:
            sel.add(n)
            est += cost
            continue
        if est > exact:
            exact = est = count_tokens(render_local(files, selected))
        if exact + tokens + (0 if adjacent else header[i]) - SLACK > target:
            res.n_skipped_size += 1
            continue
        sel.add(n)
        t = count_tokens(render_local(files, selected))
        if t > target:
            sel.discard(n)
            res.n_skipped_size += 1
            continue
        exact = est = t
        if t >= target * (1 - tol):
            res.status = "ok"
            break
    else:
        res.status = "line_limit" if res.n_skipped_size else "short"
    res.tokens = count_tokens(render_local(files, selected))
    return res, {i: s for i, s in selected.items() if s}

