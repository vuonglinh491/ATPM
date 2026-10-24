"""SAT-guided fuzzing, invariant counterexample discovery, and fault injection simulation."""

import csv
import hashlib
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from pathlib import Path
from typing import Any, Callable

from analyzer.faulty_analyzer import FaultyProductAnalyzer
from analyzer.product_analyzer import ProductAnalyzer
from .generators import seed_corpus, valid_product
from .mutations import mutate


# Formal Invariants (Các bất biến hình thức của hệ thống)
# INV_1: final_price <= price (Khi discount >= 0, giá sau giảm không được vượt giá gốc)
# INV_2: final_price >= 0 và inventory_value >= 0 (Giá trị tài chính không được âm)
# INV_3: stock == 0 ==> inventory_value == 0 (Nhất quán tồn kho)
# INV_4: rating == 0 không gây ra lỗi chia cho 0 trong các chỉ số dẫn xuất


def verify_sat_invariants(product_raw: dict[str, Any], result: dict[str, Any]) -> tuple[bool, str, str]:
    """Verify safety invariants.

    If an invariant is violated, returns (False, invariant_name,
    counterexample_description). In SAT verification terminology:
    SAT(not Invariant) is SATISFIED, producing a counterexample.
    """
    if not isinstance(result, dict) or not result.get("valid"):
        # Rejected by validator safely: no invariant violated
        return True, "", ""

    price = product_raw.get("price")
    discount = product_raw.get("discount", 0)
    stock = product_raw.get("stock")
    final_price = result.get("final_price")
    inventory_val = result.get("inventory_value")

    # INV_1: final_price <= price
    if final_price is not None and price is not None and isinstance(discount, (int, float)) and discount >= 0:
        if final_price > price:
            return (
                False,
                "INV_1_PRICE_INCREASE",
                f"Phản ví dụ SAT (Vi phạm INV_1): Chiết khấu {discount}% nhưng giá sau giảm ({final_price:,} đ) lại lớn hơn giá gốc ({price:,} đ)!",
            )

    # INV_2: final_price >= 0
    if final_price is not None and final_price < 0:
        return (
            False,
            "INV_2_NEGATIVE_PRICE",
            f"Phản ví dụ SAT (Vi phạm INV_2): Giá sau giảm bị âm ({final_price:,} đ) do chiết khấu {discount}% vượt trần nhưng không bị chặn!",
        )

    # INV_2: inventory_value >= 0
    if inventory_val is not None and inventory_val < 0:
        return (
            False,
            "INV_2_NEGATIVE_INVENTORY",
            f"Phản ví dụ SAT (Vi phạm INV_2): Giá trị tồn kho bị âm ({inventory_val:,} đ)!",
        )

    # INV_3: stock == 0 ==> inventory_value == 0
    if stock == 0 and inventory_val is not None and inventory_val != 0:
        return (
            False,
            "INV_3_STOCK_INCONSISTENCY",
            f"Phản ví dụ SAT (Vi phạm INV_3): Số lượng tồn kho bằng 0 nhưng giá trị tồn kho ({inventory_val:,} đ) khác 0!",
        )

    return True, "", ""


