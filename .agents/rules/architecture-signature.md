---
trigger: always_on
description: Tự động cập nhật chữ ký kiến trúc trong ARCHITECTURE_PLAN.md mỗi khi thêm hoặc sửa module, DB, API
---

# RULE 03: ARCHITECTURE SIGNATURE (LUÔN KÍCH HOẠT)

## 1. Cấm "Đường Ngắn Nhất" Phá Vỡ Kiến Trúc
- AI tuyệt đối không được vì muốn code nhanh mà gộp chung logic Database vào Controller/UI, hoặc gọi thẳng từ Frontend vào Database/Service nội bộ mà bỏ qua lớp API Gateway / Backend API.
- Mọi tính năng mới phải tuân theo đúng luồng kiến trúc đã định nghĩa tại mục 4 (System Architecture Diagram) và mục 6 (Request Journey) trong `docs/technical/ARCHITECTURE_PLAN.md`.

## 2. Cơ Chế Tự Động Cập Nhật Chữ Ký Kiến Trúc (`architecture-signature`)
Khác với lệnh `/architecture-plan` (dùng để quét toàn bộ hệ thống từ đầu), quy tắc `architecture-signature` này **luôn chạy ngầm**:
- Bất kỳ khi nào AI thực hiện một trong các thay đổi sau:
  1. Thêm hoặc đổi tên thư mục/module trong `frontend/`, `backend/`, `infra/`, `mcp/`.
  2. Thêm bảng (Table), cột (Column) hoặc Index mới vào Database.
  3. Thêm hoặc thay đổi Endpoint API, hàng đợi (Queue), Redis key pattern, hoặc MCP Tool.
  4. Thêm thư viện bên thứ ba (Third-party dependency) hoặc biến môi trường (`.env.example`).
- AI **BẮT BUỘC** cập nhật ngay lập tức phần tương ứng trong `docs/technical/ARCHITECTURE_PLAN.md` để tài liệu kiến trúc luôn khớp 100% với mã nguồn thực tế.

## 3. Rà Soát Điểm Khuyết (`NOT_FOUND` Audit)
- Nếu trong quá trình code một module mới mà phát hiện hệ thống chưa có tầng bảo vệ tương ứng (ví dụ: thiếu Rate Limit, thiếu Validation, thiếu Log 13 trường, thiếu Unit/Integration Test), AI phải ghi rõ vào **Mục 27 (`NOT_FOUND` / Điểm khuyết cần bổ sung)** trong `docs/technical/ARCHITECTURE_PLAN.md` để cảnh báo trực diện cho người quản lý dự án.
