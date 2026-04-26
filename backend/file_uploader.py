"""File upload handler — validation, persistence, and metadata extraction."""

import logging
import os
from datetime import datetime
from typing import List

from fastapi import HTTPException, UploadFile

from config import ALLOWED_CONTENT_TYPES, MAX_FILE_SIZE, UPLOAD_DIR

logger = logging.getLogger(__name__)


class FileUploader:
    """Validates and persists uploaded files.

    Enforces:
    - Allowed MIME types (PDF, DOC, DOCX)
    - Maximum file size (10 MB)

    Saves accepted files to *upload_dir* and returns structured metadata
    for each file that callers can store and pass to RAGManager.
    """

    def __init__(self, upload_dir: str = UPLOAD_DIR) -> None:
        self.upload_dir = upload_dir
        self.allowed_types = ALLOWED_CONTENT_TYPES
        self.max_file_size = MAX_FILE_SIZE
        os.makedirs(upload_dir, exist_ok=True)
        logger.debug(
            "FileUploader ready (dir='%s', max_size=%d B)", upload_dir, MAX_FILE_SIZE
        )

    async def process_uploads(self, files: List[UploadFile]) -> List[dict]:
        """Validate and save *files*, returning metadata for each accepted file.

        Validation is done file-by-file; the first invalid file raises an
        HTTPException, aborting the entire batch.

        Args:
            files: List of incoming :class:`~fastapi.UploadFile` objects.

        Returns:
            List of dicts with keys: ``name``, ``size``, ``uploadTime``, ``path``.

        Raises:
            :class:`~fastapi.HTTPException`: On MIME-type or size violation.
        """
        results: List[dict] = []

        for file in files:
            logger.debug("Processing upload: '%s' (%s)", file.filename, file.content_type)

            # --- MIME-type validation ---
            if file.content_type not in self.allowed_types:
                logger.warning(
                    "Rejected '%s': unsupported content type '%s'",
                    file.filename,
                    file.content_type,
                )
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"File '{file.filename}' has an unsupported type "
                        f"({file.content_type}). Only PDF and Word documents are allowed."
                    ),
                )

            # --- Read content and size validation ---
            content = await file.read()
            if len(content) > self.max_file_size:
                logger.warning(
                    "Rejected '%s': size %d B exceeds limit %d B",
                    file.filename,
                    len(content),
                    self.max_file_size,
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"File '{file.filename}' exceeds the 10 MB size limit.",
                )

            # --- Persist to disk ---
            file_path = os.path.join(self.upload_dir, file.filename)
            with open(file_path, "wb") as buf:
                buf.write(content)

            logger.info("Saved '%s' to '%s' (%d B)", file.filename, file_path, len(content))

            results.append(
                {
                    "name": file.filename,
                    "size": len(content),
                    "uploadTime": datetime.now(),
                    "path": file_path,
                }
            )

        return results