def generate_sat_counterexample_input(rng: random.Random) -> str:
    """Generate inputs specifically designed to trigger SAT counterexamples and logic violations."""
    mode = rng.randrange(5)
    prod = valid_product()

    if mode == 0:
        # Trigger INV_1 violation: inverted glitch discount formula
        prod["id"] = f"SAT_INV1_{rng.randint(100, 999)}"
        prod["category"] = "GLITCH_DISCOUNT"
        prod["price"] = rng.choice([500_000, 1_500_000, 10_000_000])
        prod["discount"] = rng.choice([10.0, 25.0, 50.0])
        prod["rating"] = 4.5
        prod["description"] = "San pham gay loi tang gia sau giam"
    elif mode == 1:
        # Trigger INV_2 violation: discount > 100% causing negative final_price
        prod["id"] = f"SAT_INV2_{rng.randint(100, 999)}"
        prod["category"] = "SAT_NEGATIVE_PRICE"
        prod["price"] = 2_000_000
        prod["discount"] = 150
        prod["rating"] = 4.0
        prod["description"] = "Chiet khau 150% vuot tran gay gia am"
    elif mode == 2:
        # Trigger ZeroDivisionError / Arithmetic exception
        prod["id"] = f"SAT_ZERO_{rng.randint(100, 999)}"
        prod["category"] = "ZERO_DIV_TRIGGER"
        prod["price"] = 1_000_000
        prod["stock"] = 0
        prod["rating"] = 0
        prod["description"] = "Rating=0 gay chia cho 0 trong tinh toan hieu qua"
    elif mode == 3:
        # Boundary seed with glitch discount trigger
        prod["id"] = f"SAT_EDGE_{rng.randint(100, 999)}"
        prod["price"] = 100_000
        prod["discount"] = 99.9  # Trigger threshold
        prod["rating"] = 4.2
    else:
        # Normal bounded product
        prod["id"] = f"SAT_NORM_{rng.randint(100, 999)}"
        prod["price"] = 800_000
        prod["discount"] = 15.0
        prod["rating"] = 4.0

    return json.dumps(prod, ensure_ascii=False)


def generate_crash_payload(rng: random.Random) -> str:
    """Generate inputs designed to trigger runtime exceptions, null-byte injections, and parse panics."""
    mode = rng.randrange(4)
    prod = valid_product()

    if mode == 0:
        # Null byte injection in name
        prod["id"] = f"CRASH_N1_{rng.randint(100, 999)}"
        prod["name"] = f"Product\x00Poison_{rng.randint(10, 99)}"
        prod["description"] = "Null byte injected string"
    elif mode == 1:
        # Crash trigger category
        prod["id"] = f"CRASH_CAT_{rng.randint(100, 999)}"
        prod["category"] = "TRIGGER_CRASH"
        prod["description"] = "Virtual memory crash trigger"
    elif mode == 2:
        # Fatal raw payload
        return f'{{"id": "CRASH_RAW", "name": "Fatal", "category": "Other", "price": 100, "stock": 1, "discount": 0, "rating": 5, "extra": "__FATAL_PAYLOAD__"}}'
    else:
        # Zero division crash with rating 0
        prod["id"] = f"CRASH_ZDIV_{rng.randint(100, 999)}"
        prod["category"] = "ZERO_DIV_TRIGGER"
        prod["rating"] = 0
        prod["stock"] = 0

    return json.dumps(prod, ensure_ascii=False)


