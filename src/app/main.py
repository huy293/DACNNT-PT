"""Tier 3 Orchestrator / Router (`src/app/main.py` < 80 lines per AGENTS.md).

Exposes `app` for FastAPI/Uvicorn (`uvicorn src.app.main:app --reload`) and falls back
automatically to the standard HTTP server when executed via `python -m src.app.main`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from src.server.http_gateway import DEMO_HTML_PATH, IMAGES_DIR, GatewayController, run_stdlib_server

controller = GatewayController()
app: Any = None

try:
    from fastapi import FastAPI, File, Form, Request, UploadFile  # type: ignore
    from fastapi.middleware.cors import CORSMiddleware  # type: ignore
    from fastapi.responses import HTMLResponse, JSONResponse  # type: ignore
    from fastapi.staticfiles import StaticFiles  # type: ignore

    app = FastAPI(
        title="Multimodal Harmful Digital Ad Detector API",
        description="Phát hiện quảng cáo số gây hại dựa trên Văn bản – Hình ảnh (CLIP + Classifier)",
        version="2.0.0",
    )
    if IMAGES_DIR.exists():
        app.mount("/data/images", StaticFiles(directory=str(IMAGES_DIR)), name="dataset_images")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz")
    async def healthz() -> Dict[str, Any]:
        _, data = controller.handle_healthz()
        return data

    @app.get("/", response_class=HTMLResponse)
    @app.get("/demo", response_class=HTMLResponse)
    async def demo_page() -> HTMLResponse:
        if DEMO_HTML_PATH.exists():
            return HTMLResponse(DEMO_HTML_PATH.read_text(encoding="utf-8"))
        return HTMLResponse("<h1>Demo Page Not Found</h1>", status_code=404)

    @app.post("/predict")
    async def predict_endpoint(
        request: Request,
        text: Optional[str] = Form(default=None),
        image_url: Optional[str] = Form(default=None),
        image: Optional[UploadFile] = File(default=None),
    ) -> JSONResponse:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            payload = await request.json()
        else:
            img_bytes = await image.read() if image is not None else None
            payload = {"text": text or "", "image_url": image_url, "image_bytes": img_bytes}
        status, result = controller.handle_predict(payload)
        return JSONResponse(status_code=status, content=result)

except ImportError:
    app = controller


if __name__ == "__main__":
    run_stdlib_server()
