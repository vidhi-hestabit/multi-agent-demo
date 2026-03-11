FROM python:3.11-slim

WORKDIR /app

# Install system dependencies + uv
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/root/.cargo/bin:/root/.local/bin:$PATH"

# Copy project metadata first so uv can resolve deps before copying all source
COPY pyproject.toml ./
# uv needs a README if declared in pyproject
COPY README.md ./

# Install all production dependencies into the system Python (no venv needed inside Docker)
RUN uv sync --no-dev --system

# Copy remaining source
COPY . .

# Default command (overridden by docker-compose)
CMD ["python", "-m", "orchestrator.main"]
