"""Tests for deep branch exploration inside the bounded domain (White-box refinement)."""

from analyzer.product_analyzer import ProductAnalyzer
from fuzzing.generators import generate_boundary_blackbox, generate_bounded_whitebox


def test_out_of_stock_with_discount_warning():
    analyzer = ProductAnalyzer()
    product = {
        "id": "P101",
        "name": "Headphones",
        "category": "Electronics",
        "price": 500_000,
        "stock": 0,
        "discount": 20,
        "rating": 4.0,
        "description": "Valid description",
    }
    result = analyzer.analyze(product)
    assert result["valid"] is True
    assert "Discount is configured for an out-of-stock product" in result["warnings"]


def test_low_stock_warning():
    analyzer = ProductAnalyzer()
    product = {
        "id": "P102",
        "name": "Keyboard",
        "category": "Electronics",
        "price": 800_000,
        "stock": 3,
        "discount": 0,
        "rating": 4.2,
        "description": "Mechanical keyboard",
    }
    result = analyzer.analyze(product)
    assert result["valid"] is True
    assert "Low stock threshold reached (<=5 items remaining)" in result["warnings"]


def test_high_value_electronics_high_discount_manager_review():
    analyzer = ProductAnalyzer()
    product = {
        "id": "P103",
        "name": "High-end Laptop",
        "category": "Electronics",
        "price": 25_000_000,
        "stock": 10,
        "discount": 25,
        "rating": 4.8,
        "description": "Manager discount",
    }
    result = analyzer.analyze(product)
    assert result["valid"] is True
    assert "High-value electronics discount (>20%) requires manager review" in result["warnings"]


def test_book_discount_publisher_cap_warning():
    analyzer = ProductAnalyzer()
    product = {
        "id": "P104",
        "name": "Algorithms Textbook",
        "category": "Book",
        "price": 150_000,
        "stock": 20,
        "discount": 60,
        "rating": 4.9,
        "description": "DSA Book",
    }
    result = analyzer.analyze(product)
    assert result["valid"] is True
    assert "Book discount exceeds standard publisher cap (50%)" in result["warnings"]


def test_free_item_100_percent_discount_warning():
    analyzer = ProductAnalyzer()
    product = {
        "id": "P105",
        "name": "Free Gift Sticker",
        "category": "Other",
        "price": 10_000,
        "stock": 50,
        "discount": 100,
        "rating": 5.0,
        "description": "Gift",
    }
    result = analyzer.analyze(product)
    assert result["valid"] is True
    assert result["final_price"] == 0.0
    assert "100% discount applied: product is free of charge" in result["warnings"]


def test_product_tier_classification():
    analyzer = ProductAnalyzer()
    # Best seller
    best_seller = {
        "id": "P106",
        "name": "Top Item",
        "category": "Other",
        "price": 200_000,
        "stock": 15,
        "discount": 0,
        "rating": 4.9,
        "description": "Popular item",
    }
    assert analyzer.analyze(best_seller)["badge"] == "BEST_SELLER"

    # Under review
    under_review = {
        "id": "P107",
        "name": "Bad Item",
        "category": "Other",
        "price": 200_000,
        "stock": 15,
        "discount": 0,
        "rating": 1.2,
        "description": "Low rating",
    }
    assert analyzer.analyze(under_review)["badge"] == "UNDER_REVIEW"


def test_generator_boundary_blackbox_produces_json():
    import json
    for _ in range(20):
        raw = generate_boundary_blackbox()
        # Some are malformed strings by design at syntax boundaries
        assert isinstance(raw, str)


def test_generator_bounded_whitebox_always_valid():
    import json
    analyzer = ProductAnalyzer()
    for _ in range(50):
        raw = generate_bounded_whitebox()
        result = analyzer.analyze_json(raw)
        assert result["valid"] is True, f"Failed on input: {raw}, errors: {result['errors']}"
