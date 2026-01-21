from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.identity import DefaultAzureCredential
from datetime import datetime, timedelta
import os
import logging
import cv2
import numpy as np
from io import BytesIO
import json
import tempfile
import time
import threading

app = Flask(__name__, static_folder='static')
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Video cache: {blob_name: {'path': temp_path, 'last_accessed': timestamp}}
video_cache = {}
cache_lock = threading.Lock()
CACHE_TTL = 900  # 15 minutes in seconds


def cleanup_expired_cache():
    """Remove cached videos older than TTL"""
    with cache_lock:
        current_time = time.time()
        expired_keys = []

        for blob_name, cache_entry in video_cache.items():
            if current_time - cache_entry['last_accessed'] > CACHE_TTL:
                expired_keys.append(blob_name)

        for key in expired_keys:
            cache_entry = video_cache[key]
            try:
                if os.path.exists(cache_entry['path']):
                    os.unlink(cache_entry['path'])
                logger.info(f"Cleaned up cached video: {key}")
            except Exception as e:
                logger.error(f"Error cleaning up cache: {e}")
            del video_cache[key]


def get_cached_video(blob_name):
    """Get video from cache or download if not cached"""
    with cache_lock:
        # Check if video is in cache and not expired
        if blob_name in video_cache:
            cache_entry = video_cache[blob_name]
            if time.time() - cache_entry['last_accessed'] < CACHE_TTL:
                cache_entry['last_accessed'] = time.time()
                logger.info(f"Cache hit for {blob_name}")
                return cache_entry['path']
            else:
                # Expired, clean it up
                try:
                    if os.path.exists(cache_entry['path']):
                        os.unlink(cache_entry['path'])
                except Exception as e:
                    logger.error(f"Error cleaning expired cache: {e}")
                del video_cache[blob_name]

        # Download video to cache
        logger.info(f"Cache miss for {blob_name}, downloading...")
        blob_client = blob_service_client.get_blob_client(
            container=CONTAINER_NAME, blob=blob_name)

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        download_stream = blob_client.download_blob()
        temp_file.write(download_stream.readall())
        temp_file.close()

        video_cache[blob_name] = {
            'path': temp_file.name,
            'last_accessed': time.time()
        }

        return temp_file.name

# Start background cleanup thread


def background_cleanup():
    while True:
        time.sleep(300)  # Run cleanup every 5 minutes
        cleanup_expired_cache()


cleanup_thread = threading.Thread(target=background_cleanup, daemon=True)
cleanup_thread.start()


def get_or_create_frame(blob_name, frame_number):
    """Get frame from blob storage or extract and save if not exists"""
    # Generate frame blob name
    frame_blob_name = f"{blob_name}/frame_{frame_number:06d}.jpg"

    try:
        # Check if frame already exists in blob storage
        frame_blob_client = blob_service_client.get_blob_client(
            container=FRAMES_CONTAINER, blob=frame_blob_name)

        if frame_blob_client.exists():
            logger.info(f"Frame cache hit: {frame_blob_name}")
            # Download and return existing frame
            frame_data = frame_blob_client.download_blob().readall()
            return BytesIO(frame_data)

        logger.info(f"Frame cache miss: {frame_blob_name}, extracting...")

        # Frame doesn't exist, extract it
        temp_path = get_cached_video(blob_name)

        cap = cv2.VideoCapture(temp_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()

        if not ret:
            cap.release()
            return None

        # Get original dimensions
        orig_height, orig_width = frame.shape[:2]

        # Resize if wider than max width
        if orig_width > FRAME_MAX_WIDTH:
            scale = FRAME_MAX_WIDTH / orig_width
            new_width = FRAME_MAX_WIDTH
            new_height = int(orig_height * scale)
            frame = cv2.resize(frame, (new_width, new_height),
                               interpolation=cv2.INTER_AREA)
            logger.info(
                f"Resized frame from {orig_width}x{orig_height} to {new_width}x{new_height}")

        cap.release()

        # Encode as JPEG
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        frame_bytes = buffer.tobytes()

        # Save to blob storage for future use
        frame_blob_client.upload_blob(frame_bytes, overwrite=True)
        logger.info(f"Saved frame to blob storage: {frame_blob_name}")

        return BytesIO(frame_bytes)

    except Exception as e:
        logger.error(f"Error in get_or_create_frame: {str(e)}")
        raise


# Azure Storage configuration
STORAGE_ACCOUNT_NAME = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
CONTAINER_NAME = 'videos'
FRAMES_CONTAINER = 'frames'  # Persistent frame cache
FRAME_MAX_WIDTH = 1280  # Resize to 720p for storage efficiency

# Initialize blob service client with managed identity
# No connection strings or shared keys needed!
credential = DefaultAzureCredential()
blob_service_client = BlobServiceClient(
    account_url=f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
    credential=credential
)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "annotation-api"}), 200


