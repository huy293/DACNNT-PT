# ==============================================================================
# MULTI-STAGE DOCKERFILE FOR HUGGINGFACE SPACES (PORT 7860) & RENDER (PORT 8000)
# Compliant with `.agents/skills/docker-3-skills/SKILL.md`
# ==============================================================================

# Stage 1: Dependency Builder
FROM python:3.12-slim AS builder
WORKDIR /build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Production Non-Root Runner
FROM python:3.12-slim AS runner
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=7860

RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser
COPY --from=builder /install /usr/local
COPY src/ ./src/
RUN chown -R appuser:appuser /app

USER appuser
EXPOSE 7860 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/healthz')" || exit 1

CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "7860"]
