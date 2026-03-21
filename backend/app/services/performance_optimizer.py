"""
PerformanceOptimizer: Utilities for handling large documents efficiently.

Sprint 3: Batch processing, lazy loading, and caching strategies for documents.
"""
from __future__ import annotations

from typing import Any, List, Dict, Optional, Callable, TypeVar, Generator
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import asyncio
import time
import structlog

logger = structlog.get_logger(__name__)

T = TypeVar('T')


class BatchProcessor:
    """
    Process items in batches for better memory management and throughput.
    """
    
    def __init__(self, batch_size: int = 50, max_workers: int = 4):
        self.batch_size = batch_size
        self.max_workers = max_workers
    
    def process_in_batches(
        self,
        items: List[T],
        processor: Callable[[List[T]], List[Any]],
        show_progress: bool = False,
    ) -> List[Any]:
        """
        Process items in batches using the provided processor function.
        
        Args:
            items: List of items to process
            processor: Function that processes a batch and returns results
            show_progress: Log progress updates
            
        Returns:
            Flattened list of all results
        """
        if not items:
            return []
        
        results: List[Any] = []
        total_batches = (len(items) + self.batch_size - 1) // self.batch_size
        
        start_time = time.time()
        
        for batch_idx, i in enumerate(range(0, len(items), self.batch_size)):
            batch = items[i:i + self.batch_size]
            batch_results = processor(batch)
            results.extend(batch_results)
            
            if show_progress and (batch_idx + 1) % 5 == 0:
                elapsed = time.time() - start_time
                logger.info(
                    "batch_progress",
                    batch=batch_idx + 1,
                    total=total_batches,
                    elapsed_sec=round(elapsed, 2),
                )
        
        if show_progress:
            logger.info(
                "batch_complete",
                total_items=len(items),
                total_batches=total_batches,
                elapsed_sec=round(time.time() - start_time, 2),
            )
        
        return results

    async def process_in_batches_async(
        self,
        items: List[T],
        processor: Callable[[List[T]], List[Any]],
    ) -> List[Any]:
        """
        Async version of batch processing using thread pool.
        """
        if not items:
            return []
        
        results: List[Any] = []
        loop = asyncio.get_event_loop()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for i in range(0, len(items), self.batch_size):
                batch = items[i:i + self.batch_size]
                future = loop.run_in_executor(executor, processor, batch)
                futures.append(future)
            
            for future in asyncio.as_completed(futures):
                batch_results = await future
                results.extend(batch_results)
        
        return results


class ChunkIterator:
    """
    Lazy iterator for processing large documents chunk by chunk.
    Avoids loading entire document into memory.
    """
    
    def __init__(
        self,
        source: Any,
        chunk_size: int = 1000,
        overlap: int = 100,
    ):
        self.source = source
        self.chunk_size = chunk_size
        self.overlap = overlap
        self._position = 0
    
    def __iter__(self) -> Generator[Dict[str, Any], None, None]:
        """Iterate over chunks with metadata."""
        if isinstance(self.source, str):
            yield from self._iterate_text()
        elif isinstance(self.source, list):
            yield from self._iterate_list()
        elif hasattr(self.source, '__iter__'):
            yield from self._iterate_iterable()
    
    def _iterate_text(self) -> Generator[Dict[str, Any], None, None]:
        """Iterate over text string."""
        text = self.source
        start = 0
        chunk_idx = 0
        
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end]
            
            yield {
                "chunk_idx": chunk_idx,
                "text": chunk_text,
                "start_char": start,
                "end_char": end,
                "is_last": end >= len(text),
            }
            
            chunk_idx += 1
            start = max(0, end - self.overlap)
            
            if start >= len(text) - self.overlap:
                break
    
    def _iterate_list(self) -> Generator[Dict[str, Any], None, None]:
        """Iterate over list items."""
        items = self.source
        chunk_idx = 0
        
        for i in range(0, len(items), self.chunk_size):
            batch = items[i:i + self.chunk_size]
            yield {
                "chunk_idx": chunk_idx,
                "items": batch,
                "start_idx": i,
                "end_idx": min(i + self.chunk_size, len(items)),
                "is_last": i + self.chunk_size >= len(items),
            }
            chunk_idx += 1
    
    def _iterate_iterable(self) -> Generator[Dict[str, Any], None, None]:
        """Iterate over any iterable."""
        buffer = []
        chunk_idx = 0
        
        for item in self.source:
            buffer.append(item)
            
            if len(buffer) >= self.chunk_size:
                yield {
                    "chunk_idx": chunk_idx,
                    "items": buffer,
                    "is_last": False,
                }
                buffer = buffer[-self.overlap:] if self.overlap > 0 else []
                chunk_idx += 1
        
        if buffer:
            yield {
                "chunk_idx": chunk_idx,
                "items": buffer,
                "is_last": True,
            }


