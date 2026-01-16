"""
Azure ML Training Pipeline for Custom Object Detection
Supports YOLOv8 training with COCO/YOLO format annotations
"""

import os
import argparse
from azure.ai.ml import MLClient
from azure.ai.ml.entities import Environment, Command, Data
from azure.ai.ml.constants import AssetTypes
from azure.identity import DefaultAzureCredential
from pathlib import Path

def create_training_pipeline(
    workspace_name: str,
    resource_group: str,
    subscription_id: str,
    compute_name: str = "gpu-cluster",
    experiment_name: str = "video-annotation-training"
):
    """Create and submit Azure ML training pipeline"""
    
    # Authenticate
    credential = DefaultAzureCredential()
    ml_client = MLClient(
        credential=credential,
        subscription_id=subscription_id,
        resource_group_name=resource_group,
        workspace_name=workspace_name
    )
    
    # Create custom environment with YOLOv8
    environment = Environment(
        name="yolov8-training-env",
        description="YOLOv8 training environment",
        conda_file="environment.yml",
        image="mcr.microsoft.com/azureml/openmpi4.1.0-cuda11.6-cudnn8-ubuntu20.04:latest"
    )
    
    # Register environment
    ml_client.environments.create_or_update(environment)
    
    # Create training command
    job = Command(
        code="./training",
        command="python train_yolo.py --data ${{inputs.dataset}} --epochs ${{inputs.epochs}} --batch ${{inputs.batch_size}} --output ${{outputs.model}}",
        environment=f"{environment.name}@latest",
        compute=compute_name,
        experiment_name=experiment_name,
        display_name="Custom Object Detection Training",
        inputs={
            "dataset": Input(type=AssetTypes.URI_FOLDER),
            "epochs": 100,
            "batch_size": 16
        },
        outputs={
            "model": Output(type=AssetTypes.MLFLOW_MODEL)
        }
    )
    
    # Submit job
    returned_job = ml_client.jobs.create_or_update(job)
    print(f"Training job submitted: {returned_job.name}")
    print(f"Job URL: {returned_job.studio_url}")
    
    return returned_job

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-name", required=True)
    parser.add_argument("--resource-group", required=True)
    parser.add_argument("--subscription-id", required=True)
    parser.add_argument("--compute-name", default="gpu-cluster")
    parser.add_argument("--experiment-name", default="video-annotation-training")
    
    args = parser.parse_args()
    
    create_training_pipeline(
        workspace_name=args.workspace_name,
        resource_group=args.resource_group,
        subscription_id=args.subscription_id,
        compute_name=args.compute_name,
        experiment_name=args.experiment_name
    )
