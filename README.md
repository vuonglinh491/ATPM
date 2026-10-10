# Product Analyzer Fuzz Testing

## Mô tả dự án

Product Analyzer Fuzz Testing là đồ án mô phỏng quy trình kiểm thử độ tin cậy và an toàn của một thành phần xử lý dữ liệu sản phẩm thương mại điện tử. Chương trình nhận sản phẩm ở định dạng JSON hoặc CSV, xác thực trường dữ liệu và kiểu, kiểm tra các giới hạn nghiệp vụ, sau đó tính giá sau giảm và giá trị tồn kho.

Dự án kết hợp black-box fuzzing để quan sát hành vi từ bên ngoài, white-box fuzzing để tận dụng coverage của mã Python, và một mô hình bộ nhớ viết hoàn toàn bằng Python để mô phỏng rủi ro về giới hạn buffer, kiểu dữ liệu, cấp phát và vòng đời bộ nhớ. Kết quả được lưu thành báo cáo để có thể xem lại input, trạng thái xử lý và phân loại CWE.

Mục tiêu là giúp thử nghiệm có hệ thống với dữ liệu hợp lệ, dữ liệu biên và dữ liệu bất thường; so sánh hai phương pháp fuzzing chính; đồng thời thực hành nhận diện các lớp điểm yếu bộ nhớ. Mô hình bộ nhớ chỉ mô phỏng và phân loại trạng thái nguy hiểm, không truy cập hay làm hỏng bộ nhớ thật. CWE là nhãn phân loại, không khẳng định sản phẩm có lỗ hổng hay CVE đã được cấp.

Dự án có hai phương pháp fuzzing chính cho Product Analyzer và một mô hình bộ nhớ bổ trợ:

- **Black-box fuzzing**: fuzzer không sử dụng thông tin bên trong mã nguồn, chỉ gửi input và quan sát output, exception hoặc timeout.
- **White-box fuzzing**: fuzzer biết mã nguồn và sử dụng coverage feedback để giữ lại những input đi qua dòng xử lý mới.
- **Memory-model fuzzing**: Python mô phỏng kiểm tra biên/kiểu và vòng đời bộ nhớ; fuzzer ghi kết quả theo CWE, không cần C compiler.

## Bắt đầu nhanh

