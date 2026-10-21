# PROJECT ROADMAP & SPRINT TRACKER (`ROADMAP.md`)

> **Đề tài:** Xây dựng mô hình đa phương thức nhằm phát hiện quảng cáo số gây hại dựa trên văn bản – hình ảnh
> - Tuân thủ `.agents/rules/roadmap-signature.md`: Cập nhật đầy đủ 5 phần sau khi hoàn thành và kiểm thử tự động Giai đoạn 1 $\rightarrow$ Giai đoạn 4.

---

## 1. Tiến Độ Tổng Thể (Overall Progress)

| Chỉ số | Giá trị hiện tại |
| :--- | :--- |
| **Phiên bản hiện tại (Current Version)** | `v1.0.0` |
| **Sprint đang thực thi** | `Sprint 01 — Hoàn thiện Giai đoạn 1 → Giai đoạn 4 (End-to-End)` |
| **Tổng số tính năng đã hoàn thành** | `10 / 12 tính năng (83.3%)` |
| **Trạng thái kiểm thử QA (`unittest` / `pytest`)** | `15 / 15 Tests PASS (100%)` |

---

## 2. Việc Còn Lại Cần Làm (Remaining Backlog — Giai đoạn 5: Tuần 8)

### Giai Đoạn 5 — Đóng Gói Báo Cáo, Quay Video Demo & Bảo Vệ Đồ Án (Tuần 8)
- [ ] `[FEAT-011]` Quay Video Demo 3–5 phút: Bật tiện ích `AdShield AI` trên Chrome/Edge $\rightarrow$ Mở trang `/demo` (hoặc trang tin tức) $\rightarrow$ Trình diễn quảng cáo độc hại tự động bị làm mờ `blur(10px)` kèm nút `"Quảng cáo này có thể chứa nội dung độc hại. Nhấp để xem"`.
- [ ] `[FEAT-012]` Hoàn thiện Slide thuyết trình bảo vệ đồ án dựa trên sơ đồ kiến trúc tại [`docs/technical/ARCHITECTURE_PLAN.md`](./technical/ARCHITECTURE_PLAN.md).

---

## 3. Thứ Tự Ưu Tiên Trong Sprint Hiện Tại (Current Sprint 01 Priority Matrix)

| Thứ tự | Mã tính năng | Tên tính năng (Bám sát kế hoạch 5 giai đoạn) | Phân khu (`Folder`) | Độ ưu tiên | Trạng thái |
| :---: | :--- | :--- | :--- | :---: | :--- |
| 1 | `FEAT-001` | **[GĐ 1 - Tuần 1]** Bộ dữ liệu mẫu Hateful Memes & Quảng cáo đa phương thức | `src/mocks/` | `P0 - Critical` | `DONE` |
| 2 | `FEAT-002` | **[GĐ 1 - Tuần 1]** Script Tiền xử lý & EDA (Pandas + OpenCV kiểm tra số ảnh, độ dài text, lệch nhãn) | `src/features/dataset_eda/` | `P0 - Critical` | `DONE` |
| 3 | `FEAT-003` | **[GĐ 2 - Tuần 2]** Trích xuất đặc trưng bằng Transfer Learning (`openai/clip-vit-base-patch32` + nối vector xuất `features.csv`) | `src/features/clip_extractor/` | `P0 - Critical` | `DONE` |
| 4 | `FEAT-004` | **[GĐ 2 - Tuần 3]** Huấn luyện Classifier (`MLP` / `SVM` / `LightGBM`) trên `features.csv` đạt `Accuracy > 75%` và xuất `.pkl` | `src/features/classifier/` | `P0 - Critical` | `DONE` |
| 5 | `FEAT-005` | **[GĐ 3 - Tuần 4]** Backend API `POST /predict` (FastAPI + Standard HTTP Fallback) trả về `{"is_harmful": true, "confidence": 0.89}` | `src/server/` + `src/app/` | `P0 - Critical` | `DONE` |
| 6 | `FEAT-006` | **[GĐ 3 - Tuần 5]** Đóng gói Multi-stage `Dockerfile` & `requirements.txt` sẵn sàng deploy HuggingFace Spaces / Render | `Dockerfile` | `P1 - High` | `DONE` |
| 7 | `FEAT-007` | **[GĐ 4 - Tuần 6]** Khởi tạo Chrome/Edge Extension Manifest V3 (`manifest.json`, `background.js`, `content.js`) quét thẻ `<img>` + `<p>`/`<span>` | `src/features/extension/` | `P0 - Critical` | `DONE` |
| 8 | `FEAT-008` | **[GĐ 4 - Tuần 7]** Tích hợp API vào `content.js`, làm mờ `element.style.filter = "blur(10px)"` và chèn nút `"Quảng cáo này có thể chứa nội dung độc hại. Nhấp để xem"` | `src/features/extension/` | `P0 - Critical` | `DONE` |
| 9 | `FEAT-009` | **[GĐ 4 - Tuần 7]** Giao diện Popup điều khiển tiện ích (đủ 4 trạng thái UI: Loading, Error, Empty, Success) | `src/features/extension/popup/` | `P1 - High` | `DONE` |
| 10 | `FEAT-010` | **[GĐ 4 & 5]** Trang Web mạng xã hội & báo điện tử giả lập (`GET /demo`) tích hợp 6 mẫu quảng cáo để kiểm thử & quay video | `src/app/demo/` | `P1 - High` | `DONE` |

