"""Label-quality audit evidence for defective JIT-Defect4J *validation* commits (Gate 1, decision D26).

Usage: python label_audit.py --root <scratch> [--n 30] [--seed 2026] [--jira]
       python label_audit.py --root <scratch> --recheck <project>:<sha> ...   (exhaustive check of single cases)
For each sampled bug-inducing commit (BIC) this script searches later history for commits whose deleted
lines `git blame` back to the BIC (forward SZZ; commits touching more than 30 files are skipped), lists their
Jira keys, optionally fetches the issue type and creation date from the public Apache Jira, and flags two
mechanical warning signs:
  * the BIC is newer than the issue report (it cannot have introduced that bug);
  * every substantive linked BIC line already existed before the BIC, in the same file or in code the BIC
    deleted elsewhere (reformatting or moving).
The search is deliberately limited and can miss the fix that produced the label: at most 400 later commits that
touch the BIC's files, at most 5 links, commits touching more than 30 files skipped, history before 2020 only,
renames after the BIC not followed (package renames end the trail), plain `git blame` (no -w/-M/-C), and only
the files the BIC added lines to. A missing or contradicting link is therefore not proof that a label is wrong.
Outputs go to <root>/label_audit/ (they reveal validation labels, so they stay outside Git):
audit.csv and one evidence file per commit for the manual rating. Uses later history: analysis only.
Never use on the test split.
"""
import argparse
import csv
import hashlib
import json
import pickle
import random
import re
import shutil
import subprocess
import urllib.request
import warnings
from pathlib import Path

GIT = r"C:\Program Files\Git\cmd\git.exe"
JAVA = ["--", "*.java", ":(exclude)*package-info.java"]
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
KEY = re.compile(r"\b([A-Z][A-Z0-9]+-\d+)\b")
MASS_CHANGE = 30  # later commits touching more files are skipped
SEARCH_LIMITS = ("Existing forward search: at most 400 later commits, 5 links, 30 files per later commit; "
                 "history before 2020; plain blame; no following later renames; only candidate-added files. "
                 "No fresh search or issue fetch in packet preparation. Missing evidence is not a false label.")


