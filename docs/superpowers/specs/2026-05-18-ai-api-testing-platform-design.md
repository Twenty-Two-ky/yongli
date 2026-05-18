# AI 驱动的 API 自动化测试平台 — 设计文档

## 概述

面试作业：通过 Vibe Coding 设计并实现一套由 AI 驱动的 API 自动化测试平台，包含可交互的 Web 管理界面。交付时限 2 天。

## 技术栈

| 层级 | 选型 |
|------|------|
| 前端 | React + Vite + shadcn/ui + Recharts |
| 后端 | Python FastAPI |
| 数据库 | SQLite（WAL 模式） |
| LLM | Claude API（Anthropic） |
| Demo 服务 | Python FastAPI |

## 架构总览

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Demo 服务    │     │  Demo 服务    │     │  React 前端   │
│  本地环境     │     │  预发布环境    │     │  (Vite)      │
│  :8001        │     │  :8002        │     │  :5173       │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                     │
       │  被测对象           │                     │ REST/SSE
       ▼                    ▼                     ▼
┌────────────────────────────────────────────────────────┐
│                    FastAPI 后端 (:8080)                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ 任务管理  │ │ 环境管理  │ │ LLM 编排 │ │ 结果查询  │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ │
│       └────────────┴────────────┼────────────┘        │
│                          SQLite DB                     │
└─────────────────────────────────┬──────────────────────┘
                                  │ Worker 通过 HTTP API 通信
                                  │ (拉取任务 / 上报结果 / 心跳)
                    ┌─────────────▼─────────────┐
                    │   Worker 进程群 (:0)        │
                    │  ┌────────┐ ┌───────────┐  │
                    │  │ 心跳上报 │ │ HTTP 执行器 │  │
                    │  └────────┘ └───────────┘  │
                    └───────────────────────────┘
```

**核心设计决策：**

- Worker 是独立 Python 进程，通过 Master HTTP API 通信，不直接访问数据库。SQLite 只有 Master 单进程写入，消除并发写锁问题。
- Worker 是无状态的——重启后重新注册、重新心跳、重新拉任务。
- 落地只跑 1 个 Worker 进程（启动脚本可开多个用于演示），架构上 Worker 接口设计为可水平扩展的抽象。
- 前端短轮询 + 任务详情页 SSE 混合策略。

## 项目结构

```
test-claude/
├── backend/                    # FastAPI 后端
│   ├── main.py                 # 应用入口
│   ├── config.py               # 配置管理
│   ├── models.py               # SQLite 数据模型 (SQLAlchemy)
│   ├── schemas.py              # Pydantic 请求/响应模型
│   ├── database.py             # 数据库连接与初始化
│   ├── routers/
│   │   ├── tasks.py            # 任务 CRUD + 执行结果接收
│   │   ├── environments.py     # 环境管理
│   │   ├── workers.py          # Worker 注册、心跳、任务拉取
│   │   └── results.py          # 结果查询与统计
│   ├── services/
│   │   ├── llm_service.py      # Claude API：自然语言解析 + 失败分析
│   │   └── failure_analyzer.py # AI 失败分析触发逻辑
│   └── requirements.txt
├── worker/                     # 独立 Worker 进程
│   ├── worker.py               # 主循环 (长轮询拉任务 → 执行 → 流式上报)
│   ├── http_runner.py          # HTTP 请求执行器 (httpx async)
│   ├── concurrency.py          # 并发控制 (asyncio.Semaphore)
│   └── heartbeat.py            # 心跳上报
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── App.tsx
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx       # 总览 (环境/Worker 状态 + 统计图表)
│   │   │   ├── TaskCreator.tsx     # 自然语言任务创建
│   │   │   ├── TaskHistory.tsx     # 历史任务列表 + 过滤搜索
│   │   │   └── TaskDetail.tsx      # 任务详情 + SSE + AI 分析
│   │   ├── components/
│   │   │   ├── EnvironmentCard.tsx # 环境管理卡片
│   │   │   ├── WorkerCard.tsx      # Worker 状态卡片
│   │   │   ├── TaskTimeline.tsx    # 任务执行时间线
│   │   │   ├── StressDashboard.tsx # 压测仪表盘
│   │   │   ├── ResultTable.tsx     # 单接口/异常输入结果表格
│   │   │   ├── AiAnalysis.tsx      # AI 失败分析展示
│   │   │   └── TaskCompare.tsx     # 跨环境任务对比
│   │   └── api/                    # 前端 API 层
│   └── package.json
├── demo-service/               # Demo 电商被测服务
│   ├── server.py               # FastAPI demo 服务
│   ├── run.sh                  # 一键启动两个环境
│   └── requirements.txt
├── docs/                       # 交付文档
│   ├── vibe-coding-log.md      # Vibe Coding 过程记录 (Prompt 技巧清单)
│   └── scalability-analysis.md # 第 5 题：大规模扩展性分析
└── README.md
```

## 数据模型

### ER 关系

```
environments 1──────N tasks N──────1 workers
                        │
                        │ 1:N
                        ▼
                   task_results
