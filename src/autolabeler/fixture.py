from __future__ import annotations

from pathlib import Path

from .io import write_jsonl


def create_fixture(output: str | Path, pages: int = 20) -> dict:
    try:
        from reportlab.pdfgen.canvas import Canvas
    except ImportError as exc:
        raise RuntimeError("Install fixture dependencies: uv sync --extra fixture") from exc
    target = Path(output)
    target.mkdir(parents=True, exist_ok=True)
    pdf = target / "demo.pdf"
    canvas = Canvas(str(pdf))
    needles = {
        5: "Project Aurora has a retention period of seven years.",
        13: "The synthetic contact is Erika Muster, email erika.muster@example.test.",
    }
    for page in range(1, pages + 1):
        canvas.drawString(72, 790, f"Synthetic evaluation handbook — page {page}")
        canvas.drawString(72, 755, needles.get(page, "Routine policy text with no answer to the evaluation questions."))
        canvas.drawString(72, 720, f"Reference code DEMO-{page:04d}. This document contains synthetic data only.")
        canvas.showPage()
    canvas.save()
    write_jsonl(
        target / "queries.jsonl",
        [
            {"query_id": "q-retention", "question": "What is Project Aurora's retention period?"},
            {"query_id": "q-contact", "question": "What is the synthetic contact email?"},
            {"query_id": "q-missing", "question": "What is the cancellation fee?"},
        ],
    )
    # The ingest run resolves page/offset to chunk IDs. This separate file is intentionally not consumed by retrieval.
    write_jsonl(
        target / "oracle_seed.jsonl",
        [
            {"query_id": "q-retention", "page": 5, "expected": "seven years"},
            {"query_id": "q-contact", "page": 13, "expected": "erika.muster@example.test"},
            {"query_id": "q-missing", "evidence_absent": True},
        ],
    )
    return {"pdf": str(pdf), "pages": pages}
