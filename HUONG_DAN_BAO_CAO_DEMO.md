# Hướng dẫn báo cáo và demo dự án

Tài liệu này hướng dẫn chuẩn bị môi trường, trình diễn các chức năng chính và hoàn thiện báo cáo cho dự án **Product Analyzer Fuzz Testing**. Các số liệu trong báo cáo phải lấy từ lần chạy thực nghiệm của chính bạn; không dùng số liệu cũ trong thư mục `reports/` làm kết quả chính thức.

## 1. Mục tiêu và thông điệp chính

Trong phần trình bày, tập trung trả lời năm câu hỏi cốt lõi:

1. Product Analyzer nhận dữ liệu gì và kiểm tra những quy tắc nào?
2. Black-box và white-box fuzzing tạo, chạy và đánh giá input khác nhau ra sao?
3. **Ý nghĩa của VALID và INVALID khi chạy fuzzing là gì? Tại sao INVALID không phải là bug/crash?**
4. Mô hình bộ nhớ minh họa CWE ra sao: Phân biệt `SAFE`, `BLOCKED` (phòng ngừa trước) và `DETECTED` (phát hiện vi phạm sở hữu)?
5. **Hệ thống phát hiện lỗi logic và phản ví dụ SAT như thế nào khi gặp kịch bản sinh lỗi (SAT Counterexample & Crash Simulation)?**

Thông điệp kết luận nên giới hạn đúng phạm vi: dự án là công cụ học tập/thực nghiệm cho một analyzer Python; black-box quan sát hành vi bên ngoài theo BVA, white-box dùng coverage của mã nguồn, memory model mô phỏng an toàn một số trạng thái bộ nhớ theo CWE, và SAT Fuzzer chứng minh tính khả thi của việc tìm phản ví dụ tự động.

---

## 2. Chuẩn bị trước buổi demo

Mở PowerShell tại thư mục dự án:

```powershell
cd D:\ATPM
```

Nếu chưa tạo môi trường ảo, thiết lập một lần:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Kiểm tra test trước khi trình bày (toàn bộ **57 tests** pass):

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Ghi lại kết quả thực tế của lệnh test. Nếu test lỗi, xử lý trước buổi demo.

Chạy một thực nghiệm mới để cập nhật báo cáo và biểu đồ:

```powershell
.\.venv\Scripts\python.exe -m experiment --count 1000
```

`--count` là số input cho **mỗi** fuzzer. Lần chạy này cập nhật các CSV, `reports/summary.json` và biểu đồ.

Kiểm tra các đầu ra cần dùng trong báo cáo:

- `reports/summary.json`: thống kê tổng hợp lần chạy gần nhất.
- `reports/blackbox_results.csv`: kết quả theo từng input black-box.
- `reports/whitebox_results.csv`: kết quả và coverage feedback theo iteration.
- `reports/memory_results.csv`: kết quả mô phỏng và nhãn CWE.
- `reports/sat_fuzzing_results.csv`: kết quả tìm phản ví dụ SAT.
- `reports/crash_simulation_results.csv`: kết quả mô phỏng runtime crash.
- `reports/charts/`: các biểu đồ được tạo từ CSV.
- `crashes/`: các thư mục lưu finding: `crashes/blackbox/`, `crashes/sat_counterexamples/`, `crashes/runtime_crashes/`, `crashes/memory_faults/`.

---

## 3. Kịch bản demo giao diện desktop (`app.py`)

Khởi chạy giao diện:

```powershell
.\.venv\Scripts\python.exe app.py
```

