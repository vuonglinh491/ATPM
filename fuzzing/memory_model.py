"""Pure-Python simulation of the project's native memory test cases."""

MAX_NAME_LENGTH = 100
MAX_ALLOCATION = 1_048_576
UINT64_MAX = (1 << 64) - 1
INVALID_RESULT = {
    "status": "BLOCKED",
    "cwe": "CWE-20",
    "details": "input record could not be parsed",
}


def _parse_unsigned(text: str) -> int | None:
    value = text.lstrip(" \t\n\r\v\f")
    if value.startswith("+"):
        value = value[1:]
    if not value or not value.isascii() or not value.isdigit():
        return None
    parsed = int(value)
    return parsed if parsed <= UINT64_MAX else None


def analyze_record(record: str) -> dict[str, str]:
    """Parse and analyze one operation, matching the original C harness."""
    fields = record.rstrip("\n").split(",")
    if len(fields) != 3:
        return INVALID_RESULT.copy()

    operation, first_text, second_text = fields
    if not operation or len(operation.encode("utf-8")) >= 16:
        return INVALID_RESULT.copy()

    first = _parse_unsigned(first_text)
    second = _parse_unsigned(second_text)
    if first is None or second is None:
        return INVALID_RESULT.copy()

    if operation == "bounded":
        if first > MAX_NAME_LENGTH:
            return {"status": "BLOCKED", "cwe": "CWE-121", "details": "stack buffer overflow attempt rejected before copy"}
        return {"status": "SAFE", "cwe": "", "details": "name length is within the declared bound"}

    if operation == "overflow":
        if first and second > UINT64_MAX // first:
            return {"status": "BLOCKED", "cwe": "CWE-190", "details": "allocation size multiplication overflow rejected"}
        return {"status": "SAFE", "cwe": "", "details": "allocation size multiplication is representable"}

    if operation == "leak":
        if second > 1:
            return {"status": "BLOCKED", "cwe": "CWE-20", "details": "invalid release flag rejected"}
        if first > 0 and second == 0:
            return {"status": "DETECTED", "cwe": "CWE-401", "details": "simulated owned allocations are not released"}
        return {"status": "SAFE", "cwe": "", "details": "simulated allocations are released"}

    if operation == "lifecycle":
        if first == 0:
            return {"status": "SAFE", "cwe": "", "details": "no allocation is owned"}
        if second == 0:
            return {"status": "DETECTED", "cwe": "CWE-401", "details": "owned allocation leaves scope without release"}
        if second == 2:
            return {"status": "DETECTED", "cwe": "CWE-415", "details": "second release detected by the simulated ownership state"}
        if second == 3:
            return {"status": "DETECTED", "cwe": "CWE-416", "details": "access after release detected by the simulated ownership state"}
        if second == 1:
            return {"status": "SAFE", "cwe": "", "details": "allocation is released exactly once"}
        return {"status": "BLOCKED", "cwe": "CWE-20", "details": "unknown lifecycle operation rejected"}

    if operation == "type":
        if first > 1 or second > 1 or first != second:
            return {"status": "BLOCKED", "cwe": "CWE-20", "details": "input type does not match the expected field type"}
        return {"status": "SAFE", "cwe": "", "details": "input type matches the expected field type"}

    if operation == "null":
        if first > 1:
            return {"status": "BLOCKED", "cwe": "CWE-20", "details": "invalid pointer-presence flag rejected"}
        if first == 0:
            return {"status": "BLOCKED", "cwe": "CWE-476", "details": "missing required pointer rejected before dereference"}
        return {"status": "SAFE", "cwe": "", "details": "required pointer is present"}

    if operation == "allocation":
        if first > MAX_ALLOCATION:
            return {"status": "BLOCKED", "cwe": "CWE-789", "details": "allocation request exceeds the configured cap"}
        return {"status": "SAFE", "cwe": "", "details": "allocation request is within the configured cap"}

    return {"status": "BLOCKED", "cwe": "CWE-20", "details": "unknown operation rejected"}


def analyze_case(operation: str, first: int, second: int) -> dict[str, str]:
    """Convenience API for callers that already have parsed fields."""
    return analyze_record(f"{operation},{first},{second}")