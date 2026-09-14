Tôi đang thực hiện một dự án môn Kiểm thử phần mềm với đề tài:

**“Kiểm thử Fuzzing Black-box và White-box cho bộ phân tích sản phẩm trong hệ thống thương mại điện tử”**

Hãy đóng vai trò là một chuyên gia về Software Testing, Fuzz Testing, Python, C/C++, Black-box Testing, White-box Testing và xây dựng báo cáo đồ án.

Mục tiêu của tôi là xây dựng một project hoàn chỉnh có thể chạy thực tế trên Windows, có mã nguồn, dữ liệu kiểm thử, kết quả thực nghiệm, biểu đồ và báo cáo.

Hãy hướng dẫn tôi theo từng bước, KHÔNG bỏ qua các bước cài đặt, cấu hình, viết code, chạy thử và đánh giá kết quả.

---

# I. MỤC TIÊU DỰ ÁN

Xây dựng một “Product Analyzer” mô phỏng bộ phân tích dữ liệu sản phẩm trong hệ thống thương mại điện tử.

Product Analyzer nhận dữ liệu sản phẩm có dạng JSON/CSV và thực hiện:

1. Đọc dữ liệu sản phẩm.
2. Kiểm tra dữ liệu đầu vào.
3. Phân tích:
   - Product ID
   - Product name
   - Category
   - Price
   - Quantity/Stock
   - Discount
   - Rating
   - Description
4. Kiểm tra các điều kiện nghiệp vụ:
   - Giá không được âm.
   - Stock không được âm.
   - Discount nằm trong khoảng 0–100%.
   - Rating nằm trong khoảng 0–5.
   - Product ID không được rỗng.
   - Product name không được vượt quá giới hạn.
5. Tính toán một số thông tin:
   - Giá sau giảm.
   - Giá trị tồn kho.
   - Điểm đánh giá trung bình.
6. Trả về:
   - Kết quả phân tích.
   - Danh sách lỗi.
   - Warning.
   - Thống kê.

Sau khi xây dựng Product Analyzer, thực hiện hai phương pháp:

### A. Black-box Fuzzing

Tester KHÔNG cần biết code bên trong Product Analyzer.

Chỉ quan tâm:

Input → Product Analyzer → Output/Error/Crash.

Fuzzer sẽ tự động tạo ra nhiều dữ liệu bất thường và gửi vào chương trình.

### B. White-box Fuzzing

Tester được phép biết và phân tích source code.

Mục tiêu là:

- Phân tích code.
- Xác định các branch/path quan trọng.
- Instrument code.
- Thu thập code coverage.
- Tạo fuzz input nhằm đi sâu vào các nhánh code.
- Phát hiện crash, exception, assertion failure hoặc logic error.

---

# II. KIẾN TRÚC PROJECT

Hãy đề xuất kiến trúc project đơn giản nhưng đủ tốt cho đồ án sinh viên.

Ưu tiên:

- Python 3.12+
- Product Analyzer viết bằng Python hoặc C++.
- Fuzzer viết bằng Python.
- pytest để regression testing.
- coverage.py cho coverage nếu sử dụng Python.
- Hypothesis có thể dùng để hỗ trợ property-based fuzzing.
- AFL++ hoặc libFuzzer có thể được giới thiệu như phần mở rộng nếu phù hợp.

Tôi muốn project có cấu trúc:

project/
│
├── analyzer/
│   ├── product_analyzer.py
│   ├── validator.py
│   └── parser.py
│
├── fuzzing/
│   ├── blackbox_fuzzer.py
│   ├── whitebox_fuzzer.py
│   ├── generators.py
│   └── mutations.py
│
├── corpus/
│   ├── valid/
│   └── invalid/
│
├── crashes/
│   ├── blackbox/
│   └── whitebox/
│
├── tests/
│   ├── test_normal.py
│   ├── test_boundary.py
│   └── test_regression.py
│
├── reports/
│   ├── blackbox_results.csv
│   ├── whitebox_results.csv
│   ├── coverage.json
│   └── charts/
│
├── requirements.txt
├── README.md
└── main.py

Nếu kiến trúc này chưa tối ưu, hãy điều chỉnh nhưng phải giải thích lý do.

---

# III. GIAI ĐOẠN 1 – THIẾT LẬP MÔI TRƯỜNG

Hướng dẫn tôi từng bước trên Windows:

1. Kiểm tra Python.
2. Tạo virtual environment.
3. Kích hoạt virtual environment.
4. Cài package.
5. Tạo requirements.txt.
6. Kiểm tra project chạy được.

Đưa chính xác các command:

python --version

python -m venv .venv

.venv\Scripts\activate

pip install ...

Sau mỗi bước, cho tôi biết kết quả mong đợi.

Nếu có lỗi, giải thích cách xử lý.

---

# IV. GIAI ĐOẠN 2 – XÂY DỰNG PRODUCT ANALYZER

Viết Product Analyzer có code hoàn chỉnh.

Input ví dụ:

{
    "id": "P001",
    "name": "Camera Wifi",
    "category": "Camera",
    "price": 1500000,
    "stock": 20,
    "discount": 10,
    "rating": 4.5,
    "description": "Camera giám sát wifi"
}

Output:

{
    "valid": true,
    "final_price": 1350000,
    "inventory_value": 27000000,
    "errors": [],
    "warnings": []
}

Phải thiết kế code sao cho có nhiều branch để White-box Fuzzing có ý nghĩa.

Ví dụ:

if price < 0:
    ...

if stock < 0:
    ...

if discount < 0 or discount > 100:
    ...

if rating < 0 or rating > 5:
    ...

if len(name) > MAX_NAME_LENGTH:
    ...

if category == "...":
    ...

Ngoài ra cố tình tạo một số vulnerability/bug có kiểm soát để fuzzing có thể phát hiện.

Ví dụ:

- xử lý input None không tốt
- kiểu dữ liệu không đúng
- JSON malformed
- số quá lớn
- chuỗi cực dài
- phép tính gây overflow hoặc lỗi
- chia cho 0 trong một branch
- nested JSON bất thường
- missing field
- duplicate field
- Unicode bất thường

Nhưng phải đánh dấu rõ những bug nào là “bug mô phỏng cho mục đích kiểm thử”, không tạo lỗi nguy hiểm cho hệ thống thật.

---

# V. GIAI ĐOẠN 3 – XÂY DỰNG TEST CASE CƠ BẢN

Trước khi fuzzing, xây dựng test suite bình thường.

Bao gồm:

1. Normal test
2. Boundary test
3. Invalid input test
4. Exception test

Ví dụ:

price = 0
price = 1
price = -1

discount = 0
discount = 100
discount = 101

rating = 0
rating = 5
rating = 5.1

stock = 0
stock = 1
stock = -1

name = ""
name = "A"
name = chuỗi vượt giới hạn

Viết pytest test case hoàn chỉnh.

Chạy:

pytest

Giải thích kết quả.

---

# VI. GIAI ĐOẠN 4 – THIẾT KẾ BLACK-BOX FUZZING

Đây là phần quan trọng nhất.

Hãy xây dựng Black-box Fuzzer.

Black-box Fuzzer KHÔNG được dựa vào source code của Product Analyzer.

Fuzzer chỉ biết:

INPUT → PROGRAM → OUTPUT

Thiết kế fuzzer có:

1. Seed corpus.
2. Random input generation.
3. Mutation.
4. Execution.
5. Oracle.
6. Crash detection.
7. Timeout detection.
8. Result logging.
9. Crash saving.
10. Deduplication.

---

# VII. INPUT GENERATION

Tạo nhiều loại dữ liệu:

### 1. Random JSON

Ví dụ:

{}

{"id": null}

{"price": -999999}

{"stock": "abc"}

{"rating": 999999}

### 2. Boundary values

0

-1

1

2147483647

2147483648

999999999999999999

### 3. String fuzzing

""

"A"

"A"*10

"A"*100

"A"*1000

"A"*10000

### 4. Special characters

"\n"

"\t"

"\0"

"<>"

"{}"

"[]"

"\""

"'"

"&"

"<script>"

### 5. Unicode

Tiếng Việt.

