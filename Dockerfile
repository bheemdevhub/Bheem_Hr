# Dockerfile at root of Bheem_Hr/

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y git build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY ../../requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Debug: confirm uvicorn is installed
RUN which uvicorn || echo "Uvicorn is not installed!" && pip show uvicorn

# Copy the rest of the app
COPY . .

# Start the app
CMD ["uvicorn", "src.bheem_hr.main:app", "--host", "0.0.0.0", "--port", "8000"]
