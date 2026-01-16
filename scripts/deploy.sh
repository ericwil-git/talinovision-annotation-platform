#!/bin/bash
# Deployment script for Video Annotation Platform

set -e

echo "🚀 Deploying Video Annotation Platform to Azure..."

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI is not installed. Please install it first."
    exit 1
fi

# Check if logged in
if ! az account show &> /dev/null; then
    echo "🔐 Please login to Azure..."
    az login
fi

# Variables
RESOURCE_GROUP="${AZURE_RESOURCE_GROUP:-rg-video-annotation}"
LOCATION="${AZURE_LOCATION:-eastus}"
ENVIRONMENT="${ENVIRONMENT:-dev}"

echo "📋 Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Location: $LOCATION"
echo "  Environment: $ENVIRONMENT"

# Create resource group
echo "📦 Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Deploy infrastructure
echo "🏗️  Deploying infrastructure with Bicep..."
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file infrastructure/main.bicep \
  --parameters infrastructure/parameters.$ENVIRONMENT.json \
  --parameters location=$LOCATION

# Get deployment outputs
echo "📤 Getting deployment outputs..."
STORAGE_ACCOUNT=$(az deployment group show --resource-group $RESOURCE_GROUP --name main --query properties.outputs.storageAccountName.value -o tsv)
ACR_NAME=$(az deployment group show --resource-group $RESOURCE_GROUP --name main --query properties.outputs.containerRegistryName.value -o tsv)
ML_WORKSPACE=$(az deployment group show --resource-group $RESOURCE_GROUP --name main --query properties.outputs.mlWorkspaceName.value -o tsv)

echo "✅ Infrastructure deployed!"
echo "  Storage Account: $STORAGE_ACCOUNT"
echo "  Container Registry: $ACR_NAME"
echo "  ML Workspace: $ML_WORKSPACE"

# Build and push Docker images
echo "🐳 Building and pushing Docker images..."
az acr build --registry $ACR_NAME --image annotation-service:latest ./annotation-service

# Update container app with new image
echo "🔄 Updating container app..."
ANNOTATION_SERVICE=$(az containerapp list --resource-group $RESOURCE_GROUP --query "[?contains(name, 'annotation')].name" -o tsv)
az containerapp update \
  --name $ANNOTATION_SERVICE \
  --resource-group $RESOURCE_GROUP \
  --image $ACR_NAME.azurecr.io/annotation-service:latest

echo ""
echo "✨ Deployment complete!"
echo ""
echo "📌 Next steps:"
echo "  1. Configure your .env file with the values above"
echo "  2. Run 'cd frontend-upload && npm run build' to build the frontend"
echo "  3. Deploy frontend: az staticwebapp deploy"
echo ""
echo "🌐 URLs will be available after frontend deployment"
