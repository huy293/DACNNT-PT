---
trigger: always_on
description: Cổng kiểm soát quyền hạn, cấm lệnh hủy diệt, bảo vệ môi trường Production và chấm điểm phản xạ JEV
---

# RULE 04: PERMISSION GATE & JEV REFLEX SECURITY (LUÔN KÍCH HOẠT)

## 1. Danh Sách Tệp Chỉ Đọc & Vùng Cấm Tuyệt Đối (Read-Only Blacklist)
1. **Tệp khóa mật khẩu & môi trường thực tế:** `.env`, `.env.local`, `.env.production`, `*.pem`, `*.key`. AI chỉ được phép đọc/sửa trên tệp mẫu `.env.example`.
2. **Tệp Lockfile:** `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `Cargo.lock` (chỉ cập nhật thông qua CLI của trình quản lý gói).
3. **Lịch sử Migration đã chạy:** Các tệp migration cũ trong `prisma/migrations/` hoặc `drizzle/migrations/` (cấm sửa tệp cũ, chỉ tạo migration mới theo chuẩn Expand & Contract).

## 2. Danh Sách Lệnh Hủy Diệt Bị Cấm Vĩnh Viễn
- **Git:** Cấm `git push --force`, `git push -f`, `git reset --hard`, `git clean -fd` trên toàn bộ kho mã nguồn. Cấm AI tự ý merge hoặc deploy thẳng lên nhánh `production`/`main` khi chưa có bước con người bấm **Approve PR**.
- **Hệ điều hành:** Cấm `rm -rf /`, `Remove-Item -Recurse -Force` trên thư mục gốc dự án.
- **Cơ sở dữ liệu:** Cấm `DROP DATABASE`, `TRUNCATE TABLE`, `prisma migrate reset`, `drizzle-kit push --force`. Dữ liệu kinh doanh quan trọng bắt buộc dùng **Soft Delete** (`deleted_at`) + **Audit Log**.

## 3. Bộ Phản Xạ Chấm Điểm Rủi Ro JEV (Risk Scoring Middleware `0.0 – 1.0`)
Trước khi thực thi bất kỳ thao tác ghi/xóa/gọi công cụ nhạy cảm nào (đặc biệt qua CLI hoặc MCP), AI phải tự đánh giá theo 3 ngưỡng điểm rủi ro JEV:
- **Ngưỡng Xanh (`Score 0.00 – 0.30` — An toàn / Read-only):** Đọc tài liệu, chạy test, tạo nhánh local, sửa code trong phạm vi module được giao $\rightarrow$ **Cho phép thực thi ngay (`ALLOW`)**.
- **Ngưỡng Vàng (`Score 0.31 – 0.70` — Thay đổi cấu trúc / Write nhạy cảm):** Cài thêm thư viện bên thứ 3, thêm migration DB, thay đổi cấu hình Docker/CI-CD, ghi dữ liệu qua MCP $\rightarrow$ **Bắt buộc hỏi xác nhận người dùng kèm phân tích Pros/Cons (`ASK_CONFIRMATION`)**.
- **Ngưỡng Đỏ (`Score 0.71 – 1.00` — Nguy hiểm / Môi trường Production):** Can thiệp DB thật, xóa dữ liệu hàng loạt, lộ API key, bỏ qua bước kiểm thử để ép deploy Prod $\rightarrow$ **Chặn đứng ngay lập tức (`BLOCK`)**.
