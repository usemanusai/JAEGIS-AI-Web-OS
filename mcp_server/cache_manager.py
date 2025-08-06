"""
Caching System

Enterprise-grade caching with TTL, size limits, and persistence.
"""

import os
import json
import pickle
import hashlib
import time
from pathlib import Path
from typing import Any, Optional, Dict, List, Tuple
from dataclasses import dataclass
from threading import Lock

from loguru import logger


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    created_at: float
    accessed_at: float
    ttl: Optional[float] = None
    size_bytes: int = 0
    metadata: Dict[str, Any] = None


class CacheManager:
    """Enterprise caching manager with persistence and size limits."""
    
    def __init__(self, cache_dir: str = ".mcp_cache", max_size_mb: int = 1024, 
                 default_ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.default_ttl = default_ttl_hours * 3600  # Convert to seconds
        self.cache: Dict[str, CacheEntry] = {}
        self.lock = Lock()
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing cache
        self._load_cache_index()
        
        # Clean expired entries
        self._cleanup_expired()
        
        logger.info(f"Cache manager initialized: {cache_dir} (max: {max_size_mb}MB)")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self.lock:
            cache_key = self._hash_key(key)
            
            if cache_key not in self.cache:
                return None
            
            entry = self.cache[cache_key]
            
            # Check if expired
            if self._is_expired(entry):
                self._remove_entry(cache_key)
                return None
            
            # Update access time
            entry.accessed_at = time.time()
            
            # Load value from disk if needed
            value = self._load_value(cache_key)
            
            logger.debug(f"Cache hit: {key}")
            return value
    
    def set(self, key: str, value: Any, ttl_hours: Optional[int] = None, 
            metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Set value in cache."""
        with self.lock:
            cache_key = self._hash_key(key)
            
            # Calculate TTL
            ttl = (ttl_hours * 3600) if ttl_hours else self.default_ttl
            
            # Serialize and calculate size
            try:
                serialized_value = self._serialize_value(value)
                size_bytes = len(serialized_value)
            except Exception as e:
                logger.error(f"Failed to serialize cache value for {key}: {e}")
                return False
            
            # Check if we need to make space
            if not self._ensure_space(size_bytes):
                logger.warning(f"Cannot cache {key}: insufficient space")
                return False
            
            # Create cache entry
            entry = CacheEntry(
                key=cache_key,
                value=None,  # Value stored on disk
                created_at=time.time(),
                accessed_at=time.time(),
                ttl=ttl,
                size_bytes=size_bytes,
                metadata=metadata or {}
            )
            
            # Save value to disk
            if not self._save_value(cache_key, serialized_value):
                return False
            
            # Add to cache
            self.cache[cache_key] = entry
            
            # Save cache index
            self._save_cache_index()
            
            logger.debug(f"Cached: {key} ({size_bytes} bytes)")
            return True
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        with self.lock:
            cache_key = self._hash_key(key)
            
            if cache_key in self.cache:
                self._remove_entry(cache_key)
                self._save_cache_index()
                logger.debug(f"Deleted from cache: {key}")
                return True
            
            return False
    
    def clear(self):
        """Clear all cache entries."""
        with self.lock:
            # Remove all files
            for cache_key in list(self.cache.keys()):
                self._remove_entry(cache_key)
            
            self.cache.clear()
            self._save_cache_index()
            
            logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total_size = sum(entry.size_bytes for entry in self.cache.values())
            total_entries = len(self.cache)
            
            # Calculate hit rate (simplified)
            hit_rate = 0.0  # Would need to track hits/misses for accurate calculation
            
            return {
                "total_entries": total_entries,
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "max_size_mb": self.max_size_bytes / (1024 * 1024),
                "usage_percent": (total_size / self.max_size_bytes) * 100,
                "hit_rate": hit_rate,
                "cache_directory": str(self.cache_dir)
            }
    
    def cleanup(self):
        """Manual cleanup of expired entries."""
        with self.lock:
            self._cleanup_expired()
            self._save_cache_index()
    
    def _hash_key(self, key: str) -> str:
        """Generate hash for cache key."""
        return hashlib.sha256(key.encode()).hexdigest()
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired."""
        if entry.ttl is None:
            return False
        
        return time.time() > (entry.created_at + entry.ttl)
    
    def _ensure_space(self, required_bytes: int) -> bool:
        """Ensure there's enough space for new entry."""
        current_size = sum(entry.size_bytes for entry in self.cache.values())
        
        if current_size + required_bytes <= self.max_size_bytes:
            return True
        
        # Need to free up space - use LRU eviction
        return self._evict_lru(required_bytes)
    
    def _evict_lru(self, required_bytes: int) -> bool:
        """Evict least recently used entries to make space."""
        # Sort by access time (oldest first)
        sorted_entries = sorted(
            self.cache.items(),
            key=lambda x: x[1].accessed_at
        )
        
        freed_bytes = 0
        evicted_keys = []
        
        for cache_key, entry in sorted_entries:
            if freed_bytes >= required_bytes:
                break
            
            freed_bytes += entry.size_bytes
            evicted_keys.append(cache_key)
        
        # Remove evicted entries
        for cache_key in evicted_keys:
            self._remove_entry(cache_key)
            logger.debug(f"Evicted cache entry: {cache_key}")
        
        return freed_bytes >= required_bytes
    
    def _cleanup_expired(self):
        """Remove expired cache entries."""
        expired_keys = []
        
        for cache_key, entry in self.cache.items():
            if self._is_expired(entry):
                expired_keys.append(cache_key)
        
        for cache_key in expired_keys:
            self._remove_entry(cache_key)
            logger.debug(f"Removed expired cache entry: {cache_key}")
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def _remove_entry(self, cache_key: str):
        """Remove cache entry and its file."""
        if cache_key in self.cache:
            # Remove file
            cache_file = self.cache_dir / f"{cache_key}.cache"
            if cache_file.exists():
                cache_file.unlink()
            
            # Remove from memory
            del self.cache[cache_key]
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for storage."""
        try:
            # Try JSON first (more readable)
            if isinstance(value, (dict, list, str, int, float, bool, type(None))):
                return json.dumps(value).encode('utf-8')
        except (TypeError, ValueError):
            pass
        
        # Fall back to pickle
        return pickle.dumps(value)
    
    def _deserialize_value(self, data: bytes) -> Any:
        """Deserialize value from storage."""
        try:
            # Try JSON first
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
        
        # Fall back to pickle
        return pickle.loads(data)
    
    def _save_value(self, cache_key: str, serialized_value: bytes) -> bool:
        """Save value to disk."""
        try:
            cache_file = self.cache_dir / f"{cache_key}.cache"
            with open(cache_file, 'wb') as f:
                f.write(serialized_value)
            return True
        except Exception as e:
            logger.error(f"Failed to save cache value {cache_key}: {e}")
            return False
    
    def _load_value(self, cache_key: str) -> Any:
        """Load value from disk."""
        try:
            cache_file = self.cache_dir / f"{cache_key}.cache"
            if not cache_file.exists():
                return None
            
            with open(cache_file, 'rb') as f:
                data = f.read()
            
            return self._deserialize_value(data)
        except Exception as e:
            logger.error(f"Failed to load cache value {cache_key}: {e}")
            return None
    
    def _save_cache_index(self):
        """Save cache index to disk."""
        try:
            index_file = self.cache_dir / "cache_index.json"
            
            # Convert cache entries to serializable format
            index_data = {}
            for cache_key, entry in self.cache.items():
                index_data[cache_key] = {
                    "key": entry.key,
                    "created_at": entry.created_at,
                    "accessed_at": entry.accessed_at,
                    "ttl": entry.ttl,
                    "size_bytes": entry.size_bytes,
                    "metadata": entry.metadata
                }
            
            with open(index_file, 'w') as f:
                json.dump(index_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save cache index: {e}")
    
    def _load_cache_index(self):
        """Load cache index from disk."""
        try:
            index_file = self.cache_dir / "cache_index.json"
            
            if not index_file.exists():
                return
            
            with open(index_file, 'r') as f:
                index_data = json.load(f)
            
            # Reconstruct cache entries
            for cache_key, entry_data in index_data.items():
                entry = CacheEntry(
                    key=entry_data["key"],
                    value=None,  # Loaded on demand
                    created_at=entry_data["created_at"],
                    accessed_at=entry_data["accessed_at"],
                    ttl=entry_data.get("ttl"),
                    size_bytes=entry_data["size_bytes"],
                    metadata=entry_data.get("metadata", {})
                )
                self.cache[cache_key] = entry
            
            logger.info(f"Loaded {len(self.cache)} cache entries from index")
            
        except Exception as e:
            logger.warning(f"Failed to load cache index: {e}")


class DocumentCache:
    """Specialized cache for document processing results."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
    
    def get_processed_document(self, file_path: str, file_hash: str) -> Optional[List]:
        """Get processed document chunks from cache."""
        cache_key = f"doc_processed:{file_hash}"
        return self.cache_manager.get(cache_key)
    
    def cache_processed_document(self, file_path: str, file_hash: str, 
                                chunks: List, ttl_hours: int = 24) -> bool:
        """Cache processed document chunks."""
        cache_key = f"doc_processed:{file_hash}"
        metadata = {
            "file_path": file_path,
            "chunk_count": len(chunks),
            "processing_time": time.time()
        }
        return self.cache_manager.set(cache_key, chunks, ttl_hours, metadata)
    
    def get_ai_analysis(self, content_hash: str) -> Optional[Dict]:
        """Get AI analysis result from cache."""
        cache_key = f"ai_analysis:{content_hash}"
        return self.cache_manager.get(cache_key)
    
    def cache_ai_analysis(self, content_hash: str, analysis: Dict, 
                         ttl_hours: int = 48) -> bool:
        """Cache AI analysis result."""
        cache_key = f"ai_analysis:{content_hash}"
        metadata = {
            "analysis_type": "architectural_synthesis",
            "provider": analysis.get("_ai_metadata", {}).get("provider", "unknown"),
            "cached_at": time.time()
        }
        return self.cache_manager.set(cache_key, analysis, ttl_hours, metadata)
