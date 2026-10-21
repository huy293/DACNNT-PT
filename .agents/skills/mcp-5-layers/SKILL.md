---
name: mcp-5-layers
description: Thiết kế và triển khai MCP Server & MCP Gateway tách biệt với 5 lớp bảo mật (API Key, Session Rate Limit, RBAC Scope, Tool Registry, API Client) + phản xạ JEV
---

# SKILL: Secure MCP Server 5-Layer Architecture

## 1. Khi Nào Kích Hoạt Kỹ Năng Này?
Kích hoạt khi xây dựng hoặc tích hợp Model Context Protocol (`mcp/`) để cho phép Claude Desktop, ChatGPT, hoặc AI Agent nội bộ truy vấn/tác động vào hệ thống mà không bao giờ lộ Database hay `.env` thật.

## 2. Kiến Trúc 5 Lớp Bảo Mật Bắt Buộc Trong `mcp/`
1. **Lớp 1 — Xác Thực API Key (`API Key Auth`):**
   - Mỗi kết nối từ AI Agent phải có khóa định danh riêng (chỉ hiển thị 1 lần khi tạo), có **ngày hết hạn (Expiration Date)**, giới hạn số thiết bị và ghi nhận nguồn gọi.
2. **Lớp 2 — Quản Lý Phiên & Giới Hạn Tốc Độ (`Session & Rate Limit`):**
   - Kiểm soát số lượng kết nối đồng thời và giới hạn số request/phút trên Redis (ví dụ: tối đa 100 requests/phút/thiết bị) để chống AI bị lặp vô hạn gây sập hệ thống.
3. **Lớp 3 — Phân Quyền Phạm Vi (`RBAC / ABAC Scope`):**
   - Tách bạch rõ quyền **Read** (ví dụ: `read:students`, `read:courses`, `read:schedule`) và quyền **Write**. Mặc định chỉ cấp quyền Read theo đúng danh mục trong `docs/technical/FEATURE_MCP.md`.
4. **Lớp 4 — Sổ Đăng Ký Công Cụ (`Tool Registry` + JEV Reflex Middleware):**
   - Chỉ đăng ký các tool đã được phê duyệt trong `FEATURE_MCP.md`.
   - Mọi tool có thao tác sửa/xóa phải đi qua middleware **JEV** chấm điểm rủi ro (`0.00–0.30`: Allow, `0.31–0.70`: Ask User, `0.71–1.00`: Block).
5. **Lớp 5 — Trình Kết Nối Nội Bộ (`Scoped API Client`):**
   - MCP Server tuyệt đối không chọc thẳng vào Database Production mà chỉ gọi qua Backend API nội bộ bằng Token có giới hạn phạm vi (Scoped Token) và ghi Audit Log 13 trường.
