from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel

# ── Environment ──
class AuthConfig(BaseModel):
    login_path: str = "/api/v1/login"
    default_credentials: dict = {}
    auth_type: str = "bearer"

class EnvironmentCreate(BaseModel):
    name: str
    base_url: str
    auth_config: AuthConfig = AuthConfig()
    default_headers: dict = {}
    health_check_path: str = "/api/v1/health"

class EnvironmentUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    auth_config: Optional[AuthConfig] = None
    default_headers: Optional[dict] = None
    health_check_path: Optional[str] = None

class EnvironmentOut(BaseModel):
    id: int
    name: str
    base_url: str
    auth_config: dict
    default_headers: dict
    health_check_path: str
    status: str
    last_health_check: Optional[datetime] = None
    created_at: datetime
    class Config: from_attributes = True

# ── Worker ──
class WorkerRegister(BaseModel):
    name: str

class WorkerOut(BaseModel):
    id: int
    name: str
    status: str
    current_task_id: Optional[int] = None
    last_heartbeat: Optional[datetime] = None
    registered_at: datetime
    class Config: from_attributes = True

# ── Task ──
class TaskCreate(BaseModel):
    natural_language: str
    environment_id: Optional[int] = None

class TaskOut(BaseModel):
    id: int
    natural_language: str
    status: str
    task_type: Optional[str] = None
    parsed_actions: Optional[Any] = None
    environment_id: int
    worker_id: Optional[int] = None
    success_count: int
    fail_count: int
    total_count: int
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    error_rate: float
    ai_analysis: Optional[Any] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    environment: Optional[EnvironmentOut] = None
    worker: Optional[WorkerOut] = None
    timeline: list[dict] = []
    class Config: from_attributes = True

class TaskListOut(BaseModel):
    items: list[TaskOut]
    total: int
    page: int
    page_size: int
    has_next: bool

# ── Task Result ──
class TaskResultOut(BaseModel):
    id: int
    task_id: int
    step_index: Optional[int] = None
    method: str
    url: str
    request_body: Optional[str] = None
    request_headers: Optional[dict] = None
    status_code: Optional[int] = None
    response_body: Optional[str] = None
    latency_ms: Optional[float] = None
    error_message: Optional[str] = None
    is_success: bool
    created_at: datetime
    class Config: from_attributes = True

class TaskResultListOut(BaseModel):
    items: list[TaskResultOut]
    total: int
    page: int
    page_size: int
    has_next: bool

# ── Worker: result submission ──
class AggregatedStats(BaseModel):
    success_count: int = 0
    fail_count: int = 0
    total_count: int = 0
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    error_rate: float = 0.0

class ResultItem(BaseModel):
    step_index: Optional[int] = None
    method: str
    url: str
    request_body: Optional[str] = None
    request_headers: Optional[dict] = None
    status_code: Optional[int] = None
    response_body: Optional[str] = None
    latency_ms: Optional[float] = None
    error_message: Optional[str] = None
    is_success: bool

class ResultSubmit(BaseModel):
    aggregated: AggregatedStats = AggregatedStats()
    results: list[ResultItem] = []
    final: bool = False

# ── Stats ──
class StatsSummary(BaseModel):
    total_tasks: int
    today_tasks: int
    overall_success_rate: float
    avg_latency_ms: float
    failed_tasks: int
