---
trigger: always_on
description: Tự động đối chiếu và cập nhật ROADMAP.md + CHANGELOG.md sau mỗi tính năng để chống AI quên việc
---

# RULE 02: ROADMAP SIGNATURE & SPRINT DISCIPLINE (LUÔN KÍCH HOẠT)

## 1. Quy Tắc Chống Quên Tính Năng (Scrum Sprint Control)
- Trước khi bắt đầu code bất kỳ yêu cầu nào, AI **BẮT BUỘC** đọc `docs/ROADMAP.md` để xác định tính năng đang làm thuộc mã nào (`[FEAT-XXX]`) và nằm trong Sprint nào.
- Mỗi đợt thực thi (Sprint), chỉ làm tối đa **5–10 tính năng** theo thứ tự ưu tiên trong mục **3. Thứ Tự Ưu Tiên Trong Sprint Hiện Tại**, sau đó dừng lại báo cáo để người dùng kiểm tra và xác nhận (`Confirm`) trước khi làm đợt tiếp theo.
- **CẤM** chạy vòng lặp tự động vô tận (`/loop` không điểm dừng) khi chưa có xác nhận kiểm thử, tránh đốt sạch token và làm lệch kiến trúc.

## 2. Tự Động Cập Nhật Chữ Ký Roadmap (`roadmap-signature`)
Ngay sau khi hoàn thành code và chạy pass kiểm thử cho một tính năng, AI bắt buộc tự động cập nhật `docs/ROADMAP.md` theo 5 phần:
1. **Tiến Độ Tổng Thể:** Cập nhật lại số lượng tính năng hoàn thành / tổng số (`%`) và mã phiên bản hiện tại.
2. **Việc Còn Lại Cần Làm (Remaining Backlog):** Gỡ tính năng vừa hoàn thành khỏi danh sách tồn đọng.
3. **Thứ Tự Ưu Tiên (Current Sprint Priority):** Chuyển trạng thái từ `IN_PROGRESS` sang `DONE`.
4. **Tính Năng Mới Bổ Sung (New Feature Requests):** Nếu người dùng yêu cầu thêm tính năng mới phát sinh trong lúc trao đổi, phải ghi nhận ngay vào mục 4 trước khi bắt tay vào code.
5. **Đã Hoàn Thành & Sẵn Sàng Kiểm Thử (Completed & Verified):** Đưa tính năng đã xong xuống mục 5 kèm nhãn phiên bản (`vX.Y.Z`) để sẵn sàng cho QA kiểm thử.

## 3. Đồng Bộ Lịch Sử Phiên Bản (`docs/CHANGELOG.md`)
- Mỗi khi chốt xong một nhóm tính năng hoặc sửa lỗi quan trọng, cập nhật ngay vào `docs/CHANGELOG.md` theo chuẩn Semantic Versioning (`v1.0.0`, `v1.1.0`, `v1.1.1`) gắn với từng phân khu (`frontend`, `backend`, `infra`, `mcp`) để phục vụ rollback tức thì khi cần.
