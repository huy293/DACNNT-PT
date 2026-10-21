# BUSINESS FLOW SPECIFICATION (`BUSINESS_FLOW.md`)

> **Đề tài Dự án Công nghệ Thông tin:** Xây dựng mô hình đa phương thức nhằm phát hiện quảng cáo số gây hại dựa trên văn bản – hình ảnh (Multimodal Harmful Digital Ad Detection based on Text & Image).
> - **Dev Agent** đọc tệp này khi chạy `/build` để triển khai đầy đủ từ Giai đoạn 1 đến Giai đoạn 4.
> - **QA Testing Engineer Agent** đọc tệp này để kiểm thử đối chiếu từng quy tắc nghiệp vụ (`BR-XXX`).

---

## Quy Trình 01: Tiền Xử Lý Dữ Liệu, Trích Xuất Đặc Trưng CLIP & Huấn Luyện Mô Hình (Giai đoạn 1 & 2)

| Thuộc tính | Nội dung đặc tả |
| :--- | :--- |
| **Mã quy trình** | `BF-ML-01` |
| **Tên quy trình** | Kiểm tra dữ liệu (EDA), Trích xuất vector đặc trưng đa phương thức bằng OpenAI CLIP (`features.csv`) và Huấn luyện bộ phân loại (`Classifier`) |
| **Tác nhân (Actors)** | - `Data Scientist / ML Engineer` (Chạy script trên Kaggle Notebook hoặc máy cục bộ)<br/>- `ML Pipeline` (Pandas + OpenCV + HuggingFace CLIP + Scikit-learn/LightGBM/PyTorch) |
| **Phân khu liên quan** | `src/features/dataset_eda/`, `src/features/clip_extractor/`, `src/features/classifier/`, `src/mocks/` |

### 1. Luồng Sự Kiện Chính (Main Success Scenario)
1. **Tiền xử lý & EDA (Giai đoạn 1 - Tuần 1):**
   - Đọc bộ dữ liệu **Hateful Memes Challenge** (Facebook) hoặc bộ dữ liệu quảng cáo đa phương thức (`jsonl` / `csv` + thư mục ảnh).
   - Dùng `Pandas` và `OpenCV` (`Pillow` fallback) thống kê tổng số mẫu, kiểm tra ảnh lỗi/hỏng, phân tích độ dài văn bản (min, max, mean, word count) và tỷ lệ lệch nhãn (`label = 1: Harmful` vs `label = 0: Benign/Safe`).
2. **Trích xuất đặc trưng bằng Transfer Learning (Giai đoạn 2 - Tuần 2):**
   - Tải mô hình pre-trained `openai/clip-vit-base-patch32` từ thư viện `transformers` của HuggingFace.
   - Chạy vòng lặp qua toàn bộ tập dữ liệu: đưa **Ảnh** qua `CLIP Vision Encoder` nhận vector $v_{\text{img}} \in \mathbb{R}^{512}$ (đã chuẩn hóa L2) và đưa **Văn bản** qua `CLIP Text Encoder` nhận vector $v_{\text{txt}} \in \mathbb{R}^{512}$.
   - **Nối (Concatenate)** 2 vector thành 1 vector đa phương thức duy nhất:
     $$v_{\text{fused}} = [v_{\text{img}} \;\Vert\; v_{\text{txt}}] \in \mathbb{R}^{1024}$$
   - Lưu toàn bộ các vector đặc trưng kèm nhãn `label` ra tệp `features.csv`.
3. **Huấn luyện bộ phân loại Classifier (Giai đoạn 2 - Tuần 3):**
   - Đọc `features.csv`, chia tập `Train / Validation / Test` theo tỷ lệ chuẩn (Stratified Split chống lệch nhãn).
   - Huấn luyện và so sánh các mô hình phân loại nhẹ: **MLP (2–3 lớp ẩn)**, **SVM (RBF Kernel)** và **LightGBM / Logistic Classifier**.
   - Đánh giá các chỉ số `Accuracy`, `Precision`, `Recall`, `F1-Score`, `ROC-AUC` và lưu mô hình tốt nhất (`.pkl` + trọng số JSON chuẩn hóa) khi đạt mục tiêu **Accuracy > 75%**.

