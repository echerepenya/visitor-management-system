FROM python:3.12-slim-bookworm AS base

RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g 1000 -m -s /bin/bash appuser

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/.local/bin:$PATH"

WORKDIR /app
RUN chown appuser:appuser /app
USER appuser

FROM base AS deps
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM base AS final

COPY --from=deps /home/appuser/.local /home/appuser/.local

COPY --chown=appuser:appuser . .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
