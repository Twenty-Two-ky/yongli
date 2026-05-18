# 大规模场景扩展性分析

## 场景定义

- 1000+ API 端点需要管理
- 1000+ Worker 执行节点
- 每个端点的测试频率和并发量随时间波动

## 瓶颈分析与改进思路

### 1. 数据库层

**当前瓶颈：** SQLite 文件级锁，单机写入。当 1000+ Worker 同时提交结果时，写冲突量指数增长。

**改进方案：**
- **SQLite → PostgreSQL：** 支持行级锁和真正并发写。1000 Worker 的结果可并行写入。
- **读写分离：** Master 写主库，查询统计走只读副本。列表页和统计 API 不再与结果提交竞争。
- **结果归档：** 7 天前的 task_results 明细迁移到对象存储（S3/MinIO），Task 表保留聚合字段用于趋势查询。

### 2. 任务调度层

**当前瓶颈：** Master HTTP 长轮询。1000 Worker 意味着 1000 个长连接 hold 在服务端，每 15 秒一轮。每个连接占用一个协程和数据库连接。实际上单 Master 最多支撑几百个并发长轮询。

**改进方案：**
- **Master HTTP → Redis Streams：** Worker 不再轮询 Master，而是订阅 Redis Stream。任务创建后发布到 stream，Worker 从 stream 消费。Master 和 Worker 完全解耦。
- **任务分区：** 按 API 域名的 hash 将任务分配到不同队列。Worker 只处理自己分区的任务，避免所有 Worker 争抢同一任务。
- **调度策略：** 支持亲和性（Worker A 优先处理环境 X 的任务）和反亲和性（避免同一 Worker 被任务压满）。

### 3. Worker 层

**当前瓶颈：** Worker 理解三种 mode 的执行逻辑。未来加新 mode 需修改 Worker 代码并重启。

**改进方案：**
- **原子执行单元：** Master 在调度阶段将 parsed_actions 展开为原子 HTTP 调用列表 + 聚合需求。Worker 退化为纯 HTTP Runner，不关心 mode 语义。新测试类型只需改 Master 的展开逻辑。
- **无状态 Worker：** 进程级无状态（已完成），可随意水平扩缩。
- **Worker 分级：** 普通 Worker 处理 sequential/parameterized 任务；LoadTest Worker 专门处理压测（更高资源配置）。

### 4. 心跳维护成本

**当前瓶颈：** 1000 Worker × 每 10 秒心跳 = 100 QPS 的心跳写入。看似不大，但加上任务拉取（长轮询不再轮询后取消此开销）和结果提交，Master DB 压力不小。

**改进方案：**
- **心跳与任务拉取合并：** 长轮询本身就证明了 Worker 存活，额外的独立心跳周期可以取消。
- **心跳走 Redis：** key 带 TTL，Worker 每 10 秒 SET，Master 只查 Redis 不查 DB。离线判定阈值从 30 秒降到 15 秒。

### 5. 1000+ API 端点的元数据管理

**当前状态：** 系统不存 API 定义表（LLM 动态解析）。在大规模场景下，这会导致：
- LLM 每次解析都需要"猜" API 路径和方法，增加 token 消耗和错误率。
- 统计无法按 API 端点维度聚合。

**改进方案：**
- **API 目录表：** 维护端点的 method、path、描述、所属服务。可从 OpenAPI spec 导入或通过流量采样自动发现。
- **解析增强：** LLM 解析时传入 API 目录作为 context，提高路径匹配准确率。
- **统计增强：** 按端点维度出成功率、P95 延迟趋势图。

### 6. 架构演进路线图

```
Phase 1 (当前)     Phase 2            Phase 3
───────────────    ───────────────    ───────────────
Master HTTP        Master + Redis     Master + Kafka
SQLite             PostgreSQL         PostgreSQL + S3
1 Worker           10+ Worker         1000+ Worker
单进程              Redis Streams      K8s Deployment
同步 LLM 解析      异步 Celery         事件驱动全异步
```
