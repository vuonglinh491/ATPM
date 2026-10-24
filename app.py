"""Desktop presentation UI for the Product Analyzer fuzzing project."""

import csv
import json
import os
import queue
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from typing import Any, Callable

import matplotlib
matplotlib.use("Agg")

from analyzer.product_analyzer import ProductAnalyzer
from experiment import run_experiment
from fuzzing.blackbox_fuzzer import BlackBoxFuzzer
from fuzzing.memory_fuzzer import MemoryModelFuzzer
from fuzzing.sat_fuzzer import CrashFuzzer, SATFuzzer, UnsafeMemoryFuzzer
from fuzzing.whitebox_fuzzer import WhiteBoxFuzzer
from reporting import generate_charts

PROJECT_ROOT = Path(__file__).resolve().parent
SAMPLE_PRODUCT = {
    "id": "P001",
    "name": "Camera Wifi",
    "category": "Camera",
    "price": 1500000,
    "stock": 20,
    "discount": 10,
    "rating": 4.5,
    "description": "Camera giam sat wifi",
}

BOUNDARY_ERROR_SAMPLES: dict[str, Any] = {
    "Tổng hợp nhiều lỗi biên (Giá, Tồn kho, Discount, Rating)": {
        "id": "P_INVALID_MULTI",
        "name": "Invalid Price & Discount Product",
        "category": "Camera",
        "price": -500000,
        "stock": -5,
        "discount": 120,
        "rating": 6.5,
        "description": "Bản ghi thử nghiệm chứa nhiều giá trị vi phạm biên",
    },
    "Lỗi đơn giá âm (Price < 0)": {
        "id": "P_NEG_PRICE",
        "name": "Camera Wifi",
        "category": "Camera",
        "price": -1,
        "stock": 20,
        "discount": 10,
        "rating": 4.5,
        "description": "Don gia am khong hop le",
    },
    "Lỗi chiết khấu vượt trần (Discount = 120%)": {
        "id": "P_OVER_DISCOUNT",
        "name": "Laptop Gaming",
        "category": "Electronics",
        "price": 25000000,
        "stock": 10,
        "discount": 120.0,
        "rating": 4.8,
        "description": "Chiet khau vuot qua 100%",
    },
    "Lỗi điểm đánh giá vượt trần (Rating = 6.0 sao)": {
        "id": "P_OVER_RATING",
        "name": "Clean Code Book",
        "category": "Book",
        "price": 250000,
        "stock": 15,
        "discount": 20,
        "rating": 6.0,
        "description": "Diem danh gia vuot qua 5.0",
    },
    "Lỗi tên sản phẩm quá dài (> 100 ký tự)": {
        "id": "P_NAME_OVERFLOW",
        "name": "A" * 105,
        "category": "Other",
        "price": 100000,
        "stock": 5,
        "discount": 0,
        "rating": 4.0,
        "description": "Ten san pham dai 105 ky tu vuot tran 100 ky tu",
    },
    "Lỗi số lượng tồn kho âm (Stock < 0)": {
        "id": "P_NEG_STOCK",
        "name": "Ao Thun Nam",
        "category": "Clothing",
        "price": 150000,
        "stock": -10,
        "discount": 5,
        "rating": 4.2,
        "description": "Ton kho am khong hop le",
    },
    "Lỗi cú pháp JSON (Malformed Syntax)": '{"id": "P_SYNTAX", "name": "Broken JSON", "price": 100000,',
}

WARNING_TRANSLATIONS = {
    "Camera products should include a warranty description": "Sản phẩm Camera cần bổ sung mô tả chính sách bảo hành",
    "Description is missing": "Bản ghi chưa có thông tin mô tả chi tiết (description rỗng)",
    "Discount is configured for an out-of-stock product": "Sản phẩm đã hết hàng (stock = 0) nhưng vẫn cấu hình giảm giá",
    "Low stock threshold reached (<=5 items remaining)": "Cảnh báo mức tồn kho sắp hết (còn <= 5 sản phẩm)",
    "High-value electronics discount (>20%) requires manager review": "Thiết bị điện tử giá cao giảm giá > 20% cần quản lý phê duyệt",
    "Book discount exceeds standard publisher cap (50%)": "Chiết khấu sách vượt trần quy định của nhà xuất bản (50%)",
    "100% discount applied: product is free of charge": "Áp dụng giảm giá 100%: Sản phẩm tặng kèm miễn phí (0 đồng)",
}

BADGE_TRANSLATIONS = {
    "BEST_SELLER": "BEST_SELLER (Sản phẩm bán chạy nhất: Rating >= 4.5 & Tồn kho > 10)",
    "UNDER_REVIEW": "UNDER_REVIEW (Đang bị xem xét / Khiếu nại: Rating < 2.0)",
    "STANDARD": "STANDARD (Sản phẩm tiêu chuẩn)",
}


class AnalyzerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.analyzer = ProductAnalyzer()
        self.action_buttons: list[ttk.Button] = []
        self.chart_images: list[tk.PhotoImage] = []
        self.task_queue: queue.Queue = queue.Queue()

        root.title("Product Analyzer | Fuzz Lab - Kiểm thử Fuzzing & Mô hình Bộ nhớ")
        root.geometry("1220x820")
        root.minsize(980, 660)
        self._configure_style()
        self._build_layout()
        self._refresh_reports()
        self._poll_task_queue()

    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 10), background="#f1f4f0", foreground="#202b29")
        style.configure("TFrame", background="#f1f4f0")
        style.configure("TLabel", background="#f1f4f0", foreground="#202b29")
        style.configure("Header.TFrame", background="#183b35")
        style.configure("HeaderTitle.TLabel", background="#183b35", foreground="#f7f5eb", font=("Segoe UI Semibold", 20))
        style.configure("HeaderSub.TLabel", background="#183b35", foreground="#b9d6c7", font=("Segoe UI", 10))
        style.configure("Section.TLabel", font=("Segoe UI Semibold", 11), foreground="#183b35")
        style.configure("SubSection.TLabel", font=("Segoe UI Semibold", 10), foreground="#41615a")
        style.configure("Accent.TButton", background="#d66a45", foreground="#ffffff", padding=(10, 6), font=("Segoe UI Semibold", 9))
        style.map("Accent.TButton", background=[("active", "#b95435"), ("disabled", "#a8b2ad")])
        style.configure("Danger.TButton", background="#a83232", foreground="#ffffff", padding=(10, 6), font=("Segoe UI Semibold", 9))
        style.map("Danger.TButton", background=[("active", "#862525"), ("disabled", "#a8b2ad")])
        style.configure("TButton", padding=(9, 6), font=("Segoe UI", 9))
        style.configure("TNotebook", background="#f1f4f0", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(16, 9), font=("Segoe UI Semibold", 10))
        style.map("TNotebook.Tab", background=[("selected", "#ffffff"), ("!selected", "#dce5df")])
        style.configure("Treeview", rowheight=27, background="#ffffff", fieldbackground="#ffffff")
        style.configure("Treeview.Heading", font=("Segoe UI Semibold", 9), background="#dce5df")

    def _build_layout(self) -> None:
        header = ttk.Frame(self.root, style="Header.TFrame", padding=(24, 16))
        header.pack(fill="x")
        ttk.Label(header, text="PRODUCT ANALYZER | FUZZ LAB", style="HeaderTitle.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Kiểm tra dữ liệu · Black-box & White-box Fuzzing · Mô hình bộ nhớ CWE · Phản ví dụ SAT",
            style="HeaderSub.TLabel",
        ).pack(anchor="w", pady=(3, 0))

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=18, pady=14)
        self.analysis_tab = ttk.Frame(self.notebook, padding=16)
        self.fuzz_tab = ttk.Frame(self.notebook, padding=16)
        self.reports_tab = ttk.Frame(self.notebook, padding=16)
        self.notebook.add(self.analysis_tab, text="Phân tích sản phẩm")
        self.notebook.add(self.fuzz_tab, text="Phòng thí nghiệm fuzzing")
        self.notebook.add(self.reports_tab, text="Kết quả & biểu đồ")
        self._build_analysis_tab()
        self._build_fuzz_tab()
        self._build_reports_tab()

        self.status = tk.StringVar(value="Sẵn sàng")
        status_bar = ttk.Frame(self.root, padding=(18, 6))
        status_bar.pack(fill="x", side="bottom")

        self.status_label = ttk.Label(status_bar, textvariable=self.status, font=("Segoe UI", 9))
        self.status_label.pack(side="left")

        self.bottom_progressbar = ttk.Progressbar(status_bar, mode="indeterminate", length=180)

    def _build_analysis_tab(self) -> None:
        self.analysis_tab.columnconfigure((0, 1), weight=1, uniform="panels")
        self.analysis_tab.rowconfigure(1, weight=1)
        ttk.Label(self.analysis_tab, text="Dữ liệu đầu vào (JSON)", style="Section.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))
        ttk.Label(self.analysis_tab, text="Kết quả kiểm tra & Giải thích", style="Section.TLabel").grid(row=0, column=1, sticky="w", padx=(16, 0), pady=(0, 8))

        self.input_text = ScrolledText(
            self.analysis_tab,
            wrap="word",
            font=("Cascadia Code", 10),
            background="#152824",
            foreground="#e5f1e9",
            insertbackground="#ffffff",
            padx=12,
            pady=12,
            borderwidth=0,
        )
        self.input_text.grid(row=1, column=0, sticky="nsew")
        self.output_text = ScrolledText(
            self.analysis_tab,
            wrap="word",
            font=("Cascadia Code", 10),
            background="#ffffff",
            foreground="#202b29",
            padx=12,
            pady=12,
            borderwidth=0,
        )
        self.output_text.grid(row=1, column=1, sticky="nsew", padx=(16, 0))
        self._set_input(json.dumps(SAMPLE_PRODUCT, ensure_ascii=False, indent=2))
        self._set_text(self.output_text, "Nhập bản ghi JSON sản phẩm bên trái rồi bấm 'Phân tích'.\nKết quả nghiệp vụ và giải thích chi tiết sẽ hiển thị tại đây.")

        actions = ttk.Frame(self.analysis_tab)
        actions.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 0))

        ttk.Button(actions, text="Nạp ví dụ chuẩn", command=self._load_sample).pack(side="left")

        sep = ttk.Separator(actions, orient="vertical")
        sep.pack(side="left", padx=10, fill="y")

        ttk.Label(actions, text="Chọn mẫu lỗi biên:").pack(side="left")
        self.invalid_sample_var = tk.StringVar(value=list(BOUNDARY_ERROR_SAMPLES.keys())[0])
        self.invalid_sample_select = ttk.Combobox(
            actions,
            textvariable=self.invalid_sample_var,
            values=list(BOUNDARY_ERROR_SAMPLES.keys()),
            state="readonly",
            width=38,
        )
        self.invalid_sample_select.pack(side="left", padx=6)
        self.invalid_sample_select.bind("<<ComboboxSelected>>", lambda _e: self._load_invalid_sample())

        ttk.Button(actions, text="Nạp lỗi biên", style="Danger.TButton", command=self._load_invalid_sample).pack(side="left", padx=(0, 10))

        ttk.Button(actions, text="Phân tích", style="Accent.TButton", command=self._analyze_product).pack(side="left")

    def _build_fuzz_tab(self) -> None:
        self.fuzz_tab.columnconfigure(0, weight=1)
        self.fuzz_tab.rowconfigure(4, weight=1)

        controls = ttk.Frame(self.fuzz_tab)
        controls.grid(row=0, column=0, sticky="ew")
        ttk.Label(controls, text="Số lượng input mỗi lần chạy:", style="Section.TLabel").pack(side="left")
        self.count_var = tk.StringVar(value="100")
        ttk.Spinbox(controls, from_=1, to=10000, increment=100, textvariable=self.count_var, width=9).pack(side="left", padx=(10, 18))

        # Standard fuzzing row
        std_frame = ttk.Frame(self.fuzz_tab)
        std_frame.grid(row=1, column=0, sticky="ew", pady=(10, 6))
        ttk.Label(std_frame, text="Kiểm thử Fuzzing chuẩn (Phòng thủ & An toàn):", style="SubSection.TLabel").pack(anchor="w", pady=(0, 4))
        std_buttons = ttk.Frame(std_frame)
        std_buttons.pack(fill="x")
        self._add_action_button(std_buttons, "Black-box (Biên BVA)", lambda: self._run_fuzzer("Black-box", lambda count: BlackBoxFuzzer(self.analyzer.analyze_json).run(count), "reports/blackbox_results.csv"))
        self._add_action_button(std_buttons, "White-box (Độ phủ Bounded)", lambda: self._run_fuzzer("White-box", lambda count: WhiteBoxFuzzer().run(count), "reports/whitebox_results.csv"))
        self._add_action_button(std_buttons, "Mô hình bộ nhớ (CWE an toàn)", lambda: self._run_fuzzer("Mô hình bộ nhớ Python", lambda count: MemoryModelFuzzer().run(count), "reports/memory_results.csv"))
        self._add_action_button(std_buttons, "Chạy toàn bộ chuẩn", self._run_full_experiment, accent=True)

        # Bug injection & SAT counterexamples row
        fault_frame = ttk.Frame(self.fuzz_tab)
        fault_frame.grid(row=2, column=0, sticky="ew", pady=(4, 8))
        ttk.Label(fault_frame, text="Mô phỏng Sinh lỗi & Phản ví dụ SAT (Bug / Counterexample Simulation):", style="SubSection.TLabel").pack(anchor="w", pady=(0, 4))
        fault_buttons = ttk.Frame(fault_frame)
        fault_buttons.pack(fill="x")
        self._add_action_button(fault_buttons, "Phản ví dụ SAT (Lỗi Logic)", lambda: self._run_fuzzer("Phản ví dụ SAT (Lỗi Logic)", lambda count: SATFuzzer().run(count), "reports/sat_fuzzing_results.csv"), danger=True)
        self._add_action_button(fault_buttons, "Mô phỏng Crash (Ngoại lệ Runtime)", lambda: self._run_fuzzer("Mô phỏng Crash / Ngoại lệ", lambda count: CrashFuzzer().run(count), "reports/crash_simulation_results.csv"), danger=True)
        self._add_action_button(fault_buttons, "Lỗi bộ nhớ nghiêm trọng (CWE Faults)", lambda: self._run_fuzzer("Lỗi bộ nhớ nghiêm trọng", lambda count: UnsafeMemoryFuzzer().run(count), "reports/unsafe_memory_results.csv"), danger=True)

        # Loading notification banner frame (row 3)
        self.loading_frame = ttk.Frame(self.fuzz_tab, padding=(10, 6))
        self.loading_frame.grid(row=3, column=0, sticky="ew", pady=(0, 8))

        self.loading_text = tk.StringVar(value="Sẵn sàng. Chọn số lượng input và bấm nút phía trên để bắt đầu.")
        self.loading_label = ttk.Label(
            self.loading_frame,
            textvariable=self.loading_text,
            font=("Segoe UI Semibold", 10),
            foreground="#183b35",
        )
        self.loading_label.pack(side="left")

        self.fuzz_progressbar = ttk.Progressbar(
            self.loading_frame,
            mode="indeterminate",
            length=260,
        )

        self.fuzz_output = ScrolledText(
            self.fuzz_tab,
            wrap="word",
            font=("Cascadia Code", 10),
            background="#ffffff",
            foreground="#202b29",
            padx=14,
            pady=14,
            borderwidth=0,
        )
        self.fuzz_output.grid(row=4, column=0, sticky="nsew")
        initial_msg = (
            "CHÀO MỪNG ĐẾN VỚI PHÒNG THÍ NGHIỆM PRODUCT ANALYZER FUZZING\n"
            + "=" * 65 + "\n\n"
            "Chọn một chế độ kiểm thử ở trên để bắt đầu mô phỏng:\n\n"
            "1. Nhóm kiểm thử chuẩn (Hệ thống phòng vệ an toàn):\n"
            "   - Black-box : Thăm dò các giá trị biên ngoài (BVA) để kiểm tra bộ lọc Validator.\n"
            "   - White-box : Đào sâu các nhánh logic nội bộ trong vùng Bounded theo độ phủ mã.\n"
            "   - Mô hình bộ nhớ : Mô phỏng và phân loại các tình huống an toàn/chặn theo chuẩn CWE.\n\n"
            "2. Nhóm mô phỏng sinh lỗi & Phản ví dụ SAT (Minh họa phát hiện lỗi):\n"
            "   - Phản ví dụ SAT : Tự động tìm input thỏa mãn SAT(¬Invariant), gây vi phạm bất biến nghiệp vụ\n"
            "     (Ví dụ: final_price > price, chiết khấu gây giá âm, lỗi chia cho 0).\n"
            "   - Mô phỏng Crash : Tiêm các payload đặc biệt gây unhandled exception (Null byte, Memory Error).\n"
            "   - Lỗi bộ nhớ nghiêm trọng : Mô phỏng tiến trình sập khi gặp Double-free (CWE-415), Use-after-free (CWE-416).\n\n"
            "(*) Toàn bộ kết quả chạy sẽ được hiển thị bằng TIẾNG VIỆT chi tiết và lưu tại reports/."
        )
        self._set_text(self.fuzz_output, initial_msg)

    def _build_reports_tab(self) -> None:
        self.reports_tab.columnconfigure((0, 1), weight=1, uniform="reports")
        self.reports_tab.rowconfigure(1, weight=1)
        report_controls = ttk.Frame(self.reports_tab)
        report_controls.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        ttk.Label(report_controls, text="Bảng kết quả CSV:", style="Section.TLabel").pack(side="left")
        self.report_var = tk.StringVar()
        self.report_select = ttk.Combobox(report_controls, textvariable=self.report_var, state="readonly", width=36)
        self.report_select.pack(side="left", padx=8)
        self.report_select.bind("<<ComboboxSelected>>", lambda _event: self._show_selected_report())
        ttk.Button(report_controls, text="Làm mới", command=self._refresh_reports).pack(side="left")
        ttk.Button(report_controls, text="Tạo biểu đồ trực quan", style="Accent.TButton", command=self._generate_charts).pack(side="left", padx=8)

        table_frame = ttk.Frame(self.reports_tab)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        self.results_tree = ttk.Treeview(table_frame, show="headings")
        self.results_tree.grid(row=0, column=0, sticky="nsew")
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.results_tree.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.results_tree.xview)
        x_scroll.grid(row=1, column=0, sticky="ew")
        self.results_tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        chart_panel = ttk.Frame(self.reports_tab)
        chart_panel.grid(row=1, column=1, sticky="nsew")
        chart_panel.rowconfigure(1, weight=1)
        chart_panel.columnconfigure(0, weight=1)
        ttk.Label(chart_panel, text="Biểu đồ trực quan", style="Section.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.chart_list = tk.Listbox(chart_panel, height=6, font=("Segoe UI", 10), background="#ffffff", borderwidth=0, activestyle="none")
        self.chart_list.grid(row=1, column=0, sticky="new")
        self.chart_list.bind("<<ListboxSelect>>", self._show_chart)
        self.chart_preview = ttk.Label(chart_panel, text="Hãy chạy thử nghiệm rồi bấm 'Tạo biểu đồ trực quan'.", anchor="center")
        self.chart_preview.grid(row=2, column=0, sticky="nsew", pady=(12, 0))

    def _add_action_button(self, parent: ttk.Frame, text: str, command: Callable[[], None], accent: bool = False, danger: bool = False) -> None:
        style_name = "Danger.TButton" if danger else ("Accent.TButton" if accent else "TButton")
        button = ttk.Button(parent, text=text, command=command, style=style_name)
        button.pack(side="left", padx=(0, 8))
        self.action_buttons.append(button)

    def _set_input(self, value: str) -> None:
        self.input_text.configure(state="normal")
        self.input_text.delete("1.0", "end")
        self.input_text.insert("1.0", value)

    @staticmethod
    def _set_text(widget: ScrolledText, value: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.configure(state="disabled")

    def _load_sample(self) -> None:
        self._set_input(json.dumps(SAMPLE_PRODUCT, ensure_ascii=False, indent=2))
        self._analyze_product()

    def _load_invalid_sample(self) -> None:
        selected_key = self.invalid_sample_var.get()
        sample = BOUNDARY_ERROR_SAMPLES.get(selected_key, list(BOUNDARY_ERROR_SAMPLES.values())[0])
        raw_text = sample if isinstance(sample, str) else json.dumps(sample, ensure_ascii=False, indent=2)
        self._set_input(raw_text)
        self._analyze_product()

    def _analyze_product(self) -> None:
        raw = self.input_text.get("1.0", "end").strip()
        result = self.analyzer.analyze_json(raw)

        is_valid = result.get("valid", False)
        lines = ["=" * 65]
        if is_valid:
            lines.append("KẾT QUẢ PHÂN TÍCH: SẢN PHẨM HỢP LỆ (VALID)")
            lines.append("=" * 65)
            lines.append("[THÔNG TIN TÍNH TOÁN NGHIỆP VỤ]")
            final_p = result.get("final_price")
            inv_val = result.get("inventory_value")
            lines.append(f"• Giá sau giảm giá      : {final_p:,.2f} VNĐ" if final_p is not None else "• Giá sau giảm giá      : N/A")
            lines.append(f"• Tổng giá trị tồn kho  : {inv_val:,.2f} VNĐ" if inv_val is not None else "• Tổng giá trị tồn kho  : N/A")
            lines.append(f"• Điểm đánh giá (Rating): {result.get('average_rating', 0)} / 5.0 sao")

            raw_badge = result.get("badge", "STANDARD")
            badge_vi = BADGE_TRANSLATIONS.get(raw_badge, raw_badge)
            lines.append(f"• Phân hạng sản phẩm    : {badge_vi}")

            warnings = result.get("warnings", [])
            lines.append("\n[CẢNH BÁO NGHIỆP VỤ - WARNINGS]")
            if warnings:
                for w in warnings:
                    translated = WARNING_TRANSLATIONS.get(w, w)
                    lines.append(f"⚠ {translated}")
            else:
                lines.append("✓ Không có cảnh báo nghiệp vụ nào.")
        else:
            lines.append("KẾT QUẢ PHÂN TÍCH: BẢN GHI KHÔNG HỢP LỆ (BỊ TỪ CHỐI / INVALID)")
            lines.append("=" * 65)
            lines.append("Validator đã PHÁT HIỆN LỖI VÀ CHẶN AN TOÀN trước khi tính toán:")
            for idx, err in enumerate(result.get("errors", []), 1):
                lines.append(f"  [{idx}] {err}")
            lines.append("\n(*) LƯU Ý KỸ THUẬT: Việc trả về 'valid: False' cùng mảng lỗi là")
            lines.append("hành vi bảo vệ mong muốn (Sanitization). Ứng dụng không bị crash.")

        lines.append("\n" + "-" * 65)
        lines.append("[DỮ LIỆU KỸ THUẬT DẠNG JSON]")
        lines.append(json.dumps(result, ensure_ascii=False, indent=2))

        self._set_text(self.output_text, "\n".join(lines))
        self.status.set("Sản phẩm hợp lệ" if is_valid else "Input ngoài biên/sai quy cách - Validator đã chặn an toàn")

    def _input_count(self) -> int:
        try:
            count = int(self.count_var.get())
        except ValueError as exc:
            raise ValueError("Số lượng input phải là số nguyên") from exc
        if not 1 <= count <= 10000:
            raise ValueError("Số lượng input nằm trong khoảng 1 đến 10.000")
        return count

    def _run_fuzzer(self, title: str, runner: Callable[[int], dict[str, Any]], report_path: str) -> None:
        try:
            count = self._input_count()
        except ValueError as exc:
            messagebox.showerror("Giá trị không hợp lệ", str(exc), parent=self.root)
            return

        def task() -> dict[str, Any]:
            result = runner(count)
            result["report"] = report_path
            return result

        self._run_background(title, task, lambda result: self._show_run_result(title, result, report_path), count=count)

    def _run_full_experiment(self) -> None:
        try:
            count = self._input_count()
        except ValueError as exc:
            messagebox.showerror("Giá trị không hợp lệ", str(exc), parent=self.root)
            return
        self._run_background("Toàn bộ thí nghiệm chuẩn", lambda: run_experiment(count), self._show_experiment_result, count=count)

    def _run_background(self, title: str, task: Callable[[], Any], on_success: Callable[[Any], None], count: int | None = None) -> None:
        count_str = f" ({count:,} inputs)" if count else ""
        self.status.set(f"Đang chạy mô phỏng: {title}{count_str}...")
        self.root.configure(cursor="watch")

        # Start loading indicators & animation
        self.loading_text.set(f"⏳ ĐANG THỰC THI MÔ PHỎNG: {title.upper()}{count_str}... Vui lòng đợi trong giây lát.")
        self.fuzz_progressbar.pack(side="right", padx=(10, 0))
        self.fuzz_progressbar.start(10)
        self.bottom_progressbar.pack(side="right", padx=(10, 0))
        self.bottom_progressbar.start(10)

        # Immediate placeholder text on Tab 2
        if count:
            self._set_text(
                self.fuzz_output,
                f"⏳ ĐANG THỰC THI MÔ PHỎNG: {title.upper()}{count_str}\n"
                + "=" * 70 + "\n\n"
                f"• Quy mô kiểm thử : {count:,} inputs\n"
                f"• Trạng thái      : Đang xử lý tính toán trong luồng ngầm (Background Thread)...\n"
                f"• Lưu ý           : Quá trình có thể mất từ vài giây đến vài chục giây tùy quy mô.\n"
                f"                    Hệ thống sẽ hiển thị thông báo hoàn tất ngay khi kết thúc!\n"
            )

        for button in self.action_buttons:
            button.configure(state="disabled")

        start_time = time.perf_counter()

        def work() -> None:
            try:
                result = task()
                elapsed = time.perf_counter() - start_time
                self.task_queue.put(("success", title, result, on_success, count, elapsed))
            except Exception as exc:
                elapsed = time.perf_counter() - start_time
                self.task_queue.put(("error", title, exc, None, count, elapsed))

        threading.Thread(target=work, daemon=True).start()

    def _poll_task_queue(self) -> None:
        try:
            while True:
                msg_type, title, payload, callback, count, elapsed = self.task_queue.get_nowait()
                if msg_type == "success":
                    self._finish_success(title, payload, callback, count, elapsed)
                elif msg_type == "error":
                    self._finish_error(title, payload, count, elapsed)
        except queue.Empty:
            pass
        finally:
            self.root.after(50, self._poll_task_queue)

    def _finish_success(self, title: str, result: Any, callback: Callable[[Any], None], count: int | None = None, elapsed: float = 0.0) -> None:
        # Stop animations & restore cursor
        self.fuzz_progressbar.stop()
        self.fuzz_progressbar.pack_forget()
        self.bottom_progressbar.stop()
        self.bottom_progressbar.pack_forget()
        self.root.configure(cursor="")

        for button in self.action_buttons:
            button.configure(state="normal")

        count_str = f" ({count:,} inputs)" if count else ""
        self.loading_text.set(f"✓ ĐÃ HOÀN TẤT: {title.upper()}{count_str} trong {elapsed:.2f}s! Kết quả hiển thị bên dưới.")
        self.status.set(f"Hoàn tất: {title}{count_str} ({elapsed:.2f}s)")
        callback(result)

        # Notify user when larger simulation (count >= 500 or taking >= 2.0s) finishes
        if (count and count >= 500) or elapsed >= 2.0:
            messagebox.showinfo(
                "Mô phỏng hoàn thành",
                f"✓ Đã hoàn tất mô phỏng '{title}' với {count:,} inputs thành công!\n\n"
                f"• Thời gian thực thi : {elapsed:.2f} giây\n"
                f"• Báo cáo CSV và biểu đồ đã được cập nhật.",
                parent=self.root,
            )

    def _finish_error(self, title: str, error: Exception, count: int | None = None, elapsed: float = 0.0) -> None:
        self.fuzz_progressbar.stop()
        self.fuzz_progressbar.pack_forget()
        self.bottom_progressbar.stop()
        self.bottom_progressbar.pack_forget()
        self.root.configure(cursor="")

        for button in self.action_buttons:
            button.configure(state="normal")

        count_str = f" ({count:,} inputs)" if count else ""
        self.loading_text.set(f"⚠ CÓ LỖI XẢY RA KHI CHẠY MÔ PHỎNG: {title.upper()}{count_str}!")
        self.status.set(f"Có lỗi khi chạy: {title}")
        messagebox.showerror("Không thể hoàn thành", str(error), parent=self.root)

    def _show_run_result(self, title: str, result: dict[str, Any], report_path: str) -> None:
        formatted_text = self._format_result_vietnamese(title, result, report_path)
        self._set_text(self.fuzz_output, formatted_text)
        self.notebook.select(self.fuzz_tab)
        self._refresh_reports(select=report_path)

    def _show_experiment_result(self, result: dict[str, Any]) -> None:
        formatted_text = self._format_full_experiment_vietnamese(result)
        self._set_text(self.fuzz_output, formatted_text)
        self.notebook.select(self.fuzz_tab)
        self._refresh_reports(select="reports/memory_results.csv")
        self._load_charts()

    def _format_result_vietnamese(self, title: str, result: dict[str, Any], report_path: str) -> str:
        total = result.get("total_inputs", 0)
        lines = [
            "=" * 70,
            f"KẾT QUẢ MÔ PHỎNG: {title.upper()}",
            "=" * 70,
            f"• Tổng số đầu vào kiểm thử (Inputs) : {total:,}",
            f"• File báo cáo chi tiết CSV         : {report_path}",
        ]
        if "execution_time_seconds" in result:
            lines.append(f"• Tổng thời gian thực thi           : {result['execution_time_seconds']} giây")
        if "average_time_ms" in result:
            lines.append(f"• Tốc độ trung bình mỗi input       : {result['average_time_ms']} ms")

        sim_type = result.get("type")

        # 1. SAT Fuzzing / Counterexample Simulation
        if sim_type == "sat_simulation" or "logic_bugs" in result:
            logic_bugs = result.get("logic_bugs", 0)
            exceptions = result.get("exceptions", 0)
            valid = result.get("valid", 0)
            invalid = result.get("invalid", 0)
            found_count = result.get("counterexamples_found", logic_bugs + exceptions)

            lines.append("\n" + "-" * 70)
            lines.append("--- PHÂN TÍCH KẾT QUẢ KIỂM CHỨNG HÌNH THỨC & PHẢN VÍ DỤ SAT ---")
            lines.append(f"[!] PHÁT HIỆN LỖI LOGIC / PHẢN VÍ DỤ SAT : {logic_bugs} trường hợp ({logic_bugs/total*100:.1f}%)" if total else "")
            lines.append("    -> Ý NGHĨA HỌC THUẬT: Trong kiểm chứng hình thức, bài toán tìm phản ví dụ")
            lines.append("       vi phạm bất biến SAT(¬Invariant) ĐÃ ĐƯỢC THỎA MÃN. Fuzzer đã tìm ra")
            lines.append("       các đầu vào khiến chương trình vi phạm các bất biến an toàn nghiệp vụ!")

            details = result.get("counterexample_details", [])
            if details:
                lines.append("\n    Chi tiết các phản ví dụ tiêu biểu vừa tìm được:")
                for idx, d in enumerate(details[:5], 1):
                    lines.append(f"    ({idx}) {d}")

            lines.append(f"\n[+] ĐẦU VÀO HỢP LỆ (VALID)        : {valid} ({valid/total*100:.1f}%)" if total else "")
            lines.append("    -> Các input tuân thủ toàn bộ các bất biến an toàn.")
            lines.append(f"[+] BỊ TỪ CHỐI AN TOÀN (INVALID) : {invalid} ({invalid/total*100:.1f}%)" if total else "")
            lines.append("    -> Các input vi phạm schema được validator ngăn chặn ngay từ đầu.")
            if exceptions > 0:
                lines.append(f"[!] NGOẠI LỆ / CRASH (EXCEPTION) : {exceptions} trường hợp (Rating=0 gây chia cho 0!)")
            lines.append(f"\n[*] Đã lưu toàn bộ {found_count} phản ví dụ JSON vào: crashes/sat_counterexamples/")

        # 2. Runtime Crash Simulation
        elif sim_type == "crash_simulation" or "crashes" in result and "coverage_points" not in result:
            crashes = result.get("crashes", 0)
            valid = result.get("valid", 0)
            invalid = result.get("invalid", 0)

            lines.append("\n" + "-" * 70)
            lines.append("--- PHÂN TÍCH KẾT QUẢ MÔ PHỎNG CRASH & NGOẠI LỆ HỆ THỐNG ---")
            lines.append(f"[!] PHÁT HIỆN CRASH / UNHANDLED EXCEPTION : {crashes} ca ({crashes/total*100:.1f}%)" if total else "")
            lines.append("    -> Ý NGHĨA: Fuzzer đã kích hoạt thành công các điểm yếu runtime unhandled")
            lines.append("       như Null-byte injection, MemoryError hoặc Deserialization Fault.")

            details = result.get("crash_details", [])
            if details:
                lines.append("\n    Danh sách ngoại lệ runtime đã bắt được:")
                for idx, c in enumerate(details[:5], 1):
                    lines.append(f"    ({idx}) {c}")
            lines.append(f"\n[+] BỊ TỪ CHỐI AN TOÀN (INVALID) : {invalid} ca")
            lines.append(f"[*] Toàn bộ dữ liệu crash được lưu trong: crashes/runtime_crashes/")

        # 3. Unsafe Memory Simulation
        elif sim_type == "unsafe_memory_simulation" or "critical_faults" in result:
            safe = result.get("safe", 0)
            blocked = result.get("blocked", 0)
            detected = result.get("detected", 0)
            critical = result.get("critical_faults", 0)

            lines.append("\n" + "-" * 70)
            lines.append("--- PHÂN TÍCH KẾT QUẢ MÔ PHỎNG LỖI BỘ NHỚ NGUY HIỂM (UNSAFE MODE) ---")
            lines.append(f"[!] LỖI BỘ NHỚ NGHIÊM TRỌNG (CRITICAL FAULT) : {critical} kịch bản ({critical/total*100:.1f}%)" if total else "")
            lines.append("    -> Ý NGHĨA: Giả lập các vi phạm Use-After-Free (CWE-416) và Double-Free (CWE-415)")
            lines.append("       ở môi trường không có guard bảo vệ dẫn đến Crash tiến trình mô phỏng!")
            lines.append(f"[+] AN TOÀN (SAFE)          : {safe} kịch bản")
            lines.append(f"[+] ĐÃ CHẶN SỚM (BLOCKED)   : {blocked} kịch bản (Buffer overflow, null pointer, integer overflow)")
            lines.append(f"[!] PHÁT HIỆN RÒ RỈ (DETECTED): {detected} kịch bản (Memory leak CWE-401)")
            lines.append(f"[*] Toàn bộ finding lỗi bộ nhớ được ghi tại: crashes/memory_faults/")

        # 4. Standard Memory Model Fuzzer
        elif "safe" in result and "blocked" in result:
            safe = result.get("safe", 0)
            blocked = result.get("blocked", 0)
            detected = result.get("findings", 0)
            cwe_counts = result.get("cwe_counts", {})

            lines.append("\n" + "-" * 70)
            lines.append("--- PHÂN LOẠI TRẠNG THÁI MÔ HÌNH BỘ NHỚ THEO CHUẨN CWE ---")
            lines.append(f"[1] AN TOÀN (SAFE) : {safe} kịch bản ({safe/total*100:.1f}%)" if total else "")
            lines.append("    -> Bộ nhớ được cấp phát, sử dụng và giải phóng chuẩn chỉnh trong giới hạn.")
            lines.append(f"[2] ĐÃ CHẶN ĐỨNG (BLOCKED) : {blocked} kịch bản ({blocked/total*100:.1f}%)" if total else "")
            lines.append("    -> Cơ chế phòng vệ (Guards) phát hiện và NGĂN CHẶN TRƯỚC KHI sự cố xảy ra:")
            cwe_explanations = {
                "CWE-121": "Tràn bộ đệm Stack (Buffer Overflow) - Tên dài > 100 byte bị chặn trước khi copy",
                "CWE-190": "Tràn số nguyên (Integer Overflow) - Nhân kích thước vượt giới hạn 64-bit bị từ chối",
                "CWE-476": "Con trỏ NULL (Null Pointer Deref) - Thiếu con trỏ bắt buộc bị chặn trước khi truy xuất",
                "CWE-789": "Cấp phát vượt hạn mức (Excessive Allocation) - Vượt ngưỡng 1MB cấu hình",
                "CWE-20": "Dữ liệu đầu vào sai cú pháp / kiểu dữ liệu không hợp lệ",
                "CWE-401": "Rò rỉ bộ nhớ (Memory Leak) - Vùng nhớ kết thúc scope mà chưa được giải phóng",
                "CWE-415": "Giải phóng hai lần (Double Free) - Cùng vùng nhớ bị free lần thứ 2",
                "CWE-416": "Sử dụng sau giải phóng (Use-After-Free) - Truy cập con trỏ đã giải phóng",
            }
            for cwe, cnt in sorted(cwe_counts.items()):
                meaning = cwe_explanations.get(cwe, "")
                lines.append(f"       • {cwe} : {cnt} kịch bản ({meaning})")

            lines.append(f"[3] PHÁT HIỆN VI PHẠM (DETECTED) : {detected} kịch bản ({detected/total*100:.1f}%)" if total else "")
            lines.append("    -> Mô hình Ownership Tracker phát hiện các vi phạm về vòng đời tài nguyên.")

        # 5. Standard White-box Fuzzer
        elif "coverage_points" in result:
            cov = result.get("coverage_points", 0)
            crashes = result.get("crashes", 0)
            corpus_size = result.get("corpus_size", 0)

            lines.append("\n" + "-" * 70)
            lines.append("--- PHÂN TÍCH KẾT QUẢ WHITE-BOX (COVERAGE-GUIDED) FUZZING ---")
            lines.append(f"• Số dòng mã analyzer được thực thi (Coverage Points): {cov} dòng mã")
            lines.append("  -> Ý NGHĨA: White-box Fuzzer dùng công cụ coverage.py để đo độ phủ mã.")
            lines.append("     Mỗi khi một input mở rộng thêm dòng mã mới, fuzzer sẽ giữ lại vào Corpus.")
            lines.append(f"• Kích thước tập hạt giống (Corpus Size)             : {corpus_size} mẫu")
            lines.append(f"• Số lần xảy ra Crash                                : {crashes} lần")
            lines.append("  -> Tỷ lệ VALID trong White-box thường rất cao vì bộ sinh tập trung đào sâu")
            lines.append("     vào các nhánh logic nghiệp vụ nội bộ (Camera warranty, Book discount, Badge...).")

        # 6. Standard Black-box Fuzzer
        else:
            valid = result.get("valid", 0)
            invalid = result.get("invalid", 0)
            crashes = result.get("crashes", 0)
            exceptions = result.get("exceptions", 0)
            logic_bugs = result.get("logic_bug", result.get("logic_bugs", 0))

            lines.append("\n" + "-" * 70)
            lines.append("--- PHÂN TÍCH KẾT QUẢ BLACK-BOX (BOUNDARY BVA) FUZZING ---")
            lines.append(f"[1] DỮ LIỆU HỢP LỆ (VALID) : {valid} inputs ({valid/total*100:.1f}%)" if total else "")
            lines.append("    -> Ý NGHĨA: Input nằm trong Bounded Region, vượt qua toàn bộ Validator,")
            lines.append("       chương trình tính toán giá sau giảm, tồn kho và gán badge thành công.")

            lines.append(f"\n[2] DỮ LIỆU BỊ TỪ CHỐI AN TOÀN (INVALID) : {invalid} inputs ({invalid/total*100:.1f}%)" if total else "")
            lines.append("    -> Ý NGHĨA KỸ THUẬT QUAN TRỌNG: Đây là các input vi phạm biên (giá âm, stock âm,")
            lines.append("       discount > 100, rating ngoài [0-5], tên > 100 ký tự, JSON hỏng cú pháp).")
            lines.append("       Validator đã PHÁT HIỆN VÀ CHẶN ĐỨNG THÀNH CÔNG, trả về valid: False kèm lỗi.")
            lines.append("       (*) ĐÂY LÀ HÀNH VI BẢO VỆ ĐÚNG ĐẮN CỦA HỆ THỐNG, KHÔNG PHẢI LỖI PHẦN MỀM!")

            lines.append(f"\n[3] LỖI RUNTIME / CRASH (EXCEPTION) : {exceptions + crashes} ca")
            lines.append("    -> Không ghi nhận ngoại lệ không xử lý nào làm sập ứng dụng.")
            lines.append(f"[4] LỖI LOGIC NGHIỆP VỤ (LOGIC_BUG) : {logic_bugs} ca")
            lines.append("    -> Toàn bộ kết quả đều tuân thủ đúng các bất biến nghiệp vụ.")

        lines.append("\n" + "=" * 70)
        lines.append("(*) Xem lại toàn bộ dữ liệu chi tiết ở tab 'Kết quả & biểu đồ'.")
        return "\n".join(lines)

    def _format_full_experiment_vietnamese(self, result: dict[str, Any]) -> str:
        count = result.get("input_count", 0)
        lines = [
            "=" * 70,
            "KẾT QUẢ TOÀN BỘ THÍ NGHIỆM CHUẨN (EXPERIMENT RUN)",
            "=" * 70,
            f"• Quy mô kiểm thử: {count:,} inputs cho mỗi phương pháp",
            "",
            "1. BLACK-BOX FUZZING (Kiểm tra biên BVA):",
            f"   - Hợp lệ (VALID)     : {result.get('blackbox', {}).get('valid', 0)} inputs",
            f"   - Bị từ chối (INVALID): {result.get('blackbox', {}).get('invalid', 0)} inputs (Validator chặn an toàn)",
            f"   - Lỗi / Crash        : {result.get('blackbox', {}).get('crashes', 0)}",
            "",
            "2. WHITE-BOX FUZZING (Độ phủ mã Bounded):",
            f"   - Độ phủ đạt được    : {result.get('whitebox', {}).get('coverage_points', 0)} dòng mã",
            f"   - Kích thước Corpus  : {result.get('whitebox', {}).get('corpus_size', 0)} seeds",
            f"   - Crash              : {result.get('whitebox', {}).get('crashes', 0)}",
            "",
            "3. MÔ HÌNH BỘ NHỚ PYTHON (Phân loại CWE):",
            f"   - An toàn (SAFE)     : {result.get('memory_model', {}).get('safe', 0)}",
            f"   - Đã chặn (BLOCKED)  : {result.get('memory_model', {}).get('blocked', 0)}",
            f"   - Phát hiện (DETECTED): {result.get('memory_model', {}).get('findings', 0)}",
            "",
            "=" * 70,
            "Đã cập nhật tự động các biểu đồ và báo cáo CSV trong thư mục reports/.",
        ]
        return "\n".join(lines)

    def _refresh_reports(self, select: str | None = None) -> None:
        reports = sorted(str(path.relative_to(PROJECT_ROOT)).replace("\\", "/") for path in (PROJECT_ROOT / "reports").glob("*.csv"))
        self.report_select["values"] = reports
        if select and select in reports:
            self.report_var.set(select)
        elif self.report_var.get() not in reports and reports:
            self.report_var.set(reports[0])
        if self.report_var.get():
            self._show_selected_report()

    def _show_selected_report(self) -> None:
        relative_path = self.report_var.get()
        path = PROJECT_ROOT / relative_path
        if not path.is_file():
            return
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        columns = list(rows[0].keys()) if rows else []
        self.results_tree.delete(*self.results_tree.get_children())
        self.results_tree["columns"] = columns
        for column in columns:
            title_text = column.replace("_", " ").title()
            if column == "result":
                title_text = "Kết quả (Result)"
            elif column == "scenario":
                title_text = "Kịch bản (Scenario)"
            elif column == "details":
                title_text = "Chi tiết (Details)"
            elif column == "time_ms":
                title_text = "Thời gian (ms)"
            elif column == "error":
                title_text = "Lỗi / Ngoại lệ"
            elif column == "invariant_violated":
                title_text = "Bất biến vi phạm (SAT)"
            self.results_tree.heading(column, text=title_text)
            self.results_tree.column(column, width=130 if column != "details" else 330, minwidth=80, stretch=True)
        for row in rows[:1000]:
            self.results_tree.insert("", "end", values=[row.get(column, "") for column in columns])
        if len(rows) > 1000:
            self.status.set(f"Hiển thị 1.000 trên {len(rows):,} dòng; file CSV vẫn lưu đầy đủ.")
        else:
            self.status.set(f"Báo cáo: {relative_path} ({len(rows):,} dòng).")

    def _generate_charts(self) -> None:
        self._run_background("Tạo biểu đồ trực quan", generate_charts, lambda _paths: self._load_charts(), count=None)

    def _load_charts(self) -> None:
        chart_dir = PROJECT_ROOT / "reports" / "charts"
        charts = sorted(chart_dir.glob("*.png")) if chart_dir.exists() else []
        self.chart_images.clear()
        self.chart_list.delete(0, "end")
        for chart in charts:
            self.chart_list.insert("end", chart.name)
        if charts:
            self.chart_list.selection_set(0)
            self._display_chart(charts[0])
        else:
            self.chart_preview.configure(text="Chưa có biểu đồ. Hãy chạy thử nghiệm rồi bấm Tạo biểu đồ.", image="")

    def _show_chart(self, _event: tk.Event) -> None:
        selection = self.chart_list.curselection()
        if selection:
            chart = PROJECT_ROOT / "reports" / "charts" / self.chart_list.get(selection[0])
            self._display_chart(chart)

    def _display_chart(self, path: Path) -> None:
        try:
            image = tk.PhotoImage(file=str(path))
        except tk.TclError:
            self.chart_preview.configure(text=f"Không thể mở biểu đồ: {path.name}", image="")
            return
        factor = max(1, (image.width() + 679) // 680, (image.height() + 459) // 460)
        if factor > 1:
            image = image.subsample(factor, factor)
        self.chart_images.append(image)
        self.chart_preview.configure(image=image, text="")


def main() -> None:
    os.chdir(PROJECT_ROOT)
    root = tk.Tk()
    AnalyzerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
