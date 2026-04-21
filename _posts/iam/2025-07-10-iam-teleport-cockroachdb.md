---
layout: post
title: "When Teleport & CockroachDB Powered Global Tier 0 Access Management"
subtitle: "How a global payments leader achieved 99.999% availability for infrastructure access"
cover-img: /assets/img/cover-iam-p3.webp
thumbnail-img: /assets/img/cover-iam-p3.webp
share-img: /assets/img/cover-iam-p3.webp
tags: [iam, security, CockroachDB, Teleport, access management, multi-region, distributed SQL]
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

In large-scale, security-sensitive enterprises — particularly in finance — access infrastructure isn't just another service: it's a critical foundation. Access must be secure, observable, and compliant. Most importantly, it must always be available. When a global payments provider set out to standardize [Teleport](https://goteleport.com/) as its internal access platform, it had to meet the strict requirements of a Tier 0 classification, which mandates 99.999% availability across a globally distributed footprint.

This article explores how this global leader in digital payments overcame limitations in their access infrastructure by using CockroachDB as the storage backend for Teleport. As a result, they were able to achieve the stringent reliability and global presence demands of a Tier 0 system.

We'll not only walk through the architectural solution, but also provide a hands-on tutorial for setting up a highly available access management system with Teleport and CockroachDB.

---

## The Challenge: Multi-Region, Tier 0 Requirements

As a major payment technology company, this organization operates at an immense global scale. With operations spanning every continent and a network that handles over hundreds of billions of transactions annually, their infrastructure must meet exceptionally high standards for availability, scalability, and compliance.

Designed for resilience across multiple regions, and with data centers spanning three continents, this global footprint allows this global payments company to serve diverse internal users and IT teams working worldwide with minimal latency, while also meeting regional data residency and regulatory requirements.

<img src="/assets/img/iam-p3-global-payments.jpg" alt="Global Payments System" style="width:100%">

{: .mx-auto.d-block :}
**Global Payments System**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

But operating across such a distributed environment comes with complexity — especially when it comes to infrastructure access. With teams located in different time zones and regions, they all need secure, compliant, and instantaneous access to systems for tasks like debugging, deployment, and monitoring. Access must be both highly secure and highly available, without introducing bottlenecks or relying on fragile VPNs or static credentials.

For this leading company, any tool used in its infrastructure must be evaluated against the company's internal classification for Tier 0 applications. Tier 0 applications are the most critical systems in an organization's IT infrastructure — foundational services upon which all other systems depend. Their failure would cause a widespread outage, disrupt core business operations, or compromise security and compliance. As such, Tier 0 applications must meet the highest standards of availability, reliability, and security. In this context, access management infrastructure — how engineers and services connect to compute, storage, and network resources — doesn't become a simple utility. It's a foundation.

### Key Characteristics of Tier 0 Systems

- **Mission-critical**: Their availability is essential for business continuity. If a Tier 0 service goes down, it may bring down multiple dependent systems.
- **High availability (HA)**: Typically expected to meet or exceed 99.999% uptime (five nines), which equates to only ~5 minutes of downtime per year.
- **Strict security controls**: These applications handle sensitive data or govern access to critical resources, requiring advanced authentication, encryption, and audit capabilities.
- **Global resilience**: Often deployed across multiple data centers or cloud regions to withstand regional outages and latency variation.
- **Compliance-sensitive**: Frequently fall under the scope of regulatory standards such as PCI-DSS, ISO 27001, SOC 2, or FedRAMP.

This global payments company's internal infrastructure spans multiple continents, serves thousands of engineers, and must meet the highest standards of compliance and availability. [Teleport](https://goteleport.com/) offered a clear and compelling advantage by streamlining and securing access across a diverse and globally distributed infrastructure.

Initially, the purpose of Teleport was to unify and secure access to its servers and applications across four core data centers located in three different continents. The goal was to establish a single access control layer across all regions, offering centralized policies, auditing, and identity-based access. However, the early implementation relied on another storage backend which is not designed to offer multi-region, high-availability deployments.

The company quickly ran into significant obstacles:

- **Scalability limitations**: The previous deployment hits a scalability ceiling not sufficient to meet the company needs. The previous storage technology is designed for small metadata and lacks sharding and scalability for large datasets typical of general-purpose databases.
- **Unsupported multi-region mode**: The previous storage technology's lack of formal support in multi-region setups required extensive operational overhead and careful orchestration.
- **Availability issues**: Network drops and jitter created synchronization and reliability issues. The previous storage technology prioritizes consistency over availability; during network partitions or quorum loss, the cluster becomes unavailable to prevent split-brain.
- **Latency bottlenecks**: Write and linearizable read requests must go through the cluster's leader, causing latency and bottlenecks in large clusters.

---

## The Solution: Teleport and CockroachDB for a Global Tier 0 Access Platform

### Why Teleport?

In modern infrastructure, access is the first line of defense. Whether you're connecting to a Linux server, a Kubernetes cluster, a cloud database, or an internal application, how users access those systems determines your overall security posture.

**Teleport** is an access plane that consolidates and secures access to all types of infrastructure environments. It's designed to replace a patchwork of SSH bastions, VPNs, identity providers, and access proxies while providing a single, unified platform.

<img src="/assets/img/iam-p3-teleport-identity.jpg" alt="Teleport Identity Platform" style="width:100%">

{: .mx-auto.d-block :}
**Teleport Identity Platform**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Teleport provided a unified access control layer capable of managing permissions across heterogeneous systems. Its agentless architecture — leveraging standard protocols like SSH and HTTPS — simplified deployment and eliminated the need for additional software on target systems. Teleport also delivered real-time audit visibility, enabling security teams and compliance officers to monitor access events and session activity with precision. With certificate-based authentication and automatic certificate rotation, it removed the risks associated with long-lived credentials. Finally, deep SSO integration with the company's internal identity provider ensured seamless, centralized authentication, reinforcing both security and operational efficiency.

Teleport offers:

- Identity-based access using SSO (SAML, OIDC, GitHub, etc.)
- Short-lived certificates for all access (no static keys or passwords)
- Comprehensive auditing of all activity, including session recordings
- RBAC and ABAC policies for fine-grained access control
- Multi-protocol support, including SSH, Kubernetes, databases (PostgreSQL, MySQL, MongoDB, CockroachDB), internal web apps, and Windows RDP

Teleport's architecture is purpose-built for securing access to infrastructure in dynamic, distributed environments. At its core, Teleport operates as a modular, distributed system, enabling it to adapt to diverse infrastructure topologies while maintaining strong security and observability guarantees.

Teleport's architecture is built from the ground up with Zero Trust Security in mind — a model that assumes no implicit trust, even within the network perimeter. This approach is especially vital in distributed, cloud-native environments where traditional network-based security boundaries no longer apply.

At the heart of Teleport's Zero Trust implementation is the principle of identity over network. Instead of relying on IP addresses, VPNs, or trusted subnets, every request to infrastructure — whether it's a Linux server, a database, or a Kubernetes cluster — is authenticated and authorized based solely on the user's identity and role. This ensures that access is tightly scoped, contextual, and fully traceable.

Let's take a closer look at the key components of Teleport's architecture.

<img src="/assets/img/iam-p3-teleport-architecture.jpg" alt="Teleport Architecture" style="width:100%">

{: .mx-auto.d-block :}
**Teleport Architecture**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

1. **`auth` server** – the Auth Server is the central authority in every Teleport deployment. It acts as the brain of the cluster, storing critical state and enforcing authentication, authorization, and audit policies. Key responsibilities of the Auth Server include:
   - Managing user and role definitions
   - Issuing short-lived certificates for user and service authentication
   - Storing session events, access requests, and audit logs
   - Acting as the API for resource registration and access decisions

   Because it is stateful and policy-driven, the Auth Server relies on durable, consistent storage backends. In multi-region deployments, these storage backends have to be distributed, highly available while preserving strong consistency. This is where CockroachDB becomes a key enabler — ensuring that the Auth Server's state is globally consistent, and replicated across geographies.

2. **`proxy`** – the gateway between external clients and internal resources. It routes requests, terminates TLS connections, and serves the Teleport Web UI. Clients authenticate and connect to the Proxy, which then:
   - Performs reverse tunneling to internal nodes
   - Proxies traffic for SSH, Kubernetes, databases, apps, and Windows RDP
   - Enforces MFA and SSO integration
   - Logs sessions for auditing and replay

   This design ensures agentless, browser-based, and CLI-based access from anywhere in the world, without requiring inbound access or VPNs.

3. **Teleport Agents**: Teleport is built around the concept of resource agents, each designed to connect a specific type of infrastructure to the cluster:
   - `node` agent connects Linux servers via SSH
   - `kube` agent integrates Kubernetes clusters using the Kubernetes API
   - `db` agent provides access to SQL/NoSQL databases like PostgreSQL, MySQL, and CockroachDB itself
   - `app` agent exposes internal HTTP applications behind secure SSO and session auditing
   - `windows` agent (available in enterprise) allows access to Windows servers over RDP

   These agents "dial home" to the Auth Server and Proxy, forming reverse tunnels and avoiding the need for public IPs or firewall changes.

4. **Teleport Shell (`tsh`)** – Teleport's command-line client, is how users authenticate and interact with the system. It offers a streamlined UX for:
   - Logging in with SSO
   - Accessing servers and clusters
   - Opening database and Kubernetes sessions
   - Requesting elevated privileges or role access
   - Viewing session history and logs

   Behind the scenes, `tsh` obtains a short-lived certificate for the user identity and resource scope — making it inherently safer than managing SSH keys or static credentials.

Together, these capabilities make Teleport a natural fit for DevSecOps teams operating in multi-region, compliance-sensitive environments. Whether you're building toward standards like PCI-DSS, FedRAMP, or ISO 27001, Teleport provides a secure, flexible, and audit-friendly access foundation.

### Teleport + CockroachDB Joint Architecture

To meet Tier 0 requirements, this global payments provider made a strategic pivot to CockroachDB — a geo-distributed SQL database built for multi-region resilience and consistency. This change simplified operations, enabled active-active deployments of Teleport, and ensured that access infrastructure could survive network partitions, node failures, and global load — without compromising on security or compliance.

<img src="/assets/img/iam-p3-joint-architecture.jpg" alt="Multi-region Teleport + CockroachDB Joint Architecture" style="width:100%">

{: .mx-auto.d-block :}
**Multi-region Teleport + CockroachDB Joint Architecture**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Each of Teleport's components relied on CockroachDB to store their state in a consistent and durable way, enabling them to function correctly even in the presence of partial outages or regional network partitions.

For instance, the Teleport Auth service is well-suited to operate with CockroachDB because of its stateless design and API-first philosophy. Each service can be deployed as a stateless service, with its only persistence requirement being [the backing SQL database](https://www.cockroachlabs.com/blog/what-is-distributed-sql/). This makes it straightforward to horizontally scale services, perform rolling updates, or deploy new regions without having to orchestrate complex data migrations. CockroachDB, in turn, provides the always-consistent database layer that ensures user identities, access control rules, and session tokens are always accurate — no matter which region is serving a request.

To achieve true global availability, it was critical to pair Teleport capabilities with a distributed SQL database that could keep up with the demands of cross-region replication, strong consistency guarantees, and fault tolerance. That's where CockroachDB came in.

<img src="/assets/img/iam-p3-cockroachdb-attributes.jpg" alt="CockroachDB attributes for Teleport" style="width:100%">

{: .mx-auto.d-block :}
**CockroachDB attributes for Teleport**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

[CockroachDB](https://www.cockroachlabs.com/product/overview/) is a distributed SQL database designed for global scale and high availability. Since it became the first commercially available distributed SQL database, CockroachDB has become known for its enterprise-ready resilience. It replicates data across multiple regions while offering serializable isolation, strong consistency, and automated failover. By deploying Teleport components on top of CockroachDB, the global payments company was able to ensure that infrastructure access control data remained consistent and always available — even [during infrastructure disruptions](https://www.cockroachlabs.com/blog/database-testing-performance-under-adversity/). For instance, a DevSecOps team logging in from the UK, while a data center in the U.S. experiences downtime, would still be able to use infrastructure assets without issue. This level of resilience was critical for maintaining seamless user experiences across geographies.

Teleport officially supports [CockroachDB as a storage backend](https://goteleport.com/docs/reference/backends/#cockroachdb) — and for good reason:

- **Built-in multi-region support**: CockroachDB is designed for geographically distributed deployments.
- **High availability**: Even during network partitions, CockroachDB maintains consistency and uptime guarantees.
- **Horizontal scalability**: Easily scale reads and writes without sharding or manual intervention.
- **Data consistency**: Strong consistency by default ensures Teleport's cluster state remains reliable across all regions.

Extensive testing of the Teleport stack with CockroachDB demonstrated the solution's ability to deliver performance, resilience, and elasticity under heavy load and cross-region traffic. This architecture empowered the company to innovate faster, while complying with Tier 0 requirements of secure, uninterrupted access for internal teams worldwide.

With the architectural decisions in place, let's walk through a real-world setup that mirrors this approach using Teleport and CockroachDB in a [multi-regional deployment](https://goteleport.com/docs/admin-guides/deploy-a-cluster/multi-region-blueprint/).

---

## How to Set Up a Multi-Region Teleport Deployment to Secure Global Infrastructure Access

The following guide walks you through setting up a multi-region Teleport with CockroachDB, ensuring that your infrastructure access is not only secure but also highly available and scalable. In this guide, CockroachDB will play two roles: the first as a storage backend for Teleport and the second as a [Teleport Protected Resource (TPR)](https://goteleport.com/docs/enroll-resources/database-access/enroll-self-hosted-databases/cockroachdb-self-hosted/). Whether you're a developer looking to implement authentication for a single app or an enterprise seeking a globally distributed solution, the following tutorial will help you achieve your goals.

### Prerequisites

To run a multi-region Teleport deployment, you must:

- Create 3 peered regional VPCs (e.g., on AWS) or 1 global VPC (e.g., on GKE).
- Create 1 Kubernetes cluster in each region; Pod CIDRs must not overlap.
- Teleport Proxy Service instances able to dial each other by IP address. This means you have cross-region Pod/Instance connectivity, typically achieved with VPC peering and/or service mesh.
- Multi-region object storages (e.g., AWS S3) for session recordings, with the required IAM policies and set up two-way-replication between the object storages.
- A GeoDNS (e.g., Route53) with a Geoproximity routing policy to route users and Teleport Agents to the closest Teleport cluster.
- A multi-region CockroachDB cluster. You can use [this tool](https://github.com/amineelkouhen/tf-roach) to provision a multi-region deployment.
- The `tctl` and `tsh` tools installed in a client host (e.g., an Amazon EC2 instance).

### Step 1: Set Up CockroachDB as a Storage Backend

First, create the Teleport databases and user in CockroachDB:

```sql
CREATE DATABASE teleport_backend;
CREATE DATABASE teleport_audit;
CREATE USER teleport;
GRANT CREATE ON DATABASE teleport_backend TO teleport;
GRANT CREATE ON DATABASE teleport_audit TO teleport;
SET CLUSTER SETTING kv.rangefeed.enabled = true;
```

For a production-like setup, you must set up mutual TLS authentication and make sure that:

- Teleport trusts certificates presented by CockroachDB nodes.
- CockroachDB nodes trust client certificates signed by both your CockroachDB CA and your Teleport cluster's `db_client` CA.

You can sign a certificate for the `teleport` user with [the cockroach certs command](https://www.cockroachlabs.com/docs/stable/cockroach-cert). You must end up with three files:

- `client.teleport.crt`
- `client.teleport.key`
- `ca.crt`

Then, declare both zones and regions to CockroachDB and configure regional fault tolerance on the database:

```sql
ALTER DATABASE teleport_backend SET PRIMARY REGION <region1>;
ALTER DATABASE teleport_backend ADD REGION IF NOT EXISTS <region2>;
ALTER DATABASE teleport_backend ADD REGION IF NOT EXISTS <region3>;
ALTER DATABASE teleport_backend SET SECONDARY REGION <region2>;
ALTER DATABASE teleport_backend SURVIVE REGION FAILURE;
ALTER DATABASE teleport_audit SET PRIMARY REGION <region1>;
ALTER DATABASE teleport_audit ADD REGION IF NOT EXISTS <region2>;
ALTER DATABASE teleport_audit ADD REGION IF NOT EXISTS <region3>;
ALTER DATABASE teleport_audit SET SECONDARY REGION <region2>;
ALTER DATABASE teleport_audit SURVIVE REGION FAILURE;
```

Note: if the primary and secondary regions are far from each other (for example, on different continents), this will make CockroachDB write operations slower.

### Step 2: Set Up the Teleport K8S Cluster

Teleport provides [Helm charts](https://github.com/gravitational/teleport/tree/master/examples/chart) for installing the Teleport Database Service in Kubernetes Clusters. To allow Helm to install charts hosted in the Teleport Helm repository, add the teleport repository:

```bash
helm repo add teleport https://charts.releases.teleport.dev
helm repo update
```

Once all Teleport dependencies are set up, deploy Teleport via the `teleport-cluster` Helm chart. You need to create one release per Kubernetes cluster. Here is an example of the values for one specific region:

```yaml
chartMode: standalone
clusterName: teleport-multi-region.cluster.cockroachlabs.com
persistence:
  enabled: false
enterprise: true
auth:
  teleportConfig:
    # Configure CockroachDB
    teleport:
      storage:
        type: cockroachdb
        conn_string: "postgres://teleport@nlb-2025061618161615980000000c-d25a41afe9be1bd5.elb.us-east-1.amazonaws.com:26257/teleport_backend?sslmode=verify-full&pool_max_conns=20"
      audit_events_uri:
        - "postgres://teleport@nlb-2025061618161615980000000c-d25a41afe9be1bd5.elb.us-east-1.amazonaws.com:26257/teleport_audit?sslmode=verify-full"
      audit_sessions_uri: "uri://teleport-crdb-demo.s3.us-east-1.amazonaws.com/session_records?complete_initiators=teleport-crdb-iam-upload-role"
      ttl_job_cron: '*/20 * * * *'
    # Configure proxy peering
    auth_service:
      tunnel_strategy:
        type: proxy_peering
        agent_connection_count: 2
    # Mount the CockroachDB certs and have Teleport use them (via default env vars)
    extraVolumes:
      - name: db-certs
        secret:
          secretName: cockroach-certs
    extraVolumeMounts:
      - name: db-certs
        mountPath: /var/lib/db-certs
        readOnly: true
    extraEnv:
      - name: PGSSLROOTCERT
        value: /var/lib/db-certs/ca.crt
      - name: PGSSLCERT
        value: /var/lib/db-certs/client.teleport.crt
      - name: PGSSLKEY
        value: /var/lib/db-certs/client.teleport.key
    tls:
      existingSecretName: proxy-cert
    highAvailability:
      replicaCount: 2
```

Now you can test your multi-regional deployment. CockroachDB is set as a Storage Backend for the Teleport Cluster. To check that you can connect to your Teleport cluster, sign in with `tsh login`, then verify that you can run `tctl` commands using your current credentials:

```bash
tsh login --proxy=teleport-multi-region.cluster.cockroachlabs.com --user=amine@cockroachlabs.com
tctl status
Cluster teleport-multi-region.cluster.cockroachlabs.com
Version 18.1.0
CA pin sha256: ....
```

### Step 3: Set Up the Teleport Database Service

The Database Service requires a valid join token to join your Teleport cluster. Run the following `tctl` command and save the token output:

```bash
tctl tokens add --type=db --format=text
```

Install the Teleport Kube Agent into your Kubernetes Cluster with the Teleport Database Service configuration. Hereafter, you will find the CockroachDB configuration for the database `demo-assets`, the one you want to secure access to using Teleport (don't confuse it with the storage backend DB):

```bash
helm install teleport-kube-agent teleport/teleport-kube-agent \
  --create-namespace \
  --namespace teleport-agent \
  --set roles=db \
  --set proxyAddr=teleport-multi-region.cluster.cockroachlabs.com:443 \
  --set authToken=${JOIN_TOKEN?} \
  --set "databases[0].name=demo-assets" \
  --set "databases[0].uri=http://20250516154447737700000007-27042aa4022d3b9a.elb.us-east-1.amazonaws.com/:26257" \
  --set "databases[0].protocol=cockroachdb" \
  --set "databases[0].static_labels.env=dev" \
  --version 18.1.0
```

### Step 4: Create a Teleport User

Create a local Teleport user with the built-in `access` and `requester` roles:

```bash
tctl users add \
  --roles=access,requester \
  --db-users="*" \
  --db-names="*" \
  danielle
```

### Step 5: Create a CockroachDB User

Teleport uses mutual TLS authentication with CockroachDB. Client certificate authentication is available to all CockroachDB users. If you don't have one, connect to your Cockroach cluster and create it. You can also prevent the user from using password auth and mandate client certificate auth by using the `WITH PASSWORD NULL` clause:

```sql
CREATE USER danielle WITH PASSWORD NULL;
```

Now, log in to your Teleport cluster. Your CockroachDB cluster should appear in the list of available databases:

```bash
tsh login --proxy=teleport-multi-region.cluster.cockroachlabs.com --user=danielle
tsh db ls
Name            Description              Labels
-----           ---------------          -------
demo-assets     Example CockroachDB      env=dev
```

### Step 6: Connect to the CockroachDB (TPR DB)

To retrieve credentials for a database and connect to it:

```bash
tsh db connect demo-assets
```

You can optionally specify the database name and the user to use by default when connecting to the database server:

```bash
tsh db connect --db-user=danielle demo-assets
```

By following this guide, you have successfully set up a global infrastructure access system with Teleport and CockroachDB. This setup ensures scalability, high availability, and resilience while securing your enterprise infrastructure assets.

---

## Summary

By using Teleport and CockroachDB, a global payments leader not only solved a technical scaling problem, but also created a foundation for future-proof, auditable, and regionally compliant infrastructure access across its global engineering teams.

Their infrastructure story is more than just about technology choice — it's about aligning architecture with business-critical goals, and building systems that can uphold the trust of a global customer base that depends on this company every second of every day. By leveraging CockroachDB, this global payments leader enabled multi-region presence, resilience to network disruptions, and consistent access control across continents.

In this article, we also provided a hands-on guide to help you replicate this use case. We used CockroachDB as a storage backend to save internal states of the Teleport control plane, but also as a [Teleport Protected Resource (TPR)](https://goteleport.com/docs/enroll-resources/database-access/enroll-self-hosted-databases/cockroachdb-self-hosted/) that we secure using Teleport itself. Whether you're managing internal engineering access or scaling enterprise-wide, identity-aware infrastructure, Teleport and CockroachDB offer a powerful foundation for secure, always-on infrastructure access management.
