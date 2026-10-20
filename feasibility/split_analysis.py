"""Evidence for the split interpretation (docs/02-datasets.md section 2 item 10). Train/validation labels only; test is
label-blind. Prototype measurement aid; no LLM.

  python feasibility/split_analysis.py --root <scratch>
"""
import argparse
import pickle
import random
import warnings
from pathlib import Path

import pandas as pd


def load(root: Path, split: str) -> pd.DataFrame:
    with warnings.catch_warnings(), open(root / "jitfine/data/data/jitfine" / f"features_{split}.pkl", "rb") as f:
        warnings.simplefilter("ignore")
        d = pickle.load(f)
    out = pd.DataFrame({"project": d.project, "commit": d.commit_hash, "split": split,
                        "t": pd.to_numeric(d.author_date_unix_timestamp).astype(int)})
    if split != "test":
        out["y"] = d.is_buggy_commit.astype(int).values
    return out


def auc(score: pd.Series, y: pd.Series) -> float:
    """Mann-Whitney AUC with ties counted half."""
    r = score.rank()
    n1 = int(y.sum())
    n0 = len(y) - n1
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--perms", type=int, default=2000)
    ap.add_argument("--boot", type=int, default=1000)
    a = ap.parse_args()
    d = pd.concat([load(a.root, s) for s in ("train", "valid", "test")], ignore_index=True)

    # 1. Position under a strict per-project 60/20/20 time split (rank by author time, then commit id)
    d = d.sort_values(["project", "t", "commit"])
    d["pos"] = d.groupby("project").cumcount() / d.groupby("project").commit.transform("size")
    d["strict"] = pd.cut(d.pos, [-1, 0.6, 0.8, 2], labels=["train", "valid", "test"], right=False).astype(str)
    print(f"in the strict 60/20/20 position: {(d.split == d.strict).mean():.3f} of all commits; test vs the rest "
          f"in the strict 80/20 position: {((d.pos >= 0.8) == (d.split == 'test')).mean():.3f}")
    test = d[d.split == "test"]

    # 2. Train + validation: which commits are out of time order, and their labels
    tv = d[d.split != "test"].copy()
    n_valid = tv[tv.split == "valid"].groupby("project").size()
    tv["rank_tv"] = tv.groupby("project").cumcount()
    tv["strict_tv"] = (tv.rank_tv >= tv.project.map(tv.groupby("project").size() - n_valid)).map(
        {True: "valid", False: "train"})
    into_valid = tv[(tv.split == "valid") & (tv.strict_tv == "train")]
    into_train = tv[(tv.split == "train") & (tv.strict_tv == "valid")]
    print(f"train+valid out of order: {len(into_valid) + len(into_train)}; moved into valid {len(into_valid)} "
          f"({into_valid.y.mean():.3f} defective), into train {len(into_train)} ({into_train.y.mean():.3f} defective)")
    v = tv[tv.split == "valid"]
    own = v[v.strict_tv == "valid"]
    print(f"validation period's own commits: {len(own)}, defect rate {own.y.mean():.3f}; defective validation "
          f"commits taken from the training period: {int(into_valid.y.sum())} of {int(v.y.sum())}")

    # 3. Per-project defect rates of train vs valid, against random splits of the same sizes
    def gap(frame):
        r = frame.groupby(["project", "split"]).y.mean().unstack()
        return (r.train - r.valid).abs().mean()
    observed = gap(tv)
    rng = random.Random(0)
    sizes = tv.groupby("project").split.value_counts().unstack()
    closer = 0
    perm_gaps = []
    for _ in range(a.perms):
        parts = []
        for p, g in tv.groupby("project"):
            idx = list(g.index)
            rng.shuffle(idx)
            k = int(sizes.loc[p, "valid"])
            parts.append(pd.Series(["valid"] * k + ["train"] * (len(idx) - k), index=idx))
        s = tv.assign(split=pd.concat(parts))
        g_ = gap(s)
        perm_gaps.append(g_)
        closer += g_ <= observed
    perm_gaps.sort()
    print(f"mean |train - valid| per-project defect rate: observed {observed * 100:.2f} pp; random splits median "
          f"{perm_gaps[len(perm_gaps) // 2] * 100:.2f} pp; random splits at least as close: {closer} of {a.perms}")

    # 4. Commit age predicts the validation label (older = higher score)
    within = [(1 - auc(g.t.rank(), g.y), g.y.sum()) for _, g in v.groupby("project") if 0 < g.y.sum() < len(g)]
    print(f"validation, commit age as the score: pooled AUC {auc(-v.t, v.y):.3f}; project-stratified AUC "
          f"(within-project AUCs weighted by defective count, design section 10) "
          f"{sum(x * n for x, n in within) / sum(n for _, n in within):.3f}; unweighted mean "
          f"{sum(x for x, _ in within) / len(within):.3f} over {len(within)} projects")

    # 5. Test, label-blind
    last_valid = d[d.split == "valid"].groupby("project").t.max()
    last_train = d[d.split == "train"].groupby("project").t.max()
    print(f"test commits before their project's 80th time percentile: {(test.pos < 0.8).sum()}; older than the "
          f"project's newest validation commit: {(test.t < test.project.map(last_valid)).sum()}; older than the newest "
          f"train commit: {(test.t < test.project.map(last_train)).sum()}")

    # 6. Supervised baselines trained on train, scored on validation: all, and the chronological window (validation
    #    commits in their strict time position, i.e. not moved there from the training period)
    raw = {s: _features(a.root, s) for s in ("train", "valid")}
    y_tr = raw["train"].is_buggy_commit.astype(int).values
    y_va = raw["valid"].is_buggy_commit.astype(int).reset_index(drop=True)
    window = raw["valid"].commit_hash.isin(set(own.commit)).values
    scores = {}
    for name, cols in (("Kamei 14", KAMEI), ("history/experience", ["ndev", "age", "nuc", "exp", "rexp", "sexp"]),
                       ("size, log(la+ld+1) (B1)", None)):
        score = pd.Series(_logit(_x(raw["train"], cols), y_tr)(_x(raw["valid"], cols)))
        scores[name] = score
        print(f"LR {name}: validation AUC {auc(score, y_va):.3f}; chronological window "
              f"{auc(score[window].reset_index(drop=True), y_va[window].reset_index(drop=True)):.3f} "
              f"(n={int(window.sum())}, defective {int(y_va[window].sum())})")

    # 7. How much project clustering widens the CI of a paired ΔAUC (design section 11): Kamei 14 minus B1 on validation
    s1, s0 = scores["Kamei 14"], scores["size, log(la+ld+1) (B1)"]
    proj = raw["valid"].project.reset_index(drop=True)
    delta = auc(s1, y_va) - auc(s0, y_va)
    rng = random.Random(1)
    groups = {k: list(g.index) for k, g in pd.DataFrame({"p": proj, "y": y_va}).groupby(["p", "y"])}
    by_proj = {p: list(g.index) for p, g in proj.groupby(proj)}
    reps = {"commits, stratified by project x label": [], "projects (cluster)": []}
    for _ in range(a.boot):
        i = [rng.choice(ix) for ix in groups.values() for _ in ix]
        j = [k for p in rng.choices(list(by_proj), k=len(by_proj)) for k in by_proj[p]]
        for name, idx in zip(reps, (i, j)):
            yy = y_va[idx].reset_index(drop=True)
            reps[name].append(auc(s1[idx].reset_index(drop=True), yy) - auc(s0[idx].reset_index(drop=True), yy))
    print(f"paired delta AUC (Kamei 14 - B1) on validation: {delta:.3f}")
    for name, r in reps.items():
        r.sort()
        print(f"  bootstrap over {name}: 95% CI {r[int(0.025 * len(r))]:.3f} to {r[int(0.975 * len(r)) - 1]:.3f}")