Mở PowerShell tại thư mục dự án, sau đó chạy:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest
python app.py
```

Kết quả mong đợi: test kết thúc thành công và cửa sổ **Product Analyzer | Fuzz Lab** mở ra. Có thể bỏ qua bước kích hoạt môi trường và gọi trực tiếp `.venv\Scripts\python.exe` như các ví dụ bên dưới.

## 1. Chức năng chính

### 1.1. Phân tích sản phẩm

Product Analyzer thực hiện các công việc sau:

1. Đọc một sản phẩm từ JSON hoặc CSV.
2. Kiểm tra field bắt buộc: `id`, `name`, `category`, `price`, `stock`, `discount`, `rating`.
3. Kiểm tra kiểu dữ liệu và giới hạn nghiệp vụ:
	- `id` không được rỗng.
	- `name` phải là chuỗi, không rỗng và không dài quá 100 ký tự.
	- `price` phải là số và không âm.
	- `stock` phải là số nguyên và không âm.
	- `discount` nằm trong khoảng từ 0 đến 100.
	- `rating` nằm trong khoảng từ 0 đến 5.
	- `category` và `description` phải là chuỗi nếu được cung cấp.
4. Tính toán:
	- Giá sau giảm: `price * (1 - discount / 100)`.
	- Giá trị tồn kho: `price * stock`.
	- Điểm rating trung bình của sản phẩm.
5. Trả về trạng thái hợp lệ, lỗi và cảnh báo.

### 1.2. Fuzzing

Fuzzer tạo hoặc biến đổi nhiều loại input bất thường:

- Thiếu field hoặc object rỗng.
- Giá trị âm, bằng 0, cực lớn và giá trị biên.
- Sai kiểu như chuỗi, danh sách, object, `null` và boolean.
- Chuỗi rỗng, chuỗi rất dài, ký tự đặc biệt và Unicode.
- JSON sai cú pháp.
- Field bổ sung không được định nghĩa.

Fuzzer theo dõi các kết quả `VALID`, `INVALID`, `EXCEPTION`, `TIMEOUT`, `INVALID_OUTPUT` và `LOGIC_BUG`. Finding được lưu để có thể kiểm tra lại.

Mô hình bộ nhớ bổ sung các tình huống giới hạn tên, sai kiểu, con trỏ bắt buộc bị thiếu, cấp phát quá lớn, phép nhân kích thước bị tràn, rò rỉ bộ nhớ, giải phóng hai lần và truy cập sau khi giải phóng. Đây là mô hình an toàn có kiểm soát: không thực hiện ghi tràn, dereference con trỏ null, double-free hoặc leak heap thật.

Các finding được gắn CWE để mô tả lớp lỗi, gồm CWE-121, CWE-190, CWE-401, CWE-415, CWE-416, CWE-476 và CWE-789. CWE là phân loại điểm yếu, không phải bằng chứng một lỗ hổng đã tồn tại trong sản phẩm. Cột CVE để trống; chỉ điền CVE sau khi có lỗ hổng cụ thể được xác minh và mã CVE chính thức.

## 2. Ví dụ input và output

Input JSON hợp lệ:

```json
{
  "id": "P001",
  "name": "Camera Wifi",
  "category": "Camera",
  "price": 1500000,
  "stock": 20,
  "discount": 10,
  "rating": 4.5,
  "description": "Camera giam sat wifi"
}
```

Output tương ứng:

```json
{
  "valid": true,
  "final_price": 1350000.0,
  "inventory_value": 30000000,
  "average_rating": 4.5,
  "errors": [],
  "warnings": [
	 "Camera products should include a warranty description"
  ]
}
```

Khi input không hợp lệ, `valid` là `false`, các phép tính trả về `null` và nguyên nhân được ghi trong mảng `errors`.

## 3. Luồng hoạt động

### 3.1. Luồng phân tích sản phẩm

```text
Input JSON/CSV
		|
		v
	  Parser
		|
		v
	Validator ---- lỗi ----> Output errors
		|
		v
	Calculator
		|
		v
Output valid, calculations, warnings
```

Chi tiết:

1. `parser.py` chuyển chuỗi JSON/CSV thành dictionary Python.
2. Nếu input sai cú pháp hoặc không phải object, parser tạo `InputParseError` và analyzer trả lỗi có cấu trúc.
3. `validator.py` kiểm tra field, kiểu dữ liệu, giới hạn và cảnh báo dữ liệu bất thường.
4. Nếu có lỗi validation, analyzer dừng tính toán và trả danh sách lỗi.
5. Nếu dữ liệu hợp lệ, `product_analyzer.py` tính giá sau giảm, giá trị tồn kho và rating.
6. Với sản phẩm thuộc category `Camera` hoặc thiếu description, hệ thống thêm warning.

### 3.2. Luồng black-box fuzzing

```text
Seed corpus / Random generator
				 |
				 v
			 Mutation
				 |
				 v
	Product Analyzer như hộp đen
				 |
				 v
 Oracle: valid / invalid / exception / timeout / logic bug
				 |
				 v
 CSV report + crash/finding files
```

Black-box fuzzer chỉ gọi hàm chương trình thông qua input text. Nó không đọc coverage và không quyết định input dựa trên nhánh code. Mỗi input được chạy trong giới hạn timeout; lỗi mới được fingerprint để tránh lưu trùng.

### 3.3. Luồng white-box fuzzing

```text
Initial corpus
		|
		v
Chọn seed và mutate
		|
		v
