# The base is deliberately version-pinned at the tag level for portability in the thesis demo.
# For production, replace it with a digest-pinned base image such as:
# FROM python:3.12-slim@sha256:<digest>
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=65532:65532 . .

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=2)"

USER 65532:65532
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
