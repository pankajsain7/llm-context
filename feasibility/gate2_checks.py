"""Gate 2 checks on validation commits (no LLM, no labels). Prototype measurement aid, see docs/04 §5.7.

  python feasibility/gate2_checks.py ranges    --root <scratch> [--n 40] [--seed 7]   tree-sitter vs git -W
  python feasibility/gate2_checks.py relevance --contexts <make-contexts JSONL> --repos <scratch>/repos

ranges: for sampled modified Java files, compares the parent-side lines of each `git diff -W` (function context,
Git's built-in java driver) hunk with jitctx's tree-sitter enclosing lines for the change anchors in that hunk.
Lines in only one of the two that are blank, comments, annotations, or braces are ignored; anything else is
printed for manual inspection.

relevance: design §5.7 automated proxy. A C2/C3 snippet is "related" if it contains a method name called or
declared (`name(`) or a type name (PascalCase) from the changed lines (at least 4 characters, minus Java keywords
and a short list of ubiquitous JDK names). Reports the paired per-commit share of related snippets for C2 vs C3
and an exact sign test (stdlib; the design's Wilcoxon needs scipy, which is not installed). The proxy is lexical,
like BM25 itself, so it checks the manipulation, not usefulness; the blinded manual rating (design §5.7) remains
necessary.
"""
import argparse
import json
import random
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from jitctx import gitrepo
from jitctx.diffparse import change_anchors, parse
from jitctx.java import enclosing_lines, split_lines

TRIVIAL = re.compile(r"^\s*(|//.*|/\*.*|\*.*|@\w+.*|[{}();]+)\s*$")
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))?")


def git_function_ranges(repo, parent, sha, path, attrs):
    out = gitrepo.decode(gitrepo.git(repo, "-c", f"core.attributesFile={attrs}", "diff", "-W", "--no-color",
                                     parent, sha, "--", path))
    ranges = []
    for line in out.split("\n"):
        if m := HUNK.match(line):
            start, length = int(m[1]), int(m[2]) if m[2] is not None else 1
            ranges.append(range(start, start + length))
    return ranges


def cmd_ranges(a):
    import pandas as pd
    attrs = Path(tempfile.gettempdir()) / "jitctx_java.gitattributes"
    attrs.write_text("*.java diff=java\n")
    m = pd.read_csv(a.manifest)
    rows = m[(m.split == "valid") & m.eligible].sort_values("commit").to_dict("records")
    rng = random.Random(a.seed)
    rng.shuffle(rows)
    n_cases, agree, outside, report = 0, 0, 0, []
    for r in rows:
        if n_cases >= a.n:
            break
        repo = a.root / "repos" / r["project"]
        files = [f for f in parse(gitrepo.java_diff(repo, r["parent"], r["commit"])) if f.old_path and f.new_path
                 and f.old_path == f.new_path and f.hunks]
        if not files:
            continue
        f = rng.choice(files)  # one file per commit, for diversity
        text = gitrepo.read_blobs(repo, r["parent"], [f.old_path])[f.old_path]
        lines = split_lines(text)
        anchors = change_anchors(f)
        for g in git_function_ranges(repo, r["parent"], r["commit"], f.old_path, attrs):
            inside = {x for x in anchors if x in g}
            if not inside:
                continue
            n_cases += 1
            ts = enclosing_lines(text, inside)
            gl = set(g)
            only = sorted(x for x in ts ^ gl if 1 <= x <= len(lines) and not TRIVIAL.match(lines[x - 1]))
            in_method = all(x in ts and min(ts) <= x for x in inside) and ts and max(ts) - min(ts) + 1 == len(ts)
            if not in_method:
                outside += 1
            if not only:
                agree += 1
            report.append(f"{r['project']} {r['commit'][:10]} {f.old_path.split('/')[-1]} anchors {min(inside)}-"
                          f"{max(inside)} ts {min(ts) if ts else '-'}-{max(ts) if ts else '-'} ({len(ts)} lines)"
                          f" git {g.start}-{g.stop - 1} {'AGREE' if not only else 'DIFF ' + str(len(only))}"
                          f"{'' if in_method else ' [outside-method]'}")
            for x in only[:6] if only else []:
                side = "ts-only " if x in ts else "git-only"
                report.append(f"      {side} {x}: {lines[x - 1].strip()[:100]}")
            if n_cases >= a.n:
                break
    print("\n".join(report))
    print(f"\ncases {n_cases}: agree {agree}, differ {n_cases - agree} (non-trivial lines), "
          f"tree-sitter fell back to the type outline in {outside}")


