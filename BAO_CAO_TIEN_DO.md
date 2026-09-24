

---

## 1. Tổng quan đề tài

Đề tài xây dựng một hệ thống mô phỏng kiểm thử fuzzing cho bộ phân tích sản phẩm trong thương mại điện tử. Hệ thống nhận dữ liệu sản phẩm ở dạng JSON hoặc CSV, kiểm tra dữ liệu theo các luật nghiệp vụ, tính toán các giá trị dẫn xuất và trả về kết quả phân tích.

Hai phương pháp fuzzing được triển khai và so sánh:

- **Black-box fuzzing:** chỉ quan sát input, output, exception và timeout của chương trình.
- **White-box fuzzing:** sử dụng thông tin mã nguồn và coverage feedback để lựa chọn input có khả năng đi qua các dòng xử lý mới.

Mục tiêu của đề tài là phát hiện các input bất thường, ghi nhận finding có thể tái hiện, đo độ bao phủ và đánh giá ưu nhược điểm của hai phương pháp.

## 2. Mục tiêu thực hiện

1. Xây dựng Product Analyzer xử lý được JSON và CSV.
2. Kiểm tra các field bắt buộc, kiểu dữ liệu và giới hạn nghiệp vụ.
3. Tính giá sau giảm, giá trị tồn kho và rating trung bình.
4. Xây dựng bộ test thông thường, test biên và test hồi quy.
5. Xây dựng black-box fuzzer có generator, mutation, timeout và lưu finding.
6. Xây dựng white-box fuzzer có coverage feedback và corpus mở rộng tự động.
7. Sinh báo cáo CSV, summary JSON và biểu đồ kết quả.
8. So sánh hiệu quả của black-box và white-box trên cùng quy mô input.

## 3. Tiến độ đã hoàn thành

### 3.1. Product Analyzer

- Đã triển khai parser cho JSON và CSV.
- Đã triển khai validation cho các field `id`, `name`, `category`, `price`, `stock`, `discount`, `rating` và `description`.
- Đã xử lý các trường hợp sai cú pháp, thiếu field, sai kiểu dữ liệu và giá trị ngoài giới hạn.
- Đã triển khai phép tính giá sau giảm, giá trị tồn kho và rating trung bình.
- Đã bổ sung cảnh báo cho một số trường hợp nghiệp vụ như sản phẩm thuộc category `Camera` hoặc thiếu description.

### 3.2. Bộ kiểm thử

Bộ test hiện có bao gồm:

- Test thông thường cho sản phẩm hợp lệ và JSON sai cú pháp.
- Test biên cho `price`, `stock`, `discount`, `rating` và độ dài `name`.
- Test hồi quy cho sai kiểu dữ liệu và đọc CSV.

**Kết quả kiểm tra gần nhất:** `10 passed`.

Lệnh đã sử dụng:

```powershell
.venv\Scripts\python.exe -m pytest
```

### 3.3. Black-box fuzzing

- Đã xây dựng generator tạo nhiều nhóm input bất thường.
- Đã bổ sung seed và mutation để tạo biến thể từ input ban đầu.
- Đã phân loại kết quả thành `VALID`, `INVALID`, `EXCEPTION`, `TIMEOUT`, `INVALID_OUTPUT` và `LOGIC_BUG`.
- Đã có cơ chế fingerprint để hạn chế lưu trùng finding.
- Đã lưu kết quả theo từng iteration vào `reports/blackbox_results.csv` và finding vào thư mục `crashes/blackbox/`.

### 3.4. White-box fuzzing

- Đã tích hợp đo coverage bằng `coverage.py`.
- Đã xây dựng cơ chế giữ input khi input tạo ra coverage mới.
- Đã lưu kết quả theo iteration vào `reports/whitebox_results.csv`.
- Đã lưu exception/finding để phục vụ tái hiện và phân tích.

### 3.5. Báo cáo và công cụ hỗ trợ

- Đã có chương trình chạy thực nghiệm tự động bằng `experiment.py`.
- Đã có chương trình demo tương tác bằng `main.py`.
- Đã có công cụ tái hiện finding bằng `reproduce_crash.py`.
- Đã có chức năng sinh biểu đồ và file tổng hợp kết quả.
- Đã hoàn thiện README hướng dẫn cài đặt, chạy test, chạy fuzzing và tái hiện finding.

## 4. Minh chứng hiện tại