KAMEI = ["la", "ld", "nf", "ns", "nd", "entropy", "ndev", "lt", "nuc", "age", "exp", "rexp", "sexp", "fix"]


def _features(root: Path, split: str) -> pd.DataFrame:
    with warnings.catch_warnings(), open(root / "jitfine/data/data/jitfine" / f"features_{split}.pkl", "rb") as f:
        warnings.simplefilter("ignore")
        return pickle.load(f)


def _x(d: pd.DataFrame, cols):
    import numpy as np
    num = d[KAMEI].apply(pd.to_numeric, errors="coerce").astype(float).fillna(0).clip(lower=0)
    if cols is None:
        return np.log1p(num[["la", "ld"]].sum(axis=1).values)[:, None]
    return np.log1p(num[cols].values)


def _logit(x, y, steps=50, l2=1e-4):
    """Logistic regression (log1p features, standardised, tiny ridge) by Newton steps; returns a scoring function."""
    import numpy as np
    mu, sd = x.mean(0), x.std(0) + 1e-9
    z = np.c_[np.ones(len(x)), (x - mu) / sd]
    w = np.zeros(z.shape[1])
    for _ in range(steps):
        p = 1 / (1 + np.exp(-z @ w))
        w -= np.linalg.solve((z * (p * (1 - p))[:, None]).T @ z + l2 * np.eye(len(w)), z.T @ (p - y) + l2 * w)
    return lambda x2: np.c_[np.ones(len(x2)), (x2 - mu) / sd] @ w


if __name__ == "__main__":
    main()
