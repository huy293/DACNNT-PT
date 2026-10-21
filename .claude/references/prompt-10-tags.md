# TÀI LIỆU THAM KHẢO NỘI BỘ: 10 Nhãn Quy Ước Prompt & Chuẩn Đặt Tên Dữ Liệu

> Đặt trong `.claude/references/` để AI và thành viên dự án tra cứu nhanh khi cần chuẩn hóa câu lệnh hoặc đặt tên biến/bảng dữ liệu.

---

## 1. 10 Nhãn Quy Ước (Convention Tags) Tối Ưu Hóa Đầu Ra Của AI

Khi giao việc cho AI, có thể đính kèm các nhãn quy ước ở đầu hoặc cuối yêu cầu để định hướng chính xác hành vi phản hồi:

| STT | Nhãn quy ước | Tác dụng điều hướng AI |
| :---: | :--- | :--- |
| 1 | `/prompt-designer` | Yêu cầu AI đóng vai kỹ sư thiết kế Prompt, biến ý tưởng ngắn thành bản Master Prompt đầy đủ ngữ cảnh, ràng buộc và định dạng đầu ra. |
| 2 | `/improve-prompt` | Phân tích điểm mơ hồ trong câu lệnh hiện tại và tối ưu hóa lại cho chặt chẽ hơn trước khi thực thi. |
| 3 | `/short-prompt` | Nén một tài liệu hoặc yêu cầu dài thành bản tóm tắt cô đọng nhất mà vẫn giữ nguyên 100% thông tin cốt lõi (tiết kiệm token). |
| 4 | `/hard-constraints` | Ép AI liệt kê và tuân thủ nghiêm ngặt các giới hạn cứng (độ dài file `< 500 dòng`, phạm vi thư mục, cấm thư viện ngoài, chuẩn thời gian UTC). |
| 5 | `/role-expert` | Định hình AI vào đúng vai trò chuyên gia cụ thể (ví dụ: `Principal Architect`, `QA Testing Engineer`, `Pentester`) với tiêu chuẩn nghiệm thu khắt khe. |
| 6 | `/few-shot-example` | Yêu cầu AI sinh trước 1–2 ví dụ mẫu chuẩn mực (Input $\rightarrow$ Output) để người dùng duyệt định dạng trước khi chạy hàng loạt. |
| 7 | `/debug-drift` | Khi AI có dấu hiệu trả lời lệch đề hoặc sửa lan man, dùng nhãn này để buộc AI đối chiếu lại với `ROADMAP.md` và `BUSINESS_FLOW.md`. |
| 8 | `/visual-first` | Yêu cầu AI xuất bản mô phỏng trực quan (Sơ đồ Mermaid hoặc bảng HTML Kanban) để con người duyệt bằng mắt trước khi viết code thật. |
| 9 | `/verify-evidence` | Buộc mọi kết luận hoặc quy tắc AI đưa ra phải kèm bằng chứng thực tế (đường dẫn file, số dòng, log test), cấm phán đoán mò. |
| 10 | `/meta-prompt` | Đúc kết một quy trình vừa làm thành khuôn mẫu tổng quát (Skill hoặc Command `.md`) để tái sử dụng cho mọi dự án về sau. |

---

## 2. Quy Tắc Đặt Tên Dữ Liệu Giúp AI Không Bao Giờ Nhầm Lẫn

1. **Cơ sở dữ liệu (PostgreSQL):**
   - Tên bảng: `snake_case` số nhiều (`users`, `course_enrollments`, `payment_transactions`).
   - Khóa chính: `id` (UUIDv7 hoặc BIGINT). Khóa ngoại: `<ten_bang_so_it>_id` (`user_id`, `course_id`).
   - Cột thời gian: Bắt buộc hậu tố `_at` và lưu chuẩn **UTC ISO-8601** (`created_at`, `updated_at`, `deleted_at`).
   - Cột trạng thái Boolean: Bắt buộc tiền tố `is_`, `has_`, `can_` (`is_verified`, `has_paid`).
2. **Backend & Frontend (TypeScript):**
   - Biến và hàm: `camelCase` mang tính động từ rõ nghĩa (`verifyWebhookSignature`, `revokeUserRefreshToken`).
   - Component & Kiểu dữ liệu (`interface`/`type`): `PascalCase` (`PaymentCheckoutCard`, `UserSessionPayload`).
   - Hằng số cấu hình: `UPPER_SNAKE_CASE` (`MAX_LOGIN_ATTEMPTS`, `ACCESS_TOKEN_TTL_SECONDS`).
3. **Redis Keys (Phân vùng theo Namespace):**
   - Luôn đặt theo mẫu `<service>:<domain>:<identifier>:<attribute>` (ví dụ: `auth:blacklist:jti_98a7b6`, `ratelimit:login:ip_192.168.1.1`).
