"""
YOLOv8 Training Script for Azure ML
"""

import os
import argparse
from pathlib import Path
from ultralytics import YOLO
import mlflow
import yaml

def train_yolo_model(
    data_path: str,
    epochs: int = 100,
    batch_size: int = 16,
    img_size: int = 640,
    model_size: str = "n",  # n, s, m, l, x
    output_dir: str = "./outputs"
):
    """Train YOLOv8 model on custom dataset"""
    
    # Start MLflow run
    mlflow.start_run()
    
    # Log parameters
    mlflow.log_param("epochs", epochs)
    mlflow.log_param("batch_size", batch_size)
    mlflow.log_param("img_size", img_size)
    mlflow.log_param("model_size", model_size)
    
    # Initialize model
    model = YOLO(f"yolov8{model_size}.pt")
    
    # Train model
    results = model.train(
        data=data_path,
        epochs=epochs,
        batch=batch_size,
        imgsz=img_size,
        project=output_dir,
        name="custom_detection",
        exist_ok=True,
        save=True,
        plots=True,
        verbose=True
    )
    
    # Log metrics
    metrics = results.results_dict
    for key, value in metrics.items():
        if isinstance(value, (int, float)):
            mlflow.log_metric(key, value)
    
    # Save model
    model_path = Path(output_dir) / "custom_detection" / "weights" / "best.pt"
    mlflow.pytorch.log_model(model, "model")
    
    # Export to ONNX for deployment
    onnx_path = model.export(format="onnx")
    mlflow.log_artifact(onnx_path, "onnx_model")
    
    print(f"Training complete! Model saved to: {model_path}")
    print(f"ONNX model: {onnx_path}")
    
    mlflow.end_run()
    
    return model_path

def validate_dataset(data_path: str):
    """Validate dataset structure"""
    data_yaml = Path(data_path)
    
    if not data_yaml.exists():
        raise FileNotFoundError(f"Data config not found: {data_path}")
    
    with open(data_yaml, 'r') as f:
        config = yaml.safe_load(f)
    
    required_keys = ['train', 'val', 'nc', 'names']
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required key in data config: {key}")
    
    print("Dataset validation passed!")
    return config

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train YOLOv8 model")
    parser.add_argument("--data", type=str, required=True, help="Path to data.yaml")
    parser.add_argument("--epochs", type=int, default=100, help="Number of epochs")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--img-size", type=int, default=640, help="Image size")
    parser.add_argument("--model-size", type=str, default="n", choices=['n', 's', 'm', 'l', 'x'])
    parser.add_argument("--output", type=str, default="./outputs", help="Output directory")
    parser.add_argument("--test", action="store_true", help="Test mode (1 epoch)")
    
    args = parser.parse_args()
    
    # Test mode for quick validation
    if args.test:
        args.epochs = 1
        args.batch = 4
        print("Running in TEST mode (1 epoch)")
    
    # Validate dataset
    config = validate_dataset(args.data)
    print(f"Training on {config['nc']} classes: {config['names']}")
    
    # Train model
    model_path = train_yolo_model(
        data_path=args.data,
        epochs=args.epochs,
        batch_size=args.batch,
        img_size=args.img_size,
        model_size=args.model_size,
        output_dir=args.output
    )
    
    print(f"✅ Training complete! Model: {model_path}")