### Phần A — Phân tích sản phẩm
1. Mở tab **Phân tích sản phẩm**; JSON mẫu được nạp sẵn.
2. Chọn **Phân tích**.
3. Chỉ ra các thông tin nghiệp vụ hiển thị bằng tiếng Việt: `Giá sau giảm`, `Giá trị tồn kho`, `Điểm đánh giá`, `Phân hạng sản phẩm` (`BEST_SELLER`), và cảnh báo chính sách bảo hành `Camera`.
4. Bấm nút **Nạp ví dụ lỗi biên (Invalid)** rồi chọn **Phân tích**:
   - Giải thích: Validator đã phát hiện các lỗi biên (giá âm, discount > 100, rating > 5) và **từ chối an toàn** (`valid: false`).
   - Nhấn mạnh: Đây là **hành vi phòng thủ mong muốn (Sanitization)**, chương trình không bị crash.

### Phần B1 — Chạy các bộ fuzzing chuẩn (An toàn & Phòng thủ)
1. Mở tab **Phòng thí nghiệm fuzzing**.
2. Đặt số input là `100` để demo nhanh.
3. Chọn lần lượt:
   - **Black-box (Biên BVA):** Tỷ lệ `INVALID` cao (~80%) chứng minh validator lọc sạch dữ liệu ngoài biên.
   - **White-box (Độ phủ Bounded):** Tỷ lệ `VALID` cao (~80%), hiển thị số `coverage_points` (dòng mã analyzer đã đi qua).
   - **Mô hình bộ nhớ (CWE an toàn):** Phân loại rõ `SAFE`, `BLOCKED` (chặn trước CWE-121, CWE-190, CWE-476, CWE-789) và `DETECTED` (phát hiện CWE-401, CWE-415, CWE-416).

### Phần B2 — Mô phỏng Sinh lỗi & Phản ví dụ SAT (TRỌNG TÂM TRẢ LỜI CÂU HỎI THẦY CÔ)
> Khi thầy cô hỏi: *"Fuzzer chạy chỉ thấy valid với invalid, vậy khi có lỗi thật thì fuzzer bắt như thế nào? Có phản ví dụ SAT không?"*

1. Bấm nút màu đỏ: **"Phản ví dụ SAT (Lỗi Logic)"**:
   - Màn hình lập tức hiển thị thông báo tiếng Việt:
     `[!] PHÁT HIỆN LỖI LOGIC / PHẢN VÍ DỤ SAT: ... trường hợp`
   - Chỉ vào các phản ví dụ tìm được:
     + Phản ví dụ $\text{INV}_1$: Chiết khấu 50% nhưng giá sau giảm lại lớn hơn giá gốc ($final\_price > price$).
     + Phản ví dụ $\text{INV}_2$: Chiết khấu 150% lọt qua validator làm giá sau giảm bị âm.
     + Phản ví dụ $\text{INV}_4$: Đầu vào $rating = 0$ làm sập phép chia số học `ZeroDivisionError`.
   - Giải thích: Về mặt hình thức, bài toán tìm phản ví dụ $\text{SAT}(\neg \text{Invariant})$ đã được thỏa mãn. Fuzzer đã lưu các file JSON phản ví dụ vào `crashes/sat_counterexamples/`.
2. Bấm nút màu đỏ: **"Mô phỏng Crash (Ngoại lệ Runtime)"**:
   - Fuzzer kích hoạt các unhandled exceptions (Null-byte string injection, Virtual memory exhaustion simulation).
3. Bấm nút màu đỏ: **"Lỗi bộ nhớ nghiêm trọng (CWE Faults)"**:
   - Mô phỏng crash tiến trình khi gặp Double-free (CWE-415) hoặc Use-after-free (CWE-416) ở chế độ Unsafe.

### Phần C — Xem kết quả và biểu đồ
1. Mở tab **Kết quả & biểu đồ**.
2. Dropdown danh sách CSV đã cập nhật đầy đủ các báo cáo:
   - `blackbox_results.csv`
   - `whitebox_results.csv`
   - `memory_results.csv`
   - `sat_fuzzing_results.csv`
   - `crash_simulation_results.csv`
   - `unsafe_memory_results.csv`
3. Bấm **Tạo biểu đồ trực quan**, chọn biểu đồ trong danh sách để trình chiếu hình ảnh trực quan cho hội đồng.

