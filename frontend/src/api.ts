import { Environment, Worker, Task, TaskResult, StatsSummary, PaginatedResponse } from './types'

const BASE = '/api';
async function get<T>(url: string): Promise<T> {
  const r = await fetch(BASE + url); if (!r.ok) throw new Error(r.statusText); return r.json();
}
async function post<T>(url: string, body?: any): Promise<T> {
  const r = await fetch(BASE + url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined });
  if (!r.ok) throw new Error(r.statusText); return r.json();
}
async function put<T>(url: string, body: any): Promise<T> {
  const r = await fetch(BASE + url, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  if (!r.ok) throw new Error(r.statusText); return r.json();
}
async function del(url: string): Promise<void> {
  const r = await fetch(BASE + url, { method: 'DELETE' }); if (!r.ok) throw new Error(r.statusText);
}
export const api = {
  // Tasks
  createTask: (body: { natural_language: string; environment_id?: number }): Promise<Task> => post<Task>('/tasks', body),
  getTasks: (params?: Record<string, string>): Promise<PaginatedResponse<Task>> => get<PaginatedResponse<Task>>('/tasks?' + new URLSearchParams(params).toString()),
  getTask: (id: number): Promise<Task> => get<Task>('/tasks/' + id),
  deleteTask: (id: number): Promise<void> => del('/tasks/' + id),
  cancelTask: (id: number): Promise<Task> => post<Task>('/tasks/' + id + '/cancel'),
  rerunTask: (id: number, envId?: number): Promise<Task> => post<Task>('/tasks/' + id + '/rerun' + (envId ? '?environment_id=' + envId : '')),
  getTaskResults: (id: number, page = 1): Promise<PaginatedResponse<TaskResult>> => get<PaginatedResponse<TaskResult>>('/tasks/' + id + '/results?page=' + page + '&page_size=50'),
  getStats: (): Promise<StatsSummary> => get<StatsSummary>('/stats/summary'),
  // Environments
  getEnvironments: (): Promise<Environment[]> => get<Environment[]>('/environments'),
  createEnvironment: (body: any): Promise<Environment> => post<Environment>('/environments', body),
  updateEnvironment: (id: number, body: any): Promise<Environment> => put<Environment>('/environments/' + id, body),
  deleteEnvironment: (id: number): Promise<void> => del('/environments/' + id),
  checkEnvironment: (id: number): Promise<Environment> => post<Environment>('/environments/' + id + '/check'),
  // Workers
  getWorkers: (): Promise<Worker[]> => get<Worker[]>('/workers'),
  // SSE
  taskStream: (id: number): EventSource => new EventSource(BASE + '/tasks/' + id + '/stream'),
};
