"""
Hybrid Retrieval System

Combines multiple retrieval strategies for optimal results:
- Dense retrieval (vector similarity)
- Sparse retrieval (BM25)
- Semantic search
- Re-ranking with cross-encoders
- Query expansion and reformulation
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder

from llama_index.core import Document
from llama_index.core.schema import NodeWithScore

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Hybrid Retrieval System
    
    Combines dense (vector) and sparse (BM25) retrieval methods
    with intelligent fusion and re-ranking.
    """
    
    def __init__(
        self,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        use_gpu: bool = False
    ):
        """
        Initialize hybrid retriever
        
        Args:
            embedding_model: Sentence transformer model for embeddings
            reranker_model: Cross-encoder model for re-ranking
            use_gpu: Use GPU if available
        """
        self.device = "cuda" if use_gpu else "cpu"
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model, device=self.device)
        
        # Initialize re-ranker
        self.reranker = CrossEncoder(reranker_model, device=self.device)
        
        # BM25 index (will be built per query)
        self.bm25_index = None
        self.documents = []
        
        # Cache for embeddings
        self.embedding_cache: Dict[str, np.ndarray] = {}
        
        logger.info(f"HybridRetriever initialized (device: {self.device})")
    
    def build_bm25_index(self, documents: List[str]) -> None:
        """
        Build BM25 index from documents
        
        Args:
            documents: List of document texts
        """
        try:
            # Tokenize documents
            tokenized_docs = [doc.lower().split() for doc in documents]
            
            # Build BM25 index
            self.bm25_index = BM25Okapi(tokenized_docs)
            self.documents = documents
            
            logger.info(f"BM25 index built with {len(documents)} documents")
            
        except Exception as e:
            logger.error(f"Error building BM25 index: {e}")
            raise
    
    async def retrieve_sparse(
        self,
        query: str,
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Sparse retrieval using BM25
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of (document, score) tuples
        """
        try:
            if self.bm25_index is None:
                logger.warning("BM25 index not built")
                return []
            
            # Tokenize query
            tokenized_query = query.lower().split()
            
            # Get BM25 scores
            scores = self.bm25_index.get_scores(tokenized_query)
            
            # Get top-k indices
            top_indices = np.argsort(scores)[::-1][:top_k]
            
            # Return documents with scores
            results = [
                (self.documents[idx], float(scores[idx]))
                for idx in top_indices
                if scores[idx] > 0
            ]
            
            logger.info(f"BM25 retrieval: {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error in sparse retrieval: {e}")
            return []
    
    async def retrieve_dense(
        self,
        query: str,
        documents: List[str],
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Dense retrieval using embeddings
        
        Args:
            query: Search query
            documents: List of documents
            top_k: Number of results to return
            
        Returns:
            List of (document, score) tuples
        """
        try:
            # Encode query
            query_embedding = self.embedding_model.encode(
                query,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            
            # Encode documents (with caching)
            doc_embeddings = []
            for doc in documents:
                if doc in self.embedding_cache:
                    doc_embeddings.append(self.embedding_cache[doc])
                else:
                    emb = self.embedding_model.encode(
                        doc,
                        convert_to_numpy=True,
                        show_progress_bar=False
                    )
                    self.embedding_cache[doc] = emb
                    doc_embeddings.append(emb)
            
            doc_embeddings = np.array(doc_embeddings)
            
            # Compute cosine similarity
            similarities = np.dot(doc_embeddings, query_embedding) / (
                np.linalg.norm(doc_embeddings, axis=1) * np.linalg.norm(query_embedding)
            )
            
            # Get top-k indices
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            # Return documents with scores
            results = [
                (documents[idx], float(similarities[idx]))
                for idx in top_indices
            ]
            
            logger.info(f"Dense retrieval: {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error in dense retrieval: {e}")
            return []
    
    async def hybrid_retrieve(
        self,
        query: str,
        documents: List[str],
        top_k: int = 10,
        alpha: float = 0.5,
        rerank: bool = True
    ) -> List[Tuple[str, float]]:
        """
        Hybrid retrieval combining sparse and dense methods
        
        Args:
            query: Search query
            documents: List of documents
            top_k: Number of results to return
            alpha: Weight for dense retrieval (1-alpha for sparse)
            rerank: Apply re-ranking
            
        Returns:
            List of (document, score) tuples
        """
        try:
            # Build BM25 index if needed
            if self.bm25_index is None or self.documents != documents:
                self.build_bm25_index(documents)
            
            # Retrieve using both methods
            sparse_results = await self.retrieve_sparse(query, top_k * 2)
            dense_results = await self.retrieve_dense(query, documents, top_k * 2)
            
            # Combine results using reciprocal rank fusion
            combined_scores = self._reciprocal_rank_fusion(
                sparse_results,
                dense_results,
                alpha=alpha
            )
            
            # Sort by combined score
            sorted_results = sorted(
                combined_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:top_k * 2]
            
            # Re-rank if requested
            if rerank and len(sorted_results) > 0:
                reranked_results = await self.rerank_results(
                    query,
                    [doc for doc, _ in sorted_results],
                    top_k
                )
                return reranked_results
            
            return sorted_results[:top_k]
            
        except Exception as e:
            logger.error(f"Error in hybrid retrieval: {e}")
            return []
    
    def _reciprocal_rank_fusion(
        self,
        sparse_results: List[Tuple[str, float]],
        dense_results: List[Tuple[str, float]],
        alpha: float = 0.5,
        k: int = 60
    ) -> Dict[str, float]:
        """
        Combine results using reciprocal rank fusion
        
        Args:
            sparse_results: Results from sparse retrieval
            dense_results: Results from dense retrieval
            alpha: Weight for dense retrieval
            k: Constant for RRF formula
            
        Returns:
            Dictionary of document to combined score
        """
        combined_scores = {}
        
        # Add sparse results
        for rank, (doc, score) in enumerate(sparse_results):
            rrf_score = (1 - alpha) / (k + rank + 1)
            combined_scores[doc] = combined_scores.get(doc, 0) + rrf_score
        
        # Add dense results
        for rank, (doc, score) in enumerate(dense_results):
            rrf_score = alpha / (k + rank + 1)
            combined_scores[doc] = combined_scores.get(doc, 0) + rrf_score
        
        return combined_scores
    
    async def rerank_results(
        self,
        query: str,
        documents: List[str],
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Re-rank results using cross-encoder
        
        Args:
            query: Search query
            documents: List of documents to re-rank
            top_k: Number of results to return
            
        Returns:
            Re-ranked list of (document, score) tuples
        """
        try:
            if len(documents) == 0:
                return []
            
            # Create query-document pairs
            pairs = [[query, doc] for doc in documents]
            
            # Get cross-encoder scores
            scores = self.reranker.predict(pairs)
            
            # Sort by score
            doc_scores = list(zip(documents, scores))
            doc_scores.sort(key=lambda x: x[1], reverse=True)
            
            logger.info(f"Re-ranked {len(documents)} documents")
            return doc_scores[:top_k]
            
        except Exception as e:
            logger.error(f"Error in re-ranking: {e}")
            return [(doc, 0.0) for doc in documents[:top_k]]
    
    async def expand_query(
        self,
        query: str,
        method: str = "synonyms"
    ) -> List[str]:
        """
        Expand query with related terms
        
        Args:
            query: Original query
            method: Expansion method (synonyms, embeddings, llm)
            
        Returns:
            List of expanded queries
        """
        try:
            expanded_queries = [query]
            
            if method == "synonyms":
                # Simple synonym expansion (placeholder)
                # In production, use WordNet or similar
                pass
            
            elif method == "embeddings":
                # Find similar queries using embeddings
                # This requires a query corpus
                pass
            
            elif method == "llm":
                # Use LLM to generate query variations
                # This requires LLM integration
                pass
            
            return expanded_queries
            
        except Exception as e:
            logger.error(f"Error expanding query: {e}")
            return [query]
    
    async def contextual_compression(
        self,
        query: str,
        documents: List[str],
        max_length: int = 500
    ) -> List[str]:
        """
        Compress documents to most relevant parts
        
        Args:
            query: Search query
            documents: List of documents
            max_length: Maximum length per document
            
        Returns:
            Compressed documents
        """
        try:
            compressed = []
            
            for doc in documents:
                if len(doc) <= max_length:
                    compressed.append(doc)
                else:
                    # Split into sentences
                    sentences = doc.split('. ')
                    
                    # Score sentences by relevance to query
                    sentence_scores = []
                    for sent in sentences:
                        # Simple word overlap score
                        query_words = set(query.lower().split())
                        sent_words = set(sent.lower().split())
                        overlap = len(query_words & sent_words)
                        sentence_scores.append((sent, overlap))
                    
                    # Sort by score and take top sentences
                    sentence_scores.sort(key=lambda x: x[1], reverse=True)
                    
                    # Reconstruct document
                    compressed_doc = '. '.join([
                        sent for sent, _ in sentence_scores
                    ])[:max_length]
                    
                    compressed.append(compressed_doc)
            
            return compressed
            
        except Exception as e:
            logger.error(f"Error in contextual compression: {e}")
            return documents
    
    def clear_cache(self) -> None:
        """Clear embedding cache"""
        self.embedding_cache.clear()
        logger.info("Embedding cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_size": len(self.embedding_cache),
            "bm25_indexed_docs": len(self.documents) if self.documents else 0
        }


class QueryOptimizer:
    """
    Query Optimization and Understanding
    
    Analyzes and optimizes queries for better retrieval.
    """
    
    def __init__(self):
        self.query_history: List[Dict[str, Any]] = []
    
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze query characteristics
        
        Args:
            query: User query
            
        Returns:
            Query analysis
        """
        try:
            analysis = {
                "original_query": query,
                "length": len(query.split()),
                "has_question_mark": "?" in query,
                "is_short": len(query.split()) < 5,
                "is_long": len(query.split()) > 20,
                "keywords": self._extract_keywords(query),
                "intent": self._classify_intent(query)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing query: {e}")
            return {"original_query": query, "error": str(e)}
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from query"""
        # Simple keyword extraction (remove stop words)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        words = query.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return keywords
    
    def _classify_intent(self, query: str) -> str:
        """Classify query intent"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['what', 'who', 'where', 'when', 'why', 'how']):
            return "question"
        elif any(word in query_lower for word in ['find', 'search', 'look for', 'show me']):
            return "search"
        elif any(word in query_lower for word in ['compare', 'difference', 'versus', 'vs']):
            return "comparison"
        elif any(word in query_lower for word in ['explain', 'describe', 'tell me about']):
            return "explanation"
        else:
            return "general"
    
    async def optimize_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Optimize query for better retrieval
        
        Args:
            query: Original query
            context: Additional context
            
        Returns:
            Optimized query
        """
        try:
            # Analyze query
            analysis = await self.analyze_query(query)
            
            # Apply optimizations based on analysis
            optimized = query
            
            # If query is too short, expand it
            if analysis["is_short"]:
                # Add context if available
                if context and "previous_query" in context:
                    optimized = f"{context['previous_query']} {query}"
            
            # If query is too long, extract key parts
            if analysis["is_long"]:
                keywords = analysis["keywords"][:5]
                optimized = " ".join(keywords)
            
            return optimized
            
        except Exception as e:
            logger.error(f"Error optimizing query: {e}")
            return query
    
    def add_to_history(self, query: str, results: List[Any]) -> None:
        """Add query to history"""
        self.query_history.append({
            "query": query,
            "timestamp": datetime.utcnow().isoformat(),
            "num_results": len(results)
        })
    
    def get_query_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent query history"""
        return self.query_history[-limit:]


# Export
__all__ = ["HybridRetriever", "QueryOptimizer"]