def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def prepare_human(root, manifest, out):
    """Keep the original 30 IDs/evidence, add blank independent rating sheets; no pickle or network access."""
    source = root / "label_audit"
    with (source / "audit.csv").open(encoding="utf-8-sig", newline="") as f:
        cases = sorted(csv.DictReader(f), key=lambda x: (x["bic"], x["project"]))
    if len(cases) != 30 or len({(r["project"], r["bic"]) for r in cases}) != 30:
        raise ValueError("Expected the original 30 unique label-audit cases; do not resample")
    with manifest.open(encoding="utf-8-sig", newline="") as f:
        valid = {(r["project"], r["commit"]) for r in csv.DictReader(f) if r["split"] == "valid"}
    if any((r["project"], r["bic"]) not in valid for r in cases):
        raise ValueError("Every existing label-audit ID must be a validation commit")
    evidence = [source / f"{r['project']}_{r['bic'][:10]}.md" for r in cases]
    if not all(p.is_file() for p in evidence):
        raise ValueError("Missing original evidence; do not silently replace cases")
    verdict_heading = re.compile(r"(?im)^\s*(?:#{1,6}\s*)?(?:rating|verdict|classification|prior AI|AI.assisted rating)\b")
    if any(verdict_heading.search(p.read_text(encoding="utf-8")) for p in evidence):
        raise ValueError("Original evidence contains rating/verdict headings; sanitize separately before blinding")
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite packet or ratings: {out}")
    # Select before any rating is supplied; sorted SHA then project, seed fixed by the protocol.
    second = set(random.Random(2027).sample(range(30), 10))
    out.mkdir(parents=True)
    instructions = ("# Independent validation label-evidence review\n\n"
        "EVALUATION ONLY. This packet contains later fixes and issue information. Never supply it to "
        "retrieval, prompts, or model execution. No human ratings have been filled in.\n\n"
        "Review at most 20 minutes per case. Rate P: the candidate wrote code a later bug fix corrects; "
        "F: the fix touches code the candidate only reformatted/moved/refactored; T: the linked bug was "
        "reported before the candidate; N: no bug fix among the available links; U: unclear. If several "
        "categories apply, choose the best-supported one and explain overlap. These are evidence judgements, "
        "not replacement benchmark labels. Record exact paths/lines, fix/issue references and uncertainty.\n\n"
        + SEARCH_LIMITS + " Existing evidence may contain abbreviated patches; complete local Java patches "
        "for the candidate and already-linked commits are supplied. No additional links were searched.\n\n"
        "Work independently. Do not see another rater's sheet, prior AI verdicts, model outputs or aggregate "
        "rating counts. Record rater_id, role (human/AI), UTC completion time and elapsed minutes. The "
        "independent10 packet must be rated by a human. Keep submitted sheets immutable; adjudicate "
        "separately afterward. Do not infer an overall label-error rate from this audit.\n")
    fields = ["case_id", "project", "candidate", "parent", "evidence_dir", "linked_fixes", "issue_keys",
              "search_limits", "rater_id", "rater_role", "category", "supporting_paths_lines",
              "supporting_fix_issue_refs", "rationale", "uncertainty", "minutes", "completed_utc"]
    sheets = {"primary30": [], "independent10": []}
    for name in sheets:
        (out / name).mkdir()
        (out / name / "README.md").write_bytes(instructions.encode("utf-8"))
    for i, (case, original) in enumerate(zip(cases, evidence)):
        case_id, repo = f"L{i + 1:02d}", root / "repos" / case["project"]
        parent = git(repo, "rev-parse", f"{case['bic']}^").strip()
        if not re.fullmatch(r"[0-9a-f]{40}", parent):
            raise ValueError("Candidate parent is not a full SHA")
        text = original.read_text(encoding="utf-8")
        links = list(dict.fromkeys(re.findall(r"^## Linked later commit ([0-9a-f]{40})", text, re.MULTILINE)))
        row = dict.fromkeys(fields, "")
        row.update(case_id=case_id, project=case["project"], candidate=case["bic"], parent=parent,
                   evidence_dir=case_id, linked_fixes=";".join(links), issue_keys=case.get("keys", ""),
                   search_limits=SEARCH_LIMITS)
        dest = out / "primary30" / case_id
        dest.mkdir()
        shutil.copyfile(original, dest / "existing_evidence.md")
        (dest / "candidate.diff").write_bytes(git(repo, "diff", "-U3", parent, case["bic"], *JAVA).encode("utf-8"))
        for sha in links:
            (dest / f"linked_{sha}.diff").write_bytes(
                git(repo, "diff", "-U3", f"{sha}^", sha, *JAVA).encode("utf-8"))
        sheets["primary30"].append(row)
        if i in second:
            shutil.copytree(dest, out / "independent10" / case_id)
            sheets["independent10"].append(row.copy())
    for name, rows in sheets.items():
        write_csv(out / name / "ratings.csv", rows, fields)
    provenance = {
        "purpose": "evaluation_only_human_audit_preparation_no_ratings",
        "selection": "existing30 sorted candidate SHA then project; independent10 Random(2027).sample",
        "historical_ratings": "Only historical aggregate AI ratings existed; no per-case ratings reconstructed.",
        "source_audit_sha256": hashlib.sha256((source / "audit.csv").read_bytes()).hexdigest(),
        "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "original_evidence_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in evidence},
        "files_sha256": {p.relative_to(out).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in sorted(out.rglob("*")) if p.is_file()},
    }
    (out / "provenance.json").write_bytes((json.dumps(provenance, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    print(f"Prepared 30 primary and 10 independent blank label ratings: {out}")


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
                for m in re.finditer(r"^([0-9a-f]{40}) (\d+) (\d+)", blame, re.MULTILINE):
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


def recheck(repo, bic):
    """Exhaustive variant of `linked_commits` for one candidate (no scan, link, or file-count limits), with
    whitespace- and move-aware blame counts per link and a line-break-insensitive test of whether the linked lines
    already existed in the code the candidate deleted. Renames after the candidate are still not followed."""
    global MASS_CHANGE
    saved, MASS_CHANGE = MASS_CHANGE, 10**9
    try:
        added, _, links = linked_commits(repo, bic, max_scan=10**9, max_links=10**9)
    finally:
        MASS_CHANGE = saved
    removed = "".join(norm(t) for hs in hunks(git(repo, "diff", "-U0", f"{bic}^", bic, *JAVA)).values()
                      for h in hs for _, t in h["old"])
    print(f"{bic[:10]}: {len(links)} linked later commits")
    for link in links:
        c, counts = link["commit"], {}
        for opts in ((), ("-w",), ("-w", "-M", "-C")):
            n = 0
            for hs in hunks(git(repo, "diff", "-U0", f"{c}^", c, "--", *added)).values():
                for h in hs:
                    if h["old"] and h["old_path"] in added:
                        blame = git(repo, "blame", "--porcelain", *opts, "-L", f"{h['old'][0][0]},{h['old'][-1][0]}",
                                    f"{c}^", "--", h["old_path"], check=False)
                        n += sum(m[1] == bic for m in re.finditer(r"^([0-9a-f]{40}) \d+ \d+", blame, re.MULTILINE))
            counts[" ".join(opts) or "plain"] = n
        texts = [t for t in (norm(added.get(x["path"], {}).get(x["line"], "")) for x in link["lines"]) if len(t) >= 8]
        issues = {k: jira(k) for k in link["keys"]}
        print(f"  {c[:10]} {link['subject'][:70]!r} keys {issues}\n    lines blamed to the candidate {counts}; "
              f"every substantive linked line already in the candidate's deleted code (ignoring all whitespace, "
              f"including line breaks): {bool(texts) and all(t in removed for t in texts)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--jira", action="store_true")
    ap.add_argument("--recheck", nargs="+", metavar="PROJECT:SHA", help="exhaustive re-check of single candidates")
    ap.add_argument("--prepare-human", type=Path, metavar="NEW_OUTPUT_DIR",
                    help="prepare existing30/independent10 human packets; no new search, labels or network")
    ap.add_argument("--manifest", type=Path, help="train/validation manifest verifying existing audit IDs")
    args = ap.parse_args()
    if args.prepare_human:
        if not args.manifest:
            ap.error("--prepare-human requires --manifest")
        prepare_human(args.root, args.manifest, args.prepare_human)
        return
    if args.recheck:
        for item in args.recheck:
            project, sha = item.split(":")
            repo = args.root / "repos" / project
            recheck(repo, git(repo, "rev-parse", sha).strip())
        return
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
                f.writelines(f"- BIC line {x['path']}:{x['line']} `{added.get(x['path'], {}).get(x['line'], '?').strip()}`"
                            f" -> replaced by {[t.strip() for t in x['fix_new'][:4]]}\n" for x in link["lines"][:15])
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
