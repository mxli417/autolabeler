from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

from .io import write_json, write_jsonl


@dataclass(frozen=True)
class SplitConfig:
    max_chars: int = 1800
    overlap_chars: int = 200
    min_text_chars: int = 40


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _boundary(text: str, start: int, ideal_end: int) -> int:
    if ideal_end >= len(text):
        return len(text)
    floor = start + max(1, (ideal_end - start) // 2)
    for pattern in ("\n\n", ". ", "\n", " "):
        point = text.rfind(pattern, floor, ideal_end)
        if point >= floor:
            return point + len(pattern)
    return ideal_end


def split_page(text: str, max_chars: int, overlap_chars: int) -> Iterable[tuple[int, int, str]]:
    if max_chars < 1 or overlap_chars < 0 or overlap_chars >= max_chars:
        raise ValueError("Require max_chars > 0 and 0 <= overlap_chars < max_chars")
    start = 0
    while start < len(text):
        end = _boundary(text, start, min(len(text), start + max_chars))
        if end <= start:
            end = min(len(text), start + max_chars)
        yield start, end, text[start:end].strip()
        if end == len(text):
            break
        start = max(start + 1, end - overlap_chars)


def ingest_pdf(
    pdf_path: str | Path,
    workspace: str | Path = "workspace",
    pipeline_version: str = "v1",
    config: SplitConfig | None = None,
) -> dict:
    config = config or SplitConfig()
    source = Path(pdf_path)
    digest = sha256_file(source)
    document_id = f"doc-{digest[:12]}"
    run_dir = Path(workspace) / document_id / pipeline_version
    manifest_path = run_dir / "manifest.json"
    if manifest_path.exists():
        import json

        return json.loads(manifest_path.read_text(encoding="utf-8"))

    reader = PdfReader(str(source))
    pages, chunks, weak_pages = [], [], []
    for page_number, page in enumerate(reader.pages, start=1):
        error = None
        try:
            text = normalize_text(page.extract_text() or "")
        except Exception as exc:  # malformed pages must not discard the document
            text, error = "", f"{type(exc).__name__}: {exc}"
        page_id = f"{document_id}-p{page_number:05d}"
        pages.append(
            {"document_id": document_id, "page_id": page_id, "page": page_number, "text": text, "error": error}
        )
        if len(text) < config.min_text_chars:
            weak_pages.append(page_number)
        for index, (start, end, content) in enumerate(
            split_page(text, config.max_chars, config.overlap_chars), start=1
        ):
            if not content:
                continue
            chunk_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            chunks.append(
                {
                    "document_id": document_id,
                    "page_id": page_id,
                    "page": page_number,
                    "chunk_id": f"{page_id}-c{index:03d}-{chunk_hash[:8]}",
                    "text": content,
                    "start": start,
                    "end": end,
                    "sha256": chunk_hash,
                    "parser": f"pypdf-{__import__('pypdf').__version__}",
                    "pipeline_version": pipeline_version,
                }
            )

    run_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(run_dir / "pages.jsonl", pages)
    write_jsonl(run_dir / "chunks.jsonl", chunks)
    manifest = {
        "document_id": document_id,
        "source_name": source.name,
        "source_sha256": digest,
        "pipeline_version": pipeline_version,
        "page_count": len(pages),
        "chunk_count": len(chunks),
        "pages_requiring_ocr": weak_pages,
        "split": {"max_chars": config.max_chars, "overlap_chars": config.overlap_chars},
        "status": "ready" if not any(p["error"] for p in pages) else "ready_with_page_errors",
        "artifacts": {"pages": "pages.jsonl", "chunks": "chunks.jsonl"},
    }
    write_json(manifest_path, manifest)
    return manifest
