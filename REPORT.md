# Báo cáo đồ án

## Chương 1 - Tổng quan

Đề tài xây dựng Product Analyzer và dùng fuzzing để tìm lỗi xử lý dữ liệu sản phẩm. Phạm vi tập trung vào JSON/CSV, kiểm tra nghiệp vụ và phép tính dẫn xuất.

## Chương 2 - Cơ sở lý thuyết

Black-box fuzzing chỉ quan sát input, output và lỗi. White-box fuzzing biết mã nguồn và dùng coverage feedback để giữ lại input đi qua dòng/nhánh mới. Mutation-based fuzzing biến đổi seed; oracle phân loại valid, invalid, exception, timeout và output bất thường.

## Chương 3 - Phân tích và thiết kế

Luồng xử lý là parser -> validator -> calculator -> output. Các nhánh chính gồm thiếu field, sai kiểu, giá/stock âm, discount ngoài `[0, 100]`, rating ngoài `[0, 5]`, tên quá dài, category Camera và description rỗng.

## Chương 4 - Triển khai

Python 3.13, pytest, coverage.py và matplotlib được dùng trong project. Black-box dùng generator, seed corpus, mutation, timeout và deduplication. White-box đo các dòng analyzer bằng coverage.py và chỉ mở rộng corpus khi có điểm coverage mới.

## Chương 5 - Thực nghiệm

Chạy các quy mô 100, 1.000 và 10.000 input bằng `experiment.py`. Điền bảng dưới đây từ `reports/summary.json`, không tự bịa số liệu.

| Metric | Black-box | White-box |
|---|---:|---:|
| Total inputs | đọc từ summary | đọc từ summary |
| Crashes/exceptions | đọc từ summary | đọc từ summary |
| Unique findings | đọc từ summary | đọc từ summary |
| Coverage points | coverage report | coverage feedback |
| Execution time | đọc từ summary | bổ sung khi đo |

## Chương 6 - Đánh giá

Black-box dễ triển khai và phù hợp khi chỉ có executable/API. White-box có thêm thông tin nội bộ nên thường tiếp cận nhánh sâu tốt hơn, nhưng phụ thuộc instrumentation và source code. Kết hợp seed từ black-box với coverage feedback của white-box cho độ bao phủ thực dụng hơn.

## Chương 7 - Kết luận và hướng phát triển

Project cung cấp analyzer, test suite, hai fuzzer, crash artifact, coverage và chart generator chạy được trên Windows. Hướng phát triển gồm REST API fuzzing, database fuzzing, AFL++, libFuzzer, distributed fuzzing và CI/CD.
