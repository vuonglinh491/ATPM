

> “Đề tài của nhóm em xây dựng Product Analyzer để tiếp nhận và kiểm tra dữ liệu sản phẩm thương mại điện tử. Nhóm kết hợp Black-box fuzzing, tập trung vào giá trị biên và dữ liệu sai, với White-box fuzzing, dùng độ phủ dòng mã để mở rộng tập mẫu và đi sâu vào các nhánh nghiệp vụ như cảnh báo tồn kho, chính sách giảm giá và phân hạng sản phẩm. Sau hai lần bổ sung, dự án có thêm mô hình bộ nhớ CWE được mô phỏng an toàn bằng Python và giao diện desktop để chạy demo, xem kết quả cùng biểu đồ. Trong bộ kết quả hiện lưu, 46 bài kiểm thử hồi quy đều đạt; Black-box và White-box mỗi phương pháp chạy 100 input mà không ghi nhận crash, White-box đạt 101 coverage points. Mô hình bộ nhớ ghi nhận các tình huống SAFE, BLOCKED và DETECTED theo kịch bản giả lập; đây không phải bằng chứng về lỗ hổng bộ nhớ trong sản phẩm thực tế. Hướng phát triển tiếp theo là kiểm thử API, cải thiện độ bao phủ và đưa fuzzing vào CI/CD.”

---

## HƯỚNG DẪN CHẠY DEMO VÀ CÔNG DỤNG CÁC CHỨC NĂNG

### 1. Chuẩn bị và khởi chạy

Mở PowerShell tại thư mục dự án. Nếu dự án chưa có môi trường ảo, tạo môi trường và cài các thư viện phụ thuộc:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Trước buổi trình bày, nên chạy bộ kiểm thử để xác nhận ứng dụng sẵn sàng:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Khởi chạy giao diện desktop:

```powershell
.\.venv\Scripts\python.exe app.py
```

Ứng dụng mở cửa sổ **Product Analyzer | Fuzz Lab**. Nếu dự án nằm ở vị trí khác, mở PowerShell tại thư mục đó hoặc thay đường dẫn tới Python trong môi trường `.venv` cho phù hợp. Bản demo hiện tại dùng Python cho mô hình bộ nhớ nên không cần cài trình biên dịch C/C++.

### 2. Trình tự demo đề xuất

#### Bước 1 — Phân tích sản phẩm

1. Mở tab **Phân tích sản phẩm**. Một bản ghi JSON mẫu được nạp sẵn.
2. Chọn **Phân tích**.
3. Giải thích kết quả gồm:
   - `valid`: bản ghi có vượt qua kiểm tra hay không.
   - `final_price`, `inventory_value`, `average_rating` và `badge`: các giá trị nghiệp vụ được tính khi bản ghi hợp lệ.
   - `errors`: các lỗi khiến dữ liệu bị từ chối.
   - `warnings`: các cảnh báo nghiệp vụ không nhất thiết làm dữ liệu mất tính hợp lệ.
4. Để minh họa xử lý dữ liệu sai, thay JSON bằng ví dụ sau rồi chọn **Phân tích**:

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

Kết quả dự kiến là `valid: false` với lỗi về giá và chiết khấu. Mục đích của phần này là cho thấy dữ liệu được kiểm tra và trả lỗi có cấu trúc, thay vì làm ứng dụng dừng bất thường. Chọn **Nạp ví dụ** để khôi phục bản ghi mẫu.

#### Bước 2 — Chạy các bộ fuzzing

1. Mở tab **Phòng thí nghiệm fuzzing**.
2. Nhập số lượng input. Dùng `100` để demo nhanh; mỗi fuzzer chạy theo số lượng đã chọn.
3. Chạy lần lượt các chức năng:
   - **Black-box:** tạo dữ liệu biên và bất thường, sau đó quan sát kết quả bên ngoài như hợp lệ, bị từ chối hoặc lỗi. Chức năng này minh họa kiểm tra cách analyzer phản hồi trước dữ liệu đầu vào đa dạng.
   - **White-box:** chạy analyzer kèm thu thập độ phủ dòng mã. Những input làm tăng số dòng được ghi nhận có thể được giữ lại làm hạt giống tiếp theo. Chức năng này minh họa cách thông tin nội bộ hướng dẫn quá trình fuzzing; `coverage_points` không phải phần trăm độ phủ nhánh.
   - **Mô hình bộ nhớ:** chạy các kịch bản Python mô phỏng giới hạn buffer, phép tính cấp phát và vòng đời vùng nhớ. Chức năng này minh họa phân loại theo CWE một cách an toàn; kết quả mô phỏng không đồng nghĩa đã phát hiện lỗ hổng thực tế trong Product Analyzer.
   - **Chạy toàn bộ:** chạy ba nhóm thử nghiệm theo số input được chọn và tạo báo cáo tổng hợp/biểu đồ. Nên dùng chức năng này khi muốn cập nhật toàn bộ kết quả trong một lượt.
