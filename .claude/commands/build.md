---
description: Chuyển hóa đặc tả nghiệp vụ BUSINESS_FLOW.md và ROADMAP.md thành mã nguồn hoàn chỉnh theo từng Sprint
---

# COMMAND: `/build` — Triển Khai Tính Năng Theo Sprint Chuẩn Vibe Coding

Khi người dùng kích hoạt lệnh `/build` (kèm tên tính năng, mã Sprint hoặc đường dẫn `@docs/product/BUSINESS_FLOW.md`), AI bắt buộc thực hiện tuần tự 6 bước sau:

## Bước 1: Đọc & Khóa Phạm Vi Ngữ Cảnh (Context Lock)
1. Đọc `docs/ROADMAP.md` để xác định danh sách các tính năng thuộc Sprint hiện tại (tối đa **5–10 tính năng/đợt**).
2. Đọc `docs/product/BUSINESS_FLOW.md` để nắm rõ:
   - Mã quy trình (`BF-XXX`)
   - Tác nhân thực hiện (`Actor`: Guest / User / Admin / System)
   - Luồng sự kiện chính và các Quy tắc nghiệp vụ (`Business Rules`).
3. Đọc `docs/design/DESIGN.md` và `docs/technical/ARCHITECTURE_PLAN.md` để xác định đúng phân khu cần can thiệp (`frontend/user`, `frontend/admin`, `frontend/landing-page`, `backend/`, `infra/`, `mcp/`).

## Bước 2: Lập Kế Hoạch Kỹ Thuật Vào `.claude/plans/`
- Trước khi viết code, xuất hoặc cập nhật bản kế hoạch kỹ thuật ngắn gọn tại `.claude/plans/current-sprint-plan.md` gồm:
  - Danh sách User Stories sẽ triển khai trong đợt này.
  - Danh sách tệp sẽ tạo mới hoặc chỉnh sửa (kèm giới hạn `< 500 dòng/tệp`).
  - Phân tích 3 chiều (Pros - Cons - Mitigation) nếu có quyết định kiến trúc quan trọng.

## Bước 3: Tách Nhánh Git Cục Bộ (Branch Isolation)
- Kiểm tra nhánh hiện tại bằng `git status` / `git branch`.
- Nếu đang ở `main` hoặc `production`, lập tức tạo nhánh riêng: `git checkout -b feat/<ma-sprint-hoac-tinh-nang>`.

## Bước 4: Triển Khai Mã Nguồn (Code Execution)
- Thực thi theo thứ tự từ dưới lên:
  1. **`infra/`**: Cập nhật schema DB (Migration an toàn Expand-Contract) & Redis keys nếu có.
  2. **`backend/`**: Xây dựng DTO validation (Zod), Service xử lý Business Rules, Controller & Route có phân quyền RBAC.
  3. **`frontend/`**: Xây dựng UI Primitives $\rightarrow$ Feature Components (đủ 4 trạng thái `Loading`, `Error`, `Empty`, `Success`, chuẩn Mobile-First) $\rightarrow$ Page Orchestrator.
- Tuyệt đối không dùng bình luận giữ chỗ (`// TODO`, `// ...`).

## Bước 5: Kiểm Thử Tự Động & Đối Soát (Verification)
- Chạy kiểm tra kiểu tĩnh (`tsc --noEmit`), Linter và bộ Unit/Integration/Business Flow Test tương ứng với các quy tắc trong `BUSINESS_FLOW.md`.

## Bước 6: Ký Duyệt Chữ Ký Tài Liệu (Signatures Update)
1. Cập nhật tiến độ trong `docs/ROADMAP.md` (chuyển tính năng đã xong xuống mục **5. Đã Hoàn Thành & Sẵn Sàng Kiểm Thử**).
2. Cập nhật `docs/technical/ARCHITECTURE_PLAN.md` nếu có thêm route/bảng/module mới.
3. Ghi nhận phiên bản vào `docs/CHANGELOG.md` và dừng lại chờ người dùng xác nhận (`Confirm`) trước khi chuyển sang Sprint tiếp theo.
