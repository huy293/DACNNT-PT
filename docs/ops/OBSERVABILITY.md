# OBSERVABILITY, 13-FIELD LOGGING & MONITORING (`OBSERVABILITY.md`)

> **Vai trò của tệp này:** Định nghĩa tiêu chuẩn **13 thành phần của một bản ghi Log chuẩn**, **5 quy tắc vàng Logging** và kiến trúc giám sát chủ động (**Prometheus + Grafana + Loki + Tempo $\rightarrow$ Telegram Alert**) phục vụ giai đoạn **Bước 6: MAINTAIN**.

---

## 1. Mười Ba Thành Phần Cấu Tạo Một Bản Ghi Log Chuẩn (`13-Field Structured JSON Log`)

Mọi bản ghi log sinh ra từ `backend/` và `mcp/` bắt buộc định dạng JSON một dòng (JSON Lines) gồm đủ 13 trường sau để **Loki / Grafana Assistant** có thể tự động truy vết nguyên nhân gốc rễ (RCA) trong vài giây:

```json
{
  "timestamp": "2026-10-20T03:15:42.128Z",
  "level": "ERROR",
  "service": "backend-payment-api",
  "environment": "production",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "request_id": "req_01J9Z8K4M2N6P8Q0R2S4T6V8W0",
  "actor_id": "usr_7210818345489728513",
  "client_ip": "203.113.152.10",
  "event_action": "PAYMENT_WEBHOOK_VERIFY",
  "http_context": { "method": "POST", "path": "/api/v1/payments/ipn", "status_code": 400 },
  "duration_ms": 14,
  "error_and_metadata": {
    "error_code": "ERR_INVALID_SIGNATURE",
    "message": "Webhook HMAC-SHA256 signature mismatch",
    "order_id": "ord_99812"
  }
}
```

| STT | Tên trường (`Field`) | Ý nghĩa phục vụ Debug, Monitoring & Bảo mật |
| :---: | :--- | :--- |
| 1 | `timestamp` | Thời gian chuẩn **UTC ISO-8601** có độ chính xác tới mili-giây. |
| 2 | `level` | Mức độ nghiêm trọng (`DEBUG`, `INFO`, `WARN`, `ERROR`, `FATAL`). |
| 3 | `service` | Tên phân hệ phát sinh log (`backend-api`, `mcp-server`, `worker-cdc`). |
| 4 | `environment` | Môi trường đang chạy (`local`, `staging`, `production`). |
| 5 | `trace_id` | Mã truy vết xuyên suốt từ Frontend $\rightarrow$ Nginx $\rightarrow$ Backend $\rightarrow$ DB (OpenTelemetry Tempo). |
| 6 | `span_id` | Mã định danh bước thực thi hiện tại bên trong `trace_id`. |
| 7 | `request_id` | Mã định danh duy nhất của từng HTTP Request. |
| 8 | `actor_id` | ID người dùng hoặc ID của API Key MCP đang thực hiện hành động (`anonymous` nếu chưa đăng nhập). |
| 9 | `client_ip` | Địa chỉ IP thực của thiết bị gọi (lấy qua Cloudflare/Nginx header đã xác thực). |
| 10 | `event_action` | Mã hành động nghiệp vụ chuẩn hóa (`USER_LOGIN`, `PAYMENT_WEBHOOK_VERIFY`, `MCP_TOOL_CALL`). |
| 11 | `http_context` | Phương thức HTTP (`GET`/`POST`), đường dẫn route và mã trạng thái trả về (`200`, `400`, `500`). |
| 12 | `duration_ms` | Thời gian xử lý tính bằng mili-giây (phát hiện ngay truy vấn chậm). |
| 13 | `error_and_metadata` | Mã lỗi chuẩn hóa, thông điệp chi tiết, stack trace (ở môi trường nội bộ) và dữ liệu ngữ cảnh đã che thông tin nhạy cảm. |

---

## 2. Năm Quy Tắc Vàng Khi Ghi Log (`5 Golden Logging Rules`)

1. **Cấm dùng `console.log` trần trụi:** Bắt buộc dùng bộ ghi log cấu trúc (`pino` hoặc `winston` / `structlog`) xuất JSON chuẩn 13 trường.
2. **Che giấu tuyệt đối dữ liệu nhạy cảm (`PII & Secret Redaction`):** Cấm ghi mật khẩu, mã OTP, số thẻ tín dụng, `access_token`, `refresh_token` hoặc khóa `.env` vào trong log.
3. **Không nuốt lỗi ngầm (`Zero Silent Catch`):** Mọi khối `catch (error)` bắt buộc ghi log mức `ERROR` kèm `trace_id` và ngữ cảnh đầu vào trước khi trả lỗi chuẩn hóa.
4. **Gắn `trace_id` xuyên tầng:** Mọi log phát sinh từ cùng 1 thao tác của người dùng phải chia sẻ chung một `trace_id` để tra cứu 1 chạm trên Grafana.
5. **Phân cấp ngưỡng cảnh báo rõ ràng:**
   - `INFO`: Ghi nhận hành trình nghiệp vụ bình thường.
   - `WARN`: Các sự kiện bất thường nhưng hệ thống tự xử lý được (ví dụ: nhập sai mật khẩu, retry kết nối).
   - `ERROR` / `FATAL`: Lỗi hệ thống hoặc nghi vấn tấn công bảo mật $\rightarrow$ **Tự động bắn cảnh báo tức thì về Telegram**.

---

## 3. Kiến Trúc Giám Sát Chủ Động (`Observability Stack`)

- **Prometheus:** Thu thập chỉ số phần cứng (CPU, RAM, Disk I/O, Network) và chỉ số ứng dụng (Request/s, Latency p95/p99).
- **Loki:** Tập trung toàn bộ bản ghi Log 13 trường từ mọi container Docker.
- **Tempo:** Truy vết phân tán (Distributed Tracing) giúp nhìn rõ request bị chậm ở tầng Backend hay tầng PostgreSQL/Redis.
- **Grafana + Telegram Alerting:** Hiển thị bảng điều khiển trực quan và tự động gửi tin nhắn cảnh báo vào nhóm Telegram vận hành ngay khi CPU `> 80%`, Disk `> 85%`, hoặc xuất hiện lỗi `HTTP 5xx`.