KEYWORDS = set("""abstract assert boolean break byte case catch char class const continue default do double else enum
extends final finally float for goto if implements import instanceof int interface long native new package private
protected public return short static strictfp super switch synchronized this throw throws transient try void volatile
while true false null var record yield String Object Integer Long Boolean List Map Set Collection Iterator Exception
RuntimeException Override Test assertEquals assertTrue assertFalse assertNull assertNotNull equals hashCode toString
length size get set add put remove contains isEmpty valueOf append println""".split())  # noqa: SIM905
IDENT = re.compile(r"\b[A-Za-z_$][A-Za-z0-9_$]*\b")
CALL = re.compile(r"\b([A-Za-z_$][A-Za-z0-9_$]*)\s*\(")
TYPE = re.compile(r"\b[A-Z][a-z0-9]\w*\b")


def changed_identifiers(prompt_user: str) -> set[str]:
    """Methods called or declared (`name(`) and type names (PascalCase) in the changed lines."""
    diff = prompt_user.split("### Code change", 1)[1]
    ids = set()
    for line in diff.split("\n"):
        if line[:1] in "+-" and not line.startswith(("+++", "---")):
            code = re.sub(r'"([^"\\]|\\.)*"', "", line[1:].split("//", 1)[0])
            ids.update(t for t in CALL.findall(code) + TYPE.findall(code) if len(t) >= 4 and t not in KEYWORDS)
    return ids


def sign_test(diffs: list[float]) -> float:
    """Exact two-sided sign test on the non-zero paired differences."""
    from math import comb
    k, n = sum(d > 0 for d in diffs), sum(d != 0 for d in diffs)
    tail = sum(comb(n, i) for i in range(min(k, n - k) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def cmd_relevance(a):
    recs = {}
    with open(a.contexts, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            recs.setdefault(r["commit"], {})[r["condition"]] = r
    cond2, cond3 = "C2" + a.suffix, "C3" + a.suffix
    p2, p3, rows = [], [], []
    for sha, rs in recs.items():
        if "prompt" not in rs.get("C0", {}):
            raise SystemExit("contexts were built without --with-prompts")
        ids = changed_identifiers(rs["C0"]["prompt"]["user"])
        shares = []
        for cond in (cond2, cond3):
            block = rs[cond]["prompt"]["user"].split("### Code change", 1)[0]
            snippets = re.split(r"(?m)^// (?=\S+\.java lines \d+-\d+$)", block)[1:]
            hits = [bool(ids & set(IDENT.findall(s.split("\n", 1)[1] if "\n" in s else ""))) for s in snippets]
            shares.append(sum(hits) / len(hits) if hits else None)
        if None in shares:
            continue
        p2.append(shares[0])
        p3.append(shares[1])
        rows.append(f"{rs['C0']['project']} {sha[:10]} ids={len(ids)} C2 {shares[0]:.2f} C3 {shares[1]:.2f}")
    print("\n".join(rows))
    diffs = [x - y for x, y in zip(p2, p3)]
    print(f"\ncommits {len(p2)}: mean related share C2 {sum(p2) / len(p2):.3f}, C3 {sum(p3) / len(p3):.3f}; "
          f"C2 > C3 in {sum(d > 0 for d in diffs)}, equal {sum(d == 0 for d in diffs)}, C2 < C3 "
          f"{sum(d < 0 for d in diffs)}; exact sign test p = {sign_test(diffs):.2g}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(required=True)
    p = sub.add_parser("ranges")
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--manifest", type=Path)
    p.add_argument("--n", type=int, default=40)
    p.add_argument("--seed", type=int, default=7)
    p.set_defaults(func=cmd_ranges)
    p = sub.add_parser("relevance")
    p.add_argument("--contexts", type=Path, required=True)
    p.add_argument("--suffix", default="", help="budget suffix, for example @8000")
    p.set_defaults(func=cmd_relevance)
    a = ap.parse_args()
    if getattr(a, "manifest", 1) is None:
        a.manifest = a.root / "manifest.csv"
    a.func(a)


if __name__ == "__main__":
    main()
