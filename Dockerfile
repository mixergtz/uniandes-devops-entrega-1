FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"
WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --no-dev --frozen

ENV PATH="/app/.venv/bin:${PATH}"

COPY . .

# Copy New Relic configuration
COPY newrelic.ini .

ENV PORT=5000
EXPOSE 5000

# Use New Relic's admin script to wrap gunicorn
CMD ["newrelic-admin", "run-program", "gunicorn", "wsgi:application", "-b", "0.0.0.0:5000", "--timeout", "120", "--workers", "2"]
