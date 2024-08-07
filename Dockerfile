# Use an official Python runtime as a parent image
FROM python:3.10.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in docker
WORKDIR /navigo-trans-service

# Install system dependencies and git
RUN apt-get update && apt-get install -y git

# Copy the current directory contents into the container at /app
COPY . /navigo-trans-service

# Retry logic for installing packages from requirements.txt
RUN set -eux; \
    retry_count=0; \
    max_retries=30; \
    until [ "$retry_count" -ge "$max_retries" ]; do \
        pip install --no-cache-dir -r /navigo-trans-service/requirements.txt && \
        break; \
        retry_count=$((retry_count+1)); \
        echo "Retry $retry_count/$max_retries"; \
        sleep 5; \
    done

# Specify the command to run on container start
CMD ["uvicorn", "api:api", "--host", "0.0.0.0", "--port", "80"]
