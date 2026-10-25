"""13-Field Structured JSON Logger compliant with docs/ops/OBSERVABILITY.md."""

from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class StructuredLogger:
    """Outputs single-line JSON logs containing all 13 mandatory observability fields."""

    def __init__(self, service: str = "multimodal-harmful-ad-api", environment: str = "development") -> None:
        self.service = service
        self.environment = environment

    def log(
        self,
        level: str,
        event_action: str,
        *,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        request_id: Optional[str] = None,
        actor_id: str = "anonymous",
        client_ip: str = "127.0.0.1",
        http_method: str = "POST",
        http_path: str = "/predict",
        http_status: int = 200,
        duration_ms: float = 0.0,
        error_and_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Construct and emit a 13-field structured JSON log entry."""
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        record: Dict[str, Any] = {
            "timestamp": now_utc,
            "level": level.upper(),
            "service": self.service,
            "environment": self.environment,
            "trace_id": trace_id or uuid.uuid4().hex,
            "span_id": span_id or uuid.uuid4().hex[:16],
            "request_id": request_id or f"req_{uuid.uuid4().hex[:20]}",
            "actor_id": actor_id,
            "client_ip": client_ip,
            "event_action": event_action,
            "http_context": {
                "method": http_method,
                "path": http_path,
                "status_code": http_status,
            },
            "duration_ms": round(float(duration_ms), 2),
            "error_and_metadata": error_and_metadata or {},
        }
        line = json.dumps(record, ensure_ascii=False) + "\n"
        try:
            sys.stdout.write(line)
            sys.stdout.flush()
        except UnicodeEncodeError:
            try:
                sys.stdout.write(json.dumps(record, ensure_ascii=True) + "\n")
                sys.stdout.flush()
            except OSError:
                pass
        except OSError:
            pass
        return record


default_logger = StructuredLogger()
