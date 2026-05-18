import asyncio
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Request
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse
from database import get_db, SessionLocal
from models import Task, TaskResult, Environment, Worker
from schemas import TaskCreate, TaskOut, TaskListOut, ResultSubmit, TaskResultOut, TaskResultListOut
from services.llm_service import parse_nl_task, analyze_failures

router = APIRouter(tags=["tasks"])

def _build_task_out(task: Task) -> dict:
    """Build TaskOut with computed timeline and nested relations."""
    data = {
        "id": task.id, "natural_language": task.natural_language, "status": task.status,
        "task_type": task.task_type, "parsed_actions": task.parsed_actions,
        "environment_id": task.environment_id, "worker_id": task.worker_id,
        "success_count": task.success_count or 0, "fail_count": task.fail_count or 0,
        "total_count": task.total_count or 0,
        "avg_latency_ms": task.avg_latency_ms or 0, "p50_latency_ms": task.p50_latency_ms or 0,
        "p95_latency_ms": task.p95_latency_ms or 0, "p99_latency_ms": task.p99_latency_ms or 0,
        "min_latency_ms": task.min_latency_ms or 0, "max_latency_ms": task.max_latency_ms or 0,
        "error_rate": task.error_rate or 0, "ai_analysis": task.ai_analysis,
        "created_at": task.created_at, "started_at": task.started_at, "completed_at": task.completed_at,
        "environment": None, "worker": None, "timeline": [],
    }
    if task.environment:
        data["environment"] = {
            "id": task.environment.id, "name": task.environment.name,
            "base_url": task.environment.base_url, "status": task.environment.status,
            "auth_config": task.environment.auth_config, "default_headers": task.environment.default_headers,
            "health_check_path": task.environment.health_check_path,
            "last_health_check": task.environment.last_health_check, "created_at": task.environment.created_at,
        }
    if task.worker:
        data["worker"] = {
            "id": task.worker.id, "name": task.worker.name, "status": task.worker.status,
            "current_task_id": task.worker.current_task_id,
            "last_heartbeat": task.worker.last_heartbeat, "registered_at": task.worker.registered_at,
        }
    # Build timeline from timestamps
    timeline = [{"event": "created", "time": str(task.created_at)}]
    if task.parsed_actions:
        timeline.append({"event": "parsed", "time": str(task.created_at)})
    if task.started_at:
        timeline.append({"event": "started", "time": str(task.started_at)})
    if task.completed_at:
        timeline.append({"event": "completed", "time": str(task.completed_at)})
    data["timeline"] = timeline
    return data

def _trigger_failure_analysis(task_id: int):
    """Run AI failure analysis on completed task (async, own session)."""
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return
        if task.fail_count == 0:
            task.ai_analysis = {"summary": "All tests passed.", "failure_categories": []}
            db.commit()
            return
        failed_results = db.query(TaskResult).filter(TaskResult.task_id == task_id, TaskResult.is_success == False).limit(50).all()
        failed_dicts = [{"method": r.method, "url": r.url, "status_code": r.status_code, "error_message": r.error_message} for r in failed_results]
        try:
            analysis = analyze_failures(
                {"natural_language": task.natural_language, "task_type": task.task_type}, failed_dicts
            )
            task.ai_analysis = analysis
        except Exception as e:
            task.ai_analysis = {"summary": f"AI analysis failed: {str(e)}", "failure_categories": []}
        db.commit()
    finally:
        db.close()

