"""Label-free commit manifest with eligibility flags (design §8, decision D4).

This is the only module that opens the benchmark pickles. Labels are dropped from the manifest and written
to a separate file for the train and validation splits only; test labels are never written or returned.
"""
import pickle
import warnings
from pathlib import Path

import pandas as pd

from . import gitrepo
from .diffparse import parse
from .tokens import count_tokens

# Test records displayed with (or next to) their labels during feasibility work; list and caveats in
# docs/02-datasets.md §8. Excluding them is proposal D27.
INSPECTED_TEST_COMMITS = frozenset({"76c125c3b74a390a39cdcd6666cf7e9cea0e5c1d",
                                    "4063338a3c8c87657a75c3c45a8b69560fee0e57",
                                    "6e710a1f78a4a733020a4b2d1f07b6fe4c6684f0",
                                    "1f73722ffb375010e74eaa5b99004ad88df93bf6"})
LABEL_SPLITS = ("train", "valid")
SPLIT_ORDER = {"train": 0, "valid": 1, "test": 2}


def flag_duplicates(m: pd.DataFrame) -> pd.DataFrame:
    """Patch-id duplicate flags (design L8). `m` must be in chronological order.

    dup_keep: the first commit of each patch id within its split. dup_earlier_split: the patch also occurs in an
    earlier split (train < valid < test), so a model trained or tuned there has seen it; such commits are not
    eligible for evaluation (a validation copy of a training patch, a test copy of a training or validation patch).
    """
    grouped = m.dropna(subset=["patch_id"]).groupby("patch_id")
    rank = m.split.map(SPLIT_ORDER)
    first_split = m.patch_id.map(rank.groupby(m.patch_id).min())
    return m.assign(dup_group_size=m.patch_id.map(grouped.size()).fillna(1).astype(int),
                    dup_other_split=m.patch_id.map(grouped.split.nunique()).fillna(1) > 1,
                    dup_earlier_split=(first_split < rank).fillna(False).astype(bool),
                    dup_keep=~m.duplicated(subset=["patch_id", "split"]) | m.patch_id.isna())


def load_split(root: Path, split: str) -> tuple[pd.DataFrame, pd.Series | None]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # old pickles trigger numpy deprecation warnings
        with open(root / "jitfine/data/data/jitfine" / f"features_{split}.pkl", "rb") as f:
            feats = pickle.load(f)
    labels = feats.set_index("commit_hash").is_buggy_commit.astype(int) if split in LABEL_SPLITS else None
    meta = pd.DataFrame({"project": feats.project, "commit": feats.commit_hash, "ds_parent": feats.parent_hashes,
                         "split": split, "la": feats.la.astype(int), "ld": feats.ld.astype(int),
                         "author_time": pd.to_numeric(feats.author_date_unix_timestamp).astype(int)})
    del feats
    return meta, labels


def audit_commits(repo: Path, df: pd.DataFrame) -> list[dict]:
    """Reconstruction, Java-scope churn, C0 size, and patch id for the commits of one project."""
    stdin = "".join(f"{c}\n" for c in df.commit).encode()
    exists = {line.split()[0].decode(): not line.endswith(b"missing")
              for line in gitrepo.git(repo, "cat-file", "--batch-check", data=stdin).splitlines()}
    present = "".join(f"{c}\n" for c in df.commit if exists.get(c)).encode()
    parents = dict(line.split(" ", 1) for line in gitrepo.decode(gitrepo.git(
        repo, "log", "--no-walk=unsorted", "--stdin", "--format=%H %P", data=present)).splitlines())
    rows, patches = [], []
    for r in df.itertuples():
        row = {"commit": r.commit, "exists": exists.get(r.commit, False)}
        if row["exists"]:
            parent = parents[r.commit].split()[0] if parents[r.commit] else ""
            diff = gitrepo.java_diff(repo, parent, r.commit) if parent else ""
            files = parse(diff)
            la = sum(line[:1] == "+" for f in files for h in f.hunks for line in h.lines)
            ld = sum(line[:1] == "-" for f in files for h in f.hunks for line in h.lines)
            row.update(parent=parent, parent_ok=parents[r.commit] == r.ds_parent, numstat_ok=(la, ld) == (r.la, r.ld),
                       n_java_files=len(files), t_c0=count_tokens(diff))
            if diff:
                patches.append(f"commit {r.commit}\n{diff}")
        rows.append(row)
    ids = gitrepo.decode(gitrepo.git(repo, "patch-id", "--stable", data="".join(patches).encode()))
    pid = {c: p for p, c in (line.split() for line in ids.splitlines())}
    for row in rows:
        row["patch_id"] = pid.get(row["commit"])
    return rows


def build(root: Path, splits=("train", "valid", "test"), cap: int = 16000, log=print):
    metas, labels = [], []
    for split in splits:
        meta, lab = load_split(root, split)
        metas.append(meta)
        if lab is not None:
            labels.append(pd.DataFrame({"commit": lab.index, "split": split, "is_buggy_commit": lab.values}))
    m = pd.concat(metas, ignore_index=True)
    audited = []
    for project, df in m.groupby("project"):
        audited += audit_commits(root / "repos" / project, df)
        log(f"audited {project}: {len(df)} commits")
    m = m.merge(pd.DataFrame(audited), on="commit", how="left").drop(columns=["la", "ld"])
    m["recon_ok"] = m.exists & m.parent_ok.fillna(False).astype(bool) & m.numstat_ok.fillna(False).astype(bool)
    m["has_java_change"] = m.n_java_files.fillna(0) > 0
    m["within_cap"] = m.t_c0.fillna(cap + 1) <= cap
    m = flag_duplicates(m.sort_values(["author_time", "commit"]).reset_index(drop=True))
    m["inspected_test_record"] = m.commit.isin(INSPECTED_TEST_COMMITS)
    m["eligible"] = m.recon_ok & m.has_java_change & m.within_cap & m.dup_keep & ~m.dup_earlier_split
    lab = pd.concat(labels, ignore_index=True) if labels else pd.DataFrame(columns=["commit", "split", "is_buggy_commit"])
    return m.sort_values(["split", "project", "author_time", "commit"]).reset_index(drop=True), lab
