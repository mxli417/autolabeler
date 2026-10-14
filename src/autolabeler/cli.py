from __future__ import annotations

import argparse
import json
from pathlib import Path

from .analysis import analyze_export
from .evaluation import evaluate_files, label_studio_agreement, retrieval_metrics
from .fixture import create_fixture
from .ingest import SplitConfig, ingest_pdf
from .io import read_jsonl, write_json
from .tasks import generate_tasks, resolve_oracle


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="autolabeler")
    commands = root.add_subparsers(dest="command", required=True)
    fixture = commands.add_parser("fixture")
    fixture.add_argument("--out", default="data/demo")
    fixture.add_argument("--pages", type=int, default=20)
    demo = commands.add_parser("demo")
    demo.add_argument("--data-dir", default="data/demo")
    demo.add_argument("--workspace", default="workspace")
    demo.add_argument("--pages", type=int, default=20)
    ingest = commands.add_parser("ingest")
    ingest.add_argument("pdf")
    ingest.add_argument("--workspace", default="workspace")
    ingest.add_argument("--pipeline-version", default="v1")
    ingest.add_argument("--chunk-size", type=int, default=1800)
    ingest.add_argument("--overlap", type=int, default=200)
    tasks = commands.add_parser("tasks")
    tasks.add_argument("chunks")
    tasks.add_argument("queries")
    tasks.add_argument("--out", required=True)
    tasks.add_argument("--ranking-out")
    tasks.add_argument("-k", type=int, default=5)
    oracle = commands.add_parser("oracle")
    oracle.add_argument("chunks")
    oracle.add_argument("seed")
    oracle.add_argument("--out", required=True)
    evaluate = commands.add_parser("evaluate")
    evaluate.add_argument("rankings")
    evaluate.add_argument("oracle")
    evaluate.add_argument("--out")
    iaa = commands.add_parser("iaa")
    iaa.add_argument("export")
    iaa.add_argument("--control", default="relevance")
    iaa.add_argument("--out")
    analyze = commands.add_parser("analyze")
    analyze.add_argument("export")
    analyze.add_argument("--control", default="relevance")
    analyze.add_argument("--out")
    return root


def _emit(result: dict, output: str | None = None) -> None:
    if output:
        write_json(output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main() -> None:
    args = parser().parse_args()
    if args.command == "fixture":
        _emit(create_fixture(args.out, args.pages))
    elif args.command == "demo":
        data_dir, workspace = Path(args.data_dir), Path(args.workspace)
        create_fixture(data_dir, args.pages)
        manifest = ingest_pdf(data_dir / "demo.pdf", workspace)
        run = workspace / manifest["document_id"] / manifest["pipeline_version"]
        generate_tasks(
            str(run / "chunks.jsonl"),
            str(data_dir / "queries.jsonl"),
            str(workspace / "tasks.json"),
            5,
            str(workspace / "ranking.jsonl"),
        )
        resolve_oracle(str(run / "chunks.jsonl"), str(data_dir / "oracle_seed.jsonl"), str(data_dir / "oracle.jsonl"))
        metrics = retrieval_metrics(read_jsonl(workspace / "ranking.jsonl"), read_jsonl(data_dir / "oracle.jsonl"))
        write_json(workspace / "evaluation.json", metrics)
        _emit({"manifest": manifest, "tasks": str(workspace / "tasks.json"), "evaluation": metrics})
    elif args.command == "ingest":
        _emit(ingest_pdf(args.pdf, args.workspace, args.pipeline_version, SplitConfig(args.chunk_size, args.overlap)))
    elif args.command == "tasks":
        _emit(
            {
                "tasks": len(generate_tasks(args.chunks, args.queries, args.out, args.k, args.ranking_out)),
                "output": args.out,
            }
        )
    elif args.command == "oracle":
        _emit({"queries": len(resolve_oracle(args.chunks, args.seed, args.out)), "output": args.out})
    elif args.command == "evaluate":
        _emit(evaluate_files(args.rankings, args.oracle), args.out)
    elif args.command in {"iaa", "analyze"}:
        export = json.loads(Path(args.export).read_text(encoding="utf-8"))
        result = (
            label_studio_agreement(export, args.control)
            if args.command == "iaa"
            else analyze_export(export, args.control)
        )
        _emit(result, args.out)


if __name__ == "__main__":
    main()