@router.post("/tasks", response_model=TaskOut)
def create_task(data: TaskCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Auto-select environment
    env = None
    if data.environment_id:
        env = db.query(Environment).filter(Environment.id == data.environment_id).first()
    if not env:
        env = db.query(Environment).filter(Environment.status == "online").first()
    if not env:
        raise HTTPException(status_code=400, detail="No online environment available")
    task = Task(natural_language=data.natural_language, status="parsing", environment_id=env.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    background_tasks.add_task(_parse_task_background, task.id, data.natural_language, env.id)
    return _build_task_out(task)

def _parse_task_background(task_id: int, nl_text: str, env_id: int):
    """Background task: call LLM, update parsed_actions and status. Uses own session."""
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        env = db.query(Environment).filter(Environment.id == env_id).first()
        env_dict = {"name": env.name, "base_url": env.base_url, "auth_config": env.auth_config, "default_headers": env.default_headers}
        try:
            result = parse_nl_task(nl_text, env_dict)
            task.parsed_actions = result["parsed_actions"]
            task.task_type = result["task_type"]
            task.status = "queued"
        except Exception as e:
            task.status = "error"
            task.ai_analysis = {"summary": f"LLM parsing failed: {str(e)}", "failure_categories": []}
        db.commit()
    finally:
        db.close()

@router.get("/tasks", response_model=TaskListOut)
def list_tasks(status: str = "", task_type: str = "", env_id: int = 0, search: str = "", page: int = 1, page_size: int = 20, db: Session = Depends(get_db)):
    q = db.query(Task)
    if status:
        q = q.filter(Task.status == status)
    if task_type:
        q = q.filter(Task.task_type == task_type)
    if env_id:
        q = q.filter(Task.environment_id == env_id)
    if search:
        q = q.filter(Task.natural_language.contains(search))
    total = q.count()
    items = q.order_by(Task.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [_build_task_out(t) for t in items], "total": total, "page": page, "page_size": page_size, "has_next": (page * page_size) < total}

@router.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _build_task_out(task)

@router.get("/tasks/{task_id}/stream")
async def stream_task(task_id: int, request: Request):
    async def event_gen():
        last_payload = None
        while True:
            if await request.is_disconnected():
                break
            db = SessionLocal()
            try:
                task = db.query(Task).filter(Task.id == task_id).first()
                if not task:
                    break
                payload = json.dumps(_build_task_out(task), default=str)
            finally:
                db.close()
            # Only push when state changed
            if payload != last_payload:
                yield {"data": payload}
                last_payload = payload
            if task.status in ("completed", "error", "cancelled"):
                break
            await asyncio.sleep(1)
    return EventSourceResponse(event_gen())

@router.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"ok": True}

@router.post("/tasks/{task_id}/cancel")
def cancel_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status in ("completed", "error", "cancelled"):
        raise HTTPException(status_code=400, detail=f"Cannot cancel task in status '{task.status}'")
    task.status = "cancelled"
    db.commit()
    return _build_task_out(task)

@router.post("/tasks/{task_id}/rerun", response_model=TaskOut)
def rerun_task(task_id: int, environment_id: int = 0, background_tasks: BackgroundTasks = None, db: Session = Depends(get_db)):
    original = db.query(Task).filter(Task.id == task_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="Original task not found")
    env_id = environment_id if environment_id else original.environment_id
    env = db.query(Environment).filter(Environment.id == env_id).first()
    if not env:
        raise HTTPException(status_code=400, detail="Environment not found")
    new_task = Task(natural_language=original.natural_language, status="parsing", environment_id=env.id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    background_tasks.add_task(_rerun_parse, new_task.id, original.parsed_actions, original.task_type)
    return _build_task_out(new_task)

def _rerun_parse(task_id: int, parsed_actions: dict, task_type: str):
    """Re-run without calling LLM — reuse parsed_actions. Own session."""
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        task.parsed_actions = parsed_actions
        task.task_type = task_type
        task.status = "queued"
        db.commit()
    finally:
        db.close()

@router.post("/tasks/{task_id}/results", response_model=TaskOut)
def submit_results(task_id: int, data: ResultSubmit, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    # Bulk insert results
    for item in data.results:
        db.add(TaskResult(
            task_id=task_id, step_index=item.step_index, method=item.method, url=item.url,
            request_body=(item.request_body or "")[:500],
            request_headers=item.request_headers,
            status_code=item.status_code,
            response_body=(item.response_body or "")[:500],
            latency_ms=item.latency_ms, error_message=item.error_message, is_success=item.is_success,
        ))
    # Update aggregated stats
    agg = data.aggregated
    task.success_count = agg.success_count
    task.fail_count = agg.fail_count
    task.total_count = agg.total_count
    task.avg_latency_ms = agg.avg_latency_ms
    task.p50_latency_ms = agg.p50_latency_ms
    task.p95_latency_ms = agg.p95_latency_ms
    task.p99_latency_ms = agg.p99_latency_ms
    task.min_latency_ms = agg.min_latency_ms
    task.max_latency_ms = agg.max_latency_ms
    task.error_rate = agg.error_rate
    if data.final:
        task.status = "completed"
        task.completed_at = datetime.now(timezone.utc)
        db.commit()
        background_tasks.add_task(_trigger_failure_analysis, task_id)  # async, own session
    else:
        db.commit()
    db.refresh(task)
    return _build_task_out(task)

@router.get("/tasks/{task_id}/results", response_model=TaskResultListOut)
def get_task_results(task_id: int, page: int = 1, page_size: int = 50, db: Session = Depends(get_db)):
    q = db.query(TaskResult).filter(TaskResult.task_id == task_id)
    total = q.count()
    items = q.order_by(TaskResult.created_at.asc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": items, "total": total, "page": page, "page_size": page_size, "has_next": (page * page_size) < total}

@router.get("/stats/summary")
def get_stats_summary(db: Session = Depends(get_db)):
    from datetime import timedelta
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    total = db.query(Task).count()
    today_count = db.query(Task).filter(Task.created_at >= today).count()
    completed = db.query(Task).filter(Task.status == "completed").all()
    success_rate = sum(1 for t in completed if t.fail_count == 0) / max(len(completed), 1)
    avg_lat = sum(t.avg_latency_ms or 0 for t in completed) / max(len(completed), 1)
    failed = db.query(Task).filter(Task.status == "error").count()
    return {"total_tasks": total, "today_tasks": today_count, "overall_success_rate": round(success_rate, 4), "avg_latency_ms": round(avg_lat, 1), "failed_tasks": failed}
