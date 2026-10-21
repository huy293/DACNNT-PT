---
description: Sinh sơ đồ kiến trúc trực quan và luồng di chuyển dữ liệu (Request Journey) bằng Mermaid hoặc HTML tương tác
---

# COMMAND: `/diagram-design` — Vẽ Sơ Đồ Kiến Trúc & Luồng Đi Trực Quan

> **Lưu ý tiết kiệm Token:** Chỉ kích hoạt lệnh `/diagram-design` khi bắt đầu dự án mới, khi hoàn tất một cột mốc kiến trúc lớn, hoặc khi cần nhìn toàn cảnh hệ thống để tối ưu chi phí hạ tầng/bảo mật.

Khi người dùng gọi `/diagram-design`, AI quét cấu trúc thực tế của hệ thống và xuất ra 3 sơ đồ trực quan vào `docs/technical/ARCHITECTURE_PLAN.md` (và cập nhật giao diện trực quan nếu được yêu cầu):

## 1. Sơ Đồ Kiến Trúc Tổng Thể Đa Tầng (End-to-End Infrastructure & Application Topology)
Sử dụng Mermaid `flowchart TD` hoặc `flowchart LR` thể hiện rõ 6 lớp:
1. **Lớp Lá Chắn Ngoài Cùng (Edge & WAF):** Trình duyệt / Thiết bị di động đi qua **Cloudflare** (DNS, SSL, chống DDoS, WAF).
2. **Lớp Cổng Điều Hướng (API Gateway & Reverse Proxy):** **Nginx / Traefik** đứng chắn phía trước để che giấu toàn bộ port nội bộ và phân luồng request.
3. **Lớp Giao Diện Phân Tách (Frontend Tier):**
   - `frontend/landing-page` (Tối ưu SEO & tốc độ tải trang đầu).
   - `frontend/user` (Ứng dụng chính cho khách hàng).
   - `frontend/admin` (Cổng quản trị nội bộ tách biệt subdomain).
4. **Lớp Nghiệp Vụ & AI (Application & MCP Tier):**
   - `backend/` (REST/GraphQL/gRPC API xử lý nghiệp vụ).
   - `mcp/` (MCP Server 5 lớp bảo mật + bộ phản xạ JEV).
5. **Lớp Dữ Liệu Nội Bộ (Data & Storage Tier - Internal Docker Network):**
   - **PostgreSQL** (Lưu trữ dữ liệu quan hệ chính + CDC Backup).
   - **Redis** (Caching truy vấn nóng + JWT Refresh Token Blacklist + Rate Limit).
   - **MinIO / Cloudflare R2** (Lưu trữ ảnh, video, tài liệu).
6. **Lớp Quan Sát & Cảnh Báo (Observability Tier):**
   - **Prometheus + Grafana** (Metrics CPU/RAM/Latency), **Loki** (Logs 13 trường), **Tempo** (Distributed Tracing) $\rightarrow$ Đẩy cảnh báo tức thì về **Telegram Bot**.

## 2. Sơ Đồ Tuần Tự Luồng Đi Của Request (Request Sequence Diagram)
Sử dụng Mermaid `sequenceDiagram` mô tả chi tiết một luồng nghiệp vụ trọng tâm (ví dụ: Đăng nhập JWT + Redis Blacklist, hoặc Thanh toán Webhook chống trùng lặp).

## 3. Sơ Đồ Thực Thể Quan Hệ Cơ Sở Dữ Liệu (Database ERD)
Sử dụng Mermaid `erDiagram` biểu diễn các bảng chính, khóa chính (`PK`), khóa ngoại (`FK`) và các cột được đánh chỉ mục (`Index`).
