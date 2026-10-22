"""Data dictionary and schema specification for product records.

Defines field constraints, types, size limits, and bounded regions
as specified in software testing requirements.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FieldSpec:
    name: str
    data_type: str
    required: bool
    description: str
    min_length: int | None = None
    max_length: int | None = None
    min_value: float | None = None
    max_value: float | None = None
    warning_threshold: float | None = None


PRODUCT_DATA_DICTIONARY: dict[str, FieldSpec] = {
    "id": FieldSpec(
        name="id",
        data_type="string",
        required=True,
        description="Unique product identifier code (e.g., P001)",
        min_length=1,
        max_length=50,
    ),
    "name": FieldSpec(
        name="name",
        data_type="string",
        required=True,
        description="Commercial product name",
        min_length=1,
        max_length=100,
    ),
    "category": FieldSpec(
        name="category",
        data_type="string",
        required=True,
        description="Product catalog category (e.g. Camera, Electronics, Book)",
        min_length=1,
        max_length=50,
    ),
    "price": FieldSpec(
        name="price",
        data_type="numeric (int or float)",
        required=True,
        description="Listed unit price in currency unit",
        min_value=0.0,
        max_value=1e12,
        warning_threshold=1e12,
    ),
    "stock": FieldSpec(
        name="stock",
        data_type="integer",
        required=True,
        description="Available inventory unit count",
        min_value=0,
        max_value=1_000_000,
        warning_threshold=1_000_000,
    ),
    "discount": FieldSpec(
        name="discount",
        data_type="numeric (int or float)",
        required=True,
        description="Promotional discount percentage",
        min_value=0.0,
        max_value=100.0,
    ),
    "rating": FieldSpec(
        name="rating",
        data_type="numeric (int or float)",
        required=True,
        description="Customer review rating score",
        min_value=0.0,
        max_value=5.0,
    ),
    "description": FieldSpec(
        name="description",
        data_type="string",
        required=False,
        description="Detailed text description of product features",
        min_length=0,
        max_length=1000,
        warning_threshold=1000,
    ),
}

# Bounded numeric and string regions for testing
BOUNDED_CONSTRAINTS: dict[str, dict[str, Any]] = {
    "price": {"min": 0.0, "max_nominal": 1e12},
    "stock": {"min": 0, "max_nominal": 1_000_000},
    "discount": {"min": 0.0, "max": 100.0},
    "rating": {"min": 0.0, "max": 5.0},
    "name_length": {"min": 1, "max": 100},
    "id_length": {"min": 1, "max": 50},
    "description_length": {"min": 0, "max": 1000},
}
