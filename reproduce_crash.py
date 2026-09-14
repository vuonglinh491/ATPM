"""Re-run an input saved by either fuzzer."""

import argparse
import json

from analyzer.product_analyzer import ProductAnalyzer


def main() -> int:
    parser = argparse.ArgumentParser(description="Reproduce a saved fuzzing finding")
    parser.add_argument("crash_file")
    args = parser.parse_args()
    finding = json.loads(open(args.crash_file, encoding="utf-8").read())
    raw = finding["input"]
    result = ProductAnalyzer().analyze_json(raw)
    print(json.dumps({"input": raw, "result": result, "recorded": finding}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
