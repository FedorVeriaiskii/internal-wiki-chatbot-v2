"""RAG (Retrieval-Augmented Generation) manager.

Handles document loading, text chunking, embedding, and similarity-based
retrieval via an in-memory LangChain vector store.
"""

import logging
from typing import List

from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import CHUNK_OVERLAP, CHUNK_SIZE, RETRIEVAL_K

logger = logging.getLogger(__name__)


class RAGManager:
    """Manages document embedding and semantic retrieval.

    Workflow:
    1. ``embed_files_to_vector_store`` — load documents from disk, split them
       into chunks, and build an in-memory vector store from their embeddings.
    2. ``retrieve_data_from_vector_store`` — perform a similarity search and
       return the top-k matching chunks.
    3. ``reset`` — clear the vector store (e.g. after a data reset).

    Note: the vector store is rebuilt from scratch on every call to
    ``embed_files_to_vector_store``, so all previously uploaded files must be
    passed each time.
    """

    def __init__(self) -> None:
        self.embeddings = OpenAIEmbeddings()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )
        self.vector_store: InMemoryVectorStore | None = None
        logger.info(
            "RAGManager initialised (chunk_size=%d, overlap=%d)",
            CHUNK_SIZE,
            CHUNK_OVERLAP,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def embed_files_to_vector_store(self, uploaded_files: list[dict]) -> None:
        """Load *uploaded_files*, chunk them, and rebuild the vector store.

        Args:
            uploaded_files: List of file-info dicts with at least ``name``
                and ``path`` keys (produced by FileUploader).
        """
        if not uploaded_files:
            logger.warning("embed_files_to_vector_store called with no files")
            return

        documents = self._load_documents(uploaded_files)
        if not documents:
            logger.error("No documents could be loaded — vector store not updated")
            return

        logger.info("Splitting %d document(s) into chunks…", len(documents))
        chunks = self.text_splitter.split_documents(documents)
        logger.info("Created %d text chunk(s)", len(chunks))

        try:
            self.vector_store = InMemoryVectorStore(self.embeddings)
            self.vector_store.add_documents(chunks)
            logger.info(
                "Vector store rebuilt with %d chunk(s) from %d document(s)",
                len(chunks),
                len(documents),
            )
        except Exception as exc:
            logger.exception("Failed to build vector store: %s", exc)
            self.vector_store = None

    def retrieve_data_from_vector_store(
        self, query: str, k: int = RETRIEVAL_K
    ) -> List[Document]:
        """Return the top-*k* document chunks most relevant to *query*.

        Args:
            query: Natural-language search string.
            k: Number of chunks to return (defaults to ``RETRIEVAL_K``).

        Returns:
            List of matching :class:`~langchain_core.documents.Document` objects,
            or an empty list if the store is not initialised or the search fails.
        """
        if self.vector_store is None:
            logger.warning("retrieve called but vector store is not initialised")
            return []

        try:
            results = self.vector_store.similarity_search(query, k=k)
            logger.info(
                "Similarity search returned %d result(s) for query: '%s'",
                len(results),
                query[:80],
            )
            return results
        except Exception as exc:
            logger.exception("Error during similarity search: %s", exc)
            return []

    def reset(self) -> None:
        """Clear the vector store, discarding all embedded documents."""
        self.vector_store = None
        logger.info("Vector store cleared")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_documents(self, uploaded_files: list[dict]) -> List[Document]:
        """Load raw documents from disk using the appropriate LangChain loader.

        Supports PDF (via PyPDFLoader) and Word (via Docx2txtLoader).
        Files with unsupported extensions are skipped with a warning.

        Args:
            uploaded_files: File-info dicts with ``name`` and ``path`` keys.

        Returns:
            Flat list of loaded :class:`~langchain_core.documents.Document` objects.
        """
        documents: List[Document] = []

        for file_info in uploaded_files:
            file_path = file_info["path"]
            file_name = file_info["name"]
            name_lower = file_name.lower()

            try:
                if name_lower.endswith(".pdf"):
                    loader = PyPDFLoader(file_path)
                    docs = loader.load()
                    documents.extend(docs)
                    logger.info("Loaded PDF '%s' (%d page(s))", file_name, len(docs))

                elif name_lower.endswith((".docx", ".doc")):
                    loader = Docx2txtLoader(file_path)
                    docs = loader.load()
                    documents.extend(docs)
                    logger.info(
                        "Loaded Word document '%s' (%d section(s))",
                        file_name,
                        len(docs),
                    )

                else:
                    logger.warning("Skipping unsupported file type: '%s'", file_name)

            except Exception as exc:
                logger.error("Error loading '%s': %s", file_name, exc)
                continue

        return documents
