# Base Ubuntu image for LLM VM
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV WORKSPACE_DIR=/workspace
ENV VM_PORT=8080

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

# Copy application files
COPY . /app/
WORKDIR /app

# Install Python packages
RUN pip3 install --no-cache-dir -r requirements.txt

# Setup security constraints
RUN useradd -m -s /bin/bash llmuser
RUN chown -R llmuser:llmuser ${WORKSPACE_DIR}
RUN chown -R llmuser:llmuser /app
USER llmuser

# Expose VM API port
EXPOSE ${VM_PORT}

# Start VM API server
CMD ["python3", "vm_api.py"] 