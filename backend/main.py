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
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain.schema import Document
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import DirectoryLoader

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
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'}
)

# Initialize text splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
)

# Initialize vector store (will be None until documents are loaded)
vector_store = None
retrieval_qa_chain = None

# Pydantic models
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
    Handle chat messages and return AI-generated responses
    In a production environment, this would integrate with an AI model
    and use RAG (Retrieval Augmented Generation) with uploaded documents
    """
    user_message = chat_message.message.lower().strip()
    
    # Simple response logic for demo purposes
    # In production, this would use an AI model with RAG
    if "hello" in user_message or "hi" in user_message:
        response_text = "Hello! I'm your internal wiki assistant. I can help you find information from your uploaded documents. What would you like to know?"
    elif "upload" in user_message:
        response_text = f"I can see you have {len(uploaded_files)} documents uploaded. You can upload more documents using the 'Load Wiki' page. What would you like to know about your documents?"
    elif "help" in user_message:
        response_text = "I can help you with information from your uploaded documents. Try asking questions about topics covered in your PDF or Word files. You can also upload new documents on the 'Load Wiki' page."
    elif "how" in user_message or "what" in user_message or "where" in user_message or "when" in user_message or "why" in user_message:
        response_text = f"That's a great question! In a full implementation, I would search through your {len(uploaded_files)} uploaded documents to find relevant information. For now, I'm a demo chatbot. Please upload some documents first on the 'Load Wiki' page."
    elif len(uploaded_files) == 0:
        response_text = "I don't have any documents to search through yet. Please upload some PDF or Word documents on the 'Load Wiki' page, and then I'll be able to help answer questions about their content."
    else:
        response_text = f"I understand you're asking about '{user_message}'. In a full implementation, I would analyze your {len(uploaded_files)} uploaded documents using AI to provide a detailed answer. This is currently a demo version."
    
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
async def upload_wiki_files(files: List[UploadFile] = File(...)):
    """
    Handle file uploads for wiki documents
    Supports PDF and Word documents
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    uploaded_file_info = []
    
    for file in files:
        # Validate file type
        allowed_types = [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"File {file.filename} has unsupported type. Only PDF and Word documents are allowed."
            )
        
        # Validate file size (10MB limit)
        file_content = await file.read()
        if len(file_content) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=400,
                detail=f"File {file.filename} exceeds 10MB size limit"
            )
        
        # Save file
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # Store file info
        file_info = {
            "name": file.filename,
            "size": len(file_content),
            "uploadTime": datetime.now(),
            "path": file_path
        }
        uploaded_files.append(file_info)
        uploaded_file_info.append(file_info)
        
        # In a production environment, here you would:
        # 1. Extract text from the PDF/Word document
        # 2. Split the text into chunks
        # 3. Generate embeddings using an embedding model
        # 4. Store embeddings in a vector database
        # 5. Index the content for retrieval
    
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



def embed_files_to_vector_store():
    """
    Placeholder function for embedding files to a vector store
    In a production environment, this would handle text extraction,
    chunking, embedding generation, and storage in a vector database
    """
    pass


def retrieve_data_from_vector_store():
    """
    Placeholder function for retrieving data from a vector store
    In a production environment, this would handle querying the vector database
    and returning relevant document chunks
    """
    pass    

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)