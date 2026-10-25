# CLEAN-ROOM SPECIFICATION (`SPEC.md`)

> **Đề tài:** Xây dựng mô hình đa phương thức nhằm phát hiện quảng cáo số gây hại dựa trên văn bản – hình ảnh.
> **Nguồn đối chứng thực tế:** Sổ ghi chú **NotebookLM** (`https://notebook.google.com/notebook/a8bfe623-f06d-4902-9a4d-dcdab650e3e2`) gồm 26 tài liệu học thuật và văn bản cảnh báo chính thức từ Bộ Công An, Bộ Y Tế, Bộ TTTT và Facebook AI Research.

---

## 1. Thông Tin Phân Hệ Đặc Tả (Target Feature Metadata)
- **Tên hệ thống (`[SYSTEM]`):** Hệ thống Phát hiện & Làm mờ Quảng cáo Số Gây hại Đa phương thức (`AdShield Multimodal AI`)
- **Phạm vi (`[SCOPE]`):** Giai đoạn 1 (EDA) $\rightarrow$ Giai đoạn 2 (CLIP Transfer Learning + Classifier) $\rightarrow$ Giai đoạn 3 (FastAPI `POST /predict`) $\rightarrow$ Giai đoạn 4 (Chrome/Edge Extension Manifest V3) $\rightarrow$ Giai đoạn 5 (Báo cáo & Demo).
- **Trạng thái kiểm duyệt:** `8/8 Core Business Rules Verified`

---

## 2. Bảng Quy Tắc Nghiệp Vụ & Kỹ Thuật Bắt Buộc (`Verified Rules`)

| Mã Rule | Quy tắc hành vi bắt buộc (Behavior Specification) | Bằng chứng xác thực (Evidence) |
| :--- | :--- | :--- |
| `BR-ML-01` | **Tiền xử lý & Kiểm định ảnh vật lý (Giai đoạn 1):** Mọi mẫu trong tập dữ liệu phải được kiểm tra bằng `OpenCV` (`cv2.imread`) và `Pandas`. Mẫu thiếu văn bản hoặc file ảnh bị hỏng/kích thước $\le 0$ phải bị loại bỏ và ghi vào `rejected_sample_ids` trong `eda_report.json`. | [`preprocess_eda.py`](../../src/features/dataset_eda/preprocess_eda.py) & [`eda_report.json`](../../src/mocks/eda_report.json) |
| `BR-ML-02` | **Trích xuất & Nối Vector Đa phương thức CLIP (Giai đoạn 2 - Tuần 2):** Ảnh và Văn bản được đưa qua mô hình `openai/clip-vit-base-patch32` (`CLIPProcessor` + `CLIPModel`) thu về vector đặc trưng hình ảnh và văn bản, chuẩn hóa L2 và nối (`Concatenate`) thành 1 vector hợp nhất lưu vào `features.csv`. | [`extract_features.py`](../../src/features/clip_extractor/extract_features.py) & [`features.csv`](../../src/mocks/features.csv) |
| `BR-ML-03` | **Huấn luyện & Đánh giá Classifier (Giai đoạn 2 - Tuần 3):** Huấn luyện các mô hình phân loại (`MLP` 2–3 lớp ẩn, `SVM`, `LightGBM`) trên `features.csv`, đánh giá độc lập trên tập kiểm thử phân tầng (Stratified Holdout / Cross-Validation) đạt `Accuracy >= 75%` và xuất mô hình `.pkl`. | [`train_classifier.py`](../../src/features/classifier/train_classifier.py) & [`model_metrics.json`](../../src/server/models/model_metrics.json) |
| `BR-API-01` | **Hợp đồng Endpoint `POST /predict` (Giai đoạn 3 - Tuần 4):** Nhận đầu vào gồm ảnh (file upload `multipart/form-data`, `image_url`, hoặc `image_base64`) và `text`; trả về JSON chứa `{"is_harmful": bool, "confidence": float, "category": str, "reasons": list}`. Nếu cả ảnh và chữ đều rỗng, trả về `HTTP 400`. | [`http_gateway.py`](../../src/server/http_gateway.py) & [`inference_service.py`](../../src/server/inference_service.py) |
| `BR-API-02` | **Chống tấn công SSRF khi tải URL ảnh:** Mọi `image_url` gửi vào `POST /predict` phải được kiểm tra qua `is_safe_external_url()`, chặn tuyệt đối `file://`, `localhost`, `127.0.0.1`, `169.254.169.254` và các dải IP nội bộ RFC1918. | [`inference_service.py`](../../src/server/inference_service.py) & [`test_predict_api.py`](../../tests/integration/test_predict_api.py) |
| `BR-EXT-01` | **Quét DOM Tìm Quảng cáo Đa phương thức (Giai đoạn 4 - Tuần 6):** `content.js` tự động quét các khối chứa thẻ `<img>` đi kèm `<p>`/`<span>`/tiêu đề trên trang web và theo dõi nội dung tải động qua `MutationObserver` (có cơ chế `cleanupListeners` chống rò rỉ bộ nhớ). | [`content.js`](../../src/features/extension/content.js) |
| `BR-EXT-02` | **Làm mờ `blur(10px)` & Nút Cảnh báo Tương tác (Giai đoạn 4 - Tuần 7):** Khi `POST /predict` trả về `{"is_harmful": true}`, `content.js` áp dụng trực tiếp `element.style.filter = "blur(10px)"` và hiển thị nút bấm có nhãn chính xác: `"Quảng cáo này có thể chứa nội dung độc hại. Nhấp để xem"`. | [`content.js`](../../src/features/extension/content.js) & [`test_extension_contract.py`](../../tests/e2e/test_extension_contract.py) |
| `BR-OBS-01` | **Structured JSON Logging 13 Trường:** Mọi sự kiện khởi động, dự đoán và ngoại lệ tại tầng Backend phải ghi log JSON đủ 13 trường chuẩn với thời gian UTC ISO-8601 (`Z`). | [`logger.py`](../../src/lib/logger.py) |
