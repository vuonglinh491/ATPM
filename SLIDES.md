# Nội dung slide thuyết trình

1. **Tên đề tài**: Fuzzing Black-box và White-box cho Product Analyzer. Hình: tiêu đề và pipeline.
2. **Vấn đề**: dữ liệu thương mại điện tử có nhiều kiểu và biên bất thường. Hình: sample JSON.
3. **Mục tiêu**: phát hiện lỗi, đo coverage, so sánh phương pháp. Lời nói: nêu tiêu chí đo.
4. **Fuzzing là gì?**: tự động tạo input bất thường và quan sát oracle. Hình: Input -> Program -> Output.
5. **Black-box**: không biết source, dùng seed và mutation. Hình: hộp đen.
6. **White-box**: biết source, dùng coverage feedback. Hình: vòng lặp corpus.
7. **Kiến trúc**: analyzer, fuzzing, tests, reports. Hình: sơ đồ thư mục.
8. **Product Analyzer**: parser, validation, calculation. Hình: control flow.
9. **Black-box implementation**: generator, timeout, dedup, crash collector.
10. **White-box implementation**: coverage.py và corpus growth.
11. **Experiment**: cùng số lượng input, seed cố định, nhiều quy mô.
12. **Results**: trình bày bảng từ `reports/summary.json` và chart sinh tự động.
13. **Comparison**: coverage, bugs, thời gian, chi phí triển khai.
14. **Demo giao diện**: chạy `app.py`, phân tích JSON, chạy fuzzers và mở bảng kết quả/biểu đồ.
15. **Memory model**: Python mô phỏng các tình huống CWE, không cần compiler C và không làm hỏng bộ nhớ thật.
16. **Conclusion**: black-box dễ tiếp cận; white-box đi sâu; memory model minh họa các lỗi bộ nhớ theo cách an toàn.
