ARG PYTHON_IMAGE_VERSION=3.14
FROM python:${PYTHON_IMAGE_VERSION}-slim AS dev

# Copy the uv binary from the official image (no installer, no PATH issues)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# "Activate" the virtual environment for every following instruction and at runtime
ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    UV_LINK_MODE=copy

RUN uv venv $VIRTUAL_ENV

WORKDIR /app

# Install the project and its dependencies
COPY pyproject.toml README.md ./
COPY src ./src
RUN uv pip install -e .
