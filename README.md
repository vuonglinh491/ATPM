# Product Analyzer Fuzz Testing

## Mô tả dự án

Product Analyzer Fuzz Testing là đồ án mô phỏng quy trình kiểm thử độ tin cậy và an toàn của một thành phần xử lý dữ liệu sản phẩm thương mại điện tử. Chương trình nhận sản phẩm ở định dạng JSON hoặc CSV, xác thực trường dữ liệu và kiểu, kiểm tra các giới hạn nghiệp vụ, sau đó tính giá sau giảm, giá trị tồn kho và phân hạng sản phẩm.

Dự án kết hợp **black-box fuzzing** để kiểm tra ranh giới ngoài biên và vùng xác định (**Bounded Region**), **white-box fuzzing** có định hướng để **đào sâu các nhánh logic nội bộ bên trong vùng Bounded**, và một mô hình bộ nhớ viết hoàn toàn bằng Python để mô phỏng rủi ro về giới hạn buffer, kiểu dữ liệu, cấp phát và vòng đời bộ nhớ. Kết quả được lưu thành báo cáo CSV, JSON và biểu đồ trực quan để có thể xem lại input, trạng thái xử lý và phân loại CWE.

Mục tiêu là giúp thử nghiệm có hệ thống với dữ liệu hợp lệ, dữ liệu biên và dữ liệu bất thường; so sánh hai phương pháp fuzzing chính; đồng thời thực hành nhận diện các lớp điểm yếu bộ nhớ. Mô hình bộ nhớ chỉ mô phỏng và phân loại trạng thái nguy hiểm, không truy cập hay làm hỏng bộ nhớ thật. CWE là nhãn phân loại, không khẳng định sản phẩm có lỗ hổng hay CVE đã được cấp.

Dự án có hai phương pháp fuzzing chính cho Product Analyzer và một mô hình bộ nhớ bổ trợ:

- **Black-box fuzzing**: fuzzer coi hệ thống như hộp đen, áp dụng phân tích giá trị biên (Boundary Value Analysis - BVA) để kiểm tra xem hệ thống có bảo vệ và từ chối đúng các giá trị nằm ngoài vùng Bounded hay không.
- **White-box fuzzing**: fuzzer biết mã nguồn, ưu tiên sinh dữ liệu hợp lệ trong vùng Bounded và dùng `coverage.py` để giữ lại input làm tăng số dòng mã analyzer được thực thi. Đây là phản hồi theo độ phủ dòng, không phải đo độ phủ nhánh hay phân tích luồng dữ liệu.
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

Kết quả mong đợi: toàn bộ **46 tests** kết thúc thành công và cửa sổ **Product Analyzer | Fuzz Lab** mở ra. Có thể bỏ qua bước kích hoạt môi trường và gọi trực tiếp `.venv\Scripts\python.exe` như các ví dụ bên dưới.

## 1. Chức năng chính

### 1.1. Từ điển dữ liệu & Đặc tả nạp Record (Data Dictionary & Schema)

Hệ thống quản lý bản ghi sản phẩm chuẩn thông qua đặc tả tường minh tại `analyzer/schema.py`:

| Trường (Field) | Bắt buộc | Kiểu dữ liệu | Giới hạn kích cỡ / Vùng Bounded | Ý nghĩa nghiệp vụ |
| :--- | :---: | :--- | :--- | :--- |
| `id` | Có | `string` | Không được rỗng hoặc chỉ có khoảng trắng | Mã định danh sản phẩm |
| `name` | Có | `string` | Không rỗng; tối đa 100 ký tự | Tên thương mại của sản phẩm |
| `category` | Có | `string` | Phải là chuỗi; hiện chưa áp dụng giới hạn độ dài hoặc cấm chuỗi rỗng | Danh mục ngành hàng |
| `price` | Có | `float` / `int` | Không âm; cảnh báo nếu $> 10^{12}$ | Đơn giá niêm yết |
| `stock` | Có | `int` | Không âm; cảnh báo nếu $> 1.000.000$ | Số lượng sản phẩm tồn kho |
| `discount` | Có | `float` / `int` | $0.0 \le \text{discount} \le 100.0$ (%) | Tỷ lệ chiết khấu giảm giá |
| `rating` | Có | `float` / `int` | $0.0 \le \text{rating} \le 5.0$ (sao) | Điểm đánh giá chất lượng trung bình |
| `description` | Không | `string` / `null` | Tối đa 1.000 ký tự; dài hơn chỉ tạo cảnh báo | Thông tin mô tả chi tiết tính năng |

Các giới hạn tối đa của `price` và `stock` là ngưỡng cảnh báo, không làm bản ghi mất tính hợp lệ. Schema trong `analyzer/schema.py` mô tả từ điển dữ liệu; quy tắc thực thi hiện tại nằm trong `analyzer/validator.py`.

