---
date: 2026-04-23
layout: post
title: "Orchestration de workflows durables avec Temporal et CockroachDB"
subtitle: "Comment exécuter Temporal avec CockroachDB comme backend de persistance distribué et fortement cohérent"
cover-img: /assets/img/cover-temporal.svg
thumbnail-img: /assets/img/cover-temporal.svg
share-img: /assets/img/cover-temporal.svg
tags: [integrations, CockroachDB, temporal, workflow, orchestration, Agentic AI, Artificial Intelligence]
lang: fr
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

Les applications d'IA modernes ne sont plus de simples appels d'inférence : ce sont des agents de longue durée qui planifient, agissent, observent et réessaient au fil du temps. Une boucle d'agent IA qui récupère du contexte depuis un vector store, appelle un LLM, écrit des résultats en base de données, attend une validation humaine, puis déclenche des actions en aval peut s'exécuter pendant des minutes, des heures, voire des jours. Sans une **couche d'orchestration durable**, toute défaillance d'infrastructure transitoire relance l'intégralité de la boucle depuis le début : refacturant des appels LLM coûteux, dupliquant les effets de bord et perdant tout le contexte accumulé.

Coordonner ces agents de manière fiable nécessite une couche qui :
- **Survit aux pannes** : l'état de l'agent est persisté après chaque étape, pas gardé en mémoire
- **Garantit l'exécution exactement-une-fois** : un appel LLM ou une écriture API externe n'est jamais ré-invoqué après son succès
- **Passe à l'échelle horizontalement** : des milliers d'instances d'agents concurrentes sans goulots d'étranglement
- **Permet des longues attentes** : un agent peut attendre des jours une réponse humaine-dans-la-boucle sans maintenir un processus ouvert

