/**
 * API service module.
 *
 * Centralises all HTTP calls to the FastAPI backend so that individual
 * components stay free of axios configuration and URL strings.
 */

import axios from 'axios';

/**
 * Send a chat message to the backend and return the response payload.
 *
 * @param {string} message - The user's message text.
 * @returns {Promise<{response: string, timestamp: string}>}
 */
export const sendChatMessage = async (message) => {
  const { data } = await axios.post('/api/chat', { message });
  return data;
};

/**
 * Upload one or more wiki documents.
 *
 * @param {File[]} files - Array of File objects to upload.
 * @param {(percent: number) => void} [onProgress] - Optional upload-progress callback.
 * @returns {Promise<{message: string, files: object[]}>}
 */
export const uploadWikiFiles = async (files, onProgress) => {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));

  const { data } = await axios.post('/api/upload-wiki', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percent);
      }
    },
  });

  return data;
};

/**
 * Fetch the list of files uploaded during the current server session.
 *
 * @returns {Promise<{files: object[], total: number}>}
 */
export const getUploadedFiles = async () => {
  const { data } = await axios.get('/api/uploaded-files');
  return data;
};
