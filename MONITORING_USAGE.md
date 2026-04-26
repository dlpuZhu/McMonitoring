# Connector Service Monitoring 使用说明

本项目提供一个完整的监控演示方案，包括模拟数据源、Grafana 仪表盘、告警说明和自我验证。

## 1. 监控流程概览

1. 生成模拟数据到数据库
2. 启动 Grafana 并加载数据源与仪表盘
3. 在 Grafana 中查看监控面板
4. 运行自我验证，确认数据和仪表盘正常

## 2. 推荐方式：本地 Docker Compose

### 启动服务

```bash
docker compose up -d
```

这会启动：

- `mysql`：用于存储模拟的 `ConnectorJobs` 数据
- `grafana`：用于展示 Grafana 仪表盘

### 访问 Grafana

打开浏览器：

```text
http://localhost:3000
```

默认账号：

- 用户名：`admin`
- 密码：`admin`

## 3. 生成模拟数据

### 默认使用 SQLite

如果你不想使用 Docker，可以直接运行：

```bash
python simulator/data_simulator.py --db-url sqlite:///connector_monitor.db
```

### 使用 MySQL 数据库

如果你已经启动了 `docker compose`：

```bash
python simulator/data_simulator.py --db-url mysql://grafana:grafana@127.0.0.1:3306/connector_monitor
```

这会自动创建表结构并写入模拟数据：

- `ConnectorJobs`
- `ConnectorJobMetrics`

## 4. Grafana 仪表盘说明

项目已经提供了 Grafana 仪表盘配置文件：

- `grafana/dashboards/connector_service_dashboard.json`
- `grafana/provisioning/datasources/datasource.yaml`
- `grafana/provisioning/dashboards/dashboard.yaml`

### 已定义的面板

- `Connector Jobs by Status`
  - 展示各状态作业数量分布
- `Failed Jobs by Connector Type`
  - 展示失败作业按连接器类型的统计
- `Regional Failure Rate`
  - 展示每个区域的失败率
- `Active Jobs and Error Count`
  - 展示当前运行作业趋势
- `Job Duration Distribution`
  - 展示不同状态作业的平均/最大时长

### 保持仪表盘方法

1.在Grafana UI中导出仪表盘
进入您修改的仪表盘
选择 Save to file 下载JSON
2.更新本地文件connector_service_dashboard.json
3.重启Grafana容器使用新配置
 ```bash
 docker compose restart grafana
 ```

## 5. 告警规则说明

项目中的告警设计目标是捕获关键问题：

- 高失败率告警：`HighFailureRate`
- 完成作业变慢告警：`SlowCompletion`
- 活动作业数量异常告警：`NoActiveJobs`
- 区域性故障告警：`RegionalFailureSpike`

详细说明可见：`grafana/alert_rules.md`

## 6. 自我验证

运行自检脚本，确认数据库数据和仪表盘配置是否完整：

```bash
python simulator/self_validation.py --db-url sqlite:///connector_monitor.db
```

如果你使用 MySQL：

```bash
python simulator/self_validation.py --db-url mysql://grafana:grafana@127.0.0.1:3306/connector_monitor
```

### 自检检查内容

- 数据库是否包含足够的 `ConnectorJobs` 数据
- 是否存在 `Failed` 和 `Running` 作业
- 是否存在扩展指标表 `ConnectorJobMetrics`
- Grafana 仪表盘 JSON 是否包含预期面板和告警

## 7. 常见问题

- 如果 Grafana 启动后没有自动加载仪表盘，请确认 `grafana/provisioning/dashboards/dashboard.yaml` 中的 `path` 是否正确。
- 如果 MySQL 中没有表，请先运行模拟数据脚本来创建表结构和写入数据。

## 8. 进一步使用

1. 启动 Docker Compose
2. 运行数据模拟器写入数据
3. 打开 Grafana 查看仪表盘
4. 运行自我验证程序确认结果

这个文件可以作为你快速使用本项目监控能力的入门指南。