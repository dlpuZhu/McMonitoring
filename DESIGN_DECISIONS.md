# 设计决策说明

本项目目标是构建一个模拟连接器服务的监控技能，包含数据模拟、Grafana 仪表盘、告警规则和自我验证。以下是关键设计决策和选择理由。

## 1. 技术栈选择

- 语言：使用 Python 实现数据模拟与验证逻辑。
  - 原因：Python 在数据处理和原型开发上效率高，并且易于编写 SQL 连接逻辑。
- 数据库：支持 SQLite 和 MySQL 两种模式。
  - 原因：SQLite 适合快速本地演示，MySQL 适合与 Grafana 集成。通过 URL 参数切换数据库类型，提升灵活性。
- 可视化：Grafana
  - 原因：Grafana 是成熟的监控可视化工具，支持多种数据源、仪表盘和告警自动化。

## 2. 数据模型设计

### 2.1 基础表 `ConnectorJobs`

- 字段设计：
  - `JobId`：作业唯一标识
  - `ConnectorType`：连接器类型（SQLServer, PostgreSQL, CosmosDB, MongoDB, MySQL）
  - `Region`：运行区域
  - `Status`：作业状态（Running, Failed, Creating, Paused, Completed）
  - `ErrorCode`：失败时的错误码
  - `CreatedTime`、`LastUpdatedTime`：时间戳字段
  - `DurationSeconds`：作业时长

- 设计理由：该表覆盖连接器服务的核心运行信息，适用于状态分布、失败率、时序趋势和性能分析。

### 2.2 扩展表 `ConnectorJobMetrics`

- 字段设计：
  - `MetricsId`：指标记录唯一标识
  - `JobId`：关联作业
  - `ThroughputMbps`：吞吐量指标
  - `ErrorCount`：错误次数
  - `Retries`：重试次数
  - `LastHeartbeat`：最后心跳时间

- 设计理由：将运行指标与作业元数据分离，便于扩展监控场景，如吞吐量、错误数和重试行为分析。

## 3. Grafana 仪表盘设计

### 3.1 数据源自动化配置

- 使用 Grafana provisioning 自动导入 MySQL 数据源。
- 选择 `uid` 固定值 `connector-monitor-mysql`，避免仪表盘和数据源之间的引用不一致。

### 3.2 仪表盘面板设计

已设计以下关键面板：

1. **Connector Jobs by Status**
   - 目标：快速判断作业整体状态分布。
   - 类型：柱状图
   - 指标：`Status`, `COUNT(*)`
2. **Failed Jobs by Connector Type**
   - 目标：定位哪类连接器失败最严重。
   - 类型：柱状图
   - 指标：`ConnectorType`, `COUNT(*)`（仅统计 `Status='Failed'`）
3. **Regional Failure Rate**
   - 目标：筛查区域性故障，发现区域失效率异常。
   - 类型：Stat / 表格
   - 指标：`Region`, `100.0 * SUM(Status='Failed') / COUNT(*)`
4. **Active Jobs and Error Count**
   - 目标：观察运行中作业趋势，判断系统活跃度。
   - 类型：时间序列图
   - 指标：`CreatedTime AS time`, `Status AS metric`, `COUNT(*)`
5. **Job Duration Distribution**
   - 目标：检测作业耗时是否超出预期。
   - 类型：表格
   - 指标：`Status`, `AVG(DurationSeconds)`, `MAX(DurationSeconds)`

### 3.3 设计原则

- 以“快速定位故障”为核心，优先展示失败率、区域分布和时序趋势。
- 保持面板简单，可快速理解和操作。
- 避免使用过于复杂的 SQL，保证数据源可复现性。

## 4. 告警规则设计

### 4.1 关键告警

1. `HighFailureRate`
   - 监控内容：短期内失败作业占比上升
   - 目的：及时感知整体服务异常
2. `SlowCompletion`
   - 监控内容：完成作业平均耗时异常增长
   - 目的：发现性能退化或下游延迟问题
3. `NoActiveJobs`
   - 监控内容：运行中作业数量降为零
   - 目的：检测服务停摆或调度异常
4. `RegionalFailureSpike`
   - 监控内容：某一区域失败率显著升高
   - 目的：快速定位区域性故障

### 4.2 告警设计考虑

- 避免噪音：告警触发条件应结合短期统计和趋势判断，避免单条错误记录触发。
- 可操作性：每条告警都应有明确的排查方向。
- 业务意义：重点关注失败、性能和可用性三类核心运营指标。

## 5. 自我验证设计

- 设计 `simulator/self_validation.py`，自动检查：
  - 数据库中是否存在足够的 `ConnectorJobs` 数据
  - 是否存在 `Failed` 和 `Running` 作业
  - 扩展指标表是否存在且数据量匹配
  - Grafana 仪表盘 JSON 是否包含预期面板和告警名称

- 设计理由：保证监控系统不仅能展示数据，还能自动验证监控对象和配置完整性。

## 6. 其他设计决策

- 采用 `docker-compose` 支持本地快速验证环境，降低“必须使用云服务”的门槛。
- 将可视化配置与代码分离，使用 Grafana provisioning 文件保持配置可版本化。
- 在 `.gitignore` 中排除本地数据库和 Docker 数据卷，避免将临时数据写入仓库。

## 7. 总结

本项目的设计目标是构建一个可复现、易验证、面向故障定位的监控演示方案。通过简单的数据模型、Grafana 可视化和告警说明，形成一个完整闭环，同时保留本地部署和自动验证能力。