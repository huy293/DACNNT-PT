# HOOK: `post-feature-check` — Chuỗi Tự Động Hóa Sau Khi Hoàn Thành Tính Năng

> **Sự kiện kích hoạt (Trigger Event):** Chạy tự động ngay sau khi Dev Agent hoàn tất việc viết code cho một tính năng trong Sprint.

## Chuỗi 5 Bước Thực Thi Liên Hoàn (Zero-Skip Chain)

1. **Bước 1 — Kiểm Tra Kiểu Tĩnh & Cú Pháp (`Static & Lint Gate`):**
   - Chạy kiểm tra kiểu (`tsc --noEmit`) và Linter trên đúng phân khu vừa sửa (`frontend/`, `backend/`, hoặc `mcp/`). Nếu có bất kỳ lỗi gạch đỏ nào, dừng chuỗi và sửa ngay tại gốc.
2. **Bước 2 — Kiểm Tra Bảo Mật Nhanh (`Quick Security Scan`):**
   - Đảm bảo không có khóa bí mật hardcode, không có `console.log` dữ liệu nhạy cảm, và mọi đường dẫn tệp đều được chuẩn hóa chống Path Traversal.
3. **Bước 3 — Đồng Bộ Chữ Ký Kiến Trúc (`Architecture Signature Sync`):**
   - Đối chiếu với `.claude/rules/architecture-signature.md`: nếu có thêm bảng DB, route API hoặc biến môi trường mới, cập nhật ngay vào `docs/technical/ARCHITECTURE_PLAN.md`.
4. **Bước 4 — Đồng Bộ Chữ Ký Tiến Độ (`Roadmap & Changelog Sync`):**
   - Đối chiếu với `.claude/rules/roadmap-signature.md`: đánh dấu trạng thái trong `docs/ROADMAP.md` và cập nhật `docs/CHANGELOG.md`.
5. **Bước 5 — Kích Hoạt Phiên Kiểm Thử Độc Lập (`Notify QA Testing Agent`):**
   - Ghi nhận trạng thái tính năng sang `READY_FOR_QA` để phiên **QA Testing Engineer Agent** chạy tiếp 7 tầng kiểm thử trong `docs/qa/QA_TESTING.md`.
