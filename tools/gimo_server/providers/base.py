from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class ProviderAdapter(ABC):
    """Provider adapter interface."""

    @abstractmethod
    async def generate(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate draft content for a prompt.

        Returns a dictionary with:
        - "content": str (the generated text)
        - "usage": dict (optional tokens usage info)
        """

    @abstractmethod
    async def health_check(self) -> bool:
        """Best-effort health check."""
