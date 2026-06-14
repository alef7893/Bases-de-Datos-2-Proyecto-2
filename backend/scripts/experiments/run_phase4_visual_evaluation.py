"""Run the complete Phase 4 evaluation for application 01."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.common.config import load_project_config
from src.experiments.app01.evaluator import VisualPhase4Evaluator
from src.experiments.common.plots import generate_cross_scale_plots, generate_phase4_plots
from src.retrieval.postgres.image import PgvectorVisualRepository, VisualArtifactPostgresLoader
from src.persistence.postgres_client import PostgresClient


SCALES = ("1k", "10k", "full")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scales", nargs="+", choices=SCALES, default=list(SCALES))
    parser.add_argument("--queries", type=int, default=25)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--prepare-postgres", action="store_true")
    return parser.parse_args()


def _artifacts_available(config, scale: str) -> bool:
    directory = config.paths.artifacts_dir / "vision" / scale
    return all(
        path.exists()
        for path in (
            directory / "codebook.joblib",
            directory / "index" / "postings.jsonl",
            directory / "histograms",
        )
    )


def _tradeoffs(reports: dict[str, dict]) -> dict[str, str]:
    if not reports:
        return {}
    latest = reports[next(reversed(reports))]
    latency = {
        engine: values["mean_ms"] for engine, values in latest["latency"].items()
    }
    precision = latest["quality"]["precision_at_k"]
    throughput = latest["throughput_queries_per_second"]
    return {
        "lowest_latency": min(latency, key=latency.get),
        "highest_throughput": max(throughput, key=throughput.get),
        "highest_precision_at_k": max(precision, key=precision.get),
        "interpretation": (
            "El indice propio y HNSW comparten el mismo histograma. "
            "Las diferencias observadas corresponden al motor de recuperacion."
        ),
    }


def main() -> None:
    args = parse_args()
    if min(args.queries, args.top_k, args.repeats, args.concurrency) <= 0:
        raise ValueError("all experimental parameters must be positive")
    config = load_project_config()
    output_root = config.paths.reports_dir / "phase4"
    output_root.mkdir(parents=True, exist_ok=True)
    reports: dict[str, dict] = {}
    skipped: dict[str, str] = {}

    if args.prepare_postgres:
        PostgresClient(config.postgres).apply_sql_directory("sql")

    for scale in args.scales:
        if not _artifacts_available(config, scale):
            skipped[scale] = "visual artifacts are not built"
            continue
        if args.prepare_postgres:
            VisualArtifactPostgresLoader(config, scale).load()
            PgvectorVisualRepository(config.postgres).rebuild_hnsw_index(
                scale=scale,
                m=config.phase3.hnsw_m,
                ef_construction=config.phase3.hnsw_ef_construction,
            )
        report = VisualPhase4Evaluator(config, scale).evaluate(
            query_count=args.queries,
            top_k=args.top_k,
            repeats=args.repeats,
            concurrency=args.concurrency,
        )
        scale_dir = output_root / scale
        scale_dir.mkdir(parents=True, exist_ok=True)
        (scale_dir / "report.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        generate_phase4_plots(report, scale_dir / "plots")
        reports[scale] = report

    summary = {
        "application": "app01_visual_search",
        "requested_scales": args.scales,
        "completed_scales": list(reports),
        "skipped_scales": skipped,
        "tradeoffs": _tradeoffs(reports),
        "reports": reports,
    }
    (output_root / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    generate_cross_scale_plots(summary, output_root / "plots")
    print(json.dumps({key: value for key, value in summary.items() if key != "reports"}, indent=2))
    print(f"Summary: {output_root / 'summary.json'}")


if __name__ == "__main__":
    main()
