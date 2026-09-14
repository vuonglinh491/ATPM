"""Small JSON mutations shared by the fuzzers."""

import json
import random
from typing import Any


def mutate(raw: str, rng: random.Random | None = None) -> str:
    rng = rng or random.Random()
    try:
        value: Any = json.loads(raw)
    except json.JSONDecodeError:
        return rng.choice(["{", "[", raw + "}", "null"])
    if not isinstance(value, dict):
        return json.dumps(value)
    actions = ["delete", "replace", "add", "duplicate_like"]
    action = rng.choice(actions)
    if action == "delete" and value:
        del value[rng.choice(list(value))]
    elif action == "replace":
        key = rng.choice(list(value) or ["price"])
        value[key] = rng.choice([None, -1, 0, 101, "x", [], {}, "A" * 1000])
    elif action == "add":
        value["fuzz_extra"] = [None, {"deep": True}]
    else:
        value["id"] = value.get("id", "P")
    return json.dumps(value, ensure_ascii=False)
