from typing import Any

from app.adapters.llm.base import LLMClient
from app.adapters.llm.mock import MockLLMClient
from app.adapters.llm.openai_compatible import OpenAICompatibleClient
from app.models.llm_config import LLMConfig


class LLMService:
    def __init__(self) -> None:
        self.openai_compatible = OpenAICompatibleClient()
        self.mock = MockLLMClient()

    def client_for(self, config: LLMConfig) -> LLMClient:
        if config.provider == "mock" or config.model_name.lower() == "mock":
            return self.mock
        return self.openai_compatible

    async def chat_json(
        self,
        config: LLMConfig,
        messages: list[dict[str, str]],
        json_schema: dict[str, Any],
    ) -> dict[str, Any]:
        return await self.client_for(config).chat_json(config, messages, json_schema)

    async def test_connection(self, config: LLMConfig) -> tuple[bool, str]:
        return await self.client_for(config).test_connection(config)