### 1.2. Đường ống xử lý bản ghi & Logic sâu trong vùng Bounded

Một Record được nạp và phân tích qua 3 tầng:

1. **Tầng 1 - Parser:** Đọc JSON hoặc CSV một sản phẩm. JSON phải là object; CSV phải có đúng một dòng dữ liệu. Lỗi cú pháp/định dạng được chuyển thành `InputParseError` và trả về như lỗi phân tích.
2. **Tầng 2 - Validator:** Kiểm tra trường bắt buộc, kiểu dữ liệu, các giới hạn được thực thi và các ngưỡng cảnh báo như trong bảng. Lỗi validation được ghi vào `errors` và đánh dấu `valid = False`; cảnh báo không làm bản ghi mất tính hợp lệ.
3. **Tầng 3 - Calculator (Đào sâu bên trong vùng Bounded):** Khi bản ghi hợp lệ (`errors` rỗng):
   - **Tính toán tài chính & làm tròn tiền tệ:**
     - Giá sau giảm: $\text{final\_price} = \text{round}(price \times (1 - \frac{discount}{100}), 2)$ (tránh sai số làm tròn số thực Floating-point).
     - Giá trị tồn kho: $\text{inventory\_value} = price \times stock$.
   - **Nhánh tương tác đa biến (Inter-field constraints):**
     - Cảnh báo sản phẩm hết hàng nhưng vẫn cài đặt giảm giá ($stock = 0 \land discount > 0$).
     - Cảnh báo sắp hết hàng ($0 < stock \le 5$).
   - **Nhánh chính sách ngành hàng:**
     - Đồ điện tử giá cao ($price \ge 10.000.000$) giảm giá $> 20\%$ phải yêu cầu phê duyệt quản lý.
     - Sách (`category == "Book"`) không được vượt trần chiết khấu của nhà xuất bản ($discount > 50\%$).
     - Cảnh báo sản phẩm ngành `Camera` nên kèm thông tin bảo hành.
   - **Nhánh giảm giá 100%:** Cảnh báo sản phẩm tặng kèm miễn phí ($0$ đồng).
   - **Nhánh phân hạng sản phẩm (`badge`):** Phân loại `BEST_SELLER` ($rating \ge 4.5 \land stock > 10$), `UNDER_REVIEW` ($rating < 2.0$), hoặc `STANDARD`.

### 1.3. Fuzzing: Black-box vs White-box

- **Black-box Fuzzing (Kiểm tra vùng Bounded):** Bộ sinh `generate_boundary_blackbox` tạo các input nhắm trực tiếp vào các ranh giới biên theo BVA:
  - Cận âm: $price = -1$, $stock = -1$, $discount = -0.01$, $rating = -0.1$.
  - Cận trần: $discount = 100.01$, $rating = 5.1$, $name$ dài 101 ký tự.
  - Chuỗi rỗng, khoảng trắng, sai kiểu (`None`, `bool`, `list`), JSON hỏng cú pháp.
  - Oracle phân loại: `VALID`, `INVALID`, `EXCEPTION`, `TIMEOUT`, `INVALID_OUTPUT` và `LOGIC_BUG`. Ngoại lệ được ghi nhận là `EXCEPTION`, không phải crash của tiến trình.
- **White-box Fuzzing (Đào sâu bên trong vùng Bounded):** Bộ sinh nhắm đến các bản ghi hợp lệ và các tổ hợp nghiệp vụ trong analyzer. Sau mỗi lần chạy, fuzzer giữ input làm tăng tập hợp dòng mã analyzer đã quan sát vào corpus trong bộ nhớ. Một số seed/mutation vẫn có thể không hợp lệ.
- Chỉ số `coverage_points` là số dòng mã analyzer duy nhất được ghi nhận bởi cơ chế feedback của fuzzer; không phải phần trăm line/branch coverage của toàn dự án.
- **Memory-model Fuzzing:** Mô phỏng an toàn các tình huống bộ nhớ mức thấp (CWE-121, CWE-190, CWE-401, CWE-415, CWE-416, CWE-476, CWE-789).

## 2. Ví dụ input và output

Input JSON hợp lệ trong vùng Bounded:

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
  "badge": "BEST_SELLER",
  "errors": [],
  "warnings": [
    "Camera products should include a warranty description"
  ]
}
```

Khi input không hợp lệ (ngoài biên), `valid` là `false`, các phép tính trả về `null` và nguyên nhân được ghi trong mảng `errors`.

## 3. Luồng hoạt động

### 3.1. Luồng phân tích sản phẩm

```text
Input Raw (JSON/CSV)
        |
        v
    [Tầng 1] Parser (Kiểm tra cú pháp & ép kiểu)
        |
        v
    [Tầng 2] Validator (Kiểm tra kiểu dữ liệu & Vùng Bounded)
        |
        +-- Ngoài biên / Sai kiểu --> Output errors (valid: false)
        |
        v (Trong vùng Bounded)
    [Tầng 3] Calculator & Business Rules
        |
        +-- Inter-field interactions (stock=0 & discount>0, low stock)
        +-- Category policies (Electronics >20%, Book >50%, Camera warranty)
        +-- Badge classification (BEST_SELLER, UNDER_REVIEW, STANDARD)
        +-- Precision rounding (final_price)
        |
        v
