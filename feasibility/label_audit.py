"""Label-quality audit evidence for defective JIT-Defect4J *validation* commits (Gate 1, decision D26).

Usage: python label_audit.py --root <scratch> [--n 30] [--seed 2026] [--jira]
For each sampled bug-inducing commit (BIC) this script searches later history for commits whose deleted
lines `git blame` back to the BIC (forward SZZ; commits touching more than 30 files are skipped), lists their
Jira keys, optionally fetches the issue type and creation date from the public Apache Jira, and flags two
mechanical warning signs:
  * the BIC is newer than the issue report (it cannot have introduced that bug);
  * every substantive linked BIC line already existed before the BIC, in the same file or in code the BIC
    deleted elsewhere (reformatting or moving).
Outputs go to <root>/label_audit/ (they reveal validation labels, so they stay outside Git):
audit.csv and one evidence file per commit for the manual rating. Uses later history: analysis only.
Never use on the test split.
"""
import argparse
import csv
import json
import pickle
import re
import subprocess
import urllib.request
import warnings
from pathlib import Path

GIT = r"C:\Program Files\Git\cmd\git.exe"
JAVA = ["--", "*.java", ":(exclude)*package-info.java"]
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
KEY = re.compile(r"\b([A-Z][A-Z0-9]+-\d+)\b")
MASS_CHANGE = 30  # later commits touching more files are skipped


def git(repo, *args, check=True):
    return subprocess.run([GIT, "-c", "core.quotePath=false", *args], cwd=repo, capture_output=True,
                          check=check).stdout.decode("utf-8", errors="replace")


def hunks(diff):
    """{path: [hunk]}; each hunk holds numbered deleted ('old') and added ('new') lines, counted from its header."""
    out, old, new, cur, left = {}, None, None, None, [0, 0]
    for line in diff.split("\n"):
        if left[0] or left[1]:
            if line[:1] == "-":
                cur["old"].append((cur["o"] + len(cur["old"]), line[1:]))
                left[0] -= 1
            elif line[:1] == "+":
                cur["new"].append((cur["n"] + len(cur["new"]), line[1:]))
                left[1] -= 1
        elif line.startswith("--- "):
            old = None if line[4:] == "/dev/null" else line[6:]
        elif line.startswith("+++ "):
            new = None if line[4:] == "/dev/null" else line[6:]
        elif m := HUNK.match(line):
            cur = {"old_path": old, "new_path": new, "old": [], "new": [], "o": int(m[1]), "n": int(m[3])}
            left = [int(m[2]) if m[2] is not None else 1, int(m[4]) if m[4] is not None else 1]
            out.setdefault(new or old, []).append(cur)
    return out


def norm(s):
    return re.sub(r"\s+", "", s)


def linked_commits(repo, bic, max_scan=400, max_links=5):
    """Later non-merge commits whose deleted Java lines blame to `bic`, with the linked lines."""
    added, deleted = {}, set()
    for hs in hunks(git(repo, "diff", "-U0", f"{bic}^", bic, *JAVA)).values():
        for h in hs:
            deleted.update(norm(t) for _, t in h["old"])
            if h["new_path"]:
                added.setdefault(h["new_path"], {}).update(dict(h["new"]))
    if not added:
        return added, deleted, []
    revs = git(repo, "rev-list", "--reverse", "--no-merges", "--before=2020-01-01", f"{bic}..HEAD", "--", *added).split()
    links = []
    for c in revs[:max_scan]:
        if len(git(repo, "diff-tree", "-r", "--name-only", "--no-commit-id", c).split()) > MASS_CHANGE:
            continue  # package renames, license or checkstyle sweeps: they delete every line and say nothing
        hit = []
        for hs in hunks(git(repo, "diff", "-U0", f"{c}^", c, "--", *added)).values():
            for h in hs:
                if not h["old"] or h["old_path"] not in added:
                    continue
                a, b = h["old"][0][0], h["old"][-1][0]
                blame = git(repo, "blame", "--porcelain", "-L", f"{a},{b}", f"{c}^", "--", h["old_path"], check=False)
                for m in re.finditer(r"^([0-9a-f]{40}) (\d+) (\d+)", blame, re.M):
                    if m[1] == bic:
                        hit.append({"path": h["old_path"], "line": int(m[2]), "fix_new": [t for _, t in h["new"]]})
        if hit:
            msg = git(repo, "log", "-1", "--format=%at%n%s%n%b", c)
            at, subject, body = (msg.split("\n", 2) + ["", ""])[:3]
            links.append({"commit": c, "time": int(at), "subject": subject, "keys": sorted(set(KEY.findall(subject + body))),
                          "lines": hit})
            if len(links) >= max_links:
                break
    return added, deleted, links


