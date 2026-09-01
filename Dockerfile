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
# IonScale CLI (only the final binary is copied into the runtime layer).
# Taken from this deployment's own ionscale image rather than an upstream
# release: the fork adds org-scoped tailnets and tailnet lock, and an upstream
# CLI lacks those subcommands. The failure is SILENT -- ensure_org_mesh catches
# and logs, so a stale CLI means organizations quietly never get a tailnet.
#
# WARNING: this tag is only as current as the last push of the fork. If
# ionskale has gained subcommands since (e.g. `tailnets tailnet-lock-status`),
# this image does NOT have them. Push the fork before relying on this build;
# the dev stack sidesteps it by bind-mounting a locally built binary over
# /usr/local/bin/ionscale (see the lok service in docker-compose.yaml).
# Verify with: docker compose exec lok ionscale tailnets --help
COPY --from=jhnnsrs/ionskale:latest /usr/local/bin/ionscale /usr/local/bin/ionscale
RUN chmod +x /usr/local/bin/ionscale
WORKDIR /workspace
# Dependency layer — cached until pyproject.toml / uv.lock change:
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev
# django-allauth[saml] pulls xmlsec + lxml, which resolve to self-contained
# manylinux_2_28 wheels on this glibc-2.36 base — so no libxmlsec1/libxml2 apt
# packages are needed. Fail the build loudly if that ever stops being true
# (a source fallback would otherwise produce an image that 500s on first login).
RUN /opt/venv/bin/python -c "import xmlsec, lxml.etree, onelogin.saml2.auth"
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
