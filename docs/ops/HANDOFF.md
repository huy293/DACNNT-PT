# AGENT CONTEXT HANDOFF (`HANDOFF.md`)

> **Hướng dẫn sử dụng (`.claude/commands/context-handoff.md`):**
> - Khi muốn chuyển công việc từ **Agent 1** sang **Agent 2, 3, 4...** mà không bị mất ngữ cảnh hay lặp lại lỗi cũ:
>   1. Ở phiên Agent hiện tại, gõ: `/context-handoff giao` $\rightarrow$ Agent sẽ cập nhật 6 mục dưới đây (loại bỏ 80% rác hội thoại).
>   2. Mở phiên Agent mới, gõ: `/context-handoff nhận @docs/ops/HANDOFF.md` $\rightarrow$ Agent mới nắm trọn vẹn 100% trạng thái chỉ trong vài trăm token.

---

## 1. Mục Tiêu & Tiêu Chí Hoàn Thành (Goal & Definition of Done)
- **Mục tiêu hiện tại:** Hoàn thiện các tính năng thuộc **Sprint 02** trong [`docs/ROADMAP.md`](../ROADMAP.md) (`[FEAT-006]` Phân quyền RBAC và `[FEAT-007]` Thanh toán Webhook IPN chống cộng tiền trùng).
- **Tiêu chí hoàn thành (Definition of Done):**
  1. Code sạch, không vượt quá `500 dòng/tệp`, không dùng bình luận giữ chỗ.
  2. Vượt qua kiểm tra kiểu tĩnh (`tsc --noEmit`) và đạt đủ các tầng kiểm thử trong [`docs/qa/QA_TESTING.md`](../qa/QA_TESTING.md).
  3. Tự động cập nhật trạng thái vào `docs/ROADMAP.md`, `docs/technical/ARCHITECTURE_PLAN.md` và `docs/CHANGELOG.md`.

---

## 2. Ràng Buộc & Điều Cấm Kỵ Tuyệt Đối (Hard Constraints & Boundaries)
- **CẤM** can thiệp hoặc chạy lệnh xóa/reset trên Database Production; chỉ làm việc với dữ liệu `Dummy/Seed` ở môi trường Local/Dev.
- **CẤM** viết code trực tiếp trên nhánh `main` hoặc `production`; bắt buộc làm việc trên nhánh tính năng riêng (`feat/...`).
- **CẤM** báo cáo "Đã hoàn thành" khi chưa chạy kiểm thử thực tế cho phần code vừa viết.

---

## 3. Trạng Thái Môi Trường & Git (Environment & Git State)
- **Thư mục làm việc trọng tâm:** `backend/`, `frontend/user/`, `frontend/admin/`
- **Nhánh Git hiện tại:** `main` *(Khi bắt đầu code tính năng mới, tạo nhánh `feat/sprint-02-rbac-payment`)*
- **Phiên bản cơ sở:** `v0.2.0`
- **Trạng thái dữ liệu:** Đang sử dụng bộ khung đặc tả chuẩn (`BUSINESS_FLOW.md`, `SPEC.md`, `DESIGN.md`).

---

## 4. Tiến Độ Thực Tế Theo Roadmap (Roadmap Progress Status)
- ✅ **Đã hoàn thành & Đã xác minh (`Sprint 01`):**
  - `[FEAT-001 -> FEAT-005]`: Cấu trúc Monorepo, hệ thống `.claude/` 6 thư mục, đặc tả `JWT + Refresh Token + Redis Blacklist` và chống Brute-force.
- ⚠️ **Đang thực hiện / Cần kiểm thử (`Sprint 02`):**
  - `[FEAT-006]`: Phân quyền RBAC đa vai trò (`STUDENT`, `INSTRUCTOR`, `ADMIN`).
  - `[FEAT-007]`: Xử lý Webhook IPN thanh toán theo đặc tả Clean-Room [`docs/specs/SPEC.md`](../specs/SPEC.md).
- ⏳ **Đang chờ phê duyệt / Các đợt tiếp theo (`Sprint 03–04`):**
  - `[FEAT-011 -> FEAT-020]`: MCP Server 5 lớp, Observability 13 trường Log, CI/CD 8 bước.

---

## 5. Quyết Định Kỹ Thuật & Vết Xe Đổ (Decisions & Dead-Ends — CẤM LẶP LẠI)
- ❌ **Cách làm SAI đã loại bỏ (Cấm Agent sau lặp lại):**
  1. *Không* nạp hàng loạt MCP Server nặng cho các thao tác Git/Local vì làm tiêu tốn tới 70% cửa sổ ngữ cảnh (143K/200K token) và làm giảm độ chính xác khi chọn công cụ.
  2. *Không* tin tưởng tổng tiền gửi lên từ phía trình duyệt (`frontend`) hay xử lý Webhook thanh toán mà thiếu khóa phân tán Redis (`SETNX`).
- ✅ **Cách làm ĐÚNG đang áp dụng:**
  1. Kết hợp **CLI** (cho thao tác local `git`, `gh`, `docker`) + **Skills** (nạp theo ngữ cảnh) + **Commands** (chỉ nạp khi gõ `/`) + **MCP 5 lớp** (chỉ dùng cho kết nối dữ liệu từ xa có kiểm soát quyền).
  2. Áp dụng quy trình **Clean-Room** (`SPEC.md` có bằng chứng) cho module thanh toán.

---

## 6. Bằng Chứng & Bước Tiếp Theo Ngay Lập Tức (Evidence & Next Immediate Steps)
- **Bằng chứng hiện có:** Toàn bộ hệ thống tài liệu điều hành `.md` đã được khởi tạo đầy đủ và đồng bộ tại `docs/` và `.claude/`.
- **Bước tiếp theo ngay lập tức cho Agent nhận bàn giao:**
  1. Đọc [`docs/product/BUSINESS_FLOW.md`](../product/BUSINESS_FLOW.md) và [`docs/specs/SPEC.md`](../specs/SPEC.md).
  2. Khi người dùng yêu cầu `/build`, tách nhánh `feat/sprint-02` và triển khai lần lượt `[FEAT-006]` $\rightarrow$ `[FEAT-010]`.
