"""Business validation rules for products."""

from typing import Any

MAX_NAME_LENGTH = 100
REQUIRED_FIELDS = ("id", "name", "category", "price", "stock", "discount", "rating")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_product(product: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(product, dict):
        return ["Product must be an object"], warnings

    for field in REQUIRED_FIELDS:
        if field not in product:
            errors.append(f"Missing field: {field}")

    product_id = product.get("id")
    if "id" in product and (not isinstance(product_id, str) or not product_id.strip()):
        errors.append("Product ID must not be empty")

    name = product.get("name")
    if "name" in product and not isinstance(name, str):
        errors.append("Product name must be text")
    elif isinstance(name, str):
        if not name.strip():
            errors.append("Product name must not be empty")
        if len(name) > MAX_NAME_LENGTH:
            errors.append("Product name exceeds maximum length")

    category = product.get("category")
    if "category" in product and not isinstance(category, str):
        errors.append("Category must be text")

    price = product.get("price")
    if "price" in product and not _is_number(price):
        errors.append("Price must be numeric")
    elif _is_number(price) and price < 0:
        errors.append("Price must not be negative")

    stock = product.get("stock")
    if "stock" in product and not isinstance(stock, int):
        errors.append("Stock must be an integer")
    elif isinstance(stock, int) and not isinstance(stock, bool) and stock < 0:
        errors.append("Stock must not be negative")

    discount = product.get("discount")
    if "discount" in product and not _is_number(discount):
        errors.append("Discount must be numeric")
    elif _is_number(discount) and not 0 <= discount <= 100:
        errors.append("Discount must be between 0 and 100")

    rating = product.get("rating")
    if "rating" in product and not _is_number(rating):
        errors.append("Rating must be numeric")
    elif _is_number(rating) and not 0 <= rating <= 5:
        errors.append("Rating must be between 0 and 5")

    description = product.get("description", "")
    if description is not None and not isinstance(description, str):
        errors.append("Description must be text")
    elif isinstance(description, str) and len(description) > 1000:
        warnings.append("Description is unusually long")

    if isinstance(stock, int) and stock > 1000000:
        warnings.append("Stock is unusually large")
    if _is_number(price) and price > 10**12:
        warnings.append("Price is unusually large")
    return errors, warnings
