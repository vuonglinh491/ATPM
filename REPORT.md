# BÁO CÁO ĐỒ ÁN MÔN HỌC: AN TOÀN PHẦN MỀM-1-1-26 (NO2)

**ĐỀ TÀI:**
## **KIỂM THỬ FUZZING BLACK-BOX VÀ WHITE-BOX CHO BỘ PHÂN TÍCH SẢN PHẨM TRONG HỆ THỐNG THƯƠNG MẠI ĐIỆN TỬ**

---

* **Giảng viên hướng dẫn:** ThS. Vũ Quang Dũng
* **Sinh viên thực hiện:**
  1. **Ngô Vương Linh** – Mã SV: **23010496**
  2. **Nguyễn Tiến Thịnh** – Mã SV: **23010500**
* **Khoá:** K17 (2023 – 2027)
* **Lớp tín chỉ:** An Toàn Phần Mềm-1-1-26 (NO2)
* **Chương trình đào tạo:** Hệ Thống Thông Tin
* **Thời gian hoàn thành:** Tháng 10 năm 2026

---

> [!NOTE]
> Báo cáo chi tiết toàn văn bao gồm Lời cảm ơn, Mục lục, Danh mục hình ảnh, 6 Chương nội dung học thuật đầy đủ và Tài liệu tham khảo đã được biên soạn và lưu trữ tại file:  
> 👉 **[BAO_CAO_CHI_TIET.md](BAO_CAO_CHI_TIET.md)**

---

## TÓM TẮT CÁC KẾT QUẢ THỰC NGHIỆM ĐẠT ĐƯỢC

### 1. Kết quả Kiểm thử đơn vị (Unit Tests):
- **Số lượng test:** **46/46 passed** (100% thành công trên Pytest).

### 2. Kết quả Black-box Fuzzing (Kiểm tra ranh giới Vùng Bounded):
- **Tổng số input:** 100
- **Số input hợp lệ (trong biên):** 42 (42%)
- **Số input bị từ chối (ngoài biên):** 58 (58%)
- **Số lỗi Crash / Exception:** 0
- **Thời gian xử lý trung bình:** 2.14 ms/input (tổng thời gian: 0.2135 s)

### 3. Kết quả White-box Fuzzing (Đào sâu bên trong Vùng Bounded):
- **Điểm độ phủ thực thi (`coverage_points`):** 101 điểm
- **Kho hạt giống mở rộng (`corpus_size`):** 27 mẫu
- **Tỷ lệ kích hoạt nhánh nội bộ:** 100% (6/6 nhánh nghiệp vụ sâu)
- **Số lỗi Crash / Exception:** 0

### 4. Kết quả mô phỏng rủi ro bộ nhớ (Python Memory Model):
- **Tổng số ca kiểm thử:** 100
- **Số ca an toàn / được bảo vệ:** 82 (Safe & Blocked)
- **Phân loại CWE:** CWE-121, CWE-190, CWE-20, CWE-401, CWE-415, CWE-416, CWE-476, CWE-789.

---

## DANH MỤC BIỂU ĐỒ MINH CHỨNG THỰC TẾ

1. **Biểu đồ phân loại kết quả đầu vào Black-box:**
   ![Phân bố kết quả Black-box](reports/charts/input_results.png)

2. **Biểu đồ tăng trưởng độ phủ mã nguồn White-box:**
   ![Tăng trưởng độ phủ White-box](reports/charts/whitebox_coverage.png)

3. **Biểu đồ phân loại an toàn bộ nhớ theo mã CWE:**
   ![Phân loại CWE bộ nhớ](reports/charts/memory_cwe_classifications.png)
