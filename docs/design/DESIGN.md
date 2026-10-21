# DESIGN SYSTEM CONTRACT (`DESIGN.md`)

> **Vai trò của tệp này:** Đây là hợp đồng thiết kế giao diện duy nhất (Single Source of Truth) cho toàn bộ `frontend/landing-page/`, `frontend/user/` và `frontend/admin/`.
> - Khi chạy quy trình **7 Bước Biến Thiết Kế Thành Code Giống 100%**, AI bắt buộc lấy đúng mã màu, tỷ lệ chữ, khoảng cách và trạng thái tương tác tại đây, kết hợp với [`.claude/rules/responsive-ui.md`](../../.claude/rules/responsive-ui.md).

---

## 1. Hệ Thống Bảng Màu Chuẩn Độ Tương Phản WCAG AA ($\ge 4.5:1$)

| Nhóm màu (Semantic Token) | CSS Variable | Light Mode (Hex) | Dark Mode (Hex) | Mục đích sử dụng |
| :--- | :--- | :--- | :--- | :--- |
| **Background Primary** | `--bg-primary` | `#F8FAFC` | `#0B0F19` | Nền chính của trang |
| **Surface / Card** | `--bg-surface` | `#FFFFFF` | `#111827` | Nền thẻ Card, Bảng, Sidebar, Bottom Sheet |
| **Surface Elevated** | `--bg-elevated` | `#F1F5F9` | `#1F2937` | Nền ô nhập liệu, Hover state, Dropdown |
| **Text Primary** | `--text-primary` | `#0F172A` | `#F9FAFB` | Tiêu đề và nội dung chính |
| **Text Secondary** | `--text-secondary` | `#475569` | `#9CA3AF` | Mô tả phụ, nhãn trường dữ liệu |
| **Brand Accent** | `--color-primary` | `#4F46E5` | `#6366F1` | Nút hành động chính (Primary CTA), Active Tab |
| **Success** | `--color-success` | `#059669` | `#10B981` | Trạng thái hoàn thành, Đã thanh toán (`PAID`) |
| **Warning** | `--color-warning` | `#D97706` | `#F59E0B` | Trạng thái chờ xử lý (`PENDING`), Cảnh báo nhẹ |
| **Danger / Error** | `--color-danger` | `#DC2626` | `#EF4444` | Báo lỗi form, Nút xóa nguy hiểm, Trạng thái `FAILED` |
| **Border Subtle** | `--border-subtle` | `#E2E8F0` | `#374151` | Đường viền phân tách thẻ và bảng (`1px solid`) |

---

## 2. Thang Đo Chữ (Typography Scale) & Chống Tự Động Phóng To Trên iOS

- **Font chữ giao diện (UI Sans):** `'Inter', system-ui, -apple-system, sans-serif`
- **Font chữ kỹ thuật / Mã đơn / Số liệu (Monospace):** `'JetBrains Mono', monospace` (bắt buộc bật `font-variant-numeric: tabular-nums` cho mọi cột giá tiền và bộ đếm).

| Cấp độ chữ | Kích thước Mobile (`Default`) | Kích thước Desktop (`md:`/`lg:`) | Line Height | Font Weight | Quy tắc bắt buộc |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Display / Hero** | `28px` (`1.75rem`) | `40px` (`2.5rem`) | `1.2` | `700 (Bold)` | Không rớt dòng cộc lốc 1 chữ cuối |
| **Page Title (`H1`)** | `22px` (`1.375rem`) | `28px` (`1.75rem`) | `1.3` | `700 (Bold)` | Mỗi trang có đúng 1 thẻ `<h1>` |
| **Section Title (`H2`)** | `18px` (`1.125rem`) | `22px` (`1.375rem`) | `1.35` | `600 (SemiBold)` | Phân tách rõ các khối chức năng |
| **Card Title (`H3`)** | `16px` (`1rem`) | `18px` (`1.125rem`) | `1.4` | `600 (SemiBold)` | Tiêu đề thẻ sản phẩm/khóa học |
| **Body & Form Input** | **`16px` (`1rem`)** | `16px` (`1rem`) | `1.5` | `400 (Regular)` | **Tối thiểu `16px` cho `input`/`select` để Safari không tự zoom** |
| **Caption / Badge** | `12px` (`0.75rem`) | `13px` (`0.8125rem`) | `1.4` | `500 (Medium)` | Chỉ dùng cho nhãn phụ, thời gian |

---

## 3. Khung Nhìn Đáp Ứng (Responsive Breakpoints) & Quy Chuẩn Chạm

1. **Mobile (`360px – 430px` — Thiết kế mặc định):**
   - Bố cục 1 cột (`grid-cols-1`), khoảng đệm trang `16px` (`p-4`).
   - Thanh điều hướng chính đặt ở đáy màn hình (**Bottom Navigation Bar**) trong vùng ngón cái (One-Thumb Zone).
   - Mọi hộp thoại (Modal) tự động chuyển thành **Bottom Sheet** trượt từ đáy lên.
2. **Tablet (`768px – 1024px` — `md:`):**
   - Bố cục 2 cột (`md:grid-cols-2`), khoảng đệm `24px` (`md:p-6`), hiển thị Sidebar thu gọn.
3. **Desktop (`>= 1280px` — `lg:`/`xl:`):**
   - Bố cục 3–4 cột (`lg:grid-cols-3`), chiều rộng nội dung tối đa `1280px` (`max-w-7xl mx-auto`).

---

## 4. Quy Trình 7 Bước Đối Chiếu Giao Diện Giống Thiết Kế 100%

1. **Bước 1:** Trích xuất toàn bộ biến màu sắc, font chữ, bo góc và khoảng cách vào tệp `DESIGN.md` này.
2. **Bước 2:** Kết hợp `DESIGN.md` + `BUSINESS_FLOW.md` để tạo khung giao diện chuẩn cho từng màn hình.
3. **Bước 3:** Xây dựng các thành phần cơ sở (`src/components/ui/`) tuân thủ vùng chạm `44x44px` và `focus-visible:ring-2`.
4. **Bước 4:** Hoàn thiện đủ **4 trạng thái giao diện** (`Loading Skeleton`, `Error + Retry`, `Empty + CTA`, `Success Data`).
5. **Bước 5:** Chạy ứng dụng trên `localhost` và dùng **Playwright** chụp ảnh màn hình ở độ phân giải Mobile (`375x812`) và Desktop (`1440x900`).
6. **Bước 6:** Đặt ảnh chụp `localhost` cạnh ảnh thiết kế mẫu để AI tự kiểm tra lệch khoảng cách, lệch màu hoặc vỡ chữ (Visual Diff).
7. **Bước 7:** Chạy chuỗi `.claude/hooks/animation-upgrade-chain.md` để tinh chỉnh chuyển động mượt 60fps trước khi nghiệm thu.
