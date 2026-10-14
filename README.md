# Document evaluation workbench

A lean, local workflow for turning long PDFs into small Label Studio tasks and measuring retrieval quality, extraction/PII labels, and annotator agreement.

## Quick start

```bash
uv sync --extra dev
uv run autolabeler demo
Copy-Item .env.example .env
docker compose up --build -d
```

Open <http://localhost:8080>, create a project with one of the configs in `label_studio/`, and import `workspace/tasks.json`. After two or more people label the same overlap set, export JSON and run:

In the project, open **Settings → Model → Connect Model** and use `http://ml-backend:9090`. The backend uses the multimodal Responses API through the official OpenAI SDK. Set `MODEL_ENABLED=true`, `MODEL_NAME`, and `OPENAI_API_KEY` for OpenAI. Set `MODEL_PROVIDER=litellm`, `MODEL_BASE_URL`, and `LITELLM_API_KEY` to route the same request through LiteLLM. Image inputs require `MODEL_SEND_IMAGES=true`; see [the backend guide](docs/ml-backend.md).

```bash
uv run autolabeler iaa export.json --out workspace/iaa.json
uv run autolabeler analyze export.json --out workspace/analysis.json
uv run autolabeler evaluate workspace/ranking.jsonl data/demo/oracle.jsonl
```

For repeatable labeling, assign every item in a 10–20% overlap set to all annotators, keep the remaining items singly assigned, adjudicate disagreements without overwriting original annotations, and freeze each export. Report agreement per label and task type alongside prevalence and raw agreement; κ alone can be misleading for rare labels.

## Ingestion and splitting

`ingest` hashes the original PDF and creates `workspace/<document-id>/<pipeline-version>/`. It extracts each page independently, records page text and extraction errors in `pages.jsonl`, then splits normalized text at paragraph/sentence boundaries. Oversized blocks are hard-split. Every chunk carries the document hash, page, page character offsets, chunk hash, parser version, and pipeline version. Re-running the same PDF and version returns the same directory and IDs.

```bash
uv run autolabeler ingest contract.pdf --workspace workspace \
  --pipeline-version v1 --chunk-size 1800 --overlap 200
```

Outputs are `manifest.json`, `pages.jsonl`, and `chunks.jsonl`. OCR is deliberately outside this lean build: pages with little or no text are flagged in the manifest for an OCR stage before production use. See [the pipeline guide](docs/pipeline.md), [the evaluation guide](docs/evaluation.md), and the runnable notebooks in [`notebooks/`](notebooks/).

## What this MVP does not solve

- It uses local files and synchronous CLI runs. Add object storage, a queue, and a job database for concurrent or untrusted uploads.
- PDF text extraction does not preserve layout boxes and does not OCR scans. Tables and multi-column pages may read in the wrong order.
- BM25 candidates help find evidence; a top-k miss never proves that evidence is absent. An annotator must search the full document or use controlled oracle data.
- Agreement reflects the annotation unit and matching rule. Span overlap, missing labels, class imbalance, and adjudication can materially change the result.
- Label Studio data, documents, and exports may contain sensitive text. This local stack has no production authentication, encryption, retention policy, or PII-safe telemetry.
- Dense retrieval, OCR, MLflow, and automatic Label Studio project creation remain extension points. The bundled ML backend can call OpenAI directly or use a LiteLLM proxy, but it is a synchronous reference integration rather than a production inference service.

The deeper architecture and a blog-ready narrative are in [docs/architecture.md](docs/architecture.md) and [docs/blog.md](docs/blog.md).

## Development checks

```bash
uv run pre-commit install --install-hooks
uv run pre-commit install --hook-type pre-push
uv run pre-commit run --all-files
```

Commits run file, YAML/TOML/JSON, Ruff, formatting, and `nbstripout`; the latter removes notebook outputs and execution counts from the working copy before commit. The pre-push hook runs the unit suite.

Run the slower container and Docker configuration scan explicitly before a release:

```bash
uv run pre-commit run trivy --hook-stage manual
```

It builds both application images, downloads Trivy's vulnerability database, and fails on fixable high or critical findings. See [the security checks](docs/security.md) for scope and limitations.

Run the credential-free multimodal HTTP smoke test with deterministic Presidio and Responses endpoints:

```bash
uv sync --extra dev --extra backend
uv run python tests/e2e/run_local.py
```
