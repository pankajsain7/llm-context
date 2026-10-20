import math

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
