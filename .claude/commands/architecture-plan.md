---
description: Quét toàn bộ mã nguồn, cơ sở dữ liệu và hạ tầng để xuất hồ sơ kiến trúc hệ thống 27 phần vào docs/technical/ARCHITECTURE_PLAN.md
---

# COMMAND: `/architecture-plan` — Xuất Hồ Sơ Kiến Trúc Hệ Thống 27 Phần

Khi người dùng gọi `/architecture-plan`, AI đóng vai **Principal System Architect**, tiến hành khảo sát thực tế toàn bộ kho mã nguồn (`frontend/`, `backend/`, `infra/`, `mcp/`, `docs/`) và xuất báo cáo đầy đủ **27 mục tiêu chuẩn** vào tệp `docs/technical/ARCHITECTURE_PLAN.md`.

## Quy Tắc Khảo Sát Trung Thực (Zero Hallucination)
- Chỉ ghi nhận những công nghệ, thư mục, bảng dữ liệu và tầng bảo vệ **thực sự tồn tại** trong mã nguồn.
- Bất kỳ mục nào trong 27 phần mà dự án hiện tại **chưa có** hoặc **đang làm thiếu**, bắt buộc đánh dấu nhãn **`[NOT_FOUND]`** và tổng hợp vào **Mục 27** để người làm chủ dự án biết chính xác lỗ hổng cần bổ sung.

## Danh Mục 27 Phần Bắt Buộc Trong `docs/technical/ARCHITECTURE_PLAN.md`
1. **Tổng quan dự án & Mục tiêu kinh doanh (Project & Domain Overview)**
2. **Bảng tổng hợp Tech Stack thực tế (Frontend, Backend, Database, Cache, Infra, AI/MCP)**
3. **Cấu trúc cây thư mục Monorepo & Ranh giới Module (Folder Structure)**
4. **Sơ đồ kiến trúc hệ thống tổng thể (System Architecture Diagram bằng Mermaid):**
   - Thể hiện rõ luồng từ `Browser/Mobile` $\rightarrow$ `Cloudflare WAF` $\rightarrow$ `Nginx API Gateway` $\rightarrow$ `Frontend (Landing/User/Admin)` $\rightarrow$ `Backend API` $\rightarrow$ `PostgreSQL / Redis / MinIO` $\rightarrow$ `Observability (Grafana/Prometheus/Loki/Tempo -> Telegram Alert)`.
5. **Cách ly mạng nội bộ & Hạ tầng VPS/Container (Network & LAN Isolation)**
6. **Hành trình chi tiết của một Request (Request Journey & Data Flow Step-by-Step)**
7. **Thiết kế Cơ sở dữ liệu & Sơ đồ thực thể kết hợp (Database Schema & Mermaid ERD)**
8. **Chiến lược Đánh chỉ mục Database (6 kiểu Database Indexing tối ưu truy vấn)**
9. **Chiến lược Bộ nhớ đệm & Thu hồi Cache (Redis Caching & Invalidation Strategy)**
10. **Chiến lược Lưu trữ File & Media (MinIO Self-hosted vs Cloud R2/S3 Cost Optimization)**
11. **Kiến trúc Xác thực & Quản lý phiên (JWT + Refresh Token + Redis Blacklist)**
12. **Ma trận Phân quyền người dùng (RBAC / ABAC Permission Matrix)**
13. **5 Lớp bảo vệ ứng dụng & Phòng chống lỗ hổng (Path Traversal, SQLi, XSS, SSRF, RCE)**
14. **Kiến trúc MCP Server & MCP Gateway (5 Lớp bảo mật kết nối AI Agent)**
15. **Bộ phản xạ JEV Middleware (Cơ chế chấm điểm rủi ro Boolean / Choice / Score `0.0–1.0`)**
16. **Kiến trúc AI Gateway, RAG Pipeline & Benchmark Evals (Chống ảo giác LLM)**
17. **Chuẩn hóa 13 thành phần bản ghi Log & 5 Quy tắc vàng Logging**
18. **Hệ thống Giám sát & Cảnh báo tức thì (Prometheus, Grafana, Loki, Tempo $\rightarrow$ Telegram)**
19. **Cơ chế Xử lý lỗi tập trung & Tự phục hồi (Error Handling, Retry, Circuit Breaker)**
20. **Đồng bộ dữ liệu & Sao lưu an toàn (CDC Pipeline, Redis RDB + AOF, DB Backup)**
21. **Trạng thái 7 Tầng Kiểm thử hệ thống (Unit, Integration, Business, E2E, Perf, Security, Reliability)**
22. **Quy trình Quản lý nhánh Git 4 Công cụ (Git CLI + SSH Key + GitHub CLI `gh` + MCP)**
23. **Quy trình CI/CD 8 Bước (GitHub Actions / Jenkins — Dev tự động, Prod duyệt PR thủ công)**
24. **Tối ưu hóa Docker & Container (Multi-stage build cắt giảm 90% dung lượng Image)**
25. **Chiến lược Triển khai Không gián đoạn (Zero-Downtime: Rolling / Blue-Green / Canary)**
26. **Phân tích Chi phí vận hành & Tối ưu Token/Cloud (Prompt Caching, Model Routing, Batch API)**
27. **Báo cáo Điểm khuyết & Hạng mục Còn thiếu (`[NOT_FOUND]` Audit & Action Plan)**
