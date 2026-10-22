"""Product analysis service used by tests and fuzzers."""

from typing import Any

from .parser import InputParseError, parse_input
from .validator import validate_product


class ProductAnalyzer:
    """Validate and calculate derived values for one product."""

    def analyze(self, product: dict[str, Any]) -> dict[str, Any]:
        errors, warnings = validate_product(product)
        result: dict[str, Any] = {
            "valid": not errors,
            "final_price": None,
            "inventory_value": None,
            "average_rating": None,
            "errors": errors,
            "warnings": warnings,
        }
        if errors:
            return result

        price = product["price"]
        discount = product["discount"]
        stock = product["stock"]
        rating = product["rating"]
        result["final_price"] = round(price * (1 - discount / 100), 2)
        result["inventory_value"] = price * stock
        result["average_rating"] = rating

        norm_category = product["category"].strip().lower()

        # Inside-bounded branch 1: Camera warranty notice
        if norm_category == "camera":
            result["warnings"].append("Camera products should include a warranty description")

        # Inside-bounded branch 2: Missing description check
        if not product.get("description"):
            result["warnings"].append("Description is missing")

        # Inside-bounded branch 3: Inter-field stock & discount interactions
        if stock == 0 and discount > 0:
            result["warnings"].append("Discount is configured for an out-of-stock product")
        elif 0 < stock <= 5:
            result["warnings"].append("Low stock threshold reached (<=5 items remaining)")

        # Inside-bounded branch 4: Category-specific high discount rules
        if norm_category in {"camera", "electronics"}:
            if price >= 10_000_000 and discount > 20:
                result["warnings"].append("High-value electronics discount (>20%) requires manager review")
        elif norm_category == "book":
            if discount > 50:
                result["warnings"].append("Book discount exceeds standard publisher cap (50%)")

        # Inside-bounded branch 5: Full discount (free item) check
        if discount == 100:
            result["warnings"].append("100% discount applied: product is free of charge")

        # Inside-bounded branch 6: Rating-based product classification
        if rating >= 4.5 and stock > 10:
            result["badge"] = "BEST_SELLER"
        elif rating < 2.0:
            result["badge"] = "UNDER_REVIEW"
        else:
            result["badge"] = "STANDARD"

        return result

    def analyze_json(self, raw: str, input_format: str = "json") -> dict[str, Any]:
        try:
            product = parse_input(raw, input_format)
        except InputParseError as exc:
            return {
                "valid": False,
                "final_price": None,
                "inventory_value": None,
                "average_rating": None,
                "errors": [str(exc)],
                "warnings": [],
            }
        return self.analyze(product)
