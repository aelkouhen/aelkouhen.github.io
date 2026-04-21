---
layout: post
title: "CockroachDB for AI Agents: MCP Servers and Database Lifecycle Automation"
subtitle: "How CockroachDB becomes agent-ready with MCP servers, CLI tools, and agent skills"
cover-img: /assets/img/cover-ai-mcp.webp
thumbnail-img: /assets/img/cover-ai-mcp.webp
share-img: /assets/img/cover-ai-mcp.webp
tags: [Artificial Intelligence, CockroachDB, GenAI, MCP, AI Agents]
comments: true
---

The way AI systems interact with databases is undergoing a fundamental shift. For decades, databases served as passive backends — waiting for application code to issue queries. Today, AI agents actively interrogate, modify, and operate databases with minimal human intervention. This requires a new kind of infrastructure: one that is structured, secure, auditable, and model-agnostic.

[CockroachDB](https://www.cockroachlabs.com/product/overview/) has embraced this shift head-on. In March 2026, Cockroach Labs announced a suite of agent-ready capabilities: a fully managed [MCP Server](https://cockroachlabs.cloud/mcp), a redesigned `ccloud` CLI, and a public library of CockroachDB Agent Skills. Alongside this, the open-source [CockroachDB MCP Server](https://github.com/amineelkouhen/mcp-cockroachdb) — a community project — provides a comprehensive natural language interface for AI agents to manage, monitor, and query CockroachDB directly.

This article covers all three dimensions of CockroachDB's agent-ready story: the open-source MCP server, the managed enterprise MCP endpoint, and the agent skills system for database lifecycle automation.

---

## What is the Model Context Protocol?

The [Model Context Protocol (MCP)](https://www.anthropic.com/news/model-context-protocol) is an open standard introduced by Anthropic that enables AI applications to communicate uniformly with external tools and data sources — from file systems to APIs to databases. Think of it as the "USB-C for AI": a single, interoperable plug that lets any LLM-powered agent connect to any tool without bespoke integration code.

Before MCP, getting an LLM agent to query a database meant manually feeding it schema information, writing custom integration code, and managing security concerns for every new model or agent framework. MCP eliminates this overhead by providing a standardized discovery and invocation layer.

---

## The CockroachDB MCP Server (Community Project)

The [CockroachDB MCP Server](https://github.com/amineelkouhen/mcp-cockroachdb) is an open-source Python project that bridges AI language models with CockroachDB through the Model Context Protocol. It integrates with MCP-compatible clients such as Claude Desktop, Cursor, VS Code with GitHub Copilot, and the OpenAI Agents SDK.

CockroachDB is not a typical monolithic database. It is a distributed SQL database where data is automatically sharded into "ranges" and replicated across multiple nodes. The MCP server exposes this complexity through 29 distinct tools organized into four categories, enabling AI agents to interact with the full breadth of CockroachDB's capabilities — from cluster health to transactional data operations — using natural language.

### Tool Categories

**Cluster Monitoring**

| Tool | Description |
|---|---|
| `get_cluster_status` | Cluster health and node distribution |
| `show_running_queries` | Currently active queries |
| `analyze_performance` | Query performance statistics |
| `get_replication_status` | Replication and distribution status |

**Database Operations**

| Tool | Description |
|---|---|
| `connect` / `connect_database` | Establish connections |
| `list_databases` | Show all databases |
| `create_database` / `drop_database` | Database lifecycle |
| `switch_database` | Change active database |
| `get_active_connections` | Active user sessions |
| `get_database_settings` | Current configuration |

**Table & Schema Management**

| Tool | Description |
|---|---|
| `list_tables` / `list_views` | Schema discovery |
| `create_table` / `drop_table` | Table management |
| `create_index` / `drop_index` | Index management |
| `describe_table` | Schema information |
| `analyze_schema` | Full database overview |
| `get_table_relationships` | Foreign key analysis |
| `bulk_import` | Cloud storage data loading (S3, GCS, Azure) |

**Query & Transaction Execution**

| Tool | Description |
|---|---|
| `execute_query` | SQL query execution (JSON, CSV, table output) |
| `execute_transaction` | Atomic multi-statement operations |
| `explain_query` | Query execution plan analysis |
| `get_query_history` | Query audit trail |

### Installation

**Quick start with `uvx`** (no local clone required):

```bash
uvx --from git+https://github.com/amineelkouhen/mcp-cockroachdb.git@0.1.0 cockroachdb-mcp-server \
  --url postgresql://localhost:26257/defaultdb
```

**Individual parameters:**

```bash
uvx --from git+https://github.com/amineelkouhen/mcp-cockroachdb.git cockroachdb-mcp-server \
  --host localhost --port 26257 --database defaultdb --user root --password mypassword
```

**SSL connection:**

```bash
uvx --from git+https://github.com/amineelkouhen/mcp-cockroachdb.git cockroachdb-mcp-server \
  --url postgresql://user:pass@cockroach.example.com:26257/defaultdb?sslmode=verify-full&sslrootcert=path/to/ca.crt&sslcert=path/to/client.username.crt&sslkey=path/to/client.username.key
```

**From source (development):**

```bash
git clone https://github.com/amineelkouhen/mcp-cockroachdb.git
cd mcp-cockroachdb
uv venv
source .venv/bin/activate
uv sync
uv run cockroachdb-mcp-server --help
```

**Docker Compose (local development):**

```bash
docker compose up -d
# MCP server: http://localhost:8000/mcp/
# CockroachDB UI: http://localhost:8080
docker compose logs -f mcp-server
```

### Configuration

The server accepts CLI arguments, environment variables, and default values in that precedence order.

| Variable | Description | Default |
|---|---|---|
| `CRDB_HOST` | Hostname/address | `127.0.0.1` |
| `CRDB_PORT` | SQL interface port | `26257` |
| `CRDB_DATABASE` | Database name | `defaultdb` |
| `CRDB_USERNAME` | SQL user | `root` |
| `CRDB_PWD` | User password | — |
| `CRDB_SSL_MODE` | SSL mode | `disable` |
| `CRDB_SSL_CA_PATH` | CA certificate path | — |
| `CRDB_SSL_CERTFILE` | Client certificate path | — |
| `CRDB_SSL_KEYFILE` | Client key path | — |

### Client Integrations

**Claude Desktop** (`claude_desktop_config.json`):

```json
{
    "mcpServers": {
        "cockroach-mcp-server": {
            "type": "stdio",
            "command": "/opt/homebrew/bin/uvx",
            "args": [
                "--from", "git+https://github.com/amineelkouhen/mcp-cockroachdb.git",
                "cockroachdb-mcp-server",
                "--url", "postgresql://localhost:26257/defaultdb"
            ]
        }
    }
}
```

**VS Code with GitHub Copilot** (`settings.json`):

```json
{
  "chat.agent.enabled": true,
  "mcp": {
    "servers": {
      "CockroachDB MCP Server": {
        "type": "stdio",
        "command": "uvx",
        "args": [
          "--from", "git+https://github.com/amineelkouhen/mcp-cockroachdb.git",
          "cockroachdb-mcp-server",
          "--url", "postgresql://root@localhost:26257/defaultdb"
        ]
      }
    }
  }
}
```

**Cursor** (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "cockroach-mcp-server": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/amineelkouhen/mcp-cockroachdb",
        "--url",
        "postgresql://root@localhost:26257/defaultdb?sslmode=disable"
      ]
    }
  }
}
```

**Docker** (Claude Desktop):

```json
{
  "mcpServers": {
    "cockroach": {
      "command": "docker",
      "args": ["run", "--rm", "--name", "cockroachdb-mcp-server",
        "-e", "CRDB_HOST=<host>",
        "-e", "CRDB_PORT=<port>",
        "-e", "CRDB_DATABASE=<database>",
        "-e", "CRDB_USERNAME=<user>",
        "mcp-cockroachdb"]
    }
  }
}
```

To troubleshoot Claude Desktop on macOS: `tail -f ~/Library/Logs/Claude/mcp-server-cockroach.log`

### Real-World Use Cases

**Use Case 1 — AI-Powered Database Administrator**

An example prompt for diagnosing intermittent slowdowns:

> *"Hey, can you check the health of my CockroachDB cluster? Show me any long-running queries. Also, please analyze the query plan for `SELECT * FROM users WHERE last_active < NOW() - INTERVAL '30 days'` and tell me if it's using an index."*

Behind the scenes the agent orchestrates: `get_cluster_status` → `show_running_queries` → `explain_query`, then synthesizes the results with optimization suggestions.

**Use Case 2 — Rapid Prototyping Assistant**

> *"I'm building a new feature. Please create a new table called `feature_flags` with columns for `id` (UUID, primary key), `name` (STRING, unique), `is_enabled` (BOOL, default true), and `created_at` (TIMESTAMP). Once that's done, bulk import the initial flags from the CSV file at `s3://my-company-data/dev/feature_flags.csv`."*

