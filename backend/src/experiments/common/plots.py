"""Dependency-free SVG charts for Phase 4 reports."""

from __future__ import annotations

from pathlib import Path


COLORS = {
    "custom": "#2563eb",
    "hnsw": "#16a34a",
    "exact": "#9333ea",
    "postgres_gin_hnsw": "#dc2626",
}


def _bar_chart(title: str, values: dict[str, float], output: Path, unit: str) -> None:
    width, height = 760, 420
    margin, chart_height = 80, 260
    maximum = max(values.values()) if values else 1
    maximum = maximum or 1
    bar_width = 120
    gap = 80
    bars = []
    labels = []
    for index, (name, value) in enumerate(values.items()):
        x = margin + index * (bar_width + gap)
        bar_height = chart_height * value / maximum
        y = 330 - bar_height
        bars.append(
            f'<rect x="{x}" y="{y:.2f}" width="{bar_width}" height="{bar_height:.2f}" '
            f'fill="{COLORS.get(name, "#64748b")}"/>'
        )
        labels.append(f'<text x="{x + bar_width / 2}" y="355" text-anchor="middle">{name}</text>')
        labels.append(
            f'<text x="{x + bar_width / 2}" y="{y - 10:.2f}" text-anchor="middle">'
            f'{value:.3f} {unit}</text>'
        )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
        '<style>text{font-family:Arial,sans-serif;fill:#111827}</style>'
        f'<text x="30" y="40" font-size="22" font-weight="bold">{title}</text>'
        '<line x1="60" y1="330" x2="720" y2="330" stroke="#111827"/>'
        + "".join(bars + labels)
        + "</svg>"
    )
    output.write_text(svg, encoding="utf-8")


def generate_phase4_plots(report: dict, output_dir: str | Path) -> list[Path]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    charts = {
        "latency_mean.svg": (
            "Latencia promedio por motor",
            {name: values["mean_ms"] for name, values in report["latency"].items()},
            "ms",
        ),
        "throughput.svg": (
            "Throughput concurrente",
            report["throughput_queries_per_second"],
            "q/s",
        ),
        "precision_at_k.svg": (
            "Precision@K por motor",
            report["quality"]["precision_at_k"],
            "",
        ),
        "index_size.svg": (
            "Tamano de indice",
            {
                "custom": report["memory_and_storage"]["custom_index_disk_bytes"] / 1048576,
                "hnsw": report["memory_and_storage"]["hnsw_index_disk_bytes"] / 1048576,
            },
            "MiB",
        ),
    }
    paths = []
    for filename, (title, values, unit) in charts.items():
        path = directory / filename
        _bar_chart(title, values, path, unit)
        paths.append(path)
    return paths


def generate_multimodal_phase4_plots(
    report: dict, output_dir: str | Path
) -> list[Path]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    charts = {
        "latency_mean.svg": (
            "Latencia multimodal promedio",
            {name: values["mean_ms"] for name, values in report["latency"].items()},
            "ms",
        ),
        "throughput.svg": (
            "Throughput multimodal concurrente",
            report["throughput_queries_per_second"],
            "q/s",
        ),
        "precision_at_k.svg": (
            "Precision@K multimodal",
            report["quality"]["precision_at_k"],
            "",
        ),
        "index_size.svg": (
            "Tamano total de indices",
            {
                "custom": report["memory_and_storage"]["custom_index_disk_bytes"]
                / 1048576,
                "postgres_gin_hnsw": report["memory_and_storage"][
                    "postgres_index_disk_bytes"
                ]
                / 1048576,
            },
            "MiB",
        ),
    }
    paths = []
    for filename, (title, values, unit) in charts.items():
        path = directory / filename
        _bar_chart(title, values, path, unit)
        paths.append(path)
    return paths


def generate_cross_scale_plots(summary: dict, output_dir: str | Path) -> list[Path]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    reports = summary["reports"]
    paths = []
    for metric, title, unit in (
        ("latency", "Latencia promedio por escala y motor", "ms"),
        ("throughput", "Throughput por escala y motor", "q/s"),
        ("precision", "Precision@K por escala y motor", ""),
    ):
        values = {}
        for scale, report in reports.items():
            if metric == "latency":
                source = {name: item["mean_ms"] for name, item in report["latency"].items()}
            elif metric == "throughput":
                source = report["throughput_queries_per_second"]
            else:
                source = report["quality"]["precision_at_k"]
            values.update({f"{scale}-{name}": value for name, value in source.items()})
        path = directory / f"cross_scale_{metric}.svg"
        _bar_chart(title, values, path, unit)
        paths.append(path)
    return paths
