# CHANGELOG — Lịch Sử Phiên Bản (`CHANGELOG.md`)

## [`v1.0.1`] — 2026-10-23 (Cải tiến cách ly số liệu quét và huy hiệu số đếm theo từng Tab)

### Fixed (`Sửa lỗi`)
- **`[Extension - Badge & Stats Per-Tab Isolation]`**:
  - Tách bộ đếm thống kê (`tabStats`) và huy hiệu đỏ (`chrome.action.setBadgeText({ text, tabId })`) độc lập theo từng Tab thay vì dùng biến toàn cục tích lũy.
  - Tự động xóa/đặt lại số đếm về 0 khi người dùng chuyển hướng trang web mới (`chrome.tabs.onUpdated` với trạng thái `loading` hoặc `url`), giải quyết dứt điểm hiện tượng số quảng cáo bị cộng dồn lên 92 khi duyệt qua nhiều trang.
  - Thêm thông điệp `ADSHIELD_PAGE_INIT` và `ADSHIELD_RESET_TAB_STATS` khi [`content.js`](../src/features/extension/content.js) khởi động trên trang mới hoặc khi người dùng bấm quét lại.
  - Cập nhật [`popup.js`](../src/features/extension/popup/popup.js) chỉ truy xuất và hiển thị số liệu của Tab đang hoạt động (`activeTab.id`).

## [`v1.0.0`] — 2026-10-22 (Hoàn thiện trọn gói Giai đoạn 1 → Giai đoạn 4)

### Added (`Tính năng mới`)
- **`[Giai đoạn 1 - Dataset & EDA]`**:
  - Khởi tạo bộ dữ liệu mẫu đa phương thức [`src/mocks/sample_ads_dataset.json`](../src/mocks/sample_ads_dataset.json) (20 mẫu quảng cáo cờ bạc, thuốc giả, lừa đảo tài chính, hateful memes và quảng cáo thương mại an toàn).
  - Xây dựng script tiền xử lý & thống kê dữ liệu [`src/features/dataset_eda/preprocess_eda.py`](../src/features/dataset_eda/preprocess_eda.py) xuất báo cáo [`src/mocks/eda_report.json`](../src/mocks/eda_report.json).
- **`[Giai đoạn 2 - Transfer Learning (CLIP + Classifier)]`**:
  - Xây dựng bộ trích xuất đặc trưng nối vector Ảnh + Văn bản [`src/features/clip_extractor/extract_features.py`](../src/features/clip_extractor/extract_features.py) xuất [`src/mocks/features.csv`](../src/mocks/features.csv) và script chạy trên Kaggle [`src/features/clip_extractor/kaggle_notebook_pipeline.py`](../src/features/clip_extractor/kaggle_notebook_pipeline.py).
  - Xây dựng quy trình huấn luyện Classifier [`src/features/classifier/train_classifier.py`](../src/features/classifier/train_classifier.py) đạt `Accuracy > 75%` và lưu mô hình tại [`src/server/models/harmful_ad_classifier.pkl`](../src/server/models/harmful_ad_classifier.pkl).
- **`[Giai đoạn 3 - Backend API & Cloud Deployment]`**:
  - Xây dựng dịch vụ suy luận [`src/server/inference_service.py`](../src/server/inference_service.py) và cổng HTTP/FastAPI [`src/app/main.py`](../src/app/main.py) cung cấp endpoint `POST /predict`, `POST /predict/batch`, `GET /healthz`.
  - Đóng gói [`Dockerfile`](../Dockerfile) Multi-stage và [`requirements.txt`](../requirements.txt) sẵn sàng đưa lên HuggingFace Spaces hoặc Render.
- **`[Giai đoạn 4 - Chrome/Edge Browser Extension & Demo Portal]`**:
  - Hoàn thiện tiện ích mở rộng trình duyệt Manifest V3 tại [`src/features/extension/`](../src/features/extension/) (`manifest.json`, `background.js`, `content.js`, `content.css`, `popup/`).
  - Tự động làm mờ quảng cáo độc hại bằng `element.style.filter = "blur(10px)"` và hiển thị nút bấm `"Quảng cáo này có thể chứa nội dung độc hại. Nhấp để xem"`.
  - Xây dựng cổng thông tin thử nghiệm trực quan [`src/app/demo/index.html`](../src/app/demo/index.html) phục vụ kiểm thử và quay video bảo vệ Giai đoạn 5.