---

## 4. Tính Năng Mới Bổ Sung (New Feature Requests / Change Requests)

- [x] `[CR-001]` Bổ sung cơ chế **Dual-Engine Fallback** (chạy được cả khi máy chưa cài `torch`/`transformers` lẫn khi chạy trên Kaggle GPU) và trang Web Demo `/demo` tích hợp sẵn *(Đã hoàn thành trong `v1.0.0`)*.

---

## 5. Đã Hoàn Thành & Sẵn Sàng Kiểm Thử (Completed & Verified — `v1.0.0`)

- [x] `[FEAT-001]` Bộ dữ liệu mẫu đa phương thức [`src/mocks/sample_ads_dataset.json`](../src/mocks/sample_ads_dataset.json) (`v1.0.0`).
- [x] `[FEAT-002]` Script EDA kiểm tra ảnh, độ dài văn bản và lệch nhãn [`src/features/dataset_eda/preprocess_eda.py`](../src/features/dataset_eda/preprocess_eda.py) (`v1.0.0`).
- [x] `[FEAT-003]` Trích xuất đặc trưng nối vector Ảnh + Text xuất `features.csv` [`src/features/clip_extractor/extract_features.py`](../src/features/clip_extractor/extract_features.py) & script Kaggle [`kaggle_notebook_pipeline.py`](../src/features/clip_extractor/kaggle_notebook_pipeline.py) (`v1.0.0`).
- [x] `[FEAT-004]` Huấn luyện bộ phân loại đạt `Accuracy = 100% (> 75%)` và lưu `.pkl` [`src/features/classifier/train_classifier.py`](../src/features/classifier/train_classifier.py) (`v1.0.0`).
- [x] `[FEAT-005]` Backend API `POST /predict`, `POST /predict/batch`, `GET /healthz` kèm Log JSON 13 trường [`src/app/main.py`](../src/app/main.py) & [`src/server/inference_service.py`](../src/server/inference_service.py) (`v1.0.0`).
- [x] `[FEAT-006]` Cấu hình triển khai Cloud (`Dockerfile` Multi-stage + `requirements.txt`) (`v1.0.0`).
- [x] `[FEAT-007]` Chrome/Edge Extension Manifest V3 [`src/features/extension/manifest.json`](../src/features/extension/manifest.json) (`v1.0.0`).
- [x] `[FEAT-008]` Logic quét DOM, gọi API, làm mờ `blur(10px)` và nút cảnh báo tương tác [`src/features/extension/content.js`](../src/features/extension/content.js) (`v1.0.0`).
- [x] `[FEAT-009]` Giao diện Popup 4 trạng thái chuẩn Mobile-First [`src/features/extension/popup/popup.html`](../src/features/extension/popup/popup.html) (`v1.0.0`).
- [x] `[FEAT-010]` Cổng thông tin thử nghiệm trực quan [`src/app/demo/index.html`](../src/app/demo/index.html) & 15 bài kiểm thử tự động trong [`tests/`](../tests/) (`v1.0.0`).
