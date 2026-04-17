# Optimize builder and runtime to use the exact same Python version
FROM python:3.13-slim-bookworm AS builder

# Copy uv from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv


# Set the working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy only requirements to leverage Docker caching for dependencies
COPY pyproject.toml uv.lock ./

# Install build dependencies (needed for tgcrypto and other C extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies without installing the project itself
RUN uv sync --frozen --no-install-project --no-dev

# Copy the source code and necessary folders
COPY main.py config.py railway.json ./
COPY core/ ./core/
COPY db/ ./db/
COPY utils/ ./utils/
COPY locales/ ./locales/
COPY plugins/ ./plugins/
COPY custom_filters/ ./custom_filters/
COPY migrations/ ./migrations/

# Install the project
RUN uv sync --frozen --no-dev

# ---

# Stage 2: Final application image
FROM python:3.13-slim-bookworm

WORKDIR /app

# Create a non-privileged user and group
RUN groupadd -r bot && useradd -r -g bot -u 1000 -d /app bot

# Create directories for persistent data and set ownership
RUN mkdir -p /app/data /app/sessions /app/logs \
    && chown -R bot:bot /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    UV_PROJECT_ENVIRONMENT="/app/.venv" \
    UV_NO_SYNC=1 \
    UV_FROZEN=1

# Copy the uv binary to the final stage
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv

# Copy the pre-built environment and optimized app files from the builder
COPY --from=builder --chown=bot:bot /app /app

# Switch to the non-privileged user
USER bot

# Run the bot directly with python for maximum speed
CMD ["python", "main.py"]
