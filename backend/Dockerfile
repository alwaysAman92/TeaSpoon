FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt requirements-prod.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-prod.txt

# Copy app code
COPY . .

# The app auto-seeds the DB on first startup via seed_if_empty() in main.py lifespan.

# Expose default port
EXPOSE 8000

# Railway injects PORT as an env var at runtime.
# Using exec form with /bin/sh -c ensures proper variable expansion.
CMD ["/bin/sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
