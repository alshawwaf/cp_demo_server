# Use official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies as root
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    mingw-w64 \
    libcurl4-openssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Add a non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser -d /home/appuser appuser

# Set the working directory
WORKDIR /usr/src/app/

# Copy requirements.txt into the container
COPY requirements.txt .

# Install Python dependencies
RUN python -m pip install --no-cache-dir --upgrade pip && python -m pip install --no-cache-dir -r requirements.txt


# Copy the entire project into the container
COPY . .

# Create a writable local directory for the appuser
RUN mkdir -p /usr/src/app/app/data && \
    chown -R appuser:appuser /usr/src/app/app && \
    mkdir -p /home/appuser/.local && \
    chown -R appuser:appuser /home/appuser

# Switch to the non-root user
USER appuser

# Update PATH for the local user pip installation
ENV PATH="/home/appuser/.local/bin:$PATH"

# Expose port 8080
EXPOSE 8080

# Run the application as a module
CMD ["python", "run.py"]
