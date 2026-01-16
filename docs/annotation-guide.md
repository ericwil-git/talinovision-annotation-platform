# Video Annotation System Guide

## Overview

Full-featured video annotation platform deployed on Azure with OpenCV integration for frame extraction and YOLO format export for ML training.

## Architecture

### Backend (Flask + OpenCV)

- **Location**: `annotation-service/app/main.py`
- **Endpoints**:
  - `GET /api/videos/<path>/info` - Extract video metadata (fps, frames, dimensions)
  - `GET /api/videos/<path>/frame/<int>` - Extract specific frame as JPEG
  - `GET /api/annotations/<path>` - Load annotations JSON
  - `POST /api/annotations/<path>` - Save annotations
  - `GET /api/annotations/<path>/export` - Export in YOLO format

### Frontend (HTML + Canvas API)

- **Location**: `annotation-service/app/static/annotate.html`
- **Features**:
  - Canvas-based drawing for bounding boxes
  - Frame navigation with slider
  - Class management with color coding
  - Real-time annotation preview
  - Keyboard shortcuts (arrows for navigation, Ctrl+S to save)

### Storage

- **Videos**: Azure Blob Storage container `videos`
- **Annotations**: Azure Blob Storage container `annotations`
- **Format**: JSON with frame-by-frame bounding box data

## Usage

### 1. Access the Platform

Navigate to: https://annotation-service.bluemushroom-befb422f.eastus2.azurecontainerapps.io/

### 2. Select Video

- Browse available projects and videos
- Click "Annotate" button on any video

### 3. Annotate Frames

1. **Select Class**: Click on class in left sidebar (Person, Vehicle, Object, or add custom)
2. **Draw Bounding Box**: Click and drag on canvas to create rectangle
3. **Navigate Frames**: Use arrow buttons, slider, or keyboard arrows
4. **Review Annotations**: Check right panel for current frame annotations
5. **Save Progress**: Click "Save Annotations" or press Ctrl+S

### 4. Export for Training

Click "Export YOLO" to download annotations in YOLO format:

```
<class_id> <x_center> <y_center> <width> <height>
```

All coordinates normalized to 0-1 range.

## Annotation Format

### Storage JSON Structure

```json
{
  "video_width": 1920,
  "video_height": 1080,
  "classes": [
    { "id": 0, "name": "Person", "color": "#ff0000" },
    { "id": 1, "name": "Vehicle", "color": "#00ff00" }
  ],
  "frames": {
    "0": {
      "objects": [
        {
          "class_id": 0,
          "bbox": {
            "x": 100,
            "y": 150,
            "width": 80,
            "height": 200
          }
        }
      ]
    }
  }
}
```

### YOLO Export Format

Each frame becomes `frame_<number>.txt`:

```
0 0.52083 0.69444 0.04167 0.18519
1 0.31250 0.45370 0.06250 0.14815
```

## API Examples

### Get Video Info

```bash
curl https://annotation-service.bluemushroom-befb422f.eastus2.azurecontainerapps.io/api/videos/project1/test-video.mp4/info
```

Response:

```json
{
  "fps": 30.0,
  "frameCount": 450,
  "duration": 15.0,
  "width": 1920,
  "height": 1080
}
```

### Extract Frame

```bash
curl https://annotation-service.bluemushroom-befb422f.eastus2.azurecontainerapps.io/api/videos/project1/test-video.mp4/frame/100 --output frame100.jpg
```

### Save Annotations

```bash
curl -X POST \
  https://annotation-service.bluemushroom-befb422f.eastus2.azurecontainerapps.io/api/annotations/project1/test-video.mp4 \
  -H "Content-Type: application/json" \
  -d @annotations.json
```

### Export YOLO Format

```bash
curl https://annotation-service.bluemushroom-befb422f.eastus2.azurecontainerapps.io/api/annotations/project1/test-video.mp4/export --output annotations.zip
```

## Integration with ML Pipeline

The YOLO format export is ready for training:

1. **Download Annotations**: Click "Export YOLO" button
2. **Extract ZIP**: Contains `frame_<number>.txt` files
3. **Prepare Dataset**: Organize with corresponding frame images
4. **Train Model**: Use with YOLOv8/YOLOv9 training pipeline in `ml-pipeline/`

Example directory structure for training:

```
dataset/
  images/
    frame_0.jpg
    frame_1.jpg
  labels/
    frame_0.txt
    frame_1.txt
  data.yaml
```

## OpenCV Features

### Frame Extraction

- Downloads video to temporary file
- Uses `cv2.VideoCapture()` for precise frame access
- Converts to JPEG with quality=90
- Returns as binary stream

### Video Analysis

- Extracts FPS, frame count, duration
- Retrieves frame dimensions
- Validates video integrity

## Performance Considerations

- **Frame Caching**: Not implemented - each frame extracted on demand
- **Video Download**: Temporary file created per request (cleaned up automatically)
- **Large Videos**: Consider chunking or thumbnail generation for >1GB files
- **Concurrent Users**: Each user creates separate temp files

## Future Enhancements

1. **Frame Caching**: Store extracted frames in blob storage
2. **Video Thumbnails**: Generate timeline preview
3. **Polygon Annotations**: Support for segmentation masks
4. **Auto-tracking**: Track objects across frames
5. **Collaborative Editing**: Multi-user annotation sessions
6. **Quality Assurance**: Validation and review workflow

## Troubleshooting

### Frames Not Loading

- Check video exists in blob storage
- Verify managed identity has Storage Blob Data Contributor role
- Check container app logs: `az containerapp logs show`

### Annotations Not Saving

- Ensure 'annotations' container exists in storage account
- Verify CORS settings allow POST requests
- Check browser console for API errors

### YOLO Export Issues

- Confirm frames have annotations before exporting
- Verify normalized coordinates are in 0-1 range
- Check ZIP file contents after download

## Links

- **Platform URL**: https://annotation-service.bluemushroom-befb422f.eastus2.azurecontainerapps.io/
- **Azure Portal**: https://portal.azure.com/#@/resource/subscriptions/a80ade45-139e-4ad0-855f-374b089cdbd9/resourceGroups/rg-vidann-dev/overview
- **Storage Account**: vidanndevr5uc5ka6jxm4i
- **Container App**: annotation-service

## Dependencies

- **opencv-python**: 4.9.0.80
- **opencv-contrib-python**: 4.9.0.80
- **numpy**: 1.26.4
- **Flask**: 3.0.2
- **azure-storage-blob**: 12.23.1
- **azure-identity**: 1.19.0
