import { API_BASE_URL, apiRequest } from "./client";
import type { LatestReportResponse, Report, ReportSummary } from "../types/report";

export function getReportSummary(projectId: number): Promise<ReportSummary> {
  return apiRequest<ReportSummary>(`/api/projects/${projectId}/reports/summary`);
}

export function getLatestReport(projectId: number): Promise<LatestReportResponse> {
  return apiRequest<LatestReportResponse>(`/api/projects/${projectId}/reports/latest`);
}

export function generateReport(projectId: number): Promise<Report> {
  return apiRequest<Report>(`/api/projects/${projectId}/reports/generate`, {
    method: "POST"
  });
}

export function getReport(projectId: number, reportId: number): Promise<Report> {
  return apiRequest<Report>(`/api/projects/${projectId}/reports/${reportId}`);
}

export async function downloadReportMarkdown(projectId: number, reportId: number): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/api/projects/${projectId}/reports/${reportId}/markdown`);
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }
  return response.blob();
}
