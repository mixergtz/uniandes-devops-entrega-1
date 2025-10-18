FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"
WORKDIR /app

# Copia solo archivos de dependencias para cachear bien
COPY pyproject.toml ./

# Instala deps declaradas en el pyproject (sin venv, en sistema del contenedor)
RUN uv sync --no-dev --frozen --system

# Ahora copia el resto del código
COPY . .

ENV PORT=5000
EXPOSE 5000
CMD ["gunicorn", "wsgi:application", "-b", "0.0.0.0:5000", "--timeout", "120", "--workers", "2"]
