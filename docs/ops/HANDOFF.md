# AGENT CONTEXT HANDOFF (`HANDOFF.md`)

> **Dự án:** Xây dựng mô hình đa phương thức nhằm phát hiện quảng cáo số gây hại dựa trên văn bản – hình ảnh (`D:\Projects\DACNTT`).
> **Sổ ghi chú nghiên cứu NotebookLM (39 nguồn thực tế):** [`https://notebook.google.com/notebook/a8bfe623-f06d-4902-9a4d-dcdab650e3e2`](https://notebook.google.com/notebook/a8bfe623-f06d-4902-9a4d-dcdab650e3e2) (ID: `a8bfe623-f06d-4902-9a4d-dcdab650e3e2`).

---

## 1. Trạng Thái Hiện Tại (Current Status)
- **Hoàn thành 100% cả 5 Giai đoạn (Tuần 1 $\rightarrow$ Tuần 8) với quy mô trọn bộ 8.560 bức ảnh chụp thực tế:**
  - **Giai đoạn 1 (EDA & Tiền xử lý):** Bộ dữ liệu thực tế **8.560 mẫu đa phương thức (`3.049` độc hại `label=1` + `5.511` hợp lệ `label=0`)** (`8.500` bức ảnh nguyên bản giải nén từ trọn bộ 7/7 gói Parquet của **Facebook AI Hateful Memes Challenge** `Multimodal-Fatima/HatefulMemes_train` và `60` mẫu quảng cáo thực tế tại Việt Nam thu thập qua **39 nguồn NotebookLM** từ Bộ Công An, Bộ Y Tế, Bộ TTTT, Quốc hội, Nghị định 87/2026/NĐ-CP) cùng **8.560 file ảnh `.png` vật lý** tại `D:\Projects\DACNTT\data\images\`. Đã kiểm định 100% qua `OpenCV` & `Pandas` (`eda_report.json`).
  - **Giai đoạn 2 (Transfer Learning CLIP + Hate-CLIPper Interaction + Classifier):** Trích xuất vector đặc trưng theo lô (`batch_size=128`) bằng **HuggingFace OpenAI CLIP (`openai/clip-vit-base-patch32`)** kết hợp tương tác chéo đa phương thức **Hate-CLIPper** (`Hadamard v_img ⊙ v_txt`, `|v_img - v_txt|`, `cos(v_img, v_txt)`), ngữ nghĩa thị giác `BLIP/CLIP ViT-L/14`, bộ chuẩn hóa chống lách chữ (`deobfuscate_ad_text`) và `EasyOCR` (`vi`, `en`, thu nhỏ ảnh `max_side=640px`), xuất ra `src/mocks/features.csv` (`8.560` mẫu $\times$ `1024` chiều). Huấn luyện cân bằng trọng số lớp và đối sánh thực nghiệm 4 mô hình qua **Holdout Validation (`6.847` train / `1.713` test, `Accuracy = 87.10%`, `F1 = 0.8138`, `ROC-AUC = 0.9489`)**, **5-Fold Stratified Cross-Validation (`8.560` mẫu, `Accuracy = 85.14%`, `ROC-AUC = 0.9256`)** và **Full Dataset (`8.560` mẫu, `Accuracy = 91.39%`, `ROC-AUC = 0.9740`)**, lưu trọng số tại `src/server/models/harmful_ad_classifier.pkl`.
  - **Giai đoạn 3 (Backend FastAPI `POST /predict` & `/data/images/*.png`):** Phục vụ `POST /predict` (tích hợp **SHA-256 LRU Cache 512 mục**), `POST /predict/batch`, `GET /healthz`, `GET /demo`, `GET /data/images/<name>.png`, tích hợp chống SSRF và Structured JSON Log 13 trường.
  - **Giai đoạn 4 (Chrome/Edge Extension Manifest V3):** Tiện ích tại `D:\Projects\DACNTT\src\features\extension` sẵn sàng nạp qua `chrome://extensions/` (`Load unpacked`), tích hợp `"all_frames": true`, đọc ảnh lazy-load (`data-src`/`srcset`) và `blob:` (qua `<canvas>`), khóa chống đua lệnh `data-adshield-state="inflight"`, **Circuit Breaker** (tạm ngắt 5s sau 3 lỗi mạng liên tiếp), tự động làm mờ `filter: blur(10px)` và hiển thị nút `"Quảng cáo này có thể chứa nội dung độc hại. Nhấp để xem"`.
  - **Giai đoạn 5 (Tài liệu Bảo vệ & Kiểm toán):** Đã chuẩn hóa toàn bộ hồ sơ kiến trúc, đặc tả và báo cáo kiểm thử.

---

## 2. Việc Đang Dở (In-Progress Work)
- Không còn hạng mục mã nguồn nào tồn đọng. Toàn bộ 8.560 file ảnh trong `data/images/` đã được giải nén và trích xuất `CLIP` đầy đủ.

---

## 3. Quyết Định Kỹ Thuật Quan Trọng (Key Technical Decisions)
1. **Giải nén trọn bộ 8.500 bức ảnh chụp nguyên bản từ 7/7 gói Parquet `Multimodal-Fatima/HatefulMemes_train` + 60 mẫu thực tế Việt Nam từ 39 nguồn NotebookLM (= 8.560 mẫu):** Xử lý tỷ lệ lệch nhãn tự nhiên của Facebook Hateful Memes (`35.62%` độc hại vs `64.38%` lành tính, `imbalance_ratio = 1.807`) bằng trọng số cân bằng lớp trong quá trình huấn luyện.
2. **Tương tác chéo đa phương thức `Hate-CLIPper` (`Kumar & Nandakumar, EMNLP 2022`):** Tính tích Hadamard $v_{\text{img}} \odot v_{\text{txt}}$, độ lệch tuyệt đối $|v_{\text{img}} - v_{\text{txt}}|$ và độ tương đồng Cosine giữa 2 nhánh `OpenAI CLIP ViT-B/32`, kết hợp đặc trưng thị giác OpenCV và từ điển song ngữ.
3. **Đánh giá 5-Fold Stratified Cross-Validation & ROC-AUC:** Đối sánh khách quan 4 kiến trúc (`MLP_NeuralNet_128_64`, `SVM_LinearKernel`, `LightGBM_Classifier`, `MultimodalLinearL2`) trên toàn bộ 8.560 mẫu.

---

## 4. Danh Sách Tệp Đã Chạm (Touched Files)
- [`src/mocks/sample_ads_dataset.json`](../../src/mocks/sample_ads_dataset.json) & `data/images/*.png` (8.560 ảnh chụp thực tế)
- [`src/features/dataset_eda/preprocess_eda.py`](../../src/features/dataset_eda/preprocess_eda.py) & [`src/mocks/eda_report.json`](../../src/mocks/eda_report.json)
- [`src/features/clip_extractor/extract_features.py`](../../src/features/clip_extractor/extract_features.py) & [`src/mocks/features.csv`](../../src/mocks/features.csv)
- [`src/features/classifier/train_classifier.py`](../../src/features/classifier/train_classifier.py), [`src/server/models/harmful_ad_classifier.pkl`](../../src/server/models/harmful_ad_classifier.pkl) & [`src/server/models/model_metrics.json`](../../src/server/models/model_metrics.json)
- [`src/server/http_gateway.py`](../../src/server/http_gateway.py), [`src/app/main.py`](../../src/app/main.py), [`src/app/demo/index.html`](../../src/app/demo/index.html)
- [`docs/product/notebooklm_raw_synthesis.txt`](../product/notebooklm_raw_synthesis.txt), [`docs/product/AUDIT_BLUEPRINT.md`](../product/AUDIT_BLUEPRINT.md), [`docs/specs/SPEC.md`](../specs/SPEC.md), [`docs/qa/PENTEST_REPORT.md`](../qa/PENTEST_REPORT.md), [`README.md`](../../README.md)

---

## 5. Rào Cản / Blocker Hiện Tại (Blockers)
- `None` (0 Blocker).

---

## 6. Ba Bước Tiếp Theo (Next 3 Immediate Steps)
1. Khởi chạy máy chủ Backend API bằng lệnh `python -m src.app.main` tại `D:\Projects\DACNTT`.
2. Mở trình duyệt Chrome/Edge tại `chrome://extensions/` $\rightarrow$ bật **Developer mode** $\rightarrow$ nhấn **Load unpacked** và trỏ tới `D:\Projects\DACNTT\src\features\extension`.
3. Truy cập `http://127.0.0.1:8000/demo` (hiển thị ảnh `.png` thực tế từ `/data/images/*.png`) để trình diễn trực tiếp hoặc quay video bảo vệ đồ án.
