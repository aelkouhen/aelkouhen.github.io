---
date: 2026-04-23
layout: post
title: "Orchestration de workflows agentiques avec CockroachDB"
subtitle: "Comment Temporal et DBOS s'appuient sur CockroachDB comme backend de stockage durable et globalement cohérent pour des workflows d'agents résilients"
tags: [integrations, CockroachDB, temporal, dbos, workflow, orchestration, ai-agents, durable-execution]
lang: fr
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

Les applications d'IA modernes ne sont plus de simples appels d'inférence — ce sont des agents de longue durée qui planifient, agissent, observent et réessaient au fil du temps. Coordonner ces agents de manière fiable nécessite une **couche d'orchestration de workflows** qui survit aux pannes, passe à l'échelle horizontalement et garantit une sémantique d'exécution exactement-une-fois. Deux frameworks se sont imposés comme solutions de référence : [Temporal](https://temporal.io/) et [DBOS](https://dbos.dev/). Les deux peuvent utiliser [CockroachDB](https://www.cockroachlabs.com/) comme moteur de persistance, vous offrant un socle de stockage distribué, fortement cohérent et auto-réparant sous votre infrastructure d'agents.

---

## Qu'est-ce que l'orchestration de workflows ?

Un **framework d'orchestration de workflows** gère le cycle de vie de programmes multi-étapes à longue durée d'exécution. Au lieu d'écrire des boucles de retry, une logique de point de contrôle et une reprise sur panne manuellement, vous déclarez votre logique métier comme une séquence d'**étapes durables** et laissez le framework s'occuper du reste.

<img src="/assets/img/teleport-crdb-distributed-sql.png" alt="Garanties d'exécution durable" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**Des fonctions sans état aux workflows durables et reprenables**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Les promesses fondamentales de tout framework de workflows sont :

- **Durabilité** — l'état du workflow survit aux pannes de processus, aux redémarrages et aux défaillances d'infrastructure
- **Sémantique exactement-une-fois** — les étapes individuelles ne sont jamais ré-exécutées après leur complétion
- **Idempotence** — relancer le même workflow avec le même identifiant est sans effet
- **Observabilité** — l'historique complet d'exécution est consultable à tout moment

Pour les charges de travail d'agents IA, ces garanties sont essentielles. Une boucle d'agent qui interroge un LLM, écrit en base de données, appelle une API externe et attend une validation humaine peut s'exécuter pendant des minutes, des heures ou des jours. Sans couche d'orchestration durable, toute défaillance transitoire relance la boucle depuis le début, refacturant les appels API, dupliquant les effets de bord et perdant le contexte accumulé.

---

## Temporal

