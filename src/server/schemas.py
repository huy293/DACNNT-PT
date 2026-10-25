"""Request and response schemas for the Multimodal Harmful Ad Detection API."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PredictRequestDTO:
    """Validated input contract for POST /predict."""

    text: str = ""
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    image_bytes: Optional[bytes] = None
    ad_id: Optional[str] = None

    def validate(self) -> None:
        has_text = bool(self.text and self.text.strip())
        has_img = bool(
            (self.image_url and self.image_url.strip())
            or (self.image_base64 and self.image_base64.strip())
            or (self.image_bytes and len(self.image_bytes) > 0)
        )
        if not has_text and not has_img:
            raise ValueError("ERR_EMPTY_INPUT: Phải cung cấp ít nhất 'text' hoặc 'image'/'image_url'.")


@dataclass
class PredictResponseDTO:
    """Standardized output contract for POST /predict (Stage 3 & Stage 4)."""

    is_harmful: bool
    confidence: float
    label: str
    category: str
    reasons: List[str] = field(default_factory=list)
    ad_id: Optional[str] = None
    model_backend: str = "lightweight-multimodal-64d"
    latency_ms: float = 0.0
    harm_modality: str = "both"

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["confidence"] = round(float(self.confidence), 4)
        payload["latency_ms"] = round(float(self.latency_ms), 2)
        return payload