def jira(key):
    url = f"https://issues.apache.org/jira/rest/api/2/issue/{key}?fields=issuetype,created,summary"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            f = json.load(r)["fields"]
        return {"type": f["issuetype"]["name"], "created": f["created"], "summary": f["summary"]}
    except Exception as e:  # noqa: BLE001 - a missing issue is recorded, not fatal
        return {"error": type(e).__name__}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--jira", action="store_true")
    args = ap.parse_args()
    import pandas as pd

    with warnings.catch_warnings(), open(args.root / "jitfine/data/data/jitfine/features_valid.pkl", "rb") as fh:
        warnings.simplefilter("ignore")
        feats = pickle.load(fh)
    sample = feats[feats.is_buggy_commit == 1].sample(n=args.n, random_state=args.seed)
    out = args.root / "label_audit"
    out.mkdir(exist_ok=True)
    rows = []
    for r in sample.itertuples():
        repo = args.root / "repos" / r.project
        bic_time = int(float(r.author_date_unix_timestamp))
        added, deleted, links = linked_commits(repo, r.commit_hash)
        parent_text = {}
        for path in added:
            parent_text[path] = {norm(x) for x in git(repo, "show", f"{r.commit_hash}^:{path}", check=False).split("\n")}
        issues = {}
        if args.jira:
            for k in sorted({k for link in links for k in link["keys"]}):
                issues[k] = jira(k)
        lines = [norm(added.get(x["path"], {}).get(x["line"], "")) + "\0" + x["path"] for link in links for x in link["lines"]]
        lines = [(t, p) for t, p in (s.split("\0") for s in lines) if len(t) >= 8]  # skip braces, blank lines, @Override
        # every substantive linked line already existed before the BIC: in the same file, or in code the BIC deleted (moved)
        reformatted = bool(lines) and all(t in parent_text.get(p, set()) or t in deleted for t, p in lines)
        created = [pd.Timestamp(v["created"]).timestamp() for v in issues.values() if "created" in v]
        rows.append({
            "project": r.project, "bic": r.commit_hash, "bic_date": pd.Timestamp(bic_time, unit="s").date(),
            "bic_subject": str(r.commit_message)[:120], "la": r.la, "ld": r.ld, "n_links": len(links),
            "first_link": links[0]["commit"] if links else "", "first_link_subject": links[0]["subject"][:120] if links else "",
            "keys": " ".join(sorted({k for link in links for k in link["keys"]})),
            "issue_types": " ".join(sorted({v.get("type", "?") for v in issues.values()})),
            "bic_after_all_reports": bool(created) and bic_time > max(created),
            "linked_lines_preexisting": reformatted})
        with open(out / f"{r.project}_{r.commit_hash[:10]}.md", "w", encoding="utf-8") as f:
            f.write(f"# {r.project} {r.commit_hash}\n\nBIC {rows[-1]['bic_date']}: {r.commit_message}\n\n")
            f.write("## BIC diff (-U0, Java)\n```diff\n" + git(repo, "diff", "-U0", f"{r.commit_hash}^", r.commit_hash, *JAVA)[:6000]
                    + "\n```\n")
            for link in links:
                f.write(f"\n## Linked later commit {link['commit']} ({pd.Timestamp(link['time'], unit='s').date()})\n"
                        f"{link['subject']}\nKeys: {link['keys']}\n")
                for x in link["lines"][:15]:
                    f.write(f"- BIC line {x['path']}:{x['line']} `{added.get(x['path'], {}).get(x['line'], '?').strip()}`"
                            f" -> replaced by {[t.strip() for t in x['fix_new'][:4]]}\n")
            for k, v in issues.items():
                f.write(f"\nJira {k}: {v}\n")
        print(f"{r.project} {r.commit_hash[:10]} links={len(links)} keys={rows[-1]['keys']} "
              f"after_report={rows[-1]['bic_after_all_reports']} reformatted={reformatted}", flush=True)
    with open(out / "audit.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
