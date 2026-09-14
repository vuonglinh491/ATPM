import pytest

from analyzer.product_analyzer import ProductAnalyzer
from analyzer.validator import MAX_NAME_LENGTH


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("price", -1, "Price must not be negative"),
        ("stock", -1, "Stock must not be negative"),
        ("discount", 101, "Discount must be between 0 and 100"),
        ("rating", 5.1, "Rating must be between 0 and 5"),
        ("name", "A" * (MAX_NAME_LENGTH + 1), "Product name exceeds maximum length"),
    ],
)
def test_business_boundaries_are_rejected(field, value, message):
    product = {"id": "P", "name": "A", "category": "Other", "price": 1, "stock": 1, "discount": 0, "rating": 0}
    product[field] = value
    result = ProductAnalyzer().analyze(product)
    assert result["valid"] is False
    assert message in result["errors"]
