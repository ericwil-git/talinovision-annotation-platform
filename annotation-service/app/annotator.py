import cv2
import numpy as np
from typing import List, Dict, Tuple
import json
import os

class VideoAnnotator:
    """OpenCV-based video annotation tool"""
    
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        self.annotations = []
        self.current_frame = 0
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.drawing = False
        self.start_point = None
        self.current_box = None
        
    def extract_frames(self, output_dir: str, sample_rate: int = 30):
        """Extract frames from video for annotation"""
        os.makedirs(output_dir, exist_ok=True)
        frame_count = 0
        saved_count = 0
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
                
            if frame_count % sample_rate == 0:
                frame_path = os.path.join(output_dir, f"frame_{saved_count:06d}.jpg")
                cv2.imwrite(frame_path, frame)
                saved_count += 1
                
            frame_count += 1
        
        self.cap.release()
        return saved_count
    
    def annotate_frame(self, frame: np.ndarray, boxes: List[Dict]) -> np.ndarray:
        """Draw annotation boxes on frame"""
        annotated = frame.copy()
        
        for box in boxes:
            x1, y1, x2, y2 = box['bbox']
            label = box['label']
            color = box.get('color', (0, 255, 0))
            
            # Draw rectangle
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(annotated, 
                         (x1, y1 - label_size[1] - 10),
                         (x1 + label_size[0], y1),
                         color, -1)
            cv2.putText(annotated, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        return annotated
    
    def export_coco_format(self, output_path: str, image_dir: str):
        """Export annotations in COCO format"""
        coco_data = {
            "images": [],
            "annotations": [],
            "categories": []
        }
        
        # Get unique categories
        categories = set()
        for ann in self.annotations:
            categories.add(ann['label'])
        
        category_map = {cat: idx for idx, cat in enumerate(sorted(categories), 1)}
        coco_data['categories'] = [
            {"id": idx, "name": cat, "supercategory": "object"}
            for cat, idx in category_map.items()
        ]
        
        # Process annotations
        for img_id, ann_group in enumerate(self.annotations, 1):
            image_info = {
                "id": img_id,
                "file_name": ann_group['image_name'],
                "width": ann_group['width'],
                "height": ann_group['height']
            }
            coco_data['images'].append(image_info)
            
            for ann_id, box in enumerate(ann_group['boxes'], 1):
                x1, y1, x2, y2 = box['bbox']
                width = x2 - x1
                height = y2 - y1
                
                annotation = {
                    "id": len(coco_data['annotations']) + 1,
                    "image_id": img_id,
                    "category_id": category_map[box['label']],
                    "bbox": [x1, y1, width, height],
                    "area": width * height,
                    "iscrowd": 0
                }
                coco_data['annotations'].append(annotation)
        
        with open(output_path, 'w') as f:
            json.dump(coco_data, f, indent=2)
        
        return output_path
    
    def export_yolo_format(self, output_dir: str, image_dir: str):
        """Export annotations in YOLO format"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Get unique categories
        categories = set()
        for ann in self.annotations:
            for box in ann['boxes']:
                categories.add(box['label'])
        
        category_map = {cat: idx for idx, cat in enumerate(sorted(categories))}
        
        # Write classes file
        with open(os.path.join(output_dir, 'classes.txt'), 'w') as f:
            for cat in sorted(categories):
                f.write(f"{cat}\n")
        
        # Write annotation files
        for ann_group in self.annotations:
            image_name = ann_group['image_name']
            width = ann_group['width']
            height = ann_group['height']
            
            txt_name = os.path.splitext(image_name)[0] + '.txt'
            txt_path = os.path.join(output_dir, txt_name)
            
            with open(txt_path, 'w') as f:
                for box in ann_group['boxes']:
                    x1, y1, x2, y2 = box['bbox']
                    
                    # Convert to YOLO format (normalized center x, y, width, height)
                    x_center = ((x1 + x2) / 2) / width
                    y_center = ((y1 + y2) / 2) / height
                    box_width = (x2 - x1) / width
                    box_height = (y2 - y1) / height
                    
                    class_id = category_map[box['label']]
                    f.write(f"{class_id} {x_center} {y_center} {box_width} {box_height}\n")
        
        return output_dir
    
    def save_annotations(self, output_path: str):
        """Save annotations to JSON file"""
        with open(output_path, 'w') as f:
            json.dump(self.annotations, f, indent=2)
        return output_path
    
    def load_annotations(self, input_path: str):
        """Load annotations from JSON file"""
        with open(input_path, 'r') as f:
            self.annotations = json.load(f)
        return len(self.annotations)

def create_annotation_dataset(video_path: str, output_base_dir: str, sample_rate: int = 30):
    """
    Complete pipeline to create annotation dataset from video
    
    Args:
        video_path: Path to input video
        output_base_dir: Base directory for output
        sample_rate: Extract every Nth frame
    
    Returns:
        Dictionary with paths to created resources
    """
    annotator = VideoAnnotator(video_path)
    
    # Create output directories
    frames_dir = os.path.join(output_base_dir, 'frames')
    annotations_dir = os.path.join(output_base_dir, 'annotations')
    os.makedirs(annotations_dir, exist_ok=True)
    
    # Extract frames
    print(f"Extracting frames (1 every {sample_rate} frames)...")
    num_frames = annotator.extract_frames(frames_dir, sample_rate)
    print(f"Extracted {num_frames} frames")
    
    return {
        'frames_dir': frames_dir,
        'annotations_dir': annotations_dir,
        'num_frames': num_frames,
        'video_info': {
            'total_frames': annotator.total_frames,
            'fps': annotator.fps
        }
    }
