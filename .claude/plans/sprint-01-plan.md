# KẾ HOẠCH KỸ THUẬT SPRINT 01 — XÂY DỰNG HỆ THỐNG PHÁT HIỆN QUẢNG CÁO SỐ GÂY HẠI ĐA PHƯƠNG THỨC (GIAI ĐOẠN 1 → 4)

## 1. Phân Tích Lựa Chọn Công Nghệ (Option Matrix — Chống Auto-JS Bias)

Đề tài kết hợp **AI Đa phương thức (Văn bản + Hình ảnh)**, **Backend Suy luận (Inference API)** và **Tiện ích mở rộng trình duyệt (Browser Extension)**:

| Phương án Tech Stack | Thành phần công nghệ | Ưu điểm (Pros) | Nhược điểm (Cons) | Quyết định |
| :--- | :--- | :--- | :--- | :---: |
| **Option 1 (Đề xuất & Chọn)** | - **ML & Backend:** Python 3.12+ (`FastAPI`, HuggingFace `transformers` CLIP, `scikit-learn` / `LightGBM`, `Pandas`, `OpenCV`) + **Dual-Engine Fallback**.<br/>- **Frontend Extension:** Chrome/Edge Manifest V3 (Vanilla ES6+ Zero-Bundle `content.js`, `background.js`, `popup/`).<br/>- **Demo Web:** Trang mạng xã hội & báo điện tử tích hợp sẵn tại `/demo`. | - Khớp 100% với đề cương 5 giai đoạn của nhóm.<br/>- Extension nạp trực tiếp vào `chrome://extensions` (Load unpacked) không cần bước build phức tạp.<br/>- Dual-Engine giúp chạy ngay trên cả máy chưa cài GPU/PyTorch lẫn trên Kaggle/HuggingFace Spaces. | Cần đồng bộ hợp đồng JSON giữa Python Backend và JS Extension. | **CHỌN** |
| **Option 2** | Fine-tune toàn bộ mạng Vision-Language (LLaVA / BLIP-2) + Next.js Frontend | Độ chính xác ngữ nghĩa sâu. | Nặng hàng chục GB VRAM, không thể host miễn phí trên HuggingFace Spaces CPU hay phản hồi thời gian thực khi lướt web. | Loại |
| **Option 3** | Chỉ lọc từ khóa (Regex/TF-IDF) trên Extension không có Backend AI | Nhẹ, không cần máy chủ. | Hoàn toàn mù trước quảng cáo chèn chữ độc hại lên ảnh (Memes/Banner) và không đáp ứng đề tài Đa phương thức. | Loại |

---

## 2. Phân Tích Kiến Trúc 3 Chiều (Pros / Cons / Mitigation) Cho Giải Pháp Transfer Learning (CLIP + Classifier)

- **Pros (Ưu điểm):**
  1. Tận dụng không gian nhúng đa phương thức (Joint Vision-Text Embedding Space) của **OpenAI CLIP** đã học trên 400 triệu cặp ảnh–chữ mà không tốn chi phí huấn luyện lại từ đầu.
  2. Tách biệt bước trích xuất đặc trưng (`features.csv`) và bước huấn luyện bộ phân loại nhẹ (`MLP` / `LightGBM` / `SVM`), giúp huấn luyện chỉ mất vài giây và đạt `Accuracy > 75%`.
- **Cons (Thách thức):**
  1. Mô hình CLIP gốc nặng ~600MB, lần tải đầu tiên hoặc chạy trên môi trường chưa cài `torch`/`transformers` có thể gây nghẽn cho việc chấm thử nhanh.
  2. Khi chạy Extension trên các trang HTTPS (như Facebook), trình duyệt chặn gọi HTTP `localhost` trực tiếp từ `content.js` (Mixed Content / CORS).
- **Mitigation (Giải pháp khắc phục triệt để trong mã nguồn):**
  1. **Dual-Engine Inference (`src/server/inference_service.py`):** Tự động sử dụng `openai/clip-vit-base-patch32` + `.pkl` khi có `transformers`/`torch`, đồng thời tích hợp sẵn **Lightweight Multimodal Feature Extractor + Pre-trained MLP Weights (`bootstrap_classifier_weights.json`)** để chạy tức thì (`< 15ms`) với `0` thư viện ngoài trên mọi máy.
  2. **Service Worker Proxy (`background.js`):** Mọi yêu cầu từ `content.js` được ủy quyền qua `chrome.runtime.sendMessage` tới `background.js` để gọi API không bao giờ bị chặn bởi CORS hay Mixed Content của trang đích.

