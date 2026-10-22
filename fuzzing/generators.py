"""Input generators for black-box boundary testing and white-box internal branch testing."""

import json
import random
from typing import Any


def valid_product() -> dict[str, Any]:
    return {
        "id": "P001",
        "name": "Product",
        "category": "Other",
        "price": 100,
        "stock": 5,
        "discount": 0,
        "rating": 4,
        "description": "demo",
    }


def generate_boundary_blackbox(rng: random.Random | None = None) -> str:
    """Generate inputs specifically targeted at the boundaries of the bounded domain."""
    rng = rng or random.Random()
    product = valid_product()
    mode = rng.randrange(12)

    if mode == 0:
        # Boundary discount: min-, min, min+, max-, max, max+
        product["discount"] = rng.choice([-0.01, 0.0, 0.01, 50.0, 99.99, 100.0, 100.01])
    elif mode == 1:
        # Boundary rating: min-, min, min+, max-, max, max+
        product["rating"] = rng.choice([-0.1, 0.0, 0.1, 2.5, 4.9, 5.0, 5.1])
    elif mode == 2:
        # Boundary price: negative, zero, positive, threshold, over-threshold
        product["price"] = rng.choice([-1, 0, 1, 10**6, 10**12, 10**12 + 1])
    elif mode == 3:
        # Boundary stock: negative, zero, positive, threshold, over-threshold
        product["stock"] = rng.choice([-1, 0, 1, 5, 1_000_000, 1_000_001])
    elif mode == 4:
        # Boundary name length: 0, 1, 100, 101
        product["name"] = rng.choice(["", "A", "A" * 100, "A" * 101])
    elif mode == 5:
        # Boundary id: empty string, whitespace only, valid short id
        product["id"] = rng.choice(["", "   ", "\t\n", "P001"])
    elif mode == 6:
        # Type violation boundaries (None, non-numeric strings, booleans)
        field = rng.choice(["price", "stock", "discount", "rating"])
        product[field] = rng.choice([None, True, False, "invalid_num", [], {}])
    elif mode == 7:
        # Missing required field
        product.pop(rng.choice(["id", "name", "category", "price", "stock", "discount", "rating"]))
    elif mode == 8:
        # Malformed syntax at parser boundary
        return rng.choice(["", "{", "}", "[]", '{"id":', '{"id": "P1",}'])
    elif mode == 9:
        # Empty dictionary
        return "{}"
    elif mode == 10:
        # Boundary description length: 0, 1000, 1001
        product["description"] = rng.choice(["", "D" * 1000, "D" * 1001])
    else:
        # Extreme numbers / numeric stress
        product["price"] = rng.choice([2**31 - 1, 2**63 - 1, 10**20])

    return json.dumps(product, ensure_ascii=False)