### 2. Quy Tắc Nghiệp Vụ & Ngoại Lệ (`Business Rules`)
- **`BR-ML-01` (Kiểm tra tính toàn vẹn đa phương thức):** Mẫu dữ liệu bị thiếu cả ảnh lẫn văn bản hoặc ảnh bị hỏng không đọc được phải bị loại bỏ và ghi nhận vào báo cáo EDA.
- **`BR-ML-02` (Chuẩn hóa kích thước Vector nối):** Vector đầu ra sau khi nối bắt buộc cố định số chiều ($512 + 512 = 1024$ chiều với CLIP ViT-B/32, hoặc $64$ chiều với bộ trích xuất đa phương thức rút gọn khi chạy local không GPU) và được chuẩn hóa L2 trước khi đưa vào Classifier.
- **`BR-ML-03` (Ngưỡng chất lượng mô hình):** Bộ phân loại xuất xưởng bắt buộc đạt `Accuracy >= 0.75` (75%) trên tập kiểm thử theo đúng mục tiêu Giai đoạn 2.

---

## Quy Trình 02: Suy Luận Thời Gian Thực Qua Backend API `POST /predict` (Giai đoạn 3)

| Thuộc tính | Nội dung đặc tả |
| :--- | :--- |
| **Mã quy trình** | `BF-API-02` |
| **Tên quy trình** | Tiếp nhận Ảnh & Văn bản quảng cáo qua REST API, trích xuất đặc trưng và dự đoán mức độ gây hại |
| **Tác nhân (Actors)** | - `Browser Extension` (`content.js` / `background.js`)<br/>- `Developer / Tester` (Gửi request qua Postman, cURL hoặc trang Web Demo)<br/>- `Backend Inference Server` (FastAPI / HTTP Server + CLIP + Classifier) |
| **Phân khu liên quan** | `src/app/main.py`, `src/server/inference_service.py`, `src/lib/` |

### 1. Luồng Sự Kiện Chính (Main Success Scenario)
1. **Client (`Extension` / `Postman`)** gửi HTTP Request `POST /predict` (hỗ trợ cả `application/json` chứa `{"text": "...", "image_url": "..."}` / `image_base64` VÀ `multipart/form-data` chứa file ảnh upload + trường `text`).
2. **Backend API** kiểm tra tính hợp lệ của dữ liệu đầu vào (ít nhất phải có `text` hoặc `image`/`image_url`).
3. **Inference Service** trích xuất vector đặc trưng của ảnh và văn bản, nối thành vector đa phương thức và đưa qua `Classifier` đã lưu để tính xác suất độc hại $p \in [0.0, 1.0]$.
4. **Backend API** ghi bản ghi Structured JSON Log đủ **13 trường chuẩn** (`trace_id`, `duration_ms`, `event_action="AD_MODERATION_PREDICT"`, v.v.) và trả về phản hồi JSON:
   ```json
   {
     "is_harmful": true,
     "confidence": 0.89,
     "label": "harmful_ad",
     "category": "scam_or_harmful_content",
     "reasons": ["Phát hiện ngôn từ lừa đảo/độc hại kết hợp hình ảnh quảng cáo tương phản cao"],
     "model_backend": "clip-vit-b32+mlp",
     "latency_ms": 18.4
   }
   ```

### 2. Quy Tắc Nghiệp Vụ & Ngoại Lệ (`Business Rules`)
- **`BR-API-01` (Khế ước JSON đầu ra bắt buộc):** Phản hồi của `POST /predict` bắt buộc luôn có mặt 2 trường cốt lõi `is_harmful` (`boolean`) và `confidence` (`float` làm tròn 2–4 chữ số thập phân trong đoạn `[0.0, 1.0]`) để tương thích 100% với `content.js` của Giai đoạn 4.
- **`BR-API-02` (Chống SSRF & Giới hạn kích thước ảnh):** Khi tải ảnh từ `image_url`, chỉ chấp nhận giao thức `http://`, `https://`, hoặc `data:image/...` (Data URI) và giới hạn dung lượng $\le 5\text{MB}$. Nếu tải ảnh thất bại, hệ thống không được sập (`500`) mà phải chuyển sang đánh giá dựa trên đặc trưng văn bản kết hợp cờ cảnh báo.
- **`BR-API-03` (Cơ chế Dual-Engine sẵn sàng triển khai Cloud & Local):** Nếu môi trường có cài đặt `torch` + `transformers`, nạp `openai/clip-vit-base-patch32`; nếu chạy trên máy nhẹ chưa cài PyTorch hoặc cần phản hồi tức thì ($< 20\text{ms}$), tự động kích hoạt bộ trích xuất đa phương thức nhẹ (`Lightweight Multimodal Engine` + trọng số MLP đã huấn luyện) để API luôn hoạt động 100%.

