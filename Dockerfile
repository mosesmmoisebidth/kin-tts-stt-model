# Use an official Python runtime as a parent image
FROM python:3.10.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install Git and system dependencies
RUN apt-get update && \
    apt-get install -y git build-essential && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip, setuptools, and wheel to the latest versions
RUN pip install --upgrade pip setuptools wheel

# Set the working directory in docker
WORKDIR /navigo-kinyarwanda-services

# Copy only requirements.txt first to leverage Docker layer caching
COPY requirements.txt /navigo-kinyarwanda-services/

# Install torch, torchvision and torchaudio CPU versions only to avoid NVIDIA packages
RUN pip install --no-cache-dir torch==2.3.1 torchvision==0.18.1 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cpu

# Install dependencies from requirements.txt with verbose logging and cache them
RUN pip install --no-cache-dir -v -r requirements.txt

# Copy the rest of the application files
COPY . /navigo-kinyarwanda-services

# Clone the TTS repository and install it with verbose logging
RUN git clone https://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@github.com/mosesmmoisebidth/torch-modified-tts.git /torch-modified-tts

# Set the working directory for TTS installation
WORKDIR /torch-modified-tts

# Install the TTS package from the cloned repository with verbose logging
RUN pip install -v .

# Copy the rest of the application files
WORKDIR /navigo-kinyarwanda-services
COPY . /navigo-kinyarwanda-services

# Specify the command to run on container start
CMD ["uvicorn", "api:api", "--host", "0.0.0.0", "--port", "80"]