```

### environments

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int PK | |
| name | str | 环境名称 |
| base_url | str | API 根地址 |
| auth_config | JSON | 认证配置（login_path, default_credentials, auth_type） |
| default_headers | JSON | 该环境通用请求头 |
| health_check_path | str | 健康检查路径，默认 /api/v1/health |
| status | str | online/offline |
| last_health_check | timestamp | |
| created_at | timestamp | |

### workers

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int PK | |
| name | str | Worker 标识 |
| status | str | online/offline |
| current_task_id | int FK | 当前正在执行的任务（可为 null） |
| last_heartbeat | timestamp | |
| registered_at | timestamp | |

### tasks

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int PK | |
| natural_language | text | 用户原始自然语言指令 |
| status | str | parsing/queued/running/completed/error/cancelled |
| task_type | str | single/abnormal/stress |
| parsed_actions | JSON | LLM 解析后的结构化执行计划 |
| environment_id | int FK | 目标环境 |
| worker_id | int FK | 执行该任务的 Worker |
| success_count | int | 聚合：成功数 |
| fail_count | int | 聚合：失败数 |
| total_count | int | 聚合：总请求数 |
| avg_latency_ms | float | 聚合：平均延迟 |
| p50_latency_ms | float | 聚合：P50 延迟 |
| p95_latency_ms | float | 聚合：P95 延迟 |
| p99_latency_ms | float | 聚合：P99 延迟 |
| min_latency_ms | float | 聚合：最小延迟 |
| max_latency_ms | float | 聚合：最大延迟 |
| error_rate | float | 聚合：错误率 |
| ai_analysis | JSON | AI 失败分析结果 |
| created_at | timestamp | |
| started_at | timestamp | |
| completed_at | timestamp | |

### task_results

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int PK | |
| task_id | int FK | |
| step_index | int | 步骤序号（单接口/异常输入）或 null（压测） |
| method | str | HTTP 方法 |
| url | str | 请求 URL |
| request_body | text | 请求体（截断 500 字符） |
| request_headers | JSON | 请求头 |
| status_code | int | 响应状态码 |
| response_body | text | 响应体（截断 500 字符） |
| latency_ms | float | 响应耗时 |
| error_message | text | 错误信息（网络超时/HTTP 错误/断言失败） |
| is_success | bool | 是否通过断言 |
| created_at | timestamp | |

### 状态机

```
parsing ──→ queued ──→ running ──→ completed
   │           │           │
   └───────────┴───────────┴──→ error
   │           │               │
   └───────────┴───────────────┴──→ cancelled
```

### parsed_actions 三种 mode 的 JSON Schema

**mode: sequential（单接口验证）**
```json
{
  "mode": "sequential",
  "steps": [
    {
      "step": 1,
      "method": "POST",
      "path": "/api/v1/login",
      "headers": {"Content-Type": "application/json"},
      "body": {"username": "admin", "password": "123456"},
      "assert": {"status_code": 200}
    }
  ]
}
```

**mode: parameterized（异常输入测试）**
```json
{
  "mode": "parameterized",
  "template": {
    "method": "GET",
    "path": "/api/v1/search",
    "query": {"keyword": "${PAYLOAD}"}
  },
  "payloads": [
    {"label": "empty", "value": ""},
    {"label": "long_string", "value": "AAAA...(10000个A)"},
    {"label": "special_chars", "value": "<script>alert(1)</script>"}
  ],
  "assert": {"status_code_in": [200, 400]}
}
```

**mode: load（并发压测）**
```json
{
  "mode": "load",
  "template": {
    "method": "GET",
    "path": "/api/v1/search?keyword=test"
  },
  "load_config": {
    "rate_per_second": 100,
    "duration_seconds": 60,
    "max_concurrent": 200
  }
}
```

Worker 根据 `mode` 字段分发执行分支。

## API 设计

### 统一约定

- 所有列表 API 使用统一分页：`?page=1&page_size=20`
- 分页响应格式：`{ "items": [...], "total": 156, "page": 1, "page_size": 20, "has_next": true }`

### 前端侧

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/tasks` | POST | 创建任务（异步 LLM 解析） |
| `/api/tasks` | GET | 任务列表 |
| `/api/tasks/{id}` | GET | 任务详情（含聚合统计 + AI 分析 + 时间线） |
| `/api/tasks/{id}` | DELETE | 删除任务 |
| `/api/tasks/{id}/cancel` | POST | 取消任务 |
| `/api/tasks/{id}/results` | GET | 任务明细结果（分页） |
| `/api/tasks/{id}/rerun` | POST | 重跑（支持 ?environment_id= 跨环境） |
| `/api/tasks/{id}/stream` | GET | SSE 实时状态推送 |
| `/api/stats/summary` | GET | 全局聚合统计 |

