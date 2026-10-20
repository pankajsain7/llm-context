"""Feasibility demo: build the C0 diff and the cross-file C2/C3 context blocks for one commit.

Usage: python context_demo.py <repo_dir> <commit_sha> [budget_tokens] [seed]
Reads repository code only from the parent snapshot (git objects, no checkout) plus the commit diff.
This is a prototype for docs/04-feasibility-demo.md, not the experiment pipeline; the masked
same-file C1 block of design revision 2 is not implemented here.
"""
import math
import random
import re
import shutil
import subprocess
import sys
from collections import Counter

GIT = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"
JAVA_KW = set("""abstract assert boolean break byte case catch char class const continue default do double else enum
extends final finally float for goto if implements import instanceof int interface long native new package private
protected public return short static strictfp super switch synchronized this throw throws transient try void volatile
while true false null string override""".split())

try:
    import tiktoken

    _enc = tiktoken.get_encoding("o200k_base")
    count_tokens = lambda s: len(_enc.encode(s, disallowed_special=()))
    TOKENIZER = "tiktoken/o200k_base"
except ImportError:
    count_tokens = lambda s: math.ceil(len(s) / 4)
    TOKENIZER = "chars/4 (approximation)"


def git(repo, *args):
    return subprocess.run([GIT, *args], cwd=repo, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", check=True).stdout


def read_blobs(repo, rev, paths):
    proc = subprocess.Popen([GIT, "cat-file", "--batch"], cwd=repo, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out = {}
    for p in paths:
        proc.stdin.write(f"{rev}:{p}\n".encode())
        proc.stdin.flush()
        header = proc.stdout.readline().decode().split()
        if len(header) < 3 or header[1] != "blob":
            continue
        data = proc.stdout.read(int(header[2]))
        proc.stdout.read(1)
        out[p] = data.decode("utf-8", errors="replace")
    proc.stdin.close()
    proc.wait()
    return out


def terms(text):
    toks = []
    for ident in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text):
        for part in re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+", ident.replace("_", " ")):
            part = part.lower()
            if len(part) > 1 and part not in JAVA_KW:
                toks.append(part)
    return toks


def strip_header(text):
    """Lines from the `package` declaration on, with the 1-based number of the first kept line."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("package "):
            return i + 1, lines[i:]
    return 1, lines


def chunk(path, text, size=40, stride=20):
    first, lines = strip_header(text)
    n = len(lines)
    if n == 0:
        return
    starts = list(range(0, max(n - size, 0) + 1, stride))
    if starts[-1] + size < n:
        starts.append(n - size)  # final window must reach the last line
    for s in starts:
        e = min(s + size, n)
        body = "\n".join(lines[s:e])
        a, b = first + s, first + e - 1
        yield {"path": path, "start": a, "end": b, "body": body, "text": f"// {path} lines {a}-{b}\n{body}"}


def bm25_rank(query, docs, k1=1.2, b=0.75):
    tfs = [Counter(terms(d["body"])) for d in docs]  # the path header is rendered but not indexed
    avgdl = sum(sum(tf.values()) for tf in tfs) / max(len(tfs), 1)
    df = Counter(t for tf in tfs for t in tf)
    n = len(docs)
    q = set(terms(query))
    scores = []
    for tf in tfs:
        dl = sum(tf.values())
        s = 0.0
        for t in q & tf.keys():
            idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
            s += idf * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * dl / avgdl))
        scores.append(s)
    return sorted(range(n), key=lambda i: (-scores[i], docs[i]["path"], docs[i]["start"])), scores


def cut(d, k):
    """The first k lines of a snippet, re-rendered."""
    body, end = "\n".join(d["body"].split("\n")[:k]), d["start"] + k - 1
    return {**d, "end": end, "body": body, "text": f"// {d['path']} lines {d['start']}-{end}\n{body}"}


def render(snippets):
    return "\n".join(d["text"] for d in snippets)


def fill(order, docs, target, scores=None, tol=0.02):
    """Take snippets in rank order; budgets are counted on the rendered block, not per snippet.

    A snippet that does not fit is cut at a line boundary; if not even its first line fits, it is
    skipped and the next snippet is tried. Returns (snippets, rendered tokens, status): "ok" (reached
    target * (1 - tol)), "line_limit" (below that, and at least one snippet could not be fitted),
    "short" (eligible snippets exhausted) or "no_hits" (scores given but none positive).
    """
    if scores is not None:
        order = [i for i in order if scores[i] > 0]
        if not order:
            return [], 0, "no_hits"
    picked, used, spans, skipped = [], 0, {}, 0
    fits = lambda d: count_tokens(render(picked + [d])) <= target
    for i in order:
        d = docs[i]
        if any(not (d["end"] < s or d["start"] > e) for s, e in spans.get(d["path"], [])):
            continue  # no overlapping windows from the same file
        if not fits(d):
            n = d["end"] - d["start"] + 1
            k = next((k for k in range(n - 1, 0, -1) if fits(cut(d, k))), 0) if fits(cut(d, 1)) else 0
            if k == 0:
                skipped += 1
                continue
            d = cut(d, k)
        picked.append(d)
        used = count_tokens(render(picked))
        spans.setdefault(d["path"], []).append((d["start"], d["end"]))
        if used >= target * (1 - tol):
            return picked, used, "ok"
    return picked, used, "line_limit" if skipped else "short"


def main(repo, sha, budget=2000, seed=0):
    parent = git(repo, "rev-parse", f"{sha}^").strip()
    changed = git(repo, "diff", "--name-only", parent, sha).split()
    diff_u3 = git(repo, "diff", "-U3", "-M", parent, sha, "--", "*.java")

    pool_paths = [p for p in git(repo, "ls-tree", "-r", "--name-only", parent).split()
                  if p.endswith(".java") and p not in changed]
    blobs = read_blobs(repo, parent, pool_paths)
    docs = [c for p, txt in blobs.items() for c in chunk(p, txt)]
    changed_lines = "\n".join(l[1:] for l in diff_u3.splitlines()
                              if l[:1] in "+-" and not l.startswith(("+++", "---")))
    order, scores = bm25_rank(changed_lines, docs)
    c2, c2_tok, c2_status = fill(order, docs, budget, scores)
    rnd = list(range(len(docs)))
    random.Random(f"{sha}:{seed}").shuffle(rnd)
    c3, c3_tok, c3_status = fill(rnd, docs, c2_tok)

    print(f"commit {sha}\nparent {parent}\nchanged files {changed}\ntokenizer {TOKENIZER}")
    print(f"C0 Java-only diff -U3 tokens: {count_tokens(diff_u3)}")
    print(f"pool @parent (excl. changed files, license headers stripped): {len(blobs)} .java files, "
          f"{len(docs)} windows, {sum(count_tokens(chr(10).join(strip_header(t)[1])) for t in blobs.values())} tokens")
    print(f"C2 BM25 (budget {budget}, {sum(s > 0 for s in scores)} windows with score > 0): "
          f"{c2_tok} rendered tokens, status {c2_status}")
    for d in c2:
        print(f"   {d['path']}:{d['start']}-{d['end']}")
    print(f"C3 random (seed={seed}) matched to C2: {c3_tok} rendered tokens "
          f"({c3_tok / max(c2_tok, 1):.1%} of C2), status {c3_status}")
    for d in c3:
        print(f"   {d['path']}:{d['start']}-{d['end']}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], *(int(x) for x in sys.argv[3:5]))
