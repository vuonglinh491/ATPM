"""Coverage-guided white-box fuzzer for the known analyzer implementation."""

import json
import random
from pathlib import Path
from typing import Any

import coverage

from analyzer.product_analyzer import ProductAnalyzer

from .generators import generate_product, seed_corpus
from .mutations import mutate


class WhiteBoxFuzzer:
    def __init__(self, crash_dir: str | Path = "crashes/whitebox", seed: int = 11):
        self.analyzer = ProductAnalyzer()
        self.crash_dir = Path(crash_dir)
        self.rng = random.Random(seed)

    def _execute_with_coverage(self, raw: str) -> tuple[dict[str, Any], frozenset[tuple[str, int]]]:
        collector = coverage.Coverage(source=["analyzer"], data_file=".whitebox_coverage")
        collector.start()
        try:
            result = self.analyzer.analyze_json(raw)
        finally:
            collector.stop()
            collector.save()
        data = collector.get_data()
        lines = frozenset((str(filename), line) for filename in data.measured_files() for line in (data.lines(filename) or []))
        return result, lines

    def run(self, count: int = 100, report_path: str | Path = "reports/whitebox_results.csv") -> dict[str, Any]:
        self.crash_dir.mkdir(parents=True, exist_ok=True)
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)
        corpus = seed_corpus()
        covered: set[tuple[str, int]] = set()
        crashes = 0
        rows = []
        for iteration in range(count):
            seed = self.rng.choice(corpus)
            raw = seed if iteration < len(corpus) else mutate(seed, self.rng) if self.rng.random() < 0.8 else generate_product(self.rng)
            try:
                result, current = self._execute_with_coverage(raw)
                if len(current - covered) > 0:
                    corpus.append(raw)
                    covered.update(current)
                kind = "VALID" if result.get("valid") else "INVALID"
                error = ""
            except Exception as exc:
                crashes += 1
                kind = "EXCEPTION"
                error = f"{type(exc).__name__}: {exc}"
                (self.crash_dir / f"crash_{crashes:03d}.json").write_text(json.dumps({"input": raw, "error": error, "iteration": iteration}, indent=2), encoding="utf-8")
            rows.append({"iteration": iteration, "result": kind, "coverage_points": len(covered), "error": error})
        import csv
        with Path(report_path).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        return {"total_inputs": count, "crashes": crashes, "coverage_points": len(covered), "corpus_size": len(corpus)}
