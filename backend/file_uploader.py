"""File Uploader for handling file uploads and validation"""

from typing import List
from fastapi import UploadFile, File, HTTPException
import os
from datetime import datetime


class FileUploader:
    """
    Manages file upload and validation
    Handles file type validation, size checking, and persistence
    """
    
    def __init__(self, upload_dir: str = "uploads"):
        """
        Initialize FileUploader
        
        Args:
            upload_dir: Directory where files will be stored
        """
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)
        self.allowed_types = [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]
        self.max_file_size = 10 * 1024 * 1024  # 10MB
    
    async def process_uploads(self, files: List[UploadFile]) -> List[dict]:
        """
        Process uploaded files with validation
        Validates file type and size, saves files, and returns file info
        
        Args:
            files: List of uploaded files
        
        Returns:
            List of file info dictionaries containing name, size, uploadTime, and path
            
        Raises:
            HTTPException: If file validation fails
        """
        uploaded_file_info = []
        
        for file in files:
            # Validate file type
            if file.content_type not in self.allowed_types:
                raise HTTPException(
                    status_code=400, 
                    detail=f"File {file.filename} has unsupported type. Only PDF and Word documents are allowed."
                )
            
            # Validate file size (10MB limit)
            file_content = await file.read()
            if len(file_content) > self.max_file_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} exceeds 10MB size limit"
                )
            
            # Save file
            file_path = os.path.join(self.upload_dir, file.filename)
            with open(file_path, "wb") as buffer:
                buffer.write(file_content)
            
            # Store file info
            file_info = {
                "name": file.filename,
                "size": len(file_content),
                "uploadTime": datetime.now(),
                "path": file_path
            }
            uploaded_file_info.append(file_info)
        
        return uploaded_file_info
