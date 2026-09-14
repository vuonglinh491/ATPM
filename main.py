"""Command-line demo for the product analyzer fuzzing project."""

import json

from analyzer.product_analyzer import ProductAnalyzer
from experiment import run_experiment
from fuzzing.blackbox_fuzzer import BlackBoxFuzzer
from fuzzing.whitebox_fuzzer import WhiteBoxFuzzer
from reporting import generate_charts


def menu() -> None:
    analyzer = ProductAnalyzer()
    while True:
        print("\n================================")
        print(" PRODUCT ANALYZER FUZZ TESTING")
        print("================================")
        print("1. Run Normal Analysis")
        print("2. Run Black-box Fuzzing")
        print("3. Run White-box Fuzzing")
        print("4. Generate Charts")
        print("5. Show Crash Results")
        print("6. Generate Report")
        print("7. Exit")
        choice = input("Select: ").strip()
        if choice == "1":
            raw = input("JSON product (Enter for demo): ").strip() or '{"id":"P1","name":"Phone","category":"Mobile","price":100,"stock":2,"discount":10,"rating":4}'
            print(json.dumps(analyzer.analyze_json(raw), indent=2, ensure_ascii=False))
        elif choice == "2":
            print(BlackBoxFuzzer(analyzer.analyze_json).run(100))
        elif choice == "3":
            print(WhiteBoxFuzzer().run(100))
        elif choice == "4":
            print(generate_charts())
        elif choice == "5":
            from pathlib import Path
            print(*list(Path("crashes").rglob("*.json")), sep="\n")
        elif choice == "6":
            print(run_experiment(1000))
        elif choice == "7":
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    menu()
