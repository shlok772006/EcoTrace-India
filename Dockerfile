# EcoTrace India — Dockerfile for Google Cloud Run
FROM python:3.11-slim

# Security: run as non-root user
RUN groupadd -r ecotrace && useradd -r -g ecotrace ecotrace

# Set working directory
WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Change ownership to non-root user
RUN chown -R ecotrace:ecotrace /app

# Switch to non-root user
USER ecotrace

# Cloud Run sets PORT env var (default 8080)
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run with gunicorn (matches Procfile)
CMD ["gunicorn", "--bind", ":8080", "--workers", "1", "--threads", "8", "app:app"]
