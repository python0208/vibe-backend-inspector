import { AlertTriangle, Clock3, Code2, Play, ShieldCheck, XCircle } from "lucide-react";
import { Fragment, useEffect, useMemo, useState } from "react";

import { analyzeAITestPlan, executeAITestStep, generateAITestPlan, listAITestPlans } from "../api/aiTests";
import { listEndpoints } from "../api/endpoints";
import { listLLMConfigs } from "../api/llm";
import { getTestRun, listTestRuns, runEndpointTest } from "../api/tests";
import { createValidationRun, getValidationRun, listValidationRuns } from "../api/validationRuns";
import { Card } from "../components/ui/Card";
import { PageHeader } from "../components/ui/PageHeader";
import { StatCard } from "../components/ui/StatCard";
import { StatusBadge, type StatusTone } from "../components/ui/StatusBadge";
import type { Messages } from "../i18n";
import type { Endpoint } from "../types/api";
import type { AITestPlan, AITestStep } from "../types/aiTest";
import type { LLMConfig } from "../types/llm";
import type { PageKey } from "../types/navigation";
import type { ProjectListItem } from "../types/project";
import type { DbChanges, TestRequestPayload, TestRun } from "../types/tests";
import type { ValidationRun, ValidationRunDetail, ValidationRunItem } from "../types/validation";

interface KeyValueRow {
  id: string;
  key: string;
  value: string;
}

interface TestRunnerProps {
  t: Messages;
  projects: ProjectListItem[];
  selectedProjectId: number | null;
  initialEndpointId: number | null;
  onNavigate: (page: PageKey) => void;
}

const destructiveMethods = new Set(["DELETE", "PUT", "PATCH"]);

