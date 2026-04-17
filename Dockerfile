FROM python:3.13-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1

COPY pyproject.toml uv.lock ./

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN uv sync --frozen --no-install-project --no-dev

COPY main.py config.py railway.json ./
COPY core/ ./core/
COPY db/ ./db/
COPY utils/ ./utils/
COPY locales/ ./locales/
COPY plugins/ ./plugins/
COPY custom_filters/ ./custom_filters/
COPY migrations/ ./migrations/

RUN uv sync --frozen --no-dev

# ---

FROM python:3.13-slim-bookworm

WORKDIR /app

RUN groupadd -r bot && useradd -r -g bot -u 1000 -d /app bot
RUN mkdir -p /app/data /app/sessions /app/logs \
    && chown -R bot:bot /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    UV_PROJECT_ENVIRONMENT="/app/.venv" \
    UV_FROZEN=1

COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv
COPY --from=builder --chown=bot:bot /app /app

USER bot

CMD ["uv", "run", "--no-dev", "main.py"]