class SATFuzzer:
    """Fuzzer that searches for SAT counterexamples violating formal invariants."""

    def __init__(
        self,
        analyzer: Any | None = None,
        crash_dir: str | Path = "crashes/sat_counterexamples",
        seed: int = 42,
    ):
        self.analyzer = analyzer or FaultyProductAnalyzer(enable_sat_logic_bugs=True, enable_zero_division=True)
        self.crash_dir = Path(crash_dir)
        self.rng = random.Random(seed)
        self.counterexamples: list[dict[str, Any]] = []

    def run(
        self,
        count: int = 100,
        timeout_seconds: float = 0.25,
        report_path: str | Path = "reports/sat_fuzzing_results.csv",
    ) -> dict[str, Any]:
        self.crash_dir.mkdir(parents=True, exist_ok=True)
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)

        counts = {
            "VALID": 0,
            "INVALID": 0,
            "LOGIC_BUG": 0,  # SAT Counterexample
            "EXCEPTION": 0,
            "TIMEOUT": 0,
        }
        rows: list[dict[str, Any]] = []
        started = time.perf_counter()

        for iteration in range(count):
            if self.rng.random() < 0.6:
                raw = generate_sat_counterexample_input(self.rng)
            else:
                raw = mutate(generate_sat_counterexample_input(self.rng), self.rng)

            t0 = time.perf_counter()
            kind = ""
            error = ""
            invariant_name = ""
            result: Any = None

            try:
                with ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(self.analyzer.analyze_json, raw)
                    result = future.result(timeout=timeout_seconds)

                # Check if input was parsed as dict
                try:
                    product_dict = json.loads(raw)
                except Exception:
                    product_dict = {}

                if not isinstance(result, dict):
                    kind = "INVALID"
                elif not result.get("valid"):
                    kind = "INVALID"
                else:
                    # Check formal safety invariants!
                    sat_safe, inv_name, desc = verify_sat_invariants(product_dict, result)
                    if not sat_safe:
                        kind = "LOGIC_BUG"
                        invariant_name = inv_name
                        error = desc
                        self._save_counterexample(raw, inv_name, desc, result, iteration)
                    else:
                        kind = "VALID"

            except TimeoutError:
                kind = "TIMEOUT"
                error = "Thực thi vượt quá giới hạn thời gian (Timeout)"
            except Exception as exc:
                kind = "EXCEPTION"
                error = f"{type(exc).__name__}: {exc}"
                self._save_counterexample(raw, "CRASH_EXCEPTION", error, {}, iteration)

            duration = (time.perf_counter() - t0) * 1000
            counts[kind] += 1
            rows.append({
                "iteration": iteration,
                "result": kind,
                "invariant_violated": invariant_name,
                "details": error,
                "time_ms": round(duration, 4),
            })

        with Path(report_path).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["iteration", "result", "invariant_violated", "details", "time_ms"])
            writer.writeheader()
            writer.writerows(rows)

        elapsed = time.perf_counter() - started
        return {
            "type": "sat_simulation",
            "total_inputs": count,
            "valid": counts["VALID"],
            "invalid": counts["INVALID"],
            "logic_bugs": counts["LOGIC_BUG"],
            "exceptions": counts["EXCEPTION"],
            "timeouts": counts["TIMEOUT"],
            "counterexamples_found": len(self.counterexamples),
            "counterexample_details": [c["error"] for c in self.counterexamples[:5]],
            "execution_time_seconds": round(elapsed, 4),
            "report": str(report_path),
        }

    def _save_counterexample(self, raw: str, inv_name: str, desc: str, result: dict, iteration: int) -> None:
        record = {
            "iteration": iteration,
            "invariant": inv_name,
            "error": desc,
            "input": raw,
            "result": result,
            "timestamp": time.time(),
        }
        self.counterexamples.append(record)
        filename = f"sat_counterexample_{len(self.counterexamples):03d}.json"
        (self.crash_dir / filename).write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")


class CrashFuzzer:
    """Fuzzer targeting unhandled runtime crashes and fatal exception injection."""

    def __init__(
        self,
        crash_dir: str | Path = "crashes/runtime_crashes",
        seed: int = 77,
    ):
        self.analyzer = FaultyProductAnalyzer(enable_sat_logic_bugs=False, enable_runtime_crashes=True, enable_zero_division=True)
        self.crash_dir = Path(crash_dir)
        self.rng = random.Random(seed)
        self.crashes: list[dict[str, Any]] = []

    def run(
        self,
        count: int = 100,
        timeout_seconds: float = 0.25,
        report_path: str | Path = "reports/crash_simulation_results.csv",
    ) -> dict[str, Any]:
        self.crash_dir.mkdir(parents=True, exist_ok=True)
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)

        counts = {"VALID": 0, "INVALID": 0, "CRASH": 0}
        rows: list[dict[str, Any]] = []
        started = time.perf_counter()

        for iteration in range(count):
            if self.rng.random() < 0.6:
                raw = generate_crash_payload(self.rng)
            else:
                raw = mutate(generate_crash_payload(self.rng), self.rng)

            t0 = time.perf_counter()
            kind = ""
            error = ""

            try:
                result = self.analyzer.analyze_json(raw)
                kind = "VALID" if result.get("valid") else "INVALID"
            except Exception as exc:
                kind = "CRASH"
                error = f"{type(exc).__name__}: {exc}"
                self._save_crash(raw, error, iteration)

            duration = (time.perf_counter() - t0) * 1000
            counts[kind] += 1
            rows.append({
                "iteration": iteration,
                "result": kind,
                "error": error,
                "time_ms": round(duration, 4),
            })

        with Path(report_path).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["iteration", "result", "error", "time_ms"])
            writer.writeheader()
            writer.writerows(rows)

        elapsed = time.perf_counter() - started
        return {
            "type": "crash_simulation",
            "total_inputs": count,
            "valid": counts["VALID"],
            "invalid": counts["INVALID"],
            "crashes": counts["CRASH"],
            "crash_details": [c["error"] for c in self.crashes[:5]],
            "execution_time_seconds": round(elapsed, 4),
            "report": str(report_path),
        }

    def _save_crash(self, raw: str, error: str, iteration: int) -> None:
        record = {
            "iteration": iteration,
            "error": error,
            "input": raw,
            "timestamp": time.time(),
        }
        self.crashes.append(record)
        filename = f"runtime_crash_{len(self.crashes):03d}.json"
        (self.crash_dir / filename).write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")


