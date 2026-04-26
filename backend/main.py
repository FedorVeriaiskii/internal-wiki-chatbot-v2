from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os
from datetime import datetime
import json
import tempfile
import shutil

# LangChain imports
from langchain_openai import ChatOpenAI

# Local imports
from rag_manager import RAGManager
from agent_manager import AgentManager
from file_uploader import FileUploader

app = FastAPI(title="Internal Wiki Chatbot API", version="2.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize LangChain components
# Initialize ChatOpenAI model
model = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.5,
)


# Initialize RAG manager
rag_manager = RAGManager()

# Initialize the agent manager
agent_manager = AgentManager(rag_manager, model)

# Initialize file uploader
file_uploader = FileUploader(UPLOAD_DIR)
class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    timestamp: datetime = None

class UploadedFile(BaseModel):
    name: str
    size: int
    uploadTime: datetime

# In-memory storage for demo purposes
uploaded_files = []
chat_history = []

@app.get("/")
async def root():
    return {"message": "Welcome to the Internal Wiki Chatbot API"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Wiki Chatbot API is running"}



@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(chat_message: ChatMessage):
    """
    Handle chat messages using LangChain agent with streaming
    Uses RAG (Retrieval Augmented Generation) with uploaded documents
    """
    agent = agent_manager.get_agent()
    
    user_message = chat_message.message.strip()
    
    # Check if agent is initialized
    if agent is None:
        response_text = "I'm sorry, but the AI agent is not properly initialized. Please check the system configuration."
    else:
        try:
            # Process agent stream and get response
            response_text = agent_manager.process_stream(user_message)
                
        except Exception as e:
            print(f"Error with agent execution: {str(e)}")
            # Fallback response
            if len(uploaded_files) == 0:
                response_text = "I don't have any documents to search through yet. Please upload some PDF or Word documents on the 'Load Wiki' page, and then I'll be able to help answer questions about their content."
            else:
                response_text = f"I encountered an error while processing your request: {str(e)}. You have {len(uploaded_files)} documents uploaded. Please try rephrasing your question."
    
    # Store chat history
    chat_entry = {
        "user_message": chat_message.message,
        "bot_response": response_text,
        "timestamp": datetime.now()
    }
    chat_history.append(chat_entry)
    
    return ChatResponse(
        response=response_text,
        timestamp=datetime.now()
    )



@app.post("/api/upload-wiki")
async def upload_and_embed_wiki_files(files: List[UploadFile] = File(...)):
    """
    Handle file uploads for wiki documents
    Supports PDF and Word documents
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Process and validate uploaded files
    uploaded_file_info = await file_uploader.process_uploads(files)
    
    # Add to global uploaded files list
    for file_info in uploaded_file_info:
        uploaded_files.append(file_info)
    
    # Process uploaded files and create embeddings in vector store
    try:
        rag_manager.embed_files_to_vector_store(uploaded_files)
    except Exception as e:
        print(f"Error processing files for embeddings: {str(e)}")
        # Continue with the response even if embedding fails
    
    return {
        "message": f"Successfully uploaded {len(files)} file(s)",
        "files": [
            {
                "name": f["name"],
                "size": f["size"],
                "uploadTime": f["uploadTime"]
            }
            for f in uploaded_file_info
        ]
    }

@app.get("/api/uploaded-files")
async def get_uploaded_files():
    """Get list of all uploaded files"""
    return {
        "files": [
            {
                "name": f["name"],
                "size": f["size"],
                "uploadTime": f["uploadTime"]
            }
            for f in uploaded_files
        ],
        "total": len(uploaded_files)
    }

@app.get("/api/chat-history")
async def get_chat_history():
    """Get chat history"""
    return {"history": chat_history}

@app.delete("/api/reset")
async def reset_data():
    """Reset all data (for demo purposes)"""
    global uploaded_files, chat_history
    
    # Remove uploaded files
    for file_info in uploaded_files:
        try:
            os.remove(file_info["path"])
        except FileNotFoundError:
            pass
    
    uploaded_files.clear()
    chat_history.clear()
    
    return {"message": "All data has been reset"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)