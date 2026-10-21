---
name: clean-room-rebuild
description: Tái cấu trúc hoặc xây dựng lại tính năng theo chuẩn Clean-Room (REA trích xuất SPEC.md kèm bằng chứng -> JEV duyệt -> Opus rebuild mù không nhìn code cũ -> Haiku tạo 3 bản lỗi Mutation Testing)
---

# SKILL: Clean-Room Feature Rebuild (REA + JEV + Opus + Haiku)

## 1. Khi Nào Kích Hoạt Kỹ Năng Này?
Kích hoạt khi cần viết lại (refactor/rebuild) một tính năng cũ đang bị rối hoặc nhiều nợ kỹ thuật mà muốn **tuyệt đối không copy lại bug cũ hay logic đoán mò**.

## 2. Nguyên Tắc Bất Biến
> *"Model thấy code gốc thì không bao giờ được viết code, và model viết code thì không bao giờ được thấy code gốc!"*

## 3. Quy Trình Thực Thi 6 Bước
1. **REA (Analyst):** Quét mã nguồn/binary của tính năng cũ, trích xuất toàn bộ quy tắc ra `docs/specs/SPEC.md`. Mỗi `RULE-XX` bắt buộc đính kèm **Evidence** (tên file, dòng lệnh, log runtime, network trace).
2. **JEV (Verifier):** Kiểm tra từng quy tắc trong `docs/specs/SPEC.md`. Quy tắc nào không có bằng chứng cụ thể bị trả về REA ngay lập tức.
3. **Human Gate:** Trình bày `docs/specs/SPEC.md` cho người dùng và dừng chờ lệnh **"BẮT ĐẦU"**.
4. **Opus (Clean Builder):** Mở một Subagent mới chỉ nhận `docs/specs/SPEC.md` (cấm đọc thư mục code cũ) để viết lại tính năng mới sạch 100%.
5. **Haiku (Mutation Tester):** Viết bộ kiểm thử tự động cho toàn bộ `RULE` trong `SPEC.md`, đồng thời tạo ra **3 phiên bản cố tình gắn lỗi (Mutants 1, 2, 3)**.
6. **Exit Criteria (`/goal`):** Chỉ hoàn tất khi bản Rebuild **PASS 100%** bộ test VÀ cả 3 bản Mutant đều bị bộ test bắt lỗi (**FAIL 100%**).
