#!/bin/bash
# Scheduled watchdog script - keeps storage public access enabled
# Add this to crontab to run every hour: 0 * * * * /path/to/watchdog-storage-access.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/../logs/storage-watchdog.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "====== Storage Watchdog Check ======"

# Source azd environment
cd "$SCRIPT_DIR/.." || exit 1

STORAGE_ACCOUNT=$(azd env get-values 2>/dev/null | grep storageAccountName | cut -d '=' -f2 | tr -d '"')
RESOURCE_GROUP=$(azd env get-values 2>/dev/null | grep AZURE_RESOURCE_GROUP | cut -d '=' -f2 | tr -d '"')

if [ -z "$STORAGE_ACCOUNT" ] || [ -z "$RESOURCE_GROUP" ]; then
    log "ERROR: Could not find storage account or resource group"
    exit 1
fi

# Check current status
CURRENT_STATUS=$(az storage account show \
    --name "$STORAGE_ACCOUNT" \
    --resource-group "$RESOURCE_GROUP" \
    --query 'publicNetworkAccess' \
    -o tsv 2>/dev/null)

log "Storage: $STORAGE_ACCOUNT | Status: $CURRENT_STATUS"

if [ "$CURRENT_STATUS" != "Enabled" ]; then
    log "⚠️  PUBLIC ACCESS DISABLED - Fixing..."
    
    az storage account update \
        --name "$STORAGE_ACCOUNT" \
        --resource-group "$RESOURCE_GROUP" \
        --public-network-access Enabled 2>&1 | tee -a "$LOG_FILE"
    
    log "✅ Fixed - public access re-enabled"
    
    # Send alert (optional - configure email/Teams webhook)
    # curl -X POST "YOUR_WEBHOOK_URL" -d "Storage public access was disabled and has been fixed"
else
    log "✅ Status OK"
fi

log "======================================"
