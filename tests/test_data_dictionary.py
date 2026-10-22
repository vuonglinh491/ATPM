"""Tests for the product schema and data dictionary."""

from analyzer.schema import BOUNDED_CONSTRAINTS, PRODUCT_DATA_DICTIONARY


def test_schema_contains_all_eight_fields():
    expected_fields = {"id", "name", "category", "price", "stock", "discount", "rating", "description"}
    assert set(PRODUCT_DATA_DICTIONARY.keys()) == expected_fields


def test_schema_required_fields_specification():
    required = {k for k, v in PRODUCT_DATA_DICTIONARY.items() if v.required}
    assert required == {"id", "name", "category", "price", "stock", "discount", "rating"}
    assert PRODUCT_DATA_DICTIONARY["description"].required is False


def test_bounded_constraints_specification():
    assert BOUNDED_CONSTRAINTS["discount"]["min"] == 0.0
    assert BOUNDED_CONSTRAINTS["discount"]["max"] == 100.0
    assert BOUNDED_CONSTRAINTS["rating"]["min"] == 0.0
    assert BOUNDED_CONSTRAINTS["rating"]["max"] == 5.0
    assert BOUNDED_CONSTRAINTS["name_length"]["max"] == 100
    assert BOUNDED_CONSTRAINTS["price"]["min"] == 0.0
