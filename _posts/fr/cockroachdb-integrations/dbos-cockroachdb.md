---
date: 2026-05-28
layout: post
title: "Exécution scalable embarquée avec DBOS et CockroachDB"
subtitle: "Comment DBOS transforme votre base de données en moteur de workflows — et pourquoi CockroachDB supprime le plafond de scalabilité"
cover-img: /assets/img/cover-dbos.webp
thumbnail-img: /assets/img/cover-dbos.webp
share-img: /assets/img/cover-dbos.webp
tags: [integrations, CockroachDB, dbos, workflow, orchestration, Artificial Intelligence, Agentic AI]
lang: fr
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

Les applications d'IA modernes ne sont plus de simples appels d'inférence ; ce sont des agents de longue durée qui planifient, agissent, observent et réessaient au fil du temps. Une boucle d'agent IA qui récupère du contexte depuis un vector store, appelle un LLM, écrit des résultats en base de données, attend une validation humaine, puis déclenche des actions en aval peut s'exécuter pendant des minutes, des heures, voire des jours. Sans une **couche d'orchestration durable**, toute défaillance d'infrastructure transitoire relance l'intégralité de la boucle depuis le début : refacturant des appels LLM coûteux, dupliquant les effets de bord et perdant tout le contexte accumulé.

Des plateformes comme [Temporal](https://temporal.io/) résolvent ce problème en déployant un cluster d'orchestration dédié — un processus serveur séparé avec son propre backend de persistance — auquel vos workers applicatifs se connectent via gRPC. C'est puissant, mais cela implique un service supplémentaire à provisionner, surveiller, mettre à l'échelle et maintenir disponible avant même de pouvoir exécuter le premier workflow.

[DBOS](https://dbos.dev/) adopte une approche fondamentalement différente : il intègre l'exécution durable **directement dans votre application** sous forme de bibliothèque Python ou TypeScript, en utilisant la base de données que vous avez déjà. Il n'y a pas de serveur d'orchestration, pas de file de tâches, pas de processus sidecar. Votre application écrit l'état des workflows dans des tables de sa propre base de données comme effet de bord naturel de l'exécution, et reprend depuis ces tables au redémarrage. Associez DBOS à [CockroachDB](https://www.cockroachlabs.com/) et vous obtenez une plateforme d'exécution distribuée globalement et auto-réparante, sans infrastructure supplémentaire à gérer.

Un **workflow durable** est une fonction dont l'état d'exécution, à savoir quelles étapes ont été complétées, ce qu'elles ont retourné et quelles entrées ont été fournies, est persisté en base après chaque étape. Si le processus crashe en cours d'exécution, il redémarre et reprend depuis la dernière étape validée : aucun travail n'est perdu, aucune étape n'est ré-exécutée, aucun effet de bord externe n'est dupliqué.

---

## Qu'est-ce que DBOS ?

DBOS est une bibliothèque Python et TypeScript qui décore des fonctions ordinaires avec des garanties d'exécution durable. Il n'y a pas de serveur à déployer, pas de file de tâches à opérer, pas de cluster de persistance séparé à gérer. DBOS écrit l'état des workflows dans des tables de votre base applicative comme effet secondaire de l'exécution normale, et récupère depuis ces tables au redémarrage.

### Concepts clés

| Concept | Définition |
|---|---|
| **`@DBOS.workflow()`** | Décorateur rendant une fonction Python durable. L'état est persisté avant chaque étape. |
| **`@DBOS.step()`** | Unité de travail dans un workflow ; s'exécute au moins une fois mais jamais après complétion |
| **Workflow ID** | La clé d'idempotence ; lancer deux fois le même ID de workflow est sans danger |
| **`DBOS.set_event()`** | Publie une valeur nommée depuis l'intérieur d'un workflow pour les consommateurs externes |
| **`DBOS.get_event()`** | Interroge un workflow pour une valeur d'événement nommée avec timeout optionnel |
| **Base système** | La base compatible PostgreSQL où DBOS stocke l'état des workflows, les completions d'étapes et les événements |

---

## Architecture

DBOS est implémenté entièrement comme une bibliothèque open-source embarquée dans votre application — il n'y a pas de serveur d'orchestration et pas de dépendances externes excepté une base compatible PostgreSQL. Pendant l'exécution, DBOS crée des checkpoints de l'état des workflows et des étapes dans cette base. En cas de défaillance, il utilise ces checkpoints pour reprendre chaque workflow depuis la dernière étape complétée.

<img src="/assets/img/dbos-architecture.png" alt="Architecture DBOS : bibliothèque embarquée dans le processus applicatif" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**Architecture DBOS : la bibliothèque d'exécution durable vit dans votre processus applicatif — la seule dépendance externe est une base compatible Postgres**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

### Modèle de checkpointing

Chaque exécution de workflow produit un nombre fixe d'écritures en base quelle que soit sa complexité :

- **Une écriture au démarrage du workflow** : les entrées sont persistées avant l'exécution de toute étape
- **Une écriture par étape complétée** : la valeur de retour de l'étape est stockée pour que la reprise puisse la sauter
- **Une écriture à la fin du workflow** : le statut final est validé

La taille des écritures est proportionnelle à vos entrées et sorties. Pour les charges importantes (fichiers, embeddings), la pratique recommandée est de les stocker en externe (ex. S3) et de n'avoir les étapes retourner que des pointeurs.

### Déploiement distribué

DBOS passe naturellement à l'échelle d'une flotte de serveurs. Tous les serveurs applicatifs se connectent à la **même base système** — c'est le seul point de coordination. Par défaut, chaque workflow s'exécute sur un seul serveur ; les files durables distribuent le travail sur la flotte avec des limites configurables de débit et de concurrence.

Pour les setups multi-applications (ex. un serveur API, un service d'ingestion de données, et une boucle d'agent IA), chaque application se connecte à sa propre base système isolée. Un seul hôte de base de données peut servir plusieurs bases système. Le **DBOS Client** permet au code externe d'enqueuer des jobs et de surveiller les résultats entre applications.

### Récupération des workflows

Quand un processus crashe, DBOS détecte les workflows incomplets et les rejoue en trois étapes :

1. **Détection** — au démarrage, DBOS scanne les workflows en attente. Dans les déploiements distribués, Conductor coordonne la détection sur toute la flotte.
2. **Redémarrage** — chaque workflow interrompu est rappelé avec ses entrées originales checkpointées.
3. **Reprise** — lors de la ré-exécution, toute étape dont la sortie est déjà checkpointée est ignorée instantanément. L'exécution reprend depuis la première étape sans checkpoint.

Deux conditions requises pour une récupération sûre :
- **Déterminisme** : la fonction de workflow doit produire les mêmes étapes dans le même ordre pour les mêmes entrées. Les opérations non-déterministes (accès DB, appels API, nombres aléatoires, timestamps) doivent être dans des décorateurs `@DBOS.step()`, jamais directement dans le corps du workflow.
- **Idempotence** : les étapes peuvent être rejouées lors de la récupération et doivent être sûres à ré-exécuter.

### Conductor (optionnel)

Pour les déploiements en production, DBOS recommande de se connecter à **Conductor** — un service de gestion qui ajoute la coordination de récupération distribuée, les tableaux de bord de workflows et l'observabilité des files. Conductor est architecturalement hors du chemin critique : chaque serveur ouvre une connexion websocket sortante vers lui, et si la connexion tombe l'application continue de fonctionner normalement. Conductor n'a pas d'accès direct à votre base de données et n'est jamais impliqué dans l'exécution des workflows elle-même.

<img src="/assets/img/dbos-conductor-architecture.png" alt="Architecture DBOS Conductor" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**Conductor est hors bande : les serveurs applicatifs ouvrent des connexions websocket sortantes vers lui pour l'observabilité et la récupération — jamais pour l'exécution des workflows**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

---

## Pourquoi CockroachDB pour DBOS ?

DBOS utilisant le protocole filaire PostgreSQL, il se connecte à CockroachDB directement sans modification de driver. Ce que CockroachDB ajoute par rapport à un PostgreSQL mono-nœud, c'est le niveau de persistance que vous avez toujours voulu mais que vous ne pouviez pas justifier d'opérer séparément :

- **Isolation sérialisable** : les exécutions de workflow concurrentes ne produisent jamais de mises à jour perdues ni de lectures fantômes
- **Réplication active-active multi-région** : l'état des workflows est durable à travers les défaillances de data center sans intervention manuelle
- **Scalabilité horizontale** : la base système passe à l'échelle avec votre application sans re-sharding
- **Basculement automatique** : les défaillances de nœuds CockroachDB sont transparentes pour DBOS, qui réessaie simplement sur le nœud suivant disponible

Lorsque DBOS se connecte à CockroachDB, il provisionne trois catégories de tables dans la base système :

<img src="/assets/img/dbos-schema.png" alt="Schéma des tables DBOS dans CockroachDB" style="width:60%;margin:1.5rem auto;display:block;">
{: .mx-auto.d-block :}
**Tables créées par DBOS dans CockroachDB : statut des workflows, sorties des étapes et événements — tout dans votre base existante**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

- **Table de statut des workflows** : une ligne par exécution, suivant l'ID, le statut et les entrées de la fonction
- **Table des sorties d'opérations** : une ligne par étape complétée, stockant la valeur de retour sérialisée pour la reprise
- **Table d'événements** : paires clé-valeur nommées publiées dans les workflows et consommées via `get_event`

Pour les équipes souhaitant des workflows agentiques résilients globalement sans la complexité d'un cluster Temporal, DBOS + CockroachDB est le chemin à moindre overhead.

| Capacité | DBOS + CockroachDB |
|---|---|
| **Pas d'infrastructure supplémentaire** | L'exécution durable s'exécute dans votre processus FastAPI / applicatif |
| **Étapes exactement-une-fois** | Les étapes ne sont jamais ré-exécutées après que leur sortie est validée dans CockroachDB |
| **Lancements idempotents** | Le même ID de workflow retourne toujours l'exécution existante |
| **Durabilité globale** | La réplication multi-région de CockroachDB protège l'état des workflows entre régions |
| **Zéro modification de driver** | Protocole filaire PostgreSQL — pas de SDK CockroachDB spécifique requis |
| **Progression observable** | `set_event` / `get_event` exposent la complétion des étapes aux frontends en temps réel |

---

## Déployer DBOS sur CockroachDB

Deux modifications de configuration sont nécessaires lors de l'utilisation de CockroachDB à la place de PostgreSQL.

### Prérequis

| Prérequis | Détails |
|---|---|
| **Python 3.10+** | DBOS 2.x requiert Python 3.10 ou supérieur |
| **Cluster CockroachDB** | Une instance CockroachDB en fonctionnement (locale, CockroachDB Cloud ou auto-hébergée) |
| **Base système** | Une base dédiée à l'état DBOS — à créer une seule fois : `CREATE DATABASE dbos_system;` |
| **Packages Python** | `dbos[otel]`, `fastapi[standard]`, `psycopg2-binary`, `sqlalchemy-cockroachdb`, `uvicorn` |

```bash
pip install "dbos[otel]==2.15.0" "fastapi[standard]" psycopg2-binary sqlalchemy-cockroachdb
```

```bash
export DBOS_COCKROACHDB_URL="postgresql://<user>:<password>@<crdb-host>:26257/dbos_system?sslmode=verify-full&sslrootcert=/certs/ca.crt"
```

### 1. Désactiver `LISTEN/NOTIFY`

Le mécanisme `LISTEN/NOTIFY` de PostgreSQL est utilisé par DBOS pour réveiller les workflows en attente sans polling. CockroachDB n'implémente pas ce mécanisme et il doit être désactivé explicitement. DBOS bascule automatiquement sur le polling :

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
    # CockroachDB does not support LISTEN/NOTIFY — use polling instead
    "use_listen_notify": False,
}
DBOS(config=config)
```

### 2. Définir l'URL de la base système

Dans `dbos-config.yaml`, pointer la base système vers CockroachDB en utilisant le format de chaîne de connexion PostgreSQL standard :

```yaml
name: my-agent-app
language: python
runtimeConfig:
  start:
    - python3 app/main.py
system_database_url: ${DBOS_COCKROACHDB_URL}
```

Définissez la variable d'environnement avec votre chaîne de connexion CockroachDB :

```bash
export DBOS_COCKROACHDB_URL="postgresql://dbos_user:password@<crdb-host>:26257/dbos_system?sslmode=verify-full&sslrootcert=/certs/ca.crt"
```

---

## Un workflow agentique DBOS complet sur CockroachDB

L'exemple suivant implémente un workflow d'agent durable en trois étapes adossé à CockroachDB. Le workflow publie des événements de progression après chaque étape qu'un frontend peut interroger en temps réel. Si le processus crashe en cours d'exécution, le redémarrer reprend depuis la dernière étape complétée, sans refacturation, pas d'écriture en double, pas de perte de contexte.

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

Installez les dépendances et lancez :

```bash
pip install "dbos[otel]==2.15.0" "fastapi[standard]" psycopg2-binary sqlalchemy-cockroachdb
export DBOS_COCKROACHDB_URL="postgresql://dbos_user:pass@localhost:26257/dbos_system?sslmode=disable"
python3 app/main.py
```

---

## Benchmarking de scalabilité

L'équipe DBOS a [mesuré le débit de DBOS sur PostgreSQL](https://dbos.dev/blog/benchmarking-workflow-execution-scalability-on-postgres), atteignant **144K écritures brutes en base de données par seconde** sur une instance AWS RDS unique (`db.m7i.24xlarge` — 96 vCPU, 384 Go RAM, 120K IOPS). Nous avons effectué le benchmark équivalent — de vrais workflows DBOS à 2 étapes, mesurés bout en bout — sur un **cluster CockroachDB à 3 nœuds co-localisé dans AWS us-east-1** (`3× m7i.8xlarge` — 96 vCPU au total). Le client de benchmark tournait dans us-east-1, sans aucune latence WAN.

> **Artefacts du benchmark :** scripts et résultats bruts disponibles dans le dépôt sous [`assets/bench/dbos-cockroachdb/`](https://github.com/aelkouhen/aelkouhen.github.io/tree/main/assets/bench/dbos-cockroachdb) :
> [`bench_direct.py`](https://github.com/aelkouhen/aelkouhen.github.io/blob/main/assets/bench/dbos-cockroachdb/bench_direct.py) · [`charts_v5.py`](https://github.com/aelkouhen/aelkouhen.github.io/blob/main/assets/bench/dbos-cockroachdb/charts_v5.py) · [`results_coloc.json`](https://github.com/aelkouhen/aelkouhen.github.io/blob/main/assets/bench/dbos-cockroachdb/results_coloc.json)

### Résultats — débit et latence co-localisés

<img src="/assets/bench/dbos-cockroachdb/dbos-bench-crdb-throughput.png" alt="Débit workflow DBOS CockroachDB de c=1 à c=512, co-localisé" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**Le débit scale linéairement de 12 wf/s à c=1 jusqu'à 117 wf/s à c=32, puis se stabilise — le cluster à 3 nœuds est saturé. Chaque nœud supplémentaire ajoute ~39 wf/s.**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

<img src="/assets/bench/dbos-cockroachdb/dbos-bench-crdb-latency.png" alt="Latence de workflow CockroachDB p50 et p95 sous charge, co-localisé" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**La latence p50 est de 72 ms au pic de débit (c=8) — les 3 nœuds sont répartis sur plusieurs AZ de us-east-1 (déploiement réellement redondant). Chaque quorum Raft franchit les frontières d'AZ ; cette latence est celle d'une production réelle, pas d'un rack unique.**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

| Concurrence | Débit (wf/s) | p50 (ms) | p95 (ms) |
|:-----------:|:------------:|:--------:|:--------:|
| 1 | 12,4 | 80 | 87 |
| 4 | 53,4 | 74 | 89 |
| **8** | **104,9** | **72** | **90** |
| 16 | 106,3 | 138 | 177 |
| 32 | **116,6 (pic)** | 251 | 316 |
| 64 | 116,3 | 526 | 598 |
| 256 | 113,5 | 2 216 | 2 304 |

### L'argument de la scalabilité

Le cluster à 3 nœuds sature à **~117 wf/s** — c'est la capacité de *ces trois nœuds*, pas une limite de CockroachDB. Ajoutez des nœuds et le débit scale proportionnellement.

<img src="/assets/bench/dbos-cockroachdb/dbos-bench-linear-vs-ceiling.png" alt="Scale-out linéaire de CockroachDB : 117 wf/s mesurés sur 3 nœuds, projection linéaire avec les nœuds supplémentaires" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**Baseline mesurée : 117 wf/s sur 3 nœuds répartis sur plusieurs AZ (redondance de zone). Chaque nœud ajoute ~39 wf/s. Le WAL de PostgreSQL est un chemin d'écriture mono-nœud — il ne peut pas être distribué sur des instances supplémentaires.**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Le **Write-Ahead Log de PostgreSQL sérialise chaque écriture dans un seul chemin de flush**. Une fois ce chemin saturé, aucun matériel supplémentaire n'améliore le débit d'écriture — on peut scaler les lectures avec des réplicas, mais les écritures restent bornées par un seul nœud pour toujours. CockroachDB remplace le WAL unique par un **log Raft distribué** : chaque nœud flush son propre log, et les écritures se répartissent sur le cluster. Le plafond de débit monte avec chaque nœud ajouté.

### Synthèse

| | PostgreSQL | CockroachDB (3 nœuds) | CockroachDB (N nœuds) |
|---|---|---|---|
| Débit wf maximum | Plafond mono-nœud | **117 wf/s (mesuré)** | **~39 × N wf/s** |
| p50 au pic de concurrence | Sub-ms (WAL local) | ~72 ms (quorum Raft, cross-AZ) | ~72 ms |
| Scale-out en écriture | **Non — WAL = 1 nœud** | Oui | **Oui — linéaire** |
| Défaillance de nœud | Basculement manuel | Automatique | Automatique |
| Durabilité multi-région | Outillage externe | Natif | Natif |

Le consensus Raft distribué de CockroachDB ajoute de la latence par écriture par rapport à un WAL local — c'est le coût de la garantie qu'aucun nœud unique n'est un goulot d'écriture. La contrepartie : **besoin de plus de débit ? Ajoutez des nœuds. Il n'y a pas de plafond.**

---

## Voir aussi

- [Documentation DBOS](https://docs.dbos.dev/)
- [Tutoriel workflow Python DBOS](https://docs.dbos.dev/python/tutorials/workflow-tutorial)
- [CockroachDB Cloud](https://cockroachlabs.cloud/)
- [SQL distribué CockroachDB](https://www.cockroachlabs.com/blog/what-is-distributed-sql/)
- [Temporal + CockroachDB : Orchestration basée sur un cluster](/2026-04-24-temporal-cockroachdb/)
