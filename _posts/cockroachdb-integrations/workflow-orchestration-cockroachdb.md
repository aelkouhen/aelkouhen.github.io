---
date: 2026-04-23
layout: post
title: "Agentic Workflow Orchestration with CockroachDB"
subtitle: "How Temporal and DBOS leverage CockroachDB as a durable, globally consistent storage backend for resilient, long-running agent workflows"
tags: [integrations, CockroachDB, temporal, dbos, workflow, orchestration, ai-agents, durable-execution]
lang: en
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

Modern AI applications are no longer single-shot inference calls — they are long-running agents that plan, act, observe, and retry across time. Coordinating these agents reliably requires a **workflow orchestration layer** that survives crashes, scales horizontally, and guarantees exactly-once execution semantics. Two frameworks have emerged as leading solutions: [Temporal](https://temporal.io/) and [DBOS](https://dbos.dev/). Both can use [CockroachDB](https://www.cockroachlabs.com/) as their persistence backbone, giving you a distributed, strongly-consistent, self-healing storage tier beneath your agent infrastructure.

---

## What Is Workflow Orchestration?

A **workflow orchestration framework** manages the lifecycle of long-running, multi-step programs. Instead of writing retry loops, checkpointing logic, and failure recovery by hand, you declare your business logic as a sequence of **durable steps** and let the framework handle the rest.

<img src="/assets/img/teleport-crdb-distributed-sql.png" alt="Durable execution guarantees" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**From stateless functions to durable, resumable workflows**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

The core promises of any workflow framework are:

- **Durability** — workflow state survives process crashes, restarts, and infrastructure failures
- **Exactly-once semantics** — individual steps are never re-executed after they complete successfully
- **Idempotency** — re-invoking the same workflow with the same ID is a no-op
- **Observability** — the full execution history is inspectable at any point

For agentic AI workloads these guarantees are essential. An agent loop that queries an LLM, writes to a database, calls an external API, and waits for a human approval can run for minutes, hours, or days. Without a durable orchestration layer, any transient failure restarts the loop from scratch, re-billing API calls, duplicating side effects, and losing accumulated context.

---

## Temporal

[Temporal](https://goteleport.com/docs/) is an open-source, language-agnostic platform for building reliable distributed applications. It introduces the concept of **Durable Execution** — the guarantee that workflow logic runs to completion regardless of infrastructure failures.

### Core Concepts

| Concept | Definition |
|---|---|
| **Workflow** | A fault-tolerant function that orchestrates Activities; can run for years |
| **Activity** | A single, retriable unit of work (API call, DB write, ML inference) |
| **Worker** | A process that polls Temporal for tasks and executes Workflows and Activities |
| **Event History** | An append-only log of every Command and Event in a workflow's lifetime — the source of truth for recovery |
| **Namespace** | A logical isolation boundary; separate event histories, task queues, and quotas |
| **Task Queue** | A durable channel connecting a Workflow/Activity to a set of Workers |
| **Signal / Query** | Mechanisms for external code to send data to, or read state from, a running workflow |

### Architecture

Temporal separates **execution** (stateless services) from **storage** (durable persistence):

<img src="https://docs.temporal.io/assets/images/temporal-system-simple-bbe37d1a86a71b86c23d97e676b4f6aa.svg" alt="Temporal cluster architecture" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**Temporal cluster: stateless services backed by a durable persistence layer**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

The cluster consists of four stateless services — **Frontend**, **History**, **Matching**, and **Worker** — each scaling independently. All durable state flows through two distinct stores:

- **Persistence Store** — workflow state, event history, timers, and task queues. Requires strong consistency and low-latency reads/writes.
- **Visibility Store** — a queryable index of workflow executions by status, type, and custom search attributes. Can tolerate slightly higher latency and is optimised for range scans.

### Why CockroachDB for Temporal?

Temporal officially supports PostgreSQL, MySQL, SQLite, and Cassandra. CockroachDB is a natural fit for the persistence store because it brings:

- **Distributed, strongly-consistent SQL** — the same ACID guarantees PostgreSQL provides, at any scale
- **Active-active multi-region** — Temporal history shards can be distributed across regions without manual replication
- **Automatic failover** — node failures are transparent to Temporal's services
- **Horizontal scalability** — scale reads and writes without sharding logic in the application
- **PostgreSQL wire protocol** — Temporal's existing `postgres12` plugin works directly

### Deploying Temporal on CockroachDB

#### Step 1 — Provision CockroachDB databases and user

```sql
CREATE DATABASE temporal;
CREATE DATABASE temporal_visibility;
CREATE USER temporal WITH PASSWORD 'temporal';
GRANT ALL ON DATABASE temporal TO temporal;
GRANT ALL ON DATABASE temporal_visibility TO temporal;
```

#### Step 2 — Initialize the persistence schema

The main schema works with CockroachDB out of the box via Temporal's SQL tool:

```bash
temporal-sql-tool \
  --plugin postgres12 \
  --ep "<crdb-host>:26257" \
  --db temporal \
  --tls \
  --tls-ca-file /certs/ca.crt \
  --tls-cert-file /certs/client.temporal.crt \
  --tls-key-file /certs/client.temporal.key \
  setup-schema -v 0.0

temporal-sql-tool \
  --plugin postgres12 \
  --ep "<crdb-host>:26257" \
  --db temporal \
  --tls ... \
  update-schema -d ./schema/postgresql/v12/temporal/versioned
```

#### Step 3 — Fix the visibility schema for CockroachDB

> **This is the critical fix.** Temporal's advanced visibility schema contains `CREATE EXTENSION IF NOT EXISTS btree_gin` — a PostgreSQL-only extension that enables B-tree operators on GIN indexes. CockroachDB does not support this extension, and the schema migration **fails** at this line.

The root cause is this migration in `schema/postgresql/v12/visibility/versioned/v1.1/manifest.json`:

```sql
-- PostgreSQL only — FAILS on CockroachDB
CREATE EXTENSION IF NOT EXISTS btree_gin;
CREATE INDEX custom_search_attributes_idx
  ON executions_visibility
  USING gin(search_attributes jsonb_path_ops);
```

**The fix**: bypass the standard migration tool for the visibility database and apply a CockroachDB-compatible schema directly. CockroachDB natively supports inverted indexes on JSONB columns without any extension:

```sql
-- CockroachDB-compatible visibility schema
CREATE TABLE executions_visibility (
  namespace_id           VARCHAR(64)   NOT NULL,
  run_id                 VARCHAR(64)   NOT NULL,
  start_time             TIMESTAMPTZ   NOT NULL,
  execution_time         TIMESTAMPTZ   NOT NULL,
  workflow_id            VARCHAR(255)  NOT NULL,
  workflow_type_name     VARCHAR(255)  NOT NULL,
  status                 INT4          NOT NULL,
  close_time             TIMESTAMPTZ,
  history_length         BIGINT,
  history_size_bytes     BIGINT,
  execution_duration     BIGINT,
  state_transition_count BIGINT,
  memo                   BYTEA,
  encoding               VARCHAR(64)   NOT NULL,
  task_queue             VARCHAR(255)  NOT NULL DEFAULT '',
  search_attributes      JSONB,
  parent_workflow_id     VARCHAR(255),
  parent_run_id          VARCHAR(255),
  root_workflow_id       VARCHAR(255)  NOT NULL DEFAULT '',
  root_run_id            VARCHAR(255)  NOT NULL DEFAULT '',
  PRIMARY KEY (namespace_id, run_id)
);

-- Standard B-tree indexes — work identically on CockroachDB
CREATE INDEX by_type_start_time
  ON executions_visibility (namespace_id, workflow_type_name, start_time DESC, run_id);
CREATE INDEX by_workflow_id_start_time
  ON executions_visibility (namespace_id, workflow_id, start_time DESC, run_id);
CREATE INDEX by_status_start_time
  ON executions_visibility (namespace_id, status, start_time DESC, run_id);
CREATE INDEX by_close_time
  ON executions_visibility (namespace_id, status, close_time DESC, run_id)
  WHERE close_time IS NOT NULL;

-- CockroachDB native inverted index replaces btree_gin GIN index
CREATE INVERTED INDEX by_search_attributes
  ON executions_visibility (search_attributes);
```

Initialize the visibility database using this schema file directly:

```bash
cockroach sql \
  --url "postgresql://temporal@<crdb-host>:26257/temporal_visibility" \
  --certs-dir=/certs \
  --file ./crdb_visibility_schema.sql
```

#### Step 4 — Configure Temporal server

```yaml
persistence:
  defaultStore: crdb-default
  visibilityStore: crdb-visibility
  numHistoryShards: 512
  datastores:
    crdb-default:
      sql:
        pluginName: "postgres12"
        databaseName: "temporal"
        connectAddr: "<crdb-host>:26257"
        connectProtocol: "tcp"
        user: "temporal"
        password: "${TEMPORAL_DB_PASSWORD}"
        maxConns: 20
        maxIdleConns: 20
        maxConnLifetime: "1h"
        tls:
          enabled: true
          caFile: "/certs/ca.crt"
          certFile: "/certs/client.temporal.crt"
          keyFile: "/certs/client.temporal.key"
          serverName: "<crdb-host>"
    crdb-visibility:
      sql:
        pluginName: "postgres12"
        databaseName: "temporal_visibility"
        connectAddr: "<crdb-host>:26257"
        connectProtocol: "tcp"
        user: "temporal"
        password: "${TEMPORAL_DB_PASSWORD}"
        maxConns: 10
        maxIdleConns: 10
        maxConnLifetime: "1h"
        tls:
          enabled: true
          caFile: "/certs/ca.crt"
          certFile: "/certs/client.temporal.crt"
          keyFile: "/certs/client.temporal.key"
```

#### Step 5 — Write your first durable agent workflow

```python
from temporalio import workflow, activity
from temporalio.client import Client
from temporalio.worker import Worker
from datetime import timedelta

@activity.defn
async def call_llm(prompt: str) -> str:
    # Any external call — billed once, never re-executed on retry
    return await my_llm_client.complete(prompt)

@activity.defn
async def write_result(result: str) -> None:
    await db.insert(result)

@workflow.defn
class AgentWorkflow:
    @workflow.run
    async def run(self, task: str) -> str:
        # Each activity executes exactly once despite crashes
        response = await workflow.execute_activity(
            call_llm, task,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        await workflow.execute_activity(
            write_result, response,
            start_to_close_timeout=timedelta(seconds=30)
        )
        return response
```

---

## DBOS

[DBOS](https://dbos.dev/) takes a fundamentally different approach: rather than deploying a dedicated orchestration cluster, it embeds durable execution **directly into your application** using the database you already have. Your database is not just a data store — it is the execution engine.

### Core Concepts

| Concept | Definition |
|---|---|
| **`@DBOS.workflow()`** | Decorator that makes a Python function durable — state is persisted to the database before each step |
| **`@DBOS.step()`** | A unit of work inside a workflow; executes at least once but never re-executes after completion |
| **Workflow ID** | The idempotency key; launching the same workflow ID twice is safe and returns the existing execution |
| **`DBOS.set_event()`** | Publishes a named value from inside a workflow for external consumers to read |
| **`DBOS.get_event()`** | Polls a workflow for a named event value with an optional timeout |
| **System Database** | The PostgreSQL-compatible database where DBOS stores all workflow state, step completions, and events |

### Architecture

<img src="/assets/img/dbos-schema.png" alt="DBOS system database schema" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**DBOS system database schema — workflow state lives in your database, not in a separate service**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

DBOS manages three categories of tables in the system database:

- **Workflow status table** — one row per workflow execution, tracking ID, status, and function inputs
- **Operation outputs table** — one row per completed step, storing the serialised return value for replay
- **Events table** — named key-value pairs published within workflows and consumed via `get_event`

When a process crashes and restarts, DBOS replays the workflow function against the saved step outputs. Any step whose result is already in the database is **skipped instantly** — only incomplete steps are re-executed.

### DBOS on CockroachDB

Because DBOS uses the PostgreSQL wire protocol, it connects to CockroachDB directly. However, there are two required configuration changes:

**1. Disable `LISTEN/NOTIFY`**

PostgreSQL's `LISTEN/NOTIFY` is used by DBOS to wake up waiting workflows without polling. CockroachDB does not implement this mechanism. You must disable it explicitly:

```python
from dbos import DBOS, DBOSConfig
from sqlalchemy import create_engine
import os

database_url = os.environ["DBOS_COCKROACHDB_URL"]
engine = create_engine(database_url)

config: DBOSConfig = {
    "name": "my-agent-app",
    "system_database_url": database_url,
    # Pass a pre-built SQLAlchemy engine so DBOS uses the CockroachDB driver
    "system_database_engine": engine,
    # CockroachDB does not support LISTEN/NOTIFY — use polling instead
    "use_listen_notify": False,
}
DBOS(config=config)
```

**2. Set the system database URL**

In `dbos-config.yaml`, point the system database at CockroachDB using the standard CockroachDB PostgreSQL connection string:

```yaml
name: my-agent-app
language: python
runtimeConfig:
  start:
    - python3 app/main.py
system_database_url: ${DBOS_COCKROACHDB_URL}
```

Set the environment variable with your CockroachDB cluster's connection string:

```bash
export DBOS_COCKROACHDB_URL="postgresql://dbos_user:password@<crdb-host>:26257/dbos_system?sslmode=verify-full&sslrootcert=/certs/ca.crt"
```

### A Complete DBOS Agentic Workflow on CockroachDB

The following example shows a three-step durable agent workflow backed by CockroachDB. The workflow publishes progress events after each step, which a frontend can poll in real time. If the process crashes mid-execution, restarting it resumes from the last completed step — no re-billing, no duplicate writes.

```python
import os
import time
import uvicorn
from dbos import DBOS, DBOSConfig, SetWorkflowID
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine

app = FastAPI()

# ── CockroachDB connection ──────────────────────────────────────────────────
database_url = os.environ["DBOS_COCKROACHDB_URL"]
engine = create_engine(database_url)

config: DBOSConfig = {
    "name": "agent-workflow",
    "system_database_url": database_url,
    "system_database_engine": engine,
    "use_listen_notify": False,   # Required: CockroachDB has no LISTEN/NOTIFY
}
DBOS(config=config)

STEPS_EVENT = "steps_event"

# ── Workflow steps ──────────────────────────────────────────────────────────

@DBOS.step()
def retrieve_context(task: str) -> str:
    """Step 1 — retrieve relevant context from the knowledge base."""
    time.sleep(3)
    DBOS.logger.info(f"Context retrieved for: {task}")
    return f"context_for_{task}"

@DBOS.step()
def call_agent(context: str) -> str:
    """Step 2 — call the LLM/agent with the context."""
    time.sleep(3)
    DBOS.logger.info("Agent invocation completed")
    return f"agent_response_given_{context}"

@DBOS.step()
def persist_result(response: str) -> None:
    """Step 3 — write the agent's output to the application database."""
    time.sleep(3)
    DBOS.logger.info(f"Result persisted: {response}")

# ── Durable workflow ────────────────────────────────────────────────────────

@DBOS.workflow()
def agent_workflow(task: str) -> None:
    context = retrieve_context(task)
    DBOS.set_event(STEPS_EVENT, 1)

    response = call_agent(context)
    DBOS.set_event(STEPS_EVENT, 2)

    persist_result(response)
    DBOS.set_event(STEPS_EVENT, 3)

# ── HTTP endpoints ──────────────────────────────────────────────────────────

@app.post("/agent/{task_id}")
def start_agent(task_id: str, task: str) -> dict:
    """Idempotently launch a durable agent workflow."""
    with SetWorkflowID(task_id):
        DBOS.start_workflow(agent_workflow, task)
    return {"workflow_id": task_id, "status": "started"}

@app.get("/agent/{task_id}/progress")
def get_progress(task_id: str) -> dict:
    """Poll workflow progress (0-3 completed steps)."""
    try:
        step = DBOS.get_event(task_id, STEPS_EVENT, timeout_seconds=0)
    except KeyError:
        return {"completed_steps": 0}
    return {"completed_steps": step if step is not None else 0}

if __name__ == "__main__":
    DBOS.launch()
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Install dependencies and run:

```bash
pip install "dbos[otel]==2.15.0" "fastapi[standard]"
export DBOS_COCKROACHDB_URL="postgresql://dbos_user:pass@localhost:26257/dbos_system?sslmode=disable"
python3 app/main.py
```

---

## Temporal vs DBOS — When to Use Which

| Dimension | Temporal | DBOS |
|---|---|---|
| **Deployment model** | Dedicated cluster (self-hosted or Temporal Cloud) | Library embedded in your application |
| **Storage** | Separate persistence + visibility stores | System tables in your existing database |
| **CockroachDB fit** | Excellent — but requires the `btree_gin` visibility fix | Native — CRDB is a first-class target |
| **Operational overhead** | Higher — Temporal cluster to manage | Lower — no separate service |
| **Scale target** | Multi-tenant SaaS, millions of workflows | Single-app or tightly-integrated services |
| **Language support** | Go, Java, TypeScript, Python | Python, TypeScript |
| **Best for agentic AI** | Coordinating many independent agents across services | Embedding durable execution into a FastAPI / LLM app |

### CockroachDB as the Common Backbone

Whether you choose Temporal or DBOS, CockroachDB brings the same three properties to your workflow persistence:

- **Serializable isolation** — no lost updates or phantom reads even under concurrent workflow execution
- **Multi-region replication** — workflow state is durable across data-center failures without manual failover
- **Horizontal scalability** — add nodes to handle more concurrent workflows without re-sharding or downtime

For Temporal, CockroachDB acts as a drop-in replacement for PostgreSQL with one schema fix. For DBOS, CockroachDB requires two configuration lines and delivers a globally distributed system database that PostgreSQL cannot match at scale.

---

## Next Steps

Both Temporal and DBOS lower the barrier to building resilient agentic AI systems. Pairing them with CockroachDB removes the last single point of failure from your workflow infrastructure.

- For Temporal: clone the [Temporal Docker Compose](https://github.com/temporalio/docker-compose) sample and replace the PostgreSQL image with CockroachDB, applying the visibility schema fix above.
- For DBOS: set `DBOS_COCKROACHDB_URL`, add the two config lines, and your first durable agent workflow is running in minutes.

## See Also

- [Temporal Documentation](https://docs.temporal.io/)
- [DBOS Documentation](https://docs.dbos.dev/)
- [DBOS Python Workflow Tutorial](https://docs.dbos.dev/python/tutorials/workflow-tutorial)
- [CockroachDB Cloud](https://cockroachlabs.cloud/)
- [CockroachDB Distributed SQL](https://www.cockroachlabs.com/blog/what-is-distributed-sql/)
