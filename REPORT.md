# Báo cáo đồ án

## Chương 1 - Tổng quan

Đề tài xây dựng Product Analyzer và dùng fuzzing để tìm lỗi xử lý dữ liệu sản phẩm. Phạm vi gồm JSON/CSV, kiểm tra nghiệp vụ, phép tính dẫn xuất và mô hình Python mô phỏng kiểu dữ liệu, biên cùng vòng đời bộ nhớ.

## Chương 2 - Cơ sở lý thuyết

Black-box fuzzing chỉ quan sát input, output và lỗi. White-box fuzzing biết mã nguồn và dùng coverage feedback để giữ lại input đi qua dòng/nhánh mới. Mutation-based fuzzing biến đổi seed; oracle phân loại valid, invalid, exception, timeout và output bất thường. Memory model viết bằng Python mô phỏng tình huống bộ nhớ an toàn, phân loại theo CWE; CWE không tương đương CVE và không chứng minh có lỗ hổng trong sản phẩm thật.

## Chương 3 - Phân tích và thiết kế

Luồng xử lý là parser -> validator -> calculator -> output. Các nhánh chính gồm thiếu field, sai kiểu, giá/stock âm, discount ngoài `[0, 100]`, rating ngoài `[0, 5]`, tên quá dài, category Camera và description rỗng.

## Chương 4 - Triển khai

Python 3.12+, pytest, coverage.py và matplotlib được dùng trong project. Giao diện demo desktop dùng Tkinter. Black-box dùng generator, seed corpus, mutation, timeout và deduplication. White-box đo các dòng analyzer bằng coverage.py và chỉ mở rộng corpus khi có điểm coverage mới. Python memory-model fuzzer chạy các ca biên, sai kiểu, null, cấp phát quá lớn, tràn số, leak, double-free và use-after-free; các hành vi nguy hiểm được mô phỏng, không truy cập bộ nhớ thật.

## Chương 5 - Thực nghiệm

Chạy các quy mô 100, 1.000 và 10.000 input bằng `experiment.py`. Điền bảng dưới đây từ `reports/summary.json`, không tự bịa số liệu.

| Metric | Black-box | White-box | Python memory model |
|---|---:|---:|---:|
| Total inputs | đọc từ summary | đọc từ summary | đọc từ summary |
| Crashes/exceptions/findings | đọc từ summary | đọc từ summary | CWE từ CSV |
| Unique findings | đọc từ summary | đọc từ summary | đếm theo CWE sau deduplication |
| Coverage points | coverage report | coverage feedback | chưa instrument |
| Execution time | đọc từ summary | đọc từ summary | bổ sung khi đo |

## Chương 6 - Đánh giá

Black-box dễ triển khai và phù hợp khi chỉ có executable/API. White-box có thêm thông tin nội bộ nên thường tiếp cận nhánh sâu tốt hơn, nhưng phụ thuộc instrumentation và source code. Kết hợp seed từ black-box với coverage feedback của white-box cho độ bao phủ thực dụng hơn.

## Chương 7 - Kết luận và hướng phát triển

Project cung cấp analyzer, test suite, ba fuzzer Python, memory model Python, giao diện demo desktop, phân loại CWE, crash artifact, coverage và chart generator chạy được trên Windows mà không cần C compiler. CVE chỉ được gắn khi có lỗ hổng cụ thể đã xác minh và mã CVE chính thức. Hướng phát triển gồm REST API fuzzing, database fuzzing, AFL++, libFuzzer, distributed fuzzing và CI/CD.
