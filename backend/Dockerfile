FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt requirements-prod.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-prod.txt

# Copy app code
COPY . .

# Seed the database with initial data
RUN python -m app.seed

# Railway sets PORT automatically
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
