#!/bin/bash
# Monitor script to identify who/what is disabling public access
# This helps diagnose the root cause

set -e

STORAGE_ACCOUNT=$(azd env get-values | grep storageAccountName | cut -d '=' -f2 | tr -d '"')
RESOURCE_GROUP=$(azd env get-values | grep AZURE_RESOURCE_GROUP | cut -d '=' -f2 | tr -d '"')

echo "🔍 Investigating recent changes to storage account: $STORAGE_ACCOUNT"
echo ""

# Check for Azure Policy assignments
echo "📋 Checking for Azure Policies..."
POLICIES=$(az policy assignment list \
    --resource-group "$RESOURCE_GROUP" \
    --query "[].{name:displayName, definition:policyDefinitionId}" \
    -o table 2>/dev/null || echo "No policies found at resource group level")

echo "$POLICIES"
echo ""

# Check subscription-level policies
echo "📋 Checking subscription-level policies..."
SUB_POLICIES=$(az policy assignment list \
    --query "[?contains(displayName, 'storage') || contains(displayName, 'Storage') || contains(displayName, 'public') || contains(displayName, 'network')].{name:displayName, enforcement:enforcementMode}" \
    -o table 2>/dev/null || echo "No relevant subscription policies found")

echo "$SUB_POLICIES"
echo ""

# Check activity logs for storage modifications
echo "🕐 Checking activity logs (last 7 days) for storage account modifications..."
echo ""

# Get storage resource ID
STORAGE_ID="/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Storage/storageAccounts/$STORAGE_ACCOUNT"

# Check for write operations on storage account
az monitor activity-log list \
    --resource-id "$STORAGE_ID" \
    --start-time "$(date -u -d '7 days ago' '+%Y-%m-%dT%H:%M:%SZ')" \
    --query "[?contains(operationName.value, 'write') || contains(operationName.value, 'update')].{Time:eventTimestamp, Operation:operationName.localizedValue, Caller:caller, Status:status.localizedValue}" \
    -o table 2>/dev/null || echo "Could not retrieve activity logs"

echo ""

# Check for Defender for Cloud / Security Center recommendations
echo "🛡️  Checking for Security Center assessments..."
az security assessment list \
    --query "[?contains(resourceDetails.Id, '$STORAGE_ACCOUNT')].{Assessment:displayName, Status:status.code, Severity:metadata.severity}" \
    -o table 2>/dev/null || echo "Could not retrieve security assessments (may require 'Security Reader' role)"

echo ""
echo "💡 Common causes:"
echo "   1. Azure Policy enforcing 'publicNetworkAccess: Disabled'"
echo "   2. Security Center auto-remediation"
echo "   3. Scheduled automation/runbook"
echo "   4. Manual changes by other users"
echo ""
echo "🔒 Resource lock status:"
az lock list --resource-group "$RESOURCE_GROUP" \
    --resource-name "$STORAGE_ACCOUNT" \
    --resource-type "Microsoft.Storage/storageAccounts" \
    --query "[].{Name:name, Level:level, Notes:notes}" \
    -o table 2>/dev/null || echo "No locks found (lock deployment may be in progress)"
