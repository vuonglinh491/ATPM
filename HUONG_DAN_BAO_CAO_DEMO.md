# Hướng dẫn báo cáo và demo dự án

Tài liệu này hướng dẫn chuẩn bị môi trường, trình diễn các chức năng chính và hoàn thiện báo cáo cho dự án **Product Analyzer Fuzz Testing**. Các số liệu trong báo cáo phải lấy từ lần chạy thực nghiệm của chính bạn; không dùng số liệu cũ trong thư mục `reports/` làm kết quả chính thức.

## 1. Mục tiêu và thông điệp chính

Trong phần trình bày, tập trung trả lời bốn câu hỏi:

1. Product Analyzer nhận dữ liệu gì và kiểm tra những quy tắc nào?
2. Black-box và white-box fuzzing tạo, chạy và đánh giá input khác nhau ra sao?
3. Kết quả được ghi lại ở đâu và có thể tái hiện như thế nào?
4. Mô hình bộ nhớ minh họa CWE ra sao, và vì sao đó không phải bằng chứng có lỗ hổng/CVE trong sản phẩm thật?

Thông điệp kết luận nên giới hạn đúng phạm vi: dự án là công cụ học tập/thực nghiệm cho một analyzer Python; black-box quan sát hành vi bên ngoài, white-box dùng coverage của mã nguồn, còn memory model mô phỏng an toàn một số trạng thái bộ nhớ.

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

Kiểm tra test trước khi trình bày:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Ghi lại kết quả thực tế của lệnh test. Nếu test lỗi, xử lý trước buổi demo; không đọc lại số `passed` từ tài liệu cũ như thể vừa chạy.

Chạy một thực nghiệm mới để cập nhật báo cáo và biểu đồ:

```powershell
.\.venv\Scripts\python.exe -m experiment --count 1000
```

`--count` là số input cho **mỗi** fuzzer. Lần chạy này cập nhật các CSV, `reports/summary.json` và biểu đồ; các kết quả trước đó trong cùng tên file sẽ bị thay thế. Nếu cần so sánh nhiều quy mô, hãy sao lưu thư mục `reports/` sau mỗi lần chạy, ví dụ:

```powershell
Copy-Item reports reports-count-1000 -Recurse
```

Kiểm tra các đầu ra cần dùng trong báo cáo:

- `reports/summary.json`: thống kê tổng hợp lần chạy gần nhất.
- `reports/blackbox_results.csv`: kết quả theo từng input black-box.
- `reports/whitebox_results.csv`: kết quả và coverage feedback theo iteration.
- `reports/memory_results.csv`: kết quả mô phỏng và nhãn CWE.
- `reports/charts/`: các biểu đồ được tạo từ CSV.
- `crashes/`: input finding/exception được lưu để xem xét hoặc tái hiện, nếu có.

## 3. Kịch bản demo giao diện desktop

Khởi chạy giao diện:

```powershell
.\.venv\Scripts\python.exe app.py
```

### Phần A — Phân tích sản phẩm

1. Mở tab **Phân tích sản phẩm**; JSON mẫu được nạp sẵn.
2. Chọn **Phân tích**.
3. Chỉ ra `valid`, `final_price`, `inventory_value`, `average_rating`, `errors` và `warnings`.
4. Thay JSON bằng ví dụ sai dưới đây rồi phân tích lại. Có thể thay nội dung trong vùng JSON:

```json
{
  "id": "P002",
  "name": "Phone",
  "category": "Mobile",
  "price": -1,
  "stock": 2,
  "discount": 101,
  "rating": 4
}
```

Giải thích rằng input sai quy tắc bị đánh dấu không hợp lệ và lỗi được trả về có cấu trúc; đây là hành vi từ chối input không hợp lệ, không phải crash.

### Phần B — Chạy fuzzing

1. Mở tab **Phòng thí nghiệm fuzzing**.
2. Đặt số input là `100` cho phần trình diễn ngắn.
3. Chọn lần lượt **Black-box**, **White-box**, và **Mô hình bộ nhớ**; đợi trạng thái hoàn tất sau mỗi lần chạy.
4. Chỉ ra phần tổng kết và đường dẫn CSV. Các tác vụ chạy nền; trong lúc chạy, nút fuzzing tạm khóa.
5. Nếu cần một lượt tổng hợp duy nhất, nhập số lượng mong muốn rồi chọn **Chạy toàn bộ**. Lượt này chạy cả ba bộ thử nghiệm, tạo summary và biểu đồ. Dùng `1000` hoặc `10000` cho thực nghiệm chính thức thay vì demo trực tiếp nếu thời gian có hạn.

