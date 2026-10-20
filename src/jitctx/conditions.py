"""Build the C0-C3 context blocks and prompts for one commit from the parent snapshot (design §5)."""
import hashlib
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from . import gitrepo
from .bm25 import bm25_scores
from .diffparse import changed_text, parse
from .local import fill_local, local_files, render_local, runs
from .prompt import PROMPT_VERSION, build_prompt, prompt_text, sha256
from .select import FillResult, fill, render_cross_file, windows
from .tokens import TOKENIZER, count_tokens


@dataclass(frozen=True)
class Config:
    budget: int = 2000
    extra_budgets: tuple[int, ...] = ()  # RQ3 series for C2/C3 only
    tolerance: float = 0.02
    window_lines: int = 40
    window_stride: int = 20
    window_max_tokens: int = 500
    bm25_k1: float = 1.2
    bm25_b: float = 0.75
    seed: int = 0
    diff_cap: int = 16000

    def digest(self) -> str:
        return hashlib.sha256(repr(sorted(asdict(self).items())).encode()).hexdigest()[:16]


def c3_order(sha: str, seed: int, n: int) -> list[int]:
    """Seeded permutation of the window indices (design §5.5)."""
    order = list(range(n))
    random.Random(int.from_bytes(hashlib.sha256(f"{sha}:{seed}".encode()).digest(), "big")).shuffle(order)
    return order


def _sources(res: FillResult, scores=None) -> list[dict]:
    out = []
    for s in res.snippets:
        item = {"path": s.path, "start": s.start, "end": s.end, "rank": s.rank, "truncated": s.truncated}
        if scores is not None:
            item["score"] = round(scores[s.rank], 4)  # C2 order index equals rank
        out.append(item)
    return out


def build_commit(repo: Path, sha: str, parent: str, cfg: Config, with_prompts: bool = False) -> list[dict]:
    """One record per condition. Reads Git objects of `parent` and the parent->commit diff only."""
    t0 = time.perf_counter()
    diff = gitrepo.java_diff(repo, parent, sha)
    files = parse(diff)
    t_c0 = count_tokens(diff)
    blocks: dict[str, tuple[str, dict]] = {"C0": ("", {"status": "none", "target_tokens": 0})}

    old_paths = [f.old_path for f in files if f.old_path]
    local = local_files(files, gitrepo.read_blobs(repo, parent, old_paths))
    res1, selected = fill_local(local, cfg.budget, cfg.tolerance)
    blocks["C1"] = (render_local(local, selected), {
        "status": res1.status, "target_tokens": cfg.budget, "n_truncated": 0, "n_skipped_size": res1.n_skipped_size,
        "pool": {"files": len(local), "lines": sum(len(f.pool()) for f in local),
                 "enclosing_lines": sum(len(f.enclosing) for f in local)},
        "sources": [{"path": local[i].path, "runs": runs(s)} for i, s in selected.items()]})

    touched = gitrepo.touched_paths(repo, parent, sha)
    pool_paths = [p for p in gitrepo.java_files(repo, parent) if p not in touched]
    pool = [w for p, text in gitrepo.read_blobs(repo, parent, pool_paths).items()
            for w in windows(p, text, cfg.window_lines, cfg.window_stride, cfg.window_max_tokens)]
    scores = bm25_scores(changed_text(files), ["\n".join(w.lines) for w in pool], cfg.bm25_k1, cfg.bm25_b)
    ranked = sorted((i for i in range(len(pool)) if scores[i] > 0),
                    key=lambda i: (-scores[i], pool[i].path, pool[i].start))
    pool_meta = {"files": len(pool_paths), "windows": len(pool), "windows_positive": len(ranked),
                 "oversized_windows": sum(w.oversized for w in pool)}
    permutation = c3_order(sha, cfg.seed, len(pool))
    for b in (cfg.budget, *cfg.extra_budgets):
        suffix = "" if b == cfg.budget else f"@{b}"
        res2 = fill(ranked, pool, b, cfg.tolerance)
        if not pool:
            res2.status = "empty_pool"
        elif not ranked:
            res2.status = "no_hits"
        res3 = fill(permutation, pool, res2.tokens, cfg.tolerance)
        if res2.tokens == 0:
            res3.status = res2.status
        ranked_scores = [scores[i] for i in ranked]
        for name, res, extra in (("C2", res2, {"sources": _sources(res2, ranked_scores)}),
                                 ("C3", res3, {"sources": _sources(res3), "seed": cfg.seed,
                                               "match_error": (res3.tokens - res2.tokens) / res2.tokens
                                               if res2.tokens else None})):
            blocks[name + suffix] = (render_cross_file(res.snippets), {
                "status": res.status, "target_tokens": res.target, "n_truncated": res.n_truncated,
                "n_skipped_size": res.n_skipped_size, "pool": pool_meta, **extra})

    seconds = round(time.perf_counter() - t0, 3)
    records = []
    for cond, (block, meta) in blocks.items():
        prompt = build_prompt(block, diff)
        text = prompt_text(prompt)
        rec = {"commit": sha, "parent": parent, "condition": cond, "budget": cfg.budget if cond != "C0" else 0,
               "context_tokens": count_tokens(block), "t_c0": t_c0, "diff_over_cap": t_c0 > cfg.diff_cap,
               "prompt_tokens": count_tokens(text), "prompt_sha256": sha256(text), "context_sha256": sha256(block),
               "prompt_version": PROMPT_VERSION, "tokenizer": TOKENIZER, "config": cfg.digest(),
               "build_seconds": seconds, **meta}
        if "@" in cond:
            rec["budget"] = int(cond.split("@")[1])
        if with_prompts:
            rec["prompt"] = prompt
        records.append(rec)
    return records
