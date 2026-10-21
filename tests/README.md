# Automated Testing Workspace (`tests/`)

Thư mục này chứa toàn bộ kịch bản kiểm thử tự động đối chiếu với [`docs/qa/QA_TESTING.md`](../docs/qa/QA_TESTING.md):

```text
tests/
├── e2e/                    # Playwright E2E Tests (Mobile 375x812 chạy trước, Desktop chạy sau)
├── integration/            # Kiểm thử API Endpoints, DB Transactions & Idempotency
└── unit/                   # Kiểm thử hàm nghiệp vụ thuần, công thức tính toán & Zod Schemas
```

## Kỷ Luật Bắt Buộc Cho Subagent QA
1. **Khế Ước `data-testid`:** Bắt buộc định vị phần tử theo cấu trúc `[feature]__[component]--[type]` (VD: `auth__submit--btn`). Cấm bắt theo class CSS/Tailwind dễ gãy.
2. **Cấm Sửa Code `src/` Để Ép Test Pass:** Khi phát hiện lỗi, Subagent QA ghi nhận báo cáo để sửa tận gốc logic, tuyệt đối không xóa assertion hoặc hạ chuẩn test.
