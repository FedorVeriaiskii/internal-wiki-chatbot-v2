import React, { useState } from 'react';

import { uploadWikiFiles } from './api';
import {
  ALLOWED_FILE_LABEL,
  ALLOWED_FILE_TYPES,
  DEFAULT_FILE_ICON,
  FILE_ICON_MAP,
  MAX_FILE_SIZE,
} from './constants';
import './LoadWikiPage.css';

/** Return an emoji icon for a given file name based on its extension. */
const getFileIcon = (fileName) => {
  const ext = fileName.split('.').pop().toLowerCase();
  return FILE_ICON_MAP[ext] ?? DEFAULT_FILE_ICON;
};

/** Format a byte count as a human-readable string (Bytes / KB / MB / GB). */
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const units = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${parseFloat((bytes / Math.pow(1024, i)).toFixed(2))} ${units[i]}`;
};

/** Derive the CSS modifier class for the status message bar. */
const statusClass = (msg) => {
  if (msg.includes('Successfully')) return 'success';
  if (msg.includes('failed') || msg.includes('filtered')) return 'error';
  return 'info';
};

const LoadWikiPage = () => {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadStatus, setUploadStatus] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);

    // Client-side validation mirrors backend rules for instant feedback
    const validFiles = files.filter(
      (file) => ALLOWED_FILE_TYPES.includes(file.type) && file.size <= MAX_FILE_SIZE
    );

    if (validFiles.length !== files.length) {
      setUploadStatus(
        'Some files were filtered out. Only PDF and Word documents under 10 MB are allowed.'
      );
    } else {
      setUploadStatus('');
    }

    setSelectedFiles(validFiles);
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      setUploadStatus('Please select files to upload.');
      return;
    }

    setIsUploading(true);
    setUploadStatus('Uploading files…');

    try {
      const data = await uploadWikiFiles(selectedFiles, (percent) => {
        setUploadStatus(`Uploading… ${percent}%`);
      });

      setUploadStatus(`Successfully uploaded ${selectedFiles.length} file(s)!`);
      setUploadedFiles((prev) => [...prev, ...data.files]);
      setSelectedFiles([]);

      // Reset the file input so the same file can be selected again if needed
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
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="load-wiki-container">
      <div className="load-wiki-header">
        <h2>📚 Load Wiki Documents</h2>
        <p>Upload PDF and Word documents to enhance the chatbot's knowledge base</p>
      </div>

      <div className="upload-section">
        <div className="upload-area">
          {/* File picker */}
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
                <small>{ALLOWED_FILE_LABEL}</small>
              </div>
            </label>
          </div>

          {/* Pending file list */}
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
                      aria-label={`Remove ${file.name}`}
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
                {isUploading ? 'Uploading…' : `Upload ${selectedFiles.length} File(s)`}
              </button>
            </div>
          )}

          {/* Status bar */}
          {uploadStatus && (
            <div className={`status-message ${statusClass(uploadStatus)}`}>
              {uploadStatus}
            </div>
          )}
        </div>
      </div>

      {/* Recently uploaded files (current session only) */}
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
        <h3>Instructions</h3>
        <ul>
          <li>Upload PDF or Word documents that contain information you want the chatbot to learn from</li>
          <li>Files are processed automatically and integrated into the AI knowledge base</li>
          <li>Maximum file size: 10 MB per file</li>
          <li>Supported formats: PDF (.pdf), Word (.doc, .docx)</li>
          <li>After uploading, go to the Chat page to ask questions about your documents</li>
        </ul>
      </div>
    </div>
  );
};

export default LoadWikiPage;
