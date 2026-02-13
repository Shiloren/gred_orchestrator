from typing import AsyncGenerator, List, Dict, Any
import httpx
import json
import logging
from .base_provider import BaseProvider

logger = logging.getLogger("orchestrator.providers.ollama")

class OllamaProvider(BaseProvider):
    """
    Provider for local Ollama instance.
    """
    
    @property
    def provider_type(self) -> str:
        return "ollama"

    @property
    def is_local(self) -> bool:
        return True

    def _get_base_url(self) -> str:
        return self.config.get("base_url", "http://localhost:11434")

    async def generate(self, prompt: str, model: str, **kwargs) -> str:
        url = f"{self._get_base_url()}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": kwargs
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=120.0)
                response.raise_for_status()
                data = response.json()
                return data.get("response", "")
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise

    async def generate_stream(self, prompt: str, model: str, **kwargs) -> AsyncGenerator[str, None]:
        url = f"{self._get_base_url()}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": kwargs
        }

        try:
            async with httpx.AsyncClient() as client:
                async with client.stream("POST", url, json=payload, timeout=120.0) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                if "response" in data:
                                    yield data["response"]
                                if data.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"Ollama streaming failed: {e}")
            raise

    async def check_availability(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self._get_base_url()}/api/tags", timeout=2.0)
                return resp.status_code == 200
        except:
            return False

    async def list_models(self) -> List[str]:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self._get_base_url()}/api/tags", timeout=5.0)
                if resp.status_code == 200:
                    data = resp.json()
                    return [m["name"] for m in data.get("models", [])]
                return []
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []
