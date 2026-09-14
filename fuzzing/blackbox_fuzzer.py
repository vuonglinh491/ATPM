"""Black-box fuzzing: only input/output behavior is used by the oracle."""

import csv
import hashlib
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from pathlib import Path
from typing import Any, Callable

from .generators import generate_product, seed_corpus
from .mutations import mutate


def classify(result: dict[str, Any]) -> str:
    if not isinstance(result, dict):
        return "INVALID_OUTPUT"
    if result.get("valid") is True and result.get("errors"):
        return "LOGIC_BUG"
    return "VALID" if result.get("valid") else "INVALID"


class BlackBoxFuzzer:
    def __init__(self, program: Callable[[str], dict[str, Any]], crash_dir: str | Path = "crashes/blackbox", seed: int = 7):
        self.program = program
        self.crash_dir = Path(crash_dir)
        self.rng = random.Random(seed)
        self.seen: set[str] = set()

    def run(self, count: int = 100, timeout_seconds: float = 0.25, report_path: str | Path = "reports/blackbox_results.csv") -> dict[str, Any]:
        self.crash_dir.mkdir(parents=True, exist_ok=True)
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)
        counts = {key: 0 for key in ("VALID", "INVALID", "CRASH", "EXCEPTION", "TIMEOUT", "INVALID_OUTPUT", "LOGIC_BUG")}
        rows: list[dict[str, Any]] = []
        started = time.perf_counter()
        seeds = seed_corpus()
        for iteration in range(count):
            raw = self.rng.choice(seeds) if iteration < len(seeds) else (generate_product(self.rng) if self.rng.random() < 0.6 else mutate(self.rng.choice(seeds), self.rng))
            t0 = time.perf_counter()
            kind = ""
            error = ""
            result: Any = None
            try:
                with ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(self.program, raw)
                    result = future.result(timeout=timeout_seconds)
                kind = classify(result)
            except TimeoutError:
                kind = "TIMEOUT"
                error = "execution exceeded timeout"
            except Exception as exc:  # The black-box oracle records all program failures.
                kind = "EXCEPTION"
                error = f"{type(exc).__name__}: {exc}"
            duration = (time.perf_counter() - t0) * 1000
            counts[kind] += 1
            if kind in {"CRASH", "EXCEPTION", "LOGIC_BUG", "TIMEOUT", "INVALID_OUTPUT"}:
                self._save_failure(raw, kind, error, iteration)
            rows.append({"iteration": iteration, "input_type": "json", "result": kind, "error": error, "time_ms": round(duration, 4)})
        with Path(report_path).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys() if rows else ["iteration", "input_type", "result", "error", "time_ms"])
            writer.writeheader()
            writer.writerows(rows)
        elapsed = time.perf_counter() - started
        return {"total_inputs": count, **{key.lower(): value for key, value in counts.items()}, "unique_failures": len(self.seen), "execution_time_seconds": round(elapsed, 4), "average_time_ms": round((elapsed / count) * 1000, 4) if count else 0}

    def _save_failure(self, raw: str, kind: str, error: str, iteration: int) -> None:
        fingerprint = hashlib.sha256(f"{kind}:{error}".encode()).hexdigest()[:12]
        if fingerprint in self.seen:
            return
        self.seen.add(fingerprint)
        path = self.crash_dir / f"crash_{len(self.seen):03d}.json"
        path.write_text(json.dumps({"input": raw, "error": error, "type": kind, "iteration": iteration, "timestamp": time.time()}, ensure_ascii=False, indent=2), encoding="utf-8")