| Hạng mục | Trạng thái | Minh chứng |
|---|---|---|
| Product Analyzer | Hoàn thành | `analyzer/` |
| Parser JSON/CSV | Hoàn thành | `analyzer/parser.py` |
| Validation nghiệp vụ | Hoàn thành | `analyzer/validator.py` |
| Tính toán kết quả | Hoàn thành | `analyzer/product_analyzer.py` |
| Test suite | Hoàn thành bước cơ bản | `10 passed` |
| Black-box fuzzer | Hoàn thành bước triển khai | `fuzzing/blackbox_fuzzer.py` |
| White-box fuzzer | Hoàn thành bước triển khai | `fuzzing/whitebox_fuzzer.py` |
| Báo cáo CSV/JSON | Đã triển khai | `reports/` |
| So sánh thực nghiệm | Đang cập nhật số liệu | Chạy `experiment.py` |
| Hoàn thiện báo cáo và slide | Đang thực hiện | `REPORT.md`, `SLIDES.md` |

## 5. Phần đang thực hiện

1. Chạy thực nghiệm ở các quy mô 100, 1.000 và 10.000 input cho mỗi fuzzer.
2. Kiểm tra lại các finding được lưu trong `crashes/` và phân biệt lỗi thật với input bị từ chối hợp lệ.
3. Tổng hợp số lượng input, exception, finding duy nhất, coverage và thời gian chạy.
4. Hoàn thiện biểu đồ so sánh black-box và white-box.
5. Bổ sung số liệu thực tế vào `REPORT.md` và các slide trình bày.
6. Rà soát lại tài liệu, kịch bản demo và phần kết luận.

## 6. Bảng số liệu cần cập nhật

Các số liệu dưới đây phải được lấy trực tiếp sau khi chạy experiment gần nhất. Không sử dụng số liệu minh họa.

| Chỉ số | Black-box | White-box |
|---|---:|---:|
| Số input đã chạy | cập nhật từ `summary.json` | cập nhật từ `summary.json` |
| Số input hợp lệ | cập nhật từ report | cập nhật từ report |
| Số input không hợp lệ | cập nhật từ report | cập nhật từ report |
| Exception/timeout | cập nhật từ report | cập nhật từ report |
| Finding duy nhất | cập nhật từ report | cập nhật từ report |
| Coverage | cập nhật từ coverage report | cập nhật từ coverage feedback |
| Thời gian chạy | cập nhật sau experiment | cập nhật sau experiment |

Lệnh chạy thực nghiệm:

```powershell
.venv\Scripts\python.exe -m experiment --count 1000
```

Sau khi chạy, kiểm tra các file `reports/summary.json`, `reports/blackbox_results.csv`, `reports/whitebox_results.csv` và thư mục `reports/charts/`.

## 7. Kế hoạch giai đoạn tiếp theo

| Giai đoạn | Công việc | Kết quả cần đạt |
|---|---|---|
| Giai đoạn 1 | Chạy lại experiment và lưu số liệu | Có bộ số liệu thực tế, nhất quán |
| Giai đoạn 2 | Phân tích finding và coverage | Xác định lỗi, nhánh và input đáng chú ý |
| Giai đoạn 3 | Hoàn thiện báo cáo, bảng và biểu đồ | Có bản báo cáo hoàn chỉnh |
| Giai đoạn 4 | Hoàn thiện slide và luyện demo | Trình bày được luồng hệ thống và kết quả |

## 8. Khó khăn và hướng xử lý

- **Khó khăn:** input fuzzing có nhiều dạng nên một số kết quả có thể là lỗi đầu vào hợp lệ bị từ chối, chưa chắc là lỗi của analyzer.  
  **Hướng xử lý:** dùng oracle, fingerprint và tái hiện finding để phân loại.

- **Khó khăn:** kết quả coverage phụ thuộc seed, mutation và số lượng iteration.  
  **Hướng xử lý:** cố định cách chạy, ghi lại command và chỉ so sánh các lần chạy cùng quy mô.

- **Khó khăn:** số liệu trong báo cáo dễ bị sai nếu nhập thủ công.  
  **Hướng xử lý:** lấy số liệu trực tiếp từ `summary.json` và các CSV sau mỗi lần chạy.

- **Khó khăn:** cần chứng minh finding có thể tái hiện.  
  **Hướng xử lý:** dùng `reproduce_crash.py` để chạy lại input và lưu kết quả đối chiếu.

## 9. Kịch bản trình bày với giảng viên

1. Giới thiệu bài toán phân tích dữ liệu sản phẩm và lý do cần fuzzing.
2. Trình bày kiến trúc `parser -> validator -> calculator -> output`.
3. Chạy một input hợp lệ và một input sai để minh họa analyzer.
4. Giải thích sự khác nhau giữa black-box và white-box fuzzing.
5. Chạy hoặc mở kết quả của hai fuzzer.
6. Trình bày CSV, finding, coverage và biểu đồ được sinh ra.
7. So sánh hai phương pháp theo coverage, finding, thời gian và độ phức tạp triển khai.
8. Nêu phần đã hoàn thành, phần đang cập nhật và kế hoạch hoàn thiện.

