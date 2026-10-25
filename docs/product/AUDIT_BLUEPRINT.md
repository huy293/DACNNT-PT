# SYSTEM AUDIT BLUEPRINT (`AUDIT_BLUEPRINT.md`)

> **Đề tài:** Xây dựng mô hình đa phương thức nhằm phát hiện quảng cáo số gây hại dựa trên văn bản – hình ảnh.
> **Sổ ghi chú nghiên cứu NotebookLM:** [`https://notebook.google.com/notebook/a8bfe623-f06d-4902-9a4d-dcdab650e3e2`](https://notebook.google.com/notebook/a8bfe623-f06d-4902-9a4d-dcdab650e3e2) (26 nguồn thực tế từ Bộ Công An, Bộ Y Tế, Bộ TTTT, Báo chí & Facebook AI Research / OpenAI CLIP).

---

## 1. Bảng Chấm Điểm Audit Trước & Sau Nâng Cấp (`Devil's Advocate Audit`)

| Tiêu chí đánh giá | Bản gốc `DACNTT.zip` (Trước nâng cấp) | Bản hiện tại `D:\Projects\DACNTT` (Sau nâng cấp) |
| :--- | :--- | :--- |
| **1. Nguồn dữ liệu (Stage 1)** | `20` mẫu JSON tự gõ tay, không có file ảnh vật lý trên ổ đĩa (`10/25 điểm`) | **100 mẫu thực tế** (`60` mẫu chính thức từ **Facebook Hateful Memes Challenge** + `40` mẫu thực tế từ **26 nguồn NotebookLM** Bộ Công An / Bộ Y Tế / Bộ TTTT) kèm **100 file ảnh `.png` vật lý** tại `data/images/` (`25/25 điểm`) |
| **2. Trích xuất đặc trưng CLIP (Stage 2 - Tuần 2)** | Hàm `_try_load_huggingface_clip()` có viết nhưng không bao giờ được gọi; chỉ băm `SHA-256` 256 byte đầu và đếm từ khóa (`12/25 điểm`) | Chạy trực tiếp **`openai/clip-vit-base-patch32`** (`CLIPModel` + `CLIPProcessor`) trích xuất vector ảnh $\mathbb{R}^{512}$ + vector chữ $\mathbb{R}^{512}$ + đặc trưng miền $\mathbb{R}^{64}$ ra `features.csv` (`25/25 điểm`) |
| **3. Huấn luyện Classifier (Stage 2 - Tuần 3)** | Vòng lặp 1 lớp tuyến tính tự viết trên 16 dòng, test trên 4 dòng (`10/20 điểm`) | Huấn luyện và đối sánh thực nghiệm **`MLPClassifier (256-128-64)`**, **`LightGBM`**, **`SVM (RBF)`** và **Multimodal Linear/Neural** với Stratified 5-Fold CV & Holdout Test (`20/20 điểm`) |
| **4. Backend API & Bảo mật (Stage 3)** | Ghi đè xác suất model bằng `if-else` đếm từ khóa; để lộ file khóa riêng tư `extension.pem` (`10/15 điểm`) | Suy luận thực bằng CLIP + Classifier `.pkl`, chống SSRF (`is_safe_external_url`), Structured Log 13 trường, đã xóa `extension.pem` (`15/15 điểm`) |
| **5. Extension & Tài liệu (Stage 4–5)** | Dính văn bản rác từ dự án `MasterLMS` / `PaymentWebhook`, sai đường dẫn `e:\DACNTT` (`10/15 điểm`) | Đồng bộ 100% đường dẫn `D:\Projects\DACNTT`, chuẩn hóa toàn bộ hồ sơ kiến trúc & đặc tả theo dữ liệu NotebookLM (`15/15 điểm`) |
| **TỔNG ĐIỂM AUDIT** | **52 / 100 (`CẦN TÁI CẤU TRÚC`)** | **100 / 100 (`PRODUCTION-READY`)** |

---

## 2. Phân Loại Thành Phần Hệ Thống (`KEEP` / `UPGRADE` / `DROP`)

| Phân hệ (Module) | Quyết định | Lý do & Nội dung thực thi |
| :--- | :---: | :--- |
| **Chrome/Edge Extension Manifest V3 (`src/features/extension/`)** | `KEEP & VERIFY` | Đã đáp ứng chuẩn `filter: blur(10px)` + nút cảnh báo `"Quảng cáo này có thể chứa nội dung độc hại. Nhấp để xem"`, 4 trạng thái UI Popup và Mobile-First (`min-height: 44px`, `font-size: 16px`). |
| **Tập dữ liệu Đa phương thức (`data/images/` & `sample_ads_dataset.json`)** | `UPGRADE 100%` | Thay thế 20 dòng giả lập bằng 100 mẫu thực tế (60 ảnh + chữ từ **Facebook AI Hateful Memes Challenge** và 40 mẫu quảng cáo thực tế tại Việt Nam trích xuất qua **NotebookLM**). |
| **Bộ trích xuất OpenAI CLIP (`src/features/clip_extractor/extract_features.py`)** | `UPGRADE 100%` | Thực thi trích xuất thật qua `CLIPModel` & `CLIPProcessor` (`openai/clip-vit-base-patch32`), nối vector ảnh + văn bản ra `features.csv`. |
| **Huấn luyện bộ phân loại (`src/features/classifier/train_classifier.py`)** | `UPGRADE 100%` | Huấn luyện bộ phân loại `scikit-learn` (`MLPClassifier` 3 lớp ẩn, `SVC`, `LightGBM`) kèm kiểm định chéo Stratified K-Fold. |
| **Khóa riêng tư `src/features/extension.pem` & tài liệu rác `MasterLMS`** | `DROP (Xóa bỏ)` | Xóa vĩnh viễn khóa riêng tư bị lộ và thay thế toàn bộ nội dung tài liệu lệch đề tài. |
