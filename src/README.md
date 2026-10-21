# Unified Source Code Architecture (`src/`)

Thư mục `src/` được thiết kế theo chuẩn **Component-First 3 Tầng Đồng Nhất**, loại bỏ hoàn toàn sự cồng kềnh và trùng lặp của mô hình tách nhiều repo/monorepo rời rạc:

```text
src/
├── components/
│   └── ui/                 # TẦNG 1: UI Primitives (Button, Input, Modal, Skeleton - thuần giao diện)
├── features/               # TẦNG 2: Feature Modules theo nghiệp vụ (auth, billing, dashboard...)
│   └── <feature>/
│       ├── components/     # Feature UI (xử lý đủ 4 trạng thái: Loading, Error, Empty, Success)
│       ├── hooks/          # Custom hooks (có cleanup tránh rò rỉ RAM)
│       └── schemas/        # Zod validation schemas & TypeScript contracts
├── app/                    # TẦNG 3: Page Orchestrator (< 80 dòng/file, mặc định Server Component)
│   ├── (marketing)/        # Landing Page, Blog, SEO-first pages
│   ├── (portal)/           # Ứng dụng chính dành cho người dùng cuối
│   ├── (admin)/            # Hệ thống quản trị nội bộ & RBAC
│   └── api/                # API Route Handlers & Webhooks (hỗ trợ Idempotency-Key)
├── server/                 # Backend Services, Repositories, Prisma/Drizzle DB Schema & Migrations
├── lib/                    # Shared Utils, Fail-fast Env Validation (Zod), Structured Logger 13 trường
└── mocks/                  # Dữ liệu giả lập cách ly (*.mock.json) khi phát triển UI độc lập
```

## Kỷ Luật Bắt Buộc Khi Viết Code Trong `src/`
1. **Giới hạn `< 500 dòng/file`:** Vượt ngưỡng phải chủ động tách module theo nguyên lý Đơn nhiệm (SRP).
2. **Colocation hợp lý:** Sub-component nhỏ chỉ dùng cho 1 màn hình và tổng file `< 250 dòng` thì giữ chung file, không xé vụn quá đà.
3. **Đẩy `'use client'` xuống tận ngọn lá (Leaf):** Cấm đặt `'use client'` ở `page.tsx` hoặc `layout.tsx`.
4. **Mobile-First & WCAG 2.1 AA:** Thiết kế cho `360px - 430px` trước, vùng chạm `>= 44x44px`, font input `>= 16px`, dùng `<button type="button">` thay vì `<div onClick>`.
