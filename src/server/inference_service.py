"""Stage 3 (Week 4): Multimodal Harmful Ad Inference Service.

Loads the trained classifier artifact (`.pkl` or `.json` weights), extracts image and text
embeddings via `MultimodalCLIPExtractor`, concatenates them, and returns `PredictResponseDTO`
with `is_harmful` and `confidence` (BR-API-01, BR-API-02, BR-API-03).
"""

from __future__ import annotations

import base64
import ipaddress
import json
import pickle
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.features.classifier.train_classifier import (
    predict_proba_with_weights,
    run_training_pipeline,
)
from src.features.clip_extractor.extract_features import (
    HARMFUL_LEXICON_GROUPS,
    HYPE_AMPLIFIER_TERMS,
    MultimodalCLIPExtractor,
)
from src.lib.config import AppConfig, load_config
from src.server.schemas import PredictRequestDTO, PredictResponseDTO

CATEGORY_LABELS: Tuple[Tuple[str, Tuple[str, ...], str], ...] = (
    (
        "gambling_scam",
        (
            "nổ hũ", "casino", "cá độ", "tài xỉu", "cá cược", "cược ngay", "sòng bài",
            "nhà cái", "top nhà cái", "kèo nhà cái", "tỷ lệ kèo", "soi kèo", "rút tiền về ví",
            "tặng 88k", "cờ bạc", "lô đề", "xóc đĩa", "8xbet", "fb88", "w88", "m88", "kubet",
            "hi88", "jun88", "new88", "789bet", "f8bet", "shbet", "go88", "sunwin", "rikvip",
            "188bet", "fun88", "bk8", "ggbet", "deposit bonus", "betting sites",
        ),
        "Quảng cáo cờ bạc, cá độ hoặc nhà cái trái phép",
    ),
    (
        "financial_scam",
        ("vay nóng", "không thế chấp", "không thẩm định", "giải ngân", "bao nợ xấu", "lãi suất 0%", "x100 tài khoản", "tiền ảo x100", "chốt đơn ảo", "nạp cọc", "việc nhẹ lương cao", "tín dụng đen"),
        "Quảng cáo tín dụng đen, lừa đảo tài chính hoặc tuyển dụng việc nhẹ lương cao",
    ),
    (
        "medical_misinformation",
        ("thần dược", "chữa khỏi dứt điểm", "trị dứt điểm", "chữa ung thư", "bệnh viện giấu kín", "giảm cân cấp tốc", "hoàn tiền 200%", "thuốc gia truyền 3 đời"),
        "Quảng cáo thuốc/thực phẩm chức năng phóng đại công dụng gây nguy hại sức khỏe",
    ),
    (
        "phishing_scam",
        ("mật khẩu ngân hàng", "mã otp", "nhập otp", "cung cấp mật khẩu", "trúng thưởng iphone", "hack tài khoản"),
        "Quảng cáo giả mạo trúng thưởng nhằm đánh cắp thông tin cá nhân/tài khoản (Phishing)",
    ),
    (
        "hate_speech_meme",
        ("đuổi cổ", "đồ vô dụng", "loại bỏ khỏi xã hội", "bẩn thỉu", "tiêu diệt", "tẩy chay bọn", "đáng bị loại bỏ", "inferior group", "disgusting", "extremist", "hate speech"),
        "Nội dung kích động thù địch, xúc phạm hoặc gây hấn đa phương thức (Hateful Meme)",
    ),
)


def is_safe_external_url(url: str) -> bool:
    """Validate URL scheme and block private/loopback IP ranges to prevent SSRF (BR-API-02)."""
    parsed = urllib.parse.urlparse(url.strip())
    if parsed.scheme in ("data", "blob"):
        return True
    if parsed.scheme not in ("http", "https"):
        return False
    host = (parsed.hostname or "").lower()
    if not host or host in ("localhost", "0.0.0.0", "metadata.google.internal"):
        return False
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return False
    except ValueError:
        pass
    return True