### Phần C — Xem kết quả

1. Mở tab **Kết quả & biểu đồ**.
2. Chọn lần lượt `blackbox_results.csv`, `whitebox_results.csv` và `memory_results.csv` để xem bảng dữ liệu.
3. Chọn **Tạo biểu đồ**, sau đó chọn tên biểu đồ để xem trước.
4. Khi chạy nhiều dữ liệu, giao diện chỉ hiển thị tối đa 1.000 dòng; CSV trên đĩa vẫn giữ đầy đủ kết quả.

## 4. Demo thay thế bằng dòng lệnh

Menu dòng lệnh:

```powershell
.\.venv\Scripts\python.exe main.py
```

Menu hiện có các thao tác: phân tích JSON mẫu/tự nhập; chạy black-box 100 input; chạy white-box 100 input; tạo biểu đồ; liệt kê file JSON trong `crashes/`; chạy experiment 1.000 input; chạy memory model 100 ca; thoát.

Chạy riêng các quy mô thực nghiệm:

```powershell
.\.venv\Scripts\python.exe -m experiment --count 100
.\.venv\Scripts\python.exe -m experiment --count 1000
.\.venv\Scripts\python.exe -m experiment --count 10000
```

Đo coverage của bộ test:

```powershell
.\.venv\Scripts\python.exe -m coverage run -m pytest
.\.venv\Scripts\python.exe -m coverage report
.\.venv\Scripts\python.exe -m coverage html
```

Lệnh coverage ở trên đo test suite. `coverage_points` trong white-box report là số dòng mới được feedback/corpus thu nhận trong lần chạy fuzzer; không nên gọi hai chỉ số này là cùng một phép đo.

## 5. Kịch bản thuyết trình miệng

Có thể dùng lời dẫn sau, điều chỉnh theo thời lượng được giao:

> Đề tài xây dựng Product Analyzer cho dữ liệu sản phẩm JSON/CSV và dùng fuzzing để kiểm tra cách chương trình xử lý input hợp lệ, biên và bất thường. Analyzer parse dữ liệu, kiểm tra field và luật nghiệp vụ, sau đó mới tính giá sau giảm, giá trị tồn kho và rating.
>
> Black-box fuzzer không dùng thông tin coverage để chọn input; nó gửi input và phân loại kết quả quan sát được. White-box fuzzer đo coverage mã analyzer và giữ input tạo ra dòng thực thi mới làm corpus. Bên cạnh đó, memory model viết bằng Python mô phỏng một số điều kiện liên quan đến kiểu và vòng đời bộ nhớ.
>
> Kết quả được ghi theo từng input vào CSV, được tổng hợp trong JSON và có thể dựng thành biểu đồ. Finding cần được kiểm tra và tái hiện trước khi kết luận. Các nhãn CWE của memory model chỉ mô tả tình huống mô phỏng; chúng không khẳng định chương trình có lỗ hổng bảo mật hay CVE.

## 6. Bố cục báo cáo đề xuất

Có thể dùng bố cục dưới đây để hoàn thiện `REPORT.md`:

1. **Tổng quan:** bài toán, động lực, mục tiêu, phạm vi và giới hạn.
2. **Cơ sở lý thuyết:** fuzzing, seed/mutation, oracle, coverage feedback, CWE/CVE.
3. **Phân tích và thiết kế:** kiến trúc `parser -> validator -> calculator -> output`; sơ đồ luồng của các fuzzer.
4. **Triển khai:** Product Analyzer, test suite, black-box, white-box, memory model, lưu finding và sinh report.
5. **Thiết kế thực nghiệm:** môi trường Python/Windows, phiên bản phụ thuộc nếu đã ghi nhận, số input, cách chạy, seed/cấu hình, tiêu chí và giới hạn phép đo.
6. **Kết quả và đánh giá:** bảng số liệu, biểu đồ, phân tích điểm mạnh/yếu, finding tiêu biểu và tái hiện.
7. **Kết luận và hướng phát triển:** kết quả đạt được, hạn chế, công việc tiếp theo.

### Bảng kết quả cần điền từ lần chạy mới nhất

| Chỉ số | Black-box | White-box | Memory model |
|---|---:|---:|---:|
| Số input | `summary.json` | `summary.json` | `summary.json` |
| Hợp lệ / an toàn | đếm `VALID` trong CSV | đếm `VALID` trong CSV | `safe` |
| Không hợp lệ | đếm `INVALID` trong CSV | đếm `INVALID` trong CSV | — |
| Exception/crash | summary và CSV | `crashes` trong summary | — |
| Timeout / output bất thường | summary black-box | — | — |
| Coverage points / corpus | — | summary white-box | — |
| Findings mô phỏng | — | — | `findings`, `blocked`, CWE counts |
| Thời gian | `execution_time_seconds` black-box | chưa có trường thời gian trong summary hiện tại | chưa có trường thời gian trong summary hiện tại |

