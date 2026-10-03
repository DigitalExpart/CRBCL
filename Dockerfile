FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc curl ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir -e "."

# Pre-download and bake tiny Whisper model into the container image cache
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('tiny', device='cpu', compute_type='int8')"

COPY backend/ .

# Production speech defaults (conservative concurrency=1 for initial rollout)
ENV SPEECH_TO_TEXT_ENABLED=true \
    SPEECH_PROVIDER=local_whisper \
    SPEECH_MODEL=tiny \
    SPEECH_MAX_CONCURRENCY=1

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
