# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Install all dependencies:
```bash
npm run install:all
```

Run both services concurrently (recommended):
```bash
npm run dev
```

Run individually:
```bash
npm run dev:frontend   # React on http://localhost:3000
npm run dev:backend    # FastAPI on http://localhost:8000
```

Run backend tests:
```bash
cd backend && pytest
```

Run frontend tests:
```bash
cd frontend && npm test
```

Build frontend for production:
```bash
npm run build
```

## Environment

The backend requires `backend/.env` with:
```
OPENAI_API_KEY=<your key>
```

The backend is run from inside the `backend/` directory (`python -m uvicorn main:app --reload`), so relative paths like `uploads/` resolve relative to `backend/`.

## Architecture

This is a fullstack RAG chatbot. The key data flow on a chat request:

1. **`POST /api/chat`** (`main.py`) receives a user message
2. **`AgentManager.process_stream()`** (`agent_manager.py`) runs a LangGraph ReAct agent (`create_react_agent`) which decides whether to call the `search_documents` tool
3. **`search_documents` tool** delegates to **`RAGManager.retrieve_data_from_vector_store()`** (`rag_manager.py`), which performs similarity search on the in-memory vector store
4. The agent synthesizes a response from retrieved document chunks and returns it

On file upload (`POST /api/upload-wiki`):
1. **`FileUploader.process_uploads()`** (`file_uploader.py`) validates (PDF/.docx only, 10 MB limit) and saves files to `backend/uploads/`
2. **`RAGManager.embed_files_to_vector_store()`** loads documents via `PyPDFLoader`/`Docx2txtLoader`, splits with `RecursiveCharacterTextSplitter` (chunk size 1000, overlap 200), and builds a new `InMemoryVectorStore` using `OpenAIEmbeddings`

**Important state limitation**: Both the vector store and the `uploaded_files`/`chat_history` lists are in-memory only. All state resets when the backend process restarts. Re-uploading files after restart is required to restore RAG functionality.

The LLM model is `gpt-3.5-turbo` (configured in `main.py`). Embeddings use `OpenAIEmbeddings` (defaults to `text-embedding-ada-002`).

### Backend modules

| File | Responsibility |
|------|---------------|
| `main.py` | FastAPI app, endpoint definitions, wires up the three managers |
| `agent_manager.py` | LangGraph ReAct agent setup, tool definitions, streaming response processing |
| `rag_manager.py` | Document loading, chunking, embedding, vector store, similarity search |
| `file_uploader.py` | File validation (type + size) and disk persistence |

### Frontend pages

| File | Route |
|------|-------|
| `ChatPage.js` | `/` — chat interface |
| `LoadWikiPage.js` | `/load-wiki` — document upload UI |
| `Navigation.js` | shared nav bar |
