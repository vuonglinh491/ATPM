"""Command-line demo for the product analyzer fuzzing project."""

import json
from pathlib import Path

from analyzer.product_analyzer import ProductAnalyzer
from experiment import run_experiment
from fuzzing.blackbox_fuzzer import BlackBoxFuzzer
from fuzzing.memory_fuzzer import MemoryModelFuzzer
from fuzzing.sat_fuzzer import CrashFuzzer, SATFuzzer, UnsafeMemoryFuzzer
from fuzzing.whitebox_fuzzer import WhiteBoxFuzzer
from reporting import generate_charts


def menu() -> None:
    analyzer = ProductAnalyzer()
    while True:
        print("\n=======================================================")
        print(" PRODUCT ANALYZER FUZZ TESTING & SAT VERIFICATION DEMO")
        print("=======================================================")
        print("1. Phân tích sản phẩm mẫu (Normal Analysis)")
        print("2. Chạy Black-box Fuzzing (Kiểm tra biên BVA)")
        print("3. Chạy White-box Fuzzing (Độ phủ mã Bounded)")
        print("4. Chạy Mô hình bộ nhớ Python (Phân loại CWE)")
        print("5. Tạo biểu đồ trực quan (Generate Charts)")
        print("6. Chạy toàn bộ thí nghiệm chuẩn (Full Experiment)")
        print("7. Xem danh sách lỗi & phản ví dụ đã lưu (Show Crashes/Findings)")
        print("8. [MỚI] Mô phỏng Phản ví dụ SAT (Lỗi Logic Invariant Violation)")
        print("9. [MỚI] Mô phỏng Crash & Ngoại lệ Runtime (Runtime Crash Simulation)")
        print("10. [MỚI] Mô phỏng Lỗi bộ nhớ nghiêm trọng (Unsafe Memory Faults)")
        print("0. Thoát (Exit)")
        choice = input("Lựa chọn (0-10): ").strip()

        if choice == "1":
            raw = input("Nhập JSON sản phẩm (Enter để dùng mẫu mặc định): ").strip() or '{"id":"P1","name":"Camera Wifi","category":"Camera","price":1500000,"stock":20,"discount":10,"rating":4.5}'
            res = analyzer.analyze_json(raw)
            print(json.dumps(res, indent=2, ensure_ascii=False))
        elif choice == "2":
            res = BlackBoxFuzzer(analyzer.analyze_json).run(100)
            print(json.dumps(res, indent=2, ensure_ascii=False))
        elif choice == "3":
            res = WhiteBoxFuzzer().run(100)
            print(json.dumps(res, indent=2, ensure_ascii=False))
        elif choice == "4":
            res = MemoryModelFuzzer().run(100)
            print(json.dumps(res, indent=2, ensure_ascii=False))
        elif choice == "5":
            charts = generate_charts()
            print("Đã tạo các biểu đồ sau:", charts)
        elif choice == "6":
            summary = run_experiment(1000)
            print("Hoàn tất thí nghiệm 1.000 inputs!")
        elif choice == "7":
            crashes = list(Path("crashes").rglob("*.json"))
            if crashes:
                print(f"Tìm thấy {len(crashes)} file lỗi/phản ví dụ đã lưu:")
                for p in crashes[:15]:
                    print("  -", p)
            else:
                print("Chưa có finding nào được lưu trong thư mục crashes/.")
        elif choice == "8":
            print("Đang chạy mô phỏng tìm kiếm phản ví dụ SAT...")
            res = SATFuzzer().run(100)
            print(json.dumps(res, indent=2, ensure_ascii=False))
        elif choice == "9":
            print("Đang chạy mô phỏng tiêm ngoại lệ và Crash runtime...")
            res = CrashFuzzer().run(100)
            print(json.dumps(res, indent=2, ensure_ascii=False))
        elif choice == "10":
            print("Đang chạy mô phỏng lỗi bộ nhớ nghiêm trọng (Unsafe mode)...")
            res = UnsafeMemoryFuzzer().run(100)
            print(json.dumps(res, indent=2, ensure_ascii=False))
        elif choice in {"0", "exit", "quit"}:
            print("Tạm biệt!")
            break
        else:
            print("Lựa chọn không hợp lệ, vui lòng chọn từ 0 đến 10.")


if __name__ == "__main__":
    menu()
