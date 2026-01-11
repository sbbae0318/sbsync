FROM python:3.11-slim-bookworm

# Install git and uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy project files
COPY pyproject.toml .
# COPY uv.lock . # Lock file might not exist yet if just init'd, but good practice

# Install dependencies
RUN uv sync --frozen --no-install-project || uv sync --no-install-project

# Copy source code
COPY src/ src/

# Environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

# Entrypoint
CMD ["python", "src/main.py"]
