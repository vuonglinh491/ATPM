"""Generate experiment summaries and charts from actual fuzzer output."""

import csv
import json
from pathlib import Path
from typing import Any


def read_results(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def generate_charts(report_dir: str | Path = "reports") -> list[str]:
    import matplotlib.pyplot as plt

    report_dir = Path(report_dir)
    chart_dir = report_dir / "charts"
    chart_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[str] = []
    blackbox = read_results(report_dir / "blackbox_results.csv") if (report_dir / "blackbox_results.csv").exists() else []
    whitebox = read_results(report_dir / "whitebox_results.csv") if (report_dir / "whitebox_results.csv").exists() else []
    if blackbox:
        counts: dict[str, int] = {}
        for row in blackbox:
            counts[row["result"]] = counts.get(row["result"], 0) + 1
        plt.figure(figsize=(7, 4))
        plt.bar(counts.keys(), counts.values(), color="#2878b5")
        plt.title("Black-box input outcomes")
        plt.ylabel("Inputs")
        plt.tight_layout()
        path = chart_dir / "input_results.png"
        plt.savefig(path, dpi=140)
        plt.close()
        outputs.append(str(path))
    if whitebox:
        points = [int(row["coverage_points"]) for row in whitebox]
        plt.figure(figsize=(7, 4))
        plt.plot(range(1, len(points) + 1), points, color="#d95f02")
        plt.title("White-box coverage feedback")
        plt.xlabel("Iteration")
        plt.ylabel("Covered lines")
        plt.tight_layout()
        path = chart_dir / "whitebox_coverage.png"
        plt.savefig(path, dpi=140)
        plt.close()
        outputs.append(str(path))
    return outputs


def save_summary(summary: dict[str, Any], path: str | Path = "reports/summary.json") -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
