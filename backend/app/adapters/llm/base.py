from abc import ABC, abstractmethod
from typing import Any

from app.models.llm_config import LLMConfig


class LLMClient(ABC):
    @abstractmethod
    async def chat_json(
        self,
        config: LLMConfig,
        messages: list[dict[str, str]],
        json_schema: dict[str, Any],
    ) -> dict[str, Any]:
        pass

    @abstractmethod
    async def test_connection(self, config: LLMConfig) -> tuple[bool, str]:
        pass
