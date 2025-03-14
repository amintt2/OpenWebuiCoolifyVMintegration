# Base Ubuntu image for OpenWebUI backend
FROM ubuntu:22.04

# Build arguments
ARG REPO_URL=https://github.com/amintt2/OpenWebui.git
ARG REPO_BRANCH=main

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV WORKSPACE_DIR=/workspace
ENV VM_PORT=8080
ENV API_HOST=0.0.0.0
ENV API_TIMEOUT=120
ENV ENABLE_AUTH=false
ENV LOG_LEVEL=info

# Install basic utilities and Python
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    curl \
    wget \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Create workspace directory
RUN mkdir -p ${WORKSPACE_DIR}
WORKDIR ${WORKSPACE_DIR}

# Clone the repository
RUN git clone -b ${REPO_BRANCH} ${REPO_URL} /app
WORKDIR /app

# Install Python packages
RUN pip3 install --no-cache-dir -r requirements.txt

# Setup security constraints
RUN useradd -m -s /bin/bash appuser
RUN chown -R appuser:appuser ${WORKSPACE_DIR}
RUN chown -R appuser:appuser /app
USER appuser

# Create log directory if needed
RUN mkdir -p /app/logs && chown -R appuser:appuser /app/logs

# Expose VM API port
EXPOSE ${VM_PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:${VM_PORT}/api/v1/health || exit 1

# Start VM API server
CMD ["python3", "vm_api.py"] 