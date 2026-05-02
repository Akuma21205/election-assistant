FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies (no dev deps, no editable install)
RUN uv sync --frozen --no-dev

# Copy source code
COPY main.py election_data.py rag.py ./

# Copy .env.example as reference (real .env injected via Cloud Run secret)
COPY .env.example .env.example

# Expose port
EXPOSE 8080

# Use uv to run the app
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
