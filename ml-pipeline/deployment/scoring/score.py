"""
Scoring script for batch inference
"""

import os
import json
import numpy as np
from typing import List
from ultralytics import YOLO
import logging

def init():
    """Initialize model"""
    global model
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    model_path = os.path.join(os.getenv("AZUREML_MODEL_DIR"), "best.pt")
    logger.info(f"Loading model from: {model_path}")
    
    model = YOLO(model_path)
    logger.info("Model loaded successfully")

def run(mini_batch: List[str]):
    """Run inference on batch of images"""
    results = []
    
    for image_path in mini_batch:
        try:
            # Run inference
            detections = model(image_path, verbose=False)
            
            # Parse results
            for result in detections:
                boxes = result.boxes
                
                predictions = {
                    "image": os.path.basename(image_path),
                    "detections": []
                }
                
                for box in boxes:
                    detection = {
                        "class": int(box.cls[0]),
                        "class_name": result.names[int(box.cls[0])],
                        "confidence": float(box.conf[0]),
                        "bbox": box.xyxy[0].tolist()
                    }
                    predictions["detections"].append(detection)
                
                results.append(json.dumps(predictions))
        
        except Exception as e:
            logging.error(f"Error processing {image_path}: {str(e)}")
            results.append(json.dumps({"image": os.path.basename(image_path), "error": str(e)}))
    
    return results
