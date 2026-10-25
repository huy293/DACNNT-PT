"""Stage 3 (Week 4 & 5): HTTP & FastAPI Gateway Handler.

Supports both FastAPI (when installed on Cloud/HuggingFace Spaces) and Python's built-in
`ThreadingHTTPServer` so `POST /predict`, `POST /predict/batch`, `GET /healthz`, and
`GET /demo` run immediately with zero external dependencies required.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import uuid
from concurrent.futures import ThreadPoolExecutor
from email.parser import BytesParser
from email.policy import default as default_email_policy
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.lib.config import AppConfig, load_config
from src.lib.logger import StructuredLogger
from src.server.inference_service import HarmfulAdInferenceService
from src.server.schemas import PredictRequestDTO

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_HTML_PATH = PROJECT_ROOT / "src" / "app" / "demo" / "index.html"
IMAGES_DIR = PROJECT_ROOT / "data" / "images"


class GatewayController:
    """Shared request controller used by both FastAPI and Standard HTTP Server."""

    def __init__(self, config: Optional[AppConfig] = None) -> None:
        self.config = config or load_config()
        self.logger = StructuredLogger(
            service=self.config.service_name, environment=self.config.app_env
        )
        self.service = HarmfulAdInferenceService(self.config)

    def handle_healthz(self) -> Tuple[int, Dict[str, Any]]:
        return 200, {
            "status": "ok",
            "service": self.config.service_name,
            "model_backend": self.service.extractor.backend_name,
            "threshold": self.config.harmful_threshold,
        }

    def handle_predict(
        self, payload: Dict[str, Any], client_ip: str = "127.0.0.1"
    ) -> Tuple[int, Dict[str, Any]]:
        start_ns = time.perf_counter_ns()
        trace_id = str(payload.get("trace_id") or uuid.uuid4().hex)
        try:
            dto = PredictRequestDTO(
                text=str(payload.get("text", "") or ""),
                image_url=payload.get("image_url"),
                image_base64=payload.get("image_base64"),
                image_bytes=payload.get("image_bytes"),
                ad_id=payload.get("ad_id"),
            )
            result = self.service.predict(dto).to_dict()
            duration_ms = (time.perf_counter_ns() - start_ns) / 1_000_000.0
            self.logger.log(
                "INFO",
                "AD_MODERATION_PREDICT",
                trace_id=trace_id,
                client_ip=client_ip,
                http_method="POST",
                http_path="/predict",
                http_status=200,
                duration_ms=duration_ms,
                error_and_metadata={
                    "is_harmful": result["is_harmful"],
                    "confidence": result["confidence"],
                    "category": result["category"],
                },
            )
            return 200, result
        except ValueError as exc:
            duration_ms = (time.perf_counter_ns() - start_ns) / 1_000_000.0
            self.logger.log(
                "WARN",
                "AD_MODERATION_VALIDATION_ERROR",
                trace_id=trace_id,
                client_ip=client_ip,
                http_method="POST",
                http_path="/predict",
                http_status=400,
                duration_ms=duration_ms,
                error_and_metadata={"error_code": "ERR_INVALID_INPUT", "message": str(exc)},
            )
            return 400, {"error": "ERR_INVALID_INPUT", "message": str(exc)}
        except Exception as exc:
            duration_ms = (time.perf_counter_ns() - start_ns) / 1_000_000.0
            self.logger.log(
                "ERROR",
                "AD_MODERATION_INTERNAL_ERROR",
                trace_id=trace_id,
                client_ip=client_ip,
                http_method="POST",
                http_path="/predict",
                http_status=500,
                duration_ms=duration_ms,
                error_and_metadata={"error_code": "ERR_INTERNAL", "message": str(exc)},
            )
            return 500, {"error": "ERR_INTERNAL", "message": "Internal inference error"}

    def handle_predict_batch(
        self, items: List[Dict[str, Any]], client_ip: str = "127.0.0.1"
    ) -> Tuple[int, Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for item in items[:50]:
            status, res = self.handle_predict(item, client_ip=client_ip)
            if status == 200:
                results.append(res)
        return 200, {"count": len(results), "results": results}


def create_stdlib_http_handler(controller: GatewayController):
    """Create a CORS-enabled BaseHTTPRequestHandler class bound to `controller`."""

    class AdShieldHTTPHandler(BaseHTTPRequestHandler):
        def _send_cors_headers(self) -> None:
            self.send_header("Access-Control-Allow-Origin", controller.config.cors_allowed_origins)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Trace-Id")

        def _send_json(self, status: int, data: Dict[str, Any]) -> None:
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            try:
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError, OSError):
                pass

        def do_OPTIONS(self) -> None:  # noqa: N802
            try:
                self.send_response(204)
                self._send_cors_headers()
                self.end_headers()
            except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError, OSError):
                pass

        def do_GET(self) -> None:  # noqa: N802
            path = self.path.split("?", 1)[0]
            if path == "/healthz":
                status, payload = controller.handle_healthz()
                self._send_json(status, payload)
                return

            if path in ("/", "/demo", "/demo/"):
                if DEMO_HTML_PATH.exists():
                    html_bytes = DEMO_HTML_PATH.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(html_bytes)))
                    self._send_cors_headers()
                    self.end_headers()
                    self.wfile.write(html_bytes)
                    return

            if path.startswith("/data/images/"):
                safe_name = Path(path.replace("/data/images/", "", 1)).name
                img_file = (IMAGES_DIR / safe_name).resolve()
                if img_file.is_file() and img_file.parent == IMAGES_DIR.resolve():
                    img_bytes = img_file.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "image/png")
                    self.send_header("Content-Length", str(len(img_bytes)))
                    self._send_cors_headers()
                    self.end_headers()
                    self.wfile.write(img_bytes)
                    return

            self._send_json(404, {"error": "NOT_FOUND", "path": path})

        def do_POST(self) -> None:  # noqa: N802
            path = self.path.split("?", 1)[0]
            content_type = self.headers.get("Content-Type", "")
            content_len = int(self.headers.get("Content-Length", "0") or "0")
            client_ip = self.client_address[0] if self.client_address else "127.0.0.1"

            if path == "/predict":
                payload: Dict[str, Any] = {}
                if "multipart/form-data" in content_type:
                    raw_body = self.rfile.read(content_len) if content_len > 0 else b""
                    mime_bytes = (
                        f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8")
                        + raw_body
                    )
                    msg = BytesParser(policy=default_email_policy).parsebytes(mime_bytes)
                    for part in msg.iter_parts():
                        field_name = part.get_param("name", header="content-disposition")
                        filename = part.get_filename()
                        part_bytes = part.get_payload(decode=True) or b""
                        if field_name == "image" or filename:
                            payload["image_bytes"] = part_bytes
                            if filename and not payload.get("image_url"):
                                payload["image_url"] = filename
                        elif field_name in ("text", "image_url", "ad_id"):
                            payload[field_name] = part_bytes.decode("utf-8", errors="replace")
                elif "application/x-www-form-urlencoded" in content_type:
                    raw_body = self.rfile.read(content_len) if content_len > 0 else b""
                    parsed_qs = urllib.parse.parse_qs(raw_body.decode("utf-8", errors="replace"))
                    payload["text"] = parsed_qs.get("text", [""])[0]
                    payload["image_url"] = parsed_qs.get("image_url", [None])[0]
                else:
                    raw_body = self.rfile.read(content_len) if content_len > 0 else b"{}"
                    try:
                        payload = json.loads(raw_body.decode("utf-8", errors="replace"))
                    except (json.JSONDecodeError, ValueError):
                        self._send_json(400, {"error": "ERR_INVALID_JSON", "message": "Invalid JSON body"})
                        return

                status, resp = controller.handle_predict(payload, client_ip=client_ip)
                self._send_json(status, resp)
                return

            if path == "/predict/batch":
                raw_body = self.rfile.read(content_len) if content_len > 0 else b"{}"
                try:
                    body_obj = json.loads(raw_body.decode("utf-8", errors="replace"))
                    items = body_obj.get("items", []) if isinstance(body_obj, dict) else body_obj
                except (json.JSONDecodeError, ValueError):
                    self._send_json(400, {"error": "ERR_INVALID_JSON"})
                    return
                status, resp = controller.handle_predict_batch(items, client_ip=client_ip)
                self._send_json(status, resp)
                return

            self._send_json(404, {"error": "NOT_FOUND", "path": path})

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            return

    return AdShieldHTTPHandler


class _BoundedPoolHTTPServer(HTTPServer):
    """HTTPServer backed by a fixed 2-worker ThreadPoolExecutor to prevent OS thread/OpenMP TLS exhaustion."""

    def __init__(self, server_address: Tuple[str, int], RequestHandlerClass: Any) -> None:
        super().__init__(server_address, RequestHandlerClass)
        self._pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="adshield-http")

    def process_request_thread(self, request: Any, client_address: Any) -> None:
        try:
            self.finish_request(request, client_address)
        except Exception:
            self.handle_error(request, client_address)
        finally:
            self.shutdown_request(request)

    def process_request(self, request: Any, client_address: Any) -> None:
        self._pool.submit(self.process_request_thread, request, client_address)

    def server_close(self) -> None:
        super().server_close()
        self._pool.shutdown(wait=False, cancel_futures=True)


def run_stdlib_server(
    host: Optional[str] = None,
    port: Optional[int] = None,
    controller: Optional[GatewayController] = None,
) -> None:
    """Start the bounded-pool HTTP server for local or container execution."""
    controller = controller or GatewayController()
    bind_host = host or controller.config.host
    bind_port = port or controller.config.port
    handler_cls = create_stdlib_http_handler(controller)
    server = _BoundedPoolHTTPServer((bind_host, bind_port), handler_cls)
    print(f"AdShield Multimodal API running on http://{bind_host}:{bind_port}")
    print(f"  -> POST http://{bind_host}:{bind_port}/predict")
    print(f"  -> GET  http://{bind_host}:{bind_port}/demo")
    server.serve_forever()
