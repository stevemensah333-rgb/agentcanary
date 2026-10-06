FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PIP_DEFAULT_TIMEOUT=120

# Copy manifest first for better layer caching
COPY pyproject.toml ./
COPY src ./src
COPY configs ./configs
COPY prompts ./prompts
COPY target_agent ./target_agent

# Semantic embeddings are optional; the local demo needs no model downloads.
RUN pip install --no-cache-dir -e .

ENV PYTHONPATH=/app:/app/src

EXPOSE 8001
EXPOSE 9000

CMD ["uvicorn", "cyberredteam.api:app", "--host", "0.0.0.0", "--port", "8001"]
