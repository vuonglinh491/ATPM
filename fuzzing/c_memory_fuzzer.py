"""Deterministic fuzzing for the native product-memory model."""

import csv
import os
import random
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any


def find_c_compiler() -> str | None:
    for candidate in ("gcc", "clang", "cc"):
        compiler = shutil.which(candidate)
        if compiler:
            return compiler
    return None


class CMemoryFuzzer:
    def __init__(self, seed: int = 23, source_path: str | Path = "c_targets/product_memory_model.c"):
        self.rng = random.Random(seed)
        self.source_path = Path(source_path)

    def _cases(self, count: int) -> list[tuple[str, int, int]]:
        scenarios = [
            ("bounded", 100, 0),
            ("bounded", 101, 0),
            ("overflow", 12, 8),
            ("overflow", 18446744073709551615, 2),
            ("leak", 1, 0),
            ("leak", 1, 1),
            ("type", 0, 0),
            ("type", 1, 0),
            ("null", 0, 0),
            ("null", 1, 0),
            ("allocation", 1048576, 0),
            ("allocation", 1048577, 0),
            ("lifecycle", 1, 0),
            ("lifecycle", 1, 1),
            ("lifecycle", 1, 2),
            ("lifecycle", 1, 3),
            ("type", 2, 2),
            ("null", 2, 0),
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

    def run(self, count: int = 100, report_path: str | Path = "reports/c_memory_results.csv") -> dict[str, Any]:
        if count < 0:
            raise ValueError("count must be non-negative")
        compiler = find_c_compiler()
        if compiler is None:
            return {"status": "SKIPPED", "reason": "No gcc, clang, or cc compiler found", "total_inputs": 0}

        source_path = self.source_path.resolve()
        if not source_path.is_file():
            raise FileNotFoundError(f"C target not found: {source_path}")
        cases = self._cases(count)
        report = Path(report_path)
        report.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="product-memory-fuzz-") as temporary_directory:
            executable = Path(temporary_directory) / ("memory_model.exe" if os.name == "nt" else "memory_model")
            build = subprocess.run(
                [compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", "-O2", str(source_path), "-o", str(executable)],
                capture_output=True,
                text=True,
                check=False,
            )
            if build.returncode:
                raise RuntimeError(f"C target compilation failed: {build.stderr.strip()}")
            payload = "".join(f"{operation},{first},{second}\n" for operation, first, second in cases)
            execution = subprocess.run([str(executable)], input=payload, capture_output=True, text=True, check=False)
        if execution.returncode:
            raise RuntimeError(f"C target execution failed: {execution.stderr.strip()}")

        outputs = execution.stdout.splitlines()
        if len(outputs) != len(cases):
            raise RuntimeError(f"Expected {len(cases)} native results, received {len(outputs)}")
        rows = []
        for iteration, (case, output) in enumerate(zip(cases, outputs)):
            fields = output.split("\t", 2)
            if len(fields) != 3:
                fields = ["INVALID", "CWE-20", "malformed native result"]
            status, cwe, details = fields
            rows.append({
                "iteration": iteration,
                "scenario": case[0],
                "result": status,
                "cwe": cwe,
                "cve": "",
                "details": details,
            })
        with report.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=("iteration", "scenario", "result", "cwe", "cve", "details"))
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