Chạy analyzer + coverage.py
		|
		+-- Có dòng mới? --> Giữ input vào corpus
		|
		+-- Exception? ----> Lưu finding
		|
		v
Lặp lại đến đủ số input
```

White-box fuzzer đo các dòng đã chạy trong thư mục `analyzer/`. Input tạo ra coverage mới sẽ được thêm vào corpus để làm seed cho các vòng sau.

## 4. Cấu trúc thư mục

```text
ATPM/
├── analyzer/
│   ├── parser.py              # Đọc và chuyển đổi JSON/CSV
│   ├── validator.py           # Kiểm tra luật nghiệp vụ
│   └── product_analyzer.py    # Điều phối và tính toán
├── fuzzing/
│   ├── generators.py          # Sinh input và seed corpus
│   ├── mutations.py           # Biến đổi input
│   ├── blackbox_fuzzer.py     # Black-box executor và oracle
│   ├── whitebox_fuzzer.py     # Coverage-guided fuzzer
│   ├── memory_model.py        # Mô phỏng các tình huống bộ nhớ bằng Python
│   └── memory_fuzzer.py       # Fuzzer cho memory model và báo cáo CWE
├── tests/                     # Test normal, boundary, regression
├── corpus/                    # Seed input hợp lệ và không hợp lệ
├── crashes/                   # Finding do fuzzer lưu lại
├── reports/                   # CSV, JSON và biểu đồ
├── BAO_CAO_TIEN_DO.md         # Báo cáo tiến độ thực hiện đề tài
├── app.py                     # Giao diện desktop để demo và xem kết quả
├── main.py                    # Menu demo tương tác
├── experiment.py              # Chạy thực nghiệm tự động
├── reporting.py               # Đọc kết quả và tạo biểu đồ
├── reproduce_crash.py         # Chạy lại finding đã lưu
├── requirements.txt           # Dependency Python
├── REPORT.md                  # Khung báo cáo đồ án
└── SLIDES.md                  # Nội dung slide thuyết trình
```

## 5. Cài đặt trên Windows

Mở PowerShell tại thư mục project:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Nếu PowerShell chặn chạy script kích hoạt, chỉ cho phép trong cửa sổ PowerShell hiện tại rồi kích hoạt lại:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

Kết quả mong đợi là Python 3.12 trở lên và các package `pytest`, `coverage`, `hypothesis`, `matplotlib` được cài trong virtual environment.

Giao diện desktop dùng Tkinter có sẵn trong bộ cài Python trên Windows. Mô hình bộ nhớ đã được chuyển hoàn toàn sang Python nên không cần cài C compiler.

Có thể dùng trực tiếp interpreter trong môi trường ảo nếu chưa activate:

```powershell
.venv\Scripts\python.exe --version
```

## 6. Chạy test thông thường

```powershell
.venv\Scripts\python.exe -m pytest
```

Các test hiện có gồm:

- `test_normal.py`: sản phẩm hợp lệ và JSON sai cú pháp.
- `test_boundary.py`: giá trị biên của price, stock, discount, rating và name.
- `test_regression.py`: sai kiểu dữ liệu và đọc CSV.
- `test_python_memory_model.py`: kết quả mô phỏng các tình huống CWE và input record sai.
- `test_memory_fuzzer.py`: các ca sinh, thống kê CWE và file CSV của memory-model fuzzer.

Đo coverage của test suite:

```powershell
.venv\Scripts\python.exe -m coverage run -m pytest
.venv\Scripts\python.exe -m coverage report
.venv\Scripts\python.exe -m coverage html
```

Sau đó mở `htmlcov/index.html` để xem báo cáo chi tiết.

## 7. Chạy chương trình demo

```powershell
.venv\Scripts\python.exe main.py
```

Menu gồm:

1. **Run Normal Analysis**: nhập JSON và xem kết quả analyzer.
2. **Run Black-box Fuzzing**: chạy black-box với 100 input.
3. **Run White-box Fuzzing**: chạy white-box với 100 input.
4. **Generate Charts**: tạo biểu đồ từ các CSV đã có.
5. **Show Crash Results**: liệt kê các file finding trong `crashes/`.
6. **Generate Report**: chạy experiment 1.000 input và tạo summary/chart.
7. **Run Memory Model Fuzzing**: chạy 100 ca mô phỏng bộ nhớ bằng Python.
8. **Exit**: thoát chương trình.

### Giao diện mô phỏng

Chạy giao diện desktop để trình bày trực quan:

```powershell
.venv\Scripts\python.exe app.py
```

Giao diện có ba màn hình:

1. **Phân tích sản phẩm**: sửa JSON, bấm **Phân tích** để xem `valid`, phép tính, errors và warnings. Bấm **Nạp ví dụ** để khôi phục sản phẩm mẫu.
2. **Phòng thí nghiệm fuzzing**: chọn số input từ 1 đến 10.000, rồi chạy riêng Black-box, White-box, Memory Model hoặc **Chạy toàn bộ**.
3. **Kết quả & biểu đồ**: chọn CSV để xem các dòng kết quả, bấm **Tạo biểu đồ** để cập nhật chart rồi chọn tên chart để xem trước.

Các tác vụ fuzzing chạy nền để cửa sổ vẫn phản hồi. Bắt đầu với 100 input để demo nhanh; dùng 1.000 hoặc 10.000 khi chạy thực nghiệm chính thức.

## 8. Chạy fuzzing bằng command line

Chạy experiment gồm cả hai phương pháp:

```powershell
.venv\Scripts\python.exe -m experiment --count 100
.venv\Scripts\python.exe -m experiment --count 1000
.venv\Scripts\python.exe -m experiment --count 10000
```

Tham số `--count` là số input cho mỗi fuzzer. Số liệu không được viết thủ công; chương trình lấy trực tiếp từ lần chạy và ghi vào các file report.

Experiment chạy cả ba bộ thử nghiệm với cùng `--count`. Các kết quả được ghi vào:

- `reports/blackbox_results.csv`: từng iteration, loại input, kết quả, lỗi và thời gian.
- `reports/whitebox_results.csv`: từng iteration, kết quả và số coverage point.
- `reports/memory_results.csv`: từng ca mô hình bộ nhớ Python, kết quả mô phỏng, CWE và CVE (để trống nếu chưa có CVE xác minh).
- `reports/summary.json`: thống kê tổng hợp của lần experiment gần nhất.
- `reports/charts/input_results.png`: phân bố kết quả black-box.
- `reports/charts/whitebox_coverage.png`: diễn biến coverage của white-box.
- `reports/charts/memory_cwe_classifications.png`: số phân loại CWE, gồm cả trường hợp bị chặn, nếu có report memory model.

Chạy riêng memory model fuzzer bằng Python:

```powershell
.venv\Scripts\python.exe -c "from fuzzing.memory_fuzzer import MemoryModelFuzzer; print(MemoryModelFuzzer().run(100))"
```

Trong `summary.json`, kết quả được phân theo các khóa `blackbox`, `whitebox`, `memory_model` và `input_count`. Mỗi lần chạy sẽ cập nhật các file report tương ứng; hãy giữ lại hoặc sao chép kết quả nếu cần so sánh nhiều lần thực nghiệm.

## 9. Tái hiện finding

Khi fuzzer lưu một finding dạng JSON, chạy:

```powershell
.venv\Scripts\python.exe reproduce_crash.py crashes\blackbox\crash_001.json
```

Chương trình đọc lại field `input`, gửi input vào analyzer và in ra kết quả hiện tại cùng thông tin đã lưu trong finding.

## 10. Ý nghĩa black-box và white-box

| Tiêu chí | Black-box | White-box |
|---|---|---|
| Biết source code | Không | Có |
| Coverage feedback | Không | Có |
| Cách chọn input | Random, seed, mutation | Mutation có coverage feedback |
| Triển khai | Đơn giản | Phức tạp hơn |
| Tìm nhánh sâu | Có thể khó | Có khả năng tốt hơn |
| Output chính | CSV, finding, thống kê | CSV, coverage, finding |

Black-box phù hợp khi chỉ có executable hoặc API. White-box phù hợp khi có source code và muốn tối ưu input để tiếp cận nhiều nhánh xử lý hơn. Trong thực tế nên kết hợp cả hai phương pháp.

## 11. Lưu ý về kết quả

Các số liệu trong báo cáo phải lấy sau khi chạy experiment thực tế từ `reports/summary.json` và các CSV tương ứng. Không sử dụng các con số minh họa trong tài liệu như kết quả chính thức.

Các input bất thường chỉ phục vụ kiểm thử cục bộ. Project không cố tình tạo lỗ hổng khai thác thật; exception và finding được ghi nhận để phục vụ phân tích lỗi.

## 12. Phân loại CWE và CVE

| Tình huống mô phỏng | Kết quả | CWE |
|---|---|---|
| Tên vượt sức chứa buffer stack, bị chặn trước khi copy | BLOCKED | CWE-121 |
| Nhân kích thước cấp phát vượt giới hạn số nguyên | BLOCKED | CWE-190 |
| Cấp phát không được giải phóng khi kết thúc scope | DETECTED | CWE-401 |
| Giải phóng cùng một vùng nhớ hai lần | DETECTED | CWE-415 |
| Truy cập vùng nhớ sau khi giải phóng | DETECTED | CWE-416 |
| Thiếu con trỏ bắt buộc, bị chặn trước dereference | BLOCKED | CWE-476 |
| Yêu cầu cấp phát vượt ngưỡng cấu hình | BLOCKED | CWE-789 |

`BLOCKED` nghĩa là input mô phỏng một điều kiện nguy hiểm nhưng guard đã ngăn hành vi; `DETECTED` nghĩa là mô hình ownership phát hiện trạng thái lỗi. Không diễn giải các kết quả này thành CVE của sản phẩm thật.

## 13. Hướng phát triển

- Bổ sung branch coverage và path coverage chi tiết.
- Thêm Hypothesis cho property-based testing.
- Fuzz REST API và dữ liệu database.
- Tích hợp AFL++ hoặc libFuzzer cho native program.
- Chạy fuzzing trong CI/CD hoặc Docker.
- Xây dựng dashboard theo dõi coverage và finding.

## 14. Báo cáo tiến độ

Xem [BAO_CAO_TIEN_DO.md](BAO_CAO_TIEN_DO.md) để theo dõi phần đã hoàn thành, minh chứng test, phần đang thực hiện, kế hoạch tiếp theo và kịch bản trình bày với giảng viên.

## 15. Xử lý lỗi thường gặp

- **Không kích hoạt được `.venv` trong PowerShell**: chạy `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`, hoặc không kích hoạt và dùng trực tiếp `.venv\Scripts\python.exe`.
- **Báo `No module named pytest` hoặc `coverage`**: kiểm tra đã kích hoạt `.venv`, sau đó chạy `python -m pip install -r requirements.txt`.
- **Không thấy biểu đồ hoặc bảng kết quả trống**: chạy một fuzzer hoặc experiment trước; biểu đồ chỉ được tạo từ các CSV đã có.
- **Không mở được cửa sổ giao diện**: chạy `python -c "import tkinter; print('Tkinter OK')"`. Nếu import thất bại, cài/repair Python trên Windows và bật thành phần Tcl/Tk.
- **Muốn chạy test không phụ thuộc lệnh kích hoạt**: dùng `.venv\Scripts\python.exe -m pytest` từ thư mục dự án.
