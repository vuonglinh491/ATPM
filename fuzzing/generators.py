"""Source-independent product input generators for black-box fuzzing."""

import json
import random
from typing import Any


def valid_product() -> dict[str, Any]:
    return {"id": "P001", "name": "Product", "category": "Other", "price": 100, "stock": 5, "discount": 0, "rating": 4, "description": "demo"}


def generate_product(rng: random.Random | None = None) -> str:
    rng = rng or random.Random()
    product = valid_product()
    fields = list(product)
    mode = rng.randrange(9)
    if mode == 0:
        return "{}"
    if mode == 1:
        product[rng.choice(fields)] = rng.choice([None, [], {}, True, "abc"])
    elif mode == 2:
        product[rng.choice(fields)] = rng.choice([-1, 0, 1, 5, 100, 101, 2**31, 10**18])
    elif mode == 3:
        product["name"] = rng.choice(["", "A", "A" * 101, "\n\t", "产品📷", "<script>"])
    elif mode == 4:
        product.pop(rng.choice(fields))
    elif mode == 5:
        product["extra"] = {"nested": [1, 2, 3]}
    elif mode == 6:
        product["price"] = rng.choice([0, -1, 1, 2**31, 10**100])
    elif mode == 7:
        product["discount"] = rng.choice([-100, 0, 100, 101])
    else:
        product["rating"] = rng.choice([-1, 0, 5, 5.1])
    return json.dumps(product, ensure_ascii=False)


def seed_corpus() -> list[str]:
    return [json.dumps(valid_product()), "{}", '{"id": null}', '{"price": -1}', '{"rating": 999999}', "{", "[]"]
