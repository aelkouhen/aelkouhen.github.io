---
date: 2026-04-23
layout: post
title: "Durable Workflow Orchestration with Temporal and CockroachDB"
subtitle: "How to run Temporal with CockroachDB as a distributed, strongly-consistent persistence backend — including the critical visibility schema fix"
tags: [integrations, CockroachDB, temporal, workflow, orchestration, durable-execution]
lang: en
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

Modern AI applications are no longer single-shot inference calls — they are long-running agents that plan, act, observe, and retry across time. Coordinating these agents reliably requires a **workflow orchestration layer** that survives crashes, scales horizontally, and guarantees exactly-once execution semantics. [Temporal](https://temporal.io/) is one of the leading open-source platforms for this — and [CockroachDB](https://www.cockroachlabs.com/) is its ideal distributed persistence backend.

A **workflow orchestration framework** manages the lifecycle of long-running, multi-step programs. Instead of writing retry loops, checkpointing logic, and failure recovery by hand, you declare your business logic as a sequence of **durable steps** and let the framework handle the rest. The core promises are:

- **Durability** — workflow state survives process crashes, restarts, and infrastructure failures
- **Exactly-once semantics** — individual steps are never re-executed after they complete successfully
- **Idempotency** — re-invoking the same workflow with the same ID is a no-op
- **Observability** — the full execution history is inspectable at any point

---

## What Is Temporal?

[Temporal](https://temporal.io/) is an open-source, language-agnostic platform for building reliable distributed applications. It introduces the concept of **Durable Execution** — the guarantee that workflow logic runs to completion regardless of infrastructure failures.

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

---

## How Temporal Works

Understanding why CockroachDB is the right persistence backend for Temporal requires understanding how Temporal stores state. The design choices that make Temporal reliable are the same ones that demand a distributed, strongly-consistent database underneath.

### Workflow as a State Machine

Every running workflow is modelled as a state machine. Each external interaction — an activity completing, a timer firing, a signal arriving — produces a new **event** appended to the workflow's **event history** log. The current state of a workflow is fully determined by replaying that log from the beginning.

<img src="/assets/img/temporal-state-machine.png" alt="Temporal workflow state machine" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**A workflow execution is a deterministic state machine driven by an append-only event history**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

When a Worker restarts after a crash, it re-fetches the event history and replays the workflow function. Steps that already completed are skipped instantly — execution continues from the last committed state.

### Consistency is Non-Negotiable

Every state transition must atomically update the workflow state **and** enqueue the next task. If either write fails, the system enters an unrecoverable inconsistent state: a phantom task that will never be delivered.

<img src="/assets/img/temporal-transactions.png" alt="Temporal transactional updates" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**State transitions require atomically updating workflow state and task queue entries in a single transaction**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

This is why Temporal demands a strongly-consistent relational store with full ACID guarantees — and why CockroachDB, which provides serializable isolation at any scale, is a natural fit where a single PostgreSQL primary would become a bottleneck.

### Visibility — Queryable Workflow Index

In addition to the main persistence store, Temporal maintains a **Visibility store** — a secondary database optimised for querying workflow executions by status, type, start time, and custom search attributes stored as JSONB.

<img src="/assets/img/temporal-visibility.png" alt="Temporal workflow visibility" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**The Visibility store indexes workflow executions for list and filter queries using JSONB search attributes**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

The standard PostgreSQL visibility schema indexes JSONB via `CREATE EXTENSION IF NOT EXISTS btree_gin` — a PostgreSQL-only extension that **does not exist in CockroachDB**. The fix is CockroachDB's native `CREATE INVERTED INDEX`, which provides the same capability without any extension (see the schema section below).

### Full Cluster Architecture with CockroachDB

A Temporal cluster consists of four independently scalable stateless services fronting two durable storage tiers. When CockroachDB backs both stores, the entire persistence tier gains distributed replication, automatic failover, and horizontal scalability — all transparent to Temporal's services.

<img src="/assets/img/temporal-architecture-overview.png" alt="Temporal cluster architecture with CockroachDB" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**Temporal cluster with CockroachDB as the persistence and visibility backend — stateless services scale independently, storage scales automatically**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

| Service | Role |
|---|---|
| **Frontend** | gRPC gateway — routes client requests to the correct History shard |
| **History** | Owns workflow state machines; processes commands and records events |
| **Matching** | Manages task queues; dispatches tasks to available Workers |
| **Worker** | Runs internal system workflows (replication, archival, cleanup) |
| **Persistence Store (CockroachDB)** | Event histories, timers, transfer queues — strong consistency, distributed writes |
| **Visibility Store (CockroachDB)** | Queryable execution index — JSONB inverted index replaces `btree_gin` |

---

## Why CockroachDB for Temporal?

Temporal officially supports PostgreSQL, MySQL, SQLite, and Cassandra. CockroachDB is a natural fit for the persistence store because it brings:

- **Distributed, strongly-consistent SQL** — the same ACID guarantees PostgreSQL provides, at any scale
- **Active-active multi-region** — Temporal history shards can be distributed across regions without manual replication
- **Automatic failover** — node failures are transparent to Temporal's services
- **Horizontal scalability** — scale reads and writes without sharding logic in the application
- **PostgreSQL wire protocol** — Temporal's existing `postgres12` plugin works directly

---

## Deploying Temporal on CockroachDB

### Step 1 — Provision CockroachDB databases and user

```sql
CREATE DATABASE temporal;
CREATE DATABASE temporal_visibility;
CREATE USER temporal WITH PASSWORD 'temporal';
GRANT ALL ON DATABASE temporal TO temporal;
GRANT ALL ON DATABASE temporal_visibility TO temporal;
```

### Step 2 — Initialize the persistence schema

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

### Step 3 — Fix the visibility schema for CockroachDB

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

### Step 4 — Configure Temporal server

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

### Step 5 — Write your first durable agent workflow

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

## Key Benefits

| Capability | CockroachDB Contribution |
|---|---|
| **Serializable isolation** | No lost updates or phantom reads under concurrent workflow execution |
| **Multi-region replication** | History shards durable across data-center failures without manual failover |
| **Horizontal scalability** | Add nodes to absorb more concurrent workflows without re-sharding |
| **Automatic failover** | Node failures transparent to all four Temporal services |
| **PostgreSQL compatibility** | Zero application code changes — `postgres12` plugin works directly |

CockroachDB acts as a drop-in replacement for PostgreSQL, giving Temporal's stateless services an indestructible, globally distributed foundation — with one schema fix for the visibility store.

---

## See Also

- [Temporal Documentation](https://docs.temporal.io/)
- [Designing a Workflow Engine from First Principles](https://temporal.io/blog/workflow-engine-principles)
- [CockroachDB Cloud](https://cockroachlabs.cloud/)
- [CockroachDB Distributed SQL](https://www.cockroachlabs.com/blog/what-is-distributed-sql/)
- [DBOS + CockroachDB — Embedded Durable Execution](/2026-04-24-dbos-cockroachdb/)
