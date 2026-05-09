import { apiRequest } from "./client";
import type { Endpoint, EndpointDiscoveryResult } from "../types/api";

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

export function listEndpoints(projectId: number): Promise<Endpoint[]> {
  return apiRequest<Endpoint[]>(`/api/projects/${projectId}/endpoints`);
}

export function getEndpoint(projectId: number, endpointId: number): Promise<Endpoint> {
  return apiRequest<Endpoint>(`/api/projects/${projectId}/endpoints/${endpointId}`);
}
