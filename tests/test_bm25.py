import json
import math
import os
import subprocess
import sys
from pathlib import Path

from jitctx.bm25 import bm25_scores, terms


def test_terms_split_identifiers_and_drop_keywords():
    assert terms("public int getHTTPResponse_code(String x)") == ["get", "http", "response", "code"]


def test_scores_match_a_hand_computation():
    docs = ["alphaBeta alpha", "beta", "gamma"]
    k1, b = 1.2, 0.75
    lengths = [3, 1, 1]  # alpha, beta, alpha | beta | gamma
    avgdl = sum(lengths) / 3

    def term(tf, df, dl):
        idf = math.log(1 + (3 - df + 0.5) / (df + 0.5))
        return idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * dl / avgdl))

    expected = [term(2, 1, 3) + term(1, 2, 3), term(1, 2, 1), 0.0]
    got = bm25_scores("alpha beta", docs, k1, b)
    assert all(math.isclose(g, e) for g, e in zip(got, expected))


def test_query_terms_count_once():
    assert bm25_scores("alpha alpha alpha", ["alpha", "beta"]) == bm25_scores("alpha", ["alpha", "beta"])


def test_empty_inputs():
    assert bm25_scores("alpha", []) == []
    assert bm25_scores("", ["alpha"]) == [0.0]


def test_scores_ranking_and_selected_prompt_are_identical_across_hash_seeds():
    # Equal document lengths and reversed term frequencies give mathematically tied scores. The
    # former unordered += accumulation could make either document win by floating-point roundoff.
    script = """
import json
from jitctx.bm25 import bm25_scores
from jitctx.prompt import build_prompt, prompt_text, sha256
from jitctx.select import Window, fill, render_cross_file
words = 'alpha beta gamma delta epsilon zeta theta lambda sigma omega kappa iota muon neutrino photon boson proton lepton neutron electron'.split()
docs = [' '.join(w for w, n in zip(words, counts) for _ in range(n))
        for counts in (range(1, 21), range(20, 0, -1))]
scores = bm25_scores(' '.join(words), docs)
order = sorted(range(len(docs)), key=lambda i: (-scores[i], str(i)))
pool = [Window(f'{i}.java', 1, (text,)) for i, text in enumerate(docs)]
result = fill(order, pool, 450)
prompt = prompt_text(build_prompt(render_cross_file(result.snippets), 'fixed diff'))
print(json.dumps({'scores': [s.hex() for s in scores], 'order': order,
                  'sources': [s.path for s in result.snippets], 'prompt_sha256': sha256(prompt)}))
"""
    results = []
    source_root = str(Path(__file__).resolve().parents[1] / "src")
    pythonpath = source_root + (os.pathsep + os.environ["PYTHONPATH"] if os.environ.get("PYTHONPATH") else "")
    for seed in (1, 2, 3, 7, 31):
        env = {**os.environ, "PYTHONPATH": pythonpath, "PYTHONHASHSEED": str(seed), "PYTHONDONTWRITEBYTECODE": "1"}
        proc = subprocess.run([sys.executable, "-B", "-c", script], env=env, text=True,
                              capture_output=True, check=True)
        results.append(json.loads(proc.stdout))
    assert all(result == results[0] for result in results)
    assert results[0]["scores"][0] == results[0]["scores"][1]
    assert results[0]["order"] == [0, 1] and results[0]["sources"]
