"""
RAG (Retrieval-Augmented Generation) Pipeline using LangChain and Pinecone.
Handles document ingestion, embedding, and retrieval for healthcare knowledge.
"""

import os
import asyncio
from typing import List, Dict, Optional, Any
from pathlib import Path
import logging

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.document_loaders import (
    DirectoryLoader, 
    TextLoader,
    CSVLoader
)

# Try to import PDFLoader, but make it optional
try:
    from langchain_community.document_loaders import PyPDFLoader as PDFLoader
except ImportError:
    try:
        from langchain_community.document_loaders import PDFPlumberLoader as PDFLoader
    except ImportError:
        PDFLoader = None

# Pinecone imports
try:
    import pinecone
    from langchain_pinecone import PineconeVectorStore
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    pinecone = None
    PineconeVectorStore = None

from app.core.config import (
    PINECONE_API_KEY,
    PINECONE_ENV,
    PINECONE_INDEX,
    DOCUMENTS_PATH,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    EMBEDDING_MODEL,
    USE_DEV_LLM
)

logger = logging.getLogger(__name__)


class RAGPipelineError(Exception):
    """Custom exception for RAG pipeline errors."""
    pass


class MockEmbeddings:
    """Mock embeddings for development mode."""
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Return mock embeddings for documents."""
        return [[0.1] * 384 for _ in texts]  # 384-dimensional mock embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """Return mock embedding for query."""
        return [0.1] * 384


class MockVectorStore:
    """Mock vector store for development mode."""
    
    def __init__(self):
        self.documents = []
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to mock store."""
        self.documents.extend(documents)
        logger.info(f"Added {len(documents)} documents to mock vector store")
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """Return mock similar documents."""
        # Return first k documents as mock results
        return self.documents[:k] if self.documents else []
    
    def as_retriever(self, search_kwargs: Optional[Dict] = None):
        """Return mock retriever."""
        return MockRetriever(self, search_kwargs)


class MockRetriever:
    """Mock retriever for development mode."""
    
    def __init__(self, vector_store, search_kwargs=None):
        self.vector_store = vector_store
        self.search_kwargs = search_kwargs or {}
    
    def get_relevant_documents(self, query: str) -> List[Document]:
        """Get relevant documents from mock store."""
        k = self.search_kwargs.get("k", 5)  # Use k from search_kwargs
        return self.vector_store.similarity_search(query, k=k)


