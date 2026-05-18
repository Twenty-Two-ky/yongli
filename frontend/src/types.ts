export interface Environment {
  id: number; name: string; base_url: string; auth_config: any; default_headers: any;
  health_check_path: string; status: string; last_health_check: string | null; created_at: string;
}
export interface Worker {
  id: number; name: string; status: string; current_task_id: number | null;
  last_heartbeat: string | null; registered_at: string;
}
export interface Task {
  id: number; natural_language: string; status: string; task_type: string | null;
  parsed_actions: any; environment_id: number; worker_id: number | null;
  success_count: number; fail_count: number; total_count: number;
  avg_latency_ms: number; p50_latency_ms: number; p95_latency_ms: number; p99_latency_ms: number;
  min_latency_ms: number; max_latency_ms: number; error_rate: number;
  ai_analysis: any; created_at: string; started_at: string | null; completed_at: string | null;
  environment: Environment | null; worker: Worker | null; timeline: TimelineEvent[];
}
export interface TimelineEvent { event: string; time: string; }
export interface TaskResult {
  id: number; task_id: number; step_index: number | null; method: string; url: string;
  request_body: string | null; request_headers: any; status_code: number | null;
  response_body: string | null; latency_ms: number | null; error_message: string | null;
  is_success: boolean; created_at: string;
}
export interface StatsSummary {
  total_tasks: number; today_tasks: number; overall_success_rate: number;
  avg_latency_ms: number; failed_tasks: number;
}
export interface PaginatedResponse<T> {
  items: T[]; total: number; page: number; page_size: number; has_next: boolean;
}
