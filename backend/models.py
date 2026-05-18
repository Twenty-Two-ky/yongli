from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Environment(Base):
    __tablename__ = "environments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    base_url = Column(String(500), nullable=False)
    auth_config = Column(JSON, default=dict)
    default_headers = Column(JSON, default=dict)
    health_check_path = Column(String(200), default="/api/v1/health")
    status = Column(String(20), default="offline")
    last_health_check = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    tasks = relationship("Task", back_populates="environment")


class Worker(Base):
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    status = Column(String(20), default="offline")
    current_task_id = Column(Integer, nullable=True)
    last_heartbeat = Column(DateTime, nullable=True)
    registered_at = Column(DateTime, default=utcnow)

    tasks = relationship("Task", back_populates="worker")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    natural_language = Column(Text, nullable=False)
    status = Column(String(20), default="parsing")
    task_type = Column(String(20), nullable=True)
    parsed_actions = Column(JSON, nullable=True)
    environment_id = Column(Integer, ForeignKey("environments.id"), nullable=False)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=True)
    success_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    total_count = Column(Integer, default=0)
    avg_latency_ms = Column(Float, default=0.0)
    p50_latency_ms = Column(Float, default=0.0)
    p95_latency_ms = Column(Float, default=0.0)
    p99_latency_ms = Column(Float, default=0.0)
    min_latency_ms = Column(Float, default=0.0)
    max_latency_ms = Column(Float, default=0.0)
    error_rate = Column(Float, default=0.0)
    ai_analysis = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    environment = relationship("Environment", back_populates="tasks")
    worker = relationship("Worker", back_populates="tasks")
    results = relationship("TaskResult", back_populates="task", cascade="all, delete-orphan")


class TaskResult(Base):
    __tablename__ = "task_results"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    step_index = Column(Integer, nullable=True)
    method = Column(String(10), nullable=False)
    url = Column(String(1000), nullable=False)
    request_body = Column(Text, nullable=True)
    request_headers = Column(JSON, nullable=True)
    status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    latency_ms = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    is_success = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    task = relationship("Task", back_populates="results")
