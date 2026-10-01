ARG PYTHON_IMAGE_VERSION=3.14
FROM python:${PYTHON_IMAGE_VERSION}-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

FROM python:${PYTHON_IMAGE_VERSION}-slim AS common

COPY --from=builder /bin/uv /bin/uvx /bin/

ENV HOME=/tmp
ENV UV_CACHE_DIR=/tmp/uv-cache

WORKDIR /app
COPY . .

RUN --mount=type=cache,target=/tmp/uv-cache uv sync --locked --no-dev

ENV PATH="/app/.venv/bin:${PATH}"

FROM common AS dev

RUN --mount=type=cache,target=/tmp/uv-cache uv sync --locked --dev
