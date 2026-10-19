"""Integrity audit of JIT-Defect4J against the original Apache Git repositories (feasibility evidence).

Usage: python audit_dataset.py --root <scratch>
Per commit: object exists, first parent equals parent_hashes, Java-only numstat equals la/ld, Git author
and committer times, Java-only patch-id, and the size of the Java-only C0 diff (o200k tokens). For
validation commits it also sizes the same-file pool (license header stripped, diff lines masked).
Labels are read only for class-specific figures on train and validation; test labels are never loaded.
Writes <root>/audit_commits.csv without labels.
"""
import argparse
import pickle
import re
import subprocess
import warnings
from pathlib import Path

import pandas as pd

import context_demo as cd
from measure_inputs import JAVA, masked_tokens, old_lines

warnings.filterwarnings("ignore")  # old pickles trigger numpy deprecation warnings
SHA = re.compile(rb"^[0-9a-f]{40}$")
COLS = ["project", "commit_hash", "parent_hashes", "la", "ld", "author_date_unix_timestamp"]


def git(repo, args, data=b""):
    return subprocess.run([cd.GIT, *args], cwd=repo, input=data, capture_output=True, check=True).stdout


def blocks(out):
    """Split `git diff-tree --stdin` output into {sha: text}."""
    res, sha, buf = {}, None, []
    for line in out.split(b"\n"):
        if SHA.match(line):
            if sha:
                res[sha] = b"\n".join(buf)
            sha, buf = line.decode(), []
        else:
            buf.append(line)
    if sha:
        res[sha] = b"\n".join(buf)
    return res


def audit_project(repo, df):
    shas = "\n".join(df.commit_hash).encode() + b"\n"
    exists = {l.split()[0].decode(): not l.endswith(b"missing")
              for l in git(repo, ["cat-file", "--batch-check"], shas).splitlines()}
    ok = [s for s in df.commit_hash if exists.get(s)]
    stdin = "\n".join(ok).encode() + b"\n"
    meta = {}
    for line in git(repo, ["log", "--no-walk=unsorted", "--stdin", "--format=%H|%P|%at|%ct"], stdin).decode().splitlines():
        h, p, at, ct = line.split("|")
        meta[h] = (p, int(at), int(ct))
    numstat = {}
    for sha, text in blocks(git(repo, ["diff-tree", "--stdin", "-r", "-M", "--numstat", *JAVA], stdin)).items():
        a = d = 0
        for row in text.decode(errors="replace").splitlines():
            x, y, _ = row.split("\t", 2)
            if x != "-":
                a, d = a + int(x), d + int(y)
        numstat[sha] = (a, d)
    patch = git(repo, ["diff-tree", "--stdin", "-r", "-M", "-p", *JAVA], stdin)
    pid = {c.decode(): p.decode() for p, c in (l.split() for l in git(repo, ["patch-id", "--stable"], patch).splitlines())}
    diffs = {s: t.decode("utf-8", errors="replace") for s, t in blocks(patch).items()}
    rows = []
    for r in df.itertuples():
        row = {"project": r.project, "sha": r.commit_hash, "split": r.split, "exists": bool(exists.get(r.commit_hash))}
        if row["exists"]:
            parents, at, ct = meta[r.commit_hash]
            diff = diffs.get(r.commit_hash, "")
            row.update(parent_ok=parents == r.parent_hashes, n_parents=len(parents.split()),
                       numstat_ok=numstat.get(r.commit_hash, (0, 0)) == (int(r.la), int(r.ld)),
                       git_at=at, git_ct=ct, ds_at=int(float(r.author_date_unix_timestamp)),
                       t_c0=cd.count_tokens(diff), patch_id=pid.get(r.commit_hash))
            if r.split == "valid" and diff:
                shown = old_lines(diff)
                blobs = cd.read_blobs(repo, r.parent_hashes, list(shown))
                row["t_local_pool"] = masked_tokens(blobs, lambda p, n: n not in shown.get(p, ()))
        rows.append(row)
    return rows


