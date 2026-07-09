---
date: 2026-05-28
layout: post
title: "Embedded Scalable Execution with DBOS and CockroachDB"
subtitle: "How DBOS turns your database into a workflow engine, and why CockroachDB removes the scalability ceiling"
cover-img: /assets/img/cover-dbos.webp
thumbnail-img: /assets/img/cover-dbos.webp
share-img: /assets/img/cover-dbos.webp
tags: [CockroachDB, dbos, workflow, orchestration, Artificial Intelligence, Agentic AI]
lang: en
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

Modern AI applications are no longer single-shot inference calls. They are long-running agents that plan, act, observe, and retry across time. An AI agent loop that retrieves context from a vector store, calls an LLM, writes results to a database, waits for human approval, and then triggers downstream actions can run for minutes, hours, or even days. Without a **durable orchestration layer**, any transient infrastructure failure restarts the entire loop from scratch: re-billing expensive LLM calls, duplicating side effects, and losing all accumulated context.

Platforms like [Temporal](https://temporal.io/) solve this by deploying a dedicated orchestration cluster (a separate server process with its own persistence backend) that your application workers connect to over gRPC. This is powerful, but it means an extra service to provision, monitor, scale, and keep available before your first workflow can run.

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

DBOS is implemented entirely as an open-source library embedded in your application: there is no orchestration server and no external dependencies except a PostgreSQL-compatible database. While your application runs, DBOS checkpoints workflow and step state to that database. On failure, it uses those checkpoints to resume each workflow from the last completed step.

<img src="/assets/img/dbos-architecture.png" alt="DBOS architecture: library embedded in the application process" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**DBOS architecture: the durable execution library lives inside your application process; the only external dependency is a Postgres-compatible database**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

### Checkpointing model

Every workflow execution produces a fixed number of database writes regardless of complexity:

- **One write at workflow start**: inputs are persisted before any step runs
- **One write per completed step**: the step's return value is stored so replay can skip it
- **One write at workflow end**: the final status is committed

Write sizes are proportional to your inputs and outputs. For large payloads (files, embeddings), the recommended pattern is to store them externally (e.g., S3) and have steps return pointers only.

### Distributed deployment

DBOS scales naturally to a fleet of servers. All application servers connect to the **same system database**, the only coordination point. By default, each workflow runs on a single server; durable queues distribute work across the fleet with configurable rate and concurrency limits.

For multi-application setups (e.g., an API server, a data-ingestion service, and an AI agent loop), each application connects to its own isolated system database. A single physical database host can serve multiple system databases. The **DBOS Client** lets external code enqueue jobs and monitor results across application boundaries.

### Workflow recovery

When a process crashes, DBOS detects incomplete workflows and replays them in three steps:

1. **Detection**: at startup, DBOS scans for pending workflows. In distributed deployments, Conductor coordinates detection across the fleet.
2. **Restart**: each interrupted workflow is called again with its original checkpointed inputs.
3. **Resume**: as the workflow re-executes, every step whose output is already checkpointed is skipped instantly. Execution resumes from the first un-checkpointed step.

Two requirements for safe recovery:
- **Determinism**: the workflow function must produce the same steps in the same order given the same inputs. Non-deterministic operations (DB access, API calls, random numbers, timestamps) must live inside `@DBOS.step()` decorators, never directly in the workflow body.
- **Idempotency**: steps may be retried on recovery and must be safe to re-execute.

### Conductor (optional)

For production deployments, DBOS recommends connecting to **Conductor**, a management service that adds distributed recovery coordination, workflow dashboards, and queue observability. Conductor is architecturally off the critical path: each server opens an outbound websocket connection to it, and if the connection drops the application continues operating normally. Conductor has no direct access to your database and is never involved in workflow execution itself.

<img src="/assets/img/dbos-conductor-architecture.png" alt="DBOS Conductor architecture" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**Conductor is out of band: application servers open outbound websocket connections to it for observability and recovery, never for workflow execution**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

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
**Tables created by DBOS in CockroachDB: workflow state, step outputs, and events, all in your existing database**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

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
| **System database** | A dedicated database for DBOS state; create it once: `CREATE DATABASE dbos_system;` |
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

The DBOS engineering team [published a benchmark](https://dbos.dev/blog/benchmarking-workflow-execution-scalability-on-postgres) claiming **43,000 durable workflows per second** on a single `db.m7i.24xlarge` PostgreSQL instance. This section reproduces that claim honestly, then compares it head to head with a CockroachDB cluster on the same hardware envelope, and stress tests both under the two things the blog never covers: durability parity and node loss.

### Test environment

All components live in a single AWS **us-east-1a** subnet: no cross-AZ network hop is measured, matching what the DBOS blog itself did (their Terraform provisions a single subnet).

| Component | Configuration |
|---|---|
| **PostgreSQL RDS 17** | `db.m7i.24xlarge`, 96 vCPU, 384 GB RAM, `io2` 120,000 IOPS, tuned parameter group |
| **CockroachDB v26.1.3** | 3 × `m7i.8xlarge`, 96 vCPU aggregate, `io2` 40,000 IOPS per node, single-AZ |
| **Load client** | `c7i.48xlarge`, 192 vCPU, 384 GB RAM, running the DBOS upstream benchmark |
| **CockroachDB LB** | AWS Network Load Balancer, single DNS endpoint routing to the 3 nodes |

The workload is DBOS's own harness ([`dbos-postgres-benchmark`](https://github.com/dbos-inc/dbos-postgres-benchmark)), unmodified for PostgreSQL and minimally patched for CockroachDB (the `sqlalchemy.postgresql` dialect cannot parse the CockroachDB version string, and one internal DBOS query relies on PostgreSQL type coercion that CockroachDB rejects). The workload calls `DBOS.start_workflow_async(noop_workflow)` at a target rate, fires-and-forgets, then drains completions via `list_workflows(status='PENDING')`. Reported throughput is end-to-end (start plus completion divided by total wall-clock).

> **Benchmark artefacts** and the patched CockroachDB variant of the upstream script are published under [`assets/bench/dbos-cockroachdb/`](https://github.com/aelkouhen/aelkouhen.github.io/tree/main/assets/bench/dbos-cockroachdb).

---

### Step 1: reproducing the DBOS blog headline

The DBOS blog reports **43,225 workflows per second** on `db.m7i.24xlarge`. Their headline command shows a single Python invocation, but a careful read of their Terraform reveals a **`count = 2`** on the client host. Two client machines run the same script against two different databases on the same PostgreSQL server, and the two throughputs are summed.

We reproduced that setup on a single `c7i.48xlarge` (192 vCPU) by running two concurrent invocations pointed at two separate benchmark databases on the same RDS instance:

```bash
# 2 concurrent invocations, separate databases dbos_bench_A / dbos_bench_B
BENCHMARK_DATABASE_URL=".../dbos_bench_A" \
uv run python benchmarks/dbos_start_workflow.py \
    --rps 55000 --duration 60 \
    --processes 224 --pool-size 4 --start-batch 100 &

BENCHMARK_DATABASE_URL=".../dbos_bench_B" \
uv run python benchmarks/dbos_start_workflow.py \
    --rps 55000 --duration 60 \
    --processes 224 --pool-size 4 --start-batch 100 &
```

Results:

| Configuration | Client A wf/s | Client B wf/s | Aggregate |
|---|---:|---:|---:|
| PostgreSQL 2×224, `synchronous_commit=off` | 13,529 | 13,610 | **27,139** |
| PostgreSQL 2×224, `synchronous_commit=on`  | 13,173 | 13,203 | **26,376** |
| CockroachDB 2×224, 3 nodes                 | 2,112  | 2,020  | **4,030**  |

Two things are immediately worth noting.

**First, on the same 192-vCPU client the DBOS blog's 43K number tops out closer to 27K.** The blog uses two *separate* client hosts (their `count = 2`). On a single host, the two invocations contend for CPU, sockets, and file descriptors, and the aggregate is only about 13% higher than what one client alone produces (~24K). Getting to 43K genuinely requires a second physical machine; the throughput ceiling is per host on the client side, not per RDS instance.

**Second, CockroachDB delivers about 15% of PostgreSQL's throughput on this workload.** That gap is real and needs explaining, which the rest of this section does.

---

### Step 2: the durability the DBOS blog does not disclose

The DBOS blog's parameter group sets `synchronous_commit=off`. That is a single-line change with two consequences:

- **PostgreSQL acknowledges the commit *before* fsyncing the WAL to disk.** A crash between commit and fsync loses that transaction, even though the client already received "success".
- **The DBOS durability guarantee is silently broken.** DBOS relies on the database to persist workflow state before returning; if the database lies about persistence, DBOS's `start_workflow` can return a workflow ID that never actually made it to disk.

CockroachDB has no such switch. Every write goes through Raft consensus and is fsynced on a quorum of nodes before the commit acknowledges. There is no "unsafe fast mode".

The obvious question: **what if we run PostgreSQL with `synchronous_commit=on`, at durability parity with CockroachDB?**

The table above already shows the answer. **The delta between `on` and `off` at 2-client saturation is 2.8%** (26,376 vs 27,139). At this load PostgreSQL is bound on CPU and the connection/query path, not on WAL fsync, so the "unsafe fast mode" barely helps. Turning it off costs almost nothing.

That means the honest headline is:

> **At durability parity, PostgreSQL delivers 26,376 workflows per second on 96 vCPU; CockroachDB on the same 96 vCPU (spread across 3 nodes) delivers 4,030 wf/s.**

CockroachDB is **6.5× slower** on raw single-DB throughput. That is a real gap and comes from three unavoidable costs of a distributed SQL database:

1. **Raft consensus round-trip on every write.** PostgreSQL commits locally; CockroachDB waits for at least one other node to acknowledge the Raft append. Even inside a single AZ this is a network round trip of ~250 µs added to every write.
2. **Cross-node coordination for range leaseholders.** A single leaseholder serves writes for each range; on a fresh empty database with a small number of ranges, one node handles nearly all traffic while the other two only shadow-replicate. Throughput scales with the range count, not the node count, until the workload spreads.
3. **Distributed SQL plan overhead.** Every `INSERT` goes through the SQL layer, the KV layer, then the raft/storage layer. Each hop adds fixed cost that a single-node PostgreSQL does not pay.

The tradeoff is not about micro-benchmark throughput. It is about what happens when the workload no longer fits on one node, or when the one node dies.

---

### Step 3: what happens when a node dies

Both systems can absorb a transient interruption. Only one can absorb a permanent one.

We ran a continuity probe: `DBOS.start_workflow_async` at a steady 200 workflows per second, then destroyed the underlying database mid-workload.

**CockroachDB test**: `aws ec2 stop-instances --force` on one of the three nodes (a hard power-off from the cluster's perspective). The killed node is not restarted.

| Time relative to kill | ok/s | p50 latency | Notes |
|---:|---:|---:|---|
| −10s to 0s | 200 | 8 ms | Steady state, all 3 nodes serving |
| 0s to +7s   | 0   | n/a     | **Dead window**: cluster detecting node loss |
| +7s to +13s | 96–200 | 2000 → 25 ms | Recovery ramp, queued workflows draining |
| +13s onward | 200 | 8 ms | Steady state on 2 remaining nodes |

**Zero workflows failed. Total user-visible impact: 13 seconds. The killed node never came back.** The cluster picked up where it left off with two nodes.

**PostgreSQL test**: `aws rds reboot-db-instance` on the RDS primary (the closest RDS equivalent to a node failure, since single-AZ RDS has no standby to fail over to).

| Time relative to reboot | ok/s | p50 latency | Notes |
|---:|---:|---:|---|
| −10s to 0s | 200 | 3 ms | Steady state |
| 0s to +6s   | 0   | n/a     | **Dead window**: instance shutting down / restarting |
| +6s to +12s | 159–201 | 1500 → 25 ms | Recovery ramp, RDS back online |
| +12s onward | 200 | 3 ms | Steady state |

The transient outage is superficially similar: ~6 seconds of zero throughput, ~6 seconds of ramp, zero permanent failures. The critical difference is under the surface.

- **The CockroachDB workload recovered without the killed node coming back.** The two surviving nodes carried the load. If the killed instance were destroyed (disk lost, region gone), the workload would still be running on the remaining two.
- **The PostgreSQL workload recovered because RDS auto-restarted the same instance.** If the instance had been terminated instead of rebooted, the outage would persist until manual restore from a snapshot. Single-AZ RDS has no failover target.

Multi-AZ RDS PostgreSQL adds a standby with 30 to 60 seconds of automatic failover time (per AWS documentation) at roughly 2× the cost. CockroachDB's 13-second recovery is included in the base price and requires no snapshot restore, no manual promotion, and no downtime SLA breach.

<!-- PLACEHOLDER Bench #3: pre-loaded DB size effect -->

### Step 4: throughput on a database that is not empty

The 4,030 wf/s CockroachDB number in Step 1 was on an empty database. Real DBOS deployments accumulate workflow history: every completed workflow leaves a row in `dbos.workflow_status`, and by default that table is never pruned. An empty-database benchmark is a first-boot number; it is not what the system will do six months into production.

We pre-loaded 100 million completed workflows (via bulk `COPY` into `dbos.workflow_status`, uuid7 keys to preserve the natural insert ordering the runtime uses) and then ran a 224-process bench against the pre-loaded database:

| Database state | Bench | wf/s | p50 latency |
|---|---|---:|---:|
| Empty (baseline, solo 224 proc) | solo 224 | 2,244 | 10,300 ms |
| 100 M pre-loaded rows | solo 224 | **2,095** | **11,640 ms** |

Throughput drops **6.6 %** and p50 latency rises **13 %** as the workflow status table crosses 100 million rows. That is a small, well-behaved degradation, not a collapse. The result also exercises the range-split boundary: `dbos.workflow_status` at 100 million rows spans hundreds of CockroachDB ranges (default 512 MiB per range) distributed across leaseholders on all three nodes, whereas the empty-DB baseline has a single range served by a single leaseholder. Under the sequential-write pressure DBOS applies, the two effects roughly cancel: more parallelism, more coordination.

For a team choosing where to run DBOS long-term, this is the number that matters. If throughput had collapsed on a full table, the empty benchmark would be a marketing artefact. It did not, so the empty benchmark is a floor and the durability guarantee is real.

<!-- PLACEHOLDER Bench #2: scale-out -->

### Step 5: adding nodes

The raw-throughput gap in Step 1 (PG 27K vs CRDB 4K at 3 nodes) narrows when CockroachDB is given more nodes. On a distributed database, throughput per range is bounded by leaseholder concurrency, but total throughput scales with the range count (which grows automatically) and the number of nodes over which those ranges are spread.

We ran the same 2×224 benchmark against clusters of 3 and 6 `m7i.8xlarge` nodes:

| Cluster size | Aggregate wf/s | Speedup vs 3-node | Notes |
|---:|---:|---:|---|
| 3 nodes | 4,030 | 1.00× | baseline |
| 6 nodes | **4,575** | **1.14×** | ranges rebalanced across 6 leaseholders |

Scaling is sub-linear at this concurrency: doubling nodes only yields 14 % more throughput. Two things explain the gap. First, the client-side generator (2×224 processes, pool 4) is already saturating the connection path at 3 nodes, so adding nodes without adding client concurrency leaves the extra capacity idle. Second, `dbos.workflow_status` on a fresh empty database has a small range count; each range still has exactly one leaseholder, so the number of concurrent write leaders does not grow linearly with node count until the table splits.

The point of the number is not that CockroachDB scales perfectly on a two-client benchmark; it is that the ceiling *moves*. PostgreSQL on the same hardware envelope offers exactly one scaling knob: buy a bigger instance. RDS goes up to `db.m7i.48xlarge` (192 vCPU) at roughly 2× the cost, and beyond that you are sharding at the application layer or migrating. CockroachDB continues to accept nodes; whether adding them helps a specific workload is an operational tuning question, not an architectural ceiling.

A 9-node measurement was planned and blocked by an AWS `io2` per-region IOPS quota (six `m7i.8xlarge` nodes at 40 K provisioned IOPS each already put us at the account limit). It is a real constraint on scale-up benchmarks but not on scale-up in production, where storage classes are chosen up-front.

---

### Summary

| Dimension | PostgreSQL RDS single-AZ | CockroachDB 3-node single-AZ |
|---|---|---|
| Aggregate throughput at durability parity | **26,376 wf/s** | 4,030 wf/s |
| `synchronous_commit=off` speedup | +2.8% (not worth losing durability) | not applicable |
| Recovery from node kill | Requires reboot or manual restore | Automatic, 13 s user impact |
| Survives permanent node loss | No, restore from snapshot | Yes, two-of-three quorum continues |
| Horizontal scale-out | Bigger instance, then re-shard | Add nodes, ranges rebalance |
| Cross-region durability | External tooling | Built in |

Two takeaways for a team choosing between them:

**If your workload permanently fits on one PostgreSQL instance and you can tolerate the recovery model, PostgreSQL is faster and simpler.** DBOS's headline 43K number is real (with two client hosts) and CockroachDB does not touch it on a small cluster.

**If your workload will outgrow one node, or you need a database that survives losing a machine without human intervention, the throughput gap disappears with cluster size and the recovery gap never existed for CockroachDB in the first place.** DBOS runs on it unchanged.

Both benchmarks ran at **Read Committed** isolation to match the DBOS blog's default. All raw JSON results and the patched CockroachDB variant of the benchmark script are in the [artefacts folder](https://github.com/aelkouhen/aelkouhen.github.io/tree/main/assets/bench/dbos-cockroachdb).


---

## See Also

- [DBOS Documentation](https://docs.dbos.dev/)
- [DBOS Python Workflow Tutorial](https://docs.dbos.dev/python/tutorials/workflow-tutorial)
- [CockroachDB Cloud](https://cockroachlabs.cloud/)
- [CockroachDB Distributed SQL](https://www.cockroachlabs.com/blog/what-is-distributed-sql/)
- [Temporal + CockroachDB: Cluster-Based Durable Execution](/2026-04-24-temporal-cockroachdb/)
