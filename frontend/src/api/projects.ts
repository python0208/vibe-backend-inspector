import { apiRequest } from "./client";
import type { Project, ProjectListItem, ProjectPayload } from "../types/project";

export function listProjects(): Promise<ProjectListItem[]> {
  return apiRequest<ProjectListItem[]>("/api/projects");
}

export function getProject(id: number): Promise<Project> {
  return apiRequest<Project>(`/api/projects/${id}`);
}

export function createProject(payload: ProjectPayload): Promise<Project> {
  return apiRequest<Project>("/api/projects", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateProject(id: number, payload: ProjectPayload): Promise<Project> {
  return apiRequest<Project>(`/api/projects/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function deleteProject(id: number): Promise<void> {
  return apiRequest<void>(`/api/projects/${id}`, {
    method: "DELETE"
  });
}
