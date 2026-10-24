"""Fault-injected ProductAnalyzer simulating logic bugs, runtime crashes, and SAT counterexamples."""

from typing import Any

from .parser import InputParseError, parse_input
from .product_analyzer import ProductAnalyzer
from .validator import validate_product


class FaultyProductAnalyzer(ProductAnalyzer):
    """Product analyzer variant with configurable fault-injection hooks.

    Used to demonstrate fuzzer bug-catching capabilities, SAT counterexample
    generation, and unhandled exception logging.
    """

    def __init__(
        self,
        enable_sat_logic_bugs: bool = True,
        enable_runtime_crashes: bool = True,
        enable_zero_division: bool = True,
    ):
        super().__init__()
        self.enable_sat_logic_bugs = enable_sat_logic_bugs
        self.enable_runtime_crashes = enable_runtime_crashes
        self.enable_zero_division = enable_zero_division

    def analyze(self, product: dict[str, Any]) -> dict[str, Any]:
        # Fault trigger 1: Runtime Crash / Critical unhandled exception simulation
        # Triggered when input contains specific poison tokens or special numeric edge cases
        if self.enable_runtime_crashes:
            description = str(product.get("description", ""))
            name = str(product.get("name", ""))
            if "\x00" in name or "\x00" in description:
                raise RuntimeError("Unhandled Native Crash: Null-byte character caused buffer deserialization fault!")
            if product.get("category") == "TRIGGER_CRASH":
                raise MemoryError("Unhandled Process Crash: Virtual memory allocation failure simulation!")

        errors, warnings = validate_product(product)

        # Fault trigger 2: SAT Counterexample - Bypass validation for extreme discounts
        # Simulates a validation flaw where discount > 100% or negative discount bypasses checks
        if self.enable_sat_logic_bugs and isinstance(product, dict):
            discount_val = product.get("discount")
            # If discount is 150%, simulate validator oversight -> final_price becomes negative!
            if discount_val == 150 or product.get("category") == "SAT_NEGATIVE_PRICE":
                errors = [e for e in errors if "Discount must be between" not in e]

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

        # Fault trigger 3: SAT Counterexample - Inverted discount formula
        # Price Reduction Invariant (final_price <= price) is violated!
        # Simulates a calculation regression where discount increases price instead of lowering it.
        if self.enable_sat_logic_bugs and (product.get("category") == "GLITCH_DISCOUNT" or discount == 99.9):
            result["final_price"] = round(price * (1 + discount / 100), 2)
            warnings.append("FAULT_INJECTED: Glitch formula applied price surge instead of discount")
        else:
            result["final_price"] = round(price * (1 - discount / 100), 2)

        result["inventory_value"] = price * stock
        result["average_rating"] = rating

        # Fault trigger 4: ZeroDivisionError arithmetic exception
        # Simulates an unhandled metric calculation when rating is 0.0
        if self.enable_zero_division and rating == 0:
            if product.get("category") == "ZERO_DIV_TRIGGER" or stock == 0:
                # Deliberate unhandled arithmetic failure
                result["rating_efficiency"] = price / rating

        norm_category = product["category"].strip().lower()

        # Regular business rules
        if norm_category == "camera":
            result["warnings"].append("Camera products should include a warranty description")
        if not product.get("description"):
            result["warnings"].append("Description is missing")
        if stock == 0 and discount > 0:
            result["warnings"].append("Discount is configured for an out-of-stock product")
        elif 0 < stock <= 5:
            result["warnings"].append("Low stock threshold reached (<=5 items remaining)")

        if norm_category in {"camera", "electronics"}:
            if price >= 10_000_000 and discount > 20:
                result["warnings"].append("High-value electronics discount (>20%) requires manager review")
        elif norm_category == "book":
            if discount > 50:
                result["warnings"].append("Book discount exceeds standard publisher cap (50%)")

        if discount == 100:
            result["warnings"].append("100% discount applied: product is free of charge")

        if rating >= 4.5 and stock > 10:
            result["badge"] = "BEST_SELLER"
        elif rating < 2.0:
            result["badge"] = "UNDER_REVIEW"
        else:
            result["badge"] = "STANDARD"

        return result

    def analyze_json(self, raw: str, input_format: str = "json") -> dict[str, Any]:
        # Crash trigger on raw level (e.g. unhandled surrogate / control bytes)
        if self.enable_runtime_crashes and "__FATAL_PAYLOAD__" in raw:
            raise SystemError("Fatal Engine Crash: Malicious binary payload injected into JSON deserializer!")

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
