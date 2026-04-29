FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    gcc \
    g++ \
    libgomp1 \
    libpq-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md /app/
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -e .[dev]

COPY . /app

RUN mkdir -p /app/uploads/reports

# Render (and similar platforms) expect the container to start a long-running process.
# Run migrations then start Uvicorn on the platform-provided $PORT.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

