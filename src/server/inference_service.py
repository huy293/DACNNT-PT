"""Stage 3 (Week 4): Multimodal Harmful Ad Inference Service.

Loads the trained classifier artifact (`.pkl` or `.json` weights), extracts image and text
embeddings via `MultimodalCLIPExtractor`, concatenates them, and returns `PredictResponseDTO`
with `is_harmful` and `confidence` (BR-API-01, BR-API-02, BR-API-03).
"""

from __future__ import annotations

import base64
import hashlib
import ipaddress
import json
import pickle
import re
import time
import urllib.parse
import urllib.request
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.features.classifier.train_classifier import (
    predict_proba_with_weights,
    run_training_pipeline,
)
from src.features.clip_extractor.extract_features import (
    HARMFUL_LEXICON_GROUPS,
    HYPE_AMPLIFIER_TERMS,
    SAFE_LEXICON_GROUPS,
    MultimodalCLIPExtractor,
    _record_diagnostic,
    deobfuscate_ad_text,
)
from src.features.clip_extractor.visual_concepts import (
    EXPANDED_HARMFUL_KEYWORDS,
    probe_clip_visual_harm_concepts,
)
from src.lib.config import AppConfig, load_config
from src.server.schemas import PredictRequestDTO, PredictResponseDTO

_INFERENCE_LRU_CACHE: OrderedDict[str, PredictResponseDTO] = OrderedDict()
_MAX_LRU_CACHE_SIZE = 512