class RAGPipeline:
    """
    RAG Pipeline for document ingestion, embedding, and retrieval.
    Supports both production (Pinecone) and development (mock) modes.
    """
    
    def __init__(self):
        self.use_dev_mode = USE_DEV_LLM or not PINECONE_AVAILABLE
        
        if self.use_dev_mode:
            logger.info("RAG Pipeline running in development mode")
            self._init_dev_mode()
        else:
            logger.info("RAG Pipeline running in production mode with Pinecone")
            self._init_production_mode()
    
    def _init_dev_mode(self):
        """Initialize RAG pipeline in development mode."""
        self.embeddings = MockEmbeddings()
        self.vectorstore = MockVectorStore()
        self.index = None
        
        # Load some sample documents for dev mode
        self._load_sample_documents()
    
    def _init_production_mode(self):
        """Initialize RAG pipeline in production mode with Pinecone."""
        if not PINECONE_API_KEY:
            raise RAGPipelineError("Pinecone API key not configured")
        
        try:
            # Initialize Pinecone
            pinecone.init(
                api_key=PINECONE_API_KEY,
                environment=PINECONE_ENV
            )
            
            # Get or create index
            if PINECONE_INDEX not in pinecone.list_indexes():
                logger.info(f"Creating Pinecone index: {PINECONE_INDEX}")
                pinecone.create_index(
                    name=PINECONE_INDEX,
                    dimension=384,  # Dimension for llama-text-embed-v2
                    metric="cosine"
                )
            
            self.index = pinecone.Index(PINECONE_INDEX)
            
            # Initialize embeddings (using Pinecone's built-in model)
            from langchain_community.embeddings import HuggingFaceEmbeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            
            # Initialize vector store
            self.vectorstore = PineconeVectorStore(
                index=self.index,
                embedding=self.embeddings
            )
            
            logger.info("Pinecone RAG pipeline initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            logger.info("Falling back to development mode")
            self.use_dev_mode = True
            self._init_dev_mode()
    
    def _load_sample_documents(self):
        """Load sample healthcare documents for development mode."""
        sample_docs = [
            Document(
                page_content="Headaches can be caused by various factors including stress, dehydration, lack of sleep, or underlying medical conditions. Common types include tension headaches, migraines, and cluster headaches.",
                metadata={"source": "headache_guide.txt", "topic": "headaches"}
            ),
            Document(
                page_content="Fever is a temporary increase in body temperature, often due to an infection. Normal body temperature is around 98.6°F (37°C). A fever is generally considered to be 100.4°F (38°C) or higher.",
                metadata={"source": "fever_info.txt", "topic": "fever"}
            ),
            Document(
                page_content="Chest pain can have many causes, ranging from minor issues like muscle strain to serious conditions like heart attack. Seek immediate medical attention for severe, crushing chest pain.",
                metadata={"source": "chest_pain.txt", "topic": "chest_pain"}
            ),
            Document(
                page_content="Diabetes is a group of metabolic disorders characterized by high blood sugar levels. Type 1 diabetes is usually diagnosed in childhood, while Type 2 diabetes typically develops in adults.",
                metadata={"source": "diabetes_overview.txt", "topic": "diabetes"}
            ),
            Document(
                page_content="Hypertension (high blood pressure) is often called the 'silent killer' because it usually has no symptoms. Normal blood pressure is less than 120/80 mmHg.",
                metadata={"source": "hypertension.txt", "topic": "hypertension"}
            )
        ]
        
        self.vectorstore.add_documents(sample_docs)
        logger.info(f"Loaded {len(sample_docs)} sample documents for development mode")
    
    async def ingest_documents(self, path: str = None) -> int:
        """
        Load, split, embed and upsert documents into the vector store.
        
        Args:
            path: Path to documents directory (defaults to DOCUMENTS_PATH)
            
        Returns:
            Number of document chunks processed
        """
        
        if self.use_dev_mode:
            logger.info("Document ingestion skipped in development mode (using sample docs)")
            return len(self.vectorstore.documents)
        
        path = path or DOCUMENTS_PATH
        
        if not os.path.exists(path):
            logger.warning(f"Documents path does not exist: {path}")
            return 0
        
        try:
            # Load documents from directory
            documents = await self._load_documents(path)
            
            if not documents:
                logger.warning(f"No documents found in {path}")
                return 0
            
            # Split documents into chunks
            chunks = await self._split_documents(documents)
            
            # Add to vector store
            await self._add_to_vectorstore(chunks)
            
            logger.info(f"Successfully ingested {len(chunks)} document chunks")
            return len(chunks)
            
        except Exception as e:
            logger.error(f"Document ingestion failed: {e}")
            raise RAGPipelineError(f"Failed to ingest documents: {e}")
    
    async def _load_documents(self, path: str) -> List[Document]:
        """Load documents from directory."""
        
        documents = []
        
        # Load text files
        try:
            text_loader = DirectoryLoader(
                path, 
                glob="**/*.txt", 
                loader_cls=TextLoader,
                show_progress=True
            )
            text_docs = text_loader.load()
            documents.extend(text_docs)
            logger.info(f"Loaded {len(text_docs)} text files")
        except Exception as e:
            logger.warning(f"Failed to load text files: {e}")
        
        # Load PDF files (if PDFLoader is available)
        if PDFLoader:
            try:
                pdf_loader = DirectoryLoader(
                    path,
                    glob="**/*.pdf",
                    loader_cls=PDFLoader,
                    show_progress=True
                )
                pdf_docs = pdf_loader.load()
                documents.extend(pdf_docs)
                logger.info(f"Loaded {len(pdf_docs)} PDF files")
            except Exception as e:
                logger.warning(f"Failed to load PDF files: {e}")
        else:
            logger.info("PDF loader not available, skipping PDF files")
        
        # Load CSV files
        try:
            csv_loader = DirectoryLoader(
                path,
                glob="**/*.csv",
                loader_cls=CSVLoader,
                show_progress=True
            )
            csv_docs = csv_loader.load()
            documents.extend(csv_docs)
            logger.info(f"Loaded {len(csv_docs)} CSV files")
        except Exception as e:
            logger.warning(f"Failed to load CSV files: {e}")
        
        return documents
    
    async def _split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks."""
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Run in thread pool to avoid blocking
        chunks = await asyncio.to_thread(splitter.split_documents, documents)
        
        logger.info(f"Split {len(documents)} documents into {len(chunks)} chunks")
        return chunks
    
    async def _add_to_vectorstore(self, chunks: List[Document]) -> None:
        """Add document chunks to vector store."""
        
        if self.use_dev_mode:
            self.vectorstore.add_documents(chunks)
        else:
            # Add to Pinecone in batches to avoid rate limits
            batch_size = 100
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                await asyncio.to_thread(self.vectorstore.add_documents, batch)
                logger.info(f"Added batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1}")
    
    async def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: Search query
            top_k: Number of documents to retrieve
            
        Returns:
            List of relevant documents with text and metadata
        """
        
        try:
            if self.use_dev_mode:
                # Use mock retriever
                retriever = self.vectorstore.as_retriever(
                    search_kwargs={"k": top_k}
                )
                results = retriever.get_relevant_documents(query)
            else:
                # Use Pinecone retriever
                retriever = self.vectorstore.as_retriever(
                    search_kwargs={"k": top_k}
                )
                results = await asyncio.to_thread(
                    retriever.get_relevant_documents, 
                    query
                )
            
            # Format results
            formatted_results = []
            for doc in results:
                formatted_results.append({
                    "text": doc.page_content,
                    "metadata": doc.metadata,
                    "score": getattr(doc, "score", 0.0)  # Some retrievers provide scores
                })
            
            logger.info(f"Retrieved {len(formatted_results)} documents for query: {query[:50]}...")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Document retrieval failed: {e}")
            # Return empty results on error rather than failing
            return []
    
    async def search_by_topic(self, topic: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search documents by topic/category.
        
        Args:
            topic: Topic to search for
            top_k: Number of documents to retrieve
            
        Returns:
            List of relevant documents
        """
        
        # Enhance query with topic-specific terms
        enhanced_query = f"medical information about {topic} symptoms treatment diagnosis"
        return await self.retrieve(enhanced_query, top_k)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the RAG pipeline.
        
        Returns:
            Dictionary with pipeline statistics
        """
        
        stats = {
            "mode": "development" if self.use_dev_mode else "production",
            "pinecone_available": PINECONE_AVAILABLE,
            "index_name": PINECONE_INDEX if not self.use_dev_mode else "mock",
            "embedding_model": EMBEDDING_MODEL,
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP
        }
        
        if self.use_dev_mode:
            stats["document_count"] = len(self.vectorstore.documents)
        else:
            try:
                stats["index_stats"] = self.index.describe_index_stats()
            except Exception as e:
                stats["index_error"] = str(e)
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the RAG pipeline.
        
        Returns:
            Health check results
        """
        
        health = {
            "status": "healthy",
            "mode": "development" if self.use_dev_mode else "production",
            "timestamp": asyncio.get_event_loop().time()
        }
        
        try:
            # Test retrieval
            test_results = await self.retrieve("test query", top_k=1)
            health["retrieval_test"] = "passed" if test_results is not None else "failed"
            
            if not self.use_dev_mode and self.index:
                # Test Pinecone connection
                stats = self.index.describe_index_stats()
                health["pinecone_connection"] = "connected"
                health["vector_count"] = stats.get("total_vector_count", 0)
            
        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)
        
        return health
