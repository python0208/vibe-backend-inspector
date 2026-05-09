from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


LLMProvider = Literal[
    "openai_compatible",
    "openai",
    "deepseek",
    "qwen",
    "zhipu",
    "ollama",
    "custom",
    "mock",
]


class LLMConfigBase(BaseModel):
    provider: LLMProvider = "openai_compatible"
    display_name: str = Field(min_length=1, max_length=200)
    base_url: str = Field(min_length=1)
    model_name: str = Field(min_length=1, max_length=200)
    temperature: float = Field(default=0.2, ge=0, le=2)
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    max_tokens: int = Field(default=2000, ge=128, le=32000)
    enabled: bool = True


class LLMConfigCreate(LLMConfigBase):
    api_key: str | None = None


class LLMConfigUpdate(BaseModel):
    provider: LLMProvider | None = None
    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    base_url: str | None = Field(default=None, min_length=1)
    api_key: str | None = None
    model_name: str | None = Field(default=None, min_length=1, max_length=200)
    temperature: float | None = Field(default=None, ge=0, le=2)
    timeout_seconds: int | None = Field(default=None, ge=1, le=300)
    max_tokens: int | None = Field(default=None, ge=128, le=32000)
    enabled: bool | None = None


class LLMConfigRead(LLMConfigBase):
    id: int
    masked_api_key: str | None = None
    has_api_key: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LLMConfigTestResponse(BaseModel):
    ok: bool
    message: str
    provider: str
    model_name: str
