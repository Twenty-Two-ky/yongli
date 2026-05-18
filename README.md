# AI 驱动的 API 自动化测试平台

## 快速启动

### 1. 启动 Demo 被测服务

```bash
cd demo-service
pip install -r requirements.txt
bash run.sh  # 启动本地(:8001) 和 预发布(:8002) 两个环境
```

### 2. 启动后端 Master

```bash
cd backend
pip install -r requirements.txt
# 设置 Claude API Key
export ANTHROPIC_API_KEY=sk-ant-xxx
python main.py  # 启动在 :8080
```

### 3. 启动 Worker

```bash
cd worker
pip install -r requirements.txt
# 启动 3 个 Worker 实例（3 个终端窗口）
python worker.py & WORKER_NAME=worker-1
python worker.py & WORKER_NAME=worker-2
python worker.py & WORKER_NAME=worker-3
```

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev  # 启动在 :5173
```

### 5. 初始化环境

打开浏览器访问 http://localhost:5173，通过 API 或界面添加两个环境：
- 本地测试：http://localhost:8001
- 预发布：http://localhost:8002

## 技术栈

- 后端：Python FastAPI + SQLite + Claude API
- 前端：React + Vite + Tailwind CSS + Recharts
- Worker：Python asyncio + httpx
- Demo 服务：Python FastAPI
