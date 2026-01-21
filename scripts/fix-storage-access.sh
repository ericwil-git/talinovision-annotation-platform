#!/bin/bash
# Script to fix storage public access issue
# Run this if the site is broken due to storage access

set -e

echo "🔍 Checking storage account status..."

# Get storage account name from azd environment
STORAGE_ACCOUNT=$(azd env get-values | grep storageAccountName | cut -d '=' -f2 | tr -d '"')
RESOURCE_GROUP=$(azd env get-values | grep AZURE_RESOURCE_GROUP | cut -d '=' -f2 | tr -d '"')

if [ -z "$STORAGE_ACCOUNT" ] || [ -z "$RESOURCE_GROUP" ]; then
    echo "❌ Could not find storage account or resource group from azd environment"
    exit 1
fi

echo "📦 Storage Account: $STORAGE_ACCOUNT"
echo "📁 Resource Group: $RESOURCE_GROUP"

# Check current status
CURRENT_STATUS=$(az storage account show \
    --name "$STORAGE_ACCOUNT" \
    --resource-group "$RESOURCE_GROUP" \
    --query 'publicNetworkAccess' \
    -o tsv)

echo "📊 Current public network access: $CURRENT_STATUS"

if [ "$CURRENT_STATUS" != "Enabled" ]; then
    echo "🔧 Enabling public network access..."
    az storage account update \
        --name "$STORAGE_ACCOUNT" \
        --resource-group "$RESOURCE_GROUP" \
        --public-network-access Enabled
    
    echo "✅ Public network access enabled"
    echo "⏳ Waiting 10 seconds for changes to propagate..."
    sleep 10
else
    echo "✅ Public network access is already enabled"
fi

# Test backend health
BACKEND_URL=$(azd env get-values | grep annotationServiceUrl | cut -d '=' -f2 | tr -d '"')
echo ""
echo "🧪 Testing backend health..."
if curl -sf "https://$BACKEND_URL/health" > /dev/null; then
    echo "✅ Backend is healthy!"
else
    echo "⚠️  Backend health check failed. You may need to wait a bit longer or check logs."
fi

echo ""
echo "✅ Done! Site should be working now."
echo "🌐 Backend: https://$BACKEND_URL"
echo "🌐 Projects: https://$BACKEND_URL/"
