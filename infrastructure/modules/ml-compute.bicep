// Azure ML Compute Cluster
targetScope = 'resourceGroup'

@description('ML Workspace name')
param workspaceName string

@description('Compute cluster name')
param computeName string = 'gpu-cluster'

@description('Location')
param location string = resourceGroup().location

@description('VM Size')
param vmSize string = 'Standard_NC4as_T4_v3'

@description('Minimum nodes')
param minNodes int = 0

@description('Maximum nodes')
param maxNodes int = 4

resource mlWorkspace 'Microsoft.MachineLearningServices/workspaces@2023-10-01' existing = {
  name: workspaceName
}

resource computeCluster 'Microsoft.MachineLearningServices/workspaces/computes@2023-10-01' = {
  parent: mlWorkspace
  name: computeName
  location: location
  properties: {
    computeType: 'AmlCompute'
    properties: {
      vmSize: vmSize
      vmPriority: 'LowPriority'
      scaleSettings: {
        minNodeCount: minNodes
        maxNodeCount: maxNodes
        nodeIdleTimeBeforeScaleDown: 'PT120S'
      }
    }
  }
}

output computeId string = computeCluster.id
