FROM python:3.12-slim
WORKDIR /app
COPY requirements.lock ./requirements.lock
RUN pip install --no-cache-dir -r requirements.lock && useradd --create-home appuser
COPY backend/__init__.py ./backend/__init__.py
COPY backend/app ./backend/app
USER appuser
EXPOSE 8000
# One worker: the current cache/budget is process-local and must not be multiplied.
CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
