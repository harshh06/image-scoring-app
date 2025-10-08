# Use a specific Python version for reproducibility
FROM python:3.10-slim-bullseye

# Set working directory inside container
WORKDIR /app

# Install system dependencies needed for libraries like psycopg2, OpenCV, and Tesseract
RUN apt-get update && apt-get install -y \
    postgresql-client \
    tesseract-ocr \
    libtesseract-dev \
    libpq-dev \
    libgl1-mesa-glx \
    libsm6 \
    libxext6 \
    build-essential \
    # Install English language data for Tesseract
    tesseract-ocr-eng \
    # Clean up apt caches to reduce final image size
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker's build cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Command to run your FastAPI application with Uvicorn
# Using "python -m uvicorn" is a reliable way to execute the module.
# The --reload flag enables auto-reloading for development.
CMD ["python", "-m", "main", "--host", "0.0.0.0", "--port", "8000", "--reload"]

