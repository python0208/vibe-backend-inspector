import { FormEvent, useEffect, useState } from "react";

import { createLLMConfig, deleteLLMConfig, listLLMConfigs, testLLMConfig, updateLLMConfig } from "../api/llm";
import type { Language, Messages } from "../i18n";
import { LanguageToggle } from "../components/layout/LanguageToggle";
import { Card } from "../components/ui/Card";
import { PageHeader } from "../components/ui/PageHeader";
import { StatusBadge } from "../components/ui/StatusBadge";
import type { LLMConfig, LLMConfigPayload, LLMProvider } from "../types/llm";

const emptyModel: LLMConfigPayload = {
  provider: "mock",
  display_name: "Mock Smart Tester",
  base_url: "mock://local",
  api_key: "",
  model_name: "mock",
  temperature: 0.2,
  timeout_seconds: 30,
  max_tokens: 2000,
  enabled: true
};

export function Settings({
  language,
  onLanguageChange,
  t
}: {
  language: Language;
  onLanguageChange: (language: Language) => void;
  t: Messages;
}) {
  const [configs, setConfigs] = useState<LLMConfig[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [form, setForm] = useState<LLMConfigPayload>(emptyModel);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refreshConfigs() {
    const data = await listLLMConfigs();
    setConfigs(data);
    if (!selectedId && data[0]) {
      selectConfig(data[0]);
    }
  }

  useEffect(() => {
    void refreshConfigs();
  }, []);

  function selectConfig(config: LLMConfig) {
    setSelectedId(config.id);
    setForm({
      provider: config.provider,
      display_name: config.display_name,
      base_url: config.base_url,
      api_key: config.has_api_key ? "********" : "",
      model_name: config.model_name,
      temperature: config.temperature,
      timeout_seconds: config.timeout_seconds,
      max_tokens: config.max_tokens,
      enabled: config.enabled
    });
    setMessage(null);
    setError(null);
  }

  function newMockConfig() {
    setSelectedId(null);
    setForm(emptyModel);
    setMessage(null);
    setError(null);
  }

  function updateField<K extends keyof LLMConfigPayload>(field: K, value: LLMConfigPayload[K]) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function saveConfig(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);
    setError(null);
    try {
      const payload = { ...form, api_key: form.api_key || null };
      const saved = selectedId
        ? await updateLLMConfig(selectedId, payload)
        : await createLLMConfig(payload);
      setSelectedId(saved.id);
      await refreshConfigs();
      setMessage(t.settings.modelSaved);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : t.common.error);
    }
  }

  async function deleteConfig() {
    if (!selectedId) return;
    await deleteLLMConfig(selectedId);
    setSelectedId(null);
    setForm(emptyModel);
    await refreshConfigs();
    setMessage(t.settings.modelDeleted);
  }

  async function testConnection() {
    if (!selectedId) return;
    const result = await testLLMConfig(selectedId);
    if (result.ok) {
      setMessage(result.message);
      setError(null);
    } else {
      setError(result.message);
      setMessage(null);
    }
  }

  return (
    <section className="page-stack">
      <PageHeader subtitle={t.placeholders.settingsSubtitle} title={t.placeholders.settingsTitle} />
      {message ? <div className="notice success">{message}</div> : null}
      {error ? <div className="notice danger">{error}</div> : null}

      <div className="split-grid">
        <Card>
          <div className="card-heading">
            <div>
              <h2>{t.settings.language}</h2>
              <p>{t.common.searchPlaceholder}</p>
            </div>
            <LanguageToggle language={language} onChange={onLanguageChange} />
          </div>
        </Card>
        <Card>
          <div className="card-heading">
            <div>
              <h2>{t.settings.localAgent}</h2>
              <p>{t.placeholders.staticOnly}</p>
            </div>
            <StatusBadge tone="success">{t.common.localAgentOnline}</StatusBadge>
          </div>
        </Card>
      </div>

      <div className="settings-llm-grid">
        <Card>
          <div className="card-heading">
            <div>
              <h2>{t.settings.llmConfigs}</h2>
              <p>{t.settings.llmDescription}</p>
            </div>
            <button className="ghost-button" onClick={newMockConfig} type="button">
              {t.settings.newMockModel}
            </button>
          </div>
          <div className="project-list-modern">
            {configs.length === 0 ? (
              <div className="empty-panel compact">{t.aiTest.noModel}</div>
            ) : (
              configs.map((config) => (
                <button
                  className={config.id === selectedId ? "saved-project active" : "saved-project"}
                  key={config.id}
                  onClick={() => selectConfig(config)}
                  type="button"
                >
                  <strong>{config.display_name}</strong>
                  <span>{config.provider} / {config.model_name}</span>
                </button>
              ))
            )}
          </div>
        </Card>

        <Card>
          <form className="runner-form" onSubmit={(event) => void saveConfig(event)}>
            <div className="card-heading">
              <div>
                <h2>{t.settings.saveModel}</h2>
                <p>{t.settings.apiKeyStoredLocally}</p>
              </div>
              <StatusBadge tone={form.enabled ? "success" : "neutral"}>
                {form.enabled ? t.common.connected : t.common.disconnected}
              </StatusBadge>
            </div>
            <label className="form-field">
              {t.settings.provider}
              <select value={form.provider} onChange={(event) => updateField("provider", event.target.value as LLMProvider)}>
                {(["mock", "openai_compatible", "openai", "deepseek", "qwen", "zhipu", "ollama", "custom"] as LLMProvider[]).map((provider) => (
                  <option key={provider} value={provider}>{provider}</option>
                ))}
              </select>
            </label>
            <div className="form-grid two">
              <label className="form-field">
                {t.settings.displayName}
                <input value={form.display_name} onChange={(event) => updateField("display_name", event.target.value)} required />
              </label>
              <label className="form-field">
                {t.settings.modelName}
                <input value={form.model_name} onChange={(event) => updateField("model_name", event.target.value)} required />
              </label>
            </div>
            <label className="form-field">
              {t.settings.baseUrl}
              <input value={form.base_url} onChange={(event) => updateField("base_url", event.target.value)} required />
            </label>
            <label className="form-field">
              {t.settings.apiKey}
              <input type="password" value={form.api_key ?? ""} onChange={(event) => updateField("api_key", event.target.value)} />
            </label>
            <div className="form-grid three">
              <label className="form-field">
                {t.settings.temperature}
                <input type="number" step="0.1" value={form.temperature} onChange={(event) => updateField("temperature", Number(event.target.value))} />
              </label>
              <label className="form-field">
                {t.settings.timeoutSeconds}
                <input type="number" value={form.timeout_seconds} onChange={(event) => updateField("timeout_seconds", Number(event.target.value))} />
              </label>
              <label className="form-field">
                {t.settings.maxTokens}
                <input type="number" value={form.max_tokens} onChange={(event) => updateField("max_tokens", Number(event.target.value))} />
              </label>
            </div>
            <label className="checkbox-row">
              <input checked={form.enabled} onChange={(event) => updateField("enabled", event.target.checked)} type="checkbox" />
              {t.settings.enabled}
            </label>
            <div className="button-row">
              <button className="primary-button" type="submit">{t.settings.saveModel}</button>
              <button className="outline-button" disabled={!selectedId} onClick={() => void testConnection()} type="button">
                {t.settings.testModelConnection}
              </button>
              <button className="danger-button" disabled={!selectedId} onClick={() => void deleteConfig()} type="button">
                {t.settings.deleteModel}
              </button>
            </div>
          </form>
        </Card>
      </div>
    </section>
  );
}
