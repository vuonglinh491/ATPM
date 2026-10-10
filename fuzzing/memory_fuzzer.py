"""Deterministic fuzzing for the simulated product-memory model."""

import csv
import random
from collections import Counter
from pathlib import Path
from typing import Any

from .memory_model import analyze_record


class MemoryModelFuzzer:
    def __init__(self, seed: int = 23):
        self.rng = random.Random(seed)

    def _cases(self, count: int) -> list[tuple[str, int, int]]:
        scenarios = [
            ("bounded", 100, 0), ("bounded", 101, 0),
            ("overflow", 12, 8), ("overflow", 18446744073709551615, 2),
            ("leak", 1, 0), ("leak", 1, 1), ("type", 0, 0), ("type", 1, 0),
            ("null", 0, 0), ("null", 1, 0), ("allocation", 1048576, 0),
            ("allocation", 1048577, 0), ("lifecycle", 1, 0), ("lifecycle", 1, 1),
            ("lifecycle", 1, 2), ("lifecycle", 1, 3), ("type", 2, 2), ("null", 2, 0),
        ]
        cases = scenarios[:count]
        while len(cases) < count:
            operation = self.rng.choice(("bounded", "overflow", "leak", "type", "null", "allocation", "lifecycle"))
            if operation == "bounded":
                case = (operation, self.rng.choice((0, 1, 99, 100, 101, 4096)), 0)
            elif operation == "overflow":
                case = (operation, self.rng.choice((0, 1, 2, 1024, 18446744073709551615)), self.rng.choice((0, 2, 8, 1024)))
            elif operation == "leak":
                case = (operation, self.rng.choice((0, 1, 2, 64)), self.rng.choice((0, 1)))
            elif operation == "type":
                case = (operation, self.rng.choice((0, 1, 2)), self.rng.choice((0, 1)))
            elif operation == "null":
                case = (operation, self.rng.choice((0, 1, 2)), 0)
            elif operation == "lifecycle":
                case = (operation, 1, self.rng.choice((0, 1, 2, 3)))
            else:
                case = (operation, self.rng.choice((0, 1, 1048576, 1048577, 4294967296)), 0)
            cases.append(case)
        return cases

    def run(self, count: int = 100, report_path: str | Path = "reports/memory_results.csv") -> dict[str, Any]:
        if count < 0:
            raise ValueError("count must be non-negative")

        cases = self._cases(count)
        report = Path(report_path)
        report.parent.mkdir(parents=True, exist_ok=True)
        rows = []
        for iteration, (operation, first, second) in enumerate(cases):
            result = analyze_record(f"{operation},{first},{second}")
            rows.append({
                "iteration": iteration,
                "scenario": operation,
                "result": result["status"],
                "cwe": result["cwe"],
                "cve": "",
                "details": result["details"],
            })

        fieldnames = ("iteration", "scenario", "result", "cwe", "cve", "details")
        with report.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        counts = Counter(row["result"] for row in rows)
        cwe_counts = Counter(row["cwe"] for row in rows if row["cwe"])
        return {
            "status": "COMPLETED",
            "total_inputs": count,
            "safe": counts["SAFE"],
            "blocked": counts["BLOCKED"],
            "findings": counts["DETECTED"],
            "cwe_counts": dict(sorted(cwe_counts.items())),
            "report": str(report),
        }