Emoji.

Chinese.

Arabic.

Unicode combining characters.

### 6. Type confusion

price = "1000"

price = []

price = {}

price = null

price = true

### 7. Missing fields

Xóa từng field.

### 8. Extra fields

Thêm field không được định nghĩa.

### 9. Malformed JSON

{

{"

[

{"price":

---

# VIII. BLACK-BOX ORACLE

Thiết kế oracle để xác định input có vấn đề.

Oracle cần phát hiện:

- Crash.
- Exception.
- Timeout.
- Invalid output.
- Unexpected output.
- Vi phạm business rule.

Ví dụ:

Nếu:

discount = 200

nhưng chương trình trả:

valid = true

thì ghi nhận:

LOGIC_BUG.

Nếu chương trình crash:

CRASH.

Nếu chương trình không phản hồi trong thời gian giới hạn:

TIMEOUT.

---

# IX. BLACK-BOX FUZZING EXPERIMENT

Thiết kế experiment:

Run 1:
100 inputs

Run 2:
1,000 inputs

Run 3:
10,000 inputs

Nếu máy đủ mạnh có thể:

50,000 hoặc 100,000 inputs.

Mỗi lần chạy lưu:

- Total inputs.
- Valid inputs.
- Invalid inputs.
- Crashes.
- Exceptions.
- Timeouts.
- Logic bugs.
- Unique crashes.
- Execution time.
- Average execution time.

Xuất CSV:

blackbox_results.csv

Ví dụ:

iteration,input_type,result,error,time_ms

---

# X. GIAI ĐOẠN 5 – WHITE-BOX FUZZING

Giải thích rõ sự khác biệt:

Black-box:

Fuzzer không biết internal code.

White-box:

Fuzzer có thông tin về source code và coverage.

Đầu tiên phân tích source code Product Analyzer.

Xác định:

- Statements.
- Branches.
- Conditions.
- Paths.
- Exception handlers.

Tạo control flow đơn giản.

Ví dụ:

Input
 ↓
Parser
 ↓
Validate ID
 ↓
Validate price
 ↓
Validate stock
 ↓
Validate discount
 ↓
Validate rating
 ↓
Calculate
 ↓
Output

Xác định những branch mà black-box khó tiếp cận.

---

# XI. CODE COVERAGE

Sử dụng coverage.py.

Command:

coverage run -m pytest

coverage report

coverage html

Phân tích:

- Statement coverage.
- Branch coverage nếu có thể.
- Missing lines.

Tạo báo cáo coverage.

Ví dụ:

Before fuzzing:

Statement coverage = 72%

Sau fuzzing:

Statement coverage = 94%

Giải thích tại sao coverage tăng.

---

# XII. WHITE-BOX FUZZER

Xây dựng whitebox_fuzzer.py.

Fuzzer sử dụng coverage feedback.

Ý tưởng:

1. Tạo seed input.
2. Chạy Product Analyzer.
3. Đo coverage.
4. Nếu input tạo ra coverage mới:
   → giữ input lại.
5. Mutate input đó.
6. Chạy lại.
7. Nếu coverage tăng:
   → giữ.
8. Nếu crash:
   → lưu crash.
9. Lặp lại.

Pseudo:

corpus = initial_inputs

for i in range(N):

    seed = choose(corpus)

    mutated = mutate(seed)

    result = execute(mutated)

    coverage = get_coverage(result)

    if coverage > previous_coverage:
        corpus.append(mutated)

    if result.crash:
        save_crash(mutated)

---

# XIII. SO SÁNH BLACK-BOX VÀ WHITE-BOX

Tạo bảng:

| Tiêu chí | Black-box | White-box |
|---|---|---|
| Biết source code | Không | Có |
| Coverage feedback | Không | Có |
| Input generation | Random/Mutation | Coverage-guided |
| Dễ triển khai | Cao | Trung bình |
| Phát hiện crash | Có | Có |
| Tìm deep branch | Khó hơn | Tốt hơn |
| Phân tích code | Không | Có |

Thực nghiệm với cùng số lượng input.

Ví dụ:

Black-box:
10,000 inputs

White-box:
10,000 inputs

So sánh:

- Number of crashes.
- Number of unique bugs.
- Coverage.
- Execution time.
- Unique paths.
- Invalid inputs discovered.

---

# XIV. THU THẬP CRASH

Mỗi crash phải được lưu lại.

Ví dụ:

crashes/
├── blackbox/
│   ├── crash_001.json
│   ├── crash_002.json
│
└── whitebox/
    ├── crash_001.json

Mỗi crash lưu:

- Input.
- Error.
- Exception.
- Timestamp.
- Fuzzer type.
- Iteration.

Sau đó tạo crash reproducer:

reproduce_crash.py

Mục tiêu:

python reproduce_crash.py crashes/blackbox/crash_001.json

và chứng minh lỗi có thể tái hiện.

---

# XV. TRIAGE VÀ PHÂN LOẠI BUG

Tự động hoặc thủ công phân loại:

1. Crash
2. Exception
3. Timeout
4. Input validation bug
5. Business logic bug
6. Parser bug
7. Type handling bug
8. Boundary bug

Tạo severity:

Critical
High
Medium
Low

Ví dụ:

Division by zero → High

Application crash → High

Invalid rating accepted → Medium

Unexpected warning → Low

---

# XVI. VISUALIZATION

Tạo biểu đồ bằng matplotlib.

Cần ít nhất:

### Biểu đồ 1

Number of bugs:

Black-box vs White-box

### Biểu đồ 2

Coverage:

Before fuzzing
After Black-box
After White-box

### Biểu đồ 3

Input result:

Valid
Invalid
Crash
Timeout

### Biểu đồ 4

Execution time:

100
1,000
10,000
50,000 inputs

Lưu vào:

reports/charts/

---

# XVII. KẾT QUẢ THỰC NGHIỆM

Tạo bảng:

| Metric | Black-box | White-box |
|---|---:|---:|
| Total Inputs | | |
| Crashes | | |
| Unique Bugs | | |
| Exceptions | | |
| Timeouts | | |
| Coverage | | |
| Execution Time | | |

Không được tự bịa số liệu.

Các số liệu phải lấy trực tiếp từ chương trình chạy thực tế.

---

# XVIII. ĐÁNH GIÁ

Phân tích:

1. Black-box tìm được những loại lỗi nào?
2. White-box tìm thêm được lỗi nào?
3. White-box có coverage cao hơn không?
4. Black-box có đơn giản hơn không?
5. Chi phí thực hiện mỗi phương pháp.
6. Khi nào nên sử dụng Black-box?
7. Khi nào nên sử dụng White-box?
8. Kết hợp hai phương pháp có tốt hơn không?

---

# XIX. DEMO TRỰC TIẾP

Thiết kế một demo hoàn chỉnh.

Khi chạy:

python main.py

Hiển thị menu:

================================
 PRODUCT ANALYZER FUZZ TESTING
================================

1. Run Normal Tests
2. Run Black-box Fuzzing
3. Run White-box Fuzzing
4. Show Coverage
5. Show Crash Results
6. Generate Report
7. Exit

Cho phép người dùng chọn.

---

# XX. README

Viết README.md hoàn chỉnh gồm:

1. Project Overview
2. Objectives
3. Architecture
4. Installation
5. Running Product Analyzer
6. Running Normal Tests
7. Running Black-box Fuzzing
8. Running White-box Fuzzing
9. Coverage
10. Crash Analysis
11. Results
12. Conclusion

---

# XXI. BÁO CÁO ĐỒ ÁN

Hãy xây dựng báo cáo theo cấu trúc:

CHƯƠNG 1 – TỔNG QUAN

1.1. Đặt vấn đề

1.2. Mục tiêu

1.3. Phạm vi

1.4. Đối tượng nghiên cứu

1.5. Phương pháp nghiên cứu

---

CHƯƠNG 2 – CƠ SỞ LÝ THUYẾT

2.1. Software Testing

2.2. Fuzz Testing

2.3. Black-box Testing

2.4. White-box Testing

2.5. Black-box Fuzzing

2.6. White-box Fuzzing

2.7. Mutation-based Fuzzing

2.8. Coverage-guided Fuzzing

2.9. Code Coverage

2.10. Oracle

2.11. Crash Detection

---

CHƯƠNG 3 – PHÂN TÍCH VÀ THIẾT KẾ

3.1. Mô tả hệ thống thương mại điện tử

3.2. Product Analyzer

3.3. Kiến trúc hệ thống

3.4. Thiết kế dữ liệu sản phẩm

3.5. Thiết kế Black-box Fuzzer

3.6. Thiết kế White-box Fuzzer

3.7. Thiết kế Test Oracle

3.8. Thiết kế Crash Collector

3.9. Thiết kế Coverage Collector

---

CHƯƠNG 4 – TRIỂN KHAI

4.1. Môi trường

4.2. Công nghệ sử dụng

4.3. Product Analyzer

4.4. Black-box Fuzzer

4.5. White-box Fuzzer

4.6. Coverage

4.7. Crash Detection

4.8. Report Generation

---

CHƯƠNG 5 – THỰC NGHIỆM

5.1. Test environment

5.2. Test dataset

5.3. Black-box experiment

5.4. White-box experiment

5.5. Coverage result

5.6. Bug discovery

5.7. Crash analysis

5.8. Performance

5.9. Comparison

---

CHƯƠNG 6 – ĐÁNH GIÁ

6.1. Ưu điểm

6.2. Hạn chế

6.3. Black-box

6.4. White-box

6.5. Kết hợp hai phương pháp

6.6. Khả năng áp dụng thực tế

---

CHƯƠNG 7 – KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

7.1. Kết quả đạt được

7.2. Những hạn chế

7.3. Hướng phát triển

Có thể phát triển:

- AFL++
- libFuzzer
- REST API fuzzing
- Database fuzzing
- Authentication fuzzing
- Distributed fuzzing
- CI/CD fuzzing
- Docker
- Dashboard

---

# XXII. SLIDE THUYẾT TRÌNH

Sau khi hoàn thành project, hãy tạo nội dung slide khoảng 12–15 slide:

Slide 1: Tên đề tài

Slide 2: Vấn đề

Slide 3: Mục tiêu

Slide 4: Fuzzing là gì?

Slide 5: Black-box Fuzzing

Slide 6: White-box Fuzzing

Slide 7: Kiến trúc hệ thống

Slide 8: Product Analyzer

Slide 9: Black-box implementation

Slide 10: White-box implementation

Slide 11: Experiment

Slide 12: Results

Slide 13: Comparison

Slide 14: Demo

Slide 15: Conclusion

Mỗi slide cần:
- Nội dung ngắn gọn.
- Hình/diagram nên sử dụng.
- Lời nói khi thuyết trình.

---

# XXIII. YÊU CẦU QUAN TRỌNG

Không được chỉ đưa lý thuyết.

Tôi muốn thực hiện project thực tế.

Hãy chia quá trình thành các PHASE:

PHASE 1 – Setup

PHASE 2 – Product Analyzer

PHASE 3 – Normal Testing

PHASE 4 – Black-box Fuzzing

PHASE 5 – White-box Fuzzing

PHASE 6 – Coverage

PHASE 7 – Crash Analysis

PHASE 8 – Experiment

PHASE 9 – Visualization

PHASE 10 – Report

PHASE 11 – Presentation

Ở mỗi PHASE:

1. Mục tiêu.
2. Cần tạo file nào.
3. Code hoàn chỉnh.
4. Command chạy.
5. Kết quả mong đợi.
6. Nếu lỗi thì cách sửa.
7. Tiêu chí hoàn thành PHASE.

KHÔNG chuyển sang PHASE tiếp theo nếu PHASE hiện tại chưa chạy thành công.

Khi tôi gửi lỗi terminal hoặc source code, hãy phân tích lỗi dựa trên project hiện tại và đưa ra code/command sửa trực tiếp.

Ưu tiên môi trường Windows + VS Code.

Hãy sử dụng tiếng Việt để giải thích.

Bắt đầu bằng:

**PHASE 1 – SETUP PROJECT**

và hướng dẫn tôi từng bước từ số 1.