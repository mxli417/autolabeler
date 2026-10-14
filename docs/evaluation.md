# Labeling and evaluation protocol

## Assignment design

Pilot 30–50 diverse tasks first. Resolve unclear guidelines, then freeze the label schema. Randomly select 10–20% of each task type and difficulty slice as the overlap set; every annotator labels it independently. Assign the remainder once. Hide other annotators' decisions and model confidence. Keep original annotations when adjudicating.

Use stable task IDs and stratify by document, label prevalence, scanned/text pages, tables, and known hard cases. Never split candidates from the same query across train/test comparisons without tracking the grouping.

## Agreement

- Report raw agreement and Cohen's κ for exactly two annotators on nominal choices.
- Report pairwise κ plus Krippendorff's nominal α for three or more annotators or incomplete overlap.
- Report class prevalence and per-label confusion counts. High raw agreement with low κ often means one label dominates.
- For evidence spans, report exact match and character overlap F1 separately. Agreeing on `relevant` while highlighting different evidence is a real disagreement.
- Calculate IAA before adjudication. After guideline changes, measure a fresh overlap batch; do not blend incompatible rounds.

Interpret metrics as diagnostics rather than pass/fail truth. Suggested investigation thresholds such as κ/α below 0.67 must be adapted to risk, prevalence, and task ambiguity.

## Retrieval evaluation

Recall@k asks whether known evidence was retrieved; MRR rewards the first relevant result; nDCG rewards useful ordering when several chunks are relevant. Report results by query and slice, not only as one average. A synthetic absent-evidence query measures unwanted candidate generation but does not prove a real-world document lacks evidence.

For extraction, add normalized exact match, field-level precision/recall/F1, schema validity, and evidence-page accuracy. For PII, score spans and entity types, then measure leakage after redaction and over-redaction of safe text. Fit normalization and span-matching rules before examining candidate-system results.

## Shortcomings

IAA does not measure correctness: annotators can agree on a wrong guideline. Retrieval scores depend on oracle completeness and chunk granularity. Overlapping chunks can inflate ranks. Character-level span F1 rewards near matches that may still omit a decisive word. PII metrics on synthetic data rarely predict performance on real language, formatting, or identifiers. Label Studio exports also reflect cancellations, skipped tasks, and reviewer behavior; retain those fields during analysis.
