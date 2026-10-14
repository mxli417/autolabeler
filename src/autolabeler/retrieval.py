from __future__ import annotations

import math
import re
from collections import Counter

TOKEN = re.compile(r"(?u)\b\w\w+\b")


def tokenize(text: str) -> list[str]:
    return TOKEN.findall(text.casefold())


class BM25:
    """Small dependency-free BM25 implementation suitable for inspectable baselines."""

    def __init__(self, chunks: list[dict], k1: float = 1.5, b: float = 0.75):
        self.chunks, self.k1, self.b = chunks, k1, b
        self.docs = [Counter(tokenize(row["text"])) for row in chunks]
        self.lengths = [sum(doc.values()) for doc in self.docs]
        self.avgdl = sum(self.lengths) / len(self.lengths) if self.lengths else 0.0
        self.df = Counter(term for doc in self.docs for term in doc)

    def search(self, query: str, k: int = 5) -> list[dict]:
        if not self.docs:
            return []
        terms = tokenize(query)
        scored = []
        for row, doc, length in zip(self.chunks, self.docs, self.lengths, strict=True):
            score = 0.0
            for term in terms:
                frequency = doc[term]
                if not frequency:
                    continue
                idf = math.log(1 + (len(self.docs) - self.df[term] + 0.5) / (self.df[term] + 0.5))
                denom = frequency + self.k1 * (1 - self.b + self.b * length / (self.avgdl or 1))
                score += idf * frequency * (self.k1 + 1) / denom
            if score > 0:
                scored.append((score, row))
        scored.sort(key=lambda item: (-item[0], item[1]["chunk_id"]))
        return [{**row, "score": round(score, 8), "rank": rank} for rank, (score, row) in enumerate(scored[:k], 1)]
