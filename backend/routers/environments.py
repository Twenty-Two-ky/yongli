from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx
from database import get_db
from models import Environment
from schemas import EnvironmentCreate, EnvironmentUpdate, EnvironmentOut

router = APIRouter(tags=["environments"])


@router.get("/environments", response_model=list[EnvironmentOut])
def list_environments(db: Session = Depends(get_db)):
    return db.query(Environment).order_by(Environment.created_at.desc()).all()


@router.post("/environments", response_model=EnvironmentOut)
def create_environment(data: EnvironmentCreate, db: Session = Depends(get_db)):
    env = Environment(
        name=data.name,
        base_url=data.base_url,
        auth_config=data.auth_config.model_dump(),
        default_headers=data.default_headers,
        health_check_path=data.health_check_path,
    )
    db.add(env)
    db.commit()
    db.refresh(env)
    return env


@router.put("/environments/{env_id}", response_model=EnvironmentOut)
def update_environment(
    env_id: int, data: EnvironmentUpdate, db: Session = Depends(get_db)
):
    env = db.query(Environment).filter(Environment.id == env_id).first()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    for key, val in data.model_dump(exclude_unset=True).items():
        if key == "auth_config" and val is not None:
            setattr(env, key, val.model_dump())
        else:
            setattr(env, key, val)
    db.commit()
    db.refresh(env)
    return env


@router.delete("/environments/{env_id}")
def delete_environment(env_id: int, db: Session = Depends(get_db)):
    env = db.query(Environment).filter(Environment.id == env_id).first()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    db.delete(env)
    db.commit()
    return {"ok": True}


@router.post("/environments/{env_id}/check")
async def check_environment(env_id: int, db: Session = Depends(get_db)):
    env = db.query(Environment).filter(Environment.id == env_id).first()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                f"{env.base_url}{env.health_check_path}"
            )
            env.status = "online" if resp.status_code < 500 else "offline"
    except Exception:
        env.status = "offline"
    env.last_health_check = datetime.now(timezone.utc)
    db.commit()
    db.refresh(env)
    return {"status": env.status, "last_health_check": env.last_health_check}
