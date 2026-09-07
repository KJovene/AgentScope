# syntax=docker/dockerfile:1

# ---------- base : dépendances installées ----------
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq5 \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml README.md ./
COPY agentscope ./agentscope
RUN pip install --upgrade pip && pip install -e ".[dev]"

# ---------- dev : rechargement à chaud, code monté par docker-compose ----------
FROM base AS dev
EXPOSE 8000
CMD ["uvicorn", "agentscope.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ---------- prod : image mince, code figé dans l'image ----------
FROM python:3.12-slim AS prod
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml README.md ./
COPY agentscope ./agentscope
RUN pip install --upgrade pip && pip install .
EXPOSE 8000
CMD ["uvicorn", "agentscope.main:app", "--host", "0.0.0.0", "--port", "8000"]
