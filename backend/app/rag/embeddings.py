"""
Embedding Generation Module

Handles generation of vector embeddings for text chunks using OpenAI's
embedding models with batch processing and error handling.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import time

from openai import AsyncOpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingResult:
    """Result of embedding generation"""
    embedding: List[float]
    text: str
    token_count: int
    model: str


class EmbeddingGenerator:
    """
    Generates embeddings using OpenAI's embedding models
    
    Features:
    - Batch processing for efficiency
    - Automatic retry with exponential backoff
    - Rate limiting
    - Cost tracking
    """
    
    def __init__(
        self,
        model: str = None,
        batch_size: int = None,
        max_retries: int = 3
    ):
        self.model = model or settings.openai_embedding_model
        self.batch_size = batch_size or settings.embedding_batch_size
        self.max_retries = max_retries
        
        # Initialize OpenAI client
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            organization=settings.openai_organization_id
        )
        
        # Cost tracking
        self.total_tokens = 0
        self.total_cost = 0.0
        
        # Rate limiting
        self.requests_per_minute = 3000
        self.last_request_time = 0
        self.request_count = 0
        
        logger.info(f"Initialized EmbeddingGenerator with model: {self.model}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception)
    )
    async def generate_embedding(self, text: str) -> EmbeddingResult:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            
        Returns:
            EmbeddingResult with embedding vector
        """
        await self._rate_limit()
        
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text
            )
            
            embedding = response.data[0].embedding
            token_count = response.usage.total_tokens
            
            # Update cost tracking
            self._update_cost(token_count)
            
            logger.debug(f"Generated embedding for text of length {len(text)}")
            
            return EmbeddingResult(
                embedding=embedding,
                text=text,
                token_count=token_count,
                model=self.model
            )
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    async def generate_embeddings_batch(
        self,
        texts: List[str],
        show_progress: bool = False
    ) -> List[EmbeddingResult]:
        """
        Generate embeddings for multiple texts in batches
        
        Args:
            texts: List of texts to embed
            show_progress: Whether to log progress
            
        Returns:
            List of EmbeddingResult objects
        """
        results = []
        total_batches = (len(texts) + self.batch_size - 1) // self.batch_size
        
        logger.info(f"Generating embeddings for {len(texts)} texts in {total_batches} batches")
        
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            
            if show_progress:
                logger.info(f"Processing batch {batch_num}/{total_batches}")
            
            # Process batch
            batch_results = await self._process_batch(batch)
            results.extend(batch_results)
            
            # Small delay between batches to avoid rate limits
            if i + self.batch_size < len(texts):
                await asyncio.sleep(0.1)
        
        logger.info(
            f"Generated {len(results)} embeddings. "
            f"Total tokens: {self.total_tokens}, "
            f"Estimated cost: ${self.total_cost:.4f}"
        )
        
        return results
    
    async def _process_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """Process a batch of texts"""
        await self._rate_limit()
        
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            
            results = []
            for i, data in enumerate(response.data):
                results.append(EmbeddingResult(
                    embedding=data.embedding,
                    text=texts[i],
                    token_count=response.usage.total_tokens // len(texts),  # Approximate
                    model=self.model
                ))
            
            # Update cost tracking
            self._update_cost(response.usage.total_tokens)
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            # Fallback to individual processing
            logger.info("Falling back to individual embedding generation")
            return await self._process_individually(texts)
    
    async def _process_individually(self, texts: List[str]) -> List[EmbeddingResult]:
        """Process texts individually (fallback)"""
        results = []
        for text in texts:
            try:
                result = await self.generate_embedding(text)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to generate embedding for text: {e}")
                # Create a zero embedding as fallback
                results.append(EmbeddingResult(
                    embedding=[0.0] * settings.embedding_dimensions,
                    text=text,
                    token_count=0,
                    model=self.model
                ))
        return results
    
    async def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        
        # Reset counter every minute
        if current_time - self.last_request_time > 60:
            self.request_count = 0
            self.last_request_time = current_time
        
        # Check if we've hit the rate limit
        if self.request_count >= self.requests_per_minute:
            sleep_time = 60 - (current_time - self.last_request_time)
            if sleep_time > 0:
                logger.warning(f"Rate limit reached. Sleeping for {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
                self.request_count = 0
                self.last_request_time = time.time()
        
        self.request_count += 1
    
    def _update_cost(self, tokens: int):
        """
        Update cost tracking
        
        OpenAI pricing (as of 2024):
        - text-embedding-3-small: $0.00002 per 1K tokens
        - text-embedding-3-large: $0.00013 per 1K tokens
        - text-embedding-ada-002: $0.00010 per 1K tokens
        """
        self.total_tokens += tokens
        
        # Cost per 1K tokens
        cost_per_1k = {
            "text-embedding-3-small": 0.00002,
            "text-embedding-3-large": 0.00013,
            "text-embedding-ada-002": 0.00010,
        }
        
        rate = cost_per_1k.get(self.model, 0.00002)
        self.total_cost += (tokens / 1000) * rate
    
    def get_cost_stats(self) -> Dict[str, Any]:
        """Get cost statistics"""
        return {
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "model": self.model,
            "average_cost_per_embedding": (
                self.total_cost / max(self.request_count, 1)
            )
        }
    
    def reset_stats(self):
        """Reset cost tracking statistics"""
        self.total_tokens = 0
        self.total_cost = 0.0
        self.request_count = 0


async def generate_embeddings_for_chunks(
    chunks: List[Dict[str, Any]],
    generator: Optional[EmbeddingGenerator] = None
) -> List[Dict[str, Any]]:
    """
    Generate embeddings for a list of chunks
    
    Args:
        chunks: List of chunk dictionaries with 'content' field
        generator: Optional EmbeddingGenerator instance
        
    Returns:
        List of chunks with 'embedding' field added
    """
    if generator is None:
        generator = EmbeddingGenerator()
    
    # Extract texts
    texts = [chunk["content"] for chunk in chunks]
    
    # Generate embeddings
    results = await generator.generate_embeddings_batch(texts, show_progress=True)
    
    # Add embeddings to chunks
    for chunk, result in zip(chunks, results):
        chunk["embedding"] = result.embedding
        chunk["token_count"] = result.token_count
    
    return chunks
