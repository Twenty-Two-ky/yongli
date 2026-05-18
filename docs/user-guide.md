# AI 驱动的 API 自动化测试平台 — 使用文档

## 架构概览

```
浏览器 (:3000) ──→ React SPA ──→ Backend Master (:8080) ──→ SQLite
                                        │
                                        ↓
                                   Worker × 3 ──→ Demo 被测服务 (:8001 / :8002)
```

- **Backend Master**：FastAPI，负责任务管理、LLM 解析、结果存储
- **Worker**：独立进程，长轮询拉取任务，执行 HTTP 请求并上报结果
- **Demo 被测服务**：模拟电商 API，提供双环境（本地 / 预发布）
- **前端**：React SPA，提供可视化管理界面

---

## 1. 启动平台

### 一键启动（推荐）

**Windows:**
```powershell
.\scripts\start-all.ps1
```

**Linux / Mac:**
```bash
bash scripts/start-all.sh
```

### 分步启动

如果一键启动失败，分窗口手动启动：

**窗口 1 — 启动 Demo 被测服务：**
```powershell
cd demo-service
pip install -r requirements.txt
python server.py --env-name local --port 8001
```
再开一个终端：
```powershell
cd demo-service
python server.py --env-name staging --port 8002
```

**窗口 2 — 启动后端：**
```powershell
cd backend
pip install -r requirements.txt
$env:ANTHROPIC_API_KEY = "sk-ant-xxx"   # 你的 Claude API Key
python main.py
```

**窗口 3 — 启动 Worker（可开 3 个）：**
```powershell
cd worker
pip install -r requirements.txt
$env:WORKER_NAME = "worker-1"; python worker.py
```
```powershell
$env:WORKER_NAME = "worker-2"; python worker.py
```
```powershell
$env:WORKER_NAME = "worker-3"; python worker.py
```

**窗口 4 — 启动前端：**
```powershell
cd frontend
npm install
npm run dev
```

### 服务地址

| 服务 | 地址 |
|------|------|
| 前端界面 | http://localhost:3000 |
| 后端 API | http://localhost:8080 |
| Demo 本地环境 | http://localhost:8001 |
| Demo 预发布环境 | http://localhost:8002 |

---

## 2. 界面功能介绍

### 总览页（首页）

- **环境卡片**：展示已注册的测试环境，点击 WiFi 图标触发健康检查
- **Worker 节点**：显示所有 Worker 的在线状态，绿色=在线，红色=离线
- **全局统计**：今日任务数、成功率、平均延迟、失败任务数
- **最近任务**：快速查看最近的 5 个任务，点击行跳转到详情
- 页面每 5 秒自动刷新

### 创建任务

1. 点击顶部导航 **"创建任务"**
2. 选择目标环境（推荐 "AI 自动选择"）
3. 输入自然语言测试指令
4. 点击 **"执行任务"**
5. 自动跳转到任务详情页，查看实时执行状态

### 任务历史

- 支持按 **状态**（解析中 / 排队中 / 执行中 / 已完成 / 异常 / 已取消）筛选
- 支持按 **类型**（单接口 / 异常输入 / 压测）筛选
- 支持按 **环境** 筛选
- 支持按 **指令关键词** 搜索
- 分页浏览，每页 20 条

### 任务详情

- **实时状态**：通过 SSE 推送，状态变化自动更新，无需刷新
- **执行时间线**：显示任务的生命周期（创建 → 解析 → 执行 → 完成）
- **执行结果表格**：每个 HTTP 请求的方法、URL、状态码、耗时、成功/失败
- **压测仪表盘**（压测类任务）：成功率、QPS、延迟百分位，延迟分布柱状图
- **AI 分析**：任务完成后自动分析失败原因，按类别归类（认证失败 / 服务端错误 / 超时等）
- **跨环境对比**：输入另一个任务 ID，并排对比两个环境的执行结果
- **重跑**：支持同环境重跑和跨环境重跑（复用解析结果，不重新调用 LLM）

---

## 3. 支持的测试类型

### 类型 1：单接口验证

