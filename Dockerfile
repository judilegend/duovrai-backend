FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies for WeasyPrint and compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libffi-dev \
    # WeasyPrint essential libraries
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libjpeg-dev \
    libopenjp2-7-dev \
    libcairo2 \
    libglib2.0-0 \
    shared-mime-info \
    # Additional fonts to make reports look gorgeous
    fonts-dejavu \
    fonts-liberation \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /workspace

# Copy requirements and install dependencies
COPY requirements.txt /workspace/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /workspace/

# Create directory for PDF storage and make sure it is writable
RUN mkdir -p /workspace/storage/reports && chmod -R 777 /workspace/storage

# Expose port
EXPOSE 8000

# Start FastAPI application using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
