import csv

import pytest

from fuzzing.c_memory_fuzzer import CMemoryFuzzer, find_c_compiler


def test_native_scenarios_cover_memory_and_input_boundaries():
    cases = CMemoryFuzzer()._cases(18)

    assert {case[0] for case in cases} == {"bounded", "overflow", "leak", "type", "null", "allocation", "lifecycle"}
    assert ("overflow", 18446744073709551615, 2) in cases
    assert ("bounded", 101, 0) in cases
    assert ("lifecycle", 1, 2) in cases


def test_native_fuzzer_reports_compiler_unavailable(monkeypatch):
    monkeypatch.setattr("fuzzing.c_memory_fuzzer.find_c_compiler", lambda: None)

    result = CMemoryFuzzer().run(10)

    assert result["status"] == "SKIPPED"
    assert result["total_inputs"] == 0


@pytest.mark.skipif(find_c_compiler() is None, reason="requires gcc, clang, or cc")
def test_native_fuzzer_compiles_and_reports_cwe_findings(tmp_path):
    report_path = tmp_path / "native.csv"

    result = CMemoryFuzzer().run(18, report_path)

    assert result["status"] == "COMPLETED"
    assert result["total_inputs"] == 18
    assert result["cwe_counts"]["CWE-190"] == 1
    assert result["cwe_counts"]["CWE-401"] == 2
    assert result["cwe_counts"]["CWE-415"] == 1
    assert result["cwe_counts"]["CWE-416"] == 1
    assert result["cwe_counts"]["CWE-20"] == 3
    with report_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert all("cve" in row and row["cve"] == "" for row in rows)