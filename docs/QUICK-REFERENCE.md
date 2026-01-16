# Quick Reference - Video Annotation Platform Alpha v0.1

## Quick Links

- **Frontend**: https://vidanndevr5uc5ka6jxm4i.z20.web.core.windows.net/
- **API**: https://annotation-service.bluemushroom-befb422f.eastus2.azurecontainerapps.io/
- **Wiki**: [Complete Documentation](./WIKI.md)

## Common Commands

### Deployment

```bash
azd up                    # Full deployment (provision + deploy)
azd deploy annotation-api # Deploy backend only
azd provision            # Update infrastructure only
```

### Monitoring

```bash
# View logs
az containerapp logs show --name annotation-service --resource-group rg-vidann-dev --follow

# Check health
curl https://annotation-service.bluemushroom-befb422f.eastus2.azurecontainerapps.io/health

# View metrics
az monitor metrics list --resource <resource-id>
```

### Troubleshooting

```bash
# Check storage policies
./scripts/check-storage-policies.sh

# Enable public access
az storage account update -n vidanndevr5uc5ka6jxm4i -g rg-vidann-dev --public-network-access Enabled

# Restart container
az containerapp revision restart --name annotation-service --resource-group rg-vidann-dev
```

## Keyboard Shortcuts

### Annotation Interface

- `←/→` - Previous/Next frame
- `Ctrl+S` - Save annotations
- `Enter` - Jump to frame
- `Del` - Delete annotation

### Video Player

- `Space` - Play/Pause
- `F` - Fullscreen
- `M` - Mute
- `←/→` - Skip 5 seconds

## API Quick Reference

### Most Used Endpoints

**Get Projects**

```bash
GET /api/projects
```

**Get Video Info**

```bash
GET /api/videos/{blob_name}/info
```

**Get Frame**

```bash
GET /api/videos/{blob_name}/frame/{number}
```

**Save Annotations**

```bash
POST /api/annotations/{blob_name}
```

**Export YOLO**

```bash
GET /api/annotations/{blob_name}/export
```

## Common Issues & Solutions

| Issue                | Solution                                                                             |
| -------------------- | ------------------------------------------------------------------------------------ |
| Frames not loading   | Check public access: `az storage account update ... --public-network-access Enabled` |
| Video player stuck   | Verify CORS configuration allows all origins                                         |
| Projects not showing | Run `./scripts/check-storage-policies.sh`                                            |
| Deployment fails     | Check Bicep syntax, verify Azure quota                                               |
| High storage costs   | Run frame cleanup: `POST /api/frames/cleanup`                                        |

## Workflow Summary

1. **Upload Video** → Frontend → Direct to blob storage
2. **Annotate** → Navigate frames → Draw boxes → Save (Ctrl+S)
3. **Export** → Click "Export YOLO" → Download annotations
4. **Train** → Use exported YOLO format with YOLOv8/v5

## Storage Structure

```
videos/raw-videos/project1/video.mp4          # Original video
frames/raw-videos/project1/video.mp4/         # Cached frames (1280x720)
annotations/raw-videos/project1/video.mp4.json # Saved annotations
annotations/projects/project1/classes.json     # Project classes
```

## Cost Estimate

- Development: ~$15-25/month
- Production: ~$100-300/month (with scaling)

## Support

- **Wiki**: [docs/WIKI.md](./WIKI.md)
- **Issues**: Create in repository
- **Azure Portal**: [Resource Group](https://portal.azure.com/#@/resource/subscriptions/a80ade45-139e-4ad0-855f-374b089cdbd9/resourceGroups/rg-vidann-dev/overview)

---

**Alpha v0.1** | Released January 16, 2026
