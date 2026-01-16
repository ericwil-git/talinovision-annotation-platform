# Azure Storage Network Configuration & Policy Management

## Summary

The video annotation platform storage account is configured to work reliably even with Azure policy enforcement. This document explains the configuration and how to handle policy-related issues.

## Current Configuration

### Storage Account Settings

- **Public Network Access**: `Enabled`
- **Shared Key Access**: `Disabled` (using managed identity only)
- **Network Bypass**: `AzureServices`
- **Default Action**: `Allow`

### Why This Configuration Works

1. **`publicNetworkAccess: Enabled`** - Allows Azure Container Apps to reach the storage account
2. **`bypass: AzureServices`** - Ensures Azure services (like Container Apps) can always access, even with restrictive network rules
3. **Managed Identity Authentication** - Uses Azure AD authentication, no shared keys needed
4. **`allowSharedKeyAccess: false`** - Enhanced security by disabling shared key access

## Azure Policy Status

### Detected Policies

The subscription has several **audit-only** policies that monitor storage account configuration:

- "Storage accounts should restrict network access"
- Various security baseline checks

**Important**: These policies are set to `audit` or `auditifnotexists` mode, which means they:

- ✅ **DO**: Report compliance status
- ❌ **DON'T**: Automatically change your configuration
- ❌ **DON'T**: Block deployments

### What If Public Access Gets Disabled Again?

If you find public network access disabled again, it could be due to:

1. **Manual change by administrator**
2. **Policy remediation task** (would need to be manually triggered)
3. **Azure Security Center recommendation** auto-applied

## Quick Fix

If storage access breaks again, run:

```bash
# Enable public access with Azure services bypass
az storage account update \
  -n vidanndevr5uc5ka6jxm4i \
  -g rg-vidann-dev \
  --public-network-access Enabled \
  --bypass AzureServices \
  --default-action Allow
```

## Monitoring

### Check Storage Configuration

```bash
./scripts/check-storage-policies.sh
```

This script will:

- Show current storage configuration
- List any policies affecting the storage account
- Report compliance status
- Provide recommendations

### Run Periodically

Consider running this weekly or after Azure policy updates:

```bash
# Add to cron or Azure DevOps pipeline
./scripts/check-storage-policies.sh
```

## Long-Term Secure Alternatives

For production environments with strict security policies, consider these alternatives:

### Option 1: Private Endpoints (Most Secure)

```bicep
resource privateEndpoint 'Microsoft.Network/privateEndpoints@2023-04-01' = {
  name: 'pe-storage'
  location: location
  properties: {
    subnet: {
      id: containerAppSubnetId
    }
    privateLinkServiceConnections: [{
      name: 'storage-connection'
      properties: {
        privateLinkServiceId: storageAccount.id
        groupIds: ['blob']
      }
    }]
  }
}
```

**Pros**:

- Fully private, no public access needed
- Complies with strictest security policies
- Traffic stays within Azure backbone

**Cons**:

- Requires VNet integration (~$7-10/month for private endpoint)
- More complex setup
- Frontend would need VNet integration too

### Option 2: Service Endpoints

```bicep
networkAcls: {
  bypass: 'AzureServices'
  defaultAction: 'Deny'
  virtualNetworkRules: [{
    id: containerAppSubnetId
    action: 'Allow'
  }]
}
```

**Pros**:

- No extra cost
- Simple to configure
- Good security

**Cons**:

- Requires VNet-integrated Container Apps
- Less isolation than Private Endpoints

### Option 3: Trusted Azure Services (Current)

```bicep
networkAcls: {
  bypass: 'AzureServices'
  defaultAction: 'Allow'
}
```

**Pros**:

- ✅ Simple and cost-effective
- ✅ Works with current setup
- ✅ Compatible with audit policies

**Cons**:

- Public endpoint remains enabled
- Less restrictive than alternatives

## Infrastructure as Code

The Bicep template has been updated to ensure this configuration persists:

```bicep
// infrastructure/main.bicep
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  properties: {
    publicNetworkAccess: 'Enabled'
    allowSharedKeyAccess: false
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
  }
}
```

## Deployment

The configuration will be maintained across deployments:

```bash
azd deploy
```

## Troubleshooting

### Backend Returns 401 Authorization Errors

1. Check public network access: `az storage account show -n <name> --query publicNetworkAccess`
2. Verify role assignments exist for the managed identity
3. Run the policy check script

### Projects Not Loading

1. Verify backend is running: `curl https://annotation-service.../health`
2. Check storage configuration: `./scripts/check-storage-policies.sh`
3. Review backend logs: `az containerapp logs show -n annotation-service`

## Contact

For Azure policy questions or to request policy exemptions, contact your Azure administrator.

## Last Updated

January 16, 2026
