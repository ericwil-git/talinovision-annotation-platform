"""
Deploy trained model to Azure ML Batch Endpoint
"""

import os
import argparse
from azure.ai.ml import MLClient
from azure.ai.ml.entities import (
    BatchEndpoint,
    BatchDeployment,
    Model,
    Environment,
    CodeConfiguration
)
from azure.identity import DefaultAzureCredential

def deploy_batch_endpoint(
    workspace_name: str,
    resource_group: str,
    subscription_id: str,
    model_name: str,
    endpoint_name: str = "video-detection-batch",
    compute_name: str = "cpu-cluster"
):
    """Deploy model to batch endpoint"""
    
    # Authenticate
    credential = DefaultAzureCredential()
    ml_client = MLClient(
        credential=credential,
        subscription_id=subscription_id,
        resource_group_name=resource_group,
        workspace_name=workspace_name
    )
    
    # Create batch endpoint
    endpoint = BatchEndpoint(
        name=endpoint_name,
        description="Batch inference for custom video detection model",
    )
    
    ml_client.batch_endpoints.begin_create_or_update(endpoint).result()
    print(f"Batch endpoint '{endpoint_name}' created/updated")
    
    # Get latest model version
    model = ml_client.models.get(name=model_name, label="latest")
    
    # Create deployment
    deployment = BatchDeployment(
        name="default",
        endpoint_name=endpoint_name,
        model=model,
        compute=compute_name,
        instance_count=1,
        max_concurrency_per_instance=2,
        mini_batch_size=10,
        output_action="append_row",
        output_file_name="predictions.csv",
        retry_settings={
            "max_retries": 3,
            "timeout": 300
        },
        logging_level="info",
        environment=Environment(
            image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu20.04:latest",
            conda_file="deployment_environment.yml"
        ),
        code_configuration=CodeConfiguration(
            code="./scoring",
            scoring_script="score.py"
        )
    )
    
    ml_client.batch_deployments.begin_create_or_update(deployment).result()
    print(f"Deployment 'default' created on endpoint '{endpoint_name}'")
    
    # Set as default deployment
    endpoint.defaults = {"deployment_name": "default"}
    ml_client.batch_endpoints.begin_create_or_update(endpoint).result()
    
    print(f"✅ Model deployed successfully!")
    print(f"Endpoint: {endpoint_name}")
    
    return endpoint

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-name", required=True)
    parser.add_argument("--resource-group", required=True)
    parser.add_argument("--subscription-id", required=True)
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--endpoint-name", default="video-detection-batch")
    parser.add_argument("--compute-name", default="cpu-cluster")
    
    args = parser.parse_args()
    
    deploy_batch_endpoint(
        workspace_name=args.workspace_name,
        resource_group=args.resource_group,
        subscription_id=args.subscription_id,
        model_name=args.model_name,
        endpoint_name=args.endpoint_name,
        compute_name=args.compute_name
    )
