ARG PYTHON_IMAGE_VERSION=3.14
FROM python:${PYTHON_IMAGE_VERSION}-slim AS dev

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV HOME=/tmp
ENV UV_CACHE_DIR=/tmp/uv-cache

WORKDIR /app
COPY . /app/

RUN uv sync && rm -rf "${UV_CACHE_DIR}"

ENV PATH="/app/.venv/bin:${PATH}"
