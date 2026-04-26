# Internal Wiki Chatbot

An AI-powered internal wiki chatbot built with React.js frontend and Python FastAPI backend. Upload documents and chat with your knowledge base using natural language.

## 🚀 Features

- **Intelligent Chat Interface**: Natural language conversation with your documents
- **Document Upload**: Support for PDF and Word documents (up to 10MB each)
- **Responsive Design**: Modern, mobile-friendly interface
- **Real-time Processing**: Instant file upload and chat responses
- **RESTful API**: Well-documented FastAPI backend with automatic OpenAPI docs

## 📁 Project Structure

```
internal-wiki-chatbot/
├── frontend/                 # React.js application
│   ├── public/
│   ├── src/
│   │   ├── ChatPage.js      # Main chat interface
│   │   ├── LoadWikiPage.js  # Document upload page  
│   │   ├── Navigation.js    # Navigation component
│   │   └── App.js          # Main app with routing
│   └── package.json
├── backend/                  # Python FastAPI application
│   ├── main.py              # FastAPI app with chat & upload endpoints
│   ├── requirements.txt     # Python dependencies
│   └── uploads/             # Uploaded documents storage
├── package.json             # Root package.json for scripts
└── README.md
```

## 🛠️ Installation

### Prerequisites

- **Node.js** (version 16 or higher)
- **npm** or **yarn**
- **Python** (version 3.8 or higher)
- **pip** (Python package installer)

### Setup Instructions

1. **Install root dependencies** (for concurrent development):
   ```bash
   npm install
   ```

2. **Install frontend dependencies**:
   ```bash
   npm run install:frontend
   ```

3. **Install backend dependencies**:
   ```bash
   npm run install:backend
   ```

4. **Or install all at once**:
   ```bash
   npm run install:all
   ```

## 🚀 Running the Application

### Development Mode (Recommended)

Run both frontend and backend simultaneously:
```bash
npm run dev
```

This will start:
- Frontend server on `http://localhost:3000`
- Backend server on `http://localhost:8000`

### Individual Services

**Frontend only**:
```bash
npm run dev:frontend
```

**Backend only**:
```bash
npm run dev:backend
```

**Production build**:
```bash
npm run build
```

## 📡 API Endpoints

The backend provides the following REST API endpoints:

### Chat Endpoints
- `POST /api/chat` - Send chat message and get AI response
- `GET /api/chat-history` - Retrieve chat conversation history

### File Management
- `POST /api/upload-wiki` - Upload PDF/Word documents
- `GET /api/uploaded-files` - List all uploaded files
- `DELETE /api/reset` - Reset all data (demo purposes)

### System
- `GET /` - Welcome message
- `GET /api/health` - Health check

## 🌐 API Documentation

When the backend is running, you can access interactive API documentation at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🎯 Usage

### Main Chat Interface
1. Start the application using `npm run dev`
2. Open your browser to `http://localhost:3000`
3. Use the chat interface to ask questions about your documents
4. The AI assistant will respond based on uploaded content

### Loading Wiki Documents
1. Navigate to the "Load Wiki" page
2. Upload PDF or Word documents (max 10MB each)
3. Files are automatically processed and indexed
4. Return to chat to ask questions about the uploaded content

## 🔧 Configuration

### Backend Configuration

The backend is configured with CORS to allow requests from the React development server (`http://localhost:3000`).

### Frontend Configuration

The frontend uses a proxy configuration in `package.json` to forward API requests to the backend server.

## 🧪 Testing

The project includes test configurations for both frontend and backend:

**Frontend tests** (React Testing Library):
```bash
cd frontend && npm test
```

**Backend tests** (pytest):
```bash
cd backend && pytest
```

## 📦 Production Deployment

1. **Build the frontend**:
   ```bash
   npm run build
   ```

2. **Serve the built files** with your preferred web server

3. **Deploy the backend** using a production ASGI server like Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

## 🛡️ Security Notes

- The current implementation uses in-memory storage for simplicity
- For production, implement proper database integration
- Add authentication and authorization as needed
- Configure proper CORS origins for production

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the ISC License - see the package.json file for details.