"""Recompute the dataset facts reported in docs/02-datasets.md.

Expected layout under --root (see docs/04-feasibility-demo.md for download commands):
  apachejit/apachejit_total.csv          from github.com/hosseinkshvrz/apachejit (dataset/)
  jitfine/data/data/jitfine/*.pkl        from github.com/jacknichao/JIT-Fine (data.zip)
"""
import argparse
import pickle
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")  # old pickles trigger numpy deprecation warnings
pd.set_option("display.width", 200)


def load_jit_defect4j(root):
    base = root / "jitfine" / "data" / "data" / "jitfine"
    frames = []
    for split in ("train", "valid", "test"):
        with open(base / f"features_{split}.pkl", "rb") as f:
            df = pickle.load(f).assign(split=split)
        with open(base / f"changes_{split}.pkl", "rb") as f:
            ids, labels, _msgs, _codes = pickle.load(f)
        agree = (df.commit_hash.map(dict(zip(ids, labels))) == df.is_buggy_commit).mean()
        print(f"[{split}] label agreement features vs changes pickle: {agree:.3f}")
        frames.append(df)
    d = pd.concat(frames, ignore_index=True)
    d["date"] = pd.to_datetime(pd.to_numeric(d.author_date_unix_timestamp), unit="s")
    d["churn"] = pd.to_numeric(d.la) + pd.to_numeric(d.ld)
    d["nf"] = pd.to_numeric(d.nf)
    return d


def report_jit_defect4j(d):
    print("\n=== JIT-Defect4J ===")
    print(f"commits {len(d)}, defective {int(d.is_buggy_commit.sum())} ({d.is_buggy_commit.mean():.2%}), "
          f"projects {d.project.nunique()}, duplicate hashes {int(d.commit_hash.duplicated().sum())}, "
          f"multi-parent commits {int(d.parent_hashes.astype(str).str.contains(',').sum())}")
    print(d.groupby("split").agg(n=("commit_hash", "size"), defective=("is_buggy_commit", "sum"),
                                 rate=("is_buggy_commit", "mean"), first=("date", "min"),
                                 last=("date", "max")).to_string())
    print(d.groupby("project").agg(n=("commit_hash", "size"), rate=("is_buggy_commit", "mean"),
                                   test_n=("split", lambda s: int((s == "test").sum()))).round(3).to_string())
    early = sum(int(((g.split == "test") & (g.date < g[g.split == "train"].date.max())).sum())
                for _, g in d.groupby("project"))
    print(f"test commits authored before their project's last train commit: {early} "
          f"of {int((d.split == 'test').sum())}")
    t = d[d.split == "test"]
    print("test churn quantiles:", t.churn.quantile([.5, .75, .9, .95, .99]).round(0).to_dict())
    for cap in (200, 400, 600):
        k = t[t.churn <= cap]
        print(f"test churn<={cap}: keeps {len(k) / len(t):.1%} of commits, "
              f"{int(k.is_buggy_commit.sum())}/{int(t.is_buggy_commit.sum())} defective")
    print("defect rate by churn quintile:")
    print(d.groupby(pd.qcut(d.churn, 5, duplicates="drop"))["is_buggy_commit"].mean().round(3).to_string())


def report_apachejit(root):
    a = pd.read_csv(root / "apachejit" / "apachejit_total.csv")
    a["churn"] = a.la + a.ld
    print("\n=== ApacheJIT ===")
    print(f"commits {len(a)}, columns {list(a.columns)}")
    print(f"buggy {int(a.buggy.sum())} ({a.buggy.mean():.2%}), duplicate ids {int(a.commit_id.duplicated().sum())}")
    print(a.groupby("project")["buggy"].agg(["count", "mean"]).round(3).to_string())
    print(a.groupby("year")["buggy"].agg(["count", "mean"]).round(3).to_string())
    print("defect rate by churn quintile:")
    print(a.groupby(pd.qcut(a.churn, 5, duplicates="drop"))["buggy"].mean().round(3).to_string())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    root = ap.parse_args().root
    report_jit_defect4j(load_jit_defect4j(root))
    report_apachejit(root)
