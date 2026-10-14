import pytest

from autolabeler.evaluation import cohen_kappa, krippendorff_alpha_nominal, retrieval_metrics, span_f1


def test_retrieval_metrics_and_absent_query():
    rankings = [
        {"query_id": "q1", "ranked_chunk_ids": ["x", "gold"]},
        {"query_id": "q2", "ranked_chunk_ids": ["noise"]},
    ]
    oracle = [
        {"query_id": "q1", "gold_chunk_ids": ["gold"]},
        {"query_id": "q2", "gold_chunk_ids": [], "evidence_absent": True},
    ]
    result = retrieval_metrics(rankings, oracle, ks=(1, 3))
    assert result["mrr"] == 0.5
    assert result["recall@1"] == 0.0
    assert result["recall@3"] == 1.0
    assert result["absent_query_candidate_rate"] == 1.0


def test_agreement_measures():
    assert cohen_kappa(["a", "b"], ["a", "b"])["kappa"] == 1.0
    alpha = krippendorff_alpha_nominal({"1": {"a": "x", "b": "x"}, "2": {"a": "y", "b": "y"}})
    assert alpha["alpha"] == 1.0
    assert span_f1([(0, 4)], [(2, 4)])["f1"] == pytest.approx(2 / 3)
