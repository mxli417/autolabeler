# Ingestion and document splitting

## Run it

Install with `uv sync --extra dev`. Generate a synthetic PDF or supply your own:

```bash
uv run autolabeler fixture --out data/demo --pages 20
uv run autolabeler ingest data/demo/demo.pdf --workspace workspace \
  --pipeline-version v1 --chunk-size 1800 --overlap 200
```

Find the run directory printed by `ingest`, then generate candidates and a hidden oracle:

```bash
uv run autolabeler tasks workspace/doc-.../v1/chunks.jsonl data/demo/queries.jsonl \
  --out workspace/tasks.json --ranking-out workspace/ranking.jsonl -k 5
uv run autolabeler oracle workspace/doc-.../v1/chunks.jsonl data/demo/oracle_seed.jsonl \
  --out data/demo/oracle.jsonl
uv run autolabeler evaluate workspace/ranking.jsonl data/demo/oracle.jsonl
```

The API alternative is `docker compose up --build workbench`, followed by `POST /ingest` with `{"pdf":"data/demo/demo.pdf"}`. Paths are relative to the repository mounted at `/workbench`. The API is synchronous; use the CLI for repeatable batch work.

## Stage details

1. **Identity.** Stream the PDF through SHA-256. The first 12 hex characters form the document ID. A new `pipeline_version` creates a distinct run; the same hash and version is idempotent.
2. **Page extraction.** `pypdf` extracts each page separately. A bad page records an error without dropping successful pages. Text whitespace is normalized without changing word content.
3. **OCR gate.** A page below `min_text_chars` is listed in `pages_requiring_ocr`. This build does not silently OCR it. In production, route those pages to a versioned OCR adapter and retain page images, boxes, confidence, and engine version.
4. **Splitting.** Each page is independent. The splitter prefers paragraph, sentence, line, and word boundaries, in that order, and enforces `chunk_size`. `overlap` repeats trailing characters to protect boundary evidence. It never merges pages, so page provenance stays exact.
5. **Provenance.** Every chunk has page-relative `start`/`end`, content SHA-256, parser version, pipeline version, and stable IDs. Re-extraction with a new parser requires a new pipeline version.
6. **Retrieval.** Tokenized lower-case BM25 ranks chunks. The ranking artifact contains IDs only; Label Studio tasks contain the candidate text needed for review.
7. **Oracle isolation.** Synthetic fixture generation writes only page and expected text to `oracle_seed.jsonl`. `oracle` resolves this against chunks after ingestion. Retrieval receives neither file.

For arbitrary documents, no oracle exists. Build an independent audit flow over `pages.jsonl`: exact/regex and full-text search, page preview, and a way to add a missed chunk. Only mark `evidence_absent_after_audit` after that review. Candidate labels alone estimate precision; they cannot establish retrieval recall.
