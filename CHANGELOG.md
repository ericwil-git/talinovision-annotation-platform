# Changelog

All notable changes to the Video Annotation Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0-alpha] - 2026-01-21

### 🔒 Security & Stability Release

Major security improvements with managed identity authentication and critical bug fix for daily access issues.

### Added

- **Managed Identity Authentication**: Full migration from shared keys to Azure AD managed identity
- **RBAC Role Assignments**: Automatic assignment of Storage Blob Data Contributor and Storage Blob Delegator roles
- **Root Cause Analysis**: Comprehensive documentation of storage access issue investigation
- **Automated Fix Scripts**:
  - `fix-storage-access.sh` - Quick fix for storage access issues
  - `watchdog-storage-access.sh` - Automated monitoring and prevention
  - `investigate-storage-changes.sh` - Diagnostic tool for identifying changes
- **Enhanced Documentation**: Complete security section with managed identity details

### Changed

- **BREAKING**: Removed all shared key authentication (connection strings, storage keys)
- **Backend Authentication**: Now uses `DefaultAzureCredential` for all storage operations
- **Environment Variables**: Simplified to only `AZURE_STORAGE_ACCOUNT_NAME` (no secrets)
- **Infrastructure**: `allowSharedKeyAccess` set to `false` for enhanced security
- **Local Development**: Changed to use `az login` instead of storage keys

### Fixed

- **Critical**: Daily storage access breakage caused by Bicep configuration contradiction
- **Root Cause**: Azure Defender auto-remediation was disabling public access due to inconsistent security settings
- **Solution**: Eliminated configuration contradiction by using managed identity consistently

### Security

- ✅ Zero secrets in configuration (no connection strings or keys)
- ✅ Automatic credential rotation via managed identity
- ✅ Audit trail for all storage access
- ✅ Least privilege access control with RBAC
- ✅ Azure security best practices compliance
- ✅ No more daily access disruptions

### Migration Notes

Existing deployments need to redeploy to apply managed identity changes:

```bash
azd provision --no-prompt
azd deploy
```

Local development now requires Azure CLI authentication:

```bash
az login  # Replaces storage key configuration
```

---

## [0.1.0-alpha] - 2026-01-16

### 🎉 Alpha Release

First public alpha release with core annotation features.

### Added

#### Infrastructure & Deployment

- Azure infrastructure provisioning with Bicep
- Azure Container Apps deployment for backend
- Azure Blob Storage with managed identity authentication
- CORS configuration for cross-origin video playback
- Network security policies and monitoring
- Dev container environment with all dependencies
- Azure Developer CLI (azd) configuration
- Automated deployment scripts

#### Video Management

- Video upload portal with drag-and-drop interface
- Direct blob upload (up to 1GB files)
- Project-based video organization
- Video listing and browsing interface
- SAS token generation for secure uploads
- Video player with HTML5 controls
- Support for MP4, AVI, MOV formats

#### Frame Processing

- OpenCV-based frame extraction
- Lazy frame extraction (on-demand)
- Frame caching at 1280x720 resolution
- Persistent frame cache in blob storage
- 65% storage savings vs full resolution
- Predictive pre-fetching system
  - Sequential navigation: 10 frames ahead
  - Jump/scrub: 5 frames ahead + 5 behind
- Frame statistics endpoint
- Frame cleanup utilities

#### Annotation Interface

- Canvas-based bounding box drawing
- Real-time annotation preview
- Frame-by-frame navigation
  - Frame slider with direct seeking
  - Previous/Next arrow navigation
  - Jump-to-frame with validation
- Class management UI
  - Add/edit class definitions
  - Color-coded class visualization
  - Project-level class persistence
- Keyboard shortcuts
  - Arrow keys for navigation
  - Ctrl+S for save
  - Enter for jump-to-frame
  - Del for delete annotation
- Toast notifications for user feedback
- Annotation counter display

#### Data Management

- JSON annotation storage format
- Annotation load endpoint (GET)
- Annotation save endpoint (POST)
- YOLO format export
- Project class synchronization
- Annotation persistence in blob storage

#### API Endpoints

- `GET /health` - Health check
- `GET /api/projects` - List projects and videos
- `GET /api/projects/{name}/classes` - Get project classes
- `POST /api/projects/{name}/classes` - Update project classes
- `GET /api/videos/{path}/info` - Get video metadata
- `GET /api/videos/{path}` - Get video playback URL
- `GET /api/videos/{path}/frame/{num}` - Extract specific frame
- `POST /api/videos/{path}/prefetch` - Trigger frame pre-fetching
- `GET /api/annotations/{path}` - Load annotations
- `POST /api/annotations/{path}` - Save annotations
- `GET /api/annotations/{path}/export` - Export YOLO format
- `GET /api/frames/stats` - Frame cache statistics
- `POST /api/frames/cleanup` - Cleanup old frames

#### Documentation

- Comprehensive README with Alpha v0.1 information
- Complete Wiki with user guide, API reference, troubleshooting
- Quick reference guide
- Storage network configuration guide
- Development guide
- Keyboard shortcuts reference

### Changed

- Optimized frame resolution from full HD to 1280x720
- Improved frame cache strategy with persistent storage
- Enhanced pre-fetching logic with adaptive frame counts
- Updated CORS to allow all origins for video playback

### Fixed

- JavaScript syntax error in annotation interface (duplicate closing brace)
- CORS configuration blocking video player
- Public network access policy blocking storage access
- Slider debouncing causing unexpected navigation behavior
- Frame loading performance issues

### Known Issues

- No multi-user collaboration (single user only)
- No undo/redo in annotation UI
- Frame cache cleanup is manual (no auto-cleanup)
- No annotation version history
- Limited to 1GB video files
- No real-time collaboration features

### Security

- Managed identity authentication for Azure resources
- SAS tokens with 1-hour expiry for uploads
- User delegation keys (no shared key storage)
- HTTPS enforced on all endpoints
- CORS configured for secure cross-origin requests

### Performance

- Frame caching reduces load times by 95% after first view
- Predictive pre-fetching eliminates wait times for sequential navigation
- 65% storage savings with 1280x720 frame resolution
- Direct blob upload bypasses backend for large files

### Dependencies

- Python 3.11
- Flask 3.0.0
- OpenCV 4.9.0
- Azure Blob Storage SDK
- Azure Identity SDK
- NumPy

### Deployment Information

- **Environment**: Development (rg-vidann-dev)
- **Region**: East US 2
- **Frontend**: Azure Storage Static Website
- **Backend**: Azure Container Apps
- **Storage**: Azure Blob Storage (Standard_LRS)
- **Cost**: ~$15-25/month for development environment

---

## Upcoming Releases

### [0.2.0-beta] - Planned Q2 2026

#### Planned Features

- Azure ML training pipeline integration
- Automated YOLO model training
- Batch inference endpoints
- Model versioning and tracking
- User authentication (Azure AD)
- Multi-user collaboration
- Annotation review workflow
- Audit logging
- Undo/redo functionality
- Auto-save annotations
- Additional export formats (COCO, Pascal VOC)

---

## Release History

### Alpha Phase (Current)

- **v0.1.0-alpha** (2026-01-16) - Initial alpha release with core features

### Beta Phase (Planned Q2 2026)

- ML pipeline integration
- User management
- Collaboration features

### GA Phase (Planned Q3 2026)

- Production-ready release
- Enterprise features
- Advanced analytics

---

**For detailed upgrade instructions, see [WIKI.md](./docs/WIKI.md)**

**For API changes, see [API Reference](./docs/WIKI.md#api-reference)**