Output valid: true, derived values, badge, warnings
```

### 3.2. Luồng Black-box Fuzzing (Boundary Checking)

```text
Boundary Value Generator (BVA) / Mutation
                 |
                 v
    Product Analyzer như hộp đen
                 |
                 v
  Oracle: Phân loại output và lỗi quan sát được
  (VALID / INVALID / EXCEPTION / TIMEOUT / INVALID_OUTPUT / LOGIC_BUG)
                 |
                 v
    CSV report + crash/finding files
```

### 3.3. Luồng White-box Fuzzing (Inside-Bounded Refinement)

```text
Bounded Input Generator (Targeted) + Corpus
                 |
                 v
    Chạy analyzer + Đo độ phủ coverage.py
                 |
                 +-- Thực thi dòng analyzer mới? --> Giữ seed vào Corpus
                 |
                 +-- Exception/Crash? -----------> Lưu finding
                 |
                 v
    Lặp lại và ghi nhận các dòng analyzer mới
```

## 4. Cấu trúc thư mục

```text
ATPM/
├── analyzer/
│   ├── schema.py              # Đặc tả Data Dictionary và giới hạn vùng Bounded
│   ├── parser.py              # Đọc và chuyển đổi cú pháp JSON/CSV
│   ├── validator.py           # Kiểm tra kiểu và quy tắc biên sơ cấp
│   └── product_analyzer.py    # Điều phối, tính toán và các nhánh nghiệp vụ sâu
├── fuzzing/
│   ├── generators.py          # Bộ sinh test biên (BVA) và test sâu trong Bounded
│   ├── mutations.py           # Biến đổi đột biến input
│   ├── blackbox_fuzzer.py     # Black-box executor và oracle
│   ├── whitebox_fuzzer.py     # Coverage-guided fuzzer đào sâu vùng Bounded
│   ├── memory_model.py        # Mô phỏng các tình huống bộ nhớ bằng Python
│   └── memory_fuzzer.py       # Fuzzer cho memory model và báo cáo CWE
├── tests/
│   ├── test_normal.py         # Test sản phẩm hợp lệ và JSON sai cú pháp
│   ├── test_boundary.py       # Test các giá trị biên ngoài (BVA)
│   ├── test_data_dictionary.py # Test tính đầy đủ của Data Dictionary và Schema
│   ├── test_bounded_whitebox.py # Test các nhánh nghiệp vụ sâu bên trong vùng Bounded
│   ├── test_regression.py     # Test hồi quy sai kiểu và đọc CSV
│   ├── test_python_memory_model.py # Test kết quả mô phỏng CWE
│   └── test_memory_fuzzer.py   # Test memory-model fuzzer
├── crashes/                   # Finding do fuzzer lưu lại
├── reports/                   # CSV, JSON và biểu đồ
├── app.py                     # Giao diện desktop để demo và xem kết quả
├── main.py                    # Menu demo tương tác
├── experiment.py              # Chạy thực nghiệm tự động
├── reporting.py               # Đọc kết quả và tạo biểu đồ
├── reproduce_crash.py         # Chạy lại finding đã lưu
├── requirements.txt           # Dependency Python
├── REPORT.md                  # Khung báo cáo đồ án chi tiết
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

Mã nguồn yêu cầu Python 3.10 trở lên. Các package `pytest`, `coverage`, `hypothesis` và `matplotlib` được cài trong virtual environment. Không cần cài C/C++ compiler; memory model là mô phỏng bằng Python, không thao tác bộ nhớ native.

## 6. Chạy test thông thường

Chạy toàn bộ **46 test cases**:

```powershell
.venv\Scripts\python.exe -m pytest
```

Đo code coverage của toàn bộ test suite:

```powershell
.venv\Scripts\python.exe -m coverage run -m pytest
.venv\Scripts\python.exe -m coverage report
.venv\Scripts\python.exe -m coverage html
```

Sau đó mở `htmlcov/index.html` trên trình duyệt để xem chi tiết từng dòng mã được bao phủ.

## 7. Chạy chương trình demo

### Menu dòng lệnh (CLI):

```powershell
.venv\Scripts\python.exe main.py
```

### Giao diện đồ họa (GUI Desktop):

