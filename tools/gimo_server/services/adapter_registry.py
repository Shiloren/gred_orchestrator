from typing import Dict, Type, Optional
from ..adapters.base import AgentAdapter
from ..adapters.local_llm import LocalLLMAdapter
from ..adapters.generic_cli import GenericCLIAdapter
# Import other adapters as needed

class AdapterRegistry:
    _adapters: Dict[str, AgentAdapter] = {}

    @classmethod
    def register(cls, name: str, adapter: AgentAdapter):
        cls._adapters[name] = adapter

    @classmethod
    def get(cls, name: str) -> Optional[AgentAdapter]:
        return cls._adapters.get(name)

    @classmethod
    def initialize_defaults(cls):
        # Register default adapters
        cls.register("local", LocalLLMAdapter(model_name="qwen-2.5-7b-instruct"))
        # Add others if configured
