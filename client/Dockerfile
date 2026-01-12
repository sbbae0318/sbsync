FROM python:3.11-slim-bookworm

# Install git and ssh client
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir "uv>=0.7.0"

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy project files
COPY pyproject.toml .

# Install dependencies (without lock file for now)
RUN uv sync --no-install-project

# Copy source code
COPY src/ src/
COPY docker/ docker/

# Environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

# Entrypoint
RUN chmod +x docker/entrypoint.sh
CMD ["docker/entrypoint.sh"]
