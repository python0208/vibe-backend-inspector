export type LLMProvider =
  | "openai_compatible"
  | "openai"
  | "deepseek"
  | "qwen"
  | "zhipu"
  | "ollama"
  | "custom"
  | "mock";

export interface LLMConfig {
  id: number;
  provider: LLMProvider;
  display_name: string;
  base_url: string;
  model_name: string;
  temperature: number;
  timeout_seconds: number;
  max_tokens: number;
  enabled: boolean;
  masked_api_key?: string | null;
  has_api_key: boolean;
  created_at: string;
  updated_at: string;
}

export interface LLMConfigPayload {
  provider: LLMProvider;
  display_name: string;
  base_url: string;
  api_key?: string | null;
  model_name: string;
  temperature: number;
  timeout_seconds: number;
  max_tokens: number;
  enabled: boolean;
}

export interface LLMConfigTestResponse {
  ok: boolean;
  message: string;
  provider: string;
  model_name: string;
}
