import pytest
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, AsyncMock
from tools.gimo_server.services.llm_cache import NormalizedLLMCache
from tools.gimo_server.services.provider_service import ProviderService
from tools.gimo_server.ops_models import OpsConfig, UserEconomyConfig

class TestNormalizedLLMCache:
    @pytest.fixture
    def cache_dir(self, tmp_path):
        d = tmp_path / "normalized_cache"
        d.mkdir()
        return d

    def test_normalization_logic(self, cache_dir):
        cache = NormalizedLLMCache(cache_dir)
        
        # Test smart quotes and dashes
        assert cache.normalize_prompt("\u201cSmart Quote\u201d") == "smart quote"
        assert cache.normalize_prompt("Em\u2014Dash") == "em dash"
        
        # Test complex markdown
        prompt = "> Hello\n- Item 1\n`code`"
        assert cache.normalize_prompt(prompt) == "hello item 1 code"
        
        # Test punctuation stripping at end
        assert cache.normalize_prompt("Is this a test?") == "is this a test"
        assert cache.normalize_prompt("Perfect!!!") == "perfect"
        assert cache.normalize_prompt("End. ") == "end"

    def test_unicode_normalization(self, cache_dir):
        cache = NormalizedLLMCache(cache_dir)
        # é vs e + ́
        assert cache.normalize_prompt("\u00e9") == cache.normalize_prompt("e\u0301")

    def test_cache_hit_and_miss(self, cache_dir):
        cache = NormalizedLLMCache(cache_dir)
        prompt = "Unique prompt"
        task = "test"
        
        # Initial miss
        assert cache.get(prompt, task) is None
        assert cache.misses == 1
        assert cache.hits == 0
        
        # Set and hit
        cache.set(prompt, task, {"success": True, "response": "OK"})
        res = cache.get("  UNIQUE  prompt!  ", task)
        assert res is not None
        assert res["result"] == "OK"
        assert cache.hits == 1
        assert cache.get_hit_rate() == pytest.approx(0.5)

    def test_ttl_expiration(self, cache_dir):
        cache = NormalizedLLMCache(cache_dir, ttl_hours=1)
        prompt = "Stale"
        task = "test"
        
        # Set entry
        cache.set(prompt, task, {"success": True, "response": "Stale"})
        
        # Manually backdate the entry
        key = cache.get_cache_key(prompt, task)
        cache_file = cache_dir / f"{key}.json"
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        past = datetime.now(timezone.utc) - timedelta(hours=2)
        data["cached_at"] = past.isoformat()
        
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
            
        # Get should return None and delete file
        assert cache.get(prompt, task) is None
        assert not cache_file.exists()
        assert cache.misses == 1

    def test_clear(self, cache_dir):
        cache = NormalizedLLMCache(cache_dir)
        cache.set("a", "b", {"success": True, "response": "1"})
        assert len(list(cache_dir.glob("*.json"))) == 1
        
        cache.clear()
        assert len(list(cache_dir.glob("*.json"))) == 0
        assert cache.hits == 0
        assert cache.misses == 0

@pytest.mark.asyncio
class TestProviderServiceCacheIntegration:
    async def test_static_generate_cache_flow(self, tmp_path):
        # Mocking the environment
        config = OpsConfig()
        config.economy = UserEconomyConfig(cache_enabled=True, cache_ttl_hours=24)
        
        with patch('tools.gimo_server.services.ops_service.OpsService.get_config', return_value=config), \
             patch('tools.gimo_server.services.provider_service.OPS_DATA_DIR', tmp_path), \
             patch('tools.gimo_server.services.provider_service.ProviderService.get_config') as mock_p_cfg:
            
            p_cfg = MagicMock()
            p_cfg.active = "mock_p"
            mock_entry = MagicMock()
            mock_entry.type = "openai_compat"
            mock_entry.model = "gpt-4"
            mock_entry.base_url = "http://localhost"
            mock_entry.api_key = None
            p_cfg.providers = {"mock_p": mock_entry}
            mock_p_cfg.return_value = p_cfg
            
            prompt = "What is 2+2?"
            
            # First call: Miss
            with patch('tools.gimo_server.providers.openai_compat.OpenAICompatAdapter.generate', new_callable=AsyncMock) as mock_gen:
                mock_gen.return_value = {
                    "content": "4",
                    "usage": {"prompt_tokens": 5, "completion_tokens": 1}
                }
                
                res1 = await ProviderService.static_generate(prompt, {})
                assert res1["cache_hit"] is False
                assert res1["content"] == "4"
                assert mock_gen.call_count == 1
            
            # Second call: Hit
            with patch('tools.gimo_server.providers.openai_compat.OpenAICompatAdapter.generate', new_callable=AsyncMock) as mock_gen:
                res2 = await ProviderService.static_generate("  WHAT is 2+2?  ", {})
                assert res2["cache_hit"] is True
                assert res2["content"] == "4"
                assert res2["tokens_used"] == 0
                assert mock_gen.call_count == 0

    async def test_cache_disabled_respected(self, tmp_path):
        config = OpsConfig()
        config.economy = UserEconomyConfig(cache_enabled=False)
        
        with patch('tools.gimo_server.services.ops_service.OpsService.get_config', return_value=config), \
             patch('tools.gimo_server.services.provider_service.OPS_DATA_DIR', tmp_path), \
             patch('tools.gimo_server.services.provider_service.ProviderService.get_config') as mock_p_cfg:
            
            p_cfg = MagicMock()
            p_cfg.active = "mock_p"
            mock_entry = MagicMock()
            mock_entry.type = "openai_compat"
            mock_entry.model = "gpt-4"
            mock_entry.base_url = "http://localhost"
            mock_entry.api_key = None
            p_cfg.providers = {"mock_p": mock_entry}
            mock_p_cfg.return_value = p_cfg
            
            with patch('tools.gimo_server.providers.openai_compat.OpenAICompatAdapter.generate', new_callable=AsyncMock) as mock_gen:
                mock_gen.return_value = {"content": "ok", "usage": {}}
                
                await ProviderService.static_generate("prompt", {})
                await ProviderService.static_generate("prompt", {})
                
                assert mock_gen.call_count == 2
