# Use Python 3.11 slim image
FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install dependencies
RUN pip install --no-cache-dir \
    boto3==1.34.* \
    rich==13.7.*

# Copy application
COPY app.py .

# Make the script executable
RUN chmod +x app.py

# Run the application
CMD ["python", "app.py"]
