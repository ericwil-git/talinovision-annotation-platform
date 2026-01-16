# Azure Video Annotation Platform - Alpha v0.1

A professional, scalable video annotation solution for training custom computer vision models using Azure services and OpenCV.

> **Status**: Alpha Release v0.1 - Core annotation features complete and functional

[![Azure](https://img.shields.io/badge/Azure-0078D4?logo=microsoft-azure&logoColor=white)](https://portal.azure.com)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.9-green.svg)](https://opencv.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🏗️ Architecture

```
Frontend (Azure Storage Static Website) → Annotation API (Container Apps) → Azure Blob Storage
                                                                ↓
                                                      Azure ML Workspace → Trained Models
```

### Components

- **Frontend**: React + Vite app hosted on Azure Storage Static Website
- **Backend API**: Flask REST API running on Azure Container Apps
- **Storage**: Azure Blob Storage for video files and annotations
- **ML Training**: Azure ML Workspace with compute cluster
- **Container Registry**: Azure Container Registry for Docker images
- **Monitoring**: Application Insights + Log Analytics

## 🌐 Live Endpoints

### Current Deployment (Dev Environment)

- **Frontend**: https://vidanndevr5uc5ka6jxm4i.z20.web.core.windows.net/
- **API**: https://annotation-service.bluemushroom-befb422f.eastus2.azurecontainerapps.io/
- **API Health Check**: https://annotation-service.bluemushroom-befb422f.eastus2.azurecontainerapps.io/health
- **Resource Group**: `rg-vidann-dev` (East US 2)
- **Storage Account**: `vidanndevr5uc5ka6jxm4i`

### Testing the Platform

1. **Upload a video**:

   - Visit the frontend URL
   - Enter a project name
   - Select a video file (up to 1GB)
   - Click "Upload Video"

2. **Check API health**:

   ```bash
   curl https://annotation-service.bluemushroom-befb422f.eastus2.azurecontainerapps.io/health
   ```

3. **List uploaded videos**:
   ```bash
   curl https://annotation-service.bluemushroom-befb422f.eastus2.azurecontainerapps.io/api/videos
   ```

## 🚀 Features (Alpha v0.1)

### ✅ Production-Ready Features

- **Video Upload Portal**: Web interface for video submission with drag-and-drop (up to 1GB)
- **Direct Blob Upload**: Client-side upload to Azure Storage using SAS tokens
- **Full Annotation Interface**: Canvas-based bounding box drawing with real-time preview
- **Frame Management**:
  - On-demand frame extraction with OpenCV
  - 1280x720 cached frames for instant loading
  - Predictive pre-fetching (10 frames ahead for sequential, 5 for jumps)
- **Navigation Controls**:
  - Frame slider with direct seeking
  - Arrow keys for previous/next frame
  - Jump-to-frame with validation
  - Keyboard shortcuts for all actions
- **Class Management**: Project-level class definitions shared across videos
- **Annotation Storage**: JSON format with automatic saving
- **YOLO Export**: One-click export to YOLO training format
- **Project Organization**: Multi-project support with video grouping
- **Toast Notifications**: Visual feedback for save operations
- **Managed Identity Security**: Azure AD authentication, no shared keys
- **CORS Configured**: Full cross-origin support for video playback
- **Dev Containers**: Fully portable development environment

### 🔄 In Development

- Azure ML training pipeline integration
- Batch inference endpoints
- Model versioning and deployment

### 📋 Planned for Beta

- User authentication and access control
- Multi-user collaboration
- Annotation review workflow
- Video segmentation tools
- Advanced class hierarchy

## 📋 Prerequisites

- Docker Desktop
- VS Code with Remote-Containers extension
- Azure subscription
- Azure CLI installed locally

## 🛠️ Getting Started

### 1. Open in Dev Container

```bash
# Open this folder in VS Code
code .

# VS Code will prompt to "Reopen in Container" - click it
# Or use Command Palette: "Remote-Containers: Reopen in Container"
```

### 2. Configure Azure

```bash
# Login to Azure
az login

# Set your subscription
az account set --subscription "your-subscription-id"
```

### 3. Deploy Infrastructure

```bash
# Initialize Azure Developer CLI (first time only)
azd auth login
azd init

# When prompted:
# - Environment name: dev
# - Resource group: Create new (e.g., rg-vidann-dev)
# - Location: eastus2 (required for Static Web Apps)

# Provision and deploy
azd up
```

**Note**: The initial deployment will:

1. Provision all Azure resources (Storage, Container Apps, ML Workspace, etc.)
2. Deploy the backend Container App
3. Frontend must be deployed separately to Azure Storage (see below)

### 4. Deploy Frontend (Manual Step)

After `azd up` completes, deploy the frontend:

```bash
cd frontend-upload
npm install
npm run build

# Upload to Azure Storage Static Website
az storage blob upload-batch \
  --account-name <your-storage-account-name> \
  --destination '$web' \
  --source ./dist \
  --auth-mode login \
  --overwrite
```

### 5. Run Locally for Development

```bash
# Terminal 1: Upload Portal
cd frontend-upload
npm install
npm run dev
# Access at http://localhost:5173

# Terminal 2: Annotation Service
cd annotation-service
python -m pip install -r requirements.txt
export AZURE_STORAGE_ACCOUNT_NAME=<your-account-name>
export AZURE_STORAGE_ACCOUNT_KEY=<your-account-key>
python app/main.py
# Access at http://localhost:5000

# Terminal 3: Test ML Pipeline
cd ml-pipeline
python training/train.py --test
```

## 📁 Project Structure

```
video-annotation-platform/
├── .devcontainer/           # Dev container configuration
├── frontend-upload/         # Upload portal (React + Vite)
│   ├── src/
│   │   ├── components/     # VideoUpload component
│   │   ├── App.jsx        # Main application
│   │   └── main.jsx       # Entry point
│   ├── dist/              # Built files (for deployment)
│   └── package.json
├── annotation-service/      # OpenCV annotation tool (Flask)
│   ├── app/
│   │   ├── main.py        # API routes
│   │   ├── annotator.py   # Video processing logic
│   │   └── static/        # HTML interface
│   ├── Dockerfile
│   └── requirements.txt
├── ml-pipeline/            # Azure ML training scripts
│   ├── training/
│   │   └── train_yolo.py
│   └── deployment/
│       └── deploy_batch.py
├── infrastructure/         # Bicep IaC files
│   ├── main.bicep         # Main infrastructure
│   ├── parameters.dev.json # Dev environment params
│   └── modules/           # Modular components
├── azure.yaml             # Azure Developer CLI config
├── docker-compose.dev.yml # Local development
└── README.md
```

## 🔐 Environment Variables

The following environment variables are automatically configured in Azure:

### Container App (Annotation API)

```env
AZURE_STORAGE_CONNECTION_STRING=<auto-configured>
AZURE_STORAGE_ACCOUNT_NAME=<auto-configured>
AZURE_STORAGE_ACCOUNT_KEY=<auto-configured>
```

### Frontend Build-time

```env
VITE_API_URL=https://annotation-service.bluemushroom-befb422f.eastus2.azurecontainerapps.io
```

### Local Development

Create a `.env` file in the project root:

```env
# Azure Configuration
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_RESOURCE_GROUP=rg-vidann-dev
AZURE_LOCATION=eastus2

# Storage
AZURE_STORAGE_ACCOUNT_NAME=vidanndevr5uc5ka6jxm4i
AZURE_STORAGE_ACCOUNT_KEY=your-storage-key
AZURE_STORAGE_CONNECTION_STRING=your-connection-string

# Azure ML
AZURE_ML_WORKSPACE_NAME=mlw-vidann-dev
AZURE_ML_RESOURCE_GROUP=rg-vidann-dev
```

## 📊 Workflow

1. **Upload**: Client visits frontend and uploads video (up to 1GB) via drag-and-drop
2. **SAS Token**: Frontend requests SAS token from API for direct blob upload
3. **Store**: Video uploaded directly from browser to Azure Blob Storage
4. **Notification**: Frontend notifies API of successful upload
5. **Annotate**: Internal team annotates using OpenCV tool (future enhancement)
6. **Train**: Azure ML pipeline trains custom YOLO model (future enhancement)
7. **Deploy**: Model available via batch endpoint or download (future enhancement)

## 🎯 API Endpoints (Alpha v0.1)

### System Endpoints

**Health Check**

```bash
GET /health
```

### Video Management

**List Projects**

```bash
GET /api/projects
# Returns: { "projects": [{ "name": "project1", "videos": [...] }] }
```

**Get Upload URL**

```bash
POST /api/get-upload-url
Content-Type: application/json
{ "projectName": "project1", "fileName": "video.mp4", "contentType": "video/mp4" }
```

**Get Video Info**

```bash
GET /api/videos/<path:blob_name>/info
# Returns: { "frameCount": 4398, "fps": 29.97, "width": 1080, "height": 1920, "duration": 146.73 }
```

**Get Video Playback URL**

```bash
GET /api/videos/<path:blob_name>
# Returns: { "videoUrl": "https://...?sas_token" }
```

### Frame Extraction

**Get Specific Frame**

```bash
GET /api/videos/<path:blob_name>/frame/<frame_number>
# Returns: image/jpeg (1280x720)
```

**Prefetch Frames** (Background operation)

```bash
POST /api/videos/<path:blob_name>/prefetch
Content-Type: application/json
{ "currentFrame": 100, "totalFrames": 4398, "nextFrames": 10 }
```

### Annotation Management

**Get Annotations**

```bash
GET /api/annotations/<path:blob_name>
# Returns: { "frames": {...}, "classes": [...], "video_width": 1080, "video_height": 1920 }
```

**Save Annotations**

```bash
POST /api/annotations/<path:blob_name>
Content-Type: application/json
{
  "video_width": 1080,
  "video_height": 1920,
  "classes": ["person", "car"],
  "frames": {
    "0": { "objects": [{ "class_id": 0, "class_name": "person", "bbox": {...} }] }
  }
}
```

**Export YOLO Format**

```bash
GET /api/annotations/<path:blob_name>/export
# Downloads: annotations.txt (YOLO format)
```

### Class Management

**Get Project Classes**

```bash
GET /api/projects/<project_name>/classes
# Returns: { "classes": ["person", "car", "dog"] }
```

**Update Project Classes**

```bash
POST /api/projects/<project_name>/classes
Content-Type: application/json
{ "classes": ["person", "car", "dog"] }
```

### Frame Cache Management

**Get Frame Stats**

```bash
GET /api/frames/stat - Alpha v0.1

**Release Date**: January 16, 2026
**Status**: Alpha Release - Core Features Complete

### ✅ Alpha v0.1 Features (Complete)

**Infrastructure & Deployment**
- ✅ Azure infrastructure provisioning with Bicep
- ✅ Container Apps deployment
- ✅ Storage account with managed identity
- ✅ CORS configuration for video playback
- ✅ Network security policies
- ✅ Dev container environment

**Video Upload & Management**
- ✅ Frontend upload portal with drag-and-drop
- ✅ Direct blob upload up to 1GB
- ✅ Project-based organization
- ✅ Video listing and browsing
- ✅ Video player with SAS token playback

**Annotation System**
- ✅ Full canvas-based annotation interface
- ✅ Bounding box drawing and editing
- ✅ Frame-by-frame navigation
- ✅ Frame slider with direct seeking
- ✅ Jump-to-frame functionality
- ✅ Keyboard shortcuts (arrows, Ctrl+S, Enter)
- ✅ Class management UI
- ✅ Project-level class persistence
- ✅ Toast notifications for feedback

**Frame Processing**
- ✅ OpenCV frame extraction (1280x720)
- ✅ Persistent frame caching in blob storage
- ✅ Lazy frame extraction (on-demand)
- ✅ Predictive pre-fetching (adaptive)
- ✅ Frame statistics and cleanup endpoints

**Data Management**
- ✅ JSON annotation storage
- ✅ Annotation load/save endpoints
- ✅ YOLO format export
- ✅ Project class synchronization
- ✅ Annotation persistence

### 🔄 Beta Roadmap

**ML Pipeline Integration**
- Azure ML workspace configuration
- Automated YOLO training pipeline
- Model versioning and tracking
- Batch inference endpoints

**Enhanced Features**
- User authentication (Azure AD)
- Multi-user collaboration
- Annotation review workflow
- Audit logging
- Advanced video segmentation

**Performance & Scale**
- Distributed frame extraction
- CDN integration for frames
- Background job processing
- Batch annotation operations

### 📊 Known Limitations (Alpha)

- Single-user annotation (no collaboration yet)
- No undo/redo in annotation UI
- Frame cache cleanup is manual
- No annotation version history
- Limited video format support (MP4 primary)
- Maximum 1GB video file size

- With auto-scaling and production SKUs: ~$100-300/month

## 🔧 Troubleshooting

### Frontend shows 405 error

- Ensure the API URL in the frontend is correct
- Check CORS configuration on the backend

### Upload fails with "user_delegation_key or account_key must be provided"

- Verify `AZURE_STORAGE_ACCOUNT_KEY` is set in Container App environment variables
- Re-provision with `azd provision --no-prompt`

### Static Web App deployment stuck

- Use Azure Storage Static Website hosting instead
- Deploy manually using `az storage blob upload-batch`

### Container App not receiving traffic

- Ensure ingress is configured as `external: true`
- Check that the `azd-service-name` tag is set on resources

## 🔒 Security

- SAS tokens for time-limited upload access (1-hour expiry)
- CORS configured for cross-origin requests
- HTTPS enforced on all endpoints
- Container App managed identity for Azure resource access
- Storage account keys stored as Container App secrets
- Network security with Azure Container Apps Environment

## 📚 Documentation

- **[Complete Wiki](./docs/WIKI.md)** - Comprehensive guide with tutorials, API reference, and troubleshooting
- **[Development Guide](./docs/development.md)** - Local development setup and contribution guidelines
- **[Storage Configuration](./docs/storage-network-config.md)** - Network and security configuration details
- **[API Reference](./docs/WIKI.md#api-reference)** - Complete API documentation with examples

### Quick Links

- [Azure Portal - Resource Group](https://portal.azure.com/#@/resource/subscriptions/a80ade45-139e-4ad0-855f-374b089cdbd9/resourceGroups/rg-vidann-dev/overview)
- [Container Apps Logs](https://portal.azure.com) → Container Apps → annotation-service → Log stream
- [Application Insights](https://portal.azure.com) → Application Insights → appi-vidann-dev

## 🚦 Project Status

**Current Phase**: Development & Testing

✅ Completed:

- Infrastructure provisioning with Bicep
- Frontend upload portal with drag-and-drop
- Backend API with SAS token generation
- Direct blob upload (up to 1GB)
- Azure deployment pipeline
- Dev container setup

🔄 In Progress:

- ML training pipeline integration
- Video annotation interface

📋 Planned:

- Automated model training
- Batch inference endpoint
- User authentication
- Advanced video processing

## 🤝 Contributing

This is a template project. Feel free to customize for your specific needs.

### Development Workflow

1. Make changes in dev container
2. Test locally
3. Build and test frontend: `npm run build`
4. Deploy to Azure: `azd deploy`
5. Update frontend: Manual upload to storage

## 📄 License

MIT License - See LICENSE file for details

---

**Version**: Alpha v0.1
**Release Date**: January 16, 2026
**Last Updated**: January 16, 2026
**Deployment**: rg-vidann-dev (East US 2)

**Documentation**: [Complete Wiki](./docs/WIKI.md) | [API Reference](./docs/WIKI.md#api-reference)

For questions, issues, or contributions, please refer to the [Wiki](./docs/WIKI.md) or create an issue in the repository.
```
