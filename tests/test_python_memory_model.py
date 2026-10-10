import pytest

from fuzzing.memory_model import analyze_case, analyze_record


@pytest.mark.parametrize(
    ("operation", "first", "second", "status", "cwe"),
    [
        ("bounded", 100, 0, "SAFE", ""),
        ("bounded", 101, 0, "BLOCKED", "CWE-121"),
        ("overflow", 12, 8, "SAFE", ""),
        ("overflow", (1 << 64) - 1, 2, "BLOCKED", "CWE-190"),
        ("leak", 1, 0, "DETECTED", "CWE-401"),
        ("leak", 1, 1, "SAFE", ""),
        ("type", 0, 0, "SAFE", ""),
        ("type", 1, 0, "BLOCKED", "CWE-20"),
        ("null", 0, 0, "BLOCKED", "CWE-476"),
        ("null", 1, 0, "SAFE", ""),
        ("allocation", 1_048_576, 0, "SAFE", ""),
        ("allocation", 1_048_577, 0, "BLOCKED", "CWE-789"),
        ("lifecycle", 1, 0, "DETECTED", "CWE-401"),
        ("lifecycle", 1, 1, "SAFE", ""),
        ("lifecycle", 1, 2, "DETECTED", "CWE-415"),
        ("lifecycle", 1, 3, "DETECTED", "CWE-416"),
        ("type", 2, 2, "BLOCKED", "CWE-20"),
        ("null", 2, 0, "BLOCKED", "CWE-20"),
    ],
)
def test_memory_scenarios_match_expected_results(operation, first, second, status, cwe):
    result = analyze_case(operation, first, second)

    assert result["status"] == status
    assert result["cwe"] == cwe


@pytest.mark.parametrize(
    "record",
    ["bounded,1", "bounded,-1,0", "bounded,18446744073709551616,0", "operation-that-is-too-long,1,0"],
)
def test_malformed_records_are_blocked(record):
    result = analyze_record(record)

    assert result["status"] == "BLOCKED"
    assert result["cwe"] == "CWE-20"