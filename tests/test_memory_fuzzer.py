import csv

import pytest

from fuzzing.memory_fuzzer import MemoryModelFuzzer


def test_memory_scenarios_cover_boundaries_and_lifecycle():
    cases = MemoryModelFuzzer()._cases(18)

    assert {case[0] for case in cases} == {"bounded", "overflow", "leak", "type", "null", "allocation", "lifecycle"}
    assert ("overflow", 18446744073709551615, 2) in cases
    assert ("bounded", 101, 0) in cases
    assert ("lifecycle", 1, 2) in cases


def test_python_memory_fuzzer_reports_expected_cwe_counts(tmp_path):
    report_path = tmp_path / "memory.csv"

    result = MemoryModelFuzzer().run(18, report_path)

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


def test_memory_fuzzer_rejects_negative_count():
    with pytest.raises(ValueError, match="count must be non-negative"):
        MemoryModelFuzzer().run(-1)