[Temporal](https://temporal.io/) est la plateforme open-source de référence pour ce type de problème. [CockroachDB](https://www.cockroachlabs.com/) est son backend de persistance distribué idéal, offrant au cluster d'exécution sans état de Temporal un socle de stockage indestructible et répliqué globalement.

Un **framework d'orchestration de workflows** gère le cycle de vie de programmes multi-étapes à longue durée d'exécution. Au lieu d'écrire des boucles de retry, une logique de point de contrôle et une reprise sur panne manuellement, vous déclarez votre logique métier comme une séquence d'**étapes durables** et laissez le framework s'occuper du reste. Les promesses fondamentales sont :

- **Durabilité** : l'état du workflow survit aux pannes de processus, aux redémarrages et aux défaillances d'infrastructure
- **Sémantique exactement-une-fois** : les étapes individuelles ne sont jamais ré-exécutées après leur complétion
- **Idempotence** : relancer le même workflow avec le même identifiant est sans effet
- **Observabilité** : l'historique complet d'exécution est consultable à tout moment

---

## Qu'est-ce que Temporal ?

[Temporal](https://temporal.io/) est une plateforme open-source, indépendante du langage, pour construire des applications distribuées fiables. Elle introduit le concept d'**exécution durable**, à savoir la garantie que la logique d'un workflow s'exécute jusqu'à complétion quelle que soit la défaillance d'infrastructure.

### Concepts clés

| Concept | Définition |
|---|---|
| **Workflow** | Fonction tolérante aux pannes orchestrant des Activities ; peut s'exécuter pendant des années |
| **Activity** | Unité de travail individuelle et retriable (appel API, écriture en base, inférence ML) |
| **Worker** | Processus qui interroge Temporal pour des tâches et exécute les Workflows et Activities |
| **Event History** | Journal append-only de chaque Command et Event dans la vie d'un workflow ; source de vérité pour la reprise |
| **Namespace** | Frontière d'isolation logique ; historiques d'événements, files de tâches et quotas séparés |
| **Task Queue** | Canal durable reliant un Workflow/Activity à un ensemble de Workers |
| **Signal / Query** | Mécanismes permettant à du code externe d'envoyer des données à, ou de lire l'état d'un workflow en cours |

---

## Comment fonctionne Temporal

Comprendre pourquoi CockroachDB est le bon backend de persistance pour Temporal nécessite de comprendre comment Temporal stocke son état. Les choix de conception qui rendent Temporal fiable exigent exactement le type de base de données distribuée et fortement cohérente que CockroachDB fournit.

### Workflow comme machine à états

Chaque workflow en cours d'exécution est modélisé comme une machine à états. Chaque interaction externe, qu'il s'agisse d'une activité terminée, d'un timer déclenché ou d'un signal reçu, produit un nouvel **événement** ajouté au **journal d'historique** du workflow. L'état courant d'un workflow est entièrement déterminé en rejouant ce journal depuis le début.

<img src="/assets/img/temporal-state-machine.png" alt="Machine à états du workflow Temporal" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**Une exécution de workflow est une machine à états déterministe pilotée par un historique d'événements en ajout seul**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Quand un Worker redémarre après un crash, il récupère l'historique des événements et rejoue la fonction de workflow. Les étapes déjà terminées sont ignorées instantanément ; l'exécution reprend depuis le dernier état validé.

### La cohérence est non négociable

Chaque transition d'état doit atomiquement mettre à jour l'état du workflow **et** mettre en file la prochaine tâche. Si l'une des deux écritures échoue, le système entre dans un état incohérent irrécupérable : une tâche fantôme qui ne sera jamais délivrée.

<img src="/assets/img/temporal-transactions.png" alt="Mises à jour transactionnelles Temporal" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**Les transitions d'état requièrent une mise à jour atomique de l'état du workflow et des entrées de file de tâches dans une seule transaction**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

C'est pourquoi Temporal exige un store relationnel fortement cohérent avec des garanties ACID complètes, et pourquoi CockroachDB, qui offre l'isolation sérialisable à n'importe quelle échelle, est un choix naturel là où un primaire PostgreSQL unique deviendrait un goulot d'étranglement.

### Visibilité : index interrogeable des workflows

En plus du store principal, Temporal maintient un **Visibility store**, une base de données secondaire optimisée pour interroger les exécutions de workflow par statut, type, heure de démarrage et attributs de recherche personnalisés stockés en JSONB.

<img src="/assets/img/temporal-visibility.png" alt="Visibilité des workflows Temporal" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**Le Visibility store indexe les exécutions de workflow pour les requêtes de liste et filtre via des attributs de recherche JSONB**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Le schéma PostgreSQL standard indexe le JSONB via `CREATE EXTENSION IF NOT EXISTS btree_gin`, une extension exclusive à PostgreSQL qui **n'existe pas dans CockroachDB**. Le correctif est le `CREATE INVERTED INDEX` natif de CockroachDB, qui offre la même capacité sans aucune extension (voir la section schéma ci-dessous).

### Architecture complète du cluster avec CockroachDB

Un cluster Temporal est composé de quatre services sans état passant à l'échelle indépendamment, devant deux niveaux de stockage durable. Quand CockroachDB supporte les deux stores, l'ensemble du niveau de persistance bénéficie de la réplication distribuée, du basculement automatique et de la scalabilité horizontale, de manière transparente pour les services Temporal.

<img src="/assets/img/temporal-architecture-overview.png" alt="Architecture du cluster Temporal avec CockroachDB" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**Cluster Temporal avec CockroachDB comme backend de persistance et de visibilité**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

| Service | Rôle |
|---|---|
| **Frontend** | Passerelle gRPC : route les requêtes clients vers le bon shard History |
| **History** | Gère les machines à états des workflows ; traite les commandes et enregistre les événements |
| **Matching** | Gère les files de tâches ; distribue les tâches aux Workers disponibles |
| **Worker** | Exécute les workflows système internes (réplication, archivage, nettoyage) |
| **Persistence Store (CockroachDB)** | Historiques d'événements, timers, files de transfert ; forte cohérence, écritures distribuées |
| **Visibility Store (CockroachDB)** | Index d'exécution interrogeable ; index inversé JSONB remplace `btree_gin` |

---

## Pourquoi CockroachDB pour Temporal ?

Temporal supporte officiellement PostgreSQL, MySQL, SQLite et Cassandra. CockroachDB convient parfaitement au persistence store car il apporte :

- **SQL distribué fortement cohérent** : les mêmes garanties ACID que PostgreSQL, à n'importe quelle échelle
- **Multi-région actif-actif** : les shards d'historique Temporal se distribuent entre régions sans réplication manuelle
- **Basculement automatique** : les défaillances de nœuds sont transparentes pour les services Temporal
- **Scalabilité horizontale** : scalez lectures et écritures sans logique de sharding dans l'application
- **Protocole filaire PostgreSQL** : le plugin `postgres12` de Temporal fonctionne directement

---

## Déployer Temporal sur CockroachDB

### Étape 1 : Provisionnement des bases et de l'utilisateur

```sql
CREATE DATABASE temporal;
CREATE DATABASE temporal_visibility;
CREATE USER temporal WITH PASSWORD 'temporal';
GRANT ALL ON DATABASE temporal TO temporal;
GRANT ALL ON DATABASE temporal_visibility TO temporal;
```

### Étape 2 : Initialisation du schéma de persistance

Le schéma principal fonctionne avec CockroachDB sans modification via l'outil SQL de Temporal :

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

### Étape 3 : Correction du schéma de visibilité pour CockroachDB

> **C'est le correctif critique.** Le schéma de visibilité avancée de Temporal contient `CREATE EXTENSION IF NOT EXISTS btree_gin`, une extension exclusive à PostgreSQL. CockroachDB ne supporte pas cette extension et la migration de schéma **échoue** à cette ligne.

La cause racine est cette migration dans `schema/postgresql/v12/visibility/versioned/v1.1/manifest.json` :

```sql
-- PostgreSQL only — FAILS on CockroachDB
CREATE EXTENSION IF NOT EXISTS btree_gin;
CREATE INDEX custom_search_attributes_idx
  ON executions_visibility
  USING gin(search_attributes jsonb_path_ops);
```

**Le correctif** : contourner l'outil de migration standard pour la base de visibilité et appliquer directement un schéma compatible CockroachDB. CockroachDB supporte nativement les index inversés sur les colonnes JSONB sans aucune extension :

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

Initialisez la base de visibilité avec ce fichier de schéma directement :

```bash
cockroach sql \
  --url "postgresql://temporal@<crdb-host>:26257/temporal_visibility" \
  --certs-dir=/certs \
  --file ./crdb_visibility_schema.sql
```

### Étape 4 : Configuration du serveur Temporal

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

### Étape 5 : Premier workflow d'agent IA durable

La boucle d'agent suivante récupère du contexte, appelle un LLM, attend une validation humaine et écrit le résultat final. Chaque étape est une Activity ; elle s'exécute exactement une fois même si le processus crashe entre les étapes. Un appel LLM coûteux n'est jamais ré-émis après son succès.

```python
from temporalio import workflow, activity
from temporalio.common import RetryPolicy
from datetime import timedelta

@activity.defn
async def retrieve_context(task: str) -> str:
    """Query a vector store for relevant context."""
    return await vector_store.search(task)

@activity.defn
async def call_llm(context: str) -> str:
    """Call the LLM — billed once, never re-executed on retry."""
    return await llm_client.complete(f"Given this context: {context}, respond.")

@activity.defn
async def request_human_approval(response: str) -> bool:
    """Write pending approval to DB — the agent can wait days here."""
    return await approvals_db.create_pending(response)

@activity.defn
async def write_final_result(result: str) -> None:
    """Persist the approved result — exactly once."""
    await results_db.insert(result)

@workflow.defn
class AICockroachAgentWorkflow:
    @workflow.run
    async def run(self, task: str) -> str:
        # Step 1 — retrieve context (retries safely, idempotent)
        context = await workflow.execute_activity(
            retrieve_context, task,
            start_to_close_timeout=timedelta(minutes=2),
        )
        # Step 2 — LLM call (exactly once — no double billing)
        response = await workflow.execute_activity(
            call_llm, context,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )
        # Step 3 — human-in-the-loop (agent sleeps until approved, days if needed)
        approved = await workflow.execute_activity(
            request_human_approval, response,
            start_to_close_timeout=timedelta(days=7),
        )
        # Step 4 — persist result (idempotent write, exactly once)
        if approved:
            await workflow.execute_activity(
                write_final_result, response,
                start_to_close_timeout=timedelta(seconds=30),
            )
        return response
```

---

## Bénéfices clés

| Capacité | Contribution de CockroachDB |
|---|---|
| **Isolation sérialisable** | Pas de mises à jour perdues ni de lectures fantômes sous exécution concurrente |
| **Réplication multi-région** | Shards d'historique durables à travers les défaillances de data center |
| **Scalabilité horizontale** | Ajoutez des nœuds pour absorber plus de workflows concurrents sans re-sharding |
| **Basculement automatique** | Défaillances de nœuds transparentes pour les quatre services Temporal |
| **Compatibilité PostgreSQL** | Aucune modification du code applicatif ; le plugin `postgres12` fonctionne directement |

CockroachDB remplace PostgreSQL directement, offrant aux services sans état de Temporal une fondation indestructible et distribuée globalement, avec un seul correctif de schéma pour le visibility store.

---

## Voir aussi

- [Documentation Temporal](https://docs.temporal.io/)
- [Concevoir un moteur de workflow depuis les premiers principes](https://temporal.io/blog/workflow-engine-principles)
- [SQL distribué CockroachDB](https://www.cockroachlabs.com/blog/what-is-distributed-sql/)
