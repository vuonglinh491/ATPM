"""Re-run and reproduce an input saved by any fuzzer or SAT invariant checker."""

import argparse
import json
from pathlib import Path

from analyzer.faulty_analyzer import FaultyProductAnalyzer
from analyzer.product_analyzer import ProductAnalyzer
from fuzzing.sat_fuzzer import verify_sat_invariants


def main() -> int:
    parser = argparse.ArgumentParser(description="Reproduce a saved fuzzing finding or SAT counterexample")
    parser.add_argument("crash_file", help="Path to saved JSON finding file")
    args = parser.parse_args()

    crash_path = Path(args.crash_file)
    if not crash_path.exists():
        print(f"Lỗi: Không tìm thấy tệp {args.crash_file}")
        return 1

    finding = json.loads(crash_path.read_text(encoding="utf-8"))
    raw = finding.get("input") or finding.get("record", "")

    print("=" * 65)
    print(f"TÁI HIỆN FINDING / LỖI TỪ TỆP: {crash_path.name}")
    print("=" * 65)
    print("• Dữ liệu đầu vào lưu trữ (Recorded Input):")
    print(raw)
    print("-" * 65)

    is_sat = "sat" in str(crash_path).lower() or "invariant" in finding
    is_crash = "runtime_crash" in str(crash_path).lower()

    if is_sat or is_crash:
        analyzer = FaultyProductAnalyzer(enable_sat_logic_bugs=True, enable_runtime_crashes=True, enable_zero_division=True)
    else:
        analyzer = ProductAnalyzer()

    try:
        if raw.startswith("{") or raw.startswith("["):
            result = analyzer.analyze_json(raw)
            try:
                prod_dict = json.loads(raw)
            except Exception:
                prod_dict = {}
            is_safe, inv, desc = verify_sat_invariants(prod_dict, result)
            print("• Kết quả thực thi hiện tại (Current Output):")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            if not is_safe:
                print("\n[!] BẤT BIẾN SAT BỊ VI PHẠM (SAT Invariant Violation):")
                print(f"    - Bất biến : {inv}")
                print(f"    - Mô tả    : {desc}")
        else:
            from fuzzing.memory_model import analyze_record
            result = analyze_record(raw)
            print("• Kết quả mô hình bộ nhớ (Memory Model Output):")
            print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as exc:
        print(f"\n[!] BẮT ĐƯỢC NGOẠI LỆ / CRASH: {type(exc).__name__}: {exc}")

    print("=" * 65)
    print("Tái hiện hoàn tất thành công!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
