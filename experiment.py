"""Run reproducible black-box and white-box experiments."""

from analyzer.product_analyzer import ProductAnalyzer
from fuzzing.blackbox_fuzzer import BlackBoxFuzzer
from fuzzing.whitebox_fuzzer import WhiteBoxFuzzer
from reporting import generate_charts, save_summary


def run_experiment(count: int = 1000) -> dict:
    analyzer = ProductAnalyzer()
    blackbox = BlackBoxFuzzer(analyzer.analyze_json).run(count)
    whitebox = WhiteBoxFuzzer().run(count)
    summary = {"blackbox": blackbox, "whitebox": whitebox, "input_count": count}
    save_summary(summary)
    generate_charts()
    return summary


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=1000)
    args = parser.parse_args()
    print(run_experiment(args.count))
