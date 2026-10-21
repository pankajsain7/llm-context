"""Command line: `python -m jitctx build-manifest | make-contexts | summarize`. No LLM is called anywhere."""
import argparse
import csv
import json
import random
import subprocess
import sys
import tomllib
from collections import Counter
from dataclasses import fields
from pathlib import Path

from . import gitrepo
from .conditions import Config, build_commit

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_config(path: Path | None, **overrides) -> Config:
    values = tomllib.loads(path.read_text())["contexts"] if path else {}
    values.update({k: v for k, v in overrides.items() if v is not None})
    if "extra_budgets" in values:
        values["extra_budgets"] = tuple(values["extra_budgets"])
    unknown = set(values) - {f.name for f in fields(Config)}
    if unknown:
        raise SystemExit(f"unknown config keys: {sorted(unknown)}")
    return Config(**values)


def read_manifest(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def validate_manifest(rows: list[dict], cfg: Config) -> None:
    """Fail closed when eligibility was built under a different cap or token accounting policy."""
    for row in rows:
        if not row.get("diff_cap") or not row.get("tokenizer"):
            raise ValueError("manifest lacks diff_cap/tokenizer metadata; rebuild it with build-manifest")
        if int(row["diff_cap"]) != cfg.diff_cap or row["tokenizer"] != cfg.tokenizer:
            raise ValueError("manifest/config diff_cap or tokenizer mismatch; rebuild with the intended config")
        if row.get("eligible") == "True":
            tokens = float(row["t_c0"])
            if not 0 <= tokens <= cfg.diff_cap:
                raise ValueError("manifest marks an over-cap or invalid-sized diff eligible")


def cmd_build_manifest(a):
    from .manifest import build  # the only code path that opens the benchmark files

    cfg = load_config(a.config, diff_cap=a.cap)
    manifest, labels = build(a.root, tuple(a.splits), cfg.diff_cap, log=lambda s: print(s, file=sys.stderr))
    manifest.to_csv(a.out, index=False)
    print(f"manifest: {len(manifest)} commits -> {a.out}")
    if a.labels_out:
        labels.to_csv(a.labels_out, index=False)
        print(f"labels (train/valid only): {len(labels)} -> {a.labels_out}")
    for split, s in manifest.groupby("split"):
        print(f"{split}: recon_ok {int(s.recon_ok.sum())}/{len(s)}, eligible {int(s.eligible.sum())}")


def cmd_make_contexts(a):
    cfg = load_config(a.config, budget=a.budget, seed=a.seed,
                      extra_budgets=tuple(a.extra_budgets) if a.extra_budgets else None)
    if a.split == "test" and not a.allow_test:
        raise SystemExit("test-split contexts are locked until the protocol freeze (Gate 4)")
    rows = read_manifest(a.manifest)
    try:
        validate_manifest(rows, cfg)
    except (KeyError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    rows = [r for r in rows if r["split"] == a.split and r["eligible"] == "True"]
    if a.commits:
        wanted = set(a.commits)
        rows = [r for r in rows if r["commit"] in wanted]
    elif a.sample:
        rows = random.Random(a.sample_seed).sample(sorted(rows, key=lambda r: r["commit"]), min(a.sample, len(rows)))
    code_rev = gitrepo.head_revision(REPO_ROOT)
    with open(a.out, "w", encoding="utf-8") as out:
        for k, r in enumerate(rows, 1):
            try:
                records = build_commit(a.repos / r["project"], r["commit"], r["parent"], cfg, a.with_prompts)
                if records[0]["t_c0"] != float(r["t_c0"]):
                    raise ValueError("rebuilt C0 token count disagrees with manifest; rebuild and inspect inputs")
            except (subprocess.CalledProcessError, OSError, ValueError) as e:  # recorded, never silently skipped
                records = [{"commit": r["commit"], "condition": "ALL", "status": "error",
                            "error": f"{type(e).__name__}: {e}"[:300]}]
            for rec in records:
                rec.update(project=r["project"], split=r["split"], code_revision=code_rev)
                out.write(json.dumps(rec) + "\n")
            print(f"[{k}/{len(rows)}] {r['project']} {r['commit'][:10]}", file=sys.stderr)


def c2_c3_pairs(recs: list[dict], tol: float) -> tuple[Counter, list[str], list[float]]:
    """Every C3 record against its C2 record at the same budget, whatever the status.

    Returns status pairs, violations (C3 not within `tol` below C2's tokens, or not empty when C2 is), and the
    share of C3's code lines that C2 also shows (overlap is allowed by design §5.5, but must be reported).
    """
    idx = {(r["commit"], r["condition"]): r for r in recs}
    pairs, bad, overlap = Counter(), [], []
    for (sha, cond), c3 in idx.items():
        if not cond.startswith("C3"):
            continue
        c2 = idx.get((sha, "C2" + cond[2:]))
        if c2 is None:
            bad.append(f"{sha[:10]} {cond}: no C2 record")
            continue
        pairs[(cond, c2["status"], c3["status"])] += 1
        t2, t3 = c2["context_tokens"], c3["context_tokens"]
        if not (t3 == t2 == 0 or (t2 > 0 and t2 * (1 - tol) <= t3 <= t2)):
            bad.append(f"{sha[:10]} {cond}: C2 {t2} tokens, C3 {t3}")
        lines = [{(s["path"], n) for s in r["sources"] for n in range(s["start"], s["end"] + 1)} for r in (c2, c3)]
        if lines[1]:
            overlap.append(len(lines[0] & lines[1]) / len(lines[1]))
    return pairs, bad, overlap


def cmd_summarize(a):
    with open(a.jsonl, encoding="utf-8") as f:
        recs = [json.loads(line) for line in f]
    by_cond = {}
    for r in recs:
        by_cond.setdefault(r["condition"], []).append(r)
    for cond, rs in sorted(by_cond.items()):
        status = Counter(r["status"] for r in rs)
        ctx = sorted(r.get("context_tokens", 0) for r in rs)
        line = f"{cond}: n={len(rs)} status={dict(status)} context_tokens median={ctx[len(ctx) // 2]} max={ctx[-1]}"
        errs = [abs(r["match_error"]) for r in rs if r.get("match_error") is not None]
        if errs:
            line += f" |match error| max={max(errs):.4f} >2%: {sum(e > 0.02 for e in errs)}"
        print(line)
    pairs, bad, overlap = c2_c3_pairs([r for r in recs if r["condition"] != "ALL"], Config().tolerance)
    print("C2/C3 status pairs:", {" ".join(k): v for k, v in sorted(pairs.items())})
    print(f"C3 token-match violations: {len(bad)} of {sum(pairs.values())}", *bad[:20], sep="\n  ")
    if overlap:
        overlap.sort()
        print(f"C3 lines also in C2: mean {sum(overlap) / len(overlap):.3f}, median {overlap[len(overlap) // 2]:.3f}, "
              f"max {overlap[-1]:.3f}, any overlap in {sum(o > 0 for o in overlap)} of {len(overlap)}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="jitctx")
    sub = ap.add_subparsers(required=True)
    p = sub.add_parser("build-manifest", help="label-free manifest with eligibility flags")
    p.add_argument("--root", type=Path, required=True, help="scratch folder with jitfine/ and repos/")
    p.add_argument("--splits", nargs="+", choices=["train", "valid", "test"], default=["train", "valid", "test"])
    p.add_argument("--config", type=Path, default=REPO_ROOT / "configs" / "contexts.toml")
    p.add_argument("--cap", type=int, help="override the config diff_cap when building eligibility")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--labels-out", type=Path, help="train/valid labels; never contains test labels")
    p.set_defaults(func=cmd_build_manifest)
    p = sub.add_parser("make-contexts", help="C0-C3 records for manifest commits (JSONL)")
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--repos", type=Path, required=True)
    p.add_argument("--split", choices=["train", "valid", "test"], default="valid")
    p.add_argument("--allow-test", action="store_true", help="only after the Gate 4 freeze")
    p.add_argument("--commits", nargs="*")
    p.add_argument("--sample", type=int)
    p.add_argument("--sample-seed", type=int, default=0)
    p.add_argument("--config", type=Path, default=REPO_ROOT / "configs" / "contexts.toml")
    p.add_argument("--budget", type=int)
    p.add_argument("--extra-budgets", type=int, nargs="*")
    p.add_argument("--seed", type=int)
    p.add_argument("--with-prompts", action="store_true")
    p.add_argument("--out", type=Path, required=True)
    p.set_defaults(func=cmd_make_contexts)
    p = sub.add_parser("summarize", help="status and token summary of a make-contexts JSONL")
    p.add_argument("jsonl", type=Path)
    p.set_defaults(func=cmd_summarize)
    a = ap.parse_args(argv)
    a.func(a)


if __name__ == "__main__":
    main()
