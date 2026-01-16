# Development Guide

## Prerequisites

- Docker Desktop
- VS Code with Remote-Containers extension
- Azure subscription
- Git

## Getting Started

### 1. Clone and Open in Dev Container

```bash
git clone <your-repo>
cd video-annotation-platform
code .
```

VS Code will prompt you to reopen in container. Click "Reopen in Container".

### 2. Configure Azure

```bash
# Login to Azure
az login

# Set subscription
az account set --subscription "your-subscription-id"

# Create resource group
az group create --name rg-video-annotation --location eastus
```

### 3. Deploy Infrastructure

```bash
# Deploy with Bicep
az deployment group create \
  --resource-group rg-video-annotation \
  --template-file infrastructure/main.bicep \
  --parameters infrastructure/parameters.dev.json

# Or use the deployment script
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your Azure values:

```bash
cp .env.example .env
# Edit .env with your values
```

Get values from Azure:

```bash
# Storage account name
az storage account list --resource-group rg-video-annotation --query "[0].name" -o tsv

# Storage connection string
az storage account show-connection-string --name <storage-account-name> --query connectionString -o tsv

# ML workspace name
az ml workspace list --resource-group rg-video-annotation --query "[0].name" -o tsv
```

## Running Locally

### Upload Portal (Frontend)

```bash
cd frontend-upload
npm install
npm run dev
```

Access at http://localhost:3000

### Annotation Service (Backend)

```bash
cd annotation-service
pip install -r requirements.txt
python app/main.py
```

Access at http://localhost:5000

### Test ML Pipeline

```bash
cd ml-pipeline
python training/train_yolo.py --data data.yaml --test
```

## Development Workflow

### 1. Upload a Test Video

1. Open http://localhost:3000
2. Enter a project name
3. Select a video file (MP4, max 200MB)
4. Click "Upload Video"

### 2. Annotate Video

1. Open http://localhost:5000
2. Select your project from sidebar
3. Use annotation tools to label objects
4. Export annotations in COCO or YOLO format

### 3. Train Model

```bash
# Create sample dataset structure
mkdir -p datasets/{train,val}/images
mkdir -p datasets/{train,val}/labels

# Update data.yaml with correct paths
# Run training
python ml-pipeline/training/train_yolo.py \
  --data ml-pipeline/data.yaml \
  --epochs 10 \
  --batch 4
```

### 4. Deploy Model

```bash
# Deploy to Azure ML batch endpoint
python ml-pipeline/deployment/deploy_batch.py \
  --workspace-name mlw-vidannotate-dev \
  --resource-group rg-video-annotation \
  --subscription-id <your-subscription-id> \
  --model-name custom-detection-model
```

## Docker Commands

### Build Images Locally

```bash
# Frontend
cd frontend-upload
docker build -t video-upload-portal .

# Backend
cd annotation-service
docker build -t annotation-service .
```

### Push to Azure Container Registry

```bash
# Login to ACR
az acr login --name <your-acr-name>

# Tag and push
docker tag annotation-service <your-acr-name>.azurecr.io/annotation-service:latest
docker push <your-acr-name>.azurecr.io/annotation-service:latest
```

## Troubleshooting

### Issue: Can't connect to Azure Storage

**Solution:**
- Verify connection string in `.env`
- Check storage account firewall settings
- Ensure container "videos" exists

### Issue: Container App not updating

**Solution:**
```bash
# Force revision update
az containerapp revision list --name <app-name> --resource-group rg-video-annotation
az containerapp revision restart --name <app-name> --resource-group rg-video-annotation
```

### Issue: ML training fails

**Solution:**
- Check compute cluster is running: `az ml compute list`
- Verify dataset paths in `data.yaml`
- Check Azure ML workspace logs in portal

## Testing

### Unit Tests

```bash
# Backend
cd annotation-service
pytest tests/

# Frontend
cd frontend-upload
npm test
```

### Integration Tests

```bash
# Test upload flow
python tests/integration/test_upload.py

# Test annotation export
python tests/integration/test_annotation.py
```

## Debugging

### VS Code Launch Configurations

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Flask",
      "type": "python",
      "request": "launch",
      "module": "flask",
      "env": {
        "FLASK_APP": "annotation-service/app/main.py",
        "FLASK_ENV": "development"
      },
      "args": ["run", "--no-debugger", "--no-reload"],
      "jinja": true
    }
  ]
}
```

## Best Practices

1. **Always use dev containers** for consistent environment
2. **Commit .env.example**, never `.env`
3. **Use feature branches** for new development
4. **Test locally** before pushing to Azure
5. **Monitor costs** in Azure Cost Management
6. **Use low-priority VMs** for ML training to save costs
7. **Archive old videos** to Cool storage tier

## Additional Resources

- [Azure ML Documentation](https://learn.microsoft.com/azure/machine-learning/)
- [YOLOv8 Documentation](https://docs.ultralytics.com/)
- [Azure Container Apps](https://learn.microsoft.com/azure/container-apps/)
- [Azure Static Web Apps](https://learn.microsoft.com/azure/static-web-apps/)
