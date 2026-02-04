"""
AI Text Cache

Caches AI-generated text for deterministic replay.
"""

import hashlib
import json
import os
import sqlite3
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
from .types import TextRequest, TextResponse


class TextCache:
    """
    Cache for AI-generated text.
    
    Supports both SQLite (thread-safe) and JSON (simple) backends.
    """
    
    def __init__(
        self,
        cache_dir: str = ".git_dungeon_cache",
        backend: str = "sqlite"
    ):
        """
        Initialize the text cache.
        
        Args:
            cache_dir: Directory for cache files
            backend: Cache backend ('sqlite' or 'json')
        """
        self.cache_dir = Path(cache_dir)
        self.backend = backend
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        if backend == "sqlite":
            self._init_sqlite()
        elif backend == "json":
            self._init_json()
        
        self._lock = threading.Lock()
    
    def _init_sqlite(self):
        """Initialize SQLite database."""
        db_path = self.cache_dir / "ai_text.sqlite"
        self.db_path = str(db_path)
        
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_text_cache (
                cache_key TEXT PRIMARY KEY,
                provider TEXT,
                text TEXT,
                created_at REAL,
                meta TEXT,
                repo_id TEXT,
                seed INTEGER,
                lang TEXT,
                kind TEXT
            )
        """)
        # Create index only if columns exist
        try:
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_repo_seed_lang 
                ON ai_text_cache (repo_id, seed, lang)
            """)
        except Exception:
            pass  # Index might already exist without those columns
        conn.commit()
        conn.close()
    
    def _init_json(self):
        """Initialize JSON cache files."""
        self.json_cache_file = self.cache_dir / "ai_text_cache.json"
        if not self.json_cache_file.exists():
            self.json_cache_file.write_text("{}")
    
    def _generate_cache_key(
        self,
        provider: str,
        repo_id: str,
        seed: int,
        lang: str,
        content_version: str,
        kind: str,
        specific_id: Optional[str] = None
    ) -> str:
        """Generate a unique cache key."""
        key_parts = {
            "provider": provider,
            "repo_id": repo_id,
            "seed": seed,
            "lang": lang,
            "content_version": content_version,
            "kind": kind,
        }
        if specific_id:
            key_parts["specific_id"] = specific_id
        
        key_str = json.dumps(key_parts, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()[:32]
    
    def get(self, cache_key: str) -> Optional[TextResponse]:
        """Get a cached text response."""
        with self._lock:
            if self.backend == "sqlite":
                return self._get_sqlite(cache_key)
            return self._get_json(cache_key)
    
    def _get_sqlite(self, cache_key: str) -> Optional[TextResponse]:
        """Get from SQLite."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute(
                "SELECT provider, text, meta FROM ai_text_cache WHERE cache_key = ?",
                (cache_key,)
            )
            row = cursor.fetchone()
            conn.close()
            if row:
                meta = json.loads(row[2]) if row[2] else {}
                return TextResponse(text=row[1], provider=row[0], cached=True, meta=meta)
        except Exception as e:
            print(f"[AI Cache] SQLite get error: {e}")
        return None
    
    def _get_json(self, cache_key: str) -> Optional[TextResponse]:
        """Get from JSON file."""
        try:
            cache = json.loads(self.json_cache_file.read_text())
            if cache_key in cache:
                entry = cache[cache_key]
                return TextResponse(
                    text=entry["text"],
                    provider=entry["provider"],
                    cached=True,
                    meta=entry.get("meta", {})
                )
        except Exception as e:
            print(f"[AI Cache] JSON get error: {e}")
        return None
    
    def set(self, cache_key: str, response: TextResponse, **kwargs):
        """Cache a text response."""
        with self._lock:
            if self.backend == "sqlite":
                self._set_sqlite(cache_key, response, **kwargs)
            else:
                self._set_json(cache_key, response)
    
    def _set_sqlite(self, cache_key: str, response: TextResponse, **kwargs):
        """Set in SQLite."""
        try:
            import datetime
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                """INSERT OR REPLACE INTO ai_text_cache 
                (cache_key, provider, text, created_at, meta, repo_id, seed, lang, kind) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (cache_key, response.provider, response.text,
                 datetime.datetime.now().timestamp(), json.dumps(response.meta),
                 kwargs.get('repo_id', ''), kwargs.get('seed', 0),
                 kwargs.get('lang', ''), kwargs.get('kind', ''))
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[AI Cache] SQLite set error: {e}")
    
    def _set_json(self, cache_key: str, response: TextResponse):
        """Set in JSON file."""
        try:
            cache = json.loads(self.json_cache_file.read_text())
            cache[cache_key] = {
                "text": response.text,
                "provider": response.provider,
                "meta": response.meta,
            }
            self.json_cache_file.write_text(json.dumps(cache, indent=2))
        except Exception as e:
            print(f"[AI Cache] JSON set error: {e}")
    
    def clear(self):
        """Clear all cached data."""
        with self._lock:
            if self.backend == "sqlite":
                try:
                    conn = sqlite3.connect(self.db_path)
                    conn.execute("DELETE FROM ai_text_cache")
                    conn.commit()
                    conn.close()
                except Exception as e:
                    print(f"[AI Cache] SQLite clear error: {e}")
            else:
                try:
                    self.json_cache_file.write_text("{}")
                except Exception as e:
                    print(f"[AI Cache] JSON clear error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            "backend": self.backend,
            "cache_dir": str(self.cache_dir),
            "entries": 0,
            "size_bytes": 0,
        }
        
        if self.backend == "sqlite":
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.execute("SELECT COUNT(*) FROM ai_text_cache")
                stats["entries"] = cursor.fetchone()[0]
                conn.close()
                stats["size_bytes"] = os.path.getsize(self.db_path)
            except Exception as e:
                print(f"[AI Cache] Stats error: {e}")
        else:
            try:
                cache = json.loads(self.json_cache_file.read_text())
                stats["entries"] = len(cache)
                stats["size_bytes"] = self.json_cache_file.stat().st_size
            except Exception as e:
                print(f"[AI Cache] Stats error: {e}")
        
        return stats
    
    def build_cache_key(
        self,
        provider: str,
        request: TextRequest,
        content_version: str,
        prompt_version: str = "1.0"
    ) -> str:
        """
        Build a cache key for a request.
        
        Args:
            provider: AI provider name
            request: Text generation request
            content_version: Content version (YAML files hash)
            prompt_version: Prompts version
            
        Returns:
            Cache key string
        """
        # Include prompt version to invalidate cache when prompts change
        combined_version = f"{content_version}:{prompt_version}"
        
        return self._generate_cache_key(
            provider=provider,
            repo_id=request.repo_id,
            seed=request.seed,
            lang=request.lang,
            content_version=combined_version,
            kind=request.kind.value,
            specific_id=request.enemy_id or request.event_id or request.commit_sha
        )
