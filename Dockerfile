FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Create a non-root user for container security
RUN useradd -m appuser

# Install dependencies first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application and test suite
COPY app.py test_app.py ./

# Ensure appuser owns /app so SQLite can create its database file at runtime
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

CMD ["python", "app.py"]