import { apiRequest } from "./client";
import type { LLMConfig, LLMConfigPayload, LLMConfigTestResponse } from "../types/llm";

export function listLLMConfigs(): Promise<LLMConfig[]> {
  return apiRequest<LLMConfig[]>("/api/llm/configs");
}

export function createLLMConfig(payload: LLMConfigPayload): Promise<LLMConfig> {
  return apiRequest<LLMConfig>("/api/llm/configs", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateLLMConfig(configId: number, payload: Partial<LLMConfigPayload>): Promise<LLMConfig> {
  return apiRequest<LLMConfig>(`/api/llm/configs/${configId}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function deleteLLMConfig(configId: number): Promise<void> {
  return apiRequest<void>(`/api/llm/configs/${configId}`, { method: "DELETE" });
}

export function testLLMConfig(configId: number): Promise<LLMConfigTestResponse> {
  return apiRequest<LLMConfigTestResponse>(`/api/llm/configs/${configId}/test`, { method: "POST" });
}