export function TestRunner({
  t,
  projects,
  selectedProjectId,
  initialEndpointId,
  onNavigate
}: TestRunnerProps) {
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]);
  const [selectedEndpointId, setSelectedEndpointId] = useState<number | null>(null);
  const [pathRows, setPathRows] = useState<KeyValueRow[]>([]);
  const [queryRows, setQueryRows] = useState<KeyValueRow[]>([]);
  const [headerRows, setHeaderRows] = useState<KeyValueRow[]>([{ id: createId(), key: "", value: "" }]);
  const [bearerToken, setBearerToken] = useState("");
  const [bodyText, setBodyText] = useState("{}");
  const [testRuns, setTestRuns] = useState<TestRun[]>([]);
  const [validationRuns, setValidationRuns] = useState<ValidationRun[]>([]);
  const [activeValidationRun, setActiveValidationRun] = useState<ValidationRunDetail | null>(null);
  const [validationScope, setValidationScope] = useState<"all" | "selected">("all");
  const [validationName, setValidationName] = useState("Validation Run");
  const [validationIncludePost, setValidationIncludePost] = useState(true);
  const [validationIncludeDestructive, setValidationIncludeDestructive] = useState(false);
  const [validationSkipDestructive, setValidationSkipDestructive] = useState(true);
  const [validationMaxEndpoints, setValidationMaxEndpoints] = useState(50);
  const [latestRun, setLatestRun] = useState<TestRun | null>(null);
  const [llmConfigs, setLlmConfigs] = useState<LLMConfig[]>([]);
  const [selectedLlmConfigId, setSelectedLlmConfigId] = useState<number | null>(null);
  const [aiPlan, setAiPlan] = useState<AITestPlan | null>(null);
  const [selectedStepId, setSelectedStepId] = useState<string | null>(null);
  const [aiLog, setAiLog] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [validationLoading, setValidationLoading] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedProject = projects.find((project) => project.id === selectedProjectId) ?? null;
  const selectedEndpoint = endpoints.find((endpoint) => endpoint.id === selectedEndpointId) ?? null;
  const computedUrl = selectedProject && selectedEndpoint
    ? joinUrl(selectedProject.service_base_url, selectedEndpoint.path)
    : "-";
  const passedCount = testRuns.filter((run) => run.status === "passed").length;
  const failedCount = testRuns.filter((run) => run.status === "failed").length;
  const avgResponseTime = useMemo(() => {
    const timings = testRuns
      .map((run) => run.response_time_ms)
      .filter((value): value is number => typeof value === "number");
    if (!timings.length) return "-";
    return `${Math.round(timings.reduce((sum, value) => sum + value, 0) / timings.length)} ms`;
  }, [testRuns]);
  const selectedStep = aiPlan?.steps.find((step) => step.step_id === selectedStepId) ?? aiPlan?.steps[0] ?? null;

  async function refreshData(projectId = selectedProjectId) {
    if (!projectId) {
      setEndpoints([]);
      setTestRuns([]);
      setLatestRun(null);
      setValidationRuns([]);
      setActiveValidationRun(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [endpointData, runData] = await Promise.all([
        listEndpoints(projectId),
        listTestRuns(projectId)
      ]);
      const validationData = await listValidationRuns(projectId);
      setEndpoints(endpointData);
      setTestRuns(runData);
      setValidationRuns(validationData);
      if (!activeValidationRun && validationData[0]) {
        const detail = await getValidationRun(projectId, validationData[0].id);
        setActiveValidationRun(detail);
      }
      setLatestRun((current) => current ?? runData[0] ?? null);
      setSelectedEndpointId((current) => {
        if (initialEndpointId && endpointData.some((endpoint) => endpoint.id === initialEndpointId)) {
          return initialEndpointId;
        }
        if (current && endpointData.some((endpoint) => endpoint.id === current)) {
          return current;
        }
        return endpointData[0]?.id ?? null;
      });
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : t.testRunner.loadFailed);
      setEndpoints([]);
      setTestRuns([]);
      setValidationRuns([]);
      setActiveValidationRun(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refreshData();
  }, [selectedProjectId, initialEndpointId]);

  useEffect(() => {
    async function loadAiData() {
      try {
        const [configs, plans] = await Promise.all([
          listLLMConfigs(),
          selectedProjectId ? listAITestPlans(selectedProjectId) : Promise.resolve([])
        ]);
        setLlmConfigs(configs.filter((config) => config.enabled));
        setSelectedLlmConfigId((current) => current ?? configs.find((config) => config.enabled)?.id ?? null);
        setAiPlan(plans[0] ?? null);
        setSelectedStepId(plans[0]?.steps[0]?.step_id ?? null);
      } catch {
        setLlmConfigs([]);
      }
    }
    void loadAiData();
  }, [selectedProjectId]);

  useEffect(() => {
    if (!selectedEndpoint) {
      setPathRows([]);
      setQueryRows([]);
      setBodyText("{}");
      return;
    }
    setPathRows(rowsFromParameters(selectedEndpoint.path_params));
    setQueryRows(rowsFromParameters(selectedEndpoint.query_params));
    setBodyText(shouldShowBody(selectedEndpoint.method) ? JSON.stringify(createBodyExample(selectedEndpoint.request_body_schema), null, 2) : "");
  }, [selectedEndpointId, selectedEndpoint]);

  async function runTest() {
    if (!selectedProjectId || !selectedEndpoint) return;
    setError(null);

    if (destructiveMethods.has(selectedEndpoint.method.toUpperCase())) {
      const confirmed = window.confirm(t.testRunner.destructiveConfirm);
      if (!confirmed) return;
    }

    let jsonBody: unknown = null;
    if (shouldShowBody(selectedEndpoint.method) && bodyText.trim()) {
      try {
        jsonBody = JSON.parse(bodyText);
      } catch {
        setError(t.testRunner.invalidJson);
        return;
      }
    }

    const validationErrors = validateRequiredInputs(
      selectedEndpoint,
      rowsToRecord(pathRows),
      rowsToRecord(queryRows),
      jsonBody
    );
    if (validationErrors.length > 0) {
      setError(`${t.testRunner.missingRequiredFields}: ${validationErrors.join(", ")}`);
      return;
    }

    const payload: TestRequestPayload = {
      path_params: rowsToRecord(pathRows),
      query_params: rowsToRecord(queryRows),
      headers: rowsToStringRecord(headerRows),
      bearer_token: bearerToken.trim() || null,
      json_body: shouldShowBody(selectedEndpoint.method) ? jsonBody : null
    };

    setLoading(true);
    try {
      const result = await runEndpointTest(selectedProjectId, selectedEndpoint.id, payload);
      setLatestRun(result);
      const [endpointData, runData] = await Promise.all([
        listEndpoints(selectedProjectId),
        listTestRuns(selectedProjectId)
      ]);
      setEndpoints(endpointData);
      setTestRuns(runData);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : t.testRunner.runFailed);
    } finally {
      setLoading(false);
    }
  }

  async function runValidation() {
    if (!selectedProjectId) return;
    if (validationIncludeDestructive || !validationSkipDestructive) {
      const confirmed = window.confirm(t.testRunner.destructiveValidationConfirm);
      if (!confirmed) return;
    }
    setValidationLoading(true);
    setError(null);
    try {
      const result = await createValidationRun(selectedProjectId, {
        name: validationName || null,
        endpoint_ids: validationScope === "selected" && selectedEndpointId ? [selectedEndpointId] : [],
        methods: [],
        skip_destructive: validationSkipDestructive,
        include_get: true,
        include_post: validationIncludePost,
        include_put_patch_delete: validationIncludeDestructive,
        use_ai_generated_params: false,
        max_endpoints: validationMaxEndpoints
      });
      setActiveValidationRun(result);
      const [runs, testRunData] = await Promise.all([
        listValidationRuns(selectedProjectId),
        listTestRuns(selectedProjectId)
      ]);
      setValidationRuns(runs);
      setTestRuns(testRunData);
      setLatestRun(testRunData[0] ?? latestRun);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : t.testRunner.validationLoadFailed);
    } finally {
      setValidationLoading(false);
    }
  }

  async function loadValidationRun(runId: number) {
    if (!selectedProjectId) return;
    setValidationLoading(true);
    setError(null);
    try {
      setActiveValidationRun(await getValidationRun(selectedProjectId, runId));
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : t.testRunner.validationLoadFailed);
    } finally {
      setValidationLoading(false);
    }
  }

  async function viewValidationTestRun(item: ValidationRunItem) {
    if (!selectedProjectId || !item.test_run_id) return;
    try {
      const run = await getTestRun(selectedProjectId, item.test_run_id);
      setLatestRun(run);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : t.testRunner.loadFailed);
    }
  }

  async function generateAiPlan() {
    if (!selectedProjectId || !selectedEndpoint || !selectedLlmConfigId) {
      setError(t.aiTest.noModel);
      return;
    }
    setAiLoading(true);
    setError(null);
    try {
      const response = await generateAITestPlan(
        selectedProjectId,
        selectedLlmConfigId,
        [selectedEndpoint.id],
        "single_endpoint"
      );
      if (response.plan) {
        setAiPlan(response.plan);
        setSelectedStepId(response.plan.steps[0]?.step_id ?? null);
        setAiLog([`${new Date().toLocaleTimeString()} ${t.aiTest.planGenerated}`]);
      }
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : t.common.error);
    } finally {
      setAiLoading(false);
    }
  }

  async function executeAiStep(step: AITestStep) {
    if (!selectedProjectId || !aiPlan) return;
    let confirmed = false;
    if (step.requires_confirmation || step.destructive) {
      confirmed = window.confirm(t.aiTest.confirmDestructive);
      if (!confirmed) return;
    }
    setAiLoading(true);
    setAiLog((current) => [...current, `${new Date().toLocaleTimeString()} running ${step.method} ${step.path}`]);
    try {
      const response = await executeAITestStep(selectedProjectId, aiPlan.plan_id, step.step_id, confirmed);
      setAiPlan(response.plan);
      setSelectedStepId(response.step.step_id);
      if (response.test_run) {
        setLatestRun(response.test_run);
        const runData = await listTestRuns(selectedProjectId);
        setTestRuns(runData);
      }
      setAiLog((current) => [...current, `${new Date().toLocaleTimeString()} ${response.step.status} ${step.step_id}`]);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : t.testRunner.runFailed);
    } finally {
      setAiLoading(false);
    }
  }

  async function executeAiPlan() {
    if (!aiPlan) return;
    for (const step of aiPlan.steps) {
      if (step.status === "passed" || step.status === "failed" || step.status === "skipped") continue;
      await executeAiStep(step);
    }
  }

  async function analyzeAiResults() {
    if (!selectedProjectId || !aiPlan) return;
    setAiLoading(true);
    try {
      const response = await analyzeAITestPlan(selectedProjectId, aiPlan.plan_id);
      setAiPlan(response.plan);
      setAiLog((current) => [...current, `${new Date().toLocaleTimeString()} ${t.aiTest.analysis}`]);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : t.common.error);
    } finally {
      setAiLoading(false);
    }
  }

  if (!selectedProjectId || !selectedProject) {
    return (
      <section className="page-stack">
        <PageHeader subtitle={t.placeholders.testRunnerSubtitle} title={t.placeholders.testRunnerTitle} />
        <Card>
          <div className="empty-panel">
            <h2>{t.testRunner.noProjectTitle}</h2>
            <p>{t.testRunner.noProjectDescription}</p>
            <button className="primary-button" onClick={() => onNavigate("setup")} type="button">
              {t.nav.projectSetup}
            </button>
          </div>
        </Card>
      </section>
    );
  }

  return (
    <section className="page-stack">
      <PageHeader
        actions={
          <button className="outline-button" disabled={loading} onClick={() => void refreshData()} type="button">
            {t.common.refresh}
          </button>
        }
        subtitle={t.placeholders.testRunnerSubtitle}
        title={t.placeholders.testRunnerTitle}
      />

      {error ? <div className="notice danger">{error}</div> : null}

      <div className="stat-grid four">
        <StatCard icon={ShieldCheck} title={t.testRunner.passedRuns} value={passedCount} hint={selectedProject.name} tone="green" />
        <StatCard icon={XCircle} title={t.testRunner.failedRuns} value={failedCount} hint={t.testRunner.recentRuns} tone="red" />
        <StatCard icon={Clock3} title={t.testRunner.avgResponseTime} value={avgResponseTime} hint={t.testRunner.recentRuns} tone="blue" />
        <StatCard icon={Code2} title={t.testRunner.availableEndpoints} value={endpoints.length} hint={selectedProject.name} tone="purple" />
      </div>

      <ValidationRunPanel
        activeRun={activeValidationRun}
        endpoints={endpoints}
        includeDestructive={validationIncludeDestructive}
        includePost={validationIncludePost}
        loading={validationLoading}
        maxEndpoints={validationMaxEndpoints}
        name={validationName}
        onIncludeDestructiveChange={setValidationIncludeDestructive}
        onIncludePostChange={setValidationIncludePost}
        onLoadRun={(runId) => void loadValidationRun(runId)}
        onMaxEndpointsChange={setValidationMaxEndpoints}
        onNameChange={setValidationName}
        onRun={() => void runValidation()}
        onScopeChange={setValidationScope}
        onSkipDestructiveChange={setValidationSkipDestructive}
        onViewTestRun={(item) => void viewValidationTestRun(item)}
        runs={validationRuns}
        scope={validationScope}
        selectedEndpointId={selectedEndpointId}
        skipDestructive={validationSkipDestructive}
        t={t}
      />

      <AISmartTestPanel
        aiLoading={aiLoading}
        aiLog={aiLog}
        aiPlan={aiPlan}
        latestRun={latestRun}
        llmConfigs={llmConfigs}
        onAnalyze={() => void analyzeAiResults()}
        onExecutePlan={() => void executeAiPlan()}
        onExecuteStep={(step) => void executeAiStep(step)}
        onGenerate={() => void generateAiPlan()}
        onSelectConfig={setSelectedLlmConfigId}
        onSelectStep={setSelectedStepId}
        selectedLlmConfigId={selectedLlmConfigId}
        selectedStep={selectedStep}
        t={t}
      />

      <div className="split-grid test">
        <Card>
          <div className="card-heading">
            <h2>{t.testRunner.requestSetup}</h2>
            <StatusBadge tone={loading ? "warning" : "info"}>
              {loading ? t.common.checking : selectedProject.name}
            </StatusBadge>
          </div>

          {endpoints.length === 0 ? (
            <div className="empty-panel compact">
              <h2>{t.testRunner.noEndpointsTitle}</h2>
              <p>{t.testRunner.noEndpointsDescription}</p>
              <button className="primary-button" onClick={() => onNavigate("apiMap")} type="button">
                {t.nav.apiMap}
              </button>
            </div>
          ) : (
            <div className="runner-form">
              <label className="form-field">
                {t.testRunner.endpoint}
                <select
                  value={selectedEndpointId ?? ""}
                  onChange={(event) => setSelectedEndpointId(Number(event.target.value))}
                >
                  {endpoints.map((endpoint) => (
                    <option key={endpoint.id} value={endpoint.id}>
                      {endpoint.method} {endpoint.path}
                    </option>
                  ))}
                </select>
              </label>

              <div className="runner-url-row">
                <StatusBadge tone={methodTone(selectedEndpoint?.method ?? "")}>{selectedEndpoint?.method ?? "-"}</StatusBadge>
                <code>{computedUrl}</code>
              </div>

              {selectedEndpoint && destructiveMethods.has(selectedEndpoint.method.toUpperCase()) ? (
                <div className="notice danger runner-warning">
                  <AlertTriangle size={16} />
                  {t.testRunner.destructiveWarning}
                </div>
              ) : null}

              <KeyValueEditor
                rows={pathRows}
                setRows={setPathRows}
                title={t.testRunner.pathParams}
                valuePlaceholder={t.testRunner.value}
              />
              <KeyValueEditor
                rows={queryRows}
                setRows={setQueryRows}
                title={t.testRunner.queryParams}
                valuePlaceholder={t.testRunner.value}
              />
              <KeyValueEditor
                rows={headerRows}
                setRows={setHeaderRows}
                title={t.testRunner.headers}
                valuePlaceholder={t.testRunner.value}
              />

              <label className="form-field">
                {t.testRunner.bearerToken}
                <input
                  onChange={(event) => setBearerToken(event.target.value)}
                  placeholder="eyJhbGci..."
                  type="password"
                  value={bearerToken}
                />
              </label>

              {selectedEndpoint && shouldShowBody(selectedEndpoint.method) ? (
                <label className="form-field">
                  {t.testRunner.jsonBody}
                  <textarea
                    className="json-editor"
                    onChange={(event) => setBodyText(event.target.value)}
                    spellCheck={false}
                    value={bodyText}
                  />
                </label>
              ) : null}

              <button
                className="primary-button full-width"
                disabled={loading || !selectedEndpoint}
                onClick={() => void runTest()}
                type="button"
              >
                <Play size={17} />
                {loading ? t.common.checking : t.testRunner.runTest}
              </button>
            </div>
          )}
        </Card>

        <ResultPanel latestRun={latestRun} t={t} />
      </div>

      <Card>
        <div className="card-heading">
          <h2>{t.testRunner.recentRuns}</h2>
          <StatusBadge tone="neutral">{testRuns.length}</StatusBadge>
        </div>
        {testRuns.length === 0 ? (
          <div className="empty-panel compact">{t.testRunner.noRuns}</div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>{t.apiMap.method}</th>
                <th>URL</th>
                <th>{t.apiMap.testStatus}</th>
                <th>{t.apiMap.lastStatus}</th>
                <th>{t.apiMap.latency}</th>
                <th>{t.testRunner.dbChangeSummary}</th>
                <th>{t.testRunner.createdAt}</th>
              </tr>
            </thead>
            <tbody>
              {testRuns.map((run) => (
                <tr key={run.id} onClick={() => setLatestRun(run)}>
                  <td><StatusBadge tone={methodTone(run.method)}>{run.method}</StatusBadge></td>
                  <td>{run.url}</td>
                  <td><StatusBadge tone={statusTone(run.status)}>{run.status}</StatusBadge></td>
                  <td>{run.http_status ?? "-"}</td>
                  <td>{run.response_time_ms != null ? `${run.response_time_ms} ms` : "-"}</td>
                  <td><DbChangesSummary dbChanges={run.db_changes} t={t} /></td>
                  <td>{new Date(run.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </section>
  );
}

function ValidationRunPanel({
  activeRun,
  endpoints,
  includeDestructive,
  includePost,
  loading,
  maxEndpoints,
  name,
  onIncludeDestructiveChange,
  onIncludePostChange,
  onLoadRun,
  onMaxEndpointsChange,
  onNameChange,
  onRun,
  onScopeChange,
  onSkipDestructiveChange,
  onViewTestRun,
  runs,
  scope,
  selectedEndpointId,
  skipDestructive,
  t
}: {
  activeRun: ValidationRunDetail | null;
  endpoints: Endpoint[];
  includeDestructive: boolean;
  includePost: boolean;
  loading: boolean;
  maxEndpoints: number;
  name: string;
  onIncludeDestructiveChange: (value: boolean) => void;
  onIncludePostChange: (value: boolean) => void;
  onLoadRun: (runId: number) => void;
  onMaxEndpointsChange: (value: number) => void;
  onNameChange: (value: string) => void;
  onRun: () => void;
  onScopeChange: (value: "all" | "selected") => void;
  onSkipDestructiveChange: (value: boolean) => void;
  onViewTestRun: (item: ValidationRunItem) => void;
  runs: ValidationRun[];
  scope: "all" | "selected";
  selectedEndpointId: number | null;
  skipDestructive: boolean;
  t: Messages;
}) {
  const [expandedItemIds, setExpandedItemIds] = useState<Set<number>>(new Set());
  const passRate = activeRun?.summary?.pass_rate;
  const passRateText = typeof passRate === "number" ? `${passRate}%` : activeRun?.total_count ? `${Math.round((activeRun.passed_count / activeRun.total_count) * 100)}%` : "0%";
  const toggleItem = (itemId: number) => {
    setExpandedItemIds((current) => {
      const next = new Set(current);
      if (next.has(itemId)) {
        next.delete(itemId);
      } else {
        next.add(itemId);
      }
      return next;
    });
  };

  return (
    <Card className="validation-panel">
      <div className="card-heading">
        <div>
          <h2>{t.testRunner.validationRun}</h2>
          <p>{t.testRunner.validationSubtitle}</p>
        </div>
        <StatusBadge tone={activeRun ? statusTone(activeRun.status) : "neutral"}>{activeRun?.status ?? t.common.idle}</StatusBadge>
      </div>

      <div className="notice info validation-explainer">
        <span>{t.testRunner.validationHowItWorks}</span>
      </div>

      <div className="validation-config-grid">
        <label className="form-field">
          {t.testRunner.validationName}
          <input value={name} onChange={(event) => onNameChange(event.target.value)} />
        </label>
        <label className="form-field">
          {t.testRunner.validationScope}
          <select value={scope} onChange={(event) => onScopeChange(event.target.value as "all" | "selected")}>
            <option value="all">{t.testRunner.allEndpoints}</option>
            <option value="selected" disabled={!selectedEndpointId}>{t.testRunner.selectedEndpoint}</option>
          </select>
        </label>
        <label className="form-field">
          {t.testRunner.maxEndpoints}
          <input
            min={1}
            max={100}
            onChange={(event) => onMaxEndpointsChange(Number(event.target.value) || 1)}
            type="number"
            value={maxEndpoints}
          />
        </label>
      </div>

      <div className="validation-option-row">
        <label className="checkbox-row">
          <input checked={skipDestructive} onChange={(event) => onSkipDestructiveChange(event.target.checked)} type="checkbox" />
          <span>{t.testRunner.skipDestructive}</span>
        </label>
        <label className="checkbox-row">
          <input checked={includePost} onChange={(event) => onIncludePostChange(event.target.checked)} type="checkbox" />
          <span>{t.testRunner.includePost}</span>
        </label>
        <label className="checkbox-row">
          <input checked={includeDestructive} onChange={(event) => onIncludeDestructiveChange(event.target.checked)} type="checkbox" />
          <span>{t.testRunner.includeDestructive}</span>
        </label>
        <button className="primary-button" disabled={loading || endpoints.length === 0} onClick={onRun} type="button">
          <Play size={17} />
          {loading ? t.common.checking : t.testRunner.runValidation}
        </button>
      </div>

      {activeRun ? (
        <>
          <div className="validation-summary-grid">
            <div><span>{t.testRunner.total}</span><strong>{activeRun.total_count}</strong></div>
            <div><span>{t.testRunner.passed}</span><strong>{activeRun.passed_count}</strong></div>
            <div><span>{t.testRunner.failed}</span><strong>{activeRun.failed_count}</strong></div>
            <div><span>{t.testRunner.skipped}</span><strong>{activeRun.skipped_count}</strong></div>
            <div><span>{t.testRunner.warnings}</span><strong>{activeRun.warning_count}</strong></div>
            <div><span>{t.reports.passRate}</span><strong>{passRateText}</strong></div>
          </div>

          <div className="card-heading compact-heading">
            <h3>{t.testRunner.validationItems}</h3>
            <StatusBadge tone="neutral">{activeRun.items.length}</StatusBadge>
          </div>
          <table className="data-table validation-table">
            <thead>
              <tr>
                <th>{t.apiMap.method}</th>
                <th>{t.apiMap.path}</th>
                <th>{t.apiMap.testStatus}</th>
                <th>{t.apiMap.lastStatus}</th>
                <th>{t.apiMap.latency}</th>
                <th>{t.testRunner.failureCategory}</th>
                <th>{t.testRunner.dbChangeSummary}</th>
                <th>{t.apiMap.actions}</th>
              </tr>
            </thead>
            <tbody>
              {activeRun.items.map((item) => (
                <Fragment key={item.id}>
                  <tr>
                    <td><StatusBadge tone={methodTone(item.method)}>{item.method}</StatusBadge></td>
                    <td>{item.path}</td>
                    <td><StatusBadge tone={statusTone(item.status)}>{item.status}</StatusBadge></td>
                    <td>{item.http_status ?? "-"}</td>
                    <td>{item.response_time_ms != null ? `${item.response_time_ms} ms` : "-"}</td>
                    <td>
                      {item.failure_category ? (
                        <StatusBadge tone={failureTone(item.failure_category)}>
                          {failureLabel(item.failure_category, t)}
                        </StatusBadge>
                      ) : "-"}
                    </td>
                    <td>{item.db_change_status ?? item.error_message ?? "-"}</td>
                    <td>
                      <div className="button-row compact-actions">
                        <button className="outline-button compact" onClick={() => toggleItem(item.id)} type="button">
                          {expandedItemIds.has(item.id) ? t.testRunner.collapseDetails : t.testRunner.expandDetails}
                        </button>
                        <button
                          className="outline-button compact"
                          disabled={!item.test_run_id}
                          onClick={() => onViewTestRun(item)}
                          type="button"
                        >
                          {t.testRunner.viewTestRun}
                        </button>
                      </div>
                    </td>
                  </tr>
                  {expandedItemIds.has(item.id) ? (
                    <tr className="validation-detail-row">
                      <td colSpan={8}>
                        <ValidationItemDetail item={item} t={t} />
                      </td>
                    </tr>
                  ) : null}
                </Fragment>
              ))}
            </tbody>
          </table>
        </>
      ) : (
        <div className="empty-panel compact">{t.testRunner.noValidationRuns}</div>
      )}

      <div className="card-heading compact-heading">
        <h3>{t.testRunner.validationHistory}</h3>
        <StatusBadge tone="neutral">{runs.length}</StatusBadge>
      </div>
      {runs.length ? (
        <div className="validation-history-row">
          {runs.map((run) => (
            <button
              className={activeRun?.id === run.id ? "validation-run-chip active" : "validation-run-chip"}
              key={run.id}
              onClick={() => onLoadRun(run.id)}
              type="button"
            >
              <strong>{run.name}</strong>
              <span>{run.passed_count}/{run.total_count} {run.status}</span>
            </button>
          ))}
        </div>
      ) : null}
    </Card>
  );
}

function ValidationItemDetail({ item, t }: { item: ValidationRunItem; t: Messages }) {
  return (
    <div className="validation-item-detail">
      <div className="validation-detail-summary">
        <div>
          <span>{t.testRunner.failureCategory}</span>
          <strong>{item.failure_category ? failureLabel(item.failure_category, t) : "-"}</strong>
        </div>
        <div>
          <span>{t.testRunner.failureReason}</span>
          <strong>{item.failure_reason ?? item.error_message ?? "-"}</strong>
        </div>
        <div>
          <span>{t.testRunner.suggestion}</span>
          <strong>{item.suggestion ?? "-"}</strong>
        </div>
      </div>
      <div className="validation-detail-grid">
        <DeveloperDataBlock title={t.testRunner.pathParamsGenerated} value={item.request_path_params} />
        <DeveloperDataBlock title={t.testRunner.queryParamsGenerated} value={item.request_query_params} />
        <DeveloperDataBlock title={t.testRunner.headersGenerated} value={item.request_headers} />
        <DeveloperDataBlock title={t.testRunner.bodyGenerated} value={item.request_body} />
        <DeveloperDataBlock title={t.testRunner.responseSummary} value={item.response_body_summary} />
        <DeveloperDataBlock title={t.testRunner.databaseChanges} value={item.db_changes} />
      </div>
    </div>
  );
}

function ResultPanel({ latestRun, t }: { latestRun: TestRun | null; t: Messages }) {
  if (!latestRun) {
    return (
      <Card>
        <div className="empty-panel">
          <h2>{t.testRunner.latestResult}</h2>
          <p>{t.testRunner.noResult}</p>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <div className="card-heading">
        <h2>{t.testRunner.latestResult}</h2>
        <StatusBadge tone={statusTone(latestRun.status)}>{latestRun.status}</StatusBadge>
      </div>
      <div className={`result-number ${latestRun.status === "failed" ? "failed" : ""}`}>
        {latestRun.http_status ?? "-"}
        <span>{latestRun.response_time_ms != null ? `${latestRun.response_time_ms} ms` : t.common.error}</span>
      </div>
      {latestRun.error_message ? <div className="notice danger">{latestRun.error_message}</div> : null}
      <ValidationFailurePanel responseBody={latestRun.response_body} statusCode={latestRun.http_status} t={t} />
      <DbChangesPanel dbChanges={latestRun.db_changes} t={t} />
      <SchemaBlock title={t.testRunner.responseBody} value={latestRun.response_body} />
      <SchemaBlock title={t.testRunner.responseHeaders} value={latestRun.response_headers} />
      <SchemaBlock title={t.testRunner.requestRecord} value={{
        headers: latestRun.request_headers,
        query: latestRun.request_query_params,
        path: latestRun.request_path_params,
        body: latestRun.request_body
      }} />
    </Card>
  );
}

function AISmartTestPanel({
  aiLoading,
  aiLog,
  aiPlan,
  latestRun,
  llmConfigs,
  onAnalyze,
  onExecutePlan,
  onExecuteStep,
  onGenerate,
  onSelectConfig,
  onSelectStep,
  selectedLlmConfigId,
  selectedStep,
  t
}: {
  aiLoading: boolean;
  aiLog: string[];
  aiPlan: AITestPlan | null;
  latestRun: TestRun | null;
  llmConfigs: LLMConfig[];
  onAnalyze: () => void;
  onExecutePlan: () => void;
  onExecuteStep: (step: AITestStep) => void;
  onGenerate: () => void;
  onSelectConfig: (configId: number | null) => void;
  onSelectStep: (stepId: string) => void;
  selectedLlmConfigId: number | null;
  selectedStep: AITestStep | null;
  t: Messages;
}) {
  return (
    <Card className="ai-test-panel ai-workspace-shell">
      <div className="card-heading ai-workspace-heading">
        <div>
          <h2>{t.aiTest.title}</h2>
          <p>{t.aiTest.subtitle}</p>
        </div>
        <StatusBadge tone={aiPlan ? riskTone(aiPlan.risk_level) : "neutral"}>
          {aiPlan?.risk_level ?? "idle"}
        </StatusBadge>
      </div>

      <div className="ai-test-toolbar">
        <label className="form-field compact-field">
          {t.aiTest.selectModel}
          <select
            value={selectedLlmConfigId ?? ""}
            onChange={(event) => onSelectConfig(event.target.value ? Number(event.target.value) : null)}
          >
            <option value="">{t.aiTest.noModel}</option>
            {llmConfigs.map((config) => (
              <option key={config.id} value={config.id}>
                {config.display_name} / {config.model_name}
              </option>
            ))}
          </select>
        </label>
        <button className="primary-button" disabled={aiLoading || !selectedLlmConfigId} onClick={onGenerate} type="button">
          {aiLoading ? <span className="button-spinner" /> : null}
          {aiLoading ? t.aiTest.generatingPlan : t.aiTest.generatePlan}
        </button>
        <button className="outline-button" disabled={aiLoading || !aiPlan} onClick={onExecutePlan} type="button">
          {t.aiTest.startExecution}
        </button>
        <button className="ghost-button" disabled={aiLoading || !aiPlan} onClick={onAnalyze} type="button">
          {t.aiTest.analyzeResults}
        </button>
      </div>

      {!aiPlan ? (
        <div className="empty-panel compact">{t.aiTest.noPlan}</div>
      ) : (
        <>
        <div className="ai-workspace-grid">
          <section className="ai-workspace-column ai-plan-column">
            <div className="ai-column-heading">
              <span>01</span>
              <div>
                <h3>{t.aiTest.steps}</h3>
                <p>{aiPlan.summary}</p>
              </div>
            </div>
            {aiPlan.steps.map((step) => (
              <button
                className={selectedStep?.step_id === step.step_id ? "ai-step active" : "ai-step"}
                key={step.step_id}
                onClick={() => onSelectStep(step.step_id)}
                type="button"
              >
                <div className="ai-step-main">
                  <div className="ai-step-route">
                    <StatusBadge tone={methodTone(step.method)}>{step.method}</StatusBadge>
                    <strong>{step.path}</strong>
                  </div>
                  <p>{step.purpose}</p>
                </div>
                <div className="ai-step-badges">
                  {step.destructive ? <StatusBadge tone="danger">{t.aiTest.destructive}</StatusBadge> : null}
                  <StatusBadge tone={statusTone(step.status)}>{step.status}</StatusBadge>
                </div>
              </button>
            ))}
          </section>

          <section className="ai-workspace-column ai-current-step-column">
            <div className="ai-column-heading">
              <span>02</span>
              <div>
                <h3>{t.aiTest.currentStep}</h3>
                <p>{t.aiTest.requestComposer}</p>
              </div>
            </div>
            {selectedStep ? (
              <>
                <div className="ai-step-summary-card">
                  <StatusBadge tone={methodTone(selectedStep.method)}>{selectedStep.method}</StatusBadge>
                  <div>
                    <strong>{selectedStep.path}</strong>
                    <p>{selectedStep.purpose}</p>
                  </div>
                </div>
                {(selectedStep.destructive || selectedStep.requires_confirmation) ? (
                  <div className="notice danger ai-danger-card">
                    <AlertTriangle size={16} />
                    {t.testRunner.destructiveWarning}
                  </div>
                ) : null}
                <div className="button-row ai-risk-row">
                  {selectedStep.destructive ? <StatusBadge tone="danger">{t.aiTest.destructive}</StatusBadge> : null}
                  {selectedStep.requires_confirmation ? <StatusBadge tone="warning">{t.aiTest.requiresConfirmation}</StatusBadge> : null}
                  {selectedStep.needs_user_input ? <StatusBadge tone="warning">{t.aiTest.needsInput}</StatusBadge> : null}
                  <StatusBadge tone="info">{t.aiTest.expectedStatus}: {selectedStep.expected_status ?? "-"}</StatusBadge>
                </div>
                <DeveloperDataBlock title={t.testRunner.pathParams} value={selectedStep.path_params} />
                <DeveloperDataBlock title={t.testRunner.queryParams} value={selectedStep.query_params} />
                <DeveloperDataBlock title={t.testRunner.headers} value={selectedStep.headers} />
                <DeveloperDataBlock title={t.testRunner.jsonBody} value={selectedStep.body} />
                <DeveloperDataBlock title={t.aiTest.expectedAssertions} value={selectedStep.expected_response_assertions} />
                <div className="button-row">
                  <button className="primary-button" disabled={aiLoading} onClick={() => onExecuteStep(selectedStep)} type="button">
                    {t.aiTest.executeStep}
                  </button>
                  <button className="ghost-button" disabled type="button">
                    {t.aiTest.skipStep}
                  </button>
                </div>
              </>
            ) : (
              <div className="empty-panel compact">{t.aiTest.noPlan}</div>
            )}
          </section>

          <section className="ai-workspace-column ai-result-column">
            <div className="ai-column-heading">
              <span>03</span>
              <div>
                <h3>{t.aiTest.executionResult}</h3>
                <p>{t.aiTest.analysis}</p>
              </div>
            </div>
            {latestRun ? (
              <>
                <div className="ai-result-meter">
                  <strong>{latestRun.http_status ?? "-"}</strong>
                  <span>{latestRun.response_time_ms != null ? `${latestRun.response_time_ms} ms` : t.common.error}</span>
                  <StatusBadge tone={statusTone(latestRun.status)}>{latestRun.status}</StatusBadge>
                </div>
                <DbChangesPanel dbChanges={latestRun.db_changes} t={t} />
                <DeveloperDataBlock title={t.testRunner.responseBody} value={latestRun.response_body} />
              </>
            ) : (
              <div className="empty-panel compact">{t.aiTest.pendingExecution}</div>
            )}
            {selectedStep?.ai_explanation ? (
              <div className="notice success">
                <strong>{t.aiTest.aiExplanation}</strong>
                <p>{selectedStep.ai_explanation}</p>
              </div>
            ) : null}
            {aiPlan.analysis ? (
              <div className="notice success">
                <strong>{t.aiTest.analysis}</strong>
                <p>{aiPlan.analysis}</p>
              </div>
            ) : null}
          </section>
        </div>
        <ExecutionTimeline aiLog={aiLog} t={t} />
        </>
      )}
    </Card>
  );
}

function DeveloperDataBlock({ title, value }: { title: string; value: unknown }) {
  return (
    <section className="developer-data-block">
      <div className="developer-data-title">
        <span>{title}</span>
      </div>
      <pre>{formatValue(value)}</pre>
    </section>
  );
}

function ExecutionTimeline({ aiLog, t }: { aiLog: string[]; t: Messages }) {
  const stages = [
    t.aiTest.timelineAnalyzing,
    t.aiTest.timelineGenerating,
    t.aiTest.timelineWaitingConfirmation,
    t.aiTest.timelineSending,
    t.aiTest.timelineReceiving,
    t.aiTest.timelineComparingDb,
    t.aiTest.timelineAnalyzingResults
  ];

  return (
    <section className="execution-timeline">
      <div className="card-heading">
        <h3>{t.aiTest.timeline}</h3>
        <StatusBadge tone="neutral">{aiLog.length}</StatusBadge>
      </div>
      <div className="timeline-stage-row">
        {stages.map((stage, index) => (
          <div className={index <= Math.min(aiLog.length, stages.length - 1) ? "timeline-stage active" : "timeline-stage"} key={stage}>
            <span>{index + 1}</span>
            <strong>{stage}</strong>
          </div>
        ))}
      </div>
      <div className="ai-log">
        {aiLog.length === 0 ? <p>-</p> : aiLog.map((item) => <p key={item}>{item}</p>)}
      </div>
    </section>
  );
}

function DbChangesPanel({ dbChanges, t }: { dbChanges?: DbChanges; t: Messages }) {
  if (!dbChanges) return null;

  if (dbChanges.status === "skipped") {
    return (
      <div className="db-change-panel skipped">
        <div className="card-heading">
          <h2>{t.testRunner.databaseChanges}</h2>
          <StatusBadge tone="warning">{t.testRunner.skipped}</StatusBadge>
        </div>
        <p>{dbChanges.warning_message || t.testRunner.databaseChangesSkipped}</p>
      </div>
    );
  }

  if (dbChanges.status === "error") {
    return (
      <div className="db-change-panel error">
        <div className="card-heading">
          <h2>{t.testRunner.databaseChanges}</h2>
          <StatusBadge tone="danger">{t.common.error}</StatusBadge>
        </div>
        <p>{dbChanges.warning_message || t.testRunner.databaseChangesError}</p>
      </div>
    );
  }

  if (!dbChanges.changed) {
    return (
      <div className="db-change-panel">
        <div className="card-heading">
          <h2>{t.testRunner.databaseChanges}</h2>
          <StatusBadge tone="neutral">{t.testRunner.noChanges}</StatusBadge>
        </div>
        <p>{t.testRunner.noDatabaseChanges}</p>
      </div>
    );
  }

  return (
    <div className="db-change-panel changed">
      <div className="card-heading">
        <h2>{t.testRunner.databaseChanges}</h2>
        <StatusBadge tone="success">
          {dbChanges.tables_modified.length} {t.testRunner.changedTables}
        </StatusBadge>
      </div>

      <div className="db-change-grid">
        <ChangeList title={t.testRunner.tablesAdded} values={dbChanges.tables_added} />
        <ChangeList title={t.testRunner.tablesRemoved} values={dbChanges.tables_removed} />
      </div>

      {Object.keys(dbChanges.row_count_diff).length > 0 ? (
        <section className="detail-section">
          <h3 className="schema-title">{t.testRunner.rowCountChanges}</h3>
          <table className="data-table">
            <thead>
              <tr>
                <th>Table</th>
                <th>Before</th>
                <th>After</th>
                <th>Diff</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(dbChanges.row_count_diff).map(([table, diff]) => (
                <tr key={table}>
                  <td>{table}</td>
                  <td>{diff.before}</td>
                  <td>{diff.after}</td>
                  <td>{diff.diff > 0 ? `+${diff.diff}` : diff.diff}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ) : null}

      {Object.keys(dbChanges.schema_diff).length > 0 ? (
        <SchemaBlock title={t.testRunner.schemaChanges} value={dbChanges.schema_diff} />
      ) : null}

      {Object.keys(dbChanges.sample_diff).length > 0 ? (
        <SchemaBlock title={t.testRunner.sampleChanges} value={dbChanges.sample_diff} />
      ) : null}
    </div>
  );
}

function DbChangesSummary({ dbChanges, t }: { dbChanges?: DbChanges; t: Messages }) {
  if (!dbChanges) return <StatusBadge tone="neutral">-</StatusBadge>;
  if (dbChanges.status === "error") return <StatusBadge tone="danger">{t.common.error}</StatusBadge>;
  if (dbChanges.status === "skipped") return <StatusBadge tone="warning">{t.testRunner.skipped}</StatusBadge>;
  if (!dbChanges.changed) return <StatusBadge tone="neutral">{t.testRunner.noChanges}</StatusBadge>;
  return <StatusBadge tone="success">{dbChanges.tables_modified.length}</StatusBadge>;
}

function ChangeList({ title, values }: { title: string; values: string[] }) {
  return (
    <section className="db-change-list">
      <strong>{title}</strong>
      {values.length ? (
        <div>
          {values.map((value) => (
            <span key={value}>{value}</span>
          ))}
        </div>
      ) : (
        <p>-</p>
      )}
    </section>
  );
}

function ValidationFailurePanel({
  responseBody,
  statusCode,
  t
}: {
  responseBody: unknown;
  statusCode?: number | null;
  t: Messages;
}) {
  const details = extractValidationDetails(responseBody);
  if (statusCode !== 422) return null;

  return (
    <div className="validation-panel">
      <strong>{t.testRunner.validationFailed}</strong>
      {details.length > 0 ? (
        <ul>
          {details.map((detail, index) => (
            <li key={`${detail.location}-${index}`}>
              <code>{detail.location}</code>
              <span>{detail.message}</span>
              <em>{detail.type}</em>
            </li>
          ))}
        </ul>
      ) : (
        <p>{t.testRunner.validationFailedDescription}</p>
      )}
    </div>
  );
}

function KeyValueEditor({
  rows,
  setRows,
  title,
  valuePlaceholder
}: {
  rows: KeyValueRow[];
  setRows: (rows: KeyValueRow[]) => void;
  title: string;
  valuePlaceholder: string;
}) {
  return (
    <section className="key-value-editor">
      <div className="section-heading">
        <h2>{title}</h2>
        <button className="ghost-button compact" onClick={() => setRows([...rows, { id: createId(), key: "", value: "" }])} type="button">
          +
        </button>
      </div>
      <div className="key-value-rows">
        {rows.map((row) => (
          <div className="key-value-row" key={row.id}>
            <input
              onChange={(event) => updateRow(rows, setRows, row.id, "key", event.target.value)}
              placeholder="key"
              value={row.key}
            />
            <input
              onChange={(event) => updateRow(rows, setRows, row.id, "value", event.target.value)}
              placeholder={valuePlaceholder}
              value={row.value}
            />
            <button
              className="icon-only"
              onClick={() => setRows(rows.filter((item) => item.id !== row.id))}
              type="button"
            >
              ×
            </button>
          </div>
        ))}
      </div>
    </section>
  );
}

function SchemaBlock({ title, value }: { title: string; value: unknown }) {
  return (
    <section className="detail-section">
      <h3 className="schema-title">{title}</h3>
      <div className="code-block">{formatValue(value)}</div>
    </section>
  );
}

function rowsFromParameters(parameters: Record<string, unknown>[]): KeyValueRow[] {
  const rows = parameters
    .map((parameter) => ({
      id: createId(),
      key: typeof parameter.name === "string" ? parameter.name : "",
      value: stringifyFormValue(sampleValue(readSchema(parameter.schema)))
    }))
    .filter((row) => row.key);
  return rows.length ? rows : [{ id: createId(), key: "", value: "" }];
}

function rowsToRecord(rows: KeyValueRow[]): Record<string, unknown> {
  return rows.reduce<Record<string, unknown>>((record, row) => {
    if (row.key.trim()) record[row.key.trim()] = coerceValue(row.value);
    return record;
  }, {});
}

function rowsToStringRecord(rows: KeyValueRow[]): Record<string, string> {
  return rows.reduce<Record<string, string>>((record, row) => {
    if (row.key.trim()) record[row.key.trim()] = row.value;
    return record;
  }, {});
}

function updateRow(
  rows: KeyValueRow[],
  setRows: (rows: KeyValueRow[]) => void,
  id: string,
  field: "key" | "value",
  value: string
) {
  setRows(rows.map((row) => (row.id === id ? { ...row, [field]: value } : row)));
}

function createBodyExample(schema: Record<string, unknown>): unknown {
  return sampleValue(schema);
}

function sampleValue(schema: Record<string, unknown>): unknown {
  if ("example" in schema) return schema.example;
  if ("default" in schema) return schema.default;
  if (schema.format === "uuid") return "00000000-0000-0000-0000-000000000000";
  if (schema.format === "date-time") return new Date().toISOString();
  if (schema.format === "date") return "2026-05-09";
  if (schema.type === "integer" || schema.type === "number") return 1;
  if (schema.type === "boolean") return true;
  if (schema.type === "array") return [];
  if (schema.type === "object" || isObjectSchema(schema)) return sampleObject(schema);
  return "string";
}

function sampleObject(schema: Record<string, unknown>): Record<string, unknown> {
  const properties = schema.properties;
  if (!isRecord(properties)) return {};
  return Object.entries(properties).reduce<Record<string, unknown>>((example, [key, value]) => {
    example[key] = sampleValue(readSchema(value));
    return example;
  }, {});
}

function validateRequiredInputs(
  endpoint: Endpoint,
  pathParams: Record<string, unknown>,
  queryParams: Record<string, unknown>,
  jsonBody: unknown
): string[] {
  const missing: string[] = [];
  for (const parameter of endpoint.path_params) {
    const name = typeof parameter.name === "string" ? parameter.name : "";
    if (name && (parameter.required === true || endpoint.path.includes(`{${name}}`)) && isEmptyValue(pathParams[name])) {
      missing.push(`path.${name}`);
    }
  }
  for (const parameter of endpoint.query_params) {
    const name = typeof parameter.name === "string" ? parameter.name : "";
    if (name && parameter.required === true && isEmptyValue(queryParams[name])) {
      missing.push(`query.${name}`);
    }
  }
  if (shouldShowBody(endpoint.method)) {
    missing.push(...missingRequiredBodyFields(endpoint.request_body_schema, jsonBody, "body"));
  }
  return missing;
}

function missingRequiredBodyFields(schema: Record<string, unknown>, value: unknown, prefix: string): string[] {
  const required = Array.isArray(schema.required) ? schema.required.filter((item): item is string => typeof item === "string") : [];
  if (!required.length) return [];
  if (!isRecord(value)) return required.map((field) => `${prefix}.${field}`);
  const properties = isRecord(schema.properties) ? schema.properties : {};
  return required.flatMap((field) => {
    const fieldPath = `${prefix}.${field}`;
    if (isEmptyValue(value[field])) return [fieldPath];
    const childSchema = readSchema(properties[field]);
    if (isObjectSchema(childSchema)) {
      return missingRequiredBodyFields(childSchema, value[field], fieldPath);
    }
    return [];
  });
}

function extractValidationDetails(responseBody: unknown): Array<{ location: string; message: string; type: string }> {
  if (!isRecord(responseBody) || !Array.isArray(responseBody.detail)) return [];
  return responseBody.detail
    .map((detail) => {
      if (!isRecord(detail)) return null;
      const loc = Array.isArray(detail.loc) ? detail.loc.map(String).join(".") : "request";
      return {
        location: loc,
        message: typeof detail.msg === "string" ? detail.msg : "Validation error",
        type: typeof detail.type === "string" ? detail.type : "-"
      };
    })
    .filter((detail): detail is { location: string; message: string; type: string } => detail !== null);
}

function readSchema(value: unknown): Record<string, unknown> {
  return isRecord(value) ? value : {};
}

function isObjectSchema(schema: Record<string, unknown>): boolean {
  return schema.type === "object" || isRecord(schema.properties);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isEmptyValue(value: unknown): boolean {
  return value === undefined || value === null || value === "";
}

function stringifyFormValue(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return JSON.stringify(value);
}

function coerceValue(value: string): unknown {
  if (value === "true") return true;
  if (value === "false") return false;
  if (value.trim() !== "" && !Number.isNaN(Number(value))) return Number(value);
  return value;
}

function shouldShowBody(method: string): boolean {
  return ["POST", "PUT", "PATCH", "DELETE"].includes(method.toUpperCase());
}

function joinUrl(baseUrl: string, path: string): string {
  return `${baseUrl.replace(/\/+$/, "")}/${path.replace(/^\/+/, "")}`;
}

function createId(): string {
  return Math.random().toString(36).slice(2);
}

function formatValue(value: unknown): string {
  if (typeof value === "string") return value;
  return JSON.stringify(value ?? null, null, 2);
}

function methodTone(method: string): StatusTone {
  if (method === "GET") return "info";
  if (method === "POST") return "success";
  if (method === "PUT" || method === "PATCH") return "warning";
  if (method === "DELETE") return "danger";
  return "neutral";
}

function statusTone(status: string): StatusTone {
  if (status === "passed") return "success";
  if (status === "failed") return "danger";
  if (status === "skipped") return "warning";
  if (status === "running") return "info";
  return "neutral";
}

function failureTone(category: string): StatusTone {
  if (category === "server_error" || category === "permission_denied" || category === "network_error") return "danger";
  if (
    category === "validation_error" ||
    category === "auth_required" ||
    category === "not_found" ||
    category === "needs_user_input" ||
    category === "skipped_safety"
  ) {
    return "warning";
  }
  return "neutral";
}

function failureLabel(category: string, t: Messages): string {
  const labels: Record<string, string> = {
    validation_error: t.testRunner.categoryValidationError,
    auth_required: t.testRunner.categoryAuthRequired,
    permission_denied: t.testRunner.categoryPermissionDenied,
    not_found: t.testRunner.categoryNotFound,
    server_error: t.testRunner.categoryServerError,
    skipped_safety: t.testRunner.categorySkippedSafety,
    needs_user_input: t.testRunner.categoryNeedsUserInput,
    network_error: t.testRunner.categoryNetworkError,
    unknown: t.testRunner.categoryUnknown
  };
  return labels[category] ?? t.testRunner.categoryUnknown;
}

function riskTone(risk: string): StatusTone {
  if (risk === "high") return "danger";
  if (risk === "medium") return "warning";
  if (risk === "low") return "success";
  return "neutral";
}
