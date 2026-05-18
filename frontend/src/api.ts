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
  createTask: (body: { natural_language: string; environment_id?: number }) => post('/tasks', body),
  getTasks: (params?: Record<string, string>) => get('/tasks?' + new URLSearchParams(params).toString()),
  getTask: (id: number) => get('/tasks/' + id),
  deleteTask: (id: number) => del('/tasks/' + id),
  cancelTask: (id: number) => post('/tasks/' + id + '/cancel'),
  rerunTask: (id: number, envId?: number) => post('/tasks/' + id + '/rerun' + (envId ? '?environment_id=' + envId : '')),
  getTaskResults: (id: number, page = 1) => get('/tasks/' + id + '/results?page=' + page + '&page_size=50'),
  getStats: () => get('/stats/summary'),
  // Environments
  getEnvironments: () => get('/environments'),
  createEnvironment: (body: any) => post('/environments', body),
  updateEnvironment: (id: number, body: any) => put('/environments/' + id, body),
  deleteEnvironment: (id: number) => del('/environments/' + id),
  checkEnvironment: (id: number) => post('/environments/' + id + '/check'),
  // Workers
  getWorkers: () => get('/workers'),
  // SSE
  taskStream: (id: number): EventSource => new EventSource(BASE + '/tasks/' + id + '/stream'),
};
