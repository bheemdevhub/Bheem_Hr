# Use a lightweight Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required by some Python packages
RUN apt-get update && apt-get install -y gcc libffi-dev git && apt-get clean

# Copy requirements.txt first and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Install current module (in case it's editable or has dependencies)
RUN pip install --no-cache-dir .

# Expose FastAPI default port
EXPOSE 8000

# Start FastAPI with Uvicorn
CMD ["uvicorn", "src.bheem_hr.main:app", "--host", "0.0.0.0", "--port", "8000"]
