"""Okapi BM25 over identifier sub-tokens (design §5.4)."""
import math
import re
from collections import Counter

JAVA_KEYWORDS = frozenset(["abstract", "assert", "boolean", "break", "byte", "case", "catch", "char", "class", "const", "continue", "default", "do", "double", "else", "enum", "extends", "final", "finally", "float", "for", "goto", "if", "implements", "import", "instanceof", "int", "interface", "long", "native", "new", "package", "private", "protected", "public", "return", "short", "static", "strictfp", "super", "switch", "synchronized", "this", "throw", "throws", "transient", "try", "void", "volatile", "while", "true", "false", "null", "string", "override", "var", "record", "yield", "sealed", "permits"])
_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_PART = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+")


def terms(text: str) -> list[str]:
    """camelCase and snake_case parts, lower-cased; Java keywords and one-character parts dropped."""
    out = []
    for ident in _IDENT.findall(text):
        for part in _PART.findall(ident.replace("_", " ")):
            part = part.lower()
            if len(part) > 1 and part not in JAVA_KEYWORDS:
                out.append(part)
    return out


def bm25_scores(query: str, docs: list[str], k1: float = 1.2, b: float = 0.75) -> list[float]:
    """One score per document. Query terms count once each; idf = ln(1 + (N - df + 0.5) / (df + 0.5))."""
    tfs = [Counter(terms(d)) for d in docs]
    n = len(docs)
    if n == 0:
        return []
    lengths = [sum(tf.values()) for tf in tfs]
    avgdl = sum(lengths) / n or 1.0
    df = Counter(t for tf in tfs for t in tf)
    # Hash-randomized set iteration can change floating-point sums, breaking score ties differently
    # across Python processes. A fixed term order and accurate summation make ranking reproducible.
    q = set(terms(query))
    scores = []
    for tf, dl in zip(tfs, lengths):
        contributions = []
        for t in sorted(q & tf.keys()):
            idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
            contributions.append(idf * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * dl / avgdl)))
        scores.append(math.fsum(contributions))
    return scores