def share(s, cond):
    return f"{cond.sum()}/{len(s)} ({cond.mean():.1%})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    args = ap.parse_args()
    base = args.root / "jitfine/data/data/jitfine"
    frames, labels = [], {}
    for split in ("train", "valid", "test"):
        with open(base / f"features_{split}.pkl", "rb") as f:
            feats = pickle.load(f)
        frames.append(feats[COLS].assign(split=split))
        if split != "test":
            labels.update(zip(feats.commit_hash, feats.is_buggy_commit.astype(int)))
    data = pd.concat(frames, ignore_index=True)
    rows = []
    for project, df in data.groupby("project"):
        repo = args.root / "repos" / project
        if not repo.exists():
            rows += [{"project": project, "sha": s, "split": sp, "exists": False}
                     for s, sp in zip(df.commit_hash, df.split)]
            continue
        rows += audit_project(repo, df)
        print(f"audited {project}: {len(df)} commits", flush=True)
    a = pd.DataFrame(rows)
    a.to_csv(args.root / "audit_commits.csv", index=False)

    a["recon_ok"] = a.exists & a.parent_ok.fillna(False).astype(bool) & a.numstat_ok.fillna(False).astype(bool)
    print("\n== Reconstruction (exists, first parent, Java-only numstat = la/ld)")
    for split, s in a.groupby("split", sort=False):
        print(f"{split}: ok {share(s, s.recon_ok)}; missing {(~s.exists).sum()}; "
              f"parent mismatch {(s.exists & ~s.parent_ok.fillna(True).astype(bool)).sum()}; "
              f"numstat mismatch {(s.exists & ~s.numstat_ok.fillna(True).astype(bool)).sum()}; "
              f"merge commits {(s.n_parents > 1).sum()}")
    bad = a[~a.recon_ok].groupby("project").size()
    print("failures by project:", bad.to_dict() if len(bad) else "none")

    e = a[a.exists]
    print("\n== Dates")
    print(f"dataset author time equals Git author time: {share(e, e.ds_at == e.git_at)}")
    for col, name in (("git_at", "author"), ("git_ct", "committer")):
        last_train = e[e.split == "train"].groupby("project")[col].max()
        for split in ("valid", "test"):
            s = e[e.split == split]
            early = s[col] < s.project.map(last_train)
            print(f"{split} commits older than their project's newest train commit by {name} time: "
                  f"{share(s, early)}; projects affected {s[early].project.nunique()}")
    first_test = e[e.split == "test"].groupby("project").git_ct.min()
    s = e[e.split == "train"]
    print(f"train commits newer than their project's oldest test commit by committer time: "
          f"{share(s, s.git_ct > s.project.map(first_test))}")

    print("\n== Duplicate Java changes (git patch-id --stable)")
    p = e.dropna(subset=["patch_id"])
    groups = p.groupby("patch_id").filter(lambda g: len(g) > 1)
    print(f"commits with a Java patch: {len(p)}; commits sharing a patch-id with another commit: {len(groups)} "
          f"in {groups.patch_id.nunique()} groups")
    cross = groups.groupby("patch_id").split.agg(lambda x: "+".join(sorted(set(x))))
    print("groups by splits involved:", cross.value_counts().to_dict())
    print(f"commits without any Java change: {(e.t_c0 == 0).sum()}")

    print("\n== Size of the Java-only C0 diff (o200k tokens), label-blind")
    for split, s in e.groupby("split", sort=False):
        q = s.t_c0.quantile([.5, .9, .95]).astype(int).tolist()
        print(f"{split}: median/p90/p95 {q}; <=8k {(s.t_c0 <= 8000).mean():.1%}; <=12k {(s.t_c0 <= 12000).mean():.1%}; "
              f"<=16k {(s.t_c0 <= 16000).mean():.1%}")
    e = e.assign(label=e.sha.map(labels))
    print("class-specific (train and valid only):")
    for split in ("train", "valid"):
        for lab, s in e[e.split == split].groupby("label"):
            print(f"  {split} label={lab}: n {len(s)}; <=8k {(s.t_c0 <= 8000).mean():.1%}; "
                  f"<=12k {(s.t_c0 <= 12000).mean():.1%}; <=16k {(s.t_c0 <= 16000).mean():.1%}")

    v = e[(e.split == "valid") & (e.t_c0 > 0)]
    print("\n== Same-file pool on validation commits (header stripped, diff lines masked)")
    for lab, s in [("all", v), *v.groupby("label")]:
        print(f"  {lab}: n {len(s)}; >=1k {(s.t_local_pool >= 1000).mean():.1%}; >=2k {(s.t_local_pool >= 2000).mean():.1%}; "
              f">=4k {(s.t_local_pool >= 4000).mean():.1%}; empty {(s.t_local_pool == 0).mean():.1%}")


if __name__ == "__main__":
    main()
