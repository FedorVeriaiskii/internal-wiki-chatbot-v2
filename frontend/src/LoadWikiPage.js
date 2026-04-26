import React, { useState } from 'react';
import axios from 'axios';
import './LoadWikiPage.css';

const LoadWikiPage = () => {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadStatus, setUploadStatus] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    const validFiles = files.filter(file => {
      const isValidType = file.type === 'application/pdf' || 
                         file.type === 'application/msword' ||
                         file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
      const isValidSize = file.size <= 10 * 1024 * 1024; // 10MB limit
      return isValidType && isValidSize;
    });

    if (validFiles.length !== files.length) {
      setUploadStatus('Some files were filtered out. Only PDF and Word documents under 10MB are allowed.');
    }

    setSelectedFiles(validFiles);
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      setUploadStatus('Please select files to upload.');
      return;
    }

    setIsUploading(true);
    setUploadStatus('Uploading files...');

    try {
      const formData = new FormData();
      selectedFiles.forEach((file) => {
        formData.append('files', file);
      });

      const response = await axios.post('/api/upload-wiki', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadStatus(`Uploading... ${percentCompleted}%`);
        },
      });

      setUploadStatus(`Successfully uploaded ${selectedFiles.length} file(s)!`);
      setUploadedFiles(prev => [...prev, ...response.data.files]);
      setSelectedFiles([]);
      
      // Reset file input
      const fileInput = document.getElementById('file-input');
      if (fileInput) fileInput.value = '';

    } catch (error) {
      console.error('Upload error:', error);
      setUploadStatus('Upload failed. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const removeFile = (index) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (fileName) => {
    const extension = fileName.split('.').pop().toLowerCase();
    switch (extension) {
      case 'pdf':
        return '📄';
      case 'doc':
      case 'docx':
        return '📝';
      default:
        return '📄';
    }
  };

  return (
    <div className="load-wiki-container">
      <div className="load-wiki-header">
        <h2>📚 Load Wiki Documents</h2>
        <p>Upload PDF and Word documents to enhance the chatbot's knowledge base</p>
      </div>

      <div className="upload-section">
        <div className="upload-area">
          <div className="file-input-wrapper">
            <input
              id="file-input"
              type="file"
              multiple
              accept=".pdf,.doc,.docx"
              onChange={handleFileSelect}
              className="file-input"
            />
            <label htmlFor="file-input" className="file-input-label">
              <div className="upload-icon">📁</div>
              <div className="upload-text">
                <span>Click to select files</span>
                <small>PDF, DOC, DOCX files up to 10MB each</small>
              </div>
            </label>
          </div>

          {selectedFiles.length > 0 && (
            <div className="selected-files">
              <h3>Selected Files ({selectedFiles.length})</h3>
              <div className="file-list">
                {selectedFiles.map((file, index) => (
                  <div key={index} className="file-item">
                    <div className="file-info">
                      <span className="file-icon">{getFileIcon(file.name)}</span>
                      <div className="file-details">
                        <span className="file-name">{file.name}</span>
                        <span className="file-size">{formatFileSize(file.size)}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => removeFile(index)}
                      className="remove-button"
                      type="button"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
              
              <button
                onClick={handleUpload}
                disabled={isUploading}
                className="upload-button"
              >
                {isUploading ? 'Uploading...' : `Upload ${selectedFiles.length} File(s)`}
              </button>
            </div>
          )}

          {uploadStatus && (
            <div className={`status-message ${uploadStatus.includes('Successfully') ? 'success' : uploadStatus.includes('failed') ? 'error' : 'info'}`}>
              {uploadStatus}
            </div>
          )}
        </div>
      </div>

      {uploadedFiles.length > 0 && (
        <div className="uploaded-files-section">
          <h3>📋 Recently Uploaded Files</h3>
          <div className="uploaded-files-list">
            {uploadedFiles.map((file, index) => (
              <div key={index} className="uploaded-file-item">
                <span className="file-icon">{getFileIcon(file.name)}</span>
                <div className="uploaded-file-info">
                  <span className="file-name">{file.name}</span>
                  <span className="upload-time">
                    Uploaded: {new Date(file.uploadTime).toLocaleString()}
                  </span>
                </div>
                <span className="status-badge success">✓ Processed</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="instructions">
        <h3>📋 Instructions</h3>
        <ul>
          <li>Upload PDF or Word documents that contain information you want the chatbot to learn from</li>
          <li>Files are processed automatically and integrated into the AI knowledge base</li>
          <li>Maximum file size: 10MB per file</li>
          <li>Supported formats: PDF (.pdf), Word (.doc, .docx)</li>
          <li>After uploading, go to the Chat page to ask questions about your documents</li>
        </ul>
      </div>
    </div>
  );
};

export default LoadWikiPage;