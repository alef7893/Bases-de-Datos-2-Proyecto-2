"""Run the complete Phase 4 evaluation for application 04."""

from __future__ import annotations

import argparse
import json

from src.common.config import load_project_config
from src.experiments.app04.evaluator import MultimodalPhase4Evaluator
from src.experiments.common.plots import (
    generate_cross_scale_plots,
    generate_multimodal_phase4_plots,
)
from src.retrieval.postgres.image import PgvectorVisualRepository
from src.persistence.postgres_client import PostgresClient
from src.persistence.artifact_loader import ArtifactPostgresLoader


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
    artifacts = config.paths.artifacts_dir
    return all(
        path.exists()
        for path in (
            artifacts / "text" / scale / "codebook.json",
            artifacts / "text" / scale / "index" / "postings.jsonl",
            artifacts / "vision" / scale / "codebook.joblib",
            artifacts / "vision" / scale / "index" / "postings.jsonl",
            artifacts / "vision" / scale / "histograms",
        )
    )


def _tradeoffs(reports: dict[str, dict]) -> dict[str, str]:
    if not reports:
        return {}
    largest = reports[next(reversed(reports))]
    latency = {
        engine: values["mean_ms"] for engine, values in largest["latency"].items()
    }
    precision = largest["quality"]["precision_at_k"]
    throughput = largest["throughput_queries_per_second"]
    storage = {
        "custom": largest["memory_and_storage"]["custom_index_disk_bytes"],
        "postgres_gin_hnsw": largest["memory_and_storage"][
            "postgres_index_disk_bytes"
        ],
    }
    return {
        "lowest_latency": min(latency, key=latency.get),
        "highest_throughput": max(throughput, key=throughput.get),
        "highest_precision_at_k": max(precision, key=precision.get),
        "lowest_index_storage": min(storage, key=storage.get),
        "interpretation": (
            "Ambos motores procesan el mismo producto y aplican la misma fusion "
            "ponderada. Las diferencias corresponden a los motores de recuperacion: "
            "indices invertidos propios frente a PostgreSQL GIN y pgvector HNSW."
        ),
    }


def _conclusions(reports: dict[str, dict], skipped: dict[str, str]) -> dict:
    if not reports:
        return {
            "status": "No scale could be evaluated",
            "limitations": list(skipped.values()),
        }
    largest_scale = next(reversed(reports))
    report = reports[largest_scale]
    overlap = report["quality"]["ranking_overlap_at_k"]
    precision = report["quality"]["precision_at_k"]
    latency = {
        engine: values["mean_ms"] for engine, values in report["latency"].items()
    }
    return {
        "evaluated_largest_available_scale": largest_scale,
        "winner_by_latency": min(latency, key=latency.get),
        "winner_by_precision_at_k": max(precision, key=precision.get),
        "same_information_recovered": {
            "ranking_overlap_at_k": overlap,
            "interpretation": (
                "Los motores recuperan conjuntos parcialmente equivalentes; "
                "el solapamiento no implica relevancia semantica perfecta."
            ),
        },
        "limitations": [
            "articleType is used as a relevance proxy because no external multimodal judgments exist",
            "the dataset contains about 44k products, so full replaces the requested 100k workload",
            "only scales with complete text and visual artifacts can be evaluated",
            *[f"{scale}: {reason}" for scale, reason in skipped.items()],
        ],
        "recommendation": (
            "Use the custom engine when latency and current Precision@K are the priority. "
            "Use PostgreSQL GIN + HNSW when lower index storage, persistence, and native "
            "database operations are more important."
        ),
    }


def main() -> None:
    args = parse_args()
    if min(args.queries, args.top_k, args.repeats, args.concurrency) <= 0:
        raise ValueError("all experimental parameters must be positive")
    config = load_project_config()
    output_root = config.paths.reports_dir / "phase4" / "app04"
    output_root.mkdir(parents=True, exist_ok=True)
    reports: dict[str, dict] = {}
    skipped: dict[str, str] = {}

    if args.prepare_postgres:
        PostgresClient(config.postgres).apply_sql_directory("sql")

    for scale in args.scales:
        if not _artifacts_available(config, scale):
            skipped[scale] = "text or visual artifacts are not built"
            continue
        if args.prepare_postgres:
            ArtifactPostgresLoader(config, scale).load(
                run_id=f"phase4-app04-load-{scale}"
            )
            PgvectorVisualRepository(config.postgres).rebuild_hnsw_index(
                scale=scale,
                m=config.phase3.hnsw_m,
                ef_construction=config.phase3.hnsw_ef_construction,
            )
        report = MultimodalPhase4Evaluator(config, scale).evaluate(
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
        generate_multimodal_phase4_plots(report, scale_dir / "plots")
        reports[scale] = report

    summary = {
        "application": "app04_multimodal_recommender",
        "requested_scales": args.scales,
        "completed_scales": list(reports),
        "skipped_scales": skipped,
        "tradeoffs": _tradeoffs(reports),
        "conclusions": _conclusions(reports, skipped),
        "reports": reports,
    }
    (output_root / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    generate_cross_scale_plots(summary, output_root / "plots")
    print(
        json.dumps(
            {key: value for key, value in summary.items() if key != "reports"},
            indent=2,
        )
    )
    print(f"Summary: {output_root / 'summary.json'}")


if __name__ == "__main__":
    main()
