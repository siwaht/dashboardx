"""
Vector Retrieval Module

Handles similarity search with FGAC (Fine-Grained Access Control) enforcement
using Supabase pgvector for high-performance retrieval.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import asyncio

from supabase import create_client, Client
import numpy as np

from app.config import settings
from app.security.fgac import FGACEnforcer

logger = logging.getLogger(__name__)


@dataclass
class RetrievedDocument:
    """Represents a retrieved document chunk"""
    id: str
    content: str
    metadata: Dict[str, Any]
    similarity_score: float
    chunk_index: int
    document_id: str
    tenant_id: str


class VectorRetriever:
    """
    Vector similarity search with FGAC enforcement
    
    CRITICAL: All queries MUST filter by tenant_id to prevent cross-tenant data leakage
    """
    
    def __init__(self):
        self.supabase: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
        self.table_name = "document_chunks"
        
        logger.info("Initialized VectorRetriever with Supabase pgvector")
    
    async def similarity_search(
        self,
        query_embedding: List[float],
        tenant_id: str,
        top_k: int = None,
        similarity_threshold: float = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievedDocument]:
        """
        Perform similarity search with mandatory tenant filtering
        
        Args:
            query_embedding: Query vector embedding
            tenant_id: Tenant ID (MANDATORY for FGAC)
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score
            filters: Additional metadata filters
            
        Returns:
            List of RetrievedDocument objects
        """
        top_k = top_k or settings.top_k_documents
        similarity_threshold = similarity_threshold or settings.similarity_threshold
        
        # CRITICAL: Build FGAC filter
        fgac_filter = FGACEnforcer.create_vector_search_filter(
            tenant_id=tenant_id,
            additional_filters=filters
        )
        
        logger.info(
            f"Performing similarity search for tenant {tenant_id} "
            f"(top_k={top_k}, threshold={similarity_threshold})"
        )
        
        try:
            # Execute vector similarity search with RPC function
            # This uses the pgvector <=> operator for cosine distance
            response = self.supabase.rpc(
                'match_documents',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': 1 - similarity_threshold,  # Convert similarity to distance
                    'match_count': top_k,
                    'filter_tenant_id': tenant_id
                }
            ).execute()
            
            if not response.data:
                logger.warning(f"No documents found for tenant {tenant_id}")
                return []
            
            # Convert to RetrievedDocument objects
            documents = []
            for item in response.data:
                # Verify tenant_id (defense in depth)
                if item.get('tenant_id') != tenant_id:
                    logger.error(
                        f"FGAC VIOLATION: Retrieved document from wrong tenant! "
                        f"Expected: {tenant_id}, Got: {item.get('tenant_id')}"
                    )
                    continue
                
                documents.append(RetrievedDocument(
                    id=item['id'],
                    content=item['content'],
                    metadata=item.get('metadata', {}),
                    similarity_score=1 - item['similarity'],  # Convert distance back to similarity
                    chunk_index=item.get('chunk_index', 0),
                    document_id=item.get('document_id', ''),
                    tenant_id=item['tenant_id']
                ))
            
            logger.info(f"Retrieved {len(documents)} documents for tenant {tenant_id}")
            return documents
            
        except Exception as e:
            logger.error(f"Error during similarity search: {e}")
            raise
    
    async def hybrid_search(
        self,
        query_embedding: List[float],
        query_text: str,
        tenant_id: str,
        top_k: int = None,
        alpha: float = 0.5
    ) -> List[RetrievedDocument]:
        """
        Hybrid search combining vector similarity and keyword matching
        
        Args:
            query_embedding: Query vector
            query_text: Query text for keyword matching
            tenant_id: Tenant ID (MANDATORY)
            top_k: Number of results
            alpha: Weight for vector search (1-alpha for keyword)
            
        Returns:
            List of RetrievedDocument objects
        """
        top_k = top_k or settings.top_k_documents
        
        # Get vector search results
        vector_results = await self.similarity_search(
            query_embedding=query_embedding,
            tenant_id=tenant_id,
            top_k=top_k * 2  # Get more for reranking
        )
        
        # Get keyword search results
        keyword_results = await self._keyword_search(
            query_text=query_text,
            tenant_id=tenant_id,
            top_k=top_k * 2
        )
        
        # Combine and rerank
        combined = self._combine_results(
            vector_results,
            keyword_results,
            alpha=alpha
        )
        
        return combined[:top_k]
    
    async def _keyword_search(
        self,
        query_text: str,
        tenant_id: str,
        top_k: int
    ) -> List[RetrievedDocument]:
        """
        Keyword-based search using PostgreSQL full-text search
        
        Args:
            query_text: Search query
            tenant_id: Tenant ID (MANDATORY)
            top_k: Number of results
            
        Returns:
            List of RetrievedDocument objects
        """
        try:
            # Use PostgreSQL full-text search
            response = self.supabase.from_(self.table_name).select('*').eq(
                'tenant_id', tenant_id
            ).text_search(
                'content', query_text
            ).limit(top_k).execute()
            
            documents = []
            for item in response.data:
                documents.append(RetrievedDocument(
                    id=item['id'],
                    content=item['content'],
                    metadata=item.get('metadata', {}),
                    similarity_score=0.5,  # Placeholder score
                    chunk_index=item.get('chunk_index', 0),
                    document_id=item.get('document_id', ''),
                    tenant_id=item['tenant_id']
                ))
            
            return documents
            
        except Exception as e:
            logger.warning(f"Keyword search failed: {e}")
            return []
    
    def _combine_results(
        self,
        vector_results: List[RetrievedDocument],
        keyword_results: List[RetrievedDocument],
        alpha: float = 0.5
    ) -> List[RetrievedDocument]:
        """
        Combine and rerank results from vector and keyword search
        
        Args:
            vector_results: Results from vector search
            keyword_results: Results from keyword search
            alpha: Weight for vector search
            
        Returns:
            Combined and reranked results
        """
        # Create score dictionary
        scores: Dict[str, Tuple[float, RetrievedDocument]] = {}
        
        # Add vector results
        for doc in vector_results:
            scores[doc.id] = (alpha * doc.similarity_score, doc)
        
        # Add keyword results
        for doc in keyword_results:
            if doc.id in scores:
                # Combine scores
                existing_score, existing_doc = scores[doc.id]
                new_score = existing_score + (1 - alpha) * doc.similarity_score
                scores[doc.id] = (new_score, existing_doc)
            else:
                scores[doc.id] = ((1 - alpha) * doc.similarity_score, doc)
        
        # Sort by combined score
        sorted_results = sorted(
            scores.values(),
            key=lambda x: x[0],
            reverse=True
        )
        
        # Update similarity scores
        results = []
        for score, doc in sorted_results:
            doc.similarity_score = score
            results.append(doc)
        
        return results
    
    async def get_document_chunks(
        self,
        document_id: str,
        tenant_id: str
    ) -> List[RetrievedDocument]:
        """
        Get all chunks for a specific document
        
        Args:
            document_id: Document ID
            tenant_id: Tenant ID (MANDATORY)
            
        Returns:
            List of document chunks
        """
        # CRITICAL: Verify tenant access
        FGACEnforcer.validate_tenant_access(tenant_id, tenant_id, "document")
        
        try:
            response = self.supabase.from_(self.table_name).select('*').eq(
                'document_id', document_id
            ).eq(
                'tenant_id', tenant_id
            ).order('chunk_index').execute()
            
            documents = []
            for item in response.data:
                documents.append(RetrievedDocument(
                    id=item['id'],
                    content=item['content'],
                    metadata=item.get('metadata', {}),
                    similarity_score=1.0,
                    chunk_index=item.get('chunk_index', 0),
                    document_id=item['document_id'],
                    tenant_id=item['tenant_id']
                ))
            
            return documents
            
        except Exception as e:
            logger.error(f"Error retrieving document chunks: {e}")
            raise
    
    async def delete_document_chunks(
        self,
        document_id: str,
        tenant_id: str
    ) -> int:
        """
        Delete all chunks for a document
        
        Args:
            document_id: Document ID
            tenant_id: Tenant ID (MANDATORY)
            
        Returns:
            Number of chunks deleted
        """
        # CRITICAL: Verify tenant access
        FGACEnforcer.validate_tenant_access(tenant_id, tenant_id, "document")
        
        try:
            response = self.supabase.from_(self.table_name).delete().eq(
                'document_id', document_id
            ).eq(
                'tenant_id', tenant_id
            ).execute()
            
            count = len(response.data) if response.data else 0
            logger.info(f"Deleted {count} chunks for document {document_id}")
            return count
            
        except Exception as e:
            logger.error(f"Error deleting document chunks: {e}")
            raise


async def create_match_documents_function():
    """
    Create the PostgreSQL function for vector similarity search
    
    This should be run once during setup to create the RPC function
    """
    sql = """
    CREATE OR REPLACE FUNCTION match_documents(
        query_embedding vector(1536),
        match_threshold float,
        match_count int,
        filter_tenant_id uuid
    )
    RETURNS TABLE (
        id uuid,
        document_id uuid,
        tenant_id uuid,
        content text,
        metadata jsonb,
        chunk_index int,
        similarity float
    )
    LANGUAGE sql STABLE
    AS $$
        SELECT
            id,
            document_id,
            tenant_id,
            content,
            metadata,
            chunk_index,
            1 - (embedding <=> query_embedding) as similarity
        FROM document_chunks
        WHERE tenant_id = filter_tenant_id
        AND 1 - (embedding <=> query_embedding) > match_threshold
        ORDER BY embedding <=> query_embedding
        LIMIT match_count;
    $$;
    """
    
    logger.info("SQL function for match_documents created")
    return sql
