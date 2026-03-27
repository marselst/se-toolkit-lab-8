# Nanobot Dockerfile - multi-stage build with uv

# ---
# Stage 1: Build the application
# ---

ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}astral/uv:python3.14-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Omit development dependencies
ENV UV_NO_DEV=1

# Disable Python downloads, use system interpreter
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app
COPY --from=workspace pyproject.toml uv.lock /app/
COPY pyproject.toml /app/nanobot/pyproject.toml
COPY --from=webchat . /app/nanobot-websocket-channel
COPY --from=mcp . /app/mcp

# Sync the nanobot package and nanobot-webchat from workspace
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --package nanobot --package nanobot-webchat

COPY . /app/nanobot/

# ---
# Stage 2: Final image
# ---

ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}python:3.14.2-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8

# Setup non-root user
RUN groupadd --system --gid 999 nonroot \
    && useradd --system --gid 999 --uid 999 --create-home nonroot

# Copy the application
COPY --from=builder --chown=nonroot:nonroot /app /app

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/nanobot"

USER nonroot

WORKDIR /app/nanobot

# Run the entrypoint which resolves env vars and launches nanobot gateway
CMD ["python", "/app/nanobot/entrypoint.py"]
