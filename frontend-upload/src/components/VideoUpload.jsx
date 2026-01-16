import { useState } from 'react'
import axios from 'axios'
import './VideoUpload.css'

// API Base URL - use environment variable or default to annotation service
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://annotation-service.bluemushroom-befb422f.eastus2.azurecontainerapps.io'

const VideoUpload = ({ onUploadComplete }) => {
  const [projectName, setProjectName] = useState('')
  const [selectedFile, setSelectedFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState('')

  const handleFileSelect = (e) => {
    const file = e.target.files[0]
    if (file) {
      // Validate file type
      const validTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/mkv']
      if (!validTypes.includes(file.type) && !file.name.match(/\.(mp4|avi|mov|mkv)$/i)) {
        setError('Please select a valid video file (MP4, AVI, MOV, MKV)')
        return
      }

      // Validate file size (max 1GB)
      if (file.size > 1024 * 1024 * 1024) {
        setError('File size must be less than 1GB')
        return
      }

      setSelectedFile(file)
      setError('')
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  const handleUpload = async () => {
    if (!projectName.trim()) {
      setError('Please enter a project name')
      return
    }

    if (!selectedFile) {
      setError('Please select a video file')
      return
    }

    setUploading(true)
    setProgress(0)
    setError('')

    try {
      // Step 1: Get SAS URL from backend
      const sasResponse = await axios.post(`${API_BASE_URL}/api/get-upload-url`, {
        projectName: projectName.trim(),
        fileName: selectedFile.name,
        contentType: selectedFile.type
      })

      const { sasUrl, blobUrl } = sasResponse.data

      // Step 2: Upload directly to Azure Blob Storage
      await axios.put(sasUrl, selectedFile, {
        headers: {
          'x-ms-blob-type': 'BlockBlob',
          'Content-Type': selectedFile.type
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          )
          setProgress(percentCompleted)
        }
      })

      // Step 3: Notify backend of successful upload
      await axios.post(`${API_BASE_URL}/api/upload-complete`, {
        projectName: projectName.trim(),
        fileName: selectedFile.name,
        blobUrl,
        fileSize: selectedFile.size
      })

      // Success!
      onUploadComplete({
        projectName: projectName.trim(),
        fileName: selectedFile.name,
        fileSize: formatFileSize(selectedFile.size),
        timestamp: new Date().toISOString()
      })

      // Reset form
      setProjectName('')
      setSelectedFile(null)
      setProgress(0)
    } catch (err) {
      console.error('Upload error:', err)
      setError(err.response?.data?.error || 'Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="video-upload">
      <div className="upload-card">
        <h2>Upload Video</h2>

        <div className="form-group">
          <label htmlFor="projectName">Project Name</label>
          <input
            id="projectName"
            type="text"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            placeholder="e.g., object-detection-project-1"
            disabled={uploading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="videoFile">Video File</label>
          <div className="file-input-wrapper">
            <input
              id="videoFile"
              type="file"
              accept="video/*,.mp4,.avi,.mov,.mkv"
              onChange={handleFileSelect}
              disabled={uploading}
            />
            {selectedFile && (
              <div className="file-info">
                <span className="file-name">📹 {selectedFile.name}</span>
                <span className="file-size">{formatFileSize(selectedFile.size)}</span>
              </div>
            )}
          </div>
          <small>Supported formats: MP4, AVI, MOV, MKV (max 200MB)</small>
        </div>

        {error && (
          <div className="error-message">
            ⚠️ {error}
          </div>
        )}

        {uploading && (
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }}>
              {progress}%
            </div>
          </div>
        )}

        <button
          className="upload-button"
          onClick={handleUpload}
          disabled={uploading || !selectedFile || !projectName.trim()}
        >
          {uploading ? 'Uploading...' : 'Upload Video'}
        </button>
      </div>
    </div>
  )
}

export default VideoUpload
