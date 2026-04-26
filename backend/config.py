"""Application configuration constants.

All tuneable values live here so that main.py and the service
modules stay free of magic literals.
"""

# ---------------------------------------------------------------------------
# File upload
# ---------------------------------------------------------------------------
UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_CONTENT_TYPES = [
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]

# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------
LLM_MODEL = "gpt-3.5-turbo"
LLM_TEMPERATURE = 0.5

# ---------------------------------------------------------------------------
# RAG / vector store
# ---------------------------------------------------------------------------
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
RETRIEVAL_K = 3  # number of document chunks returned per similarity search

# ---------------------------------------------------------------------------
# API / CORS
# ---------------------------------------------------------------------------
CORS_ORIGINS = ["http://localhost:3000"]  # React dev server
