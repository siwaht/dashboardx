"""
RAG (Retrieval-Augmented Generation) Module

Handles document ingestion, chunking, embedding generation, and retrieval
using LlamaIndex for optimized performance.
"""

from .ingestion import DocumentIngestionPipeline
from .chunking import ChunkingStrategy, RecursiveChunker, SemanticChunker
from .embeddings import EmbeddingGenerator
from .retrieval import VectorRetriever

__all__ = [
    "DocumentIngestionPipeline",
    "ChunkingStrategy",
    "RecursiveChunker",
    "SemanticChunker",
    "EmbeddingGenerator",
    "VectorRetriever",
]
