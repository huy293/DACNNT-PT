# Xây Dựng Mô Hình Đa Phương Thức Nhằm Phát Hiện Quảng Cáo Số Gây Hại Dựa Trên Văn Bản – Hình Ảnh

Dự án Công nghệ Thông tin kết hợp **Transfer Learning (OpenAI CLIP + Classifier)**, **FastAPI Backend (`POST /predict`)** và **Tiện ích mở rộng trình duyệt Chrome/Edge (Manifest V3)** để tự động phát hiện, làm mờ (`filter: blur(10px)`) và cảnh báo các quảng cáo số gây hại theo thời gian thực.

---

## 1. Cấu Trúc Dự Án Theo 5 Giai Đoạn Thực Hiện

| Giai đoạn | Hạng mục công việc | Tệp mã nguồn tương ứng |
| :--- | :--- | :--- |
| **Giai đoạn 1 (Tuần 1)** | Chốt dữ liệu & Viết script Tiền xử lý / EDA (kiểm tra số lượng ảnh, độ dài text, tỷ lệ lệch nhãn) | - [`src/mocks/sample_ads_dataset.json`](./src/mocks/sample_ads_dataset.json)<br/>- [`src/features/dataset_eda/preprocess_eda.py`](./src/features/dataset_eda/preprocess_eda.py)<br/>- [`src/mocks/eda_report.json`](./src/mocks/eda_report.json) |
| **Giai đoạn 2 (Tuần 2–3)** | Trích xuất đặc trưng bằng **OpenAI CLIP**, nối (Concatenate) 2 vector Ảnh + Text ra `features.csv` và huấn luyện **Classifier** (`.pkl`, Accuracy > 75%) | - [`src/features/clip_extractor/extract_features.py`](./src/features/clip_extractor/extract_features.py)<br/>- [`src/features/clip_extractor/kaggle_notebook_pipeline.py`](./src/features/clip_extractor/kaggle_notebook_pipeline.py)<br/>- [`src/features/classifier/train_classifier.py`](./src/features/classifier/train_classifier.py)<br/>- [`src/server/models/harmful_ad_classifier.pkl`](./src/server/models/harmful_ad_classifier.pkl) |
| **Giai đoạn 3 (Tuần 4–5)** | Hiện thực hóa **Backend API (`POST /predict`)** trả về `{"is_harmful": true, "confidence": 0.89}` và đóng gói triển khai Cloud (HuggingFace Spaces / Render) | - [`src/app/main.py`](./src/app/main.py)<br/>- [`src/server/inference_service.py`](./src/server/inference_service.py)<br/>- [`src/server/http_gateway.py`](./src/server/http_gateway.py)<br/>- [`Dockerfile`](./Dockerfile) & [`requirements.txt`](./requirements.txt) |
| **Giai đoạn 4 (Tuần 6–7)** | Xây dựng **Chrome/Edge Extension** (`manifest.json`, `content.js`, `popup/`) tự động quét thẻ `<img>` + `<p>`/`<span>`, gọi API, làm mờ `blur(10px)` và gắn nút `"Quảng cáo này có thể chứa nội dung độc hại. Nhấp để xem"` | - [`src/features/extension/manifest.json`](./src/features/extension/manifest.json)<br/>- [`src/features/extension/content.js`](./src/features/extension/content.js)<br/>- [`src/features/extension/background.js`](./src/features/extension/background.js)<br/>- [`src/features/extension/popup/popup.html`](./src/features/extension/popup/popup.html)<br/>- [`src/app/demo/index.html`](./src/app/demo/index.html) |
| **Giai đoạn 5 (Tuần 8)** | Tài liệu Kiến trúc hệ thống, Sơ đồ luồng dữ liệu & Môi trường quay Video Demo bảo vệ | - [`docs/technical/ARCHITECTURE_PLAN.md`](./docs/technical/ARCHITECTURE_PLAN.md)<br/>- [`docs/product/BUSINESS_FLOW.md`](./docs/product/BUSINESS_FLOW.md) |

---

## 2. Hướng Dẫn Chạy Nhanh Ngay Trên Máy (Không Cần Cài Thư Viện Nặng)

Hệ thống được tích hợp cơ chế **Dual-Engine**: chạy được ngay lập tức bằng Python chuẩn trên máy tính của bạn mà không cần tải hàng GB thư viện, đồng thời tự động nâng cấp lên `FastAPI` + `HuggingFace CLIP` khi cài đầy đủ `requirements.txt` hoặc chạy trên Kaggle/HuggingFace Spaces.

### Bước 1: Chạy Giai đoạn 1 (EDA) & Giai đoạn 2 (Trích xuất đặc trưng + Huấn luyện model)
```powershell
python -m src.features.dataset_eda.preprocess_eda
python -m src.features.clip_extractor.extract_features
python -m src.features.classifier.train_classifier
```

### Bước 2: Khởi động Backend API (Giai đoạn 3) & Trang Web Demo
```powershell
python -m src.app.main
```
Sau khi chạy lệnh trên:
- **Endpoint dự đoán:** `POST http://127.0.0.1:8000/predict`
- **Endpoint kiểm tra sức khỏe:** `GET http://127.0.0.1:8000/healthz`
- **Trang mạng xã hội & báo điện tử giả lập (có sẵn 6 quảng cáo để test & quay video):** Mở trình duyệt tại `http://127.0.0.1:8000/demo`

### Bước 3: Cài đặt Tiện ích mở rộng lên Chrome hoặc Microsoft Edge (Giai đoạn 4)
1. Mở trình duyệt Chrome truy cập `chrome://extensions/` (hoặc Edge truy cập `edge://extensions/`).
2. Bật công tắc **Chế độ dành cho nhà phát triển (Developer mode)** ở góc trên bên phải.
3. Nhấn nút **Tải tiện ích đã giải nén (Load unpacked)**.
4. Chọn thư mục: `D:\Projects\DACNTT\src\features\extension`
5. Mở trang `http://127.0.0.1:8000/demo` (hoặc bất kỳ trang báo/mạng xã hội nào):
   - Các quảng cáo độc hại sẽ tự động bị làm mờ `filter: blur(10px)` kèm nút bấm: **"Quảng cáo này có thể chứa nội dung độc hại. Nhấp để xem"**.
   - Nhấp vào biểu tượng tiện ích **AdShield AI** trên thanh công cụ trình duyệt để xem thống kê số quảng cáo đã quét, số quảng cáo độc hại đã chặn và cấu hình URL API.

### Bước 4: Chạy bộ Kiểm thử Tự động (15 bài test)
```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```
