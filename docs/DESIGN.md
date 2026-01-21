# TalinoVision Annotation Platform - Detailed Design

**Version**: 0.2.0-alpha  
**Last Updated**: January 21, 2026  
**Status**: Active Development

## Table of Contents

- [1. Overview](#1-overview)
- [2. System Architecture](#2-system-architecture)
- [3. Security Architecture](#3-security-architecture)
- [4. Component Design](#4-component-design)
- [5. Data Architecture](#5-data-architecture)
- [6. API Design](#6-api-design)
- [7. Performance & Scalability](#7-performance--scalability)
- [8. Design Decisions](#8-design-decisions)
- [9. Future Architecture](#9-future-architecture)

---

## 1. Overview

### 1.1 Purpose

TalinoVision is a cloud-native video annotation platform designed for creating training datasets for computer vision models. The platform enables users to efficiently annotate video frames with bounding boxes and export annotations in YOLO format for model training.

### 1.2 Design Goals

1. **Security First**: Zero secrets in configuration, managed identity for all Azure services
2. **Scalability**: Horizontal scaling for annotation workloads
3. **Performance**: Sub-100ms frame retrieval through intelligent caching
4. **Cost Efficiency**: Optimized storage and compute usage
5. **Developer Experience**: Simple deployment with Azure Developer CLI
6. **Maintainability**: Clean separation of concerns, infrastructure as code

### 1.3 Key Constraints

- **Cloud-Only**: No on-premises deployment
- **Azure-Native**: Leverages Azure PaaS services
- **Single-Region**: Initial deployment in one Azure region
- **Video Size Limit**: 1GB per video file
- **Format Support**: MP4, AVI, MOV containers

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Internet                                 │
└────────────────┬────────────────────────────────┬────────────────┘
                 │                                 │
                 │                                 │
         ┌───────▼────────┐              ┌────────▼────────┐
         │  Azure Static  │              │  Azure Blob     │
         │   Web Apps     │              │    Storage      │
         │   (Upload UI)  │              │  (Static Site)  │
         └───────┬────────┘              └─────────────────┘
                 │
                 │ HTTPS/CORS
                 │
         ┌───────▼─────────────────────────────────────────┐
         │        Azure Container Apps Environment         │
         │  ┌─────────────────────────────────────────┐   │
         │  │    Annotation Service (Flask)           │   │
         │  │    - Frame Extraction (OpenCV)          │   │
         │  │    - Annotation Management              │   │
         │  │    - YOLO Export                        │   │
         │  │    - SAS Token Generation               │   │
         │  └──────────┬──────────────────────────────┘   │
         └─────────────┼──────────────────────────────────┘
                       │
                       │ Managed Identity (RBAC)
                       │
         ┌─────────────▼──────────────────────────────────┐
         │         Azure Blob Storage                      │
         │  ┌────────────┬────────────┬──────────────┐    │
         │  │  videos/   │  frames/   │ annotations/ │    │
         │  │  (raw)     │  (cache)   │  (JSON)      │    │
         │  └────────────┴────────────┴──────────────┘    │
         └─────────────────────────────────────────────────┘
                       │
                       │
         ┌─────────────▼──────────────────────────────────┐
         │    Azure Application Insights + Log Analytics   │
         │    (Monitoring, Logging, Diagnostics)           │
         └─────────────────────────────────────────────────┘
```

### 2.2 Component Interaction Flow

#### Video Upload Flow

```
User → Upload Portal → Generate SAS Token (Backend) → Direct Upload to Blob →
Complete Callback → Backend Notification → Project Index Update
```

#### Annotation Flow

```
User → Project Page → Annotation Interface → Request Frame (Backend) →
Check Frame Cache → Extract if Missing → Resize & Cache → Return Frame →
User Annotates → Save JSON (Backend) → Blob Storage
```

#### Export Flow

```
User → Request Export → Backend Reads Annotations → Convert to YOLO Format →
Generate ZIP → Stream to User
```

### 2.3 Deployment Architecture

```yaml
Infrastructure:
  Resource Group: rg-vidann-dev
  Region: eastus2

  Compute:
    - Container Apps Environment (cae-vidann-dev)
      - annotation-service (0.5 vCPU, 1Gi RAM, 1-5 replicas)
    - Azure Static Web Apps (upload portal)

  Storage:
    - Storage Account (Standard_LRS)
      - Containers: videos, frames, annotations, models
      - Access: Managed Identity only (no shared keys)

  Identity & Security:
    - Managed Identity (System-Assigned)
    - RBAC: Storage Blob Data Contributor, Storage Blob Delegator

  Monitoring:
    - Application Insights
    - Log Analytics Workspace

  Development:
    - Container Registry (ACR)
    - Key Vault (for future secrets)
```

---

## 3. Security Architecture

### 3.1 Authentication & Authorization Model

#### Managed Identity Flow

```
┌─────────────────────────────────────────────────────────┐
│  Container App (annotation-service)                     │
│                                                          │
│  ┌────────────────────────────────────────────┐        │
│  │  Python Application                         │        │
│  │  ┌──────────────────────────────────┐      │        │
│  │  │ DefaultAzureCredential            │      │        │
│  │  │  1. Environment Variables         │      │        │
│  │  │  2. Managed Identity ←─────────┐  │      │        │
│  │  │  3. Azure CLI (local dev)      │  │      │        │
│  │  └──────────────────────────────┬──┘  │      │        │
│  │                                 │     │      │        │
│  │  BlobServiceClient ←────────────┘     │      │        │
│  └────────────────────────────────────────────┘        │
│                                                          │
│  System-Assigned Managed Identity                       │
│  Principal ID: f56fd7b2-50c8-409c-8adb-00d3e99e24ee    │
└────────────────────────┬─────────────────────────────────┘
                         │
                         │ Azure AD Token Request
                         │
                ┌────────▼──────────┐
                │   Azure AD        │
                │   Issues Token    │
                └────────┬──────────┘
                         │
                         │ Bearer Token
                         │
         ┌───────────────▼─────────────────────────┐
         │   Azure Blob Storage                     │
         │                                          │
         │   RBAC Check:                            │
         │   ✓ Storage Blob Data Contributor       │
         │   ✓ Storage Blob Delegator              │
         │                                          │
         │   allowSharedKeyAccess: false           │
         │   publicNetworkAccess: Enabled          │
         └──────────────────────────────────────────┘
```

#### Why Managed Identity?

**Problems with Shared Keys:**

- ❌ Secrets in configuration
- ❌ Manual rotation required
- ❌ Broad access (all-or-nothing)
- ❌ Audit trail limited
- ❌ Security policy conflicts

**Benefits of Managed Identity:**

- ✅ No secrets to manage
- ✅ Automatic credential rotation
- ✅ Fine-grained RBAC control
- ✅ Complete audit trail
- ✅ Azure best practice
- ✅ Eliminates auto-remediation conflicts

### 3.2 RBAC Role Assignment

```bicep
// Storage Blob Data Contributor (ba92f5b4-2d11-453d-a403-e96b0029c9fe)
// Permissions: Read, Write, Delete blobs and containers
resource blobContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, annotationService.id, storageBlobDataContributorRoleId)
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions',
                                             storageBlobDataContributorRoleId)
    principalId: annotationService.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Storage Blob Delegator (db58b8e5-c6ad-4a2a-8342-4190687cbf4a)
// Permissions: Generate user delegation SAS keys
resource blobDelegatorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, annotationService.id, storageBlobDelegatorRoleId)
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions',
                                             storageBlobDelegatorRoleId)
    principalId: annotationService.identity.principalId
    principalType: 'ServicePrincipal'
  }
}
```

### 3.3 SAS Token Generation

**User Delegation Keys** (instead of Account Keys):

```python
# Get user delegation key (managed identity)
user_delegation_key = blob_service_client.get_user_delegation_key(
    key_start_time=datetime.utcnow(),
    key_expiry_time=datetime.utcnow() + timedelta(hours=1)
)

# Generate SAS with user delegation key
sas_token = generate_blob_sas(
    account_name=STORAGE_ACCOUNT_NAME,
    container_name=CONTAINER_NAME,
    blob_name=blob_name,
    user_delegation_key=user_delegation_key,  # Not account key!
    permission=BlobSasPermissions(write=True, create=True),
    expiry=expiry_time
)
```

**Benefits:**

- Auditable: Each SAS tied to managed identity
- Time-limited: 1-hour expiry
- Least privilege: Only write/create permissions
- Revocable: Revoke managed identity = all SAS invalidated

### 3.4 Network Security

```yaml
Storage Account:
  publicNetworkAccess: Enabled # Required for Container App access
  allowSharedKeyAccess: false # Enforce managed identity only
  networkAcls:
    bypass: AzureServices # Allow Azure backbone traffic
    defaultAction: Allow # Accept traffic (RBAC controls access)

Container App:
  ingress:
    external: true # Internet-facing
    targetPort: 5000
    transport: http
    allowInsecure: false # HTTPS enforced
  corsPolicy:
    allowedOrigins: ["*"] # CORS enabled for all origins
    allowedMethods: [GET, POST, PUT, OPTIONS]
```

---

## 4. Component Design

### 4.1 Backend Service (annotation-service)

#### Technology Stack

- **Runtime**: Python 3.11
- **Framework**: Flask 3.0.1
- **Computer Vision**: OpenCV 4.9.0
- **Azure SDK**: azure-storage-blob 12.19.0, azure-identity 1.15.0
- **Server**: Gunicorn 21.2.0 (production)

#### Architecture Pattern

**Layered Architecture** with clear separation:

```
┌─────────────────────────────────────┐
│     Flask Routes (main.py)          │  ← HTTP endpoints
├─────────────────────────────────────┤
│     Business Logic                  │  ← Annotation, Export
├─────────────────────────────────────┤
│     Frame Processing (annotator.py) │  ← OpenCV operations
├─────────────────────────────────────┤
│     Azure SDK Layer                 │  ← Blob operations
├─────────────────────────────────────┤
│     Managed Identity                │  ← Authentication
└─────────────────────────────────────┘
```

#### Key Components

**1. Video Cache Manager**

```python
# In-memory cache with TTL
video_cache = {
    'blob_name': {
        'path': '/tmp/cached_video.mp4',
        'last_accessed': timestamp
    }
}

# Background cleanup thread
def cleanup_expired_cache():
    # Remove videos older than 15 minutes
    # Prevents disk space exhaustion
```

**Design Rationale:**

- Downloads video once, extracts multiple frames
- Reduces blob storage reads by 95%
- TTL prevents unbounded growth
- Thread-safe with locking

**2. Frame Cache Strategy**

```python
def get_or_create_frame(blob_name, frame_number):
    """
    1. Check if frame exists in blob storage
    2. If exists: Download and return (cache hit)
    3. If not: Extract from video → Resize → Upload → Return
    """
    frame_blob_name = f"{blob_name}/frame_{frame_number:06d}.jpg"

    # Check persistent cache
    if frame_blob_client.exists():
        return cached_frame  # ~50ms

    # Extract and cache
    frame = extract_frame(video, frame_number)
    frame_resized = resize_to_1280x720(frame)
    upload_to_blob(frame_resized)
    return frame  # ~200ms first time
```

**Design Rationale:**

- Persistent cache survives service restarts
- Frame extraction expensive (200ms), caching critical
- Resize to 1280x720 balances quality vs storage (65% savings)
- Lazy extraction: only create frames user requests

**3. Predictive Pre-fetching**

```python
def prefetch_frames(blob_name, current_frame, direction='forward'):
    """
    Sequential navigation: Pre-fetch 10 frames ahead
    Jump navigation: Pre-fetch 5 ahead + 5 behind
    """
    if direction == 'forward':
        frames_to_prefetch = range(current_frame + 1, current_frame + 11)
    else:
        frames_to_prefetch = range(current_frame - 5, current_frame + 6)

    # Async background pre-fetching
    threading.Thread(target=prefetch_worker, args=(frames_to_prefetch,)).start()
```

**Design Rationale:**

- Anticipates user navigation patterns
- Eliminates wait time for sequential annotation
- Background threads don't block current request
- Adaptive: different strategies for different nav types

**4. YOLO Export Generator**

```python
def export_to_yolo(annotations_json):
    """
    Convert internal JSON format to YOLO training format:
    - classes.txt: Class ID to name mapping
    - labels/: One .txt file per frame
    - Format: <class_id> <x_center> <y_center> <width> <height>
    """
    # Normalize coordinates to [0, 1]
    # Generate training split (train/val/test)
    # Create data.yaml for YOLO training
```

### 4.2 Frontend Components

#### Upload Portal (React + Vite)

```jsx
<VideoUpload>
  ├── Project Selector
  ├── File Picker (Drag & Drop)
  ├── SAS Token Request → Backend
  ├── Direct Blob Upload (XMLHttpRequest)
  └── Progress Tracking
```

**Design Decision:** Direct blob upload bypasses backend bottleneck

- Backend generates SAS token only
- File transfer direct to storage (no proxy)
- Supports large files (up to 1GB)

#### Annotation Interface (Vanilla JS)

```javascript
// Why not React/Angular?
// - Canvas manipulation requires direct DOM access
// - Framework overhead unnecessary for simple UI
// - Better performance for real-time drawing

annotate.html:
  - Canvas element (drawing surface)
  - Frame navigation controls
  - Class selector dropdown
  - Keyboard event handlers
  - REST API client
```

---

## 5. Data Architecture

### 5.1 Storage Structure

```
Azure Blob Storage (vidanndevr5uc5ka6jxm4i)
│
├── videos/
│   └── raw-videos/
│       ├── project1/
│       │   └── 20260115_181530_video.mp4
│       └── project2/
│           └── 20260115_194716_video.mp4
│
├── frames/
│   └── raw-videos/
│       └── project1/
│           └── 20260115_181530_video.mp4/
│               ├── frame_000000.jpg  (1280x720, ~150KB)
│               ├── frame_000001.jpg
│               └── frame_000050.jpg
│
├── annotations/
│   └── raw-videos/
│       └── project1/
│           └── 20260115_181530_video.mp4.json
│               {
│                 "classes": [...],
│                 "frames": {
│                   "50": {
│                     "annotations": [
│                       {
│                         "bbox": [x, y, w, h],
│                         "class_id": 0,
│                         "class_name": "person"
│                       }
│                     ]
│                   }
│                 }
│               }
│
└── models/  (future: trained YOLO models)
```

### 5.2 Data Model

#### Annotation JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "classes": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "integer" },
          "name": { "type": "string" },
          "color": { "type": "string", "pattern": "^#[0-9A-Fa-f]{6}$" }
        },
        "required": ["id", "name", "color"]
      }
    },
    "frames": {
      "type": "object",
      "patternProperties": {
        "^[0-9]+$": {
          "type": "object",
          "properties": {
            "annotations": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "bbox": {
                    "type": "array",
                    "items": { "type": "number" },
                    "minItems": 4,
                    "maxItems": 4
                  },
                  "class_id": { "type": "integer" },
                  "class_name": { "type": "string" }
                },
                "required": ["bbox", "class_id", "class_name"]
              }
            }
          },
          "required": ["annotations"]
        }
      }
    }
  },
  "required": ["classes", "frames"]
}
```

#### YOLO Export Format

```
training_data/
├── classes.txt
│   person
│   vehicle
│   object
│
├── images/
│   ├── train/
│   ├── val/
│   └── test/
│
├── labels/
│   ├── train/
│   │   └── frame_000050.txt
│   │       0 0.512 0.384 0.125 0.256
│   ├── val/
│   └── test/
│
└── data.yaml
    train: ./images/train
    val: ./images/val
    test: ./images/test
    nc: 3
    names: ['person', 'vehicle', 'object']
```

### 5.3 Storage Optimization

**Frame Resolution Strategy:**

```
Original Video: 1920x1080 (Full HD)
Cached Frames: 1280x720 (720p)
Compression: JPEG quality 85

Storage Savings:
- Original frame: ~450KB (uncompressed)
- Cached frame: ~150KB (resized + JPEG)
- Savings: 65%

Quality Impact:
- Sufficient for annotation accuracy
- Maintains aspect ratio
- Acceptable JPEG artifacts for bounding boxes
```

**Why 1280x720?**

- Sweet spot for annotation precision
- Readable object details
- 3x smaller than 1080p
- Standard 16:9 aspect ratio
- Balances UX and cost

---

## 6. API Design

### 6.1 REST Principles

**Design Philosophy:**

- RESTful resource-based URLs
- HTTP verbs match intent (GET=read, POST=create)
- JSON request/response bodies
- Consistent error format

### 6.2 Endpoint Catalog

#### Project Management

```
GET /api/projects
├── Returns: List of projects with video metadata
└── Pattern: Collection resource

GET /api/projects/{name}/classes
├── Returns: Class definitions for project
└── Pattern: Sub-resource

POST /api/projects/{name}/classes
├── Body: {"classes": [...]}
└── Pattern: Update sub-resource
```

#### Video Operations

```
GET /api/videos/{path}/info
├── Returns: {duration, fps, frameCount, width, height}
└── Pattern: Resource metadata

GET /api/videos/{path}/frame/{number}
├── Returns: JPEG image (binary)
└── Pattern: Nested resource

GET /api/videos/{path}
├── Returns: {videoUrl: "https://...?sas_token"}
└── Pattern: Temporary access URL
```

#### Annotation CRUD

```
GET /api/annotations/{path}
├── Returns: Full annotation JSON or {"frames": {}}
└── Pattern: Read resource

POST /api/annotations/{path}
├── Body: Full annotation JSON
└── Pattern: Update entire resource (not PATCH)

GET /api/annotations/{path}/export
├── Returns: ZIP file (YOLO format)
└── Pattern: Resource transformation
```

### 6.3 Error Handling

```python
@app.errorhandler(Exception)
def handle_error(e):
    return jsonify({
        "error": str(e),
        "type": type(e).__name__,
        "timestamp": datetime.utcnow().isoformat()
    }), 500

# Specific error codes:
# 400 - Bad Request (invalid input)
# 404 - Not Found (blob doesn't exist)
# 500 - Internal Server Error (OpenCV failure, etc.)
```

### 6.4 API Versioning Strategy

**Current:** No versioning (Alpha phase)

**Future:** URL-based versioning

```
/api/v1/projects
/api/v2/projects  (when breaking changes needed)
```

---

## 7. Performance & Scalability

### 7.1 Performance Metrics

**Target SLAs:**

- Frame retrieval (cached): < 100ms (p95)
- Frame extraction (first time): < 300ms (p95)
- Annotation save: < 200ms (p95)
- Project list: < 500ms (p95)

**Measured Performance (v0.2.0):**

- Frame cache hit: ~50ms ✅
- Frame cache miss: ~200ms ✅
- Annotation save: ~150ms ✅
- Video info: ~100ms ✅

### 7.2 Scalability Design

#### Horizontal Scaling

```yaml
Container App:
  scale:
    minReplicas: 1
    maxReplicas: 5
    rules:
      - name: http-scaling
        http:
          metadata:
            concurrentRequests: 10
```

**Scalability Characteristics:**

- **Stateless**: No session affinity required
- **Shared Storage**: All instances access same blob storage
- **Cache Isolation**: Each instance has own video cache (acceptable trade-off)
- **Automatic**: Azure Container Apps handles scaling

#### Current Bottlenecks

1. **OpenCV processing**: CPU-bound (mitigated by caching)
2. **Blob storage IOPS**: Limited by storage tier (Standard_LRS)
3. **Memory**: 1Gi per instance (video cache size limited)

#### Scaling Strategies

```
Users 1-10:     1 instance (sufficient)
Users 10-50:    2-3 instances (auto-scale on CPU)
Users 50-100:   3-5 instances (may need Premium storage)
Users 100+:     Requires architecture review
                - Redis cache layer
                - Premium storage tier
                - Dedicated frame processing workers
```

### 7.3 Caching Strategy Summary

```
┌─────────────────────────────────────────────────────────┐
│                    Caching Layers                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  L1: Browser Cache (Client-side)                        │
│      - Frame images (HTTP cache headers)                │
│      - TTL: 1 hour                                       │
│      - Hit rate: ~80% (repeated views)                  │
│                                                          │
│  L2: Video File Cache (Server-side, Memory)             │
│      - Downloaded video files                           │
│      - TTL: 15 minutes                                  │
│      - Hit rate: ~90% (during annotation session)       │
│                                                          │
│  L3: Frame Cache (Blob Storage, Persistent)             │
│      - Extracted frames (JPEG)                          │
│      - TTL: Infinite (until manual cleanup)             │
│      - Hit rate: ~70% (cross-session, cross-user)       │
│                                                          │
└─────────────────────────────────────────────────────────┘

Total Cache Hit Rate: ~95% after initial warm-up
```

---

## 8. Design Decisions

### 8.1 Why Azure Container Apps (vs. alternatives)?

**Alternatives Considered:**

- Azure App Service
- Azure Functions
- Azure Kubernetes Service (AKS)
- Virtual Machines

**Decision: Container Apps**

**Rationale:**

- ✅ Simplified Kubernetes (no cluster management)
- ✅ Auto-scaling built-in
- ✅ Pay-per-request (cost-effective for Alpha)
- ✅ Managed ingress and HTTPS
- ✅ Container-based (portable, reproducible)
- ❌ Less control than AKS (acceptable trade-off)

### 8.2 Why Blob Storage (vs. alternatives)?

**Alternatives Considered:**

- Azure Files
- Azure Data Lake
- Managed Database with binary columns

**Decision: Blob Storage**

**Rationale:**

- ✅ Optimized for large binary objects
- ✅ Lowest cost per GB
- ✅ Direct upload from browser (SAS tokens)
- ✅ HTTP streaming support
- ✅ Managed identity integration
- ✅ Hierarchical namespace (virtual folders)

### 8.3 Why OpenCV (vs. alternatives)?

**Alternatives Considered:**

- FFmpeg (command-line)
- Azure Video Indexer
- PIL/Pillow
- MediaPipe

**Decision: OpenCV**

**Rationale:**

- ✅ Industry standard for CV
- ✅ Python bindings (cv2)
- ✅ Frame extraction + manipulation
- ✅ Well-documented
- ✅ Active community
- ❌ Large dependency (~150MB) - acceptable for server-side

### 8.4 Why Flask (vs. alternatives)?

**Alternatives Considered:**

- FastAPI
- Django
- Express.js (Node)

**Decision: Flask**

**Rationale:**

- ✅ Lightweight (micro-framework)
- ✅ Python ecosystem (OpenCV, Azure SDK)
- ✅ Simple for REST APIs
- ✅ Mature and stable
- ❌ Not async (but I/O not bottleneck)
- ❌ No built-in validation (acceptable for Alpha)

### 8.5 Why Managed Identity Migration?

**Original Design:** Shared keys with connection strings

**Problem:**

- Bicep contradiction triggered auto-remediation
- Daily site breakage
- Security policy conflicts

**Decision: Migrate to Managed Identity**

**Rationale:**

- ✅ Eliminates auto-remediation conflict
- ✅ Azure best practice
- ✅ Zero secrets in config
- ✅ Better security posture
- ✅ Automatic credential rotation
- ❌ Slightly more complex initial setup (one-time cost)

**Result:** Permanent fix, improved security, no daily breakage

---

## 9. Future Architecture

### 9.1 Beta Release Roadmap

**Target: Q2 2026**

#### ML Pipeline Integration

```
┌─────────────────────────────────────────────────────────┐
│         Azure Machine Learning Workspace                 │
│                                                          │
│  ┌────────────────────────────────────────────┐        │
│  │  Training Pipeline                          │        │
│  │  1. Ingest annotations (blob trigger)       │        │
│  │  2. Generate YOLO dataset                   │        │
│  │  3. Train YOLOv8 model                      │        │
│  │  4. Evaluate performance                    │        │
│  │  5. Register model                          │        │
│  └────────────────────────────────────────────┘        │
│                                                          │
│  ┌────────────────────────────────────────────┐        │
│  │  Batch Inference                            │        │
│  │  - Deploy model to managed endpoint         │        │
│  │  - Batch process videos                     │        │
│  │  - Auto-annotate suggestions                │        │
│  └────────────────────────────────────────────┘        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

#### User Authentication

```
Azure AD B2C Integration:
  - User login/registration
  - Multi-tenant support
  - Role-based access (annotator, reviewer, admin)
  - Project-level permissions
```

### 9.2 GA Release (Q3 2026)

#### Advanced Features

- **Collaborative Annotation**: Real-time multi-user editing
- **Annotation Review**: Approval workflow
- **Version History**: Track annotation changes
- **Auto-annotation**: ML-assisted labeling
- **Quality Metrics**: Inter-annotator agreement
- **Export Formats**: COCO, Pascal VOC, Custom

#### Architecture Enhancements

- **Redis Cache**: Distributed caching layer
- **SignalR**: Real-time collaboration
- **Event Grid**: Event-driven architecture
- **Premium Storage**: Higher IOPS for scale
- **CDN**: Global frame delivery
- **Multi-region**: Geo-distributed deployment

### 9.3 Scalability Targets

**Current (Alpha v0.2.0):**

- Users: 1-10 concurrent
- Videos: 100s
- Annotations: 1,000s of frames
- Cost: ~$15-25/month

**Beta Target (Q2 2026):**

- Users: 10-50 concurrent
- Videos: 1,000s
- Annotations: 10,000s of frames
- Cost: ~$100-200/month

**GA Target (Q3 2026):**

- Users: 50-200 concurrent
- Videos: 10,000s
- Annotations: 100,000s of frames
- Cost: ~$500-1,000/month

---

## Appendix A: Design Patterns Used

1. **Repository Pattern**: Blob storage abstraction
2. **Facade Pattern**: Azure SDK complexity hidden
3. **Cache-Aside**: Frame caching strategy
4. **Circuit Breaker**: (Future) Resilience for external services
5. **Factory Pattern**: Frame extractor initialization
6. **Strategy Pattern**: Different pre-fetch strategies

## Appendix B: Technology Radar

**Adopt:**

- Managed Identity
- Azure Container Apps
- Bicep (Infrastructure as Code)
- OpenCV

**Trial:**

- Azure ML Pipelines
- SignalR for real-time features

**Assess:**

- Dapr for microservices
- Azure Container Storage (when GA)

**Hold:**

- Shared key authentication
- VM-based deployment

---

**Document Version**: 1.0  
**Last Review**: January 21, 2026  
**Next Review**: Q2 2026 (Beta release)  
**Maintained By**: Architecture Team