The agent combines `create_table` DDL execution with `bulk_import` in sequence, then confirms the record count.

---

## CockroachDB is Built for AI Agents

Beyond the community MCP server, Cockroach Labs has announced a set of native, enterprise-grade agent capabilities. AI systems behave differently from traditional services — they fan out work, retry aggressively, and generate bursts of concurrent writes across regions. CockroachDB handles this expanded load through automatic data distribution, horizontal scaling, and serializable isolation by default.

### How AI Agents Use Databases

There are two major interaction patterns:

1. **Application backend** — AI systems require databases supporting always-on availability and multi-region deployments. CockroachDB handles this through distributed data and horizontal scale without manual partitioning.

2. **Interaction surface** — Agents assist with the full database lifecycle: provisioning clusters, reviewing schemas, and triaging alerts.

### What "Agent-Ready" Means

An agent-ready database requires:

- **Structured interfaces** — reliable, machine-interpretable outputs
- **Scoped permissions** — governing what agents can and cannot do
- **Auditability** — complete action logging for every agent operation
- **Model-agnostic interfaces** — compatibility across frameworks and LLM providers

---

## CockroachDB's Managed MCP Server

The [Managed MCP Server](https://www.cockroachlabs.com/docs/cockroachcloud/connect-to-the-cockroachdb-cloud-mcp-server) is a Cloud-hosted MCP endpoint designed for enterprise environments with shared agent systems. Unlike the community server, it requires no local deployment: developers copy a configuration snippet from the Cloud Console and paste it into their MCP client within minutes.

**Endpoint:** `https://cockroachlabs.cloud/mcp`

<img src="/assets/img/ai-mcp-01.png" alt="How the CockroachDB Managed MCP Server Works" style="width:100%">
{: .mx-auto.d-block :}
**How the CockroachDB Managed MCP Server Works**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

### Request Flow

Each MCP request follows this path:

1. MCP client (e.g., Claude Code) sends a JSON-RPC request over HTTPS
2. Request passes through a load balancer
3. The internal `mcp-service` routes `/mcp` traffic to the MCP handler
4. The middleware pipeline enforces auth, rate limits, and logging
5. A tool handler performs authorization and executes the requested operation
6. Results are returned as an MCP-compliant JSON-RPC response

The implementation uses the official `modelcontextprotocol/go-sdk`. HTTP transport is supported and recommended; SSE transport is intentionally excluded (deprecated in MCP).

<img src="/assets/img/ai-mcp-02.png" alt="Managed MCP Server Architecture" style="width:100%">
{: .mx-auto.d-block :}
**Managed MCP Server Architecture**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

### Security: Authentication and Authorization

Two authentication mechanisms are supported:

1. **OAuth 2.1 (Authorization Code Flow with PKCE)** — For interactive user workflows with scoped permissions:
   - `mcp:read` for safe, read-only access
   - `mcp:write` for controlled mutations

2. **Service account API keys** — For fully autonomous environments with Cloud RBAC roles scoped to specific clusters

Every tool invocation performs a Cloud RBAC check before execution. Requests are rejected if permissions exceed the expected scope.

### Read and Write Consent

**Read-only consent** permits only safe, introspective tools such as `list_databases`, `select_query`, and `get_table_schema`. Write operations are explicitly blocked and system tables are deny-listed to prevent sensitive access.

**Write consent** enables additional tools such as `create_database`, `create_table`, and `insert_rows`. Destructive SQL operations (`DROP`, `TRUNCATE`) remain unsupported.

<img src="/assets/img/ai-mcp-03.png" alt="Authorizing MCP Access: Read and Write Consent" style="width:100%">
{: .mx-auto.d-block :}
**Authorizing MCP Access: Read and Write Consent**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

### Observability

All requests emit structured logs tagged with `mcp`, including:
- Tool name
- Cluster and organization context
- Redacted SQL shape
- Latency and response size
- MCP-specific error codes

End-to-end traces flow into the observability pipeline, with spans covering middleware steps, API calls, and database queries. Tool usage events are sent to the analytics pipeline, enabling analysis of adoption patterns and real-world workflows.

### Getting Started

1. Log into the [CockroachDB Cloud Console](https://cockroachlabs.cloud)
2. Navigate to your cluster, click the **Connect** modal, and select the MCP integration option
3. Copy the generated configuration snippet
4. Paste the snippet into your MCP client's configuration file (Claude Code, Cursor, or VS Code)
5. Start asking your AI assistant questions about your database

---

## AI Agent Skills for Database Lifecycle Automation

[CockroachDB Agent Skills](https://www.cockroachlabs.com/blog/cockroachdb-ai-agents-database-lifecycle-automation/) are structured capabilities that define how an AI system interacts with CockroachDB. They follow open standard interfaces, making them portable across different models and tools without rewriting integrations. Teams can use agent skills across onboarding, development, operations, and scaling decisions — throughout the full database lifecycle.

<img src="/assets/img/ai-mcp-04.png" alt="CockroachDB Agent Skills — Database Lifecycle Overview" style="width:100%">
{: .mx-auto.d-block :}
**CockroachDB Agent Skills — Database Lifecycle Overview**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

### Six Skill Domains

**1. Onboarding and Migrations**

Skills that guide data movement using [MOLT](https://www.cockroachlabs.com/docs/stable/migration-overview) — CockroachDB's migration toolchain — covering schema translation, data verification, and cutover strategies.

<img src="/assets/img/ai-mcp-05.png" alt="CockroachDB Agent Skills — Onboarding and Migrations" style="width:100%">
{: .mx-auto.d-block :}
**CockroachDB Agent Skills — Onboarding and Migrations**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

**2. Query and Schema Design**

Skills that translate natural language requirements into SQL, enforce distributed SQL best practices (e.g., avoiding full table scans, choosing hash-sharded indexes), and review schema proposals.

**3. Operations and Lifecycle**

Skills covering cluster management and maintenance tasks: version upgrades, node replacement, backup scheduling, and recovery procedures.

<img src="/assets/img/ai-mcp-06.png" alt="CockroachDB Agent Skills — Operations and Lifecycle" style="width:100%">
{: .mx-auto.d-block :}
**CockroachDB Agent Skills — Operations and Lifecycle**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

**4. Performance and Scaling**

Skills that identify query bottlenecks, analyze range distribution, recommend index changes, and guide horizontal scale-out decisions.

**5. Security and Governance**

Skills that harden deployments across authentication, encryption, RBAC, and audit logging — aligned with enterprise compliance requirements.

<img src="/assets/img/ai-mcp-07.png" alt="CockroachDB Agent Skills — Performance, Security, and Governance" style="width:100%">
{: .mx-auto.d-block :}
**CockroachDB Agent Skills — Performance, Security, and Governance**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

**6. Observability and Diagnostics**

Skills that profile SQL statements, monitor background jobs, and surface contention events and range distribution anomalies.

<img src="/assets/img/ai-mcp-08.png" alt="CockroachDB Agent Skills — Observability and Diagnostics" style="width:100%">
{: .mx-auto.d-block :}
**CockroachDB Agent Skills — Observability and Diagnostics**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

### Real-World Scenario: CPU Spike Response

Consider a practical example where an agent receives a "High CPU utilization" alert on a staging cluster:

1. The agent connects to CockroachDB via the managed MCP server
2. It monitors background jobs and profiles SQL statements
3. It identifies root causes: expensive queries on the `user_events` table, backup job scheduling overlap, and suboptimal UUID primary key patterns
4. It proposes fixes: hash-sharded UUID primary keys, supporting indexes, and a rescheduled backup window

Critically, the agent **does not apply these changes automatically**. It generates migration scripts for human review. This creates workflows that are conversational, structured, auditable, and still human-approved.

---

## Three Interfaces, One Agent-Ready Database

The three components serve different scenarios and audiences:

| Interface | Best For |
|---|---|
| **Open-source MCP Server** | Developers, local clusters, full administrative control |
| **Managed MCP Server** | Enterprise teams, shared agent systems, production safety |
| **Agent Skills** | Cross-framework portability, structured reasoning, lifecycle automation |
| **`ccloud` CLI** | Developer agents operating through shell commands, CI/CD pipelines |

Together, they reflect a deliberate architectural philosophy: CockroachDB exposes internal state — statement statistics, execution plans, contention events, range distribution, replication status — through structured interfaces that agents can reliably interpret and act upon.

As Spencer Kimball, CEO of Cockroach Labs, put it: *"All of the activity that databases have had to deal with up till now has been humans. Now it's going to be agents… You could have a trillion."*

The age of the AI agent is here, and CockroachDB is built for it.

---

## Resources

- [CockroachDB MCP Server (open-source)](https://github.com/amineelkouhen/mcp-cockroachdb)
- [CockroachDB Managed MCP Server quickstart](https://www.cockroachlabs.com/docs/cockroachcloud/connect-to-the-cockroachdb-cloud-mcp-server)
- [CockroachDB is Built for AI Agents](https://www.cockroachlabs.com/blog/cockroachdb-ai-agents-agent-ready-database/)
- [CockroachDB's Managed MCP Server: Production-Ready AI Agent Access](https://www.cockroachlabs.com/blog/cockroachdb-ai-agents-managed-mcp-server/)
- [AI Agent Skills for CockroachDB: Database Lifecycle Automation](https://www.cockroachlabs.com/blog/cockroachdb-ai-agents-database-lifecycle-automation/)
- [Introducing the Model Context Protocol — Anthropic](https://www.anthropic.com/news/model-context-protocol)
- [Getting Started with GenAI Using CockroachDB](/2025-10-05-cockroachdb-ai-intro/)
- [Real-Time Indexing for Billions of Vectors with C-SPANN](/2025-11-23-cockroachdb-ai-spann/)