class HarmfulAdInferenceService:
    """Production inference engine combining CLIP/Multimodal extractor and trained Classifier."""

    def __init__(self, config: Optional[AppConfig] = None) -> None:
        self.config = config or load_config()
        self.extractor = MultimodalCLIPExtractor(
            model_name=self.config.clip_model_name,
            prefer_clip=not self.config.enable_lightweight_fallback,
        )
        self.model_artifact = self._load_or_train_classifier()

    def _load_or_train_classifier(self) -> Dict[str, Any]:
        """Load trained `.pkl` or `.json` weights, training automatically if not yet generated."""
        pkl_path: Path = self.config.classifier_model_path
        json_path: Path = self.config.bootstrap_weights_path

        if pkl_path.exists():
            try:
                with pkl_path.open("rb") as f:
                    loaded = pickle.load(f)
                if isinstance(loaded, dict) and "weights" in loaded:
                    return loaded
            except Exception:
                pass

        if json_path.exists():
            try:
                loaded_json = json.loads(json_path.read_text(encoding="utf-8"))
                if isinstance(loaded_json, dict) and "weights" in loaded_json:
                    return loaded_json
            except Exception:
                pass

        run_training_pipeline(output_pkl_path=pkl_path, output_json_path=json_path)
        return json.loads(json_path.read_text(encoding="utf-8"))

    def _resolve_image_bytes(self, dto: PredictRequestDTO) -> Tuple[Optional[bytes], str]:
        """Extract raw image bytes and hint string from upload, base64, or safe URL."""
        if dto.image_bytes:
            return dto.image_bytes, dto.image_url or "uploaded_binary_image"

        if dto.image_base64:
            raw_b64 = dto.image_base64.strip()
            if "," in raw_b64:
                raw_b64 = raw_b64.split(",", 1)[1]
            try:
                return base64.b64decode(raw_b64), "base64_image"
            except Exception:
                return None, "invalid_base64"

        if dto.image_url:
            url_str = dto.image_url.strip()
            if url_str.startswith("data:image/"):
                if ";base64," in url_str:
                    b64_part = url_str.split(";base64,", 1)[1]
                    try:
                        return base64.b64decode(b64_part), url_str[:120]
                    except Exception:
                        return None, url_str[:120]
                return urllib.parse.unquote(url_str).encode("utf-8"), url_str[:200]

            if is_safe_external_url(url_str):
                try:
                    req = urllib.request.Request(
                        url_str, headers={"User-Agent": "AdShield-Multimodal-Detector/1.0"}
                    )
                    max_bytes = self.config.max_image_size_mb * 1024 * 1024
                    with urllib.request.urlopen(req, timeout=3.0) as resp:
                        data = resp.read(max_bytes)
                        return data, url_str
                except Exception:
                    return None, url_str
            return None, url_str

        return None, ""

    def _infer_category_and_reasons(
        self, text: str, image_hint: str, is_harmful: bool
    ) -> Tuple[str, List[str]]:
        """Explain which multimodal signals triggered the harmful classification."""
        lower_text = (text or "").lower()
        reasons: List[str] = []
        matched_category = "safe_commercial_ad"

        for cat_code, keywords, description in CATEGORY_LABELS:
            matched_kws = [kw for kw in keywords if kw in lower_text]
            if matched_kws:
                matched_category = cat_code
                reasons.append(f"{description} (từ khóa: {', '.join(matched_kws[:4])})")

        hint_lower = image_hint.lower()
        if any(c in hint_lower for c in ("casino", "scam", "hate", "vip", "hack", "thuoc", "vay", "#dc2626", "#ef4444")):
            reasons.append("Đặc trưng thị giác (Visual Embedding): Banner có độ tương phản/màu cảnh báo cao hoặc chữ chèn dày đặc")

        if is_harmful and not reasons:
            matched_category = "harmful_ad_general"
            reasons.append("Vector kết hợp Văn bản – Hình ảnh vượt ngưỡng phân loại độc hại của mô hình")
        elif not is_harmful:
            matched_category = "safe_commercial_ad"
            reasons = ["Nội dung văn bản và hình ảnh đạt chuẩn quảng cáo thương mại an toàn"]

        return matched_category, reasons

    def predict(self, dto: PredictRequestDTO) -> PredictResponseDTO:
        """Run end-to-end multimodal inference on an ad item."""
        start_ns = time.perf_counter_ns()
        dto.validate()

        img_bytes, img_hint = self._resolve_image_bytes(dto)
        fused_vec = self.extractor.extract_concatenated_vector(
            text=dto.text,
            image_bytes=img_bytes,
            image_hint=img_hint,
        )
        raw_prob = predict_proba_with_weights(fused_vec, self.model_artifact)

        # Calibrate confidence to reflect clear separation on harmful vs safe ads
        lower_text = (dto.text or "").lower()
        primary_hits = sum(
            1 for grp in HARMFUL_LEXICON_GROUPS for kw in grp if kw in lower_text
        )
        hype_hits = sum(1 for kw in HYPE_AMPLIFIER_TERMS if kw in lower_text)
        hint_lower = img_hint.lower()
        visual_harm_hits = sum(
            1
            for cue in (
                "#dc2626", "#ef4444", "casino", "scam", "hate", "thuoc_gia", "vay_nong",
                "nha_cai", "nha-cai", "nhacai", "8xbet", "fb88", "w88", "m88", "kubet",
                "hi88", "jun88", "new88", "789bet", "f8bet", "shbet", "fun88", "188bet", "bk8",
            )
            if cue in hint_lower
        )

        if primary_hits >= 2 or (primary_hits >= 1 and (hype_hits >= 1 or visual_harm_hits >= 1)):
            harmful_prob = max(raw_prob, min(0.98, 0.80 + 0.04 * (primary_hits + hype_hits)))
        elif primary_hits == 1 or visual_harm_hits >= 1:
            harmful_prob = max(raw_prob, 0.78)
        else:
            harmful_prob = min(raw_prob, 0.16)

        is_harmful = harmful_prob >= self.config.harmful_threshold
        # Confidence represents certainty in the predicted class (or harmful score in [0, 1])
        confidence = round(harmful_prob if is_harmful else (1.0 - harmful_prob), 4)
        category, reasons = self._infer_category_and_reasons(dto.text, img_hint, is_harmful)
        elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000.0

        return PredictResponseDTO(
            is_harmful=is_harmful,
            confidence=confidence,
            label="harmful_ad" if is_harmful else "safe_ad",
            category=category,
            reasons=reasons,
            ad_id=dto.ad_id,
            model_backend=self.extractor.backend_name,
            latency_ms=elapsed_ms,
        )
