import hashlib
import json
import logging
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Optional, Any

try:
    from filelock import FileLock
except ImportError:
    # Fallback to a dummy lock if filelock is not available
    class FileLock:
        def __init__(self, *args, **kwargs):
            """Dummy init."""
            pass
        def __enter__(self):
            """Dummy enter."""
            return self
        def __exit__(self, *args):
            """Dummy exit."""
            pass


logger = logging.getLogger("orchestrator.llm_security.cache")


class LLMResponseCache:
    """Implement caching for LLM responses to reduce costs and latency."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cache_key(self, code: str, analysis_type: str) -> str:
        """Generate a stable SHA256 key from content and analysis type."""
        payload = f"{code}:{analysis_type}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def get(self, code: str, analysis_type: str) -> Optional[Dict]:
        """Retrieve a cached response if available."""
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
        """
        Cache a successful result.

        result expected format:
        {
            'response': str,
            'metadata': dict,
            'success': bool
        }
        """
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
    Advanced cache that normalizes prompts to increase hit rate.
    Includes TTL support and hit/miss statistics.
    """

    def __init__(self, cache_dir: Path, ttl_hours: int = 24):
        super().__init__(cache_dir)
        self.ttl_hours = ttl_hours
        self.hits = 0
        self.misses = 0

    def normalize_prompt(self, prompt: str) -> str:
        """
        Normalize prompt to reduce sensitive variations.
        - NFC Unicode normalization
        - Lowercase
        - Collapse multiple spaces/newlines
        - Strip whitespace
        - Remove common markdown formatting artifacts
        - Standardize common separators
        """
        if not prompt:
            return ""

        # 1. NFC Normalization for consistent unicode representation
        text = unicodedata.normalize("NFC", prompt)

        # 2. Lowercase for case-insensitive matching
        text = text.lower()

        # 3. Standardize "smart" quotes and dashes
        text = text.replace("\u201c", '"').replace("\u201d", '"') # Smart double quotes
        text = text.replace("\u2018", "'").replace("\u2019", "'") # Smart single quotes
        text = text.replace("\u2014", "-").replace("\u2013", "-") # Em/En dashes

        # 4. Remove common markdown formatting artifacts and stylistic markers (quotes)
        # Replace bold, italic, code block markers, headers, list markers, quotes, etc. with space
        text = re.sub(r"[*_`#~|>+\-=[\(\)\{\}\"']+", " ", text)

        # 5. Collapse all whitespace including tabs and multiple newlines
        text = re.sub(r"\s+", " ", text).strip()

        # 6. Handle trailing punctuation that often varies but rarely changes intent
        # (Only if it's common trailing noise)
        text = re.sub(r"[.!?]+$", "", text).strip()

        return text

    def get_cache_key(self, prompt: str, task_type: str) -> str:
        """Generate key using normalized prompt."""
        normalized = self.normalize_prompt(prompt)
        payload = f"{normalized}:{task_type}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def get(self, prompt: str, task_type: str) -> Optional[Dict]:
        """Retrieve cached response with TTL check."""
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

            # TTL Check
            cached_at_str = data.get("cached_at")
            if cached_at_str:
                cached_at = datetime.fromisoformat(cached_at_str)
                # Ensure timezone aware comparison
                if cached_at.tzinfo is None:
                    cached_at = cached_at.replace(tzinfo=timezone.utc)
                
                age = datetime.now(timezone.utc) - cached_at
                if age > timedelta(hours=self.ttl_hours):
                    logger.info("Cache entry expired for key: %s", key)
                    self.misses += 1
                    try:
                        cache_file.unlink() # Delete expired entry
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
        """Saves result to cache using normalized key."""
        # Wrap LLMResponseCache.set but use normalized key
        # Note: LLMResponseCache expects 'code', we use 'prompt'
        super().set(prompt, task_type, result)

    def get_hit_rate(self) -> float:
        """Calculate hit rate as 0.0 to 1.0."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total

    def clear(self):
        """Wipe all cached entries and reset stats."""
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