**示例指令：**
```
测试登录接口 /api/v1/login，使用账号 admin/123456，校验返回码是否为 200
```

**执行方式：** Worker 按步骤顺序发送 HTTP 请求，每个断言独立判断。

### 类型 2：异常输入测试

**示例指令：**
```
对搜索接口 /api/v1/search 的 keyword 参数分别传入空值、超长字符串、特殊字符等异常输入
```

**执行方式：** LLM 自动生成 3-5 种异常 Payload（空值、超长字符串、SQL 注入、XSS、Unicode），Worker 逐个替换 `${PAYLOAD}` 占位符发送请求。

### 类型 3：并发压测

**示例指令：**
```
对查询接口 /api/v1/search 模拟高并发流量，每秒发送 100 个请求，持续 1 分钟
```

**执行方式：** Worker 按指定速率发送请求，实时统计成功率、QPS 和各百分位延迟，分批上报结果。

---

## 4. 环境管理

### 添加环境

通过 API：
```powershell
curl -X POST http://localhost:8080/api/environments `
  -H "Content-Type: application/json" `
  -d '{
    "name": "本地测试",
    "base_url": "http://localhost:8001",
    "auth_config": {
      "login_path": "/api/v1/login",
      "default_credentials": {"username": "admin", "password": "123456"},
      "auth_type": "bearer"
    },
    "health_check_path": "/api/v1/health"
  }'
```

### 删除环境

```powershell
curl -X DELETE http://localhost:8080/api/environments/1
```

### 健康检查

```powershell
curl -X POST http://localhost:8080/api/environments/1/check
```

---

## 5. Demo 被测服务 API

### 端点列表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/health` | 健康检查 |
| POST | `/api/v1/login` | 登录（admin/123456） |
| GET | `/api/v1/products` | 商品列表，支持 `?keyword=` 搜索 |
| GET | `/api/v1/products/{id}` | 商品详情（id=0 触发 500 错误） |
| GET | `/api/v1/orders` | 订单列表，支持 `?status=` 筛选 |

### 环境差异

| 环境 | 端口 | 密码 |
|------|------|------|
| local | 8001 | 123456 |
| staging | 8002 | staging123 |

---

## 6. 环境变量

### Backend Master

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `sqlite:///./test_platform.db` | 数据库路径 |
| `ANTHROPIC_API_KEY` | (空) | Claude API Key（不设置则走 Fallback） |
| `LLM_MODEL` | `claude-sonnet-4-6` | 使用的模型 |
| `MASTER_HOST` | `0.0.0.0` | 监听地址 |
| `MASTER_PORT` | `8080` | 监听端口 |

### Worker

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MASTER_URL` | `http://localhost:8080` | Master 地址 |
| `WORKER_NAME` | `worker-1` | Worker 名称（每个实例须不同） |

---

## 7. 无 API Key 使用

如果未设置 `ANTHROPIC_API_KEY`，系统内置了 3 个 Demo 场景的 Fallback 解析结果，按下表匹配：

| 指令关键词 | 触发场景 |
|-----------|----------|
| 包含 "登录" + "admin" + "123456" | 单接口验证：登录接口 |
| 包含 "异常"/"空值"/"特殊字符" + "keyword"/"搜索"/"search" | 异常输入：搜索接口 |
| 包含 "并发"/"压测"/"qps" + "每秒"/"持续"/"分钟" | 并发压测：搜索接口 |

AI 分析功能在无 API Key 时不可用。

---

## 8. 常见问题

**Q: 创建任务后一直处于 "解析中" 状态？**
A: 检查是否设置了 `ANTHROPIC_API_KEY`，或者指令是否匹配 Fallback 关键词。

**Q: 任务卡在 "排队中"？**
A: 检查 Worker 是否在线。总览页 Worker 卡片应显示绿色。如果离线，检查 Worker 进程是否已启动。

**Q: 前端报 "拒绝连接"？**
A: 确认后端 Master 已启动在 8080 端口，且 Vite 代理配置正确。

**Q: 端口被占用？**
A: `netstat -ano | findstr :8001` 查看占用进程，`taskkill /PID <pid> /F` 杀掉。
