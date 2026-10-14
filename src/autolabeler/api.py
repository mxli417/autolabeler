from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .ingest import SplitConfig, ingest_pdf
from .tasks import generate_tasks

app = FastAPI(title="Document evaluation workbench", version="0.1.0")
ROOT = Path(os.getenv("WORKBENCH_ROOT", "/workbench")).resolve()


def within_root(value: str) -> Path:
    path = (ROOT / value).resolve()
    if ROOT not in path.parents and path != ROOT:
        raise HTTPException(400, "Path must be inside WORKBENCH_ROOT")
    return path


class IngestRequest(BaseModel):
    pdf: str
    pipeline_version: str = "v1"
    chunk_size: int = 1800
    overlap: int = 200


class TaskRequest(BaseModel):
    chunks: str
    queries: str
    output: str = "workspace/tasks.json"
    ranking_output: str = "workspace/ranking.jsonl"
    k: int = 5


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ingest")
def ingest(request: IngestRequest) -> dict:
    return ingest_pdf(
        within_root(request.pdf),
        within_root("workspace"),
        request.pipeline_version,
        SplitConfig(request.chunk_size, request.overlap),
    )


@app.post("/tasks")
def tasks(request: TaskRequest) -> dict:
    result = generate_tasks(
        str(within_root(request.chunks)),
        str(within_root(request.queries)),
        str(within_root(request.output)),
        request.k,
        str(within_root(request.ranking_output)),
    )
    return {"tasks": len(result), "output": request.output}
