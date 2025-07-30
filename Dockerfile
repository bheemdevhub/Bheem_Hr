# Use a lightweight Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required by some Python packages
RUN apt-get update && apt-get install -y gcc libffi-dev && apt-get clean

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire app
COPY . .

# Expose FastAPI default port
EXPOSE 8000

# Start FastAPI using Uvicorn
CMD ["uvicorn", "src.bheem_hr.main:app", "--host", "0.0.0.0", "--port", "8000"]