class UnsafeMemoryFuzzer:
    """Memory fuzzer simulating critical memory violations (double-free, use-after-free crashes)."""

    def __init__(self, crash_dir: str | Path = "crashes/memory_faults", seed: int = 99):
        self.crash_dir = Path(crash_dir)
        self.rng = random.Random(seed)
        self.findings: list[dict[str, Any]] = []

    def run(
        self,
        count: int = 100,
        report_path: str | Path = "reports/unsafe_memory_results.csv",
    ) -> dict[str, Any]:
        from .memory_model import analyze_record

        self.crash_dir.mkdir(parents=True, exist_ok=True)
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)

        rows = []
        counts = {"SAFE": 0, "BLOCKED": 0, "DETECTED": 0, "CRITICAL_FAULT": 0}
        cwe_counter = {}

        for iteration in range(count):
            scenario = self.rng.choice(["bounded", "overflow", "leak", "lifecycle", "null", "allocation"])
            if scenario == "lifecycle":
                # Inject high rate of dangerous lifecycle operations (double-free, use-after-free)
                second = self.rng.choice([0, 1, 2, 3])
                first = 1
            elif scenario == "overflow":
                first = 18446744073709551615
                second = self.rng.choice([0, 2, 8])
            elif scenario == "bounded":
                first = self.rng.choice([50, 100, 105, 200])
                second = 0
            elif scenario == "leak":
                first = self.rng.choice([1, 4])
                second = self.rng.choice([0, 1])
            else:
                first = self.rng.choice([0, 1])
                second = 0

            res = analyze_record(f"{scenario},{first},{second}")
            status = res["status"]
            cwe = res["cwe"]
            details = res["details"]

            # Unsafe escalation: double-free (CWE-415) and use-after-free (CWE-416) are escalated to CRITICAL_FAULT
            if cwe in {"CWE-415", "CWE-416"}:
                status = "CRITICAL_FAULT"
                details = f"NGUY HIỂM CẤP ĐỘ CAO: Giả lập lỗi bộ nhớ nghiêm trọng ({cwe}) - Gây Crash tiến trình!"
                self._save_memory_fault(f"{scenario},{first},{second}", cwe, details, iteration)

            counts[status] = counts.get(status, 0) + 1
            if cwe:
                cwe_counter[cwe] = cwe_counter.get(cwe, 0) + 1

            rows.append({
                "iteration": iteration,
                "scenario": scenario,
                "result": status,
                "cwe": cwe,
                "details": details,
            })

        with Path(report_path).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["iteration", "scenario", "result", "cwe", "details"])
            writer.writeheader()
            writer.writerows(rows)

        return {
            "type": "unsafe_memory_simulation",
            "total_inputs": count,
            "safe": counts["SAFE"],
            "blocked": counts["BLOCKED"],
            "detected": counts["DETECTED"],
            "critical_faults": counts["CRITICAL_FAULT"],
            "cwe_counts": dict(sorted(cwe_counter.items())),
            "report": str(report_path),
        }

    def _save_memory_fault(self, record_text: str, cwe: str, details: str, iteration: int) -> None:
        item = {
            "iteration": iteration,
            "record": record_text,
            "cwe": cwe,
            "details": details,
            "timestamp": time.time(),
        }
        self.findings.append(item)
        filename = f"memory_fault_{len(self.findings):03d}.json"
        (self.crash_dir / filename).write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
