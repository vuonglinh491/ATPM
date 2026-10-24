"""Tests for SAT invariants verification, fault injection, and counterexample discovery."""

import csv
import json
import pytest

from analyzer.faulty_analyzer import FaultyProductAnalyzer
from fuzzing.sat_fuzzer import (
    CrashFuzzer,
    SATFuzzer,
    UnsafeMemoryFuzzer,
    verify_sat_invariants,
)


def test_sat_invariants_pass_on_valid_product():
    product = {"price": 1000, "discount": 10, "stock": 5}
    result = {"valid": True, "final_price": 900.0, "inventory_value": 5000}
    is_safe, inv, desc = verify_sat_invariants(product, result)
    assert is_safe is True
    assert inv == ""
    assert desc == ""


def test_sat_invariants_detect_price_increase_counterexample():
    # INV_1 violation: final_price > price
    product = {"price": 1000, "discount": 20, "stock": 5}
    result = {"valid": True, "final_price": 1200.0, "inventory_value": 5000}
    is_safe, inv, desc = verify_sat_invariants(product, result)
    assert is_safe is False
    assert inv == "INV_1_PRICE_INCREASE"
    assert "lớn hơn giá gốc" in desc


def test_sat_invariants_detect_negative_price_counterexample():
    # INV_2 violation: final_price < 0
    product = {"price": 1000, "discount": 150, "stock": 5}
    result = {"valid": True, "final_price": -500.0, "inventory_value": 5000}
    is_safe, inv, desc = verify_sat_invariants(product, result)
    assert is_safe is False
    assert inv == "INV_2_NEGATIVE_PRICE"
    assert "bị âm" in desc


def test_sat_invariants_detect_stock_inconsistency():
    # INV_3 violation: stock == 0 but inventory_value > 0
    product = {"price": 1000, "discount": 0, "stock": 0}
    result = {"valid": True, "final_price": 1000.0, "inventory_value": 5000}
    is_safe, inv, desc = verify_sat_invariants(product, result)
    assert is_safe is False
    assert inv == "INV_3_STOCK_INCONSISTENCY"


def test_faulty_analyzer_glitch_discount():
    analyzer = FaultyProductAnalyzer(enable_sat_logic_bugs=True)
    product = {
        "id": "P_GLITCH",
        "name": "Glitch Item",
        "category": "GLITCH_DISCOUNT",
        "price": 1000,
        "stock": 10,
        "discount": 20,
        "rating": 4.5,
    }
    result = analyzer.analyze(product)
    assert result["valid"] is True
    # Inverted formula: 1000 * (1 + 0.20) = 1200
    assert result["final_price"] == 1200.0
    assert result["final_price"] > product["price"]


def test_faulty_analyzer_negative_price():
    analyzer = FaultyProductAnalyzer(enable_sat_logic_bugs=True)
    product = {
        "id": "P_NEG",
        "name": "Negative Price Item",
        "category": "SAT_NEGATIVE_PRICE",
        "price": 1000,
        "stock": 10,
        "discount": 150,
        "rating": 4.0,
    }
    result = analyzer.analyze(product)
    assert result["valid"] is True
    # 1000 * (1 - 1.5) = -500
    assert result["final_price"] == -500.0


def test_faulty_analyzer_zero_division():
    analyzer = FaultyProductAnalyzer(enable_zero_division=True)
    product = {
        "id": "P_ZERO",
        "name": "Zero Rating Item",
        "category": "ZERO_DIV_TRIGGER",
        "price": 1000,
        "stock": 0,
        "discount": 0,
        "rating": 0,
    }
    with pytest.raises(ZeroDivisionError):
        analyzer.analyze(product)


def test_faulty_analyzer_runtime_crash():
    analyzer = FaultyProductAnalyzer(enable_runtime_crashes=True)
    product = {
        "id": "P_CRASH",
        "name": "Poison\x00NullByte",
        "category": "Other",
        "price": 1000,
        "stock": 1,
        "discount": 0,
        "rating": 4.0,
    }
    with pytest.raises(RuntimeError, match="Null-byte character"):
        analyzer.analyze(product)


def test_sat_fuzzer_discovers_counterexamples(tmp_path):
    report_file = tmp_path / "sat_report.csv"
    crash_dir = tmp_path / "crashes"
    fuzzer = SATFuzzer(crash_dir=crash_dir, seed=42)
    res = fuzzer.run(count=30, report_path=report_file)

    assert res["total_inputs"] == 30
    assert res["logic_bugs"] > 0
    assert res["counterexamples_found"] > 0
    assert report_file.exists()

    with report_file.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert any(r["result"] == "LOGIC_BUG" for r in rows)


def test_crash_fuzzer_discovers_runtime_crashes(tmp_path):
    report_file = tmp_path / "crash_report.csv"
    crash_dir = tmp_path / "crashes"
    fuzzer = CrashFuzzer(crash_dir=crash_dir, seed=77)
    res = fuzzer.run(count=25, report_path=report_file)

    assert res["total_inputs"] == 25
    assert res["crashes"] > 0
    assert report_file.exists()


def test_unsafe_memory_fuzzer_discovers_critical_faults(tmp_path):
    report_file = tmp_path / "unsafe_mem_report.csv"
    crash_dir = tmp_path / "crashes"
    fuzzer = UnsafeMemoryFuzzer(crash_dir=crash_dir, seed=99)
    res = fuzzer.run(count=25, report_path=report_file)

    assert res["total_inputs"] == 25
    assert res["critical_faults"] > 0
    assert report_file.exists()
