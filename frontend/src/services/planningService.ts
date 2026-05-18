import { apiRequest } from "../lib/api";
import type { Task, TaskPayload } from "../types/task";

export function listPlanningTasks(): Promise<Task[]> {
  return apiRequest<Task[]>("/planning/tasks");
}

export function createPlanningTask(payload: TaskPayload): Promise<Task> {
  return apiRequest<Task>("/planning/tasks", {
    method: "POST",
    body: payload,
  });
}

export function updatePlanningTask(taskId: number, payload: TaskPayload): Promise<Task> {
  return apiRequest<Task>(`/planning/tasks/${taskId}`, {
    method: "PATCH",
    body: payload,
  });
}

export function deletePlanningTask(taskId: number): Promise<void> {
  return apiRequest<void>(`/planning/tasks/${taskId}`, {
    method: "DELETE",
  });
}
