import json

from autolabeler.io import write_jsonl
from autolabeler.tasks import generate_tasks, resolve_oracle


def test_tasks_keep_provenance_and_oracle_is_separate(tmp_path):
    chunks = tmp_path / "chunks.jsonl"
    queries = tmp_path / "queries.jsonl"
    seed = tmp_path / "seed.jsonl"
    write_jsonl(chunks, [{"chunk_id": "c1", "document_id": "d1", "page": 2, "text": "Retention is seven years."}])
    write_jsonl(queries, [{"query_id": "q1", "question": "What is the retention period?"}])
    write_jsonl(seed, [{"query_id": "q1", "page": 2, "expected": "seven years"}])
    tasks = generate_tasks(
        str(chunks), str(queries), str(tmp_path / "tasks.json"), ranking_output=str(tmp_path / "rank.jsonl")
    )
    assert tasks[0]["data"]["chunk_id"] == "c1"
    assert "expected" not in json.dumps(tasks)
    oracle = resolve_oracle(str(chunks), str(seed), str(tmp_path / "oracle.jsonl"))
    assert oracle[0]["gold_chunk_ids"] == ["c1"]