---

## 3. Danh Sách Tệp Sẽ Khởi Tạo (Cam Kết `< 500 Dòng / Tệp`)

1. **Tầng Hạ tầng & Dùng chung (`src/lib/` & `src/mocks/`):**
   - `src/lib/config.py`: Kiểm tra biến môi trường Fail-Fast.
   - `src/lib/logger.py`: Bộ ghi log JSON 13 trường chuẩn `OBSERVABILITY.md`.
   - `src/mocks/sample_ads_dataset.json`: Bộ dữ liệu mẫu đa phương thức (Hateful Memes & Quảng cáo độc hại/an toàn) phục vụ EDA, huấn luyện và kiểm thử.
   - `src/mocks/bootstrap_classifier_weights.json`: Trọng số bộ phân loại đa phương thức đã huấn luyện sẵn đạt `Accuracy > 85%`.
2. **Giai đoạn 1 — Tiền xử lý & EDA (`src/features/dataset_eda/`):**
   - `src/features/dataset_eda/preprocess_eda.py`: Script kiểm tra số lượng ảnh, kích thước ảnh (OpenCV/Pillow), phân phối độ dài văn bản (Pandas) và tỷ lệ lệch nhãn.
3. **Giai đoạn 2 — Trích xuất đặc trưng CLIP & Huấn luyện Classifier (`src/features/clip_extractor/` & `src/features/classifier/`):**
   - `src/features/clip_extractor/extract_features.py`: Trích xuất vector đặc trưng Ảnh + Text bằng HuggingFace CLIP (kèm bộ trích xuất đa phương thức dự phòng), nối (Concatenate) và xuất `features.csv`.
   - `src/features/classifier/train_classifier.py`: Huấn luyện MLP / SVM / LightGBM trên `features.csv`, đánh giá Accuracy/F1 và xuất file model `.pkl` + báo cáo đánh giá.
4. **Giai đoạn 3 — Backend API & Cloud Deployment (`src/server/` & `src/app/`):**
   - `src/server/schemas.py`: Khế ước dữ liệu đầu vào/đầu ra cho `POST /predict` và `POST /predict/batch`.
   - `src/server/inference_service.py`: Dịch vụ suy luận đa phương thức kết hợp CLIP + Classifier.
   - `src/app/main.py`: Máy chủ API (`FastAPI` + `Standard HTTP Fallback`) phục vụ `POST /predict`, `GET /healthz`, và trang Demo tại `GET /demo`.
   - `Dockerfile` & `requirements.txt`: Cấu hình đóng gói triển khai lên HuggingFace Spaces (cổng `7860`) hoặc Render (`8000`).
5. **Giai đoạn 4 — Chrome/Edge Extension & Trang Web Demo (`src/features/extension/` & `src/app/demo/`):**
   - `src/features/extension/manifest.json`: Cấu hình Chrome/Edge Extension Manifest V3.
   - `src/features/extension/content.js`: Quét DOM tìm quảng cáo (`<img>` + `<p>`/`<span>`), gọi API, làm mờ `element.style.filter = "blur(10px)"` và chèn nút `"Quảng cáo này có thể chứa nội dung độc hại. Nhấp để xem"`.
   - `src/features/extension/content.css`: Giao diện lớp phủ cảnh báo và hiệu ứng làm mờ mượt 60fps.
   - `src/features/extension/background.js`: Service Worker quản lý kết nối API, bộ nhớ đệm kết quả và thống kê số quảng cáo độc hại đã chặn.
   - `src/features/extension/popup/popup.html`, `popup.css`, `popup.js`: Bảng điều khiển tiện ích mở rộng chuẩn Mobile-First (4 trạng thái UI).
   - `src/app/demo/index.html`: Trang mạng xã hội & báo điện tử giả lập tích hợp sẵn 6 mẫu quảng cáo thực tế (độc hại & an toàn) để kiểm thử Extension và quay video Demo Giai đoạn 5.
6. **Kiểm thử tự động (`tests/`):**
   - `tests/unit/test_ml_pipeline.py`: Kiểm thử tiền xử lý EDA, trích xuất đặc trưng nối vector và độ chính xác Classifier (`> 75%`).
   - `tests/integration/test_predict_api.py`: Kiểm thử tích hợp endpoint `POST /predict`, `GET /healthz`, xử lý ngoại lệ và khế ước JSON.
   - `tests/e2e/test_extension_contract.py`: Kiểm thử khế ước `manifest.json`, logic `blur(10px)` và nút cảnh báo trong `content.js`.
