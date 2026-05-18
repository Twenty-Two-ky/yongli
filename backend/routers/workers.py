import asyncio
import time
from datetime import datetime, timezone
from sqlalchemy import text
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from database import get_db, SessionLocal
from models import Worker, Task
from schemas import WorkerRegister, WorkerOut

router = APIRouter(tags=["workers"])

@router.post("/workers/register", response_model=WorkerOut)
def register_worker(data: WorkerRegister, db: Session = Depends(get_db)):
    existing = db.query(Worker).filter(Worker.name == data.name).first()
    if existing:
        existing.status = "online"
        existing.last_heartbeat = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing
    worker = Worker(name=data.name, status="online", last_heartbeat=datetime.now(timezone.utc))
    db.add(worker)
    db.commit()
    db.refresh(worker)
    return worker

@router.post("/workers/{worker_id}/heartbeat")
def worker_heartbeat(worker_id: int, db: Session = Depends(get_db)):
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    worker.last_heartbeat = datetime.now(timezone.utc)
    worker.status = "online"
    db.commit()
    return {"ok": True}

@router.get("/workers/{worker_id}/next-task")
async def next_task(worker_id: int, wait: int = 15):
    """Long-poll for the next queued task. Uses fresh session per loop + BEGIN IMMEDIATE for atomic claim."""
    deadline = time.time() + wait
    while time.time() < deadline:
        db = SessionLocal()
        try:
            # BEGIN IMMEDIATE ensures atomic SELECT + UPDATE — prevents multiple workers grabbing the same task
            db.execute(text("BEGIN IMMEDIATE"))
            task = db.query(Task).filter(Task.status == "queued").order_by(Task.created_at.asc()).first()
            if task:
                task.status = "running"
                task.worker_id = worker_id
                task.started_at = datetime.now(timezone.utc)
                worker = db.query(Worker).filter(Worker.id == worker_id).first()
                if worker:
                    worker.current_task_id = task.id
                db.commit()
                return {
                    "id": task.id, "natural_language": task.natural_language,
                    "task_type": task.task_type, "parsed_actions": task.parsed_actions,
                    "environment_id": task.environment_id,
                }
            db.rollback()
        finally:
            db.close()
        await asyncio.sleep(0.3)
    return Response(status_code=204)

@router.get("/workers", response_model=list[WorkerOut])
def list_workers(db: Session = Depends(get_db)):
    from config import WORKER_HEARTBEAT_TIMEOUT
    now = datetime.now(timezone.utc)
    workers = db.query(Worker).order_by(Worker.registered_at.desc()).all()
    for w in workers:
        if w.last_heartbeat and (now - w.last_heartbeat).total_seconds() > WORKER_HEARTBEAT_TIMEOUT:
            w.status = "offline"
            w.current_task_id = None
    db.commit()
    return workers
