# Video Annotation Platform - Complete Wiki

**Version**: Alpha v0.1  
**Last Updated**: January 16, 2026  
**Status**: Production-Ready for Annotation Workflows

---

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [User Guide](#user-guide)
4. [Architecture](#architecture)
5. [API Reference](#api-reference)
6. [Development Guide](#development-guide)
7. [Deployment](#deployment)
8. [Troubleshooting](#troubleshooting)
9. [FAQ](#faq)

---

## Overview

### What is the Video Annotation Platform?

The Azure Video Annotation Platform is a cloud-native solution for creating labeled training data for computer vision models. It enables teams to:

- Upload videos to Azure Blob Storage
- Annotate frames with bounding boxes
- Organize projects and classes
- Export annotations in YOLO format
- Train custom object detection models

### Key Features (Alpha v0.1)

- **Fast Frame Navigation**: Cached frames load instantly after first access
- **Predictive Loading**: Smart pre-fetching for smooth navigation
- **Project Organization**: Multi-project support with shared classes
- **YOLO Export**: One-click export for model training
- **Scalable Storage**: Azure Blob Storage with managed identity
- **Responsive UI**: Canvas-based annotation with keyboard shortcuts

### Technology Stack

- **Frontend**: HTML5, JavaScript, Canvas API
- **Backend**: Python 3.11, Flask, OpenCV 4.9
- **Storage**: Azure Blob Storage
- **Compute**: Azure Container Apps
- **Infrastructure**: Bicep (Infrastructure as Code)
- **Development**: Dev Containers (VS Code)

---

## Getting Started

### Prerequisites

1. **Azure Subscription** with permissions to create resources
2. **Docker Desktop** for dev container
3. **VS Code** with Remote-Containers extension
4. **Azure CLI** for deployment

### Quick Start (5 minutes)

```bash
# 1. Clone repository and open in VS Code
code .

# 2. Reopen in dev container (when prompted)

# 3. Login to Azure
azd auth login

# 4. Deploy infrastructure and application
azd up

# 5. Access your platform
# Frontend: https://<storage-account>.z20.web.core.windows.net/
# Backend: https://annotation-service.<random>.eastus2.azurecontainerapps.io/
```

### First Project

1. Visit the frontend URL
2. Enter a project name (e.g., "traffic-monitoring")
3. Upload a video (MP4, up to 1GB)
4. Click "Annotate" on the uploaded video
5. Define classes (e.g., "car", "person", "bicycle")
6. Draw bounding boxes on frames
7. Press Ctrl+S to save
8. Export annotations for training

---

## User Guide

### Uploading Videos

**Step 1: Access Upload Portal**

- Navigate to your frontend URL
- You'll see the upload interface

**Step 2: Create/Select Project**

- Enter a project name (letters, numbers, hyphens only)
- Projects organize related videos

**Step 3: Upload Video**

- Drag and drop or click "Select Video"
- Supported formats: MP4 (primary), AVI, MOV
- Maximum size: 1GB
- Upload directly to Azure Blob Storage

**Step 4: Monitor Progress**

- Progress bar shows upload status
- Upload typically takes 30 seconds per 100MB

### Annotating Videos

**Opening Annotation Interface**

1. Go to project listing page
2. Find your video
3. Click "Annotate" button

**Interface Layout**

- **Top Bar**: Video name, save/export buttons, back button
- **Main Canvas**: Video frame with annotations
- **Left Panel**: Frame navigation, class selection
- **Bottom**: Frame slider, frame counter

**Drawing Annotations**

1. Select a class from the dropdown
2. Click and drag on the canvas to draw a bounding box
3. Box appears in the selected class color
4. Repeat for all objects in the frame

**Navigation**

- **Frame Slider**: Drag to any frame
- **Arrow Keys**:
  - `←` Previous frame
  - `→` Next frame
- **Jump to Frame**: Enter frame number, press Enter
- **Mouse Wheel**: Scroll through frames

**Keyboard Shortcuts**

- `←/→`: Navigate frames
- `Ctrl+S`: Save annotations
- `Enter`: Jump to typed frame number
- `Del`: Delete selected annotation
- `1-9`: Quick class selection (if defined)

**Managing Classes**

- Add new class: Type name and click "Add"
- Classes are shared across all videos in the project
- Each class gets a unique color

**Saving Work**

- Press `Ctrl+S` or click "Save Annotations"
- Toast notification confirms save
- Annotations saved to Azure Blob Storage
- Auto-save every 5 minutes (future feature)

**Exporting for Training**

- Click "Export YOLO" button
- Downloads `annotations.txt` in YOLO format
- Format: `class_id x_center y_center width height` (normalized)
- Ready for YOLOv8/v5 training

### Video Playback

**Accessing Video Player**

1. Go to project listing
2. Click "View" button on a video
3. Player opens in new view

**Player Controls**

- Standard HTML5 video controls
- Keyboard shortcuts:
  - `Space`: Play/Pause
  - `F`: Fullscreen toggle
  - `M`: Mute/Unmute
  - `←/→`: Skip 5 seconds
  - `↑/↓`: Volume adjustment

---

## Architecture

### System Architecture

```
┌─────────────────┐
│  Static Website │  Upload Portal (HTML/JS)
│  (Azure Storage)│
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────────────────────┐
│   Annotation API                │  Flask + OpenCV
│   (Azure Container Apps)        │  Python 3.11
├─────────────────────────────────┤
│ • Video Info Extraction         │
│ • Frame Extraction (1280x720)   │
│ • Annotation Storage            │
│ • YOLO Export                   │
│ • SAS Token Generation          │
└────────┬───────────────────┬────┘
         │                   │
         ▼                   ▼
┌─────────────────┐  ┌──────────────────┐
│  Blob Storage   │  │  Frame Cache     │
│  (Videos)       │  │  (Blob Storage)  │
└─────────────────┘  └──────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Azure ML Workspace (Future)    │
│  • Training Pipeline            │
│  • Model Registry               │
│  • Batch Endpoints              │
└─────────────────────────────────┘
```

### Data Flow

**Upload Flow**

1. User selects video in frontend
2. Frontend requests SAS token from API
3. API generates user delegation key SAS token (1-hour expiry)
4. Frontend uploads directly to blob storage
5. Frontend notifies API of completion
6. Video appears in project listing

**Annotation Flow**

1. User opens annotation interface
2. Frontend loads video info (frame count, dimensions, FPS)
3. User navigates to frame N
4. API checks frame cache in blob storage
5. If cached: Returns frame immediately
6. If not: Extracts frame with OpenCV, saves to cache, returns frame
7. Predictive pre-fetch runs in background (next 10 frames)
8. User draws annotations
9. Press Ctrl+S to save annotations as JSON
10. Annotations stored in "annotations" container

**Export Flow**

1. User clicks "Export YOLO"
2. API retrieves annotations JSON
3. Converts to YOLO format:
   - Normalized coordinates (0-1)
   - Format: `class_id x_center y_center width height`
   - One line per object
4. Returns as downloadable text file

### Storage Structure

```
Blob Storage Containers:

videos/
├── raw-videos/
│   ├── project1/
│   │   ├── video1.mp4
│   │   └── video2.mp4
│   └── project2/
│       └── video3.mp4

frames/  (Persistent Frame Cache)
├── raw-videos/
│   └── project1/
│       └── video1.mp4/
│           ├── frame_000000.jpg  (1280x720)
│           ├── frame_000001.jpg
│           └── frame_000100.jpg

annotations/
├── raw-videos/
│   └── project1/
│       └── video1.mp4.json
└── projects/
    ├── project1/
    │   └── classes.json
    └── project2/
        └── classes.json

models/ (Future)
└── project1/
    └── yolov8-v1.pt
```

### Frame Caching Strategy

**Lazy Extraction**

- Frames extracted only when first viewed
- Reduces upfront processing time
- Storage efficient: only store viewed frames

**Persistent Cache**

- Frames saved to blob storage after extraction
- Instant loading on subsequent views
- Shared across users/sessions

**Resolution Optimization**

- Original: 1920x1080 (~200KB/frame)
- Cached: 1280x720 (~35KB/frame)
- 65% storage savings
- Maintains annotation quality

**Predictive Pre-fetching**

- Sequential navigation: Pre-fetch 10 frames ahead
- Jump/scrub: Pre-fetch 5 frames ahead + 5 behind
- Non-blocking background operation
- Improves perceived performance

---

## API Reference

### Authentication

All API requests use managed identity authentication. No API keys required for deployment.

For development, set environment variables:

```bash
AZURE_STORAGE_ACCOUNT_NAME=<account-name>
```

### Base URL

```
Production: https://annotation-service.<your-random>.eastus2.azurecontainerapps.io
Development: http://localhost:5000
```

### Endpoints

#### System

**GET /health**

Check API health status.

Response:

```json
{
  "status": "healthy",
  "service": "annotation-api"
}
```

#### Projects

**GET /api/projects**

List all projects and their videos.

Response:

```json
{
  "projects": [
    {
      "name": "project1",
      "videos": [
        {
          "fileName": "video.mp4",
          "blobName": "raw-videos/project1/video.mp4",
          "size": 252306566,
          "lastModified": "2026-01-15T18:15:43+00:00"
        }
      ]
    }
  ]
}
```

**GET /api/projects/{project_name}/classes**

Get class definitions for a project.

Response:

```json
{
  "classes": ["person", "car", "dog"]
}
```

**POST /api/projects/{project_name}/classes**

Update project classes.

Request:

```json
{
  "classes": ["person", "car", "dog", "bicycle"]
}
```

#### Videos

**GET /api/videos/{blob_name}/info**

Get video metadata.

Response:

```json
{
  "frameCount": 4398,
  "fps": 29.974119662634777,
  "width": 1080,
  "height": 1920,
  "duration": 146.72657777777778
}
```

**GET /api/videos/{blob_name}**

Get SAS URL for video playback.

Response:

```json
{
  "videoUrl": "https://storage.blob.core.windows.net/videos/raw-videos/project1/video.mp4?sv=2023-11-03&se=..."
}
```

**GET /api/videos/{blob_name}/frame/{frame_number}**

Get specific frame as JPEG image.

Response: `image/jpeg` (1280x720)

**POST /api/videos/{blob_name}/prefetch**

Trigger background pre-fetching of frames.

Request:

```json
{
  "currentFrame": 100,
  "totalFrames": 4398,
  "nextFrames": 10
}
```

Response:

```json
{
  "status": "prefetching",
  "frames": [101, 102, ..., 110, 99, 98, ..., 95]
}
```

#### Annotations

**GET /api/annotations/{blob_name}**

Load annotations for a video.

Response:

```json
{
  "video_width": 1080,
  "video_height": 1920,
  "classes": ["person", "car"],
  "frames": {
    "0": {
      "objects": [
        {
          "class_id": 0,
          "class_name": "person",
          "bbox": {
            "x": 100,
            "y": 200,
            "width": 50,
            "height": 150
          }
        }
      ]
    }
  }
}
```

**POST /api/annotations/{blob_name}**

Save annotations for a video.

Request: Same format as GET response

Response:

```json
{
  "status": "success",
  "message": "Annotations saved"
}
```

**GET /api/annotations/{blob_name}/export**

Export annotations in YOLO format.

Response: Text file

```
0 0.5694444444444444 0.6510416666666667 0.046296296296296294 0.078125
1 0.2222222222222222 0.3958333333333333 0.09259259259259259 0.125
```

Format: `class_id x_center y_center width height` (normalized 0-1)

#### Frame Cache Management

**GET /api/frames/stats**

Get frame cache statistics.

Response:

```json
{
  "totalFrames": 1234,
  "totalSize": "43.2 MB",
  "videos": {
    "raw-videos/project1/video.mp4": {
      "frameCount": 450,
      "size": "15.8 MB"
    }
  }
}
```

**POST /api/frames/cleanup**

Delete old cached frames.

Request:

```json
{
  "daysOld": 30
}
```

Response:

```json
{
  "status": "success",
  "deletedCount": 150,
  "freedSpace": "5.2 MB"
}
```

---

## Development Guide

### Local Development Setup

**1. Start Dev Container**

```bash
# Open in VS Code
code .

# Reopen in container
# Command Palette: "Remote-Containers: Reopen in Container"
```

**2. Install Dependencies**

```bash
# Backend
cd annotation-service
pip install -r requirements.txt

# Frontend
cd frontend-upload
npm install
```

**3. Configure Environment**

```bash
# Set Azure credentials
export AZURE_STORAGE_ACCOUNT_NAME=vidanndevr5uc5ka6jxm4i
```

**4. Run Services**

```bash
# Terminal 1: Backend
cd annotation-service
python app/main.py
# Runs on http://localhost:5000

# Terminal 2: Frontend
cd frontend-upload
npm run dev
# Runs on http://localhost:5173
```

### Project Structure

```
video-annotation-platform/
├── annotation-service/          # Backend API
│   ├── app/
│   │   ├── main.py             # Flask routes and logic
│   │   └── static/
│   │       ├── index.html      # Project listing page
│   │       ├── annotate.html   # Main annotation interface
│   │       └── player.html     # Video player
│   ├── requirements.txt        # Python dependencies
│   └── Dockerfile
│
├── frontend-upload/            # Upload portal
│   ├── src/
│   │   ├── App.jsx            # Main app component
│   │   ├── components/
│   │   │   └── VideoUpload.jsx
│   │   └── main.jsx
│   ├── index.html
│   └── package.json
│
├── infrastructure/             # Bicep IaC
│   ├── main.bicep             # Main infrastructure
│   ├── parameters.dev.json
│   └── modules/
│       └── ml-compute.bicep
│
├── ml-pipeline/               # Training scripts (future)
│   ├── training/
│   │   └── train_yolo.py
│   └── deployment/
│       └── deploy_batch.py
│
├── docs/                      # Documentation
│   ├── WIKI.md               # This file
│   ├── development.md
│   └── storage-network-config.md
│
├── scripts/                   # Utility scripts
│   ├── deploy.sh
│   └── check-storage-policies.sh
│
├── azure.yaml                 # Azure Developer CLI config
└── README.md
```

### Adding New Features

**1. Backend Endpoint**

```python
# In annotation-service/app/main.py

@app.route('/api/your-endpoint', methods=['GET', 'POST'])
def your_endpoint():
    try:
        # Your logic here
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500
```

**2. Frontend Integration**

```javascript
// In annotation-service/app/static/annotate.html

async function callYourEndpoint() {
  try {
    const response = await fetch(`${API_BASE}/api/your-endpoint`);
    const data = await response.json();
    console.log(data);
  } catch (error) {
    console.error("Error:", error);
  }
}
```

**3. Deploy**

```bash
azd deploy annotation-api
```

### Testing

**Manual Testing**

```bash
# Test health endpoint
curl http://localhost:5000/health

# Test video info
curl http://localhost:5000/api/videos/raw-videos/project1/video.mp4/info

# Test frame extraction
curl http://localhost:5000/api/videos/raw-videos/project1/video.mp4/frame/0 \
  --output frame.jpg
```

**Load Testing** (Future)

```bash
# Install tools
pip install locust

# Run load test
locust -f tests/load_test.py
```

---

## Deployment

### Initial Deployment

```bash
# 1. Login to Azure
azd auth login

# 2. Initialize project
azd init

# 3. Provision + Deploy
azd up
```

### Update Deployment

**Backend Only**

```bash
azd deploy annotation-api
```

**Infrastructure Only**

```bash
azd provision
```

**Full Redeployment**

```bash
azd up
```

### Environment Variables

Automatically configured in Container Apps:

- `AZURE_STORAGE_ACCOUNT_NAME`: Storage account name
- `AZURE_STORAGE_CONNECTION_STRING`: Connection string
- `AZURE_STORAGE_ACCOUNT_KEY`: Access key (deprecated, use managed identity)

### Monitoring

**View Logs**

```bash
# Real-time logs
az containerapp logs show \
  --name annotation-service \
  --resource-group rg-vidann-dev \
  --type console \
  --follow

# Search logs
az containerapp logs show \
  --name annotation-service \
  --resource-group rg-vidann-dev \
  --type console \
  --tail 100 | grep ERROR
```

**Application Insights**

- Navigate to Azure Portal
- Find Application Insights resource
- View Live Metrics, Failures, Performance

### Scaling

**Manual Scaling**

```bash
az containerapp update \
  --name annotation-service \
  --resource-group rg-vidann-dev \
  --min-replicas 1 \
  --max-replicas 5
```

**Auto-scaling** (Add to Bicep)

```bicep
scale: {
  minReplicas: 1
  maxReplicas: 10
  rules: [
    {
      name: 'http-scaling'
      http: {
        metadata: {
          concurrentRequests: '10'
        }
      }
    }
  ]
}
```

---

## Troubleshooting

### Common Issues

**Problem: Frames not loading**

Symptoms: Loading spinner never completes

Solutions:

1. Check backend logs for errors
2. Verify storage account public access is enabled
3. Check CORS configuration on blob storage
4. Ensure managed identity has "Storage Blob Data Contributor" role

**Problem: Video player stuck on "loading video"**

Symptoms: Player shows loading message indefinitely

Solutions:

1. Verify CORS allows all origins (`*`)
2. Check SAS token is generated correctly
3. Ensure video URL is accessible from browser
4. Clear browser cache

**Problem: Annotations not saving**

Symptoms: Save button pressed but no confirmation

Solutions:

1. Check browser console for JavaScript errors
2. Verify POST endpoint is reachable
3. Check storage account permissions
4. Review backend logs for save errors

**Problem: Public network access disabled**

Symptoms: 403 AuthorizationFailure errors

Solutions:

```bash
# Enable public access
az storage account update \
  -n <storage-account-name> \
  -g rg-vidann-dev \
  --public-network-access Enabled

# Check policy compliance
./scripts/check-storage-policies.sh
```

**Problem: Deployment fails**

Symptoms: `azd up` or `azd deploy` errors

Solutions:

1. Check syntax of Bicep files
2. Verify Azure subscription has quota
3. Review deployment logs in Azure Portal
4. Try deploying infrastructure separately: `azd provision`

### Debug Mode

**Enable Backend Debug Logging**

```python
# In main.py
logging.basicConfig(level=logging.DEBUG)
```

**Frontend Debug Console**

```javascript
// In annotate.html
localStorage.debug = true;
```

**Check Container App Status**

```bash
az containerapp show \
  --name annotation-service \
  --resource-group rg-vidann-dev \
  --query "properties.runningStatus"
```

### Performance Issues

**Slow Frame Loading**

- Check if frames are being cached
- Verify storage account is in same region
- Consider CDN for frame delivery (future)
- Review network latency

**High Storage Costs**

- Run frame cleanup regularly
- Implement auto-cleanup policy
- Monitor frame cache size
- Consider frame compression

---

## FAQ

### General Questions

**Q: What video formats are supported?**

A: Primary support for MP4 (H.264). AVI and MOV also work but may have compatibility issues.

**Q: What's the maximum video file size?**

A: 1GB per video. For larger files, split the video or contact support for enterprise options.

**Q: How much does it cost to run?**

A: Development environment: ~$15-25/month. Production with scaling: ~$100-300/month depending on usage.

**Q: Can multiple users annotate simultaneously?**

A: Not in Alpha v0.1. Multi-user collaboration is planned for Beta release.

### Technical Questions

**Q: What annotation formats are supported for export?**

A: Currently YOLO format. COCO and Pascal VOC formats planned for Beta.

**Q: How are frames cached?**

A: Frames extracted on-demand, resized to 1280x720, saved as JPEG in blob storage, reused on subsequent views.

**Q: Can I train models directly in the platform?**

A: Not yet. Export YOLO annotations and train externally. Integrated training coming in Beta.

**Q: Is there an API rate limit?**

A: No explicit rate limiting in Alpha. Production deployments should implement rate limiting.

**Q: How do I backup annotations?**

A: Annotations stored in blob storage. Use Azure Backup or download via API.

### Troubleshooting Questions

**Q: Why are my projects not showing up?**

A: Check if public network access is enabled on storage account. Run `./scripts/check-storage-policies.sh` for diagnostics.

**Q: Can I use this on-premises?**

A: Platform designed for Azure. On-premises deployment requires modifications for storage and authentication.

**Q: How do I report bugs?**

A: Create an issue in the repository with logs and reproduction steps.

---

## Appendix

### Keyboard Shortcuts Reference

| Key      | Action                     |
| -------- | -------------------------- |
| `←`      | Previous frame             |
| `→`      | Next frame                 |
| `Ctrl+S` | Save annotations           |
| `Enter`  | Jump to frame              |
| `Del`    | Delete selected annotation |
| `Esc`    | Cancel drawing             |
| `Space`  | Play/Pause (player only)   |
| `F`      | Fullscreen (player only)   |

### Storage Containers

| Container     | Purpose                 | Contents                                            |
| ------------- | ----------------------- | --------------------------------------------------- |
| `videos`      | Raw uploaded videos     | `raw-videos/<project>/<video>.mp4`                  |
| `frames`      | Cached extracted frames | `raw-videos/<project>/<video>.mp4/frame_NNNNNN.jpg` |
| `annotations` | Saved annotations       | `raw-videos/<project>/<video>.mp4.json`             |
| `annotations` | Project classes         | `projects/<project>/classes.json`                   |
| `models`      | Trained models (future) | `<project>/<model-version>.pt`                      |

### Azure Resources

| Resource                   | Type           | Purpose                  |
| -------------------------- | -------------- | ------------------------ |
| Storage Account            | `Standard_LRS` | Video/annotation storage |
| Container App              | Basic          | Backend API              |
| Container Apps Environment |                | Hosting environment      |
| Container Registry         | Basic          | Docker images            |
| Application Insights       |                | Monitoring               |
| Log Analytics              |                | Log aggregation          |
| ML Workspace               | Basic          | Model training (future)  |

### Cost Optimization Tips

1. **Frame Cache Cleanup**: Run weekly cleanup to remove old frames
2. **Video Compression**: Compress videos before upload
3. **Storage Tier**: Move old videos to Cool/Archive tier
4. **Container Scaling**: Set appropriate min/max replicas
5. **Application Insights**: Configure sampling to reduce data ingestion

### Security Best Practices

1. **Network Access**: Use private endpoints for production
2. **Authentication**: Enable Azure AD authentication
3. **RBAC**: Use least-privilege role assignments
4. **SAS Tokens**: Use short expiry times (1 hour default)
5. **HTTPS**: Always use HTTPS endpoints
6. **Secrets**: Store in Azure Key Vault
7. **Managed Identity**: Disable shared key access

---

**Version**: Alpha v0.1  
**Release Date**: January 16, 2026  
**Documentation**: https://github.com/your-repo/video-annotation-platform

**Support**: Create an issue in the repository

**License**: MIT - See LICENSE file
