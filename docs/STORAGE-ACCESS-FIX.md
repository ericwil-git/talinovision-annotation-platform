# Storage Public Access Fix

## Problem
The storage account's `publicNetworkAccess` setting keeps getting disabled daily, breaking the site.

## Root Cause Investigation
Based on investigation, possible causes:
1. **Azure Policy** (subscription or management group level)
2. **Security Center Auto-Remediation** 
3. **Scheduled Automation**
4. **Manual Changes**

Run the investigation script to identify the cause:
```bash
./scripts/investigate-storage-changes.sh
```

## Solutions Implemented

### 1. Quick Fix Script (Immediate Use)
When the site is broken, run:
```bash
./scripts/fix-storage-access.sh
```

This script:
- ✅ Checks current storage public access status
- ✅ Re-enables it if disabled
- ✅ Tests backend health
- ✅ Shows URLs to verify

**Use this every morning if the site is broken.**

### 2. Automated Watchdog (Preventive)
A monitoring script that automatically fixes the issue:
```bash
./scripts/watchdog-storage-access.sh
```

#### Setup as Cron Job (Linux/Mac)
```bash
# Edit crontab
crontab -e

# Add this line to run every hour at :00
0 * * * * cd /workspaces/video-annotation-platform && ./scripts/watchdog-storage-access.sh

# Or run every 30 minutes
*/30 * * * * cd /workspaces/video-annotation-platform && ./scripts/watchdog-storage-access.sh
```

#### Setup as Scheduled Task (Windows)
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily, repeat every 1 hour
4. Action: Start program
   - Program: `bash`
   - Arguments: `/workspaces/video-annotation-platform/scripts/watchdog-storage-access.sh`

The watchdog creates logs at: `logs/storage-watchdog.log`

### 3. Azure Automation Runbook (Cloud-Based)
For a cloud-native solution, create an Azure Automation runbook:

```powershell
# PowerShell runbook example
$resourceGroup = "rg-vidann-dev"
$storageAccount = "vidanndevr5uc5ka6jxm4i"

$status = (Get-AzStorageAccount -ResourceGroupName $resourceGroup -Name $storageAccount).PublicNetworkAccess

if ($status -ne "Enabled") {
    Write-Output "Public access is $status - enabling..."
    Set-AzStorageAccount -ResourceGroupName $resourceGroup `
                         -Name $storageAccount `
                         -PublicNetworkAccess Enabled
    Write-Output "Fixed!"
} else {
    Write-Output "Status OK"
}
```

Schedule this runbook to run hourly.

### 4. Infrastructure Lock (Attempted)
We attempted to add a resource lock in Bicep:
```bicep
resource storageAccountLock 'Microsoft.Authorization/locks@2020-05-01' = {
  scope: storageAccount
  name: 'prevent-public-access-changes'
  properties: {
    level: 'CanNotDelete'
    notes: 'Prevents deletion and helps preserve settings'
  }
}
```

Note: `CanNotDelete` locks don't prevent property modifications, only deletion. `ReadOnly` locks would prevent changes but also prevent the app from working.

## Long-Term Solution

The proper fix is to redesign the architecture to not require public network access:

### Option A: Private Endpoints
```bicep
resource privateEndpoint 'Microsoft.Network/privateEndpoints@2023-05-01' = {
  name: 'pe-storage'
  location: location
  properties: {
    subnet: {
      id: containerAppSubnet.id
    }
    privateLinkServiceConnections: [
      {
        name: 'storage-connection'
        properties: {
          privateLinkServiceId: storageAccount.id
          groupIds: ['blob']
        }
      }
    ]
  }
}
```

### Option B: Service Endpoints with VNet Integration
- Deploy Container App to a VNet subnet
- Enable service endpoints for storage
- Configure storage firewall to only allow VNet access
- Keep `publicNetworkAccess: Disabled`

### Option C: Managed Identity with Private Access Only
The current setup uses managed identity but still requires public access. With private endpoints, you can keep public access disabled permanently.

## Monitoring

Check watchdog logs:
```bash
tail -f logs/storage-watchdog.log
```

Check Azure activity logs:
```bash
az monitor activity-log list \
  --resource-group rg-vidann-dev \
  --start-time "$(date -u -d '1 day ago' '+%Y-%m-%dT%H:%M:%SZ')" \
  --query "[?contains(operationName.value, 'storageAccounts')]"
```

## Recommended Actions

1. **Immediate**: Set up the cron job with `watchdog-storage-access.sh`
2. **This Week**: Identify who/what is changing the setting using the investigation script
3. **Next Sprint**: Implement proper private endpoint architecture
4. **Future**: Enable Azure Policy exemption or modify the policy

## Testing

Test the fix script:
```bash
# Check current status
az storage account show --name vidanndevr5uc5ka6jxm4i \
  --resource-group rg-vidann-dev \
  --query '{publicNetworkAccess:publicNetworkAccess}'

# Run fix
./scripts/fix-storage-access.sh

# Verify site works
curl https://annotation-service.bluemushroom-befb422f.eastus2.azurecontainerapps.io/health
```

## Support

If the scripts don't work:
1. Check Azure CLI is logged in: `az account show`
2. Check you have permissions: `az role assignment list --assignee $(az account show --query user.name -o tsv)`
3. Check the logs: `cat logs/storage-watchdog.log`
4. Manually enable: `az storage account update --name vidanndevr5uc5ka6jxm4i --resource-group rg-vidann-dev --public-network-access Enabled`
