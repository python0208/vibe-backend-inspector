import { apiRequest } from "./client";
import type { Endpoint, EndpointDeleteResult, EndpointDiscoveryResult, EndpointMutationPayload } from "../types/api";

export function discoverOpenApi(projectId: number): Promise<EndpointDiscoveryResult> {
  return apiRequest<EndpointDiscoveryResult>(`/api/projects/${projectId}/openapi/discover`, {
    method: "POST"
  });
}

export function autoDetectOpenApi(projectId: number): Promise<EndpointDiscoveryResult> {
  return apiRequest<EndpointDiscoveryResult>(`/api/projects/${projectId}/openapi/auto-detect`, {
    method: "POST"
  });
}

export function importOpenApiFile(projectId: number, file: File): Promise<EndpointDiscoveryResult> {
  const formData = new FormData();
  formData.append("file", file);
  return apiRequest<EndpointDiscoveryResult>(`/api/projects/${projectId}/openapi/import-file`, {
    body: formData,
    method: "POST"
  });
}

export function listEndpoints(projectId: number): Promise<Endpoint[]> {
  return apiRequest<Endpoint[]>(`/api/projects/${projectId}/endpoints`);
}

export function getEndpoint(projectId: number, endpointId: number): Promise<Endpoint> {
  return apiRequest<Endpoint>(`/api/projects/${projectId}/endpoints/${endpointId}`);
}

export function createEndpoint(projectId: number, payload: EndpointMutationPayload): Promise<Endpoint> {
  return apiRequest<Endpoint>(`/api/projects/${projectId}/endpoints`, {
    body: JSON.stringify(payload),
    method: "POST"
  });
}

export function updateEndpoint(
  projectId: number,
  endpointId: number,
  payload: EndpointMutationPayload
): Promise<Endpoint> {
  return apiRequest<Endpoint>(`/api/projects/${projectId}/endpoints/${endpointId}`, {
    body: JSON.stringify(payload),
    method: "PUT"
  });
}

export function deleteEndpoint(projectId: number, endpointId: number): Promise<EndpointDeleteResult> {
  return apiRequest<EndpointDeleteResult>(`/api/projects/${projectId}/endpoints/${endpointId}`, {
    method: "DELETE"
  });
}
