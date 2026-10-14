# From 2,000-page PDFs to defensible human evaluation

## The problem

Long-document evaluation fails when a PDF becomes one giant annotation task or when retrieved candidates are mistaken for ground truth. The useful unit is a small, traceable claim: a query, one candidate chunk, its page, and the retrieval run that produced it.

## The lean design

Describe the three boundaries: immutable ingestion artifacts, candidate generation that cannot see the oracle, and independent human annotations. Use the architecture diagram from `architecture.md`. Show how a content hash and pipeline version make reruns comparable.

## Finding the needle

For synthetic tests, plant facts and record their locations before retrieval runs. For unknown documents, combine candidate review with independent full-document search. Explain why “not in top-k” means retrieval miss, while “absent” requires an audit.

## Measuring humans and systems

Walk through the overlap-set assignment, κ and α, span F1, Recall@k, MRR, and nDCG. Include prevalence and per-slice results. A strong article should show one disagreement and how adjudication changed the guideline.

## What breaks at production scale

Discuss OCR and layout, table reading order, queueing, parser isolation, access control, PII-safe logs, object storage, and immutable dataset versions. Close with the principle that infrastructure should follow a measured bottleneck: the local baseline is intentionally small enough to inspect and replace.

## Reproducible appendix

Link the exact CLI commands in `pipeline.md`, the three notebooks, the Label Studio XML configs, and a frozen export. Record package versions, pipeline version, document hash, annotator protocol, matching rules, and all exclusions.
