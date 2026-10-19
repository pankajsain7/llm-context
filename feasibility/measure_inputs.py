"""Measure input sizes and reconstruction fidelity on a JIT-Defect4J commit sample (feasibility evidence only).

Usage: python measure_inputs.py --root <scratch> --split valid --projects commons-codec commons-io --per-project 50
       [--defective-only]   (validation/train only: estimate eligibility among defective commits)
Expects <root>/jitfine/data/data/jitfine/features_<split>.pkl and clones at <root>/repos/<project>.
Labels are never read for the test split.
"""
import argparse
import pickle
import re
import statistics
import tempfile
import time
import warnings
from pathlib import Path

import pandas as pd

import context_demo as cd

warnings.filterwarnings("ignore")  # old pickles trigger numpy deprecation warnings


JAVA = ("--", "*.java", ":(exclude)*package-info.java")  # the scope of JIT-Defect4J's la/ld (feasibility/audit_dataset.py)
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? ")


def numstat(repo, parent, sha):
    added = deleted = 0
    for line in cd.git(repo, "diff", "--numstat", parent, sha, *JAVA).splitlines():
        a, d, _ = line.split("\t", 2)
        if a != "-":
            added, deleted = added + int(a), deleted + int(d)
    return added, deleted


def old_lines(diff):
    """Parent-side line numbers shown in each hunk of a unified diff, per parent path."""
    shown, path = {}, None
    for line in diff.splitlines():
        if line.startswith("--- "):
            path = None if line == "--- /dev/null" else line[6:]
        elif path and (m := HUNK.match(line)):
            start, count = int(m[1]), int(m[2] if m[2] is not None else 1)
            shown.setdefault(path, set()).update(range(start, start + count))
    return shown


def masked_tokens(blobs, keep):
    """Tokens of parent-file lines (license header stripped) selected by keep(path, line_no)."""
    total = 0
    for p, text in blobs.items():
        first, lines = cd.strip_header(text)
        total += cd.count_tokens("\n".join(l for n, l in enumerate(lines, first) if keep(p, n)))
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--split", default="valid")
    ap.add_argument("--projects", nargs="+", required=True)
    ap.add_argument("--per-project", type=int, default=50)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--bm25-timing", type=int, default=5, help="commits per project to time C2 construction")
    ap.add_argument("--defective-only", action="store_true")
    args = ap.parse_args()
    if args.split == "test" and args.defective_only:
        ap.error("test labels must not be used")

    with open(args.root / "jitfine/data/data/jitfine" / f"features_{args.split}.pkl", "rb") as f:
        feats = pickle.load(f)
    if args.defective_only:
        feats = feats[feats.is_buggy_commit == 1]
    attr = Path(tempfile.gettempdir()) / "java.attributes"
    attr.write_text("*.java diff=java\n")
    rows = []
    for project in args.projects:
        repo = args.root / "repos" / project
        sample = feats[feats.project == project].sample(n=min(args.per_project, (feats.project == project).sum()),
                                                        random_state=args.seed)
        for i, r in enumerate(sample.itertuples()):
            row = {"project": project, "sha": r.commit_hash, "la": int(r.la), "ld": int(r.ld)}
            if args.split != "test":
                row["label"] = int(r.is_buggy_commit)
            try:
                parent = cd.git(repo, "rev-parse", f"{r.commit_hash}^").strip()
                row["parent_ok"] = parent == r.parent_hashes
                row["numstat_ok"] = numstat(repo, parent, r.commit_hash) == (int(r.la), int(r.ld))
                diff = cd.git(repo, "diff", "-U3", "-M", parent, r.commit_hash, *JAVA)
                diff_w = cd.git(repo, "-c", f"core.attributesFile={attr}", "diff", "--function-context", "-M",
                                parent, r.commit_hash, *JAVA)
                row["t_c0"], row["t_w"] = cd.count_tokens(diff), cd.count_tokens(diff_w)
                shown, enclosing = old_lines(diff), old_lines(diff_w)
                blobs = cd.read_blobs(repo, parent, list(shown))
                not_shown = lambda p, n: n not in shown.get(p, ())
                row["t_local_pool"] = masked_tokens(blobs, not_shown)
                row["t_enclosing"] = masked_tokens(blobs, lambda p, n: not_shown(p, n) and n in enclosing.get(p, ()))
                if i < args.bm25_timing:
                    start = time.perf_counter()
                    changed = cd.git(repo, "diff", "--name-only", parent, r.commit_hash).split()
                    paths = [p for p in cd.git(repo, "ls-tree", "-r", "--name-only", parent).split()
                             if p.endswith(".java") and p not in changed]
                    docs = [c for p, t in cd.read_blobs(repo, parent, paths).items() for c in cd.chunk(p, t)]
                    query = "\n".join(l[1:] for l in diff.splitlines()
                                      if l[:1] in "+-" and not l.startswith(("+++", "---")))
                    order, scores = cd.bm25_rank(query, docs)
                    cd.fill(order, docs, 2000, scores)
                    row["c2_seconds"] = time.perf_counter() - start
                    row["pool_chunks"] = len(docs)
            except Exception as e:  # record and continue: failures are part of the measurement
                row["error"] = f"{type(e).__name__}: {str(e)[:80]}"
            rows.append(row)
    df = pd.DataFrame(rows)
    out = args.root / f"measure_{args.split}{'_defective' if args.defective_only else ''}.csv"
    df.to_csv(out, index=False)

    ok = df.dropna(subset=["t_c0"])
    churn = ok.la + ok.ld
    print(f"commits {len(df)}, errors {int(df.get('error', pd.Series(dtype=str)).notna().sum())}, "
          f"parent ok {ok.parent_ok.mean():.1%}, numstat ok {ok.numstat_ok.mean():.1%}")
    for col in ("t_c0", "t_w", "t_enclosing", "t_local_pool"):
        q = ok[col].quantile([.1, .25, .5, .75, .9, .95]).round(0).astype(int).to_dict()
        print(f"{col}: mean {ok[col].mean():.0f}, quantiles {q}")
    print(f"tokens per changed line (median over commits with churn>0): "
          f"{statistics.median(ok.t_c0[churn > 0] / churn[churn > 0]):.1f}")
    for cap in (8000, 12000):
        print(f"share with T(C0) <= {cap}: {(ok.t_c0 <= cap).mean():.1%}")
    for b in (1000, 2000, 4000):
        print(f"share with local pool >= {b}: {(ok.t_local_pool >= b).mean():.1%}")
    print(f"share with empty same-file pool (new files, or all lines shown in the diff): {(ok.t_local_pool == 0).mean():.1%}")
    if "c2_seconds" in ok:
        t = ok.c2_seconds.dropna()
        print(f"C2 build time per commit (n={len(t)}): median {t.median():.1f}s, max {t.max():.1f}s; "
              f"pool chunks median {ok.pool_chunks.dropna().median():.0f}")
    print("per project:")
    print(ok.groupby("project").agg(n=("sha", "size"), t_c0_median=("t_c0", "median"),
                                    t_local_pool_median=("t_local_pool", "median")).to_string())
    print(f"written {out}")


if __name__ == "__main__":
    main()
