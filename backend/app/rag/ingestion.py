"""
Document Ingestion Pipeline

Handles document upload, processing, chunking, embedding generation,
and storage in the vector database with full FGAC enforcement.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, BinaryIO
from pathlib import Path
from datetime import datetime
import hashlib

from supabase import create_client, Client

from app.config import settings
from app.rag.chunking import get_chunker, Chunk
from app.rag.embeddings import EmbeddingGenerator
from app.security.fgac import FGACEnforcer

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Processes different document types and extracts text
    
    Supported formats:
    - PDF
    - DOCX
    - TXT
    - MD (Markdown)
    - HTML
    """
    
    @staticmethod
    async def process_pdf(file_content: bytes) -> str:
        """Extract text from PDF"""
        try:
            from pypdf import PdfReader
            from io import BytesIO
            
            pdf = PdfReader(BytesIO(file_content))
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n\n"
            
            return text.strip()
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            raise
    
    @staticmethod
    async def process_docx(file_content: bytes) -> str:
        """Extract text from DOCX"""
        try:
            from docx import Document
            from io import BytesIO
            
            doc = Document(BytesIO(file_content))
            text = "\n\n".join([para.text for para in doc.paragraphs])
            
            return text.strip()
        except Exception as e:
            logger.error(f"Error processing DOCX: {e}")
            raise
    
    @staticmethod
    async def process_txt(file_content: bytes) -> str:
        """Extract text from TXT"""
        try:
            return file_content.decode('utf-8').strip()
        except UnicodeDecodeError:
            # Try other encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    return file_content.decode(encoding).strip()
                except:
                    continue
            raise ValueError("Unable to decode text file")
    
    @staticmethod
    async def process_markdown(file_content: bytes) -> str:
        """Extract text from Markdown"""
        try:
            import markdown
            from bs4 import BeautifulSoup
            
            md_text = file_content.decode('utf-8')
            html = markdown.markdown(md_text)
            soup = BeautifulSoup(html, 'html.parser')
            
            return soup.get_text().strip()
        except Exception as e:
            logger.error(f"Error processing Markdown: {e}")
            # Fallback to plain text
            return file_content.decode('utf-8').strip()
    
    @staticmethod
    async def process_html(file_content: bytes) -> str:
        """Extract text from HTML"""
        try:
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(file_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            return soup.get_text().strip()
        except Exception as e:
            logger.error(f"Error processing HTML: {e}")
            raise
    
    async def process_file(self, file_content: bytes, file_type: str) -> str:
        """
        Process file based on type
        
        Args:
            file_content: File content as bytes
            file_type: File extension (pdf, docx, txt, md, html)
            
        Returns:
            Extracted text
        """
        processors = {
            'pdf': self.process_pdf,
            'docx': self.process_docx,
            'doc': self.process_docx,
            'txt': self.process_txt,
            'md': self.process_markdown,
            'markdown': self.process_markdown,
            'html': self.process_html,
            'htm': self.process_html,
        }
        
        processor = processors.get(file_type.lower())
        if not processor:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        return await processor(file_content)


class DocumentIngestionPipeline:
    """
    Complete document ingestion pipeline
    
    Steps:
    1. Process document and extract text
    2. Chunk text into segments
    3. Generate embeddings
    4. Store in vector database with FGAC metadata
    """
    
    def __init__(self):
        self.supabase: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
        self.processor = DocumentProcessor()
        self.embedding_generator = EmbeddingGenerator()
        
        logger.info("Initialized DocumentIngestionPipeline")
    
    async def ingest_document(
        self,
        file_content: bytes,
        filename: str,
        tenant_id: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ingest a document through the complete pipeline
        
        Args:
            file_content: Document content as bytes
            filename: Original filename
            tenant_id: Tenant ID (MANDATORY for FGAC)
            user_id: User ID who uploaded the document
            metadata: Additional metadata
            
        Returns:
            Dictionary with ingestion results
        """
        start_time = datetime.utcnow()
        
        # Extract file type
        file_type = Path(filename).suffix.lstrip('.')
        
        logger.info(
            f"Starting ingestion for {filename} "
            f"(type: {file_type}, tenant: {tenant_id})"
        )
        
        try:
            # Step 1: Create document record
            document_id = await self._create_document_record(
                filename=filename,
                file_type=file_type,
                file_size=len(file_content),
                tenant_id=tenant_id,
                user_id=user_id,
                metadata=metadata or {}
            )
            
            # Step 2: Process document
            await self._update_document_status(document_id, 'processing')
            text = await self.processor.process_file(file_content, file_type)
            
            if not text.strip():
                raise ValueError("No text extracted from document")
            
            logger.info(f"Extracted {len(text)} characters from {filename}")
            
            # Step 3: Chunk text
            chunker = get_chunker(
                strategy=settings.chunking_strategy,
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap
            )
            
            chunk_metadata = {
                'tenant_id': tenant_id,
                'document_id': document_id,
                'filename': filename,
                'file_type': file_type,
                'uploaded_by': user_id,
                **(metadata or {})
            }
            
            chunks = chunker.chunk(text, chunk_metadata)
            logger.info(f"Created {len(chunks)} chunks")
            
            # Step 4: Generate embeddings
            chunk_dicts = [
                {
                    'content': chunk.content,
                    'chunk_index': chunk.chunk_index,
                    'metadata': chunk.metadata
                }
                for chunk in chunks
            ]
            
            from app.rag.embeddings import generate_embeddings_for_chunks
            chunks_with_embeddings = await generate_embeddings_for_chunks(
                chunk_dicts,
                self.embedding_generator
            )
            
            # Step 5: Store in vector database
            await self._store_chunks(
                chunks=chunks_with_embeddings,
                document_id=document_id,
                tenant_id=tenant_id
            )
            
            # Step 6: Update document status
            await self._update_document_status(document_id, 'completed')
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            result = {
                'document_id': document_id,
                'filename': filename,
                'status': 'completed',
                'chunks_created': len(chunks),
                'total_tokens': sum(c.get('token_count', 0) for c in chunks_with_embeddings),
                'processing_time_seconds': duration,
                'tenant_id': tenant_id
            }
            
            logger.info(
                f"Successfully ingested {filename}: "
                f"{len(chunks)} chunks in {duration:.2f}s"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error ingesting document {filename}: {e}")
            
            # Update document status to failed
            if 'document_id' in locals():
                await self._update_document_status(
                    document_id,
                    'failed',
                    error_message=str(e)
                )
            
            raise
    
    async def _create_document_record(
        self,
        filename: str,
        file_type: str,
        file_size: int,
        tenant_id: str,
        user_id: str,
        metadata: Dict[str, Any]
    ) -> str:
        """Create document record in database"""
        
        # CRITICAL: Inject tenant_id
        document_data = FGACEnforcer.inject_tenant_id(
            {
                'title': filename,
                'file_type': file_type,
                'file_size': file_size,
                'status': 'pending',
                'uploaded_by': user_id,
                'metadata': metadata
            },
            tenant_id=tenant_id
        )
        
        response = self.supabase.from_('documents').insert(
            document_data
        ).execute()
        
        if not response.data:
            raise ValueError("Failed to create document record")
        
        return response.data[0]['id']
    
    async def _update_document_status(
        self,
        document_id: str,
        status: str,
        error_message: Optional[str] = None
    ):
        """Update document processing status"""
        update_data = {'status': status}
        
        if error_message:
            update_data['metadata'] = {'error': error_message}
        
        self.supabase.from_('documents').update(
            update_data
        ).eq('id', document_id).execute()
    
    async def _store_chunks(
        self,
        chunks: List[Dict[str, Any]],
        document_id: str,
        tenant_id: str
    ):
        """Store chunks in vector database"""
        
        # Prepare chunk records
        chunk_records = []
        for chunk in chunks:
            # CRITICAL: Ensure tenant_id is present
            chunk_record = {
                'document_id': document_id,
                'tenant_id': tenant_id,
                'content': chunk['content'],
                'embedding': chunk['embedding'],
                'chunk_index': chunk['chunk_index'],
                'metadata': chunk['metadata']
            }
            
            # Verify FGAC
            FGACEnforcer.validate_metadata_has_tenant(
                chunk_record['metadata'],
                tenant_id,
                strict=True
            )
            
            chunk_records.append(chunk_record)
        
        # Batch insert
        batch_size = 100
        for i in range(0, len(chunk_records), batch_size):
            batch = chunk_records[i:i + batch_size]
            
            response = self.supabase.from_('document_chunks').insert(
                batch
            ).execute()
            
            if not response.data:
                raise ValueError(f"Failed to insert chunk batch {i // batch_size + 1}")
            
            logger.debug(f"Inserted batch {i // batch_size + 1} ({len(batch)} chunks)")
    
    async def delete_document(
        self,
        document_id: str,
        tenant_id: str
    ) -> Dict[str, Any]:
        """
        Delete document and all its chunks
        
        Args:
            document_id: Document ID
            tenant_id: Tenant ID (MANDATORY for FGAC)
            
        Returns:
            Deletion result
        """
        # CRITICAL: Verify tenant access
        FGACEnforcer.validate_tenant_access(tenant_id, tenant_id, "document")
        
        try:
            # Delete chunks
            chunks_response = self.supabase.from_('document_chunks').delete().eq(
                'document_id', document_id
            ).eq(
                'tenant_id', tenant_id
            ).execute()
            
            chunks_deleted = len(chunks_response.data) if chunks_response.data else 0
            
            # Delete document
            doc_response = self.supabase.from_('documents').delete().eq(
                'id', document_id
            ).eq(
                'tenant_id', tenant_id
            ).execute()
            
            logger.info(
                f"Deleted document {document_id} and {chunks_deleted} chunks "
                f"for tenant {tenant_id}"
            )
            
            return {
                'document_id': document_id,
                'chunks_deleted': chunks_deleted,
                'status': 'deleted'
            }
            
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            raise
