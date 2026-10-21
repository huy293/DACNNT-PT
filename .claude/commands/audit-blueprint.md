---
description: Phỏng vấn 4 câu hỏi ngữ cảnh và mổ xẻ hệ thống mẫu/mã nguồn mở để xuất tài liệu đặc tả AUDIT_BLUEPRINT.md
---

# COMMAND: `/audit-blueprint` — Mổ Xẻ Hệ Thống Mẫu & Lập Đặc Tả Toàn Diện

Khi người dùng muốn học hỏi, clone hoặc tùy biến từ một hệ thống lớn có sẵn (ví dụ: ERPNext, Trello, LMS, E-commerce, CRM) và gõ lệnh `/audit-blueprint`, AI thực hiện theo đúng quy trình 2 giai đoạn sau:

## Giai Đoạn 1: Phỏng Vấn 4 Câu Hỏi Định Hình Ngữ Cảnh (Bắt Buộc Hỏi Trước)
AI tuyệt đối không phán đoán mò mà phải hỏi ngắn gọn người dùng **4 câu hỏi cốt lõi**:
1. **Mục đích xây dựng (Purpose):** Hệ thống này dùng để kinh doanh thương mại (SaaS/Bán lẻ), dùng nội bộ doanh nghiệp, hay phục vụ học tập/nghiên cứu?
2. **Quy mô vận hành (Scale):** Hướng tới quy mô Cá nhân/Startup nhỏ, Doanh nghiệp vừa (SME), hay Tổ chức lớn (Enterprise đa chi nhánh)?
3. **Định hướng Công nghệ (Tech Stack):** Muốn giữ nguyên công nghệ của bản mẫu hay chuyển đổi sang Tech Stack chuẩn của bạn (ví dụ: Next.js/React + NestJS/FastAPI/Go + PostgreSQL + Redis + MinIO)?
4. **Phạm vi trích xuất (Scope):** Muốn mổ xẻ toàn bộ hệ thống hay chỉ trích xuất một số phân hệ (modules) cốt lõi?

## Giai Đoạn 2: Xuất Hồ Sơ Đặc Tả Vào `docs/product/AUDIT_BLUEPRINT.md`
Sau khi người dùng trả lời 4 câu hỏi trên, AI tiến hành phân tích hệ thống mẫu và xuất tài liệu hoàn chỉnh vào `docs/product/AUDIT_BLUEPRINT.md` gồm 6 phần:
1. **Tổng quan Hệ thống & Định vị theo 4 tiêu chí đã chọn.**
2. **Bản đồ Phân hệ chức năng (Module Breakdown):** Liệt kê đầy đủ các module (Auth, Core Domain, Billing, Notification, Admin, Reporting) — phân loại rõ module nào **Giữ lại (`KEEP`)**, module nào **Tối giản (`SIMPLIFY`)**, module nào **Loại bỏ (`DROP`)**.
3. **Danh mục Actor & Ma trận Phân quyền (RBAC Matrix).**
4. **Chuyển hóa thành Quy trình Nghiệp vụ (`BUSINESS_FLOW.md` Ready):** Tóm tắt các luồng nghiệp vụ cốt lõi kèm Business Rules để sẵn sàng đưa sang `docs/product/BUSINESS_FLOW.md`.
5. **Thiết kế Dữ liệu & Kiến trúc Đề xuất:** Các bảng dữ liệu trọng tâm và cách bố trí vào Monorepo (`frontend/`, `backend/`, `infra/`, `mcp/`).
6. **Lộ trình Chia nhỏ theo Sprint (`ROADMAP.md` Ready):** Chia toàn bộ tính năng thành các Sprint (mỗi Sprint 5–10 tính năng) theo thứ tự ưu tiên từ nền móng đến nâng cao.
