"""Desktop presentation UI for the Product Analyzer fuzzing project."""

import csv
import json
import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from typing import Any, Callable

from analyzer.product_analyzer import ProductAnalyzer
from experiment import run_experiment
from fuzzing.blackbox_fuzzer import BlackBoxFuzzer
from fuzzing.memory_fuzzer import MemoryModelFuzzer
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


class AnalyzerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.analyzer = ProductAnalyzer()
        self.action_buttons: list[ttk.Button] = []
        self.chart_images: list[tk.PhotoImage] = []

        root.title("Product Analyzer | Fuzz Lab")
        root.geometry("1180x780")
        root.minsize(900, 620)
        self._configure_style()
        self._build_layout()
        self._refresh_reports()

    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 10), background="#f1f4f0", foreground="#202b29")
        style.configure("TFrame", background="#f1f4f0")
        style.configure("TLabel", background="#f1f4f0", foreground="#202b29")
        style.configure("Header.TFrame", background="#183b35")
        style.configure("HeaderTitle.TLabel", background="#183b35", foreground="#f7f5eb", font=("Segoe UI Semibold", 20))
        style.configure("HeaderSub.TLabel", background="#183b35", foreground="#b9d6c7", font=("Segoe UI", 10))
        style.configure("Section.TLabel", font=("Segoe UI Semibold", 12), foreground="#183b35")
        style.configure("Accent.TButton", background="#d66a45", foreground="#ffffff", padding=(12, 8), font=("Segoe UI Semibold", 10))
        style.map("Accent.TButton", background=[("active", "#b95435"), ("disabled", "#a8b2ad")])
        style.configure("TButton", padding=(9, 6))
        style.configure("TNotebook", background="#f1f4f0", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(16, 9), font=("Segoe UI Semibold", 10))
        style.map("TNotebook.Tab", background=[("selected", "#ffffff"), ("!selected", "#dce5df")])
        style.configure("Treeview", rowheight=27, background="#ffffff", fieldbackground="#ffffff")
        style.configure("Treeview.Heading", font=("Segoe UI Semibold", 9), background="#dce5df")

    def _build_layout(self) -> None:
        header = ttk.Frame(self.root, style="Header.TFrame", padding=(24, 18))
        header.pack(fill="x")
        ttk.Label(header, text="PRODUCT ANALYZER", style="HeaderTitle.TLabel").pack(anchor="w")
        ttk.Label(header, text="Kiểm tra dữ liệu · Fuzzing · Báo cáo thử nghiệm", style="HeaderSub.TLabel").pack(anchor="w", pady=(3, 0))

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=18, pady=16)
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
        ttk.Label(self.root, textvariable=self.status, anchor="w", padding=(18, 7)).pack(fill="x")

    def _build_analysis_tab(self) -> None:
        self.analysis_tab.columnconfigure((0, 1), weight=1, uniform="panels")
        self.analysis_tab.rowconfigure(1, weight=1)
        ttk.Label(self.analysis_tab, text="Dữ liệu đầu vào (JSON)", style="Section.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))
        ttk.Label(self.analysis_tab, text="Kết quả kiểm tra", style="Section.TLabel").grid(row=0, column=1, sticky="w", padx=(16, 0), pady=(0, 8))

        self.input_text = ScrolledText(self.analysis_tab, wrap="word", font=("Cascadia Code", 10), background="#152824", foreground="#e5f1e9", insertbackground="#ffffff", padx=12, pady=12, borderwidth=0)
        self.input_text.grid(row=1, column=0, sticky="nsew")
        self.output_text = ScrolledText(self.analysis_tab, wrap="word", font=("Cascadia Code", 10), background="#ffffff", foreground="#202b29", padx=12, pady=12, borderwidth=0)
        self.output_text.grid(row=1, column=1, sticky="nsew", padx=(16, 0))
        self._set_text(self.input_text, json.dumps(SAMPLE_PRODUCT, ensure_ascii=False, indent=2))
        self._set_text(self.output_text, "Nhập JSON rồi chọn Phân tích.")

        actions = ttk.Frame(self.analysis_tab)
        actions.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Button(actions, text="Nạp ví dụ", command=self._load_sample).pack(side="left")
        ttk.Button(actions, text="Phân tích", style="Accent.TButton", command=self._analyze_product).pack(side="left", padx=(8, 0))

    def _build_fuzz_tab(self) -> None:
        self.fuzz_tab.columnconfigure(0, weight=1)
        self.fuzz_tab.rowconfigure(2, weight=1)
        controls = ttk.Frame(self.fuzz_tab)
        controls.grid(row=0, column=0, sticky="ew")
        ttk.Label(controls, text="Số input mỗi fuzzer:", style="Section.TLabel").pack(side="left")
        self.count_var = tk.StringVar(value="100")
        ttk.Spinbox(controls, from_=1, to=10000, increment=100, textvariable=self.count_var, width=9).pack(side="left", padx=(10, 18))

        buttons = ttk.Frame(self.fuzz_tab)
        buttons.grid(row=1, column=0, sticky="ew", pady=(14, 14))
        self._add_action_button(buttons, "Black-box", lambda: self._run_fuzzer("Black-box", lambda count: BlackBoxFuzzer(self.analyzer.analyze_json).run(count), "reports/blackbox_results.csv"))
        self._add_action_button(buttons, "White-box", lambda: self._run_fuzzer("White-box", lambda count: WhiteBoxFuzzer().run(count), "reports/whitebox_results.csv"))
        self._add_action_button(buttons, "Mô hình bộ nhớ", lambda: self._run_fuzzer("Mô hình bộ nhớ Python", lambda count: MemoryModelFuzzer().run(count), "reports/memory_results.csv"))
        self._add_action_button(buttons, "Chạy toàn bộ", self._run_full_experiment, accent=True)

        self.fuzz_output = ScrolledText(self.fuzz_tab, wrap="word", font=("Cascadia Code", 10), background="#ffffff", foreground="#202b29", padx=12, pady=12, borderwidth=0)
        self.fuzz_output.grid(row=2, column=0, sticky="nsew")
        self._set_text(self.fuzz_output, "Chọn một fuzzer để bắt đầu. Kết quả chi tiết sẽ được lưu trong thư mục reports/.")

    def _build_reports_tab(self) -> None:
        self.reports_tab.columnconfigure((0, 1), weight=1, uniform="reports")
        self.reports_tab.rowconfigure(1, weight=1)
        report_controls = ttk.Frame(self.reports_tab)
        report_controls.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        ttk.Label(report_controls, text="Bảng kết quả:", style="Section.TLabel").pack(side="left")
        self.report_var = tk.StringVar()
        self.report_select = ttk.Combobox(report_controls, textvariable=self.report_var, state="readonly", width=32)
        self.report_select.pack(side="left", padx=8)
        self.report_select.bind("<<ComboboxSelected>>", lambda _event: self._show_selected_report())
        ttk.Button(report_controls, text="Làm mới", command=self._refresh_reports).pack(side="left")
        ttk.Button(report_controls, text="Tạo biểu đồ", style="Accent.TButton", command=self._generate_charts).pack(side="left", padx=8)

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
        ttk.Label(chart_panel, text="Biểu đồ", style="Section.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.chart_list = tk.Listbox(chart_panel, height=5, font=("Segoe UI", 10), background="#ffffff", borderwidth=0, activestyle="none")
        self.chart_list.grid(row=1, column=0, sticky="new")
        self.chart_list.bind("<<ListboxSelect>>", self._show_chart)
        self.chart_preview = ttk.Label(chart_panel, text="Chạy thử nghiệm rồi tạo biểu đồ.", anchor="center")
        self.chart_preview.grid(row=2, column=0, sticky="nsew", pady=(12, 0))

    def _add_action_button(self, parent: ttk.Frame, text: str, command: Callable[[], None], accent: bool = False) -> None:
        button = ttk.Button(parent, text=text, command=command, style="Accent.TButton" if accent else "TButton")
        button.pack(side="left", padx=(0, 8))
        self.action_buttons.append(button)

    @staticmethod
    def _set_text(widget: ScrolledText, value: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.configure(state="disabled")

    def _load_sample(self) -> None:
        self.input_text.delete("1.0", "end")
        self.input_text.insert("1.0", json.dumps(SAMPLE_PRODUCT, ensure_ascii=False, indent=2))

    def _analyze_product(self) -> None:
        raw = self.input_text.get("1.0", "end").strip()
        result = self.analyzer.analyze_json(raw)
        self._set_text(self.output_text, json.dumps(result, ensure_ascii=False, indent=2))
        self.status.set("Sản phẩm hợp lệ" if result.get("valid") else "Input có lỗi cần kiểm tra")

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

        self._run_background(title, task, lambda result: self._show_run_result(title, result, report_path))

    def _run_full_experiment(self) -> None:
        try:
            count = self._input_count()
        except ValueError as exc:
            messagebox.showerror("Giá trị không hợp lệ", str(exc), parent=self.root)
            return
        self._run_background("Toàn bộ thí nghiệm", lambda: run_experiment(count), self._show_experiment_result)

    def _run_background(self, title: str, task: Callable[[], Any], on_success: Callable[[Any], None]) -> None:
        self.status.set(f"Đang chạy: {title}...")
        for button in self.action_buttons:
            button.configure(state="disabled")

        def work() -> None:
            try:
                result = task()
            except Exception as exc:
                self.root.after(0, lambda error=exc: self._finish_error(title, error))
            else:
                self.root.after(0, lambda value=result: self._finish_success(title, value, on_success))

        threading.Thread(target=work, daemon=True).start()

    def _finish_success(self, title: str, result: Any, callback: Callable[[Any], None]) -> None:
        for button in self.action_buttons:
            button.configure(state="normal")
        self.status.set(f"Hoàn tất: {title}")
        callback(result)

    def _finish_error(self, title: str, error: Exception) -> None:
        for button in self.action_buttons:
            button.configure(state="normal")
        self.status.set(f"Có lỗi khi chạy: {title}")
        messagebox.showerror("Không thể hoàn thành", str(error), parent=self.root)

    def _show_run_result(self, title: str, result: dict[str, Any], report_path: str) -> None:
        self._set_text(self.fuzz_output, f"{title}\n\n{json.dumps(result, ensure_ascii=False, indent=2)}")
        self.notebook.select(self.fuzz_tab)
        self._refresh_reports(select=report_path)

    def _show_experiment_result(self, result: dict[str, Any]) -> None:
        self._set_text(self.fuzz_output, f"Toàn bộ thí nghiệm\n\n{json.dumps(result, ensure_ascii=False, indent=2)}")
        self.notebook.select(self.fuzz_tab)
        self._refresh_reports(select="reports/memory_results.csv")
        self._load_charts()

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
            self.results_tree.heading(column, text=column.replace("_", " ").title())
            self.results_tree.column(column, width=125 if column != "details" else 310, minwidth=80, stretch=True)
        for row in rows[:1000]:
            self.results_tree.insert("", "end", values=[row.get(column, "") for column in columns])
        if len(rows) > 1000:
            self.status.set(f"Hiển thị 1.000 trên {len(rows):,} dòng; CSV vẫn đầy đủ.")

    def _generate_charts(self) -> None:
        self._run_background("Tạo biểu đồ", generate_charts, lambda _paths: self._load_charts())

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
            self.chart_preview.configure(text="Chưa có biểu đồ. Hãy chạy thử nghiệm trước.", image="")

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