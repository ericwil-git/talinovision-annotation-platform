#!/bin/bash
# Script to check for Azure policies that might affect storage account configuration
# Run this periodically to monitor for policy changes

set -e

STORAGE_ACCOUNT="${AZURE_STORAGE_ACCOUNT_NAME:-vidanndevr5uc5ka6jxm4i}"
RESOURCE_GROUP="${AZURE_RESOURCE_GROUP:-rg-vidann-dev}"
SUBSCRIPTION="${AZURE_SUBSCRIPTION_ID:-a80ade45-139e-4ad0-855f-374b089cdbd9}"

echo "========================================"
echo "Azure Storage Policy Check"
echo "========================================"
echo "Storage Account: $STORAGE_ACCOUNT"
echo "Resource Group: $RESOURCE_GROUP"
echo ""

# Check current storage account configuration
echo "📊 Current Storage Configuration:"
az storage account show \
  -n $STORAGE_ACCOUNT \
  -g $RESOURCE_GROUP \
  --query "{
    publicAccess: publicNetworkAccess,
    sharedKeyAccess: allowSharedKeyAccess,
    networkBypass: networkRuleSet.bypass,
    networkDefaultAction: networkRuleSet.defaultAction
  }" -o table

echo ""

# Check for resource group level policies
echo "🔍 Checking Resource Group Policies..."
RG_POLICIES=$(az policy assignment list --resource-group $RESOURCE_GROUP --query "length([])" -o tsv)
if [ "$RG_POLICIES" = "0" ]; then
  echo "✓ No policies assigned at resource group level"
else
  echo "⚠️  Found $RG_POLICIES policy assignment(s) at resource group level:"
  az policy assignment list --resource-group $RESOURCE_GROUP \
    --query "[].{Name:displayName, Policy:policyDefinitionId}" -o table
fi

echo ""

# Check for subscription level policies affecting storage
echo "🔍 Checking Subscription-Level Storage Policies..."
STORAGE_POLICIES=$(az policy assignment list \
  --scope "/subscriptions/$SUBSCRIPTION" \
  --query "[?contains(policyDefinitionId, 'storage') || contains(displayName, 'storage') || contains(displayName, 'network') || contains(displayName, 'public')].{Name:displayName, Policy:policyDefinitionId, Enforcement:enforcementMode}" \
  -o json)

if [ "$(echo $STORAGE_POLICIES | jq 'length')" = "0" ]; then
  echo "✓ No storage-related policies found at subscription level"
else
  echo "⚠️  Found storage-related policies:"
  echo "$STORAGE_POLICIES" | jq -r '.[] | "  - \(.Name) (\(.Enforcement))"'
fi

echo ""

# Check policy compliance state
echo "🎯 Policy Compliance State:"
COMPLIANCE=$(az policy state list \
  --resource "/subscriptions/$SUBSCRIPTION/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Storage/storageAccounts/$STORAGE_ACCOUNT" \
  --query "[?complianceState=='NonCompliant'].{Policy:policyDefinitionName, Reason:policyDefinitionAction}" \
  -o json 2>/dev/null || echo "[]")

if [ "$(echo $COMPLIANCE | jq 'length')" = "0" ]; then
  echo "✓ Storage account is compliant with all policies"
else
  echo "⚠️  Non-compliant policies detected:"
  echo "$COMPLIANCE" | jq -r '.[] | "  - \(.Policy): \(.Reason)"'
fi

echo ""
echo "========================================"
echo "✅ Policy check complete"
echo ""
echo "Recommended Actions:"
echo "  1. If policies are found, review with your Azure administrator"
echo "  2. Consider using Private Endpoints for production environments"
echo "  3. Ensure 'bypass: AzureServices' is always enabled"
echo "  4. Keep managed identity authentication (no shared keys)"
echo "========================================"