---

## Quy Trình 03: Quét Trang Web & Che Quảng Cáo Độc Hại Bằng Trình Duyệt Extension (Giai đoạn 4)

| Thuộc tính | Nội dung đặc tả |
| :--- | :--- |
| **Mã quy trình** | `BF-EXT-03` |
| **Tên quy trình** | Tự động quét thẻ quảng cáo trên trang web, gọi API phân loại và làm mờ quảng cáo độc hại kèm nút cảnh báo |
| **Tác nhân (Actors)** | - `End User` (Người dùng lướt Facebook, báo điện tử hoặc trang Demo)<br/>- `Chrome/Edge Extension` (`manifest.json`, `content.js`, `background.js`, `popup/`) |
| **Phân khu liên quan** | `src/features/extension/`, `src/app/demo/` |

### 1. Luồng Sự Kiện Chính (Main Success Scenario)
1. **Người dùng** mở trình duyệt Chrome/Edge có bật tiện ích mở rộng **AdShield Multimodal Detector** và truy cập một trang web (trang tin tức, mạng xã hội Facebook, hoặc trang Demo kiểm thử `/demo`).
2. **`content.js`** tự động quét DOM để tìm các khối chứa quảng cáo:
   - Các khối có đánh dấu quảng cáo (`[data-ad-card]`, `.ad-card`, `.sponsored-post`, `article`, `.feed-card`) hoặc các phần tử chứa cặp thẻ `<img>` đi kèm thẻ văn bản `<p>`, `<span>`, `<h3>`, `<h4>`.
3. Với mỗi khối quảng cáo chưa được kiểm tra (`data-adshield-scanned !== "true"`), **`content.js`** trích xuất `image_url` (từ `img.src` hoặc ảnh nền/canvas) và `text` (từ các thẻ `<p>`, `<span>` lân cận + `img.alt`), sau đó gửi yêu cầu phân loại tới `POST /predict` (thông qua `background.js` hoặc gọi trực tiếp).
4. Khi API trả về `{"is_harmful": true, "confidence": ...}`:
   - **`content.js`** áp dụng CSS trực tiếp lên phần tử hình ảnh/nội dung quảng cáo:
     ```javascript
     element.style.filter = "blur(10px)";
     ```
   - Tạo lớp phủ bảo vệ (Overlay Wrapper) bọc bên ngoài quảng cáo với nhãn độ tin cậy và nút bấm tương tác có đúng nội dung:
     **"Quảng cáo này có thể chứa nội dung độc hại. Nhấp để xem"**
5. Nếu **Người dùng** nhấn vào nút **"Quảng cáo này có thể chứa nội dung độc hại. Nhấp để xem"**, tiện ích gỡ bỏ `blur(10px)` (`element.style.filter = "none"`) để hiển thị nội dung và đổi nút thành **"Ẩn lại quảng cáo độc hại"** để người dùng có thể làm mờ trở lại bất kỳ lúc nào.

### 2. Quy Tắc Nghiệp Vụ & Ngoại Lệ (`Business Rules`)
- **`BR-EXT-01` (Chống quét trùng lặp & Hỗ trợ cuộn vô tận):** Mỗi quảng cáo đã quét phải được gắn thuộc tính `data-adshield-scanned="true"` và lưu bộ nhớ đệm theo khóa `(image_url + text)` để khi người dùng cuộn trang (`MutationObserver`), tiện ích chỉ gửi các quảng cáo mới về API.
- **`BR-EXT-02` (Đúng chuẩn CSS & Thông điệp Giai đoạn 4):** Hiệu ứng làm mờ bắt buộc gán `element.style.filter = "blur(10px)"` và nút cảnh báo bắt buộc hiển thị rõ câu **"Quảng cáo này có thể chứa nội dung độc hại. Nhấp để xem"** với vùng chạm tối thiểu `44x44px`.
- **`BR-EXT-03` (Xử lý đủ 4 trạng thái giao diện):** Cả trên trang web (`content.js`) và trong hộp thoại tiện ích (`popup.html`) đều phải thể hiện rõ 4 trạng thái: `Loading` (Đang phân tích AI...), `Error` (Mất kết nối API + nút Thử lại), `Empty` (Chưa phát hiện quảng cáo trên trang), và `Success` (Thống kê số quảng cáo đã quét & đã chặn).
