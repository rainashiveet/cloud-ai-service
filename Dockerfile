# ============================================
# Dockerfile for Cloud-Native AI Inference Service
# ============================================
#
# A Dockerfile is like a recipe that tells Docker how to build your application image.
# Each line (instruction) adds a "layer" to the image.
#
# Think of it as:
# 1. Start with a base operating system (FROM)
# 2. Set up a working directory (WORKDIR)
# 3. Copy your files (COPY)
# 4. Install dependencies (RUN)
# 5. Define what runs when container starts (CMD)
#
# ============================================

# --------------------------------------------
# STAGE 1: Base Image
# --------------------------------------------
# FROM: Specifies the base image to start from.
# We use Python 3.10 slim version (lightweight, smaller download)
# "slim" images are smaller because they don't include unnecessary packages
FROM python:3.10-slim

# --------------------------------------------
# STAGE 2: Metadata
# --------------------------------------------
# LABEL: Adds metadata to the image (optional but good practice)
LABEL maintainer="Your Name <your.email@example.com>"
LABEL description="Cloud-Native AI Inference Service with FAISS"
LABEL version="1.0.0"

# --------------------------------------------
# STAGE 3: Environment Variables
# --------------------------------------------
# ENV: Sets environment variables inside the container
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files (not needed in production)
# PYTHONUNBUFFERED: Ensures Python output is sent straight to terminal (good for logs)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# --------------------------------------------
# STAGE 4: Working Directory
# --------------------------------------------
# WORKDIR: Sets the working directory inside the container
# Like doing "cd /app" inside the container
# If the directory doesn't exist, Docker creates it
WORKDIR /app

# --------------------------------------------
# STAGE 5: Install System Dependencies
# --------------------------------------------
# RUN: Executes a command during the build process
# We install system libraries needed for FAISS and other packages
# apt-get is the package manager for Debian-based Linux (what slim uses)
# We clean up apt cache to keep image small
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# --------------------------------------------
# STAGE 6: Install Python Dependencies
# --------------------------------------------
# COPY: Copies files from your computer into the container
# First path: source on your computer (relative to Dockerfile location)
# Second path: destination inside container
# We copy requirements.txt first (before all code) for caching efficiency
COPY requirements.txt .

# Install Python packages using pip
# --no-cache-dir: Don't cache downloaded packages (saves space)
# -r requirements.txt: Install all packages listed in the file
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --------------------------------------------
# STAGE 7: Copy Application Code
# --------------------------------------------
# Now copy all application code into the container
# The "." means "copy everything from current directory"
# This includes our app/ folder with main.py and inference.py
COPY . .

# --------------------------------------------
# STAGE 8: Expose Port
# --------------------------------------------
# EXPOSE: Documents which port the application uses
# This is like putting a sign on the door saying "this is door 8000"
# It doesn't actually open the port - you still need -p flag when running
EXPOSE 8000

# --------------------------------------------
# STAGE 9: Create Non-Root User (Security Best Practice)
# --------------------------------------------
# Running as non-root is more secure (if someone hacks the container,
# they have limited permissions)
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# --------------------------------------------
# STAGE 10: Start Command
# --------------------------------------------
# CMD: The command that runs when the container starts
# uvicorn: ASGI server that runs FastAPI
# app.main:app - looks for "app" variable in main.py inside app/ folder
# --host 0.0.0.0: Listen on all network interfaces (required for Docker)
# --port 8000: Use port 8000
#
# Note: In Docker, we use 0.0.0.0 instead of localhost
# localhost inside container = container itself, not accessible from outside
# 0.0.0.0 = all interfaces, accessible from outside the container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ============================================
# HOW TO BUILD AND RUN
# ============================================
#
# Build the image:
#   docker build -t ai-service .
#
# Run a container from the image:
#   docker run -p 8000:8000 ai-service
#
# -p 8000:8000 means: map port 8000 on your computer to port 8000 in container
# You can then access: http://localhost:8000
#
# ============================================
