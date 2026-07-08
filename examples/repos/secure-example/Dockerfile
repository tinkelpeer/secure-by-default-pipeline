FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN useradd --uid 10001 appuser
USER 10001
HEALTHCHECK CMD python -c "print('ok')"
CMD ["python", "-c", "print('secure example')"]
