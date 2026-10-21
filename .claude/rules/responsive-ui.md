---
trigger: always_on
description: Kỷ luật thiết kế giao diện Mobile-First, Touch UX 44x44px, đủ 4 trạng thái UI và đối chiếu Visual Diff 100%
---

# RULE 06: RESPONSIVE UI/UX & VISUAL FIDELITY (LUÔN KÍCH HOẠT)

## 1. Tư Duy Mobile-First & 4 Quy Chuẩn Trải Nghiệm Chạm (Touch UX)
1. **Thiết kế Mobile (`360px – 430px`) trước tiên:** Mọi layout/component phải viết class mặc định cho màn hình nhỏ trước (`w-full flex-col p-4 text-sm`), sau đó mới mở rộng lên Tablet (`md:`) và Desktop (`lg:`). Cấm làm ngược lại gây vỡ giao diện di động.
2. **Touch Target tối thiểu `44x44px`:** Mọi nút bấm, liên kết, biểu tượng tương tác phải có vùng chạm $\ge 44\times 44\text{px}$, khoảng cách giữa 2 nút liền kề $\ge 8\text{px}$.
3. **Chống Safari Auto-Zoom & Hover Trap:**
   - Ô nhập liệu (`input`, `textarea`, `select`) trên mobile bắt buộc có `font-size >= 16px` (`text-base`).
   - Không giấu các thao tác quan trọng bên trong `:hover`. Mọi hành động phải thực hiện được qua thao tác chạm (Tap/Click).
4. **Triệt tiêu tràn ngang (Zero Horizontal Overflow):** 100% trang không được sinh thanh cuộn ngang ngoài ý muốn trên mọi kích thước màn hình.

## 2. Bắt Buộc Đủ 4 Trạng Thái Giao Diện & Chuẩn Semantic HTML
- Mọi thành phần tải dữ liệu từ API bắt buộc xử lý đủ 4 trạng thái:
  1. **`Loading`**: Hiển thị Skeleton khớp kích thước thật (tránh giật bố cục CLS).
  2. **`Error`**: Hiển thị thông báo lỗi thân thiện kèm nút **Thử lại (Retry)**.
  3. **`Empty`**: Hiển thị trạng thái trống rõ ràng kèm nút kêu gọi hành động (**CTA**).
  4. **`Success`**: Hiển thị dữ liệu hoàn chỉnh.
- Sử dụng đúng thẻ HTML ngữ nghĩa: nút bấm dùng `<button type="button">`, điều hướng dùng `<a href>` / `<Link>`. **CẤM** dùng `<div onClick>` hoặc `<span onClick>` thay cho button.

## 3. Quy Trình 7 Bước Chuyển Thiết Kế Sang Code Giống 100%
- Mọi thông số màu sắc, font chữ, khoảng cách, bo góc và đổ bóng phải đọc từ `docs/design/DESIGN.md` (tuyệt đối không tự bịa mã màu cứng rời rạc).
- Sau khi dựng giao diện trên `localhost`, sử dụng **Playwright** chụp ảnh thực tế ở cả 2 khung nhìn Mobile (`375x812`) và Desktop (`1440x900`) để đối chiếu trực quan (Visual Diff) với bản thiết kế trước khi bàn giao.