```powershell
.venv\Scripts\python.exe app.py
```

Giao diện gồm ba tab trực quan:
1. **Phân tích sản phẩm**: Nhập/sửa JSON, bấm **Phân tích** để xem kết quả hợp lệ, tính toán tài chính, badge và cảnh báo.
2. **Phòng thí nghiệm fuzzing**: Chọn số lượng input (100, 1000, 10000), chạy riêng Black-box, White-box, Memory Model hoặc **Chạy toàn bộ**.
3. **Kết quả & biểu đồ**: Xem bảng dữ liệu CSV và xem trước các biểu đồ trực quan.

## 8. Chạy thực nghiệm tự động

Chạy experiment gồm cả ba bộ thử nghiệm để tự động xuất CSV và biểu đồ:

```powershell
.venv\Scripts\python.exe -m experiment --count 100
.venv\Scripts\python.exe -m experiment --count 1000
.venv\Scripts\python.exe -m experiment --count 10000
```

Các đầu ra cập nhật tại `reports/`:
- `reports/blackbox_results.csv`: Kết quả phân loại từng input ngoài/trong biên.
- `reports/whitebox_results.csv`: Sự gia tăng điểm độ phủ (`coverage_points`) theo thời gian.
- `reports/memory_results.csv`: Kết quả mô phỏng các ca CWE.
- `reports/summary.json`: Thống kê tổng hợp số lượng.
- `reports/charts/`: Các biểu đồ PNG tương ứng.

## 9. So sánh chuyên sâu: Black-box vs White-box

| Tiêu chí so sánh | Black-box Testing / Fuzzing | White-box Testing / Fuzzing |
| :--- | :--- | :--- |
| **Mục tiêu chính** | Kiểm tra **vùng Bounded** (ranh giới ngoài biên và lọc dữ liệu rác) | Đào sâu **bên trong vùng Bounded** (khi dữ liệu đã hợp lệ về biên) |
| **Kiến thức về hệ thống** | Dựa vào đặc tả và quan sát input/output | Có mã nguồn; đo các dòng analyzer được thực thi bằng `coverage.py` |
| **Kỹ thuật sinh dữ liệu** | BVA, input sai kiểu/thiếu trường và mutation | Sinh input hướng đến vùng Bounded, mutation và giữ seed khi có dòng thực thi mới |
| **Phản hồi (Feedback)** | Phân loại `VALID`, `INVALID`, `EXCEPTION`, `TIMEOUT`, `INVALID_OUTPUT` hoặc `LOGIC_BUG` | Số dòng mã analyzer mới được quan sát (`coverage_points`); không phải coverage nhánh |
| **Trọng tâm kiểm thử** | Nhập sai kiểu, chuỗi rỗng, số âm, vượt ngưỡng nghiệp vụ, JSON sai cú pháp | Tổ hợp nghiệp vụ, tính toán giá và các nhánh cảnh báo; fuzzer ghi nhận exception nhưng không tự xác minh tính đúng đắn nghiệp vụ |

## 10. Phân loại CWE trong mô hình bộ nhớ

| Tình huống mô phỏng | Kết quả | CWE |
|---|---|---|
| Cú pháp, kiểu dữ liệu hoặc thao tác không hợp lệ bị từ chối | BLOCKED | CWE-20 |
| Tên vượt sức chứa buffer stack, bị chặn trước khi copy | BLOCKED | CWE-121 |
| Nhân kích thước cấp phát vượt giới hạn số nguyên | BLOCKED | CWE-190 |
| Cấp phát không được giải phóng khi kết thúc scope | DETECTED | CWE-401 |
| Giải phóng cùng một vùng nhớ hai lần | DETECTED | CWE-415 |
| Truy cập vùng nhớ sau khi giải phóng | DETECTED | CWE-416 |
| Thiếu con trỏ bắt buộc, bị chặn trước dereference | BLOCKED | CWE-476 |
| Yêu cầu cấp phát vượt ngưỡng cấu hình | BLOCKED | CWE-789 |

`BLOCKED` nghĩa là input mô phỏng một điều kiện nguy hiểm nhưng guard đã ngăn hành vi; `DETECTED` nghĩa là mô hình ownership phát hiện trạng thái lỗi. Không diễn giải các kết quả này thành CVE của sản phẩm thật.

## 11. Tài liệu kèm theo

- [REPORT.md](REPORT.md): Nội dung báo cáo đồ án gồm 7 chương.
- [HUONG_DAN_BAO_CAO_DEMO.md](HUONG_DAN_BAO_CAO_DEMO.md): Hướng dẫn từng bước chuẩn bị demo, thuyết trình và bảo vệ trước giảng viên.
- [SLIDES.md](SLIDES.md): Dàn ý slide thuyết trình báo cáo.