@app.route('/api/get-upload-url', methods=['POST'])
def get_upload_url():
    """Generate SAS URL for direct blob upload using user delegation key"""
    try:
        data = request.json
        project_name = data.get('projectName', '').strip()
        file_name = data.get('fileName', '')

        if not project_name or not file_name:
            return jsonify({"error": "Missing projectName or fileName"}), 400

        # Create blob path: raw-videos/{project-name}/{timestamp}_{filename}
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        blob_name = f"raw-videos/{project_name}/{timestamp}_{file_name}"

        # Get blob client
        blob_client = blob_service_client.get_blob_client(
            container=CONTAINER_NAME, blob=blob_name)

        # Generate user delegation key (valid for Azure AD authentication)
        # Get user delegation key
        start_time = datetime.utcnow()
        expiry_time = start_time + timedelta(hours=1)

        user_delegation_key = blob_service_client.get_user_delegation_key(
            key_start_time=start_time,
            key_expiry_time=expiry_time
        )

        # Generate SAS token with user delegation key
        sas_token = generate_blob_sas(
            account_name=STORAGE_ACCOUNT_NAME,
            container_name=CONTAINER_NAME,
            blob_name=blob_name,
            user_delegation_key=user_delegation_key,
            permission=BlobSasPermissions(write=True, create=True),
            expiry=expiry_time
        )

        sas_url = f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{CONTAINER_NAME}/{blob_name}?{sas_token}"
        blob_url = f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{CONTAINER_NAME}/{blob_name}"

        logger.info(f"Generated SAS URL for: {blob_name}")

        return jsonify({
            "sasUrl": sas_url,
            "blobUrl": blob_url,
            "blobName": blob_name
        }), 200

    except Exception as e:
        logger.error(f"Error generating SAS URL: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/upload-complete', methods=['POST'])
def upload_complete():
    """Callback after successful upload"""
    try:
        data = request.json
        project_name = data.get('projectName')
        file_name = data.get('fileName')
        blob_url = data.get('blobUrl')

        logger.info(f"Upload completed: {project_name} - {file_name}")

        # Here you could:
        # - Update database with upload metadata
        # - Trigger video processing pipeline
        # - Send notifications

        return jsonify({
            "status": "success",
            "message": "Upload registered successfully",
            "projectName": project_name,
            "fileName": file_name
        }), 200

    except Exception as e:
        logger.error(f"Error processing upload completion: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/projects', methods=['GET'])
def list_projects():
    """List all projects (video folders)"""
    try:
        container_client = blob_service_client.get_container_client(
            CONTAINER_NAME)

        # List all blobs with prefix 'raw-videos/'
        blobs = container_client.list_blobs(name_starts_with='raw-videos/')

        projects = {}
        for blob in blobs:
            # Extract project name from path
            parts = blob.name.split('/')
            if len(parts) >= 2:
                project_name = parts[1]
                if project_name not in projects:
                    projects[project_name] = []

                projects[project_name].append({
                    'fileName': parts[-1],
                    'blobName': blob.name,
                    'size': blob.size,
                    'lastModified': blob.last_modified.isoformat()
                })

        return jsonify({
            "projects": [
                {"name": name, "videos": videos}
                for name, videos in projects.items()
            ]
        }), 200

    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/videos/<path:blob_name>', methods=['GET'])
def get_video_url(blob_name):
    """Get temporary URL for video viewing"""
    try:
        # Get user delegation key
        start_time = datetime.utcnow()
        expiry_time = start_time + timedelta(hours=2)

        user_delegation_key = blob_service_client.get_user_delegation_key(
            key_start_time=start_time,
            key_expiry_time=expiry_time
        )

        # Generate read-only SAS token with user delegation
        sas_token = generate_blob_sas(
            account_name=STORAGE_ACCOUNT_NAME,
            container_name=CONTAINER_NAME,
            blob_name=blob_name,
            user_delegation_key=user_delegation_key,
            permission=BlobSasPermissions(read=True),
            expiry=expiry_time
        )

        video_url = f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{CONTAINER_NAME}/{blob_name}?{sas_token}"

        return jsonify({"videoUrl": video_url}), 200

    except Exception as e:
        logger.error(f"Error generating video URL: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/videos/<path:blob_name>/info', methods=['GET'])
def get_video_info(blob_name):
    """Get video metadata (duration, fps, frame count) - uses caching"""
    try:
        # Get cached video path
        temp_path = get_cached_video(blob_name)

        # Get video info with OpenCV
        cap = cv2.VideoCapture(temp_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        cap.release()

        return jsonify({
            "fps": fps,
            "frameCount": frame_count,
            "duration": duration,
            "width": width,
            "height": height
        }), 200

    except Exception as e:
        logger.error(f"Error getting video info: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/videos/<path:blob_name>/frame/<int:frame_number>', methods=['GET'])
def get_video_frame(blob_name, frame_number):
    """Get frame (from blob storage cache or extract on-demand)"""
    try:
        frame_data = get_or_create_frame(blob_name, frame_number)

        if frame_data is None:
            return jsonify({"error": "Could not read frame"}), 404

        return send_file(
            frame_data,
            mimetype='image/jpeg',
            as_attachment=False
        )

    except Exception as e:
        logger.error(f"Error getting frame: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/videos/<path:blob_name>/prefetch', methods=['POST'])
def prefetch_frames(blob_name):
    """Pre-fetch multiple frames in background (non-blocking)"""
    try:
        data = request.json
        current_frame = data.get('currentFrame', 0)
        total_frames = data.get('totalFrames', 0)
        next_frames = data.get('nextFrames', 10)  # Configurable: default 10

        # Calculate frames to prefetch: configurable next N and previous 5
        frames_to_fetch = []

        # Next N frames (configurable)
        for i in range(1, next_frames + 1):
            next_frame = current_frame + i
            if next_frame < total_frames:
                frames_to_fetch.append(next_frame)

        # Previous 5 frames
        for i in range(1, 6):
            prev_frame = current_frame - i
            if prev_frame >= 0:
                frames_to_fetch.append(prev_frame)

        # Start background thread to prefetch
        def prefetch_worker():
            for frame_num in frames_to_fetch:
                try:
                    # Check if frame already exists
                    frame_blob_name = f"{blob_name}/frame_{frame_num:06d}.jpg"
                    frame_blob_client = blob_service_client.get_blob_client(
                        container=FRAMES_CONTAINER, blob=frame_blob_name)

                    if not frame_blob_client.exists():
                        # Extract and save frame
                        get_or_create_frame(blob_name, frame_num)
                        logger.info(f"Pre-fetched frame {frame_num}")
                except Exception as e:
                    logger.error(f"Error prefetching frame {frame_num}: {e}")

        # Run prefetch in background thread
        thread = threading.Thread(target=prefetch_worker, daemon=True)
        thread.start()

        return jsonify({
            "status": "prefetching",
            "frames": frames_to_fetch
        }), 200

    except Exception as e:
        logger.error(f"Error starting prefetch: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/annotations/<path:blob_name>', methods=['GET'])
def get_annotations(blob_name):
    """Load annotations for a video"""
    try:
        annotation_blob_name = f"{blob_name}.json"
        annotation_container = 'annotations'

        blob_client = blob_service_client.get_blob_client(
            container=annotation_container,
            blob=annotation_blob_name
        )

        if not blob_client.exists():
            return jsonify({"frames": {}}), 200

        download_stream = blob_client.download_blob()
        annotations = json.loads(download_stream.readall())

        logger.info(f"Loaded annotations for: {blob_name}")
        return jsonify(annotations), 200

    except Exception as e:
        logger.error(f"Error loading annotations: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/annotations/<path:blob_name>', methods=['POST'])
def save_annotations(blob_name):
    """Save annotations for a video and update project classes"""
    try:
        annotations = request.json

        # Save annotations as {blob_name}.json in 'annotations' container
        annotation_blob_name = f"{blob_name}.json"
        annotation_container = 'annotations'

        blob_client = blob_service_client.get_blob_client(
            container=annotation_container,
            blob=annotation_blob_name
        )

        blob_client.upload_blob(
            json.dumps(annotations, indent=2),
            overwrite=True
        )

        logger.info(f"Saved annotations for: {blob_name}")

        # Also save classes to project level
        classes = annotations.get('classes', [])
        if classes:
            # Extract project name from blob_name (e.g., raw-videos/project1/video.mp4 -> project1)
            parts = blob_name.split('/')
            if len(parts) >= 2:
                project_name = parts[1]
                class_blob_name = f"projects/{project_name}/classes.json"
                class_blob_client = blob_service_client.get_blob_client(
                    container='annotations', blob=class_blob_name)

                class_data = json.dumps({"classes": classes}, indent=2)
                class_blob_client.upload_blob(class_data, overwrite=True)
                logger.info(f"Updated project classes for {project_name}")

        return jsonify({"status": "success", "message": "Annotations saved"}), 200

    except Exception as e:
        logger.error(f"Error saving annotations: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/projects/<project_name>/classes', methods=['GET'])
def get_project_classes(project_name):
    """Get class definitions for a project"""
    try:
        class_blob_name = f"projects/{project_name}/classes.json"
        class_blob_client = blob_service_client.get_blob_client(
            container='annotations', blob=class_blob_name)

        if class_blob_client.exists():
            class_data = class_blob_client.download_blob().readall()
            return jsonify(json.loads(class_data)), 200
        else:
            # Return default classes
            default_classes = [
                {"id": 0, "name": "Person", "color": "#ff0000"},
                {"id": 1, "name": "Vehicle", "color": "#00ff00"},
                {"id": 2, "name": "Object", "color": "#0000ff"}
            ]
            return jsonify({"classes": default_classes}), 200

    except Exception as e:
        logger.error(f"Error getting project classes: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/projects/<project_name>/classes', methods=['POST'])
def save_project_classes(project_name):
    """Save class definitions for a project"""
    try:
        data = request.json
        classes = data.get('classes', [])

        class_blob_name = f"projects/{project_name}/classes.json"
        class_blob_client = blob_service_client.get_blob_client(
            container='annotations', blob=class_blob_name)

        class_data = json.dumps({"classes": classes}, indent=2)
        class_blob_client.upload_blob(class_data, overwrite=True)

        logger.info(f"Saved {len(classes)} classes for project {project_name}")
        return jsonify({"status": "success", "classes_count": len(classes)}), 200

    except Exception as e:
        logger.error(f"Error saving project classes: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/frames/cleanup', methods=['POST'])
def cleanup_frames():
    """Clean up cached frames older than specified days (default 30)"""
    try:
        days = request.json.get('days', 30) if request.json else 30
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        frames_container_client = blob_service_client.get_container_client(
            FRAMES_CONTAINER)

        deleted_count = 0
        deleted_size = 0

        # List all blobs in frames container
        blobs = frames_container_client.list_blobs()

        for blob in blobs:
            if blob.last_modified < cutoff_date:
                blob_client = frames_container_client.get_blob_client(
                    blob.name)
                deleted_size += blob.size
                blob_client.delete_blob()
                deleted_count += 1

        logger.info(
            f"Cleaned up {deleted_count} frames ({deleted_size / (1024*1024):.2f} MB)")

        return jsonify({
            "deleted_count": deleted_count,
            "deleted_size_mb": round(deleted_size / (1024*1024), 2),
            "cutoff_days": days
        }), 200

    except Exception as e:
        logger.error(f"Error cleaning up frames: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/frames/stats', methods=['GET'])
def frame_stats():
    """Get statistics about cached frames"""
    try:
        frames_container_client = blob_service_client.get_container_client(
            FRAMES_CONTAINER)

        total_count = 0
        total_size = 0

        blobs = frames_container_client.list_blobs()
        for blob in blobs:
            total_count += 1
            total_size += blob.size

        return jsonify({
            "total_frames": total_count,
            "total_size_mb": round(total_size / (1024*1024), 2),
            "total_size_gb": round(total_size / (1024*1024*1024), 2)
        }), 200

    except Exception as e:
        logger.error(f"Error getting frame stats: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/annotations/<path:blob_name>/export', methods=['GET'])
def export_annotations(blob_name):
    """Export annotations in YOLO format"""
    try:
        # Get annotations
        annotation_blob_name = f"{blob_name}.json"
        annotation_container = 'annotations'

        blob_client = blob_service_client.get_blob_client(
            container=annotation_container,
            blob=annotation_blob_name
        )

        if not blob_client.exists():
            return jsonify({"error": "No annotations found"}), 404

        download_stream = blob_client.download_blob()
        annotations = json.loads(download_stream.readall())

        # Convert to YOLO format (one line per object: class x_center y_center width height)
        yolo_data = []
        for frame_num, frame_data in annotations.get('frames', {}).items():
            for obj in frame_data.get('objects', []):
                class_id = obj.get('class_id', 0)
                bbox = obj.get('bbox', {})
                # YOLO format: normalized coordinates
                x_center = (bbox['x'] + bbox['width'] / 2) / \
                    annotations.get('video_width', 1)
                y_center = (bbox['y'] + bbox['height'] / 2) / \
                    annotations.get('video_height', 1)
                width = bbox['width'] / annotations.get('video_width', 1)
                height = bbox['height'] / annotations.get('video_height', 1)

                yolo_data.append(
                    f"{class_id} {x_center} {y_center} {width} {height}")

        return send_file(
            BytesIO('\n'.join(yolo_data).encode()),
            mimetype='text/plain',
            as_attachment=True,
            download_name=f"{blob_name.replace('/', '_')}_annotations.txt"
        )

    except Exception as e:
        logger.error(f"Error exporting annotations: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/videos/<path:blob_name>', methods=['GET'])
def get_video_url_old(blob_name):
    """Deprecated - use /info endpoint instead"""
    return get_video_url(blob_name)


@app.route('/')
def serve_annotation_tool():
    """Serve annotation UI"""
    return send_from_directory('static', 'index.html')


if __name__ == '__main__':
    # Ensure container exists
    try:
        container_client = blob_service_client.get_container_client(
            CONTAINER_NAME)
        if not container_client.exists():
            container_client.create_container()
            logger.info(f"Created container: {CONTAINER_NAME}")
    except Exception as e:
        logger.warning(f"Container check failed: {str(e)}")

    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
