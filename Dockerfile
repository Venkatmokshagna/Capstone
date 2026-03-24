# ── Stage: Build the Flask application ──────────────────────────
FROM python:3.10-slim

# Set working directory inside container
WORKDIR /app

# Install system dependencies (needed for mysql-connector-python & bcrypt)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first (cache-friendly layer)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose Flask port
EXPOSE 5000

# Start the Flask app using Gunicorn for production
CMD ["gunicorn", "--workers=2", "--timeout=120", "--bind=0.0.0.0:5000", "app:app"]