4. Chờ trạng thái **Hoàn tất** trước khi chuyển tab. Các tác vụ chạy nền; trong lúc chạy, các nút fuzzing tạm thời bị khóa để tránh khởi chạy chồng lấn.

#### Bước 3 — Xem bảng kết quả và biểu đồ

1. Mở tab **Kết quả & biểu đồ**.
2. Chọn CSV cần xem, ví dụ `blackbox_results.csv`, `whitebox_results.csv` hoặc `memory_results.csv`. Bảng giúp đối chiếu từng lượt chạy và trạng thái tương ứng.
3. Chọn **Làm mới** nếu vừa chạy thử nghiệm và danh sách báo cáo chưa cập nhật.
4. Chọn **Tạo biểu đồ**, sau đó chọn biểu đồ trong danh sách để xem trước.

Các file kết quả được lưu trong thư mục `reports/`: CSV lưu chi tiết từng lượt, `summary.json` lưu số liệu tổng hợp và `reports/charts/` lưu hình biểu đồ. Công dụng của tab này là hỗ trợ giải thích số liệu bằng dữ liệu truy xuất được và trực quan hóa kết quả trong phần báo cáo.

### 3. Giá trị của giao diện demo khi thuyết trình

Giao diện nối các thành phần của dự án thành một luồng thao tác có thể quan sát trực tiếp:

```text
Nhập JSON → Phân tích và xác thực → Chạy fuzzing
          → Lưu kết quả CSV/JSON → Xem bảng và biểu đồ
```

Nhờ đó, người trình bày có thể minh họa đồng thời:

- **Chức năng của sản phẩm:** kiểm tra bản ghi sản phẩm và tính các giá trị nghiệp vụ.
- **Cách kiểm thử:** phân biệt mục tiêu của Black-box, White-box và mô hình bộ nhớ.
- **Khả năng kiểm chứng:** xem kết quả chi tiết thay vì chỉ nêu số liệu tổng kết.
- **Tính trực quan:** biểu đồ giúp người nghe nhanh chóng nhận biết phân bố kết quả và các nhóm CWE được mô phỏng.

### 4. Lưu ý trước khi báo cáo

- Chạy test và mở thử giao diện trước buổi trình bày; không dùng số liệu cũ để khẳng định đó là kết quả của lần chạy demo hiện tại.
- Chạy thực nghiệm chính thức bằng lệnh `.\.venv\Scripts\python.exe -m experiment --count 1000`; `--count` là số input cho mỗi fuzzer.
- Lệnh chạy thực nghiệm cập nhật các file báo cáo hiện có trong `reports/`. Nếu cần giữ lại kết quả từ nhiều lần chạy để so sánh, sao lưu thư mục đó trước mỗi lần chạy.
- Khi giải thích kết quả bộ nhớ, nhấn mạnh đây là mô hình giả lập bằng Python: nhãn CWE dùng để phân loại tình huống kiểm thử, không phải kết luận có lỗ hổng hoặc CVE trong ứng dụng thực tế.

---
Nhóm em dùng phân tích giá trị biên BVA vì lỗi thường xuất hiện ở ngay sát ranh giới hợp lệ. Với mỗi trường, nhóm xem xét các giá trị ngay dưới ngưỡng tối thiểu, tại ngưỡng tối thiểu, ngay trên ngưỡng tối thiểu, một giá trị thông thường, rồi tương tự quanh ngưỡng tối đa. Ví dụ, discount có miền hợp lệ từ 0 đến 100: giá trị 0 và 100 được chấp nhận, còn -0,01 và 100,01 bị từ chối. Nhóm cũng kiểm tra rating từ 0 đến 5 và độ dài tên từ 1 đến 100 ký tự.

Riêng price và stock cần phân biệt: trong mã hiện tại, giá âm và stock âm bị từ chối, nhưng giá trên (10^{12}) hoặc stock trên 1.000.000 chỉ phát cảnh báo, không làm bản ghi mất hợp lệ. Vì vậy, nhóm không kết luận các giá trị vượt hai ngưỡng này bị chặn; đây là điểm khác nhau giữa ngưỡng trong đặc tả và hành vi validator đang thực thi.”

Ví dụ các giá trị có thể nêu\
Trường	Biên dưới và giá trị quanh biên	Biên trên và giá trị quanh biên	Hành vi trong mã hiện tại
discount	-0,01; 0; 0,01	99,99; 100; 100,01	Ngoài 0–100 bị từ chối
rating	-0,1; 0; 0,1	4,9; 5; 5,1	Ngoài 0–5 bị từ chối
price	-1; 0; 1	(10^{12}-1); (10^{12}); (10^{12}+1)	Giá âm bị từ chối; vượt (10^{12}) chỉ cảnh báo
stock	-1; 0; 1	999.999; 1.000.000; 1.000.001	Stock âm bị từ chối; vượt 1.000.000 chỉ cảnh báo
name	Rỗng; 1 ký tự; 2 ký tự	99; 100; 101 ký tự	Rỗng hoặc dài hơn 100 ký tự bị từ chối