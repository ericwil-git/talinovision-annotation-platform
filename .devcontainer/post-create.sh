#!/bin/bash
set -e

echo "Installing Azure CLI extensions..."
az extension add --name ml --only-show-errors || echo "Warning: Failed to install ml extension"
az extension add --name containerapp --only-show-errors || echo "Warning: Failed to install containerapp extension"

echo "Installing Python packages..."
pip install --user -r .devcontainer/requirements.txt

echo "Installing npm global packages..."
npm install -g @azure/static-web-apps-cli

echo "Post-create setup completed successfully!"
