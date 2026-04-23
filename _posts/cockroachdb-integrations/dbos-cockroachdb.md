---
date: 2026-04-24
layout: post
title: "Embedded Durable Execution with DBOS and CockroachDB"
subtitle: "How DBOS turns your existing database into a workflow engine — and why CockroachDB makes it globally distributed"
tags: [integrations, CockroachDB, dbos, workflow, orchestration, durable-execution]
lang: en
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

Most workflow orchestration platforms require you to deploy and operate a dedicated cluster alongside your application. [DBOS](https://dbos.dev/) takes a fundamentally different approach: it embeds durable execution **directly into your application** using the database you already have. Your database is not just a data store — it is the execution engine. Pair DBOS with [CockroachDB](https://www.cockroachlabs.com/) and you get a globally distributed, self-healing execution platform with no additional infrastructure to manage.

A **durable workflow** is a function whose execution state — which steps have completed, what they returned, what inputs were given — is persisted to the database after every step. If the process crashes mid-run, it restarts and replays from the last committed step: no work is lost, no step is re-executed, no external side effect is duplicated.

---

## What Is DBOS?

DBOS is a Python and TypeScript library that decorates ordinary functions with durable execution guarantees. There is no server to deploy, no task queue to operate, no separate persistence cluster to manage. DBOS writes workflow state to tables in your application database as a side effect of normal execution, and recovers from those tables on restart.

### Core Concepts

| Concept | Definition |
|---|---|
| **`@DBOS.workflow()`** | Decorator that makes a Python function durable — state is persisted before each step |
| **`@DBOS.step()`** | A unit of work inside a workflow; executes at least once but never re-executes after completion |
| **Workflow ID** | The idempotency key; launching the same workflow ID twice is safe and returns the existing execution |
| **`DBOS.set_event()`** | Publishes a named value from inside a workflow for external consumers to read |
| **`DBOS.get_event()`** | Polls a workflow for a named event value with an optional timeout |
| **System Database** | The PostgreSQL-compatible database where DBOS stores all workflow state, step completions, and events |

---

## Architecture

DBOS manages three categories of tables in the system database:

<img src="/assets/img/dbos-schema.png" alt="DBOS system database schema" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**DBOS system database schema — workflow state lives in your database, not in a separate service**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

- **Workflow status table** — one row per workflow execution, tracking ID, status, and function inputs
- **Operation outputs table** — one row per completed step, storing the serialised return value for replay
- **Events table** — named key-value pairs published within workflows and consumed via `get_event`

When a process crashes and restarts, DBOS replays the workflow function against the saved step outputs. Any step whose result is already in the database is **skipped instantly** — only incomplete steps are re-executed. The result is exactly-once execution semantics without a dedicated orchestration service.

---

## Why CockroachDB for DBOS?

DBOS uses the PostgreSQL wire protocol, so it connects to CockroachDB directly without any driver changes. What CockroachDB adds over a single-node PostgreSQL is the persistence tier you always wanted but couldn't justify operating separately:

- **Serializable isolation** — concurrent workflow executions never produce lost updates or phantom reads
- **Multi-region active-active replication** — workflow state is durable across data-center failures without manual intervention
- **Horizontal scalability** — the system database scales with your application without re-sharding
- **Automatic failover** — CockroachDB node failures are transparent to DBOS, which simply retries on the next available node

For teams that want globally resilient agentic workflows without the complexity of a Temporal cluster, DBOS + CockroachDB is the lowest-overhead path.

---

## Deploying DBOS on CockroachDB

There are two required configuration changes when using CockroachDB instead of PostgreSQL.

### 1. Disable `LISTEN/NOTIFY`

PostgreSQL's `LISTEN/NOTIFY` mechanism is used by DBOS to wake up waiting workflows without polling. CockroachDB does not implement this mechanism, so it must be disabled explicitly — DBOS falls back to polling automatically:

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

### 2. Set the system database URL

In `dbos-config.yaml`, point the system database at CockroachDB using the standard PostgreSQL connection string format:

```yaml
name: my-agent-app
language: python
runtimeConfig:
  start:
    - python3 app/main.py
system_database_url: ${DBOS_COCKROACHDB_URL}
```

Set the environment variable with your CockroachDB connection string:

```bash
export DBOS_COCKROACHDB_URL="postgresql://dbos_user:password@<crdb-host>:26257/dbos_system?sslmode=verify-full&sslrootcert=/certs/ca.crt"
```

---

## A Complete DBOS Agentic Workflow on CockroachDB

The following example implements a three-step durable agent workflow backed by CockroachDB. The workflow publishes progress events after each step that a frontend can poll in real time. If the process crashes mid-execution, restarting it resumes from the last completed step — no re-billing, no duplicate writes, no lost context.

```python
import os
import time
import uvicorn
from dbos import DBOS, DBOSConfig, SetWorkflowID
from fastapi import FastAPI
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

## Key Benefits

| Capability | DBOS + CockroachDB |
|---|---|
| **No extra infrastructure** | Durable execution runs inside your FastAPI / application process |
| **Exactly-once steps** | Steps never re-execute after their output is committed to CockroachDB |
| **Idempotent launches** | Same workflow ID always returns the existing execution |
| **Global durability** | CockroachDB multi-region replication protects workflow state across regions |
| **Zero driver changes** | PostgreSQL wire protocol — no CockroachDB-specific SDK required |
| **Observable progress** | `set_event` / `get_event` expose real-time step completion to frontends |

The two configuration changes — `use_listen_notify: False` and a CockroachDB connection URL — are everything needed to make the DBOS system database globally distributed and fault-tolerant.

---

## See Also

- [DBOS Documentation](https://docs.dbos.dev/)
- [DBOS Python Workflow Tutorial](https://docs.dbos.dev/python/tutorials/workflow-tutorial)
- [CockroachDB Cloud](https://cockroachlabs.cloud/)
- [CockroachDB Distributed SQL](https://www.cockroachlabs.com/blog/what-is-distributed-sql/)
- [Temporal + CockroachDB — Cluster-Based Durable Execution](/2026-04-23-temporal-cockroachdb/)