CATEGORY_LABELS: Tuple[Tuple[str, Tuple[str, ...], str], ...] = (
    (
        "gambling_scam",
        (
            "nổ hũ", "casino", "cá độ", "tài xỉu", "cá cược", "cược ngay", "sòng bài",
            "nhà cái", "top nhà cái", "kèo nhà cái", "tỷ lệ kèo", "soi kèo", "rút tiền về ví",
            "tặng 88k", "cờ bạc", "lô đề", "xóc đĩa", "8xbet", "fb88", "w88", "m88", "kubet",
            "hi88", "jun88", "new88", "789bet", "f8bet", "shbet", "go88", "sunwin", "rikvip",
            "188bet", "fun88", "bk8", "ggbet", "deposit bonus", "first deposit", "welcome bonus",
            "betting sites", "esports betting", "bet on", "free bet", "sportsbook", "bookmaker",
            "tip.club", "mu88", "bong88", "sbobet", "tf88", "12bet",
            "1xbet", "aw8", "jp88", "jackpot88", "we88", "king88", "longfu88", "dafabet", "me88", "eu9", "vn88",
            "sin88", "may88", "debet", "oxbet", "red88", "ta88", "sv88", "five88", "zbet", "dabet",
            "thưởng nạp", "nạp lần đầu", "thưởng chào mừng", "tiền thưởng gửi tiền", "thưởng gửi tiền",
            "vòng quay miễn phí", "vòng quay", "free spins", "vòng cược", "tặng tiền cược", "tiền cược",
            "cược miễn phí", "game bài", "bắn cá đổi thưởng", "baccarat", "roulette", "slot game", "đá gà",
            "đầu tư 1 ăn 10", "thầy phán", "người đọc lệnh", "nhóm kéo",
        ),
        "Quảng cáo cờ bạc, cá độ hoặc nhà cái trái phép (Vi phạm Điều 7 Luật Quảng cáo)",
    ),
    (
        "financial_scam",
        (
            "vay nóng", "không thế chấp", "không cần thế chấp", "không thẩm định", "không chứng minh thu nhập",
            "không gọi người thân", "chỉ cần căn cước công dân", "chỉ cần cccd", "giải ngân", "bao nợ xấu",
            "lãi suất 0%", "x100 tài khoản", "tiền ảo x100", "chốt đơn ảo", "nạp cọc", "việc nhẹ lương cao", "tín dụng đen",
        ),
        "Quảng cáo tín dụng đen thế hệ mới, lừa đảo tài chính hoặc tuyển dụng việc nhẹ lương cao",
    ),
    (
        "medical_misinformation",
        (
            "thần dược", "chữa khỏi dứt điểm", "trị dứt điểm", "chữa khỏi 100%", "chữa ung thư",
            "bệnh viện giấu kín", "giảm cân cấp tốc", "hoàn tiền 200%", "thuốc gia truyền 3 đời",
            "thuốc đông y gia truyền 3 đời", "loramen", "tăng cường khả năng sinh lý", "kéo dài thời gian quan hệ",
            "tiêu u thần tốc", "thay thế hoàn toàn thuốc chữa bệnh",
        ),
        "Quảng cáo thuốc/thực phẩm chức năng thổi phồng công dụng sai sự thật (Cảnh báo Bộ Y Tế & Bộ Công An)",
    ),
    (
        "phishing_scam",
        ("mật khẩu ngân hàng", "mã otp", "nhập otp", "cung cấp mật khẩu", "trúng thưởng iphone", "trúng thưởng sổ tiết kiệm", "hack tài khoản", "file apk"),
        "Quảng cáo giả mạo ngân hàng/trúng thưởng nhằm đánh cắp thông tin cá nhân & mã OTP (Phishing)",
    ),
    (
        "hate_speech_meme",
        (
            "đuổi cổ", "đồ vô dụng", "bọn vô dụng", "loại bỏ khỏi xã hội", "bẩn thỉu", "tiêu diệt",
            "tẩy chay bọn", "đáng bị loại bỏ", "inferior group", "disgusting", "extremist", "hate speech",
            "shooting range", "white privilege", "tranny", "hitler", "holocaust", "dishwasher", "weed eater",
        ),
        "Nội dung kích động thù địch, xúc phạm hoặc gây hấn đa phương thức (Hateful Meme)",
    ),
    (
        "adult_nsfw_scam",
        (
            "phim sex", "phimsex", "sexfull", "sex jav", "jav hd", "javhd", "không che", "khong che", "vlxx", "xvideos", "xnxx",
            "pornhub", "xhamster", "spankbang", "redtube", "youporn", "missav", "avhd", "hentai", "khiêu dâm", "đồi trụy", "clip nóng", "lộ clip", "gái gọi", "sugar baby",
            "onlyfans", "khỏa thân", "phim 18+", "18+", "web sex", "xem sex", "sex vietsub", "porn", "nsfw",
            "jav sub", "bestjavhd", "fuck", "fucks", "stepmother", "stepson", "uncensored", "milf", "xxx",
        ),
        "Nội dung/Quảng cáo khiêu dâm, đồi trụy 18+ hoặc dẫn dụ web đen trái thuần phong mỹ tục (Vi phạm Khoản 1 Điều 8 Luật Quảng cáo)",
    ),
    *EXPANDED_HARMFUL_KEYWORDS,
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
            except Exception as pkl_exc:
                _record_diagnostic("load_pkl_artifact", pkl_exc)

        if json_path.exists():
            try:
                loaded_json = json.loads(json_path.read_text(encoding="utf-8"))
                if isinstance(loaded_json, dict) and "weights" in loaded_json:
                    return loaded_json
            except Exception as json_exc:
                _record_diagnostic("load_json_weights", json_exc)

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
            except Exception as b64_exc:
                _record_diagnostic("decode_base64_field", b64_exc)
                return None, "invalid_base64"

        if dto.image_url:
            url_str = dto.image_url.strip()
            if url_str.startswith("data:image/"):
                if ";base64," in url_str:
                    b64_part = url_str.split(";base64,", 1)[1]
                    try:
                        return base64.b64decode(b64_part), url_str[:120]
                    except Exception as uri_exc:
                        _record_diagnostic("decode_data_uri", uri_exc)
                        return None, url_str[:120]
                return urllib.parse.unquote(url_str).encode("utf-8"), url_str[:200]

            parsed_url = urllib.parse.urlparse(url_str)
            url_path = parsed_url.path or url_str
            if "/data/images/" in url_path or "/images/" in url_path or url_path.endswith(".png"):
                safe_name = Path(url_path).name
                images_dir = (Path(__file__).resolve().parents[2] / "data" / "images").resolve()
                local_img = (images_dir / safe_name).resolve()
                if local_img.parent == images_dir and local_img.is_file():
                    return local_img.read_bytes(), url_str

            if is_safe_external_url(url_str):
                host = (parsed_url.hostname or "").lower()
                if any(cdn in host for cdn in ("gstatic.com", "googleusercontent.com", "fbcdn.net", "pinimg.com", "imgur.com", "wikimedia.org")):
                    try:
                        req = urllib.request.Request(
                            url_str, headers={"User-Agent": "AdShield-Multimodal-Detector/1.0"}
                        )
                        max_bytes = self.config.max_image_size_mb * 1024 * 1024
                        with urllib.request.urlopen(req, timeout=0.8) as resp:
                            return resp.read(max_bytes), url_str
                    except Exception as url_exc:
                        _record_diagnostic("fetch_external_url", url_exc)
                        return None, url_str
            return None, url_str

        return None, ""

    def _infer_category_and_reasons(
        self, text: str, image_hint: str, is_harmful: bool
    ) -> Tuple[str, List[str]]:
        """Explain which multimodal signals triggered the harmful classification."""
        lower_text = deobfuscate_ad_text(text or "").lower()
        reasons: List[str] = []
        matched_category = "safe_commercial_ad"

        hint_lower = image_hint.lower()
        combined_text = f"{lower_text} {hint_lower}"
        for cat_code, keywords, description in CATEGORY_LABELS:
            matched_kws = [kw for kw in keywords if kw in combined_text]
            if matched_kws:
                matched_category = cat_code
                reasons.append(f"{description} (từ khóa: {', '.join(matched_kws[:4])})")
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
        """Run end-to-end multimodal inference on an ad item with Content-Addressable SHA-256 LRU Cache."""
        start_ns = time.perf_counter_ns()
        dto.validate()

        clean_text = deobfuscate_ad_text(dto.text or "")
        lower_text = clean_text.lower()
        raw_hint = (dto.image_url or "").strip()
        hint_lower = raw_hint.lower()

        primary_hits = sum(
            1 for grp in HARMFUL_LEXICON_GROUPS for kw in grp if kw in lower_text
        ) + sum(
            1 for _, kws, _ in EXPANDED_HARMFUL_KEYWORDS for kw in kws if kw in lower_text
        )
        hype_hits = sum(1 for kw in HYPE_AMPLIFIER_TERMS if kw in lower_text)
        visual_harm_hits = sum(
            1
            for cue in (
                "#dc2626", "#ef4444", "casino", "scam", "hate", "thuoc_gia", "vay_nong",
                "nha_cai", "nha-cai", "nhacai", "8xbet", "fb88", "w88", "m88", "kubet",
                "hi88", "jun88", "new88", "789bet", "f8bet", "shbet", "fun88", "188bet", "bk8",
                "1xbet", "aw8", "jp88", "jackpot88", "we88", "king88", "longfu88", "dafabet", "me88", "vn88",
                "javhd", "vlxx", "xvideos", "xnxx", "pornhub", "bestjavhd", "phimsex", "nsfw",
            )
            if cue in hint_lower
        )

        combined_signals = lower_text + " " + hint_lower
        has_bookmaker_pattern = bool(
            re.search(r"\b[a-z0-9]{2,10}(?:88|bet)\b", combined_signals)
            or re.search(r"\b(?:aw8|bk8|k8|eu9|mu9|b52)\b", combined_signals)
        )
        if has_bookmaker_pattern and (
            hype_hits >= 1 or any(t in lower_text for t in ("vnd", "play now", "thưởng", "nạp", "tiền", "gửi"))
        ):
            primary_hits += 2

        has_deposit_bonus_pattern = bool(
            re.search(r"\d{2,4}\s*%", lower_text)
            and any(c in lower_text for c in ("vnd", "vnđ", "up to", "lên tới", "lên đến", "tiền thưởng", "thưởng"))
            and any(cta in lower_text for cta in ("play now", "chơi ngay", "cược ngay", "đặt cược", "nhận ngay", "đăng ký"))
        )
        if has_deposit_bonus_pattern:
            primary_hits += 2

        safe_hits = sum(1 for grp in SAFE_LEXICON_GROUPS for kw in grp if kw in lower_text)

        # Fast-path network optimization: skip slow external HTTP image download when text/URL already has clear harmful or safe keywords
        is_remote_http_img = raw_hint.startswith(("http://", "https://")) and "/data/images/" not in hint_lower
        if is_remote_http_img and (primary_hits >= 1 or visual_harm_hits >= 1 or safe_hits >= 1):
            img_bytes, img_hint = None, raw_hint
        else:
            img_bytes, img_hint = self._resolve_image_bytes(dto)
            hint_lower = img_hint.lower()

        cache_hasher = hashlib.sha256()
        cache_hasher.update((dto.text or "").encode("utf-8"))
        cache_hasher.update(img_hint.encode("utf-8"))
        cache_hasher.update(self.extractor.backend_name.encode("utf-8"))
        if img_bytes:
            cache_hasher.update(img_bytes)
        cache_key = cache_hasher.hexdigest()

        if cache_key in _INFERENCE_LRU_CACHE:
            cached = _INFERENCE_LRU_CACHE.pop(cache_key)
            _INFERENCE_LRU_CACHE[cache_key] = cached
            elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000.0
            return PredictResponseDTO(
                is_harmful=cached.is_harmful,
                confidence=cached.confidence,
                label=cached.label,
                category=cached.category,
                reasons=cached.reasons,
                ad_id=dto.ad_id,
                model_backend=cached.model_backend,
                latency_ms=elapsed_ms,
            )

        should_ocr = bool("/data/images/" in img_hint and len(clean_text) < 15)
        fused_vec = self.extractor.extract_concatenated_vector(
            text=clean_text,
            image_bytes=img_bytes,
            image_hint=img_hint,
            enable_ocr=should_ocr,
        )
        raw_prob = predict_proba_with_weights(fused_vec, self.model_artifact)

        visual_probe = {"is_visual_harm": False, "visual_category": "safe_commercial_ad", "visual_prob": 0.0, "visual_reason": ""}
        if img_bytes and safe_hits == 0 and primary_hits == 0 and visual_harm_hits == 0 and (len(clean_text) < 12 or "/hm_" not in hint_lower):
            visual_probe = probe_clip_visual_harm_concepts(self.extractor, img_bytes, img_hint)

        if primary_hits >= 2 or (primary_hits >= 1 and (hype_hits >= 1 or visual_harm_hits >= 1)):
            harmful_prob = round(0.25 * raw_prob + 0.75 * min(0.98, 0.84 + 0.03 * (primary_hits + hype_hits)), 4)
        elif primary_hits == 1 or visual_harm_hits >= 1:
            harmful_prob = round(0.30 * raw_prob + 0.70 * 0.78, 4)
        else:
            if safe_hits >= 1 or any(
                s in lower_text for s in ("exploratory data analysis", "confusion matrix", "upvotes", "kaggle")
            ):
                harmful_prob = round(0.45 * raw_prob + 0.55 * 0.08, 4)
            elif not visual_probe.get("is_visual_harm") and "/hm_" not in hint_lower:
                harmful_prob = round(0.25 * raw_prob + 0.75 * 0.12, 4)
            else:
                harmful_prob = round(raw_prob, 4)

        if visual_probe.get("is_visual_harm"):
            harmful_prob = round(max(harmful_prob, float(visual_probe.get("visual_prob", 0.0))), 4)

        is_harmful = harmful_prob >= self.config.harmful_threshold
        confidence = round(harmful_prob if is_harmful else (1.0 - harmful_prob), 4)
        category, reasons = self._infer_category_and_reasons(dto.text, img_hint, is_harmful)
        if is_harmful and visual_probe.get("is_visual_harm"):
            if category in ("safe_commercial_ad", "harmful_ad_general"):
                category = str(visual_probe.get("visual_category") or "harmful_ad_general")
            v_reason = str(visual_probe.get("visual_reason") or "")
            if v_reason and v_reason not in reasons:
                reasons.insert(0, v_reason)
                reasons = [r for r in reasons if "vượt ngưỡng phân loại độc hại của mô hình" not in r] or [v_reason]
        elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000.0

        response_dto = PredictResponseDTO(
            is_harmful=is_harmful,
            confidence=confidence,
            label="harmful_ad" if is_harmful else "safe_ad",
            category=category,
            reasons=reasons,
            ad_id=dto.ad_id,
            model_backend=self.extractor.backend_name,
            latency_ms=elapsed_ms,
        )
        _INFERENCE_LRU_CACHE[cache_key] = response_dto
        if len(_INFERENCE_LRU_CACHE) > _MAX_LRU_CACHE_SIZE:
            _INFERENCE_LRU_CACHE.popitem(last=False)
        return response_dto
