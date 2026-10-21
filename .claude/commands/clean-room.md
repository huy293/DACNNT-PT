---
description: Quy trình tái cấu trúc độc lập Clean-Room (REA đọc hành vi xuất SPEC.md -> JEV duyệt bằng chứng -> Opus xây lại không nhìn code gốc -> Haiku tạo 3 bản lỗi kiểm chứng)
---

# COMMAND: `/clean-room` — Quy Trình Xây Dựng Lại Độc Lập (Clean-Room Rebuild)

> **Định luật Clean-Room trong 1 câu:** *"Model thấy code gốc thì không bao giờ được viết code, và model viết code thì không bao giờ được thấy code gốc!"* (Ngăn chặn triệt để việc AI copy lại bug cũ, nợ kỹ thuật và logic đoán mò khi refactor tính năng).

Khi người dùng kích hoạt `/clean-room [FEATURE] [APP]`, hệ thống thực thi nghiêm ngặt theo 6 bước phân vai:

## Bước 1: REA — Điều Tra & Trích Xuất Đặc Tả Có Bằng Chứng (`docs/specs/SPEC.md`)
- Agent đóng vai **REA (Reverse Engineering Analyst)** đọc và kiểm tra tính năng `[FEATURE]` trong ứng dụng `[APP]`.
- Ghi lại toàn bộ quy tắc nghiệp vụ, trạng thái đầu vào/đầu ra và xử lý ngoại lệ vào tệp `docs/specs/SPEC.md`.
- **Yêu cầu bắt buộc:** Mỗi quy tắc (`RULE-01`, `RULE-02`...) phải đi kèm **Bằng chứng xác thực (Evidence)** thu thập được (dòng code/binary offset, log runtime, network trace hoặc test case thực tế). Không suy đoán những hành vi không có bằng chứng.

## Bước 2: JEV — Kiểm Duyệt Bằng Chứng Khắt Khe (Evidence Gatekeeper)
- Bộ phản xạ **JEV** xét duyệt độc lập từng quy tắc trong `docs/specs/SPEC.md`:
  - Chấm điểm xác thực (`0.0 – 1.0`) dựa trên bằng chứng của REA.
  - Bất kỳ quy tắc nào thiếu bằng chứng hoặc mô tả mơ hồ (`Score < 0.85`) đều bị đánh nhãn `REJECTED` và trả về Bước 1 để REA điều tra bổ sung.
  - Chỉ giữ lại các quy tắc đạt chuẩn `APPROVED`.

## Bước 3: Cổng Dừng Xác Nhận Của Con Người (Mandatory Human Gate)
- Hiển thị tệp `docs/specs/SPEC.md` đã qua JEV lọc để người dùng kiểm tra.
- **TUYỆT ĐỐI KHÔNG** bắt đầu viết code xây dựng lại cho đến khi người dùng gõ lệnh xác nhận: **"BẮT ĐẦU"** (hoặc **"DUYỆT"**).

## Bước 4: Opus Builder — Xây Dựng Lại Từ Đầu Trong Phiên Sạch (Blind Rebuild)
- Khởi tạo một Subagent hoặc phiên làm việc hoàn toàn mới (**Opus Builder**), **CHỈ** cung cấp duy nhất tệp `docs/specs/SPEC.md` (và `docs/design/DESIGN.md` nếu có UI).
- **CẤM TUYỆT ĐỐI** mở, đọc hoặc tham khảo mã nguồn cũ của tính năng đó. Xây dựng lại tính năng mới tinh, sạch nợ kỹ thuật 100% bám theo `SPEC.md`.

## Bước 5: Haiku Tester — Kiểm Thử Đột Biến Với 3 Phiên Bản Cố Tình Làm Hỏng (Mutation Testing)
- Khởi tạo **Haiku Tester** viết bộ bài kiểm thử toàn diện cho toàn bộ các `RULE` trong `docs/specs/SPEC.md`.
- Đồng thời tạo ra **3 phiên bản cố tình gắn lỗi (Mutants 1, 2, 3)** trong thư mục tạm để kiểm chứng độ sắc bén của bộ test (nếu bản hỏng mà vẫn pass test nghĩa là bài test vô dụng, phải viết lại test).

## Bước 6: Duy Trì Thực Thi Cho Tới Khi Đạt Chuẩn Tuyệt Đối (`/goal` Gate)
- Duy trì vòng kiểm tra cho đến khi thỏa mãn đồng thời 2 điều kiện:
  1. Phiên bản xây dựng lại của Opus **VƯỢT QUA 100%** toàn bộ bài kiểm thử.
  2. Cả **3 phiên bản cố tình chứa lỗi (Mutants)** đều bị bộ kiểm thử phát hiện và **ĐÁNH TRƯỢT 100%**.
- Những trường hợp kiểm thử ranh giới chưa rõ ràng được chuyển lại cho Opus xử lý và ký duyệt trước khi xuất xưởng.