class DocumentCache:
    """
    Simple in-memory cache for document processing results.
    Uses LRU eviction strategy.
    """
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._cache: Dict[str, Any] = {}
        self._access_order: List[str] = []
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache, updating access order."""
        if key in self._cache:
            # Move to end (most recently used)
            self._access_order.remove(key)
            self._access_order.append(key)
            return self._cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Set item in cache, evicting if necessary."""
        if key in self._cache:
            self._access_order.remove(key)
        elif len(self._cache) >= self.max_size:
            # Evict least recently used
            oldest_key = self._access_order.pop(0)
            del self._cache[oldest_key]
        
        self._cache[key] = value
        self._access_order.append(key)
    
    def clear(self) -> None:
        """Clear all cached items."""
        self._cache.clear()
        self._access_order.clear()
    
    def __contains__(self, key: str) -> bool:
        return key in self._cache
    
    def __len__(self) -> int:
        return len(self._cache)


class EmbeddingCache:
    """
    Specialized cache for embeddings with memory-efficient storage.
    """
    
    def __init__(self, max_items: int = 10000):
        self.max_items = max_items
        self._embeddings: Dict[str, bytes] = {}
        self._texts_hash: Dict[str, str] = {}
    
    def get_embedding(self, text: str) -> Optional[bytes]:
        """Get cached embedding for text."""
        text_hash = self._hash_text(text)
        return self._embeddings.get(text_hash)
    
    def set_embedding(self, text: str, embedding: bytes) -> None:
        """Cache embedding for text."""
        if len(self._embeddings) >= self.max_items:
            # Remove oldest 10%
            keys_to_remove = list(self._embeddings.keys())[:self.max_items // 10]
            for key in keys_to_remove:
                del self._embeddings[key]
        
        text_hash = self._hash_text(text)
        self._embeddings[text_hash] = embedding
        self._texts_hash[text_hash] = text[:100]  # Store truncated for debugging
    
    def _hash_text(self, text: str) -> str:
        """Create hash for text."""
        import hashlib
        return hashlib.md5(text.encode()).hexdigest()
    
    def __len__(self) -> int:
        return len(self._embeddings)


def estimate_processing_time(
    num_items: int,
    item_size_bytes: int,
    processing_rate: float = 1000,  # items per second
) -> Dict[str, Any]:
    """
    Estimate processing time for a batch of items.
    
    Args:
        num_items: Number of items to process
        item_size_bytes: Average size of each item in bytes
        processing_rate: Expected items per second
        
    Returns:
        Dict with time estimates and recommendations
    """
    estimated_seconds = num_items / processing_rate
    total_size_mb = (num_items * item_size_bytes) / (1024 * 1024)
    
    recommendations = []
    
    if num_items > 10000:
        recommendations.append("Consider using batch processing")
    if total_size_mb > 100:
        recommendations.append("Consider streaming/chunked processing")
    if estimated_seconds > 60:
        recommendations.append("Consider background job processing")
    
    return {
        "num_items": num_items,
        "total_size_mb": round(total_size_mb, 2),
        "estimated_seconds": round(estimated_seconds, 2),
        "estimated_minutes": round(estimated_seconds / 60, 2),
        "recommendations": recommendations,
        "batch_size_recommended": min(100, max(10, num_items // 100)),
    }


# Singleton instances
_batch_processor: Optional[BatchProcessor] = None
_document_cache: Optional[DocumentCache] = None
_embedding_cache: Optional[EmbeddingCache] = None


def get_batch_processor(batch_size: int = 50, max_workers: int = 4) -> BatchProcessor:
    """Get or create batch processor singleton."""
    global _batch_processor
    if _batch_processor is None:
        _batch_processor = BatchProcessor(batch_size, max_workers)
    return _batch_processor


def get_document_cache(max_size: int = 100) -> DocumentCache:
    """Get or create document cache singleton."""
    global _document_cache
    if _document_cache is None:
        _document_cache = DocumentCache(max_size)
    return _document_cache


def get_embedding_cache(max_items: int = 10000) -> EmbeddingCache:
    """Get or create embedding cache singleton."""
    global _embedding_cache
    if _embedding_cache is None:
        _embedding_cache = EmbeddingCache(max_items)
    return _embedding_cache