def generate_bounded_whitebox(rng: random.Random | None = None) -> str:
    """Generate inputs strictly INSIDE the bounded region, targeting deep internal branches."""
    rng = rng or random.Random()
    product = valid_product()
    branch_scenario = rng.randrange(9)

    categories = ["Camera", "Electronics", "Book", "Clothing", "Other"]

    if branch_scenario == 0:
        # Branch: Camera category with and without warranty/description
        product["category"] = "Camera"
        product["name"] = "Sony Alpha A7"
        product["price"] = 35_000_000
        product["stock"] = 15
        product["discount"] = rng.choice([0, 10, 15])
        product["rating"] = 4.8
        product["description"] = rng.choice(["", "Chinh hang bao hanh 24 thang"])
    elif branch_scenario == 1:
        # Branch: High-value Electronics with high discount (>20%) requiring manager review
        product["category"] = "Electronics"
        product["name"] = "MacBook Pro M3"
        product["price"] = rng.choice([12_000_000, 25_000_000, 45_000_000])
        product["discount"] = rng.choice([25.0, 30.0, 50.0])
        product["stock"] = 8
        product["rating"] = 4.7
        product["description"] = "Laptop cao cap"
    elif branch_scenario == 2:
        # Branch: Book publisher cap rule (discount > 50%)
        product["category"] = "Book"
        product["name"] = "Giao trinh Kiem thu Phan mem"
        product["price"] = 120_000
        product["stock"] = 50
        product["discount"] = rng.choice([30.0, 55.0, 70.0])
        product["rating"] = 4.6
        product["description"] = "Sach chuyen nganh CNTT"
    elif branch_scenario == 3:
        # Branch: Out-of-stock product with discount (inter-field interaction)
        product["category"] = rng.choice(categories)
        product["price"] = 500_000
        product["stock"] = 0
        product["discount"] = rng.choice([0.0, 15.0, 25.0])
        product["rating"] = 4.0
        product["description"] = "San pham tam het hang"
    elif branch_scenario == 4:
        # Branch: Low stock warning (stock <= 5)
        product["category"] = rng.choice(categories)
        product["price"] = 750_000
        product["stock"] = rng.choice([1, 2, 3, 4, 5])
        product["discount"] = 5.0
        product["rating"] = 4.2
        product["description"] = "So luong con it"
    elif branch_scenario == 5:
        # Branch: 100% discount free of charge
        product["category"] = "Clothing"
        product["name"] = "Ao thun qua tang"
        product["price"] = 150_000
        product["stock"] = 100
        product["discount"] = 100.0
        product["rating"] = 5.0
        product["description"] = "Qua tang kem 0 dong"
    elif branch_scenario == 6:
        # Branch: Best seller classification (rating >= 4.5 and stock > 10)
        product["category"] = rng.choice(categories)
        product["price"] = 300_000
        product["stock"] = rng.choice([20, 50, 100])
        product["discount"] = 10.0
        product["rating"] = rng.choice([4.5, 4.8, 5.0])
        product["description"] = "San pham ban chay nhat"
    elif branch_scenario == 7:
        # Branch: Under review classification (rating < 2.0)
        product["category"] = rng.choice(categories)
        product["price"] = 200_000
        product["stock"] = 12
        product["discount"] = 5.0
        product["rating"] = rng.choice([0.5, 1.2, 1.9])
        product["description"] = "San pham nhieu phan hoi tieu cuc"
    else:
        # Branch: Precision testing with floating point numbers
        product["category"] = rng.choice(categories)
        product["price"] = round(rng.uniform(10_000, 5_000_000), 2)
        product["stock"] = rng.randint(6, 30)
        product["discount"] = round(rng.uniform(1.0, 49.0), 2)
        product["rating"] = round(rng.uniform(2.1, 4.4), 1)
        product["description"] = "Standard catalog entry"

    return json.dumps(product, ensure_ascii=False)


def generate_product(rng: random.Random | None = None) -> str:
    """General generator combining boundary blackbox and internal branch inputs."""
    rng = rng or random.Random()
    if rng.random() < 0.4:
        return generate_boundary_blackbox(rng)
    return generate_bounded_whitebox(rng)


def seed_corpus() -> list[str]:
    """Diverse seed corpus covering valid baseline, boundary limits, and malformed inputs."""
    return [
        json.dumps(valid_product()),
        # Bounded scenarios for white-box
        json.dumps({
            "id": "P002",
            "name": "MacBook Pro",
            "category": "Electronics",
            "price": 30_000_000,
            "stock": 10,
            "discount": 25,
            "rating": 4.9,
            "description": "Premium laptop",
        }),
        json.dumps({
            "id": "P003",
            "name": "Camera Canon EOS",
            "category": "Camera",
            "price": 18_000_000,
            "stock": 3,
            "discount": 10,
            "rating": 4.6,
            "description": "",
        }),
        json.dumps({
            "id": "P004",
            "name": "Clean Code Book",
            "category": "Book",
            "price": 250_000,
            "stock": 0,
            "discount": 60,
            "rating": 4.8,
            "description": "Tech book",
        }),
        json.dumps({
            "id": "P005",
            "name": "Defective Widget",
            "category": "Other",
            "price": 50_000,
            "stock": 25,
            "discount": 100,
            "rating": 1.5,
            "description": "Old batch",
        }),
        # Boundaries for black-box
        '{"id": "P010", "name": "B", "category": "Other", "price": -1, "stock": 1, "discount": 0, "rating": 5}',
        '{"id": "P011", "name": "B", "category": "Other", "price": 100, "stock": 1, "discount": 105, "rating": 5}',
        '{"id": "P012", "name": "B", "category": "Other", "price": 100, "stock": 1, "discount": 10, "rating": 6}',
        "{}",
        '{"id": null}',
        "{",
        "[]",
    ]
