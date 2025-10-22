"""
Document Chunking Strategies

Implements various chunking strategies for splitting documents into
semantically meaningful segments optimized for RAG retrieval.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """Represents a document chunk with metadata"""
    content: str
    chunk_index: int
    metadata: Dict[str, Any]
    token_count: Optional[int] = None


class ChunkingStrategy(ABC):
    """Abstract base class for chunking strategies"""
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    @abstractmethod
    def chunk(self, text: str, metadata: Dict[str, Any]) -> List[Chunk]:
        """
        Split text into chunks
        
        Args:
            text: Text to chunk
            metadata: Metadata to attach to each chunk
            
        Returns:
            List of Chunk objects
        """
        pass
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count (rough approximation: 1 token ≈ 4 characters)
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        return len(text) // 4


class RecursiveChunker(ChunkingStrategy):
    """
    Recursive text splitter that tries to split on semantic boundaries
    
    Attempts to split on:
    1. Double newlines (paragraphs)
    2. Single newlines (sentences)
    3. Periods (sentence endings)
    4. Spaces (words)
    5. Characters (last resort)
    """
    
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        separators: Optional[List[str]] = None
    ):
        super().__init__(chunk_size, chunk_overlap)
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]
    
    def chunk(self, text: str, metadata: Dict[str, Any]) -> List[Chunk]:
        """Split text recursively using hierarchical separators"""
        chunks = []
        current_chunks = [text]
        
        for separator in self.separators:
            new_chunks = []
            
            for chunk_text in current_chunks:
                if self._estimate_tokens(chunk_text) <= self.chunk_size:
                    new_chunks.append(chunk_text)
                else:
                    # Split by current separator
                    split_chunks = self._split_by_separator(chunk_text, separator)
                    new_chunks.extend(split_chunks)
            
            current_chunks = new_chunks
            
            # Check if all chunks are small enough
            if all(self._estimate_tokens(c) <= self.chunk_size for c in current_chunks):
                break
        
        # Create Chunk objects with overlap
        for i, chunk_text in enumerate(current_chunks):
            if not chunk_text.strip():
                continue
            
            # Add overlap from previous chunk
            if i > 0 and self.chunk_overlap > 0:
                prev_chunk = current_chunks[i - 1]
                overlap_text = prev_chunk[-self.chunk_overlap * 4:]  # Approximate characters
                chunk_text = overlap_text + chunk_text
            
            chunks.append(Chunk(
                content=chunk_text.strip(),
                chunk_index=i,
                metadata={**metadata, "chunking_strategy": "recursive"},
                token_count=self._estimate_tokens(chunk_text)
            ))
        
        logger.info(f"Created {len(chunks)} chunks using recursive strategy")
        return chunks
    
    def _split_by_separator(self, text: str, separator: str) -> List[str]:
        """Split text by separator"""
        if separator == "":
            # Character-level split as last resort
            return [text[i:i + self.chunk_size * 4] 
                    for i in range(0, len(text), self.chunk_size * 4)]
        
        return text.split(separator)


class SemanticChunker(ChunkingStrategy):
    """
    Semantic chunker that uses sentence boundaries and semantic similarity
    
    This is a simplified version. In production, you might use:
    - Sentence transformers for semantic similarity
    - LLM-based chunking for better context preservation
    """
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        super().__init__(chunk_size, chunk_overlap)
    
    def chunk(self, text: str, metadata: Dict[str, Any]) -> List[Chunk]:
        """Split text into semantic chunks based on sentences"""
        # Split into sentences
        sentences = self._split_into_sentences(text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_tokens = self._estimate_tokens(sentence)
            
            if current_size + sentence_tokens > self.chunk_size and current_chunk:
                # Create chunk from accumulated sentences
                chunk_text = " ".join(current_chunk)
                chunks.append(Chunk(
                    content=chunk_text,
                    chunk_index=len(chunks),
                    metadata={**metadata, "chunking_strategy": "semantic"},
                    token_count=current_size
                ))
                
                # Start new chunk with overlap
                if self.chunk_overlap > 0:
                    overlap_sentences = self._get_overlap_sentences(
                        current_chunk, self.chunk_overlap
                    )
                    current_chunk = overlap_sentences
                    current_size = sum(self._estimate_tokens(s) for s in overlap_sentences)
                else:
                    current_chunk = []
                    current_size = 0
            
            current_chunk.append(sentence)
            current_size += sentence_tokens
        
        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(Chunk(
                content=chunk_text,
                chunk_index=len(chunks),
                metadata={**metadata, "chunking_strategy": "semantic"},
                token_count=current_size
            ))
        
        logger.info(f"Created {len(chunks)} chunks using semantic strategy")
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences
        
        This is a simple implementation. For production, consider using:
        - spaCy sentence segmentation
        - NLTK sentence tokenizer
        """
        import re
        
        # Simple sentence splitting on common punctuation
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _get_overlap_sentences(self, sentences: List[str], overlap_tokens: int) -> List[str]:
        """Get last N sentences that fit within overlap token limit"""
        overlap_sentences = []
        current_tokens = 0
        
        for sentence in reversed(sentences):
            sentence_tokens = self._estimate_tokens(sentence)
            if current_tokens + sentence_tokens > overlap_tokens:
                break
            overlap_sentences.insert(0, sentence)
            current_tokens += sentence_tokens
        
        return overlap_sentences


class FixedSizeChunker(ChunkingStrategy):
    """
    Simple fixed-size chunker that splits text into equal-sized chunks
    
    Useful for:
    - Uniform chunk sizes
    - Simple benchmarking
    - When semantic boundaries are not important
    """
    
    def chunk(self, text: str, metadata: Dict[str, Any]) -> List[Chunk]:
        """Split text into fixed-size chunks"""
        chunks = []
        chunk_size_chars = self.chunk_size * 4  # Approximate characters
        overlap_chars = self.chunk_overlap * 4
        
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + chunk_size_chars
            chunk_text = text[start:end]
            
            if chunk_text.strip():
                chunks.append(Chunk(
                    content=chunk_text.strip(),
                    chunk_index=chunk_index,
                    metadata={**metadata, "chunking_strategy": "fixed"},
                    token_count=self._estimate_tokens(chunk_text)
                ))
                chunk_index += 1
            
            start = end - overlap_chars
        
        logger.info(f"Created {len(chunks)} chunks using fixed-size strategy")
        return chunks


def get_chunker(strategy: str, chunk_size: int = 512, chunk_overlap: int = 50) -> ChunkingStrategy:
    """
    Factory function to get chunking strategy
    
    Args:
        strategy: Strategy name ('recursive', 'semantic', 'fixed')
        chunk_size: Target chunk size in tokens
        chunk_overlap: Overlap size in tokens
        
    Returns:
        ChunkingStrategy instance
    """
    strategies = {
        "recursive": RecursiveChunker,
        "semantic": SemanticChunker,
        "fixed": FixedSizeChunker,
    }
    
    chunker_class = strategies.get(strategy.lower())
    if not chunker_class:
        logger.warning(f"Unknown strategy '{strategy}', defaulting to recursive")
        chunker_class = RecursiveChunker
    
    return chunker_class(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
