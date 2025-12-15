# Use a specific Python version
FROM python:3.10-slim-bullseye

# Set working directory inside container
WORKDIR /app

# Install system dependencies needed for PyTorch and Postgres
RUN apt-get update && apt-get install -y \
    # Required for building psycopg2 (Postgres adapter)
    libpq-dev \
    # Required for compiling certain Python packages
    build-essential \
    # Clean up to reduce size
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage build cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Instead of running "python main.py", we run uvicorn directly.
# This gives you standard control over reload, workers, and ports.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]