**POST /api/tasks 流程：**
1. 接收自然语言文本 + 目标环境 ID
2. 立即入库（status=parsing），< 100ms 返回 task_id
3. FastAPI BackgroundTasks 异步调用 LLM 解析
4. 解析成功：写入 parsed_actions，status → queued
5. 解析失败：status → error，错误信息写入 ai_analysis

**GET /api/tasks/{id} 返回结构包含：**
- 完整 task 字段
- 计算字段 `timeline` 数组（由现有 timestamp 字段推导，无需独立事件表）
- 嵌套 environment 和 worker 摘要

### Worker 侧

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/workers/register` | POST | Worker 注册 |
| `/api/workers/{id}/heartbeat` | POST | 心跳上报（每 10 秒） |
| `/api/workers/{id}/next-task` | GET | 长轮询拉任务（服务端 hold 15 秒） |
| `/api/tasks/{id}/results` | POST | 流式上报结果（每攒 200 条提交一次） |

**POST /api/tasks/{id}/results 请求体：**
```json
{
  "aggregated": {
    "success_count": 5990, "fail_count": 10, "total_count": 6000,
    "avg_latency_ms": 23.5, "p50_latency_ms": 18, "p95_latency_ms": 67,
    "p99_latency_ms": 120, "min_latency_ms": 5, "max_latency_ms": 450,
    "error_rate": 0.0017
  },
  "results": [ /* 200 条明细 */ ],
  "final": false
}
```

`final: true` 时 Master 触发 AI 失败分析 + status → completed。聚合字段增量更新（running average）。

### 环境 & Worker 管理

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/environments` | GET | 环境列表 |
| `/api/environments` | POST | 添加环境 |
| `/api/environments/{id}` | PUT | 编辑环境 |
| `/api/environments/{id}` | DELETE | 删除环境 |
| `/api/environments/{id}/check` | POST | 手动触发健康检查 |
| `/api/workers` | GET | Worker 列表（含当前执行任务） |

## LLM 服务设计

`backend/services/llm_service.py` — 两个独立函数：

### 1. `parse_nl_task(nl_text, environment) → TaskDefinition`

- 输入：用户自然语言 + 目标环境的 auth_config / base_url
- 输出：`{ task_type, parsed_actions, inferred_environment_reason }`
- 角色：将自然语言指令解析为结构化的执行计划
- Prompt 要点：明确输出 schema（三种 mode），推断 task_type，利用环境 auth_config 注入认证信息
- 错误处理：LLM 调用超时/失败 → status=error；JSON 格式无效 → status=error，保留原始指令

### 2. `analyze_failures(task, failed_results) → FailureAnalysis`

- 输入：任务上下文 + 失败结果列表
- 输出：`{ summary, failure_categories: [{ category, count, sample_errors }] }`
- 角色：对失败用例进行分类和根因分析
- 分类维度：401 鉴权失效 / 500 服务端错误 / 断言失败 / 网络超时 / 其他

两个函数的 prompt、输出格式、错误处理各自独立，但共用同一个 Claude API 客户端。

## 前端页面设计

### 页面 1：总览 (Dashboard)

- 环境卡片网格（本地测试 / 预发布），展示在线状态、延迟、今日任务数、成功率、auth_config 摘要
- Worker 卡片网格（至少 3 个 Worker），展示在线状态、当前执行任务编号
- 全局统计卡片：今日任务数 / 成功率 / 平均延迟 / 失败任务数
- 成功率趋势图 + 平均延迟趋势图（Recharts）
- 最近 5 条任务列表
- 异常状态：所有 Worker 离线时顶部警告条

### 页面 2：创建任务 (TaskCreator)

- 环境选择下拉（默认 "AI 自动选择"）
- 大文本域输入自然语言
- 三个快速示例卡片：单接口验证 / 异常输入 / 并发压测，点击「填入」自动填充文本
- 提交后跳转任务详情页
- 异常状态：所有环境离线时禁用提交

