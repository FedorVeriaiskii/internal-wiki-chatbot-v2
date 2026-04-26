"""RAG Manager for document retrieval and vector store management"""

from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document


class RAGManager:
    """
    Manages Retrieval Augmented Generation (RAG) functionality including:
    - Document embedding and vector store management
    - Document retrieval based on similarity search
    """
    
    def __init__(self):
        """Initialize RAG components: embeddings, text splitter, and vector store"""
        self.embeddings = OpenAIEmbeddings()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self.vector_store = None
    
    def _load_documents(self, uploaded_files):
        """
        Load documents from uploaded files
        Handles PDF and Microsoft Word documents using LangChain loaders
        
        Args:
            uploaded_files: List of file info dictionaries containing file metadata
        
        Returns:
            List of loaded documents
        """
        documents = []
        
        for file_info in uploaded_files:
            file_path = file_info["path"]
            file_name = file_info["name"]
            
            try:
                # Load PDF documents
                if file_name.lower().endswith('.pdf'):
                    loader = PyPDFLoader(file_path)
                    docs = loader.load()
                    documents.extend(docs)
                    print(f"Loaded PDF: {file_name} ({len(docs)} pages)")
                
                # Load Microsoft Word documents using Docx2txtLoader
                elif file_name.lower().endswith(('.docx', '.doc')):
                    loader = Docx2txtLoader(file_path)
                    docs = loader.load()
                    documents.extend(docs)
                    print(f"Loaded Word document: {file_name} ({len(docs)} documents)")
                
                else:
                    print(f"Unsupported file type: {file_name}")
                    
            except Exception as e:
                print(f"Error loading {file_name}: {str(e)}")
                continue
        
        return documents
    
    def embed_files_to_vector_store(self, uploaded_files):
        """
        Process uploaded files and create embeddings in in-memory vector store
        Handles PDF and Microsoft Word documents using LangChain loaders
        Uses OpenAIEmbeddings and RecursiveCharacterTextSplitter
        
        Args:
            uploaded_files: List of file info dictionaries containing file metadata
        """
        if not uploaded_files:
            print("No files to process")
            return
        
        # Load all documents
        documents = self._load_documents(uploaded_files)
        
        if not documents:
            print("No documents were successfully loaded")
            return
        
        # Split documents into chunks using RecursiveCharacterTextSplitter
        print(f"Splitting {len(documents)} documents into chunks...")
        text_chunks = self.text_splitter.split_documents(documents)
        print(f"Created {len(text_chunks)} text chunks")
        
        # Create in-memory vector store with OpenAI embeddings
        try:
            self.vector_store = InMemoryVectorStore(self.embeddings)
            
            # Add documents to vector store
            self.vector_store.add_documents(text_chunks)
            print(f"Successfully created in-memory vector store with {len(text_chunks)} chunks")
            
        except Exception as e:
            print(f"Error creating in-memory vector store: {str(e)}")
            return
        
        print(f"Successfully processed {len(documents)} documents into in-memory vector store")
    
    def retrieve_data_from_vector_store(self, query: str, k: int = 3) -> List[Document]:
        """
        Retrieve relevant documents from vector store based on query using similarity search
        
        Args:
            query: Search query string
            k: Number of documents to retrieve (default: 3)
        
        Returns:
            List of Document objects containing relevant information
        """
        if self.vector_store is None:
            print("Vector store is not initialized")
            return []
        
        try:
            # Perform similarity search on the vector store
            results = self.vector_store.similarity_search(query, k=k)
            print(f"Retrieved {len(results)} documents for query: '{query}'")
            return results
            
        except Exception as e:
            print(f"Error retrieving from vector store: {str(e)}")
            return []
