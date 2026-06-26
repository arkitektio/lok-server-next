# syntax=docker/dockerfile:1
# ---- builder: compile deps + fetch ionscale, then discard the toolchain ----
FROM python:3.12-slim-bookworm AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv
# curl only fetches the ionscale binary (py-ubjson falls back to pure Python, no gcc).
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl \
 && rm -rf /var/lib/apt/lists/*
# IonScale CLI (only the final binary is copied into the runtime layer):
RUN curl -L -o /usr/local/bin/ionscale \
      https://github.com/jsiebens/ionscale/releases/download/v0.18.0/ionscale_linux_amd64 \
 && chmod +x /usr/local/bin/ionscale
WORKDIR /workspace
# Dependency layer — cached until pyproject.toml / uv.lock change:
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev
# Project layer:
COPY . .
RUN uv sync --frozen --no-dev

# ---- runtime: slim base + prebuilt venv; psycopg[binary] bundles libpq ----
FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"
COPY --from=builder /usr/local/bin/ionscale /usr/local/bin/ionscale
WORKDIR /workspace
COPY --from=builder /opt/venv /opt/venv
COPY . .
