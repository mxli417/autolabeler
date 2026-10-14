FROM python:3.12-slim-bookworm
WORKDIR /app
RUN groupadd --system app && useradd --system --gid app --create-home app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir ".[api]"
RUN mkdir -p /workbench && chown -R app:app /app /workbench
USER app
EXPOSE 8000
CMD ["uvicorn", "autolabeler.api:app", "--host", "0.0.0.0", "--port", "8000"]
