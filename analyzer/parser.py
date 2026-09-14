"""Input parsing for JSON and CSV product records."""

import csv
import io
import json
from typing import Any


class InputParseError(ValueError):
    """Raised when an input cannot be parsed as a product record."""


def parse_json(raw: str) -> dict[str, Any]:
    if not isinstance(raw, str):
        raise InputParseError("JSON input must be text")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InputParseError(f"Malformed JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise InputParseError("A product must be a JSON object")
    return value


def parse_csv(raw: str) -> dict[str, Any]:
    if not isinstance(raw, str):
        raise InputParseError("CSV input must be text")
    rows = list(csv.DictReader(io.StringIO(raw)))
    if len(rows) != 1:
        raise InputParseError("CSV input must contain exactly one product row")
    product = rows[0]
    for field in ("price", "stock", "discount", "rating"):
        value = product.get(field)
        if value is None:
            continue
        try:
            product[field] = float(value) if field == "rating" else int(value)
        except (TypeError, ValueError):
            pass
    return product


def parse_input(raw: str, input_format: str = "json") -> dict[str, Any]:
    if input_format.lower() == "csv":
        return parse_csv(raw)
    if input_format.lower() == "json":
        return parse_json(raw)
    raise InputParseError(f"Unsupported format: {input_format}")