---

## 4. Kịch bản trả lời phản biện (Q&A)

### Câu 1: "Làm rõ kết quả invalid/valid khi chạy fuzzing?"
- **Trả lời:**
  - `VALID` là input vượt qua toàn bộ Validator, nằm trong vùng Bounded, chương trình tính toán tài chính và phân hạng thành công.
  - `INVALID` là input vi phạm schema hoặc nằm ngoài biên ($price < 0$, $discount > 100$, sai kiểu...). Validator phát hiện và từ chối an toàn (`valid: false`, nạp lỗi vào `errors`).
  - **Quan trọng:** `INVALID` là **hành vi phòng thủ đúng đắn**, KHÔNG PHẢI lỗi phần mềm và KHÔNG PHẢI lỗi của fuzzer. Trong Black-box, vì mục tiêu là thử thách biên (BVA) nên tỷ lệ `INVALID` cao (~80%) chứng minh cơ chế phòng vệ của hệ thống hoạt động rất tốt.

### Câu 2: "Giải thích kết quả chạy các kiểm thử (memory, fuzzing)?"
- **Trả lời:**
  - Fuzzing: Black-box tập trung vào biên nên tỷ lệ `INVALID` cao; White-box hướng theo độ phủ dòng (`coverage.py`) nên ưu tiên nạp seed hợp lệ để đào sâu logic nghiệp vụ, do đó tỷ lệ `VALID` cao hơn.
  - Mô hình bộ nhớ: Phân biệt rõ 3 mức:
    + `SAFE`: Thao tác an toàn trong hạn mức.
    + `BLOCKED`: Guard phòng vệ chặn đứng TRƯỚC KHI xảy ra sự cố (CWE-121 tràn buffer stack, CWE-190 tràn số nguyên, CWE-476 null pointer, CWE-789 cấp phát quá dung lượng).
    + `DETECTED`: Trạng thái vi phạm quyền sở hữu tài nguyên sau khi thực thi (CWE-401 rò rỉ bộ nhớ, CWE-415 double free, CWE-416 use-after-free).

### Câu 3: "Chương trình sinh lỗi và phản ví dụ SAT hoạt động ra sao?"
- **Trả lời:**
  - Trong kiểm chứng hình thức, ta định nghĩa các bất biến an toàn:
    + $\text{INV}_1: final\_price \le price$
    + $\text{INV}_2: final\_price \ge 0 \land inventory\_value \ge 0$
    + $\text{INV}_4: \text{Không phát sinh ZeroDivisionError khi tính toán}$
  - Khi chương trình có khiếm khuyết (hoặc bật chế độ mô phỏng lỗi), fuzzer tự động giải bài toán $\text{SAT}(\neg \text{Invariant})$ để tìm ra **Phản ví dụ (Counterexample)**:
    + Tìm ra input khiến giá sau giảm tăng lên thay vì giảm đi.
    + Tìm ra input khiến giá bị âm do discount vượt trần.
    + Tìm ra input $rating = 0$ làm sập phép chia số học.
  - Toàn bộ phản ví dụ được lưu trữ vào thư mục `crashes/` dưới dạng JSON để có thể tái hiện và kiểm tra độc lập.

---

## 5. Danh sách kiểm tra trước khi lên báo cáo

- [ ] Chạy `pytest` xác nhận **57 passed** thành công.
- [ ] Chạy `python app.py`, thử bấm qua các nút Fuzzing chuẩn và các nút Mô phỏng lỗi/SAT màu đỏ.
- [ ] Xác nhận toàn bộ thông báo kết quả hiển thị bằng Tiếng Việt rõ ràng.
- [ ] Xác nhận các biểu đồ trong tab "Kết quả & biểu đồ" hiển thị đầy đủ.
- [ ] Nắm vững cách giải thích `VALID`, `INVALID`, `SAFE`, `BLOCKED`, `DETECTED`, và `SAT Counterexample`.