[Temporal](https://docs.temporal.io/) est une plateforme open-source, indépendante du langage, pour construire des applications distribuées fiables. Elle introduit le concept d'**exécution durable** — la garantie que la logique d'un workflow s'exécute jusqu'à complétion quelle que soit la défaillance d'infrastructure.

### Concepts clés

| Concept | Définition |
|---|---|
| **Workflow** | Fonction tolérante aux pannes orchestrant des Activities ; peut s'exécuter pendant des années |
| **Activity** | Unité de travail individuelle et retriable (appel API, écriture en base, inférence ML) |
| **Worker** | Processus qui interroge Temporal pour des tâches et exécute les Workflows et Activities |
| **Event History** | Journal append-only de chaque Command et Event dans la vie d'un workflow — source de vérité pour la reprise |
| **Namespace** | Frontière d'isolation logique ; historiques d'événements, files de tâches et quotas séparés |
| **Task Queue** | Canal durable reliant un Workflow/Activity à un ensemble de Workers |
| **Signal / Query** | Mécanismes permettant à du code externe d'envoyer des données à, ou de lire l'état d'un workflow en cours |

### Architecture

Temporal sépare l'**exécution** (services sans état) du **stockage** (persistance durable) :

<img src="https://docs.temporal.io/assets/images/temporal-system-simple-bbe37d1a86a71b86c23d97e676b4f6aa.svg" alt="Architecture du cluster Temporal" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**Cluster Temporal : services sans état adossés à une couche de persistance durable**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Le cluster est composé de quatre services sans état — **Frontend**, **History**, **Matching** et **Worker** — chacun passant à l'échelle indépendamment. Tout l'état durable transite par deux stores distincts :

- **Persistence Store** — état du workflow, historique des événements, timers et files de tâches. Requiert forte cohérence et latence faible.
- **Visibility Store** — index interrogeable des exécutions de workflow par statut, type et attributs de recherche personnalisés.

### Pourquoi CockroachDB pour Temporal ?

Temporal supporte officiellement PostgreSQL, MySQL, SQLite et Cassandra. CockroachDB convient parfaitement au persistence store car il apporte :

- **SQL distribué fortement cohérent** — les mêmes garanties ACID que PostgreSQL, à n'importe quelle échelle
- **Multi-région actif-actif** — les shards d'historique Temporal se distribuent entre régions sans réplication manuelle
- **Basculement automatique** — les défaillances de nœuds sont transparentes pour les services Temporal
- **Scalabilité horizontale** — scalez lectures et écritures sans logique de sharding dans l'application
- **Protocole filaire PostgreSQL** — le plugin `postgres12` de Temporal fonctionne directement

### Déployer Temporal sur CockroachDB

#### Étape 1 — Provisionnement des bases et de l'utilisateur

```sql
CREATE DATABASE temporal;
CREATE DATABASE temporal_visibility;
CREATE USER temporal WITH PASSWORD 'temporal';
GRANT ALL ON DATABASE temporal TO temporal;
GRANT ALL ON DATABASE temporal_visibility TO temporal;
```

#### Étape 2 — Initialisation du schéma de persistance

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

#### Étape 3 — Correction du schéma de visibilité pour CockroachDB

> **C'est le correctif critique.** Le schéma de visibilité avancée de Temporal contient `CREATE EXTENSION IF NOT EXISTS btree_gin` — une extension exclusive à PostgreSQL qui permet d'utiliser des opérateurs B-tree avec des index GIN. CockroachDB ne supporte pas cette extension, et la migration de schéma **échoue** à cette ligne.

La cause racine est cette migration dans `schema/postgresql/v12/visibility/versioned/v1.1/manifest.json` :

```sql
-- PostgreSQL uniquement — ÉCHOUE sur CockroachDB
CREATE EXTENSION IF NOT EXISTS btree_gin;
CREATE INDEX custom_search_attributes_idx
  ON executions_visibility
  USING gin(search_attributes jsonb_path_ops);
```

**Le correctif** : contourner l'outil de migration standard pour la base de visibilité et appliquer directement un schéma compatible CockroachDB. CockroachDB supporte nativement les index inversés sur les colonnes JSONB sans aucune extension :

```sql
-- Schéma de visibilité compatible CockroachDB
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

-- Index B-tree standard — fonctionnent identiquement sur CockroachDB
CREATE INDEX by_type_start_time
  ON executions_visibility (namespace_id, workflow_type_name, start_time DESC, run_id);
CREATE INDEX by_workflow_id_start_time
  ON executions_visibility (namespace_id, workflow_id, start_time DESC, run_id);
CREATE INDEX by_status_start_time
  ON executions_visibility (namespace_id, status, start_time DESC, run_id);
CREATE INDEX by_close_time
  ON executions_visibility (namespace_id, status, close_time DESC, run_id)
  WHERE close_time IS NOT NULL;

-- Index inversé natif de CockroachDB remplace l'index GIN btree_gin
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

#### Étape 4 — Configuration du serveur Temporal

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

---

## DBOS

[DBOS](https://dbos.dev/) adopte une approche fondamentalement différente : plutôt que de déployer un cluster d'orchestration dédié, il intègre l'exécution durable **directement dans votre application** via la base de données que vous utilisez déjà. Votre base de données n'est pas seulement un store de données — c'est le moteur d'exécution.

### Concepts clés

| Concept | Définition |
|---|---|
| **`@DBOS.workflow()`** | Décorateur rendant une fonction Python durable — l'état est persisté en base avant chaque étape |
| **`@DBOS.step()`** | Unité de travail dans un workflow ; s'exécute au moins une fois mais jamais après complétion |
| **Workflow ID** | La clé d'idempotence ; lancer deux fois le même ID de workflow est sans danger |
| **`DBOS.set_event()`** | Publie une valeur nommée depuis l'intérieur d'un workflow pour les consommateurs externes |
| **`DBOS.get_event()`** | Interroge un workflow pour une valeur d'événement nommée avec timeout optionnel |
| **Base système** | La base compatible PostgreSQL où DBOS stocke l'état des workflows, les completions d'étapes et les événements |

### Architecture

<img src="/assets/img/dbos-schema.png" alt="Schéma de la base système DBOS" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**Schéma de la base système DBOS — l'état des workflows vit dans votre base, pas dans un service séparé**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

DBOS gère trois catégories de tables dans la base système :

- **Table de statut des workflows** — une ligne par exécution, suivant l'ID, le statut et les entrées de la fonction
- **Table des sorties d'opérations** — une ligne par étape complétée, stockant la valeur de retour sérialisée pour la reprise
- **Table d'événements** — paires clé-valeur nommées publiées dans les workflows et consommées via `get_event`

### DBOS sur CockroachDB

DBOS utilisant le protocole filaire PostgreSQL, il se connecte directement à CockroachDB. Deux modifications de configuration sont cependant nécessaires :

**1. Désactiver `LISTEN/NOTIFY`**

`LISTEN/NOTIFY` de PostgreSQL est utilisé par DBOS pour réveiller les workflows en attente sans polling. CockroachDB n'implémente pas ce mécanisme et il doit être désactivé explicitement :

```python
from dbos import DBOS, DBOSConfig
from sqlalchemy import create_engine
import os

database_url = os.environ["DBOS_COCKROACHDB_URL"]
engine = create_engine(database_url)

config: DBOSConfig = {
    "name": "my-agent-app",
    "system_database_url": database_url,
    # Fournir un engine SQLAlchemy pré-construit pour le driver CockroachDB
    "system_database_engine": engine,
    # CockroachDB ne supporte pas LISTEN/NOTIFY — utiliser le polling
    "use_listen_notify": False,
}
DBOS(config=config)
```

**2. Définir l'URL de la base système**

Dans `dbos-config.yaml`, pointer la base système vers CockroachDB :

```yaml
name: my-agent-app
language: python
runtimeConfig:
  start:
    - python3 app/main.py
system_database_url: ${DBOS_COCKROACHDB_URL}
```

```bash
export DBOS_COCKROACHDB_URL="postgresql://dbos_user:password@<crdb-host>:26257/dbos_system?sslmode=verify-full&sslrootcert=/certs/ca.crt"
```

### Un workflow agentique DBOS complet sur CockroachDB

```python
import os, time, uvicorn
from dbos import DBOS, DBOSConfig, SetWorkflowID
from fastapi import FastAPI
from sqlalchemy import create_engine

app = FastAPI()
database_url = os.environ["DBOS_COCKROACHDB_URL"]
engine = create_engine(database_url)

config: DBOSConfig = {
    "name": "agent-workflow",
    "system_database_url": database_url,
    "system_database_engine": engine,
    "use_listen_notify": False,
}
DBOS(config=config)

STEPS_EVENT = "steps_event"

@DBOS.step()
def retrieve_context(task: str) -> str:
    time.sleep(3)
    DBOS.logger.info(f"Contexte récupéré pour : {task}")
    return f"context_for_{task}"

@DBOS.step()
def call_agent(context: str) -> str:
    time.sleep(3)
    DBOS.logger.info("Invocation de l'agent terminée")
    return f"reponse_agent_{context}"

@DBOS.step()
def persist_result(response: str) -> None:
    time.sleep(3)
    DBOS.logger.info(f"Résultat persisté : {response}")

@DBOS.workflow()
def agent_workflow(task: str) -> None:
    context = retrieve_context(task)
    DBOS.set_event(STEPS_EVENT, 1)
    response = call_agent(context)
    DBOS.set_event(STEPS_EVENT, 2)
    persist_result(response)
    DBOS.set_event(STEPS_EVENT, 3)

@app.post("/agent/{task_id}")
def start_agent(task_id: str, task: str) -> dict:
    with SetWorkflowID(task_id):
        DBOS.start_workflow(agent_workflow, task)
    return {"workflow_id": task_id, "status": "démarré"}

@app.get("/agent/{task_id}/progression")
def get_progress(task_id: str) -> dict:
    try:
        step = DBOS.get_event(task_id, STEPS_EVENT, timeout_seconds=0)
    except KeyError:
        return {"etapes_completees": 0}
    return {"etapes_completees": step if step is not None else 0}

if __name__ == "__main__":
    DBOS.launch()
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## Temporal vs DBOS — Quand utiliser lequel ?

| Dimension | Temporal | DBOS |
|---|---|---|
| **Modèle de déploiement** | Cluster dédié (auto-hébergé ou Temporal Cloud) | Bibliothèque intégrée à votre application |
| **Stockage** | Stores de persistance et visibilité séparés | Tables système dans votre base existante |
| **Compatibilité CockroachDB** | Excellente — mais nécessite le correctif visibilité `btree_gin` | Native — CRDB est une cible de premier ordre |
| **Complexité opérationnelle** | Élevée — cluster Temporal à gérer | Faible — pas de service séparé |
| **Cible de montée en charge** | SaaS multi-tenant, millions de workflows | Application unique ou services étroitement intégrés |
| **Support de langage** | Go, Java, TypeScript, Python | Python, TypeScript |
| **Idéal pour l'IA agentique** | Coordination de nombreux agents indépendants entre services | Intégration d'exécution durable dans une app FastAPI / LLM |

### CockroachDB comme socle commun

Que vous choisissiez Temporal ou DBOS, CockroachDB apporte les mêmes trois propriétés à votre persistance de workflows :

- **Isolation sérialisable** — pas de mises à jour perdues ni de lectures fantômes même sous exécution de workflow concurrente
- **Réplication multi-région** — l'état des workflows est durable à travers les défaillances de data center sans basculement manuel
- **Scalabilité horizontale** — ajoutez des nœuds pour gérer plus de workflows concurrents sans re-sharding ni temps d'arrêt

Pour Temporal, CockroachDB remplace PostgreSQL directement avec un correctif de schéma. Pour DBOS, deux lignes de configuration suffisent et vous obtenez une base système distribuée globalement que PostgreSQL ne peut pas égaler à l'échelle.

---

## Prochaines étapes

Temporal et DBOS abaissent la barrière à la construction de systèmes d'IA agentique résilients. Les associer à CockroachDB élimine le dernier point de défaillance unique de votre infrastructure de workflows.

- Pour Temporal : clonez l'exemple [Temporal Docker Compose](https://github.com/temporalio/docker-compose) et remplacez l'image PostgreSQL par CockroachDB en appliquant le correctif de schéma de visibilité ci-dessus.
- Pour DBOS : définissez `DBOS_COCKROACHDB_URL`, ajoutez les deux lignes de configuration, et votre premier workflow d'agent durable est opérationnel en quelques minutes.

## Voir aussi

- [Documentation Temporal](https://docs.temporal.io/)
- [Documentation DBOS](https://docs.dbos.dev/)
- [Tutoriel workflow Python DBOS](https://docs.dbos.dev/python/tutorials/workflow-tutorial)
- [CockroachDB Cloud](https://cockroachlabs.cloud/)
- [SQL distribué CockroachDB](https://www.cockroachlabs.com/blog/what-is-distributed-sql/)
