FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY pyproject.toml pytest.ini ./
COPY src ./src
COPY tests ./tests

ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["uvicorn", "fincrime_os.api.main:app", "--host", "0.0.0.0", "--port", "8000"]