# CLEAN-ROOM SPECIFICATION (`SPEC.md`)

> **Luật Clean-Room Bất Biến (`.claude/commands/clean-room.md`):**
> *"Model thấy code gốc thì không bao giờ được viết code, và model viết code thì không bao giờ được thấy code gốc!"*
>
> - **Bước 1 (REA):** Phân tích tính năng hiện có và ghi lại toàn bộ quy tắc hành vi vào tệp này kèm **Bằng chứng xác thực (Evidence)**.
> - **Bước 2 (JEV):** Kiểm duyệt từng quy tắc; trả về REA bất kỳ quy tắc nào không có bằng chứng.
> - **Bước 3 (Opus Builder):** Mở phiên làm việc hoàn toàn mới, **CHỈ** nhận tệp `SPEC.md` này (tuyệt đối không mở code gốc) để xây dựng lại tính năng sạch nợ kỹ thuật 100%.
> - **Bước 4 (Haiku Tester):** Chạy kiểm thử trên bản Rebuild và kiểm tra thêm **3 phiên bản cố tình gắn lỗi (Mutants)** để chứng minh bộ test đủ mạnh.

---

## 1. Thông Tin Tính Năng Tái Cấu Trúc (Target Feature Metadata)
- **Tên tính năng (`[FEATURE]`):** Xử lý Thanh toán & Đối soát Webhook IPN (`PaymentWebhookProcessor`)
- **Ứng dụng (`[APP]`):** Phân hệ `backend/src/modules/payment/`
- **Trạng thái kiểm duyệt của JEV:** `16/16 Rules APPROVED` *(Đã loại bỏ 7 quy tắc suy đoán không có bằng chứng)*

---

## 2. Bảng Quy Tắc Hành Vi Kèm Bằng Chứng Đã Duyệt (`Verified Rules`)

| Mã Rule | Quy tắc hành vi bắt buộc (Behavior Specification) | Bằng chứng xác thực từ REA (Evidence) | Điểm JEV |
| :--- | :--- | :--- | :---: |
| `RULE-01` | Khi tổng tiền thanh toán `amount <= 0` hoặc không phải số nguyên dương, trả về `HTTP 400` với mã lỗi `ERR_INVALID_AMOUNT`. | Runtime trace `logs/payment_trace_01.json` & kiểm tra đầu vào tại hàm xử lý giao dịch. | `1.00 (APPROVED)` |
| `RULE-02` | Chữ ký `HMAC-SHA256` của gói tin Webhook phải được so sánh bằng hàm chống tấn công thời gian (`crypto.timingSafeEqual`). | Bằng chứng kiểm toán bảo mật tại `security_audit_hmac.log` dòng 42. | `1.00 (APPROVED)` |
| `RULE-03` | Khi nhận gói tin Webhook có cùng `order_id` đang trong quá trình xử lý, khóa phân tán Redis `SETNX` phải chặn request thứ hai ngay lập tức với `HTTP 200 (Already Processing)`. | Network capture `concurrent_ipn_test.har` (2 requests cách nhau `3ms`). | `0.98 (APPROVED)` |
| `RULE-04` | Nếu đơn hàng đã ở trạng thái `PAID`, mọi gói tin IPN gửi lại sau đó không được cộng tiền lần 2 và phải trả về `HTTP 200 (Idempotent Success)`. | Database transaction log `pg_tx_idempotent_8821.log`. | `1.00 (APPROVED)` |
| `RULE-05` | Nếu cổng thanh toán phản hồi quá `10,000ms`, chuyển trạng thái đơn sang `PAYMENT_VERIFY_REQUIRED` và đẩy cảnh báo đối soát, tuyệt đối không tự động hủy đơn. | Timeout simulation log `gateway_timeout_10s.log`. | `0.95 (APPROVED)` |

---

## 3. Ba Phiên Bản Cố Tình Chứa Lỗi (`Haiku Mutation Testing Suite`)

Để đảm bảo bộ kiểm thử không bị "pass ảo", **Haiku Tester** bắt buộc tạo 3 bản cố tình làm hỏng sau đây và chứng minh bộ test **ĐÁNH TRƯỢT CẢ 3**:

1. **`Mutant-01` (Bỏ qua xác thực chữ ký HMAC):** Sửa hàm kiểm tra chữ ký luôn trả về `true` $\rightarrow$ Bộ test bắt buộc phải phát hiện và đánh **FAIL**.
2. **`Mutant-02` (Tắt khóa chống trùng lặp Idempotency):** Bỏ qua kiểm tra trạng thái `PAID` khi nhận 2 request liên tiếp $\rightarrow$ Bộ test bắt buộc phát hiện số dư bị cộng 2 lần và đánh **FAIL**.
3. **`Mutant-03` (Hủy đơn sai quy tắc khi Timeout):** Đổi trạng thái khi timeout sang `CANCELLED` thay vì `PAYMENT_VERIFY_REQUIRED` $\rightarrow$ Bộ test bắt buộc phát hiện và đánh **FAIL**.

---

## 4. Cổng Ký Duyệt Trước Khi Ship (`Opus Sign-Off Gate`)
- [x] Hiển thị `SPEC.md` để người dùng kiểm tra và nhận lệnh **"BẮT ĐẦU"**.
- [ ] Phiên bản xây dựng lại của Opus vượt qua **100%** bài kiểm thử.
- [ ] Cả 3 phiên bản `Mutant-01`, `Mutant-02`, `Mutant-03` đều bị bộ kiểm thử bắt sống (**FAIL 100%**).
