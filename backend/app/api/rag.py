"""
RAG API Endpoints

Provides REST API for document ingestion, querying, and management
using the LlamaIndex RAG pipeline with multi-tenant support.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

from app.security.auth import get_current_user
from app.rag.ingestion import DocumentIngestionPipeline
from app.rag.llama_index import get_llama_rag
from llama_index.core import Document

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Request/Response Models ====================

class QueryRequest(BaseModel):
    """Request model for RAG queries"""
    query: str = Field(..., description="User query text", min_length=1)
    top_k: int = Field(5, description="Number of results to return", ge=1, le=20)
    similarity_threshold: Optional[float] = Field(
        None, 
        description="Minimum similarity score (0-1)",
        ge=0.0,
        le=1.0
    )


class QueryResponse(BaseModel):
    """Response model for RAG queries"""
    answer: str = Field(..., description="Generated answer")
    sources: List[dict] = Field(..., description="Source documents with scores")
    query: str = Field(..., description="Original query")
    tenant_id: str = Field(..., description="Tenant ID")
    timestamp: str = Field(..., description="Query timestamp")


class IngestionResponse(BaseModel):
    """Response model for document ingestion"""
    status: str = Field(..., description="Ingestion status")
    document_id: str = Field(..., description="Document ID")
    filename: str = Field(..., description="Original filename")
    chunks_created: int = Field(..., description="Number of chunks created")
    processing_time_seconds: float = Field(..., description="Processing time")


class DocumentListResponse(BaseModel):
    """Response model for document listing"""
    documents: List[dict] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents")
    tenant_id: str = Field(..., description="Tenant ID")


class DeleteResponse(BaseModel):
    """Response model for document deletion"""
    status: str = Field(..., description="Deletion status")
    document_id: str = Field(..., description="Deleted document ID")
    chunks_deleted: int = Field(..., description="Number of chunks deleted")


class IndexStatsResponse(BaseModel):
    """Response model for index statistics"""
    tenant_id: str
    status: str
    embedding_model: str
    chunk_size: int
    timestamp: str


# ==================== API Endpoints ====================

@router.post("/ingest", response_model=IngestionResponse)
async def ingest_document(
    file: UploadFile = File(..., description="Document file to ingest"),
    metadata: Optional[str] = Form(None, description="Additional metadata as JSON string"),
    current_user: dict = Depends(get_current_user)
):
    """
    Ingest a document into the RAG system
    
    Supported formats: PDF, DOCX, TXT, MD, HTML
    
    The document will be:
    1. Processed and text extracted
    2. Chunked into segments
    3. Embedded using OpenAI
    4. Stored in vector database with tenant isolation
    """
    try:
        logger.info(f"Ingesting document: {file.filename} for tenant {current_user['tenant_id']}")
        
        # Parse metadata if provided
        import json
        parsed_metadata = {}
        if metadata:
            try:
                parsed_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid metadata JSON")
        
        # Initialize ingestion pipeline
        pipeline = DocumentIngestionPipeline()
        
        # Read file content
        content = await file.read()
        
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Process document
        result = await pipeline.ingest_document(
            file_content=content,
            filename=file.filename,
            tenant_id=current_user["tenant_id"],
            user_id=current_user["user_id"],
            metadata=parsed_metadata
        )
        
        logger.info(f"Document ingested successfully: {result['document_id']}")
        
        return IngestionResponse(
            status=result["status"],
            document_id=result["document_id"],
            filename=result["filename"],
            chunks_created=result["chunks_created"],
            processing_time_seconds=result["processing_time_seconds"]
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error ingesting document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/query", response_model=QueryResponse)
async def query_rag(
    request: QueryRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Query the RAG system
    
    The system will:
    1. Search for relevant documents using vector similarity
    2. Filter by tenant for data isolation
    3. Generate a response using retrieved context
    4. Return answer with source citations
    """
    try:
        logger.info(f"RAG query from tenant {current_user['tenant_id']}: {request.query}")
        
        # Get LlamaIndex RAG instance
        llama_rag = get_llama_rag()
        
        # Execute query
        result = await llama_rag.query(
            query_text=request.query,
            tenant_id=current_user["tenant_id"],
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold
        )
        
        logger.info(f"Query completed: {len(result['sources'])} sources retrieved")
        
        return QueryResponse(**result)
        
    except Exception as e:
        logger.error(f"Error querying RAG system: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """
    List all documents for the current tenant
    
    Returns paginated list of documents with metadata.
    """
    try:
        from supabase import create_client
        from app.config import settings
        
        supabase = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
        
        # Query documents with tenant filtering
        response = supabase.from_('documents').select(
            'id, title, file_type, file_size, status, uploaded_by, created_at, metadata'
        ).eq(
            'tenant_id', current_user['tenant_id']
        ).order(
            'created_at', desc=True
        ).range(
            skip, skip + limit - 1
        ).execute()
        
        # Get total count
        count_response = supabase.from_('documents').select(
            'id', count='exact'
        ).eq(
            'tenant_id', current_user['tenant_id']
        ).execute()
        
        total = count_response.count if hasattr(count_response, 'count') else len(response.data)
        
        return DocumentListResponse(
            documents=response.data or [],
            total=total,
            tenant_id=current_user['tenant_id']
        )
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get details of a specific document
    """
    try:
        from supabase import create_client
        from app.config import settings
        
        supabase = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
        
        # Query document with tenant filtering
        response = supabase.from_('documents').select('*').eq(
            'id', document_id
        ).eq(
            'tenant_id', current_user['tenant_id']
        ).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return response.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@router.delete("/documents/{document_id}", response_model=DeleteResponse)
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a document and all its chunks
    
    This will:
    1. Delete all vector embeddings
    2. Delete all chunks
    3. Delete the document record
    """
    try:
        logger.info(f"Deleting document {document_id} for tenant {current_user['tenant_id']}")
        
        # Initialize ingestion pipeline
        pipeline = DocumentIngestionPipeline()
        
        # Delete document
        result = await pipeline.delete_document(
            document_id=document_id,
            tenant_id=current_user["tenant_id"]
        )
        
        logger.info(f"Document deleted successfully: {document_id}")
        
        return DeleteResponse(
            status=result["status"],
            document_id=result["document_id"],
            chunks_deleted=result["chunks_deleted"]
        )
        
    except Exception as e:
        logger.error(f"Error deleting document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")


@router.get("/index/stats", response_model=IndexStatsResponse)
async def get_index_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    Get statistics about the RAG index for the current tenant
    """
    try:
        llama_rag = get_llama_rag()
        
        stats = await llama_rag.get_index_stats(
            tenant_id=current_user["tenant_id"]
        )
        
        return IndexStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting index stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.post("/index/refresh")
async def refresh_index(
    current_user: dict = Depends(get_current_user)
):
    """
    Refresh the vector index for the current tenant
    
    This can be used to rebuild the index if needed.
    """
    try:
        logger.info(f"Refreshing index for tenant {current_user['tenant_id']}")
        
        # This is a placeholder for index refresh logic
        # In production, you might want to:
        # 1. Re-index all documents
        # 2. Update embeddings
        # 3. Optimize the index
        
        return {
            "status": "success",
            "message": "Index refresh initiated",
            "tenant_id": current_user["tenant_id"]
        }
        
    except Exception as e:
        logger.error(f"Error refreshing index: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Refresh failed: {str(e)}")


# ==================== Health Check ====================

@router.get("/health")
async def rag_health_check():
    """
    Health check endpoint for RAG system
    """
    try:
        # Test LlamaIndex connection
        llama_rag = get_llama_rag()
        
        return {
            "status": "healthy",
            "service": "RAG Pipeline",
            "embedding_model": llama_rag.vector_store is not None,
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"RAG health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }
