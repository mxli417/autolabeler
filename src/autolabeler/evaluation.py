from __future__ import annotations

import math
from collections import Counter, defaultdict
from itertools import combinations
from statistics import mean

from .io import read_jsonl


def retrieval_metrics(rankings: list[dict], oracle: list[dict], ks: tuple[int, ...] = (1, 3, 5, 10)) -> dict:
    gold = {row["query_id"]: set(row.get("gold_chunk_ids", [row.get("gold_chunk_id")])) - {None} for row in oracle}
    per_query, absent_candidate_hits = [], []
    for row in rankings:
        expected = gold.get(row["query_id"], set())
        ranked = row["ranked_chunk_ids"]
        if not expected:
            absent_candidate_hits.append(bool(ranked))
            continue
        positions = [i for i, item in enumerate(ranked, 1) if item in expected]
        record = {"query_id": row["query_id"], "mrr": 1 / min(positions) if positions else 0.0}
        for k in ks:
            found = sum(1 for item in ranked[:k] if item in expected)
            record[f"recall@{k}"] = found / len(expected) if expected else 0.0
            dcg = sum(1 / math.log2(i + 1) for i, item in enumerate(ranked[:k], 1) if item in expected)
            ideal = sum(1 / math.log2(i + 1) for i in range(1, min(k, len(expected)) + 1))
            record[f"ndcg@{k}"] = dcg / ideal if ideal else 0.0
        per_query.append(record)
    keys = ["mrr", *(metric for k in ks for metric in (f"recall@{k}", f"ndcg@{k}"))]
    return {
        "queries_with_gold": len(per_query),
        "evidence_absent_queries": len(absent_candidate_hits),
        "absent_query_candidate_rate": mean(absent_candidate_hits) if absent_candidate_hits else None,
        **{key: mean([r[key] for r in per_query]) if per_query else 0.0 for key in keys},
        "per_query": per_query,
    }


def cohen_kappa(left: list[str], right: list[str]) -> dict:
    pairs = [(a, b) for a, b in zip(left, right, strict=True) if a is not None and b is not None]
    if not pairs:
        return {"n": 0, "agreement": None, "kappa": None}
    labels = set(a for a, _ in pairs) | set(b for _, b in pairs)
    agreement = sum(a == b for a, b in pairs) / len(pairs)
    lc, rc = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    chance = sum(lc[label] / len(pairs) * rc[label] / len(pairs) for label in labels)
    kappa = (agreement - chance) / (1 - chance) if chance < 1 else (1.0 if agreement == 1 else 0.0)
    return {"n": len(pairs), "agreement": agreement, "kappa": kappa}


def krippendorff_alpha_nominal(items: dict[str, dict[str, str]]) -> dict:
    units = [[v for v in ratings.values() if v is not None] for ratings in items.values()]
    units = [ratings for ratings in units if len(ratings) >= 2]
    values = [value for ratings in units for value in ratings]
    if not units or len(values) < 2:
        return {"units": len(units), "ratings": len(values), "alpha": None}
    # Coincidence-matrix form: units with missing ratings receive the correct
    # n/(n-1) weighting instead of being over-weighted by all pair combinations.
    observed_disagreement = 0.0
    for ratings in units:
        counts = Counter(ratings)
        n = len(ratings)
        observed_disagreement += (n * n - sum(count * count for count in counts.values())) / (n - 1)
    do = observed_disagreement / len(values)
    counts = Counter(values)
    total = len(values)
    de = sum(count * (total - count) for count in counts.values()) / (total * (total - 1))
    return {"units": len(units), "ratings": len(values), "alpha": 1 - do / de if de else (1.0 if do == 0 else None)}


def _choice(annotation: dict, control: str = "relevance") -> str | None:
    for result in annotation.get("result", []):
        if result.get("from_name") == control:
            choices = result.get("value", {}).get("choices", [])
            if choices:
                return choices[0]
    return None


def label_studio_agreement(export: list[dict], control: str = "relevance") -> dict:
    units: dict[str, dict[str, str]] = defaultdict(dict)
    for task in export:
        task_id = str(task.get("id", task.get("data", {}).get("candidate_id", "unknown")))
        for index, annotation in enumerate(task.get("annotations", [])):
            annotator = annotation.get("completed_by", annotation.get("created_by", f"annotator-{index}"))
            if isinstance(annotator, dict):
                annotator = annotator.get("email") or annotator.get("id") or str(annotator)
            value = _choice(annotation, control)
            if value is not None:
                units[task_id][str(annotator)] = value
    annotators = sorted({person for ratings in units.values() for person in ratings})
    pairwise = {}
    for a, b in combinations(annotators, 2):
        common = [ratings for ratings in units.values() if a in ratings and b in ratings]
        pairwise[f"{a} vs {b}"] = cohen_kappa([r[a] for r in common], [r[b] for r in common])
    return {
        "control": control,
        "units": len(units),
        "annotators": annotators,
        "pairwise_cohen": pairwise,
        "krippendorff_nominal": krippendorff_alpha_nominal(units),
    }


def span_f1(left: list[tuple[int, int]], right: list[tuple[int, int]]) -> dict:
    """Character-level overlap; useful for diagnostic IAA, not a substitute for label agreement."""
    a = {point for start, end in left for point in range(start, end)}
    b = {point for start, end in right for point in range(start, end)}
    overlap = len(a & b)
    precision = overlap / len(a) if a else (1.0 if not b else 0.0)
    recall = overlap / len(b) if b else (1.0 if not a else 0.0)
    return {
        "precision": precision,
        "recall": recall,
        "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
    }


def evaluate_files(rankings_path: str, oracle_path: str) -> dict:
    return retrieval_metrics(read_jsonl(rankings_path), read_jsonl(oracle_path))
