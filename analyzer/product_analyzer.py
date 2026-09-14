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
        result["final_price"] = price * (1 - discount / 100)
        result["inventory_value"] = price * stock
        result["average_rating"] = rating
        if product["category"].strip().lower() == "camera":
            result["warnings"].append("Camera products should include a warranty description")
        if not product.get("description"):
            result["warnings"].append("Description is missing")
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
