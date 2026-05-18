import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test_platform.db")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
MASTER_HOST = os.getenv("MASTER_HOST", "0.0.0.0")
MASTER_PORT = int(os.getenv("MASTER_PORT", "8080"))
WORKER_HEARTBEAT_TIMEOUT = 30  # seconds before worker considered offline
