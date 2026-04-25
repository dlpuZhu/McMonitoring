# Connector Service Monitoring Skill

这是一个基于 Python 的模拟连接器服务监控方案，包含：

- 数据模拟器：生成 `ConnectorJobs` 以及扩展指标数据
- Grafana 仪表盘：展示服务健康和故障趋势
- 警报规则：捕获关键失败场景
- 自我验证：自动检查数据仿真、仪表盘结构和警报规则

## 文件结构

- `simulator/data_simulator.py`：生成并写入模拟数据
- `simulator/self_validation.py`：验证数据库数据和 Grafana 仪表盘/警报结构
- `grafana/dashboards/connector_service_dashboard.json`：Grafana 仪表盘定义
- `grafana/alert_rules.md`：警报规则说明
- `docker-compose.yml`：可选本地 Grafana + MySQL 环境

## 运行环境

推荐安装 Python 3.11+。

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> 注意：如果要使用 MySQL 数据库，请先安装依赖包。`requirements.txt` 已包含 `mysql-connector-python` 和 `PyMySQL`。

## 数据模拟

默认使用 SQLite，本地运行：

```bash
python simulator/data_simulator.py --db-url sqlite:///connector_monitor.db
```

若使用 Docker Compose，本地运行 MySQL：

```bash
docker compose up -d
python simulator/data_simulator.py --db-url mysql://grafana:grafana@127.0.0.1:3306/connector_monitor
```

## Grafana 仪表盘

如果你使用 `docker compose`，Grafana 将在 `http://localhost:3000` 可访问，默认账号：

- 用户名：`admin`
- 密码：`admin`

当前 `grafana/dashboards/connector_service_dashboard.json` 包含：

- `Connector Jobs by Status`
- `Failed Jobs by Connector Type`
- `Regional Failure Rate`
- `Active Jobs and Error Count`
- `Job Duration Distribution`

## 警报规则

请参见 `grafana/alert_rules.md`，其中定义了：

- 高失败率告警
- 完成作业变慢告警
- 活动作业数量异常告警
- 区域性故障告警

## 自我验证

运行验证程序：

```bash
python simulator/self_validation.py --db-url sqlite:///connector_monitor.db
```

该程序会检查：

- 数据是否已写入
- 失败作业是否存在
- 作业状态分布是否合理
- Grafana 仪表盘 JSON 是否包含预期面板和警报字段

## 设计说明

本方案使用 Python 生成模拟数据，并保留 Grafana 仪表盘 JSON 与 alert 文档，用于演示监控技能的完整闭环。