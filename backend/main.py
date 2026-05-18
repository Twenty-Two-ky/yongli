from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import tasks, environments, workers

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI API Testing Platform")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(tasks.router, prefix="/api")
app.include_router(environments.router, prefix="/api")
app.include_router(workers.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    from config import MASTER_HOST, MASTER_PORT
    uvicorn.run(app, host=MASTER_HOST, port=MASTER_PORT)
