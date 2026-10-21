---
trigger: always_on
description: Kỷ luật tối ưu hóa Token, chống đọc file lan man và cơ chế Fast-Track Bypass cho chỉnh sửa nhỏ
---

# RULE 05: TOKEN GUARD & FAST-TRACK PROTOCOL (LUÔN KÍCH HOẠT)

## 1. Nguyên Tắc Phối Hợp Công Cụ Để Tiết Kiệm 70%+ Token
1. **Không lạm dụng MCP cho tác vụ Local:**
   - Dùng **CLI** (`git`, `gh`, `npm`, `docker`) cho các thao tác cục bộ (gần như tốn `0` token nền).
   - Dùng **Skills** (`.claude/skills/`) để nạp quy trình chuyên môn theo ngữ cảnh (chỉ đọc tên + 1 dòng mô tả, khi trúng tác vụ mới mở file).
   - Dùng **Commands** (`.claude/commands/`) cho các biểu mẫu dài (`/architecture-plan`, `/clean-room`, `/context-handoff`) để không bao giờ tốn token nền khi chưa gọi lệnh.
   - Chỉ dùng **MCP Server** khi cần kết nối dữ liệu từ xa có kiểm soát quyền hạn (RBAC/OAuth) và Audit Log.
2. **Chống Quét File Mù Quáng:**
   - Cấm đọc toàn bộ các thư mục sinh tự động (`node_modules/`, `dist/`, `.next/`, `build/`, `coverage/`, file log hàng chục nghìn dòng).
   - Tra cứu đúng thư mục mục tiêu thông qua bản đồ `AGENTS.md` và `docs/technical/ARCHITECTURE_PLAN.md` trước khi mở file.

## 2. Cơ Chế Phân Luồng Tác Vụ (Full Workflow vs Fast-Track Bypass)
- **Luồng Chuẩn (Full 6-Step Workflow):** Áp dụng khi xây mới tính năng, thiết kế hệ thống hoặc tái cấu trúc module (`>= 50 dòng code` hoặc thay đổi DB/API). Bắt buộc đi qua: Kiểm tra `BUSINESS_FLOW.md` $\rightarrow$ `ROADMAP.md` $\rightarrow$ Phân tích 3 chiều (Pros/Cons/Mitigation) + Option Matrix $\rightarrow$ Code $\rightarrow$ Kiểm thử $\rightarrow$ Cập nhật `ARCHITECTURE_PLAN.md` & `CHANGELOG.md`.
- **Luồng Fast-Track Bypass (`< 50 dòng code`, hotfix giao diện, sửa lỗi cục bộ không đổi kiến trúc):**
  - Bỏ qua bước vẽ sơ đồ Mermaid dài dòng và không cần quét lại toàn bộ 27 mục kiến trúc.
  - Nêu giải pháp trực diện trong 1–2 câu $\rightarrow$ Sửa tận gốc tại đoạn code lỗi (`replace_file_content`) $\rightarrow$ Chạy kiểm tra kiểu tĩnh (`tsc --noEmit`) & Unit Test của hàm đó $\rightarrow$ Báo cáo ngắn gọn.

## 3. Bàn Giao Sạch Khi Hội Thoại Dài (`Context Handoff`)
- Khi ngữ cảnh phiên làm việc vượt quá 60–70% giới hạn token hoặc khi hoàn thành xong 1 Sprint lớn, chủ động đề xuất người dùng gõ `/context-handoff giao` để nén toàn bộ trạng thái vào `docs/ops/HANDOFF.md` (loại bỏ 80% nhiễu hội thoại) trước khi mở phiên mới.
