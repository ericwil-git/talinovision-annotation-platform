import { useState } from 'react'
import VideoUpload from './components/VideoUpload'
import './App.css'

function App() {
  const [uploads, setUploads] = useState([])

  const handleUploadComplete = (uploadInfo) => {
    setUploads([uploadInfo, ...uploads])
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>🎥 Video Annotation Platform</h1>
        <p>Upload videos for AI model training</p>
      </header>

      <main className="app-main">
        <VideoUpload onUploadComplete={handleUploadComplete} />

        {uploads.length > 0 && (
          <div className="upload-history">
            <h2>Recent Uploads</h2>
            <div className="upload-list">
              {uploads.map((upload, index) => (
                <div key={index} className="upload-item">
                  <div className="upload-icon">✅</div>
                  <div className="upload-details">
                    <h3>{upload.projectName}</h3>
                    <p>{upload.fileName} • {upload.fileSize}</p>
                    <small>{new Date(upload.timestamp).toLocaleString()}</small>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      <footer className="app-footer">
        <p>Powered by Azure • Professional Video Annotation Solution</p>
      </footer>
    </div>
  )
}

export default App