### 页面 3：任务历史 (TaskHistory)

- 过滤栏：状态 + 类型 + 环境 + 关键词搜索
- 任务列表表格，点击跳转详情
- 统一分页组件

### 页面 4：任务详情 (TaskDetail) — SSE 驱动

- 任务元信息（指令、环境、状态）
- 执行时间线（毫秒精度）：创建 → 解析完成 → 入队 → Worker 领取 → 开始执行 → 断言结果 → AI 分析 → 完成
- 按 task_type 切换结果展示：
  - single/abnormal → 步骤结果表格
  - stress → 仪表盘（进度条 + 6 指标卡片 + 延迟分布直方图 + 错误样本列表）
- AI 分析区：失败类别分组 + 分析摘要
- 操作按钮：重跑 / 跨环境重跑（弹窗选环境）
- 对比模式：选中另一已完成任务，并排展示两地差异
- SSE 实现：useEffect 建立 EventSource → 收到事件更新 state → 终态 close() → cleanup 中 close()
- 异常状态：LLM 解析失败展示原因 + 编辑重试按钮；SSE 断连展示重连指示器

### 技术细节

- 无状态管理库（fetch + useState 足够）
- 路由：React Router v6，4 个页面
- SSE 仅用于任务详情页；总览页 Worker/环境状态用轮询（5-10 秒）

## Demo 被测服务

电商后台 API：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/login` | POST | 登录，返回 token |
| `/api/v1/products` | GET | 商品列表，支持 ?keyword= 搜索 |
| `/api/v1/products/{id}` | GET | 商品详情 |
| `/api/v1/orders` | GET | 订单列表，支持 ?status= 过滤 |
| `/api/v1/health` | GET | 健康检查 |

- 内置测试账号：admin/123456（本地），admin/staging123（预发布）
- 内置测试数据：5 个商品、3 个订单
- 异常接口：`/api/v1/products/{id}` 对 id=0 返回 500（模拟内部错误），对 id=999 返回 404
- 一键启动脚本 `run.sh`：启两个实例在不同端口并传入不同 `--env-name`

## 三个演示场景

1. **单接口验证**：「测试登录接口 /api/v1/login，使用账号 admin/123456，校验返回码是否为 200」
   - mode: sequential，1 个步骤，1 次 HTTP 调用
   - 重点展示：自然语言→LLM 解析→自动执行→结果入库→详情页查看

2. **异常输入测试**：「对搜索接口的 keyword 参数分别传入空值、超长字符串、特殊字符等异常输入」
   - mode: parameterized，1 个模板 × 5 组参数，5 次 HTTP 调用
   - 重点展示：LLM 自动生成异常 payload，结果按类别呈现

3. **并发压测**：「对查询接口模拟高并发，每秒 100 请求，持续 1 分钟」
   - mode: load，6000 次 HTTP 调用，Worker 并发执行
   - 重点展示：仪表盘实时更新、延迟分布直方图、流式结果上报

## 交付文档

### docs/vibe-coding-log.md

Vibe Coding 完整过程记录，包含：
- 与 AI 的完整交互对话记录（关键轮次摘录）
- Prompt 技巧清单：
  - 自然语言解析 prompt 的迭代过程
  - 失败分析 prompt 的设计思路
  - 复杂逻辑拆解策略（哪些问题需要分步引导 AI）
  - 遇到的问题及 prompt 调整记录
- 设计决策记录（哪些建议采纳/拒绝及理由）

### docs/scalability-analysis.md

第 5 题：大规模场景下的扩展性分析，包含：
- 1000+ API 端点：元数据管理、测试组织策略
- 1000+ Worker：从 Master HTTP → 消息队列（Redis Streams）的演进路径
- 数据层：SQLite → PostgreSQL + 读写分离
- Worker 原子执行单元演进方向
- 瓶颈分析：任务调度延迟、结果存储、心跳维护成本

### README.md

项目启动说明：依赖安装、Demo 服务启动、后端启动、Worker 启动、前端启动。

## 未实现但已规划的扩展点

以下不在此次交付范围内，但在架构中预留了扩展空间，且在第 5 题文档中分析：

- Worker 水平扩展（Redis Streams / Kafka 消息队列）
- Worker 收敛为原子 HTTP Runner（调度逻辑上移到 Master）
- WebSocket 替代 SSE 用于双向场景
- 多租户认证
- API Schema 自动发现（OpenAPI/Swagger 导入）
- 定时任务 / CI 集成触发器
