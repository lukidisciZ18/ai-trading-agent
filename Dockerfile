FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl wget \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY src/ /app/src/
COPY scripts/ /app/scripts/
COPY strategies/ /app/strategies/
COPY config/ /app/config/
RUN mkdir -p /app/data /app/logs

# Expose FastAPI port
EXPOSE 8000

# Healthcheck to verify service is up
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://localhost:8000/health || exit 1

ENTRYPOINT ["python", "-u", "src/main.py"]
CMD ["--mode", "api"]
