FROM mcr.microsoft.com/devcontainers/python:3.11

# Install system dependencies for OpenCV and Node.js
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    curl \
    ca-certificates \
    apt-transport-https \
    lsb-release \
    gnupg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Azure CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# Install Node.js 20 LTS
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Azure CLI extensions (do this before Python packages for better caching)
RUN az extension add --name ml --system --only-show-errors 2>/dev/null || true \
    && az extension add --name containerapp --system --only-show-errors 2>/dev/null || true

# Copy requirements and install Python packages
# Copy requirements first for better layer caching
COPY requirements.txt /tmp/devcontainer-requirements.txt
RUN pip install --no-cache-dir -r /tmp/devcontainer-requirements.txt \
    && rm /tmp/devcontainer-requirements.txt

# Install npm global packages
RUN npm install -g @azure/static-web-apps-cli

# Set working directory
WORKDIR /workspace

# Keep container running
CMD ["sleep", "infinity"]
