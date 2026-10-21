---
name: docker-3-skills
description: Bộ 3 kỹ năng Docker cho dự án AI-Native: Multi-stage Dockerfile giảm 90% dung lượng (1.2GB xuống 120MB), Docker Compose mạng nội bộ cô lập, và Container Registry CI/CD
---

# SKILL: Bộ 3 Kỹ Năng Docker Cho Dự Án Production

## 1. Khi Nào Kích Hoạt Kỹ Năng Này?
Kích hoạt khi đóng gói ứng dụng (`frontend/`, `backend/`, `mcp/`) hoặc thiết lập hạ tầng trong `infra/`.

## 2. Ba Trụ Cột Thực Thi
1. **Kỹ năng 1 — Multi-Stage Build Cắt Giảm 90% Dung Lượng Image:**
   - Tách rõ các stage: `deps` (cài đặt thư viện) $\rightarrow$ `builder` (biên dịch TypeScript/Next.js standalone) $\rightarrow$ `runner` (chỉ copy file build cuối cùng trên nền `alpine` hoặc `distroless`).
   - Luôn chạy bằng tài khoản non-root (`USER node` / `USER appuser`) và có `.dockerignore` loại bỏ `node_modules`, `.git`, `docs/`, `.env`.
2. **Kỹ năng 2 — Docker Compose & Mạng Nội Bộ Cô Lập (`Internal LAN Isolation`):**
   - Chỉ duy nhất **Nginx API Gateway** được mở cổng ra ngoài (`80`/`443`).
   - Toàn bộ `backend`, `postgres`, `redis`, `minio`, `prometheus`, `loki` phải nằm trong mạng nội bộ Docker (`internal_net`), không phơi port trực tiếp ra Internet trên VPS Production.
   - Bắt buộc khai báo `healthcheck`, `restart: unless-stopped` và giới hạn tài nguyên (`mem_limit`, `cpus`) cho từng container.
3. **Kỹ năng 3 — Container Registry & Semantic Tagging:**
   - Đóng gói và đẩy Image lên GitHub Container Registry (`ghcr.io`) hoặc Docker Hub kèm 2 nhãn: nhãn phiên bản (`v1.1.0`) và nhãn commit (`sha-xxxxxxx`) để có thể rollback về bản cũ trong 1 lệnh duy nhất.
