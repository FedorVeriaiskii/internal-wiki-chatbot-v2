"""FastAPI application entry point.

Wires together the RAGManager, AgentManager, and FileUploader and
exposes REST endpoints consumed by the React frontend.
"""

import logging
import os
from datetime import datetime
from typing import List

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from agent_manager import AgentManager
from config import CORS_ORIGINS, LLM_MODEL, LLM_TEMPERATURE, UPLOAD_DIR
from file_uploader import FileUploader
from rag_manager import RAGManager

# Load environment variables from backend/.env before any OpenAI client is created
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(title="Internal Wiki Chatbot API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Service initialisation
# ---------------------------------------------------------------------------
os.makedirs(UPLOAD_DIR, exist_ok=True)

model = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)

rag_manager = RAGManager()
agent_manager = AgentManager(rag_manager, model)
file_uploader = FileUploader(UPLOAD_DIR)

logger.info("All services initialised (RAG, Agent, FileUploader)")

# ---------------------------------------------------------------------------
# In-memory state (demo — resets on process restart)
# ---------------------------------------------------------------------------
uploaded_files: list[dict] = []
chat_history: list[dict] = []


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------
class ChatMessage(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    timestamp: datetime = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/")
async def root():
    return {"message": "Welcome to the Internal Wiki Chatbot API"}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Wiki Chatbot API is running"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(chat_message: ChatMessage):
    """Process a chat message through the LangChain ReAct agent.

    The agent uses the RAG search_documents tool to ground its answer in
    the uploaded wiki documents before responding.
    """
    user_message = chat_message.message.strip()
    logger.info("Chat request received (message length: %d)", len(user_message))

    if not agent_manager.is_ready:
        logger.error("Agent is not initialised — cannot handle chat request")
        response_text = (
            "I'm sorry, but the AI agent is not properly initialised. "
            "Please check the system configuration."
        )
    else:
        try:
            response_text = agent_manager.process_stream(user_message)
            logger.info("Agent returned a response (length: %d)", len(response_text))
        except Exception as exc:
            logger.exception("Error during agent execution: %s", exc)
            if not uploaded_files:
                response_text = (
                    "I don't have any documents to search through yet. "
                    "Please upload some PDF or Word documents on the 'Load Wiki' page."
                )
            else:
                response_text = (
                    f"I encountered an error while processing your request: {exc}. "
                    f"You have {len(uploaded_files)} document(s) uploaded. "
                    "Please try rephrasing your question."
                )

    # Persist to in-memory chat history
    chat_history.append(
        {
            "user_message": chat_message.message,
            "bot_response": response_text,
            "timestamp": datetime.now(),
        }
    )

    return ChatResponse(response=response_text, timestamp=datetime.now())


@app.post("/api/upload-wiki")
async def upload_and_embed_wiki_files(files: List[UploadFile] = File(...)):
    """Validate, save, and embed uploaded wiki documents.

    Accepted formats: PDF, DOC, DOCX (max 10 MB each).
    After saving, all currently uploaded files are re-embedded into the
    in-memory vector store so the agent can search them.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    logger.info("Upload request received for %d file(s)", len(files))

    # Persist files to disk and collect metadata
    uploaded_file_info = await file_uploader.process_uploads(files)
    uploaded_files.extend(uploaded_file_info)

    # Rebuild vector store embeddings from all known files
    try:
        rag_manager.embed_files_to_vector_store(uploaded_files)
    except Exception as exc:
        # Log the failure but still return a success response for the upload itself
        logger.error("Failed to embed uploaded files into vector store: %s", exc)

    logger.info(
        "Upload complete — %d new file(s), %d total",
        len(uploaded_file_info),
        len(uploaded_files),
    )

    return {
        "message": f"Successfully uploaded {len(files)} file(s)",
        "files": [
            {"name": f["name"], "size": f["size"], "uploadTime": f["uploadTime"]}
            for f in uploaded_file_info
        ],
    }


@app.get("/api/uploaded-files")
async def get_uploaded_files():
    """Return metadata for all files uploaded in the current session."""
    return {
        "files": [
            {"name": f["name"], "size": f["size"], "uploadTime": f["uploadTime"]}
            for f in uploaded_files
        ],
        "total": len(uploaded_files),
    }


@app.get("/api/chat-history")
async def get_chat_history():
    """Return the in-memory chat history for the current session."""
    return {"history": chat_history}


@app.delete("/api/reset")
async def reset_data():
    """Delete all uploaded files and clear chat history (demo purposes)."""
    global uploaded_files, chat_history

    # Remove files from disk
    for file_info in uploaded_files:
        try:
            os.remove(file_info["path"])
            logger.debug("Deleted file: %s", file_info["path"])
        except FileNotFoundError:
            logger.warning("File not found during reset: %s", file_info["path"])

    uploaded_files.clear()
    chat_history.clear()

    # Clear the vector store so stale embeddings are not reused
    rag_manager.reset()

    logger.info("All data has been reset")
    return {"message": "All data has been reset"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