## 10. Kết luận tiến độ

Đề tài đã hoàn thành phần nền tảng gồm Product Analyzer, bộ kiểm thử cơ bản, black-box fuzzer, white-box fuzzer và các công cụ sinh báo cáo. Kết quả kiểm thử hiện tại cho thấy test suite cơ bản đang chạy ổn định với `10 passed`.

Phần trọng tâm cần hoàn thiện tiếp theo là chạy thực nghiệm có kiểm soát, cập nhật số liệu thực tế, phân tích finding và hoàn chỉnh báo cáo so sánh. Sau khi hoàn tất các bước này, dự án có thể dùng để demo đầy đủ từ lúc tạo input, chạy analyzer, ghi nhận finding đến lúc tổng hợp coverage và biểu đồ.

## 11. Ví dụ kiểm thử minh họa

Các ví dụ dưới đây có thể dùng trực tiếp khi trình bày với giảng viên. Kết quả được mô tả theo cấu trúc trả về của `ProductAnalyzer`.

### Ví dụ 1: Sản phẩm hợp lệ

**Input:**

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

**Kết quả mong đợi:**

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

Trường hợp này kiểm tra toàn bộ luồng thành công: parse input, validation và tính toán kết quả. Warning về warranty là cảnh báo nghiệp vụ, không làm sản phẩm trở thành không hợp lệ.

### Ví dụ 2: JSON sai cú pháp

**Input:**

```text
{"id":
```

**Kết quả mong đợi:**

```json
{
  "valid": false,
  "final_price": null,
  "inventory_value": null,
  "average_rating": null,
  "errors": ["Malformed JSON: Expecting value"],
  "warnings": []
}
```

Ví dụ này kiểm tra parser có bắt lỗi cú pháp và trả về kết quả có cấu trúc thay vì làm chương trình bị crash hay không.

### Ví dụ 3: Giá trị biên không hợp lệ

**Input:** sản phẩm có `price = -1`, `stock = -1`, `discount = 101` hoặc `rating = 5.1`.

**Kết quả mong đợi:**

```text
valid = false
errors có thể gồm:
- Price must not be negative
- Stock must not be negative
- Discount must be between 0 and 100
- Rating must be between 0 and 5
```

Trường hợp này kiểm tra các luật giới hạn nghiệp vụ. Khi có lỗi validation, các giá trị tính toán như `final_price` và `inventory_value` phải giữ giá trị `null`.

### Ví dụ 4: Sai kiểu dữ liệu

**Input:**

```json
{
  "id": null,
  "price": [],
  "stock": "x"
}
```

**Kết quả mong đợi:**

```text
valid = false
errors khác rỗng, trong đó có thể gồm:
- Missing field: name
- Missing field: category
- Product ID must not be empty
- Price must be numeric
- Stock must be an integer
```

Ví dụ này mô phỏng input thường gặp từ fuzzer như `null`, list và string sai vị trí. Analyzer phải trả lỗi validation và không phát sinh exception ngoài dự kiến.

### Ví dụ 5: Đọc sản phẩm từ CSV

**Input:**

```csv
id,name,category,price,stock,discount,rating
P1,Phone,Mobile,100,2,0,4
```

**Kết quả mong đợi:**

```text
valid = true
final_price = 100.0
inventory_value = 200
average_rating = 4.0
errors = []
```

Trường hợp này xác nhận parser chuyển các cột số trong CSV sang kiểu dữ liệu phù hợp trước khi chuyển sang bước validation và calculation.

### Ví dụ 6: Thiếu field bắt buộc

**Input:**

```json
{
  "id": "P002",
  "name": "Phone",
  "price": 5000000
}
```

**Kết quả mong đợi:**

```text
valid = false
errors có thể gồm:
- Missing field: category
- Missing field: stock
- Missing field: discount
- Missing field: rating
```

Ví dụ này kiểm tra khả năng phát hiện object không đầy đủ. Hệ thống không thực hiện phép tính khi còn thiếu field bắt buộc.

### Cách chạy kiểm thử

Chạy toàn bộ các test tự động bằng lệnh:

```powershell
.venv\Scripts\python.exe -m pytest
```

Kết quả hiện tại của test suite là `10 passed`. Các ví dụ trên cũng có thể dùng làm input seed cho black-box fuzzer và làm cơ sở để kiểm tra coverage của white-box fuzzer.
