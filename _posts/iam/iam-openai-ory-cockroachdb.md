---
date: 2025-06-12
layout: post
title: "Inside OpenAI's Always-On IAM Stack with Ory and CockroachDB"
subtitle: "How OpenAI built a resilient, multi-region CIAM platform"
cover-img: /assets/img/cover-iam-p2.png
thumbnail-img: /assets/img/cover-iam-p2.png
share-img: /assets/img/cover-iam-p2.png
tags: [iam, security, authentication, authorization, CockroachDB, OpenAI, Ory]
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

As organizations scale globally and users expect seamless, real-time access from anywhere in the world, traditional [identity and access management (IAM) systems](https://www.cockroachlabs.com/solutions/usecases/identity-access-management/) often become a bottleneck. These legacy solutions, typically built on monolithic, region-bound architectures, struggle to provide the resilience, performance, and flexibility required in distributed, cloud-native environments. They often lack support for multi-region replication, offer limited observability, and are difficult to adapt to evolving product needs. Most importantly, they do not offer enterprises the control they need over their architecture as their business grows.

When an IAM system goes down, even briefly, it can block user logins, halt API access, and disrupt core application functionality. In today's digital-first world, where identity is the front door to every product experience, downtime is not an option. Always-on identity, capable of surviving regional outages and scaling effortlessly with user growth, is no longer a nice-to-have; it's a mission-critical requirement for modern applications operating at global scale.

This is where [Ory](https://www.ory.sh/) comes into play. This leading identity and access management (IAM) solution is helping organizations modernize their authentication and authorization stacks with a composable, cloud-native approach. Ory has established itself as a pioneer in delivering flexible, scalable, and developer-friendly IAM tools for modern applications.

Among the companies leveraging Ory to meet these demands is [OpenAI](https://www.ory.sh/case-studies/openai), which needed a resilient, multi-region IAM infrastructure to support global user access for ChatGPT. This article explores how OpenAI integrated Ory with CockroachDB to build an always-on authentication system, and the lessons learned from building a highly available IAM solution.

---

## Executive Summary

- **Modern applications demand always-on identity:** Legacy identity and access management (IAM) systems can't meet the expectations of today's global, always-connected users. Downtime in IAM can cripple product experiences.
- **Ory redefines IAM for the cloud-native era:** Ory provides modular, open-source, API-first IAM components that scale independently and support complex use cases like fine-grained access control, passwordless login, and social sign-ins.
- **OpenAI's challenge, scaling IAM:** With the explosive growth of ChatGPT, OpenAI required a resilient, multi-region CIAM platform that could operate seamlessly across geographies, support fast iteration, and stay vendor-neutral.
- **The Ory + CockroachDB solution:** OpenAI deployed Ory's identity stack on CockroachDB, our distributed SQL database known for enterprise-ready resilience, to achieve global consistency, automated failover, and high availability across regions.
- **Secure, scalable, always-available IAM:** The described architecture ensures that authentication and access control remain consistent and online even during regional outages, allowing OpenAI to serve millions of users with uninterrupted experiences.
- **Key takeaways:** Always-on IAM is now a baseline requirement for customer-facing applications. Architecting for resilience and scale, as demonstrated by the Ory and CockroachDB partnership, is essential to meet modern demands.

---

## Meet Ory: Modern, Flexible, and Scalable IAM

Ory provides a powerful suite of identity and access management tools, designed from the ground up to support distributed systems and cloud-native architectures. At the core of Ory's [offerings](https://www.ory.sh/deployment-solutions) is a set of modular, API-first services designed to address various aspects of identity and access management. These include components such as:

- [Ory Kratos](https://www.ory.sh/kratos) for identity management (including users, groups, and organizations)
- [Ory Hydra](https://www.ory.sh/hydra) for OAuth2 and OIDC flows
- [Ory Keto](https://www.ory.sh/keto) for fine-grained authorization and relationship-based access control (ReBAC, inspired by Google Zanzibar)
- [Ory Oathkeeper](https://www.ory.sh/oathkeeper) for edge authentication and request-level access control with an Identity and Access Proxy

Each of these services is built to scale independently and integrate seamlessly, giving teams the flexibility to tailor their IAM systems to their exact needs. By decoupling concerns like [identity, authorization, and federation](/2025-05-23-iam-guide/), Ory allows organizations to adopt a composable security model that is both robust and extensible.

Ory's commitment to open-source principles has fostered a vibrant community of developers and contributors. [The company's projects](https://github.com/ory) have garnered significant attention, with over 35,000 GitHub stars and a presence in more than 50,000 live deployments worldwide. This community-driven approach ensures continuous improvement, transparency, and adaptability to the evolving needs of the digital landscape.

In addition to its open-source offerings, Ory provides a fully managed SaaS solution through the [Ory Network](https://www.ory.sh/network), a global, high-availability IAM platform that delivers low-latency identity services. This platform supports a range of authentication methods, including passkeys, passwordless login, multi-factor authentication, and social sign-ins, catering to the diverse requirements of modern applications. For organizations where identity infrastructure becomes mission-critical, and you need enterprise-grade reliability, Ory offers the Ory Enterprise License (OEL) which bridges self-hosted flexibility with enterprise support, giving you enterprise support for production-readiness and extensively tested releases that keeps your business secure and moving forward.

<img src="/assets/img/iam-p2-ory-architecture.png" alt="Ory Architecture Overview" style="width:100%">

{: .mx-auto.d-block :}
**Figure 1: Ory Architecture Overview**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

---

## The OpenAI Use Case: Multi-Region CIAM at Scale

When OpenAI launched ChatGPT in November 2022, it quickly became one of the fastest-growing applications in history, reaching 1 million users within five days and surpassing 100 million monthly active users by January 2023. By December 2024, ChatGPT had over 400 million weekly active users. This unprecedented scale brought with it an urgent need for a modern, reliable customer identity and access management (CIAM) platform.

The rapid expansion exposed limitations in traditional CIAM solutions, which often rely on closed, inflexible architectures that hinder customization, transparency, and self-hosting. These legacy systems simply couldn't meet OpenAI's requirements for innovation velocity, user experience control, and cloud-native integration.

<img src="/assets/img/iam-p2-chatgpt-visits.png" alt="ChatGPT Daily Visits rapid expansion" style="width:100%">

{: .mx-auto.d-block :}
**Figure 2: ChatGPT's rapid expansion**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

To keep pace with product growth and evolving user expectations, OpenAI needed a CIAM solution that could scale effortlessly, support advanced analytics, and operate seamlessly across cloud environments. It wasn't just about authentication. It was about building a foundation for secure, user-centric experiences at massive scale.

When OpenAI set out to build a multi-region IAM system, the requirements were clear: the system needed to be resilient to regional failures, capable of supporting global user bases, and consistent in enforcing access control and session management across its services. To address these needs, OpenAI sought a solution that aligned with its product-first mindset, modular, transparent, and free from [vendor lock-in](https://www.cockroachlabs.com/blog/multi-cloud-deployment-distributed-sql/). It needed IAM infrastructure that could evolve as quickly as the products it supported.

---

## The Solution: Ory and CockroachDB for Scalable CIAM

OpenAI chose to partner with Ory to bring flexibility and control to its identity infrastructure. At the heart of this integration was [Ory Hydra](https://www.ory.sh/hydra), a web-scale OAuth2 and OpenID Connect provider capable of handling authorization at global scale. Ory stood out among other IAM platforms as the ideal solution. Its modular design, open-source foundation, and cloud-native compatibility aligned perfectly with OpenAI's needs.

However, to achieve true global availability, it was critical to pair Ory's IAM capabilities with a distributed SQL database that could keep up with the demands of cross-region replication, strong consistency guarantees, and fault tolerance. That's where [CockroachDB](https://www.cockroachlabs.com/product/overview/) came in.

CockroachDB is a distributed SQL database designed for global scale and high availability. Since it became the first commercially available distributed SQL database, CockroachDB has become known for its enterprise-ready resilience. It replicates data across multiple regions while offering serializable isolation, strong consistency, and automated failover. By deploying Ory components on top of CockroachDB, OpenAI was able to ensure that identity and access control data remained consistent and always available, even [during infrastructure disruptions](https://www.cockroachlabs.com/blog/database-testing-performance-under-adversity/). For instance, a user logging in from Europe, while a data center in the U.S. experiences downtime, would still be able to authenticate and authorize requests without issue. This level of resilience was critical for maintaining seamless user experiences across geographies.

<img src="/assets/img/iam-p1-cloud-portability.png" alt="How CockroachDB Enables Cloud Portability" style="width:100%">

{: .mx-auto.d-block :}
**How CockroachDB Enables Cloud Portability**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

> **Measure what matters.** Traditional benchmarks only test when everything's perfect. But you need to know what happens when everything fails. CockroachDB's benchmark, "Performance under Adversity," tests real-world scenarios: network partitions, regional outages, disk stalls, and so much more. [See it in action](https://www.cockroachlabs.com/performance-under-adversity/?referralid=blogs_pua_launch_bottom_card)

Extensive testing of the Ory Network alongside CockroachDB demonstrated the solution's ability to deliver performance, resilience, and elasticity under heavy load and cross-region traffic. This architecture empowered OpenAI to innovate faster, while ensuring secure, uninterrupted access for millions of users worldwide. Through an Ory Enterprise License, OpenAI gained access to advanced authorization capabilities, along with the ability to self-host, fine-tune configurations, and maintain full control of its CIAM stack. Together with CockroachDB's fault-tolerant, globally replicated database, the solution offers a modern IAM foundation that evolves with OpenAI's pace of development, supporting security, compliance, and seamless user experiences at scale.

---

## How IAM Components Use CockroachDB

The integration focused on three core Ory services. Ory Kratos handled identity management, including user credentials, profile metadata, and sessions. Ory Hydra served as the OAuth2 and OIDC provider, managing token issuance, consent flows, and client registration. Ory Keto implemented fine-grained access control based on Google Zanzibar-inspired relationships.

Each of these components relied on CockroachDB to store their state in a consistent and durable way, enabling them to function correctly even in the presence of partial outages or regional network partitions. Ory's architecture is well-suited to operate with CockroachDB because of its stateless design and API-first philosophy. Each component can be deployed as a stateless service, with its only persistence requirement being [the backing SQL database](https://www.cockroachlabs.com/blog/what-is-distributed-sql/). This makes it straightforward to horizontally scale services, perform rolling updates, or deploy new regions without having to orchestrate complex data migrations. CockroachDB, in turn, provides the always-consistent database layer that ensures user identities, access control rules, and session tokens are always accurate, no matter which region is serving a request.

<img src="/assets/img/iam-p2-multi-region-architecture.png" alt="Ory CockroachDB Multi-Region Deployment Architecture" style="width:100%">

{: .mx-auto.d-block :}
**Figure 3: Ory, CockroachDB Multi-Region Deployment Architecture**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

From a technical standpoint, identity and authorization in this system are modeled as structured entities within CockroachDB. The use of CockroachDB's strongly consistent [transactions](https://www.cockroachlabs.com/docs/stable/transactions) ensures that IAM operations remain correct, even when issued concurrently from different regions or under network duress.

### 1. Kratos

Kratos stores user identity records, recovery flows, sessions, and login attempts in transactional tables. The diagram below illustrates the data model used by Ory Kratos, the identity and user management component of the Ory stack. At the heart of this schema is the `identities` table, which represents individual users in the system. Nearly every other table in the schema connects to this central entity, reflecting the various aspects of a user's identity lifecycle, from login credentials and sessions to recovery and verification flows.

<img src="/assets/img/iam-p2-kratos-data-model.png" alt="Ory Kratos Data Model" style="width:100%">

{: .mx-auto.d-block :}
**Figure 4: Ory Kratos Data Model**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Each identity can be associated with one or more credentials, stored in the `identity_credentials` table. These credentials define how a user authenticates with the system, such as through a password, social login, or other mechanisms. The type of each credential, whether it's a password, an OpenID Connect token, or another method, is defined in the `identity_credential_types` table, ensuring a consistent and extensible way to categorize authentication mechanisms. To support flexible login options, the `identity_credential_identifiers` table stores unique identifiers like usernames or email addresses that are linked to specific credentials.

Beyond authentication, Ory Kratos also supports comprehensive account recovery and verification workflows. The `identity_recovery_addresses` table stores contact points such as recovery email addresses that can be used to initiate account recovery. Associated with these are `identity_recovery_tokens`, which represent one-time-use tokens issued during recovery flows, enabling secure reset or re-verification operations. Similarly, the `identity_verifiable_addresses` table tracks verifiable addresses, typically emails, that require confirmation before being trusted by the system.

The `sessions` table keeps track of user login sessions, associating each active session with a specific identity. This allows the system to manage session lifecycle, expiration, and security-related checks in a distributed and scalable way. The typical interaction flow between a browser-based client, a backend application, and Ory Kratos is structured as follows:

<img src="/assets/img/iam-p2-kratos-flow.png" alt="Interaction flow using Ory Kratos" style="width:100%">

{: .mx-auto.d-block :}
**Figure 5: Interaction flow using Ory Kratos**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

The sequence diagram above illustrates a typical self-service identity flow using Ory Kratos, involving a frontend application, a backend application, and the Kratos identity service. This flow is common in scenarios like user login, registration, or profile updates, where the frontend manages the user interface while Kratos handles the identity logic.

The process begins when the frontend application initiates a self-service flow by sending a GET request to Ory Kratos, for example to the `/self-service/login/browser` or `/self-service/registration/browser` endpoint. In response, Kratos returns an HTTP 200 OK status along with a JSON payload that describes the flow. This payload includes information needed to render the appropriate form, such as required fields and configuration data.

Using this payload, the frontend renders a form for the user to interact with. The user then fills out the form, whether to log in, sign up, or update their profile, and submits it. The frontend application then forwards the submitted form data to the corresponding self-service endpoint, passing the flow ID as a query parameter. The payload includes the user's input data. Kratos then validates the submitted payload. If the data is valid, it performs the appropriate action: for example, it may create a new user, update an email address, or issue a session cookie to log the user in. If the payload is invalid, perhaps due to missing fields or incorrect values, Kratos updates the flow with validation errors and returns a 400 Bad Request response. The frontend then re-renders the form with validation feedback, allowing the user to correct their input and resubmit.

Once the user successfully completes the flow and receives a session cookie from Kratos, the frontend can use this session cookie to make authenticated requests to the backend application. When the backend receives these requests, it delegates session validation to Kratos, which confirms whether the session is valid before allowing access to protected resources.

### 2. Hydra

Having covered how identity is managed, let's turn to how secure authorization is handled with Ory Hydra. Ory Hydra is a server implementation of the OAuth 2.0 authorization framework and the OpenID Connect Core 1.0. It tracks clients, consent requests, and tokens with strong consistency to prevent replay attacks or duplicate authorizations.

The OAuth 2.0 authorization framework enables a third-party application to obtain limited access to an HTTP service, either on behalf of a resource owner by orchestrating an approval interaction between the resource owner and the HTTP service, or by allowing the third-party application to obtain access on its own behalf.

<img src="/assets/img/iam-p2-oauth2-flow.png" alt="OAuth2 Flow" style="width:100%">

{: .mx-auto.d-block :}
**Figure 6: OAuth2 flow**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

The OAuth 2.0 authorization flow involving a client application, the resource owner, Ory Hydra (as the authorization server), and the resource server is structured as follows:

<img src="/assets/img/iam-p2-hydra-flow.png" alt="Interaction flow using Ory Hydra" style="width:100%">

{: .mx-auto.d-block :}
**Figure 7: Interaction flow using Ory Hydra**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

The sequence diagram depicts the interactions between four key components: the Client, the Resource Owner (typically the user), Ory Hydra, and the Resource Server (the API or service that hosts protected resources).

The flow begins when the Client, an application seeking access to protected resources, initiates a request for authorization from the Resource Owner. This typically takes the form of a redirect to a login or consent screen provided by the Authorization Server (Ory Hydra). The Resource Owner reviews the request and, upon granting access, provides an authorization grant (often an authorization code) to the client.

Next, the Client uses this authorization grant to request an access token from Ory Hydra. Along with the grant, the client also authenticates itself (using credentials such as a client ID and secret). Ory Hydra validates the authorization grant and client credentials. If everything checks out, it responds by issuing an access token to the client.

Armed with the access token, the Client then makes a request to the Resource Server, presenting the token as proof of authorization. The Resource Server validates the access token, often by introspecting it via Hydra or verifying its signature if it's a JWT (JSON Web Token), and, if valid, serves the requested protected resource to the client.

This flow encapsulates the standard Authorization Code Grant pattern in OAuth 2.0, with Ory Hydra fulfilling the role of a secure, standards-compliant authorization server that manages token issuance, validation, and policy enforcement. It's designed to separate concerns between applications and services, enabling scalable and secure delegated access.

The following data model represents the implementation of the OAuth2 flow in Ory Hydra. This schema outlines how OAuth2 and OIDC flows are handled, from client registration to issuing access tokens, refresh tokens, authorization codes, and managing authentication sessions.

<img src="/assets/img/iam-p2-hydra-data-model.png" alt="Ory Hydra Data Model" style="width:100%">

{: .mx-auto.d-block :}
**Figure 8: Ory Hydra Data Model**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

At the core of this schema is the `hydra_client` table, which defines OAuth2/OIDC clients registered within a Hydra Network. These clients represent applications that can initiate authorization flows and request access tokens. Every major flow, including authorization code, access token, refresh token, and device authorization, is tied back to a specific client.

The `hydra_oauth2_flow` table models the lifecycle of an OAuth2 authorization flow. It serves as a unifying entity that links various stages of an OAuth2 transaction: authorization codes, device codes, access tokens, and refresh tokens. This flow-centric model provides traceability across all issued credentials and ensures cohesive handling of authorization decisions.

The `hydra_oauth2_code` table stores short-lived authorization codes issued during the OAuth2 Authorization Code Flow. These codes are exchanged by clients for access and refresh tokens. Each code is tied to a specific flow and client, and indirectly to the user's authentication session when present.

To support OpenID Connect, the `hydra_oauth2_oidc` table stores OIDC-specific information such as ID token data or nonce values. These entries are related back to a flow and client, ensuring compliance with OIDC specifications layered on top of OAuth2. Device-based authentication flows are handled by the `hydra_oauth2_device_auth_codes` table. This supports the OAuth2 Device Authorization Grant, enabling login on devices with limited input capabilities.

Access tokens are stored in the `hydra_oauth2_access` table, which includes information about token scope, expiration, and the associated flow. These tokens are issued after successful authorization and are the primary means by which clients access protected resources. For long-term sessions, Hydra supports refresh tokens, which are stored in the `hydra_oauth2_refresh` table. These tokens allow clients to request new access tokens without re-authenticating the user.

Authentication state is managed in the `hydra_oauth2_authentication_session` table. This optional relationship links a flow to a specific authentication session, tracking details like when the user authenticated and whether re-authentication is needed. This helps enforce policies like `prompt=login` or session expiration.

Together, these tables form a highly normalized schema that aligns with OAuth2 and OIDC standards while providing full visibility and control over every part of the authorization process. The `hydra_oauth2_flow` table serves as the central coordination point, ensuring all tokens, codes, and sessions are part of a traceable, auditable flow, ideal for large-scale, compliant identity systems.

### 3. Keto

Keto expresses access control as relationships, mapping subjects, objects, and permissions in a way that enables efficient permission checks even at massive scale. The diagram below shows the core data model used by Ory Keto, Ory's authorization service inspired by Google Zanzibar. Keto models fine-grained access control through `keto_relation_tuples`, which express permissions as relationships between subjects and objects. Each row in this table is a *relation tuple*, describing who (subject) can do what (relation) on which resource (object) within a defined namespace.

<img src="/assets/img/iam-p2-keto-data-model.png" alt="Ory Keto Data Model" style="width:100%">

{: .mx-auto.d-block :}
**Figure 9: Ory Keto Data Model**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

In Ory Keto, authorization is checked by evaluating whether a relation tuple exists (directly or through recursive expansion) that permits a given subject to perform a relation on an object in a namespace. This data model is designed for high scalability and flexibility, enabling complex access patterns like group membership, role inheritance, and hierarchical access rights.

A typical interaction between a user, an application, Ory Kratos, and Ory Keto looks like this:

<img src="/assets/img/iam-p2-keto-kratos-flow.png" alt="Interaction flow between Ory Keto and Ory Kratos" style="width:100%">

{: .mx-auto.d-block :}
**Figure 10: Interaction flow between Ory Keto and Ory Kratos**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

The process begins when the subject initiates a request to access a resource through the application. Upon receiving the request, the application first delegates the task of verifying the user's identity to Ory Kratos, which is responsible for user authentication. Kratos authenticates the subject, typically by validating credentials, session tokens, or cookies, and responds back to the application confirming the user's identity.

Once authentication is successful, the application then needs to determine whether the authenticated subject has the necessary permissions to access the requested resource. To do this, it sends an authorization query to Ory Keto, asking whether the subject is allowed to perform a specific action (in this case, "read") on the specified resource (e.g., "resource x"). Ory Keto evaluates the query against its stored authorization policies. If the subject is permitted to perform the requested action, Keto responds with a "Permissions Granted" response. With both authentication and authorization successfully completed, the application proceeds to return the requested resource to the subject.

- Ory Kratos handles **who the user is**
- Ory Keto determines **what the user is allowed to do**

This flow ensures a clear separation of concerns, forming a secure, scalable model for access management in modern applications.

---

## Ory and CockroachDB: The Combination for Next-Gen Identity Management

OpenAI is rapidly evolving its identity infrastructure, already achieving record-breaking login rates while maintaining levels of data transparency and infrastructure flexibility that were previously unattainable with traditional vendor solutions. This transformation reflects a fundamental shift toward modern, developer-centric identity architecture, one that prioritizes speed, visibility, and adaptability.

By adopting Ory and CockroachDB, OpenAI has gained the ability to innovate rapidly, developing and iterating on identity solutions tailored to a wide range of use cases across its expanding product ecosystem. The platform's modular and extensible design enables OpenAI to respond quickly to new requirements without being constrained by rigid or opaque systems. Scalability has also been a critical benefit. As global demand for AI services continues to surge, OpenAI can scale its identity systems seamlessly, ensuring consistent performance and reliability at massive scale. Deep observability into authentication flows and IAM operations allows the team to proactively optimize user experience, bolster security, and troubleshoot performance bottlenecks with precision.

Perhaps most importantly, resilience has been a defining factor. Even amid exponential user growth, Ory's architecture coupled with a resilient storage backend like CockroachDB enables reliable, always-on identity services that support uninterrupted access and secure engagement. As OpenAI continues to scale, the need for a highly available, transparent, and observable identity platform will only intensify, and Ory's modern CIAM capabilities are well-positioned to meet that challenge, far surpassing the limitations of legacy systems.

> *"For global enterprises, IAM can't be an afterthought. Modern IAM demands secure, compliant, multi-region access from day one, free from legacy database bottlenecks. We built Ory on CockroachDB for its inherently distributed architecture, enabling true multi-region deployments and data localization, essential for mission-critical identity infrastructure."*
> Aenas Rekkas, CTO of Ory

<img src="/assets/img/iam-p2-uninterrupted-access.png" alt="Uninterrupted access management with CockroachDB" style="width:100%">

{: .mx-auto.d-block :}
**Figure 11: Uninterrupted access management with CockroachDB**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

OpenAI's deployment spans across distinct data centers, each containing a set of CockroachDB nodes. Although physically distributed, these nodes form a unified, logically consistent database. Despite the failure of a node or an entire data center, the overall system remains fully operational. This is made possible by CockroachDB's use of the [Raft consensus protocol](https://www.cockroachlabs.com/docs/stable/architecture/replication-layer.html#raft), which allows the database to continue processing reads and writes as long as a quorum of replicas is available. In this configuration, the cluster is still able to serve global OpenAI authentication traffic through the functioning nodes in the healthy datacenters without data inconsistency or service interruption.

---

## Ory and CockroachDB Integration: Key Takeaways

Throughout the process of integrating Ory with CockroachDB, several key lessons emerged. First, ensuring schema compatibility and minimizing cross-region latencies are essential for performance-sensitive workloads like authentication. Tuning transactional workloads to avoid hotspots and leveraging [CockroachDB's multi-region capabilities](https://www.cockroachlabs.com/docs/stable/multiregion-overview), such as [follower reads](https://www.cockroachlabs.com/docs/stable/follower-reads) and [geo-partitioning](https://www.cockroachlabs.com/docs/stable/partitioning), were critical to achieving optimal performance.

<img src="/assets/img/iam-p2-data-locality.png" alt="Data locality: common patterns for table locality with CockroachDB" style="width:100%">

{: .mx-auto.d-block :}
**Figure 12: Data locality: common patterns for table locality with CockroachDB**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Second, [monitoring and observability](https://www.cockroachlabs.com/docs/stable/monitoring-and-alerting.html) were indispensable. Combining logs, metrics, and distributed traces helped identify bottlenecks and optimize latency paths across services and regions. Finally, adopting a modular, standards-based IAM platform like Ory accelerated the implementation and made it easier to reason about failure domains and service dependencies.

<img src="/assets/img/iam-p2-distributed-iam.png" alt="Distributed identity and access management (IAM) platform" style="width:100%">

{: .mx-auto.d-block :}
**Figure 13: Distributed identity and access management (IAM) platform**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

For organizations seeking to build similar architectures, the combination of Ory and CockroachDB offers a powerful pattern: composable, scalable IAM backed by a globally distributed, resilient SQL database. Whether you're serving users in a single region or spanning multiple continents, this approach provides a strong foundation for building secure, available, and consistent identity systems. OpenAI's journey highlights the value of investing in cloud-native, open-source technologies that work together to deliver truly always-on authentication.
