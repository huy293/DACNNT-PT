# SYSTEM AUDIT BLUEPRINT (`AUDIT_BLUEPRINT.md`)

> **Vai trò của tệp này:** Được tạo bởi lệnh `/audit-blueprint` khi bạn muốn phân tích, học hỏi hoặc xây dựng lại một hệ thống lớn có sẵn (ví dụ: ERPNext, Trello, MasterLMS, Shopify) sao cho phù hợp 100% với quy mô và công nghệ của bạn.

---

## 1. Bốn Câu Hỏi Định Hình Ngữ Cảnh (Context Calibration)

| Câu hỏi cốt lõi | Lựa chọn cấu hình hiện tại (Ví dụ mẫu: Nền tảng MasterLMS) |
| :--- | :--- |
| **1. Mục đích xây dựng (Purpose)?** | **Thương mại (Commercial SaaS)** — Phục vụ học viên, phụ huynh và đội ngũ giảng viên thực tế. |
| **2. Quy mô vận hành (Scale)?** | **Doanh nghiệp vừa & đang tăng trưởng (SME / Growth)** — Từ 1,000 đến 50,000 người dùng hoạt động, yêu cầu Zero-Downtime khi nâng cấp. |
| **3. Định hướng Công nghệ (Tech Stack)?** | **Chuyển sang Stack chuẩn AI-Native:**<br/>- `frontend/`: React / Next.js + Tailwind CSS (tách `landing-page`, `user`, `admin`)<br/>- `backend/`: Node.js (NestJS / FastAPI / Go) Stateless API<br/>- `infra/`: PostgreSQL + Redis + MinIO + Nginx + Docker + Grafana<br/>- `mcp/`: MCP Server 5 lớp bảo mật |
| **4. Phạm vi trích xuất (Scope)?** | **Trích xuất có chọn lọc (Core Modules First):** Giữ các phân hệ cốt lõi tạo doanh thu trước, loại bỏ các phân hệ rườm rà chưa cần thiết. |

---

## 2. Bản Đồ Phân Loại Phân Hệ (`KEEP` / `SIMPLIFY` / `DROP`)

| Phân hệ (Module) từ hệ thống mẫu | Quyết định | Lý do & Hướng xử lý trong dự án |
| :--- | :---: | :--- |
| **Xác thực & Phân quyền đa vai trò (Auth & RBAC)** | `KEEP (Giữ 100%)` | Xương sống bảo mật của toàn hệ thống (`JWT + Refresh Token + Redis Blacklist`). |
| **Quản lý Khóa học, Lịch học 1-1 & Điểm danh** | `KEEP (Giữ 100%)` | Giá trị cốt lõi phục vụ học viên và giảng viên hàng ngày. |
| **Thanh toán Học phí, Hóa đơn & Webhook IPN** | `KEEP (Giữ 100%)` | Trực tiếp tạo dòng tiền, cần kiểm thử Clean-Room và Idempotency chặt chẽ. |
| **Kết nối AI Agent tra cứu lịch học & thống kê qua MCP** | `KEEP (Giữ 100%)` | Điểm khác biệt cạnh tranh giúp quản trị viên hỏi đáp dữ liệu tự nhiên an toàn. |
| **Hệ thống Forum / Mạng xã hội nội bộ phức tạp** | `SIMPLIFY (Tối giản)` | Thay bằng khu vực Bình luận & Hỏi đáp gọn nhẹ ngay dưới từng bài học. |
| **Hệ thống Kế toán kép đa tiền tệ quốc tế (Full ERP)** | `DROP (Loại bỏ)` | Quá nặng cho giai đoạn đầu; chỉ giữ sổ thu/chi và đối soát cổng thanh toán VNĐ/USD. |

---

## 3. Ma Trận Tác Nhân & Quyền Hạn (Actor & RBAC Matrix)

| Hành động / Tài nguyên | `Guest` | `Student` | `Instructor` | `Admin` | `MCP Agent (Read Scope)` |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Xem trang giới thiệu & bảng giá | ✅ | ✅ | ✅ | ✅ | ✅ |
| Đăng ký khóa học & Thanh toán | ❌ | ✅ | ❌ | ✅ | ❌ |
| Xem lịch học & tài liệu của chính mình | ❌ | ✅ | ✅ | ✅ | ✅ *(Theo Scope)* |
| Điểm danh & Chấm điểm buổi học | ❌ | ❌ | ✅ | ✅ | ❌ |
| Quản lý người dùng, học phí & cấp API Key MCP | ❌ | ❌ | ❌ | ✅ | ❌ |
| Truy cập trực tiếp Database Production | ❌ | ❌ | ❌ | ❌ | ❌ *(Cấm tuyệt đối)* |
