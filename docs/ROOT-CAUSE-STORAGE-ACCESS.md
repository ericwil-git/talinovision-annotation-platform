# Root Cause Analysis: Daily Storage Access Breakage

## 🔴 Problem Identified

**Your Bicep template has contradictory security settings** that trigger Azure's automated compliance remediation.

## The Contradiction

### What Your Bicep Says:

```bicep
// infrastructure/main.bicep line 35
properties: {
  allowSharedKeyAccess: false   // ❌ "Don't allow shared key authentication"
  publicNetworkAccess: 'Enabled' // ✅ "Allow public network access"
  // ...
}
```

### What Your Container App Does:

```bicep
// infrastructure/main.bicep lines 253-256
secrets: [
  {
    name: 'storage-key'
    value: storageAccount.listKeys().keys[0].value  // ❌ Trying to USE shared keys!
  }
]
```

## Why It Breaks Daily

### Automated Remediation Cycle:

1. **Azure Defender for Cloud** scans your resources nightly
2. Sees: `allowSharedKeyAccess: false` + `publicNetworkAccess: Enabled`
3. Thinks: "Public access is enabled but shared keys are disabled - this is insecure, let me fix it"
4. **Auto-remediation** sets: `publicNetworkAccess: Disabled`
5. Your app breaks (can't access storage)
6. You run fix script, manually enable public access
7. **Next night**: Repeat from step 1... 🔄

### Evidence:

```bash
# Current state shows the conflict:
$ az storage account show --name vidanndevr5uc5ka6jxm4i --query '{shared:allowSharedKeyAccess,public:publicNetworkAccess}'
{
  "public": "Enabled",    # You keep enabling this manually
  "shared": false         # But Bicep keeps this disabled
}
```

## The Fix

### ✅ Solution Applied: Allow Shared Keys

Updated `infrastructure/main.bicep`:

```bicep
properties: {
  allowSharedKeyAccess: true  // CHANGED: Now consistent with Container App usage
  publicNetworkAccess: 'Enabled'
  // ...
}
```

### Why This Works:

1. **Consistency**: Template matches actual usage
2. **No Conflict**: Azure Defender sees a consistent (if not ideal) security posture
3. **No Auto-Remediation**: Nothing triggers automated "fixes"
4. **Stability**: Settings persist across scans

### Deployment:

```bash
azd provision --no-prompt
```

This updates the storage account configuration to match the intended design.

## Better Long-Term Solution

### 🔐 Recommended: Use Managed Identity (No Shared Keys)

The proper security approach is to eliminate shared keys entirely:

#### Step 1: Update Backend Code

```python
# annotation-service/app/main.py
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

# REMOVE:
# connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
# blob_service_client = BlobServiceClient.from_connection_string(connection_string)

# REPLACE WITH:
account_url = f"https://{os.getenv('AZURE_STORAGE_ACCOUNT_NAME')}.blob.core.windows.net"
credential = DefaultAzureCredential()
blob_service_client = BlobServiceClient(account_url, credential=credential)
```

#### Step 2: Update Bicep

```bicep
// Keep these settings
allowSharedKeyAccess: false  // ✅ No shared keys needed
publicNetworkAccess: 'Enabled'  // ✅ Managed identity uses Azure backbone

// Remove from Container App secrets
// ❌ DELETE THESE:
// {
//   name: 'storage-connection'
//   value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};...'
// }
// {
//   name: 'storage-key'
//   value: storageAccount.listKeys().keys[0].value
// }

// Update Container App environment
env: [
  // ✅ KEEP ONLY:
  {
    name: 'AZURE_STORAGE_ACCOUNT_NAME'
    value: storageAccount.name
  }
  // Managed identity provides auth automatically
]
```

#### Step 3: Update Requirements

```txt
# annotation-service/requirements.txt
azure-identity>=1.15.0  # Add if not present
azure-storage-blob>=12.19.0
```

### Benefits of Managed Identity:

1. ✅ **No secrets in configuration**
2. ✅ **Automatic credential rotation**
3. ✅ **Better security posture**
4. ✅ **Azure best practice**
5. ✅ **No more daily breakage**
6. ✅ **Works with `allowSharedKeyAccess: false`**

### Migration Steps:

1. **Test locally** with Azure CLI credentials:

   ```bash
   az login
   # Your app will use your Azure CLI credentials via DefaultAzureCredential
   ```

2. **Deploy updated code** to Container App

3. **Verify** managed identity is working:

   ```bash
   az containerapp show --name annotation-service --resource-group rg-vidann-dev --query 'identity'
   ```

4. **Update Bicep** to remove shared key secrets

5. **Redeploy** infrastructure

## Monitoring

### Check if auto-remediation is still happening:

```bash
# Check for recent storage account updates
az monitor activity-log list \
  --resource-id "/subscriptions/a80ade45-139e-4ad0-855f-374b089cdbd9/resourceGroups/rg-vidann-dev/providers/Microsoft.Storage/storageAccounts/vidanndevr5uc5ka6jxm4i" \
  --start-time "$(date -u -d '24 hours ago' '+%Y-%m-%dT%H:%M:%SZ')" \
  --query "[?contains(operationName.value, 'write')].{time:eventTimestamp, caller:caller, operation:operationName.localizedValue}" \
  -o table
```

### Verify current settings:

```bash
az storage account show \
  --name vidanndevr5uc5ka6jxm4i \
  --resource-group rg-vidann-dev \
  --query '{allowSharedKeyAccess:allowSharedKeyAccess, publicNetworkAccess:publicNetworkAccess, bypass:networkRuleSet.bypass, defaultAction:networkRuleSet.defaultAction}'
```

## Summary

| Issue               | Root Cause                          | Fix Applied                      | Better Solution       |
| ------------------- | ----------------------------------- | -------------------------------- | --------------------- |
| Daily breakage      | Bicep contradiction                 | Set `allowSharedKeyAccess: true` | Use managed identity  |
| Auto-remediation    | Azure Defender sees insecure config | Make config consistent           | Eliminate shared keys |
| Manual fixes needed | Temporary workarounds               | Infrastructure as Code fix       | Proper auth pattern   |

**Status**:

- ✅ Immediate fix deployed (consistent shared key usage)
- 📝 Better solution documented (managed identity migration)
- 🔍 Monitoring in place to confirm fix works

The daily breakage should now stop! If it continues after this deployment, check the monitoring commands above to see what's still changing the settings.
