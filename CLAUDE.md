# CLAUDE.md — Project Navigation & Operating Contract

> Tệp này được liên kết đồng bộ với [`AGENTS.md`](./AGENTS.md) để đảm bảo **Claude Code**, **Antigravity**, **Cursor** và **Codex** đều đọc chung một nguồn sự thật duy nhất (Single Source of Truth) ngay khi khởi tạo phiên làm việc.

## 1. Thứ Tự Đọc Ngữ Cảnh Khi Mở Phiên Mới
1. Đọc [`AGENTS.md`](./AGENTS.md) để nắm cấu trúc Unified Component-First 3 tầng (`src/`, `tests/`, `docs/`).
2. Nạp các quy tắc bất biến trong [`.claude/rules/`](./.claude/rules/).
3. Kiểm tra tiến độ hiện tại trong [`docs/ROADMAP.md`](./docs/ROADMAP.md) và tệp bàn giao [`docs/ops/HANDOFF.md`](./docs/ops/HANDOFF.md) (nếu tiếp tục công việc từ Agent trước).

## 2. Bảng Ánh Xạ Nhanh Các Tệp `.md` Trọng Tâm

| Nhu cầu thực tế | Tệp `.md` hoặc Lệnh cần dùng |
| :--- | :--- |
| Chuyển ý tưởng thô thành đặc tả nghiệp vụ | [`docs/product/BUSINESS_FLOW.md`](./docs/product/BUSINESS_FLOW.md) |
| Xem bảng Kanban đặc tả trực quan trên trình duyệt | [`docs/product/visual-spec.html`](./docs/product/visual-spec.html) |
| Kiểm soát danh sách tính năng theo Sprint (chống quên) | [`docs/ROADMAP.md`](./docs/ROADMAP.md) |
| Quét & xem toàn cảnh 27 phần kiến trúc hệ thống | Lệnh `/architecture-plan` $\rightarrow$ [`docs/technical/ARCHITECTURE_PLAN.md`](./docs/technical/ARCHITECTURE_PLAN.md) |
| Bàn giao công việc sang phiên Agent mới không mất context | Lệnh `/context-handoff` $\rightarrow$ [`docs/ops/HANDOFF.md`](./docs/ops/HANDOFF.md) |
| Viết lại tính năng cũ theo chuẩn Clean-Room (REA + JEV) | Lệnh `/clean-room` $\rightarrow$ [`docs/specs/SPEC.md`](./docs/specs/SPEC.md) |
| Kiểm thử 7 tầng & Pentest bảo mật trước khi deploy | [`docs/qa/QA_TESTING.md`](./docs/qa/QA_TESTING.md) & [`docs/qa/PENTEST_REPORT.md`](./docs/qa/PENTEST_REPORT.md) |
| Quy trình Git 4 công cụ & CI/CD Zero-Downtime | [`docs/ops/GIT_WORKFLOW.md`](./docs/ops/GIT_WORKFLOW.md) & [`docs/ops/CICD_PIPELINE.md`](./docs/ops/CICD_PIPELINE.md) |
