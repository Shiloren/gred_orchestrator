"""
LLM Response Cache — migrado desde tools/llm_security/cache.py

Implementa caching de respuestas LLM con normalización de prompts
para aumentar el hit rate, soporte TTL y estadísticas hit/miss.
"""

import hashlib
import json
import logging
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Optional

try:
    from filelock import FileLock
except ImportError:
    class FileLock:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass


logger = logging.getLogger("orchestrator.llm_cache")


class LLMResponseCache:
    """Caching básico de respuestas LLM con SHA256 keys."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cache_key(self, code: str, analysis_type: str) -> str:
        payload = f"{code}:{analysis_type}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def get(self, code: str, analysis_type: str) -> Optional[Dict]:
        key = self.get_cache_key(code, analysis_type)
        cache_file = self.cache_dir / f"{key}.json"
        lock_file = self.cache_dir / f"{key}.lock"

        if cache_file.exists():
            with FileLock(lock_file):
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        return json.load(f)
                except (json.JSONDecodeError, IOError):
                    return None
        return None

    def set(self, code: str, analysis_type: str, result: Dict):
        if not result.get("success", False):
            return

        key = self.get_cache_key(code, analysis_type)
        cache_file = self.cache_dir / f"{key}.json"
        lock_file = self.cache_dir / f"{key}.lock"

        cache_data = {
            "result": result.get("response"),
            "metadata": result.get("metadata", {}),
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            with FileLock(lock_file):
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(cache_data, f, indent=2)
        except IOError as e:
            logger.warning("Failed to write cache for %s: %s", key, e)


class NormalizedLLMCache(LLMResponseCache):
    """
    Cache avanzado que normaliza prompts para aumentar el hit rate.
    Incluye soporte TTL y estadísticas hit/miss.
    """

    def __init__(self, cache_dir: Path, ttl_hours: int = 24):
        super().__init__(cache_dir)
        self.ttl_hours = ttl_hours
        self.hits = 0
        self.misses = 0

    def normalize_prompt(self, prompt: str) -> str:
        if not prompt:
            return ""

        text = unicodedata.normalize("NFC", prompt)
        text = text.lower()
        text = text.replace("\u201c", '"').replace("\u201d", '"')
        text = text.replace("\u2018", "'").replace("\u2019", "'")
        text = text.replace("\u2014", "-").replace("\u2013", "-")
        text = re.sub(r"[*_`#~|>+\-=[\(\)\{\}\"']+", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"[.!?]+$", "", text).strip()

        return text

    def get_cache_key(self, prompt: str, task_type: str) -> str:
        normalized = self.normalize_prompt(prompt)
        payload = f"{normalized}:{task_type}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def get(self, prompt: str, task_type: str) -> Optional[Dict]:
        key = self.get_cache_key(prompt, task_type)
        cache_file = self.cache_dir / f"{key}.json"
        lock_file = self.cache_dir / f"{key}.lock"

        if not cache_file.exists():
            self.misses += 1
            return None

        try:
            with FileLock(lock_file):
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

            cached_at_str = data.get("cached_at")
            if cached_at_str:
                cached_at = datetime.fromisoformat(cached_at_str)
                if cached_at.tzinfo is None:
                    cached_at = cached_at.replace(tzinfo=timezone.utc)

                age = datetime.now(timezone.utc) - cached_at
                if age > timedelta(hours=self.ttl_hours):
                    logger.info("Cache entry expired for key: %s", key)
                    self.misses += 1
                    try:
                        cache_file.unlink()
                    except OSError:
                        pass
                    return None

            self.hits += 1
            return data
        except (json.JSONDecodeError, IOError) as exc:
            logger.error("Failed to read cache file %s: %s", cache_file, exc)
            self.misses += 1
            return None

    def set(self, prompt: str, task_type: str, result: Dict):
        super().set(prompt, task_type, result)

    def get_hit_rate(self) -> float:
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total

    def clear(self):
        for file in self.cache_dir.glob("*.json"):
            try:
                file.unlink()
            except OSError:
                pass
        for file in self.cache_dir.glob("*.lock"):
            try:
                file.unlink()
            except OSError:
                pass
        self.hits = 0
        self.misses = 0
