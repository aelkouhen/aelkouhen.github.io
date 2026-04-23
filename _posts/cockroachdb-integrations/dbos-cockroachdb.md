---
date: 2026-05-28
layout: post
title: "Embedded Scalable Execution with DBOS and CockroachDB"
subtitle: "How DBOS turns your database into a workflow engine — and why CockroachDB removes the scalability ceiling"
cover-img: /assets/img/cover-dbos.webp
thumbnail-img: /assets/img/cover-dbos.webp
share-img: /assets/img/cover-dbos.webp
tags: [integrations, CockroachDB, dbos, workflow, orchestration, Artificial Intelligence, Agentic AI]
lang: en
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

Modern AI applications are no longer single-shot inference calls. They are long-running agents that plan, act, observe, and retry across time. An AI agent loop that retrieves context from a vector store, calls an LLM, writes results to a database, waits for human approval, and then triggers downstream actions can run for minutes, hours, or even days. Without a **durable orchestration layer**, any transient infrastructure failure restarts the entire loop from scratch: re-billing expensive LLM calls, duplicating side effects, and losing all accumulated context.

Platforms like [Temporal](https://temporal.io/) solve this by deploying a dedicated orchestration cluster — a separate server process with its own persistence backend — that your application workers connect to over gRPC. This is powerful, but it means an extra service to provision, monitor, scale, and keep available before your first workflow can run.

[DBOS](https://dbos.dev/) takes a fundamentally different approach: it embeds durable execution **directly into your application** as a Python or TypeScript library, using the database you already have. There is no orchestration server, no task queue, no sidecar process. Your application writes workflow state to tables in its own database as a natural side effect of execution, and recovers from those tables on restart. Pair DBOS with [CockroachDB](https://www.cockroachlabs.com/) and you get a globally distributed, self-healing execution platform with no additional infrastructure to manage.

A **durable workflow** is a function whose execution state (which steps have completed, what they returned, what inputs were given) is persisted to the database after every step. If the process crashes mid-run, it restarts and replays from the last committed step: no work is lost, no step is re-executed, no external side effect is duplicated.

---

## What Is DBOS?

DBOS is a Python and TypeScript library that decorates ordinary functions with durable execution guarantees. There is no server to deploy, no task queue to operate, no separate persistence cluster to manage. DBOS writes workflow state to tables in your application database as a side effect of normal execution, and recovers from those tables on restart.

### Core Concepts

| Concept | Definition |
|---|---|
| **`@DBOS.workflow()`** | Decorator that makes a Python function durable; state is persisted before each step |
| **`@DBOS.step()`** | A unit of work inside a workflow; executes at least once but never re-executes after completion |
| **Workflow ID** | The idempotency key; launching the same workflow ID twice is safe and returns the existing execution |
| **`DBOS.set_event()`** | Publishes a named value from inside a workflow for external consumers to read |
| **`DBOS.get_event()`** | Polls a workflow for a named event value with an optional timeout |
| **System Database** | The PostgreSQL-compatible database where DBOS stores all workflow state, step completions, and events |

---

## Architecture

DBOS is implemented entirely as an open-source library embedded in your application — there is no orchestration server and no external dependencies except a PostgreSQL-compatible database. While your application runs, DBOS checkpoints workflow and step state to that database. On failure, it uses those checkpoints to resume each workflow from the last completed step.

<img src="/assets/img/dbos-architecture.png" alt="DBOS architecture: library embedded in the application process" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**DBOS architecture: the durable execution library lives inside your application process — the only external dependency is a Postgres-compatible database**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

### Checkpointing model

Every workflow execution produces a fixed number of database writes regardless of complexity:

- **One write at workflow start**: inputs are persisted before any step runs
- **One write per completed step**: the step's return value is stored so replay can skip it
- **One write at workflow end**: the final status is committed

Write sizes are proportional to your inputs and outputs. For large payloads (files, embeddings), the recommended pattern is to store them externally (e.g., S3) and have steps return pointers only.

### Distributed deployment

DBOS scales naturally to a fleet of servers. All application servers connect to the **same system database** — this is the only coordination point. By default, each workflow runs on a single server; durable queues distribute work across the fleet with configurable rate and concurrency limits.

For multi-application setups (e.g., an API server, a data-ingestion service, and an AI agent loop), each application connects to its own isolated system database. A single physical database host can serve multiple system databases. The **DBOS Client** lets external code enqueue jobs and monitor results across application boundaries.

### Workflow recovery

When a process crashes, DBOS detects incomplete workflows and replays them in three steps:

1. **Detection** — at startup, DBOS scans for pending workflows. In distributed deployments, Conductor coordinates detection across the fleet.
2. **Restart** — each interrupted workflow is called again with its original checkpointed inputs.
3. **Resume** — as the workflow re-executes, every step whose output is already checkpointed is skipped instantly. Execution resumes from the first un-checkpointed step.

Two requirements for safe recovery:
- **Determinism**: the workflow function must produce the same steps in the same order given the same inputs. Non-deterministic operations (DB access, API calls, random numbers, timestamps) must live inside `@DBOS.step()` decorators, never directly in the workflow body.
- **Idempotency**: steps may be retried on recovery and must be safe to re-execute.

### Conductor (optional)

For production deployments, DBOS recommends connecting to **Conductor** — a management service that adds distributed recovery coordination, workflow dashboards, and queue observability. Conductor is architecturally off the critical path: each server opens an outbound websocket connection to it, and if the connection drops the application continues operating normally. Conductor has no direct access to your database and is never involved in workflow execution itself.

<img src="/assets/img/dbos-conductor-architecture.png" alt="DBOS Conductor architecture" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**Conductor is out of band: application servers open outbound websocket connections to it for observability and recovery — never for workflow execution**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

---

## Why CockroachDB for DBOS?

DBOS uses the PostgreSQL wire protocol, so it connects to CockroachDB directly without any driver changes. What CockroachDB adds over a single-node PostgreSQL is the persistence tier you always wanted but couldn't justify operating separately:

- **Serializable isolation**: concurrent workflow executions never produce lost updates or phantom reads
- **Multi-region active-active replication**: workflow state is durable across data-center failures without manual intervention
- **Horizontal scalability**: the system database scales with your application without re-sharding
- **Automatic failover**: CockroachDB node failures are transparent to DBOS, which simply retries on the next available node

When DBOS connects to CockroachDB, it provisions three categories of tables in the system database:

<img src="/assets/img/dbos-schema.png" alt="DBOS system database schema in CockroachDB" style="width:60%;margin:1.5rem auto;display:block;">
{: .mx-auto.d-block :}
**Tables created by DBOS in CockroachDB: workflow state, step outputs, and events — all in your existing database**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

- **Workflow status table**: one row per execution, tracking ID, status, and function inputs
- **Operation outputs table**: one row per completed step, storing the serialised return value for replay
- **Events table**: named key-value pairs published within workflows and consumed via `get_event`

For teams that want globally resilient agentic workflows without the complexity of a Temporal cluster, DBOS + CockroachDB is the lowest-overhead path.

| Capability | DBOS + CockroachDB |
|---|---|
| **No extra infrastructure** | Durable execution runs inside your FastAPI / application process |
| **Exactly-once steps** | Steps never re-execute after their output is committed to CockroachDB |
| **Idempotent launches** | Same workflow ID always returns the existing execution |
| **Global durability** | CockroachDB multi-region replication protects workflow state across regions |
| **Zero driver changes** | PostgreSQL wire protocol; no CockroachDB-specific SDK required |
| **Observable progress** | `set_event` / `get_event` expose real-time step completion to frontends |

---

## Deploying DBOS on CockroachDB

There are two required configuration changes when using CockroachDB instead of PostgreSQL.

### Prerequisites

| Requirement | Details |
|---|---|
| **Python 3.10+** | DBOS 2.x requires Python 3.10 or later |
| **CockroachDB cluster** | A running CockroachDB instance (local, CockroachDB Cloud, or self-hosted) |
| **System database** | A dedicated database for DBOS state — create it once: `CREATE DATABASE dbos_system;` |
| **Python packages** | `dbos[otel]`, `fastapi[standard]`, `psycopg2-binary`, `sqlalchemy-cockroachdb`, `uvicorn` |

```bash
pip install "dbos[otel]==2.15.0" "fastapi[standard]" psycopg2-binary sqlalchemy-cockroachdb
```

```bash
export DBOS_COCKROACHDB_URL="postgresql://<user>:<password>@<crdb-host>:26257/dbos_system?sslmode=verify-full&sslrootcert=/certs/ca.crt"
```

### 1. Disable `LISTEN/NOTIFY`

PostgreSQL's `LISTEN/NOTIFY` mechanism is used by DBOS to wake up waiting workflows without polling. CockroachDB does not implement this mechanism, so it must be disabled explicitly; DBOS falls back to polling automatically:

```python
from dbos import DBOS, DBOSConfig
from sqlalchemy import create_engine
import os

database_url = os.environ["DBOS_COCKROACHDB_URL"]
# SQLAlchemy's postgresql dialect cannot parse CockroachDB's version string;
# the cockroachdb dialect (sqlalchemy-cockroachdb) handles it correctly.
crdb_url = database_url.replace("postgresql://", "cockroachdb://", 1)
engine = create_engine(crdb_url)

config: DBOSConfig = {
    "name": "my-agent-app",
    "system_database_url": database_url,
    # Pass a pre-built SQLAlchemy engine so DBOS uses the CockroachDB driver
    "system_database_engine": engine,
    # CockroachDB does not support LISTEN/NOTIFY; use polling instead
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

The following example implements a three-step durable agent workflow backed by CockroachDB. The workflow publishes progress events after each step that a frontend can poll in real time. If the process crashes mid-execution, restarting it resumes from the last completed step: no re-billing, no duplicate writes, no lost context.

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
# Use cockroachdb:// dialect so SQLAlchemy can parse CockroachDB's version string
crdb_url = database_url.replace("postgresql://", "cockroachdb://", 1)
engine = create_engine(crdb_url)

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
    """Step 1: retrieve relevant context from the knowledge base."""
    time.sleep(3)
    DBOS.logger.info(f"Context retrieved for: {task}")
    return f"context_for_{task}"

@DBOS.step()
def call_agent(context: str) -> str:
    """Step 2: call the LLM/agent with the context."""
    time.sleep(3)
    DBOS.logger.info("Agent invocation completed")
    return f"agent_response_given_{context}"

@DBOS.step()
def persist_result(response: str) -> None:
    """Step 3: write the agent's output to the application database."""
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
pip install "dbos[otel]==2.15.0" "fastapi[standard]" psycopg2-binary sqlalchemy-cockroachdb
export DBOS_COCKROACHDB_URL="postgresql://dbos_user:pass@localhost:26257/dbos_system?sslmode=disable"
python3 app/main.py
```

---

## Scalability Benchmarking

The DBOS engineering team [benchmarked DBOS durable workflow throughput on PostgreSQL](https://dbos.dev/blog/benchmarking-workflow-execution-scalability-on-postgres), reaching **144K raw database writes per second** on a single co-located AWS RDS instance (`db.m7i.24xlarge` — 96 vCPU, 384 GB RAM, 120K IOPS). We ran the equivalent benchmark — real DBOS 2-step workflows, measuring end-to-end completion throughput — against a **3-node CockroachDB cluster co-located in AWS us-east-1** (`3× m7i.8xlarge` — 96 vCPU total). The benchmark client ran inside us-east-1, eliminating all WAN overhead.

> **Benchmark artefacts:** scripts and raw results are in the repository under [`assets/bench/dbos-cockroachdb/`](https://github.com/aelkouhen/aelkouhen.github.io/tree/main/assets/bench/dbos-cockroachdb):
> [`bench_direct.py`](https://github.com/aelkouhen/aelkouhen.github.io/blob/main/assets/bench/dbos-cockroachdb/bench_direct.py) · [`charts_v5.py`](https://github.com/aelkouhen/aelkouhen.github.io/blob/main/assets/bench/dbos-cockroachdb/charts_v5.py) · [`results_coloc.json`](https://github.com/aelkouhen/aelkouhen.github.io/blob/main/assets/bench/dbos-cockroachdb/results_coloc.json)

### Results — co-located throughput and latency

<img src="/assets/bench/dbos-cockroachdb/dbos-bench-crdb-throughput.png" alt="CockroachDB DBOS workflow throughput c=1 to c=512, co-located" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**Throughput scales linearly from 12 wf/s at c=1 to 117 wf/s at c=32, then plateaus — the 3-node cluster is saturated. Each additional node adds ~39 wf/s.**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

<img src="/assets/bench/dbos-cockroachdb/dbos-bench-crdb-latency.png" alt="CockroachDB workflow latency p50 and p95 under load, co-located" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**p50 latency is 72 ms at peak throughput (c=8) — each 2-step DBOS workflow requires multiple sequential Raft consensus rounds, each achieving quorum across 2 of 3 nodes.**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

| Concurrency | Throughput (wf/s) | p50 (ms) | p95 (ms) |
|:-----------:|:-----------------:|:--------:|:--------:|
| 1 | 12.4 | 80 | 87 |
| 4 | 53.4 | 74 | 89 |
| **8** | **104.9** | **72** | **90** |
| 16 | 106.3 | 138 | 177 |
| 32 | **116.6 (peak)** | 251 | 316 |
| 64 | 116.3 | 526 | 598 |
| 256 | 113.5 | 2,216 | 2,304 |

### The scalability argument

The 3-node cluster saturates at **~117 wf/s** — that is the capacity of *these three nodes*, not a limit of CockroachDB. Add more nodes and throughput scales proportionally.

<img src="/assets/bench/dbos-cockroachdb/dbos-bench-linear-vs-ceiling.png" alt="CockroachDB linear scale-out: 117 wf/s measured on 3 nodes, projects linearly with additional nodes" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**Measured baseline: 117 wf/s on 3 nodes. Each node adds ~39 wf/s. PostgreSQL's WAL is a single-node write path — it cannot be distributed across additional instances.**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

PostgreSQL's **Write-Ahead Log serialises every write through a single flush path**. Once that path is saturated, no additional hardware increases write throughput — you can scale reads with replicas, but writes are bounded by one node forever. CockroachDB replaces the single WAL with a **distributed Raft log**: each node flushes its own log, and writes are spread across the cluster. The throughput ceiling rises with every node you add.

### Summary

| | PostgreSQL | CockroachDB (3 nodes) | CockroachDB (N nodes) |
|---|---|---|---|
| Peak wf/s | Single-node ceiling | **117 wf/s (measured)** | **~39 × N wf/s** |
| p50 at peak concurrency | Sub-ms (local WAL) | ~72 ms (Raft quorum) | ~72 ms |
| Write scale-out | **No — WAL is one node** | Yes | **Yes — linear** |
| Node failure | Manual failover | Automatic | Automatic |
| Multi-region durability | External tooling | Built-in | Built-in |

CockroachDB's distributed Raft consensus adds latency per write compared to a local WAL — that is the cost of the guarantee that no single node is a write bottleneck. The payoff: **need more throughput? Add nodes. There is no ceiling.**

---

## See Also

- [DBOS Documentation](https://docs.dbos.dev/)
- [DBOS Python Workflow Tutorial](https://docs.dbos.dev/python/tutorials/workflow-tutorial)
- [CockroachDB Cloud](https://cockroachlabs.cloud/)
- [CockroachDB Distributed SQL](https://www.cockroachlabs.com/blog/what-is-distributed-sql/)
- [Temporal + CockroachDB: Cluster-Based Durable Execution](/2026-04-24-temporal-cockroachdb/)
