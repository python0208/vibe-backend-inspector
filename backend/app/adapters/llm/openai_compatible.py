import json
from typing import Any

import httpx

from app.adapters.llm.base import LLMClient
from app.models.llm_config import LLMConfig


class OpenAICompatibleClient(LLMClient):
    async def chat_json(
        self,
        config: LLMConfig,
        messages: list[dict[str, str]],
        json_schema: dict[str, Any],
    ) -> dict[str, Any]:
        url = self._chat_url(config.base_url)
        headers = {"Content-Type": "application/json"}
        if config.api_key:
            headers["Authorization"] = f"Bearer {config.api_key}"

        payload = {
            "model": config.model_name,
            "messages": messages,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "response_format": {"type": "json_object"},
        }

        async with httpx.AsyncClient(timeout=float(config.timeout_seconds)) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        if isinstance(content, dict):
            return content
        try:
            loaded = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError("LLM response was not valid JSON.") from exc
        if not isinstance(loaded, dict):
            raise ValueError("LLM response JSON must be an object.")
        return loaded

    async def test_connection(self, config: LLMConfig) -> tuple[bool, str]:
        try:
            result = await self.chat_json(
                config,
                [
                    {
                        "role": "system",
                        "content": "Return only JSON.",
                    },
                    {
                        "role": "user",
                        "content": '{"ok": true, "message": "connection test"}',
                    },
                ],
                {},
            )
        except httpx.HTTPStatusError as exc:
            return False, f"Model connection failed: HTTP {exc.response.status_code}."
        except httpx.TimeoutException:
            return False, "Model connection failed: timeout."
        except Exception as exc:
            return False, f"Model connection failed: {exc.__class__.__name__}."
        return True, f"Model connection succeeded: {result.get('message', 'ok')}."

    @staticmethod
    def _chat_url(base_url: str) -> str:
        normalized = base_url.rstrip("/")
        if normalized.endswith("/chat/completions"):
            return normalized
        if normalized.endswith("/v1"):
            return f"{normalized}/chat/completions"
        return f"{normalized}/v1/chat/completions"
