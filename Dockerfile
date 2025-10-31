# Use specific Python version (not just 3.10-slim which could become 3.10.99)
FROM python:3.10.15-slim

# Set working directory
WORKDIR /app

# Install system dependencies that won't change
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt /app/

# Upgrade pip to specific version and install dependencies
RUN pip install --no-cache-dir pip==24.0 setuptools==69.5.1 wheel==0.43.0 && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app/

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    mkdir -p /app/uploads && \
    chown -R appuser:appuser /app/uploads

USER appuser

# Expose port
EXPOSE 5000

# Run with exec form for proper signal handling
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:app"]