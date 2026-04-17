# Stage 1: Build the virtual environment
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

# Set the working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy only requirements to leverage Docker caching for dependencies
COPY pyproject.toml uv.lock ./

# Install build dependencies if needed (e.g., for tgcrypto)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies without installing the project itself
RUN uv sync --frozen --no-install-project --no-dev

# Copy the source code and other required files
COPY . .

# Install the project
RUN uv sync --frozen --no-dev

# ---

# Stage 2: Create a stable runtime base
FROM python:3.13-slim-bookworm AS runtime-base

WORKDIR /app

# Create a non-privileged user and group
RUN groupadd -r bot && useradd -r -g bot -u 1000 -d /app bot

# Create directories for persistent data and set ownership
RUN mkdir -p /app/data /app/sessions /app/logs \
    && chown -R bot:bot /app

# ---

# Stage 3: Final application image
FROM runtime-base

# Copy the uv binary from the builder
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    UV_PROJECT_ENVIRONMENT="/app/.venv" \
    UV_NO_SYNC=1 \
    UV_FROZEN=1

# Copy the pre-built environment and project from the builder
COPY --from=builder --chown=bot:bot /app /app

# Switch to the non-privileged user
USER bot

# Run the bot
CMD ["uv", "run", "main.py"]
