import os
import httpx
import logging
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, Optional

logger = logging.getLogger("orchestrator.model_service")

class ModelProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, model: str, **kwargs) -> str:
        pass

    @abstractmethod
    async def generate_stream(self, prompt: str, model: str, **kwargs) -> AsyncGenerator[str, None]:
        pass

    @abstractmethod
    async def check_availability(self) -> bool:
        pass

class OllamaProvider(ModelProvider):
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url

    async def generate(self, prompt: str, model: str, **kwargs) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": kwargs
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=60.0)
                response.raise_for_status()
                data = response.json()
                return data.get("response", "")
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise

    async def generate_stream(self, prompt: str, model: str, **kwargs) -> AsyncGenerator[str, None]:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": kwargs
        }

        try:
            async with httpx.AsyncClient() as client:
                async with client.stream("POST", url, json=payload, timeout=60.0) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            import json
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
                resp = await client.get(f"{self.base_url}/api/tags", timeout=2.0)
                return resp.status_code == 200
        except:
            return False

class ModelService:
    _provider: Optional[ModelProvider] = None

    @classmethod
    def initialize(cls, provider_type: str = "ollama", **kwargs):
        if provider_type == "ollama":
            base_url = kwargs.get("base_url", "http://localhost:11434")
            cls._provider = OllamaProvider(base_url)
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")

    @classmethod
    async def generate(cls, prompt: str, model: str, **kwargs) -> str:
        if not cls._provider:
            raise RuntimeError("ModelService not initialized")
        return await cls._provider.generate(prompt, model, **kwargs)

    @classmethod
    async def generate_stream(cls, prompt: str, model: str, **kwargs) -> AsyncGenerator[str, None]:
        if not cls._provider:
            raise RuntimeError("ModelService not initialized")
        return cls._provider.generate_stream(prompt, model, **kwargs)

    @classmethod
    async def is_backend_ready(cls) -> bool:
        if not cls._provider:
            return False
        return await cls._provider.check_availability()
