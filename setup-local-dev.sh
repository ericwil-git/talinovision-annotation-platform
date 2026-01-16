#!/bin/bash
# Local development setup script for macOS

echo "Setting up local development environment..."

# Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install Python 3.11 if not installed
if ! command -v python3.11 &> /dev/null; then
    echo "Installing Python 3.11..."
    brew install python@3.11
fi

# Install ffmpeg for video processing
if ! command -v ffmpeg &> /dev/null; then
    echo "Installing ffmpeg..."
    brew install ffmpeg
fi

# Install Node.js 20 if needed
if ! command -v node &> /dev/null; then
    echo "Installing Node.js..."
    brew install node@20
fi

# Install Azure CLI if needed
if ! command -v az &> /dev/null; then
    echo "Installing Azure CLI..."
    brew install azure-cli
fi

# Create Python virtual environment
echo "Creating Python virtual environment..."
python3.11 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
if [ -f "annotation-service/requirements.txt" ]; then
    pip install -r annotation-service/requirements.txt
fi
if [ -f ".devcontainer/requirements.txt" ]; then
    pip install -r .devcontainer/requirements.txt
fi

# Install Azure CLI extensions
echo "Installing Azure CLI extensions..."
az extension add --name ml --only-show-errors 2>/dev/null || echo "Warning: ml extension install skipped"
az extension add --name containerapp --only-show-errors 2>/dev/null || echo "Warning: containerapp extension install skipped"

# Install npm packages for frontend
if [ -f "frontend-upload/package.json" ]; then
    echo "Installing frontend dependencies..."
    cd frontend-upload && npm install && cd ..
fi

# Install SWA CLI globally
npm install -g @azure/static-web-apps-cli

echo "✅ Local development environment setup complete!"
echo ""
echo "To activate the Python environment, run:"
echo "  source .venv/bin/activate"
