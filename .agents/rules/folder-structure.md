---
trigger: always_on
description: Quy hoạch cấu trúc Component-First 3 tầng (src/) và quy tắc lưu trữ tài liệu .md trong docs/
---

# RULE 01: COMPONENT-FIRST FOLDER STRUCTURE & MODULE ISOLATION (LUÔN KÍCH HOẠT)

## 1. Kiến Trúc Thống Nhất `src/` (Chống Phân Mảnh Monorepo Thừa Thãi)
Tuyệt đối không tự ý xé nhỏ dự án thành nhiều sub-repo rời rạc (`frontend/landing-page`, `frontend/user`, `frontend/admin`) gây trùng lặp `node_modules` và UI components. Toàn bộ mã nguồn tuân thủ **Component-First 3 Tầng** trong `src/`:
1. **`src/components/ui/` (Tầng 1 — UI Primitives / Atoms):** Chứa linh kiện thuần giao diện (`Button`, `Input`, `Modal`, `Skeleton`). Cấm chứa logic nghiệp vụ, gọi API hoặc import DB.
2. **`src/features/<feature>/` (Tầng 2 — Feature Components & Domain Logic):** Chứa `components/`, `hooks/`, `schemas/` (Zod + RHF) xử lý từng nghiệp vụ cụ thể và đảm bảo đủ 4 trạng thái UI (`Loading`, `Error`, `Empty`, `Success`).
3. **`src/app/` (Tầng 3 — Page Orchestrator & Route Groups):**
   - Dùng Route Groups `(marketing)/`, `(portal)/`, `(admin)/` và `api/` để phân tách phân hệ mà vẫn dùng chung 100% UI Primitives & Types.
   - File `page.tsx` **chỉ điều phối (tối đa 50–80 dòng)**, mặc định là Server Component; đẩy `'use client'` xuống tận ngọn lá (Leaf).
4. **`src/server/` & `src/lib/`:** Chứa Services, Repositories, Database Schema/Migrations, Fail-fast Env Validation (Zod) và Structured Logger 13 trường.
5. **`src/mocks/` & `tests/`:** Chứa dữ liệu giả lập cách ly (`*.mock.json`) và kịch bản kiểm thử tự động (Playwright E2E Mobile-First).

## 2. Kỷ Luật Lưu Trữ Tài Liệu `.md` (Chống Rác Thư Mục Gốc)
- **CẤM** tạo file `.md` mới tràn lan ở thư mục gốc (`root`), ngoại trừ `README.md`, `AGENTS.md`, `CLAUDE.md`.
- Khi xuất bất kỳ tài liệu nào, AI bắt buộc xếp đúng vào 6 phân khu trong `docs/`:
  - Tiến độ & Phiên bản: `docs/ROADMAP.md`, `docs/CHANGELOG.md`
  - Nghiệp vụ & Sản phẩm: `docs/product/` (`BUSINESS_FLOW.md`, `AUDIT_BLUEPRINT.md`, `visual-spec.html`)
  - Thiết kế UI/UX: `docs/design/` (`DESIGN.md`)
  - Kỹ thuật & Kiến trúc: `docs/technical/` (`ARCHITECTURE_PLAN.md`, `FEATURE_MCP.md`)
  - Đặc tả Clean-Room: `docs/specs/` (`SPEC.md`)
  - Kiểm thử & Bảo mật: `docs/qa/` (`QA_TESTING.md`, `PENTEST_REPORT.md`)
  - Vận hành, Git, CI/CD & Chuyển giao: `docs/ops/` (`HANDOFF.md`, `GIT_WORKFLOW.md`, `CICD_PIPELINE.md`, `OBSERVABILITY.md`)

## 3. Giới Hạn Độ Dài File & Kỷ Luật Phạm Vi
- Mỗi file code tối đa **500 dòng**. Vượt ngưỡng bắt buộc tách module theo nguyên lý Single Responsibility (SRP).
- Yêu cầu sửa tính năng/component nào thì chỉ can thiệp đúng file/hàm đó (Function-Level Isolation). Cấm tự ý refactor các file lân cận không liên quan.
