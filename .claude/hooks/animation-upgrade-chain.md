# HOOK: `animation-upgrade-chain` — Chuỗi 5 Bước Quét, Đánh Giá & Nâng Cấp Animation Toàn App

> **Sự kiện kích hoạt (Trigger Event):** Khi hoàn thiện giao diện một trang mới trong `frontend/` hoặc khi người dùng yêu cầu nâng cấp trải nghiệm chuyển động của ứng dụng.

## Chuỗi 5 Bước Thực Thi Liên Hoàn

1. **Bước 1 — Quét Toàn Bộ Giao Diện (`Animation Audit Scan`):**
   - Rà soát các trang và thành phần trong `frontend/` để phát hiện các điểm chuyển trạng thái bị giật cục (vào trang, mở Modal/Bottom Sheet, chuyển Tab, tải Skeleton, thông báo Toast).
2. **Bước 2 — Phân Loại Hiệu Năng Chuyển Động (`Hardware-Accelerated Filter`):**
   - Loại bỏ mọi animation gây tính toán lại bố cục nặng (`width`, `height`, `top`, `left`); chỉ giữ và chuyển sang `transform` (`translate3d`, `scale`) và `opacity` chạy trên GPU 60fps.
3. **Bước 3 — Chuẩn Hóa Thời Lượng & Đường Cong Gia Tốc (`Timing & Easing Tokens`):**
   - Đồng bộ với `docs/design/DESIGN.md`: Micro-interaction (`150ms–200ms`), Chuyển cảnh/Modal (`250ms–350ms`, `cubic-bezier(0.22, 1, 0.36, 1)`).
4. **Bước 4 — Hỗ Trợ Trợ Năng & Thiết Bị Yếu (`Reduced Motion Guard`):**
   - Bắt buộc tôn trọng cấu hình `prefers-reduced-motion: reduce` của hệ điều hành để không gây chóng mặt và tiết kiệm pin trên thiết bị di động.
5. **Bước 5 — Kiểm Chứng Khung Hình Trên Playwright (`Visual & FPS Verification`):**
   - Kiểm tra trên trình duyệt thực tế đảm bảo không phát sinh lỗi tràn ngang (`overflow-x`) hay lệch bố cục (`CLS = 0`) trong suốt quá trình chạy hiệu ứng.
