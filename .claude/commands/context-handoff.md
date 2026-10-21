---
description: Đóng gói và tiếp nhận bàn giao ngữ cảnh 6 mục giữa các phiên AI Agent (loại bỏ 80% rác hội thoại, chống quên điều cấm và lặp lại lỗi cũ)
---

# COMMAND: `/context-handoff` — Giao Thức Bàn Giao Giữa Các AI Agent

Khi làm việc qua nhiều phiên (Session 1 $\rightarrow$ Session 2 $\rightarrow$ Session 3) hoặc phối hợp nhiều Agent, tuyệt đối không copy/export toàn bộ lịch sử chat dài dòng vì sẽ làm Agent sau bị nhiễu ngữ cảnh, quên điều cấm và thử lại đúng cách làm đã thất bại của Agent trước.

Lệnh `/context-handoff` hỗ trợ 2 chế độ:

---

## Chế Độ 1: `/context-handoff giao` (Dành Cho Agent Đang Làm Việc Xuất Bàn Giao)
Khi người dùng gõ `/context-handoff giao`, Agent hiện tại phải lọc bỏ 80% hội thoại thừa và ghi đè trạng thái thực tế mới nhất vào tệp `docs/ops/HANDOFF.md` theo đúng **6 mục bắt buộc**:

1. **Mục Tiêu & Tiêu Chí Hoàn Thành (Goal & Definition of Done):**
   - Nêu rõ mục tiêu chính đang thực hiện và tiêu chí thế nào mới được coi là hoàn tất (ví dụ: phải pass đủ Unit Test + Integration Test + E2E).
2. **Ràng Buộc & Điều Cấm Kỵ Tuyệt Đối (Hard Constraints & Boundaries):**
   - Liệt kê các giới hạn không được vi phạm (ví dụ: cấm đụng DB thật, chỉ dùng dữ liệu Dummy/Seed, chỉ sửa trong phạm vi thư mục được giao).
3. **Trạng Thái Môi Trường & Git (Environment & Git State):**
   - Thư mục đang làm việc (`frontend/`, `backend/`, `infra/`, `mcp/`).
   - Nhánh Git hiện tại, mã Commit mới nhất, cổng dịch vụ đang chạy, biến môi trường mẫu đã thêm.
4. **Tiến Độ Thực Tế Theo Roadmap (Roadmap Progress Status):**
   - Tách bạch 3 trạng thái trung thực:
     - ✅ **Đã code & Đã kiểm thử thành công (Verified)**
     - ⚠️ **Đã code nhưng CHƯA kiểm thử (Coded - Untested)**
     - ⏳ **Chưa làm hoặc Đang chờ Admin/PM phê duyệt (Pending / Blocked)**
5. **Quyết Định Kỹ Thuật & Vết Xe Đổ (Decisions & Dead-Ends — CẤM LẶP LẠI):**
   - Ghi rõ: **Cách A đã thử và thất bại vì lý do gì** (để cấm Agent tiếp theo tốn thời gian và token thử lại Cách A).
   - Ghi rõ: **Cách B đã chọn và đang hoạt động đúng như thế nào**.
6. **Bằng Chứng & Bước Tiếp Theo Ngay Lập Tức (Evidence & Next Immediate Steps):**
   - Đính kèm bằng chứng (đường dẫn file test đã pass, log kết quả).
   - Liệt kê chính xác 1–3 việc đầu tiên mà Agent tiếp theo phải bắt tay vào làm ngay.

---

## Chế Độ 2: `/context-handoff nhận @docs/ops/HANDOFF.md` (Dành Cho Agent Mới Tiếp Nhận)
Khi người dùng mở phiên mới và gõ `/context-handoff nhận @docs/ops/HANDOFF.md`, Agent mới phải:
1. Đọc kỹ toàn bộ 6 mục trong `docs/ops/HANDOFF.md` và đối chiếu nhanh với `docs/ROADMAP.md`.
2. Tóm tắt lại trong 5 dòng: *(1) Nhánh Git hiện tại, (2) Các điều cấm đã ghi nhận, (3) Các vết xe đổ sẽ tuyệt đối tránh, (4) Các phần chưa test cần kiểm tra, (5) Hành động tiếp theo sẽ thực hiện ngay*.
3. Bắt tay vào thực hiện ngay mục **6. Bước Tiếp Theo Ngay Lập Tức** mà không hỏi lại những thông tin đã có trong tệp bàn giao.
