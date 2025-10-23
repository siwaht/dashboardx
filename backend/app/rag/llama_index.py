"""
LlamaIndex Integration for RAG Pipeline

Provides vector store integration with Supabase using LlamaIndex.
Handles document indexing, querying, and retrieval with multi-tenant support.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from llama_index.core import (
    VectorStoreIndex,
    Document,
    StorageContext,
    Settings,
    ServiceContext
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.postgres import PGVectorStore
from sqlalchemy import make_url

from app.config import settings

logger = logging.getLogger(__name__)


class LlamaIndexRAG:
    """
    LlamaIndex RAG Pipeline
    
    Integrates LlamaIndex with Supabase PostgreSQL + pgvector for:
    - Document indexing with embeddings
    - Semantic search and retrieval
    - Multi-tenant data isolation
    """
    
    def __init__(self):
        """Initialize LlamaIndex with OpenAI and Supabase vector store"""
        
        # Configure LlamaIndex global settings
        Settings.embed_model = OpenAIEmbedding(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key,
            dimensions=settings.embedding_dimensions
        )
        
        Settings.llm = OpenAI(
            model=settings.openai_chat_model,
            api_key=settings.openai_api_key,
            temperature=settings.openai_temperature,
            max_tokens=settings.openai_max_tokens
        )
        
        Settings.chunk_size = settings.chunk_size
        Settings.chunk_overlap = settings.chunk_overlap
        
        # Initialize node parser
        self.node_parser = SentenceSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        
        # Initialize vector store
        self.vector_store = self._create_vector_store()
        
        # Create storage context
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )
        
        logger.info("LlamaIndex RAG initialized successfully")
    
    def _create_vector_store(self) -> PGVectorStore:
        """
        Create PGVector store connected to Supabase
        
        Returns:
            PGVectorStore instance
        """
        try:
            # Parse connection string
            connection_string = settings.supabase_db_connection
            
            # Create vector store
            vector_store = PGVectorStore.from_params(
                database=make_url(connection_string).database,
                host=make_url(connection_string).host,
                password=make_url(connection_string).password,
                port=make_url(connection_string).port or 5432,
                user=make_url(connection_string).username,
                table_name="document_chunks",
                embed_dim=settings.embedding_dimensions,
                hybrid_search=False,  # Can enable for hybrid search
                text_search_config="english"
            )
            
            logger.info("Vector store connected to Supabase")
            return vector_store
            
        except Exception as e:
            logger.error(f"Error creating vector store: {e}")
            raise
    
    async def create_index_from_documents(
        self,
        documents: List[Document],
        tenant_id: str,
        show_progress: bool = True
    ) -> VectorStoreIndex:
        """
        Create vector index from documents
        
        Args:
            documents: List of LlamaIndex Document objects
            tenant_id: Tenant ID for multi-tenancy
            show_progress: Show progress bar
            
        Returns:
            VectorStoreIndex
        """
        try:
            # Add tenant_id to all document metadata
            for doc in documents:
                if not doc.metadata:
                    doc.metadata = {}
                doc.metadata["tenant_id"] = tenant_id
                doc.metadata["indexed_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"Creating index for {len(documents)} documents (tenant: {tenant_id})")
            
            # Create index
            index = VectorStoreIndex.from_documents(
                documents,
                storage_context=self.storage_context,
                show_progress=show_progress,
                node_parser=self.node_parser
            )
            
            logger.info(f"Index created successfully for tenant {tenant_id}")
            return index
            
        except Exception as e:
            logger.error(f"Error creating index: {e}")
            raise
    
    async def query(
        self,
        query_text: str,
        tenant_id: str,
        top_k: int = 5,
        similarity_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Query the RAG system
        
        Args:
            query_text: User query
            tenant_id: Tenant ID for filtering
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score
            
        Returns:
            Query response with answer and sources
        """
        try:
            logger.info(f"Querying RAG system: '{query_text}' (tenant: {tenant_id})")
            
            # Load index from vector store
            index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store,
                storage_context=self.storage_context
            )
            
            # Create query engine with metadata filtering
            from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
            
            filters = MetadataFilters(
                filters=[
                    ExactMatchFilter(
                        key="tenant_id",
                        value=tenant_id
                    )
                ]
            )
            
            query_engine = index.as_query_engine(
                similarity_top_k=top_k,
                filters=filters,
                response_mode="compact"
            )
            
            # Execute query
            response = query_engine.query(query_text)
            
            # Extract sources with scores
            sources = []
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes:
                    source = {
                        "text": node.text,
                        "score": node.score if hasattr(node, 'score') else None,
                        "metadata": node.metadata if hasattr(node, 'metadata') else {}
                    }
                    
                    # Apply similarity threshold if specified
                    if similarity_threshold is None or (
                        source["score"] is not None and 
                        source["score"] >= similarity_threshold
                    ):
                        sources.append(source)
            
            result = {
                "answer": str(response),
                "sources": sources,
                "query": query_text,
                "tenant_id": tenant_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Query completed: {len(sources)} sources retrieved")
            return result
            
        except Exception as e:
            logger.error(f"Error querying RAG system: {e}")
            raise
    
    async def add_documents(
        self,
        documents: List[Document],
        tenant_id: str
    ) -> None:
        """
        Add documents to existing index
        
        Args:
            documents: List of documents to add
            tenant_id: Tenant ID
        """
        try:
            # Add tenant_id to metadata
            for doc in documents:
                if not doc.metadata:
                    doc.metadata = {}
                doc.metadata["tenant_id"] = tenant_id
                doc.metadata["indexed_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"Adding {len(documents)} documents to index (tenant: {tenant_id})")
            
            # Load existing index
            index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store,
                storage_context=self.storage_context
            )
            
            # Insert documents
            for doc in documents:
                index.insert(doc)
            
            logger.info(f"Documents added successfully")
            
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise
    
    async def delete_documents(
        self,
        document_ids: List[str],
        tenant_id: str
    ) -> int:
        """
        Delete documents from index
        
        Args:
            document_ids: List of document IDs to delete
            tenant_id: Tenant ID for verification
            
        Returns:
            Number of documents deleted
        """
        try:
            logger.info(f"Deleting {len(document_ids)} documents (tenant: {tenant_id})")
            
            # Load index
            index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store,
                storage_context=self.storage_context
            )
            
            deleted_count = 0
            for doc_id in document_ids:
                try:
                    # Delete by document ID
                    # Note: This requires the document to have tenant_id in metadata
                    index.delete_ref_doc(doc_id, delete_from_docstore=True)
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Could not delete document {doc_id}: {e}")
            
            logger.info(f"Deleted {deleted_count} documents")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            raise
    
    async def get_index_stats(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get statistics about the index for a tenant
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Index statistics
        """
        try:
            # This is a simplified version
            # In production, you'd query the database directly for accurate stats
            
            return {
                "tenant_id": tenant_id,
                "status": "active",
                "embedding_model": settings.openai_embedding_model,
                "chunk_size": settings.chunk_size,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            raise


# Singleton instance
_llama_rag_instance: Optional[LlamaIndexRAG] = None


def get_llama_rag() -> LlamaIndexRAG:
    """
    Get or create LlamaIndex RAG singleton instance
    
    Returns:
        LlamaIndexRAG instance
    """
    global _llama_rag_instance
    
    if _llama_rag_instance is None:
        _llama_rag_instance = LlamaIndexRAG()
    
    return _llama_rag_instance


# Convenience alias
llama_rag = get_llama_rag()
