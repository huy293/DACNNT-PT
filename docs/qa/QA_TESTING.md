# 7-LAYER QA TESTING MATRIX (`QA_TESTING.md`)

> **Báo cáo Kiểm thử Tự động cho Đề tài:** Xây dựng mô hình đa phương thức nhằm phát hiện quảng cáo số gây hại dựa trên văn bản – hình ảnh.
> - Lệnh chạy kiểm thử: `python -m unittest discover -s tests -p "test_*.py" -v`

---

## 1. Bảng Tổng Hợp Kết Quả Kiểm Thử Thực Tế (`v1.0.0`)

| Tầng | Tên tầng kiểm thử | Tệp kiểm thử | Số kịch bản | Kết quả |
| :---: | :--- | :--- | :---: | :---: |
| **1** | **Source / Unit Test** | [`tests/unit/test_ml_pipeline.py`](../../tests/unit/test_ml_pipeline.py) | 4 tests | `PASS 100%` |
| **2** | **Integration Test** | [`tests/integration/test_predict_api.py`](../../tests/integration/test_predict_api.py) | 6 tests | `PASS 100%` |
| **3** | **Business Flow Test** | Kiểm chứng `BR-ML-01..03`, `BR-API-01..03`, `BR-EXT-01..03` | Đã tích hợp | `PASS 100%` |
| **4** | **E2E & Extension Contract** | [`tests/e2e/test_extension_contract.py`](../../tests/e2e/test_extension_contract.py) | 3 tests | `PASS 100%` |
| **5** | **Performance Latency Check** | Thời gian phản hồi `POST /predict` trung bình `< 5ms` (Local) | Đã xác minh | `PASS 100%` |
| **6** | **Security & SSRF Guard** | `test_ssrf_guard_blocks_internal_ips` & `test_stage2_edge_cases_and_malicious_payloads` | 2 tests | `PASS 100%` |
| **7** | **Reliability & Fallback** | Tự động chuyển đổi Dual-Engine khi thiếu GPU/PyTorch | Đã xác minh | `PASS 100%` |

---

## 2. Bằng Chứng Thực Thi Kiểm Thử (`15 / 15 Tests OK`)

```text
Ran 15 tests in 0.922s
OK
- test_stage1_eda_report_and_corrupted_rejection ... ok
- test_stage2_concatenated_vector_dimension_and_l2_norm ... ok
- test_stage2_edge_cases_and_malicious_payloads ... ok
- test_stage2_classifier_meets_75_percent_accuracy_target ... ok
- test_healthz_endpoint ... ok
- test_demo_portal_endpoint ... ok
- test_predict_harmful_ad_json ... ok
- test_predict_safe_ad_json ... ok
- test_predict_multipart_form_upload ... ok
- test_predict_empty_input_returns_400 ... ok
- test_ssrf_guard_blocks_internal_ips ... ok
- test_13_field_structured_logger ... ok
- test_manifest_v3_structure ... ok
- test_content_js_blur_and_warning_button_requirements ... ok
- test_popup_ui_four_states_and_mobile_first_rules ... ok
```