Lưu ý khi diễn giải:

- Black-box `unique_failures` đếm fingerprint lỗi đã lưu, không phải mọi input không hợp lệ.
- White-box `coverage_points` là các điểm dòng mới được quan sát bởi cơ chế feedback của fuzzer; không đồng nhất với phần trăm line/branch coverage của toàn dự án.
- Memory model phân biệt `SAFE`, `BLOCKED` và `DETECTED`. `BLOCKED` là trường hợp guard chặn điều kiện nguy hiểm; `DETECTED` là trạng thái lỗi được mô phỏng/phát hiện trong model.
- CWE là phân loại điểm yếu, không phải CVE. Không trình bày `DETECTED` của mô hình Python thành lỗ hổng bộ nhớ của Product Analyzer.
- Nếu không có exception/finding trong lần chạy, báo đúng kết quả đó; không suy diễn ra lỗi để làm demo hấp dẫn hơn.
- Thời gian của lần chạy phụ thuộc môi trường. So sánh thời gian chỉ có ý nghĩa khi ghi rõ thiết bị/cấu hình và dùng cùng điều kiện chạy.

## 7. Slide và minh chứng nên chuẩn bị

Một bài trình bày ngắn có thể gộp nội dung trong `SLIDES.md` thành 10–12 slide:

1. Tên đề tài và vấn đề.
2. Mục tiêu, phạm vi và giới hạn.
3. Khái niệm fuzzing và oracle.
4. Kiến trúc Product Analyzer.
5. Black-box: generator, seed, mutation và kết quả.
6. White-box: coverage feedback và corpus.
7. Memory model và phân biệt CWE/CVE.
8. Thiết kế thực nghiệm.
9. Bảng số liệu và biểu đồ lấy từ lần chạy mới nhất.
10. Demo trực tiếp.
11. Hạn chế và hướng phát triển.
12. Kết luận.

Chụp minh chứng từ dự án của bạn: kết quả pytest, input hợp lệ và input lỗi trong giao diện, màn hình thống kê fuzzer, bảng CSV, biểu đồ và `summary.json`. Ghi chú số lượng input và lệnh chạy trên slide kết quả để người xem biết số liệu thuộc thực nghiệm nào.

## 8. Danh sách kiểm tra nhanh

Trước buổi trình bày:

- [ ] Môi trường ảo và dependencies đã sẵn sàng.
- [ ] `pytest` chạy thành công và đã ghi lại kết quả mới.
- [ ] Experiment đã chạy; bảng, JSON và biểu đồ cùng thuộc một lần chạy.
- [ ] Đã sao lưu report nếu cần so sánh nhiều quy mô.
- [ ] Giao diện mở được; đã thử trước các nút cần demo.
- [ ] Có sẵn ví dụ hợp lệ và không hợp lệ.
- [ ] Đã phân biệt lỗi validation, exception, finding, CWE và CVE.
- [ ] Báo cáo không dùng số liệu chưa chạy hoặc tự suy diễn.

## 9. Xử lý tình huống thường gặp

- **Không mở được giao diện:** kiểm tra Tkinter bằng `.\.venv\Scripts\python.exe -c "import tkinter; print('Tkinter OK')"`; nếu thiếu, repair/cài lại Python có Tcl/Tk.
- **Thiếu package:** chạy `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.
- **CSV hoặc biểu đồ trống:** chạy fuzzer/experiment trước, sau đó bấm **Làm mới** hoặc **Tạo biểu đồ**.
- **Không có finding trong `crashes/`:** đây vẫn là kết quả hợp lệ; demo input bị validation từ chối và giải thích oracle.
- **Muốn tái hiện finding đã lưu:** dùng đường dẫn JSON có thật trong thư mục `crashes/`, ví dụ `.\.venv\Scripts\python.exe reproduce_crash.py crashes\blackbox\crash_001.json`. Không dùng tên ví dụ nếu file đó không tồn tại.

## 10. Tài liệu liên quan

- [README.md](README.md): cài đặt và tham chiếu lệnh vận hành.
- [REPORT.md](REPORT.md): nội dung báo cáo đồ án.
- [SLIDES.md](SLIDES.md): dàn ý slide.
