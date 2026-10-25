"""Layer 2 & Layer 6 Tests: Stage 3 FastAPI / HTTP Gateway & Security Checks."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
import unittest
from http.server import ThreadingHTTPServer

from src.lib.logger import StructuredLogger
from src.server.http_gateway import GatewayController, create_stdlib_http_handler
from src.server.inference_service import is_safe_external_url


class TestPredictAPIIntegration(unittest.TestCase):
    """Integration tests for POST /predict, GET /healthz, GET /demo, and SSRF protection."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.controller = GatewayController()
        handler_cls = create_stdlib_http_handler(cls.controller)
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
        cls.port = cls.server.server_address[1]
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()

    def test_healthz_endpoint(self) -> None:
        with urllib.request.urlopen(f"{self.base_url}/healthz", timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            body = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(body["status"], "ok")

    def test_demo_portal_endpoint(self) -> None:
        with urllib.request.urlopen(f"{self.base_url}/demo", timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            html = resp.read().decode("utf-8")
            self.assertIn("Quảng cáo này có thể chứa nội dung độc hại. Nhấp để xem", html)

    def test_predict_harmful_ad_json(self) -> None:
        """BR-API-01: Harmful ad returns is_harmful=True and confidence in [0.5, 1.0]."""
        payload = json.dumps({
            "text": "Nạp 100k nhận ngay 10 triệu! Casino VIP nổ hũ cực khủng rút tiền 30 giây!",
            "image_url": "banner_casino_vip.png",
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/predict",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIs(data["is_harmful"], True)
            self.assertGreaterEqual(data["confidence"], 0.75)
            self.assertEqual(data["label"], "harmful_ad")

    def test_predict_adversarial_obfuscated_harmful_ad(self) -> None:
        """Edge Case Mitigation: Obfuscated text ('8.x.b.e.t', 'n.ổ h.ũ', 'L.o.r.a.m.e.n') is still caught."""
        for adv_text in (
            "Khuyến mãi 8.x.b.e.t n.ổ h.ũ cực đỉnh! Nạp đầu nhận ngay 888k, rút tiền 30 giây!",
            "Thực phẩm L.o.r.a.m.e.n chính hãng: Tăng cường khả năng sinh lý, trị dứt điểm 100%!",
        ):
            req = urllib.request.Request(
                f"{self.base_url}/predict",
                data=json.dumps({"text": adv_text, "image_url": "https://example.com/ad.jpg"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                self.assertEqual(resp.status, 200)
                data = json.loads(resp.read().decode("utf-8"))
                self.assertIs(data["is_harmful"], True, f"Failed to detect obfuscated ad: {adv_text}")
                self.assertEqual(data["label"], "harmful_ad")

    def test_predict_safe_ad_json(self) -> None:
        """BR-API-01: Legitimate commercial ad returns is_harmful=False."""
        payload = json.dumps({
            "text": "Khóa học Lập trình Python & Trí tuệ Nhân tạo dành cho sinh viên CNTT.",
            "image_url": "khoa_hoc_python_ai.png",
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/predict",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIs(data["is_harmful"], False)
            self.assertEqual(data["label"], "safe_ad")

    def test_predict_normal_kaggle_and_ecommerce_cards_are_safe(self) -> None:
        """Regression test: Normal Kaggle notebooks and e-commerce ads with '100%' or 'miễn phí' must be safe."""
        cases = [
            {
                "text": "Related Notebooks: Exploratory Data Analysis & Confusion Matrix 99% Accuracy — 64 upvotes",
                "image_url": "https://www.googleapis.com/download/storage/v1/b/kaggle-user-content/o/plot_123.png",
            },
            {
                "text": "Giày chạy bộ chính hãng 100%, miễn phí vận chuyển toàn quốc trong 3 ngày, nhận quà bình nước thể thao.",
                "image_url": "https://example.com/running_shoes_banner.jpg",
            },
        ]
        for case in cases:
            req = urllib.request.Request(
                f"{self.base_url}/predict",
                data=json.dumps(case).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                self.assertEqual(resp.status, 200)
                data = json.loads(resp.read().decode("utf-8"))
                self.assertIs(data["is_harmful"], False, f"False positive on: {case['text']}")
                self.assertEqual(data["label"], "safe_ad")

    def test_predict_multipart_form_upload(self) -> None:
        """Stage 3 Week 4: Supports multipart/form-data file upload + text field (Postman style)."""
        boundary = "----AdShieldTestBoundary987654"
        body_parts = [
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"text\"\r\n\r\n"
            "Thần dược bác sĩ giấu kín chữa khỏi dứt điểm ung thư sau 3 ngày!\r\n",
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"thuoc_scam.png\"\r\n"
            "Content-Type: image/png\r\n\r\n\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\r\n",
            f"--{boundary}--\r\n",
        ]
        body_bytes = "".join(body_parts).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/predict",
            data=body_bytes,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIs(data["is_harmful"], True)

    def test_predict_empty_input_returns_400(self) -> None:
        payload = json.dumps({"text": "   ", "image_url": ""}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/predict",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=5)
        self.assertEqual(ctx.exception.code, 400)

    def test_ssrf_guard_blocks_internal_ips(self) -> None:
        """BR-API-02 & Layer 6 Security: Block loopback, metadata, and file:// schemes."""
        self.assertFalse(is_safe_external_url("http://127.0.0.1:8000/admin"))
        self.assertFalse(is_safe_external_url("http://169.254.169.254/latest/meta-data/"))
        self.assertFalse(is_safe_external_url("http://192.168.1.1/config"))
        self.assertFalse(is_safe_external_url("file:///etc/passwd"))
        self.assertTrue(is_safe_external_url("https://example.com/ad_banner.jpg"))

    def test_13_field_structured_logger(self) -> None:
        """Verify 13 mandatory log fields per docs/ops/OBSERVABILITY.md."""
        logger = StructuredLogger()
        rec = logger.log("INFO", "UNIT_TEST_EVENT")
        expected_fields = {
            "timestamp", "level", "service", "environment", "trace_id", "span_id",
            "request_id", "actor_id", "client_ip", "event_action", "http_context",
            "duration_ms", "error_and_metadata",
        }
        self.assertEqual(set(rec.keys()), expected_fields)
        self.assertTrue(rec["timestamp"].endswith("Z"))


if __name__ == "__main__":
    unittest.main()
