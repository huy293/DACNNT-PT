"""Fail-fast environment configuration validation for Multimodal Harmful Ad Detector."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class AppConfig:
    """Validated application configuration loaded from environment variables."""

    app_env: str
    host: str
    port: int
    log_level: str
    service_name: str
    clip_model_name: str
    classifier_model_path: Path
    bootstrap_weights_path: Path
    harmful_threshold: float
    enable_lightweight_fallback: bool
    cors_allowed_origins: str
    max_image_size_mb: int
    request_timeout_seconds: int


def load_config() -> AppConfig:
    """Load and validate environment variables with fail-fast checks."""
    port_raw = os.getenv("PORT", "8000")
    try:
        port = int(port_raw)
    except ValueError as exc:
        raise ValueError(f"Invalid PORT value: {port_raw!r}. Must be an integer.") from exc

    if not (1 <= port <= 65535):
        raise ValueError(f"PORT out of valid range (1..65535): {port}")

    threshold_raw = os.getenv("HARMFUL_THRESHOLD", "0.50")
    try:
        threshold = float(threshold_raw)
    except ValueError as exc:
        raise ValueError(f"Invalid HARMFUL_THRESHOLD: {threshold_raw!r}") from exc

    if not (0.0 < threshold < 1.0):
        raise ValueError(f"HARMFUL_THRESHOLD must be in (0.0, 1.0), got {threshold}")

    classifier_rel = os.getenv(
        "CLASSIFIER_MODEL_PATH", "src/server/models/harmful_ad_classifier.pkl"
    )
    bootstrap_rel = os.getenv(
        "BOOTSTRAP_WEIGHTS_PATH", "src/mocks/bootstrap_classifier_weights.json"
    )

    fallback_raw = os.getenv("ENABLE_LIGHTWEIGHT_FALLBACK", "false").strip().lower()
    enable_fallback = fallback_raw in ("1", "true", "yes", "on")

    max_img_mb = int(os.getenv("MAX_IMAGE_SIZE_MB", "5"))
    req_timeout = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "10"))
    if max_img_mb <= 0 or req_timeout <= 0:
        raise ValueError("MAX_IMAGE_SIZE_MB and REQUEST_TIMEOUT_SECONDS must be positive integers.")

    return AppConfig(
        app_env=os.getenv("APP_ENV", "development"),
        host=os.getenv("HOST", "127.0.0.1"),
        port=port,
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        service_name=os.getenv("SERVICE_NAME", "multimodal-harmful-ad-api"),
        clip_model_name=os.getenv("CLIP_MODEL_NAME", "openai/clip-vit-base-patch32"),
        classifier_model_path=PROJECT_ROOT / classifier_rel,
        bootstrap_weights_path=PROJECT_ROOT / bootstrap_rel,
        harmful_threshold=threshold,
        enable_lightweight_fallback=enable_fallback,
        cors_allowed_origins=os.getenv("CORS_ALLOWED_ORIGINS", "*"),
        max_image_size_mb=max_img_mb,
        request_timeout_seconds=req_timeout,
    )
