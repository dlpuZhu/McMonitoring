# Take-Home Assignment: Connector Service Monitoring Skill

## 📋 Assignment Overview

Build a **monitoring skill** for a Connector Service that includes:
1. A simulated data source (based on ConnectorJobs)
2. A Grafana Dashboard for service health visibility
3. Alert rules for key failure scenarios
4. A self-validation mechanism to verify dashboard and alerts are working correctly

**Time**: Weekend (2 days)  
**Deliverable**: A GitHub repo with code, screenshots, and a README  
**AI Usage**: Encouraged — you may use any AI tools (Copilot, ChatGPT, etc.). We value your ability to leverage AI effectively, not whether you wrote every line by hand.

---

## 🗄️ Part 1: Data Simulation (Data Source)

Create a program that generates realistic ConnectorJobs data and writes it to a database. You can use any language or tool you're comfortable with.

### Base Table

```sql
CREATE TABLE ConnectorJobs (
    JobId            INT PRIMARY KEY AUTO_INCREMENT,
    ConnectorType    VARCHAR(50),    -- SQLServer, PostgreSQL, CosmosDB, MongoDB, MySQL
    Region           VARCHAR(50),    -- EastUS, WestEurope, SoutheastAsia, JapanEast
    Status           VARCHAR(20),    -- Running, Failed, Creating, Paused, Completed
    ErrorCode        VARCHAR(20),    -- NULL when not failed; e.g. E001, E002, E003
    CreatedTime      DATETIME,
    LastUpdatedTime  DATETIME,
    DurationSeconds  INT
);
```

### Extended Tables (pick at least 1 to add)

The base table alone may not be enough to build a comprehensive monitoring dashboard. Think about what additional data would be useful for monitoring a connector service, and design at least one extra table.

---

## 📊 Part 2: Grafana Dashboard

Create a Grafana dashboard that gives an on-call engineer a clear view of the Connector Service health.

Design the panels yourself — think about what an operator would need to see to quickly understand the system status and identify problems.

---

## 🔔 Part 3: Alert Rules

Configure alert rules in Grafana for the Connector Service. For each alert, document:
- **What** it monitors
- **Why** this alert matters

Design the alerts yourself based on what you think is important for this service.

---

## ✅ Part 4: Self-Validation

Build a way to **automatically verify** your monitoring setup is working correctly. Think about what checks would give you confidence that the dashboard and alerts are functioning as expected.

### Output

The validation should output a clear result showing what passed and what failed.

---

## 🛠️ Environment Setup

### Option A: Azure Managed Grafana (Recommended)

Use an Azure free account to create a **Managed Grafana** instance in the Azure Portal:

1. Go to [azure.microsoft.com/free](https://azure.microsoft.com/free/) — sign up with any Microsoft account (Outlook/Hotmail/Live). You get $200 credit for 30 days.
2. In Azure Portal, search for **"Azure Managed Grafana"** and create an instance.
3. Use an Azure database service (e.g., Azure SQL, Azure Database for MySQL/PostgreSQL) as your data source.

### Option B: Local Docker

Use Docker Compose to run Grafana and a database locally — no cloud account needed.

### What We Do NOT Care About

- ❌ Beautiful UI design — functional is fine
- ❌ Production-grade infrastructure — this is a demo
- ❌ Whether you used AI — we care about the result and your understanding of it

### What We DO Care About

- ✅ Can you explain **why** you chose each dashboard panel and alert?
- ✅ Can you explain **what each alert means** operationally — what would an on-call engineer do when it fires?
- ✅ Did you think about **false positives** (noisy alerts) and **false negatives** (missing real issues)?
