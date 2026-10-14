from __future__ import annotations

from .io import read_jsonl, write_json, write_jsonl
from .retrieval import BM25


def generate_tasks(
    chunks_path: str, queries_path: str, output: str, k: int = 5, ranking_output: str | None = None
) -> list[dict]:
    chunks, queries = read_jsonl(chunks_path), read_jsonl(queries_path)
    index, tasks, ranking = BM25(chunks), [], []
    for query in queries:
        hits = index.search(query["question"], k=k)
        ranking.append({"query_id": query["query_id"], "ranked_chunk_ids": [h["chunk_id"] for h in hits]})
        for hit in hits:
            candidate_id = f"{query['query_id']}-{hit['chunk_id']}"
            tasks.append(
                {
                    "id": candidate_id,
                    "data": {
                        "task_type": "retrieval",
                        "query_id": query["query_id"],
                        "question": query["question"],
                        "candidate_id": candidate_id,
                        "document_id": hit["document_id"],
                        "chunk_id": hit["chunk_id"],
                        "page": hit["page"],
                        "text": hit["text"],
                        "rank": hit["rank"],
                        "score": hit["score"],
                        "retriever": "bm25",
                    },
                }
            )
    write_json(output, tasks)
    if ranking_output:
        write_jsonl(ranking_output, ranking)
    return tasks


def resolve_oracle(chunks_path: str, seed_path: str, output: str) -> list[dict]:
    chunks, seeds = read_jsonl(chunks_path), read_jsonl(seed_path)
    rows = []
    for seed in seeds:
        if seed.get("evidence_absent"):
            rows.append({"query_id": seed["query_id"], "gold_chunk_ids": [], "evidence_absent": True})
            continue
        expected = seed["expected"].casefold()
        matches = [c["chunk_id"] for c in chunks if c["page"] == seed["page"] and expected in c["text"].casefold()]
        if not matches:
            raise ValueError(f"Could not resolve oracle seed {seed['query_id']} on page {seed['page']}")
        rows.append(
            {
                "query_id": seed["query_id"],
                "gold_chunk_ids": matches,
                "page": seed["page"],
                "expected": seed["expected"],
            }
        )
    write_jsonl(output, rows)
    return rows
