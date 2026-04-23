---
date: 2026-04-24
layout: post
title: "Exécution durable embarquée avec DBOS et CockroachDB"
subtitle: "Comment DBOS transforme votre base de données existante en moteur de workflows  -  et pourquoi CockroachDB le rend distribué globalement"
tags: [integrations, CockroachDB, dbos, workflow, orchestration, durable-execution]
lang: fr
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

Les applications d'IA modernes ne sont plus de simples appels d'inférence  -  ce sont des agents de longue durée qui planifient, agissent, observent et réessaient au fil du temps. Une boucle d'agent IA qui récupère du contexte depuis un vector store, appelle un LLM, écrit des résultats en base de données, attend une validation humaine, puis déclenche des actions en aval peut s'exécuter pendant des minutes, des heures, voire des jours. Sans une **couche d'orchestration durable**, toute défaillance d'infrastructure transitoire relance l'intégralité de la boucle depuis le début : refacturant des appels LLM coûteux, dupliquant les effets de bord et perdant tout le contexte accumulé.

La plupart des plateformes d'orchestration de workflows résolvent ce problème en déployant un cluster dédié à côté de votre application. [DBOS](https://dbos.dev/) adopte une approche fondamentalement différente : il intègre l'exécution durable **directement dans votre application** via la base de données que vous utilisez déjà. Votre base de données n'est pas seulement un store de données  -  c'est le moteur d'exécution. Associez DBOS à [CockroachDB](https://www.cockroachlabs.com/) et vous obtenez une plateforme d'exécution distribuée globalement et auto-réparante, sans infrastructure supplémentaire à gérer.

Un **workflow durable** est une fonction dont l'état d'exécution  -  quelles étapes ont été complétées, ce qu'elles ont retourné, quelles entrées ont été fournies  -  est persisté en base après chaque étape. Si le processus crashe en cours d'exécution, il redémarre et reprend depuis la dernière étape validée : aucun travail n'est perdu, aucune étape n'est ré-exécutée, aucun effet de bord externe n'est dupliqué.

---

## Qu'est-ce que DBOS ?

DBOS est une bibliothèque Python et TypeScript qui décore des fonctions ordinaires avec des garanties d'exécution durable. Il n'y a pas de serveur à déployer, pas de file de tâches à opérer, pas de cluster de persistance séparé à gérer. DBOS écrit l'état des workflows dans des tables de votre base applicative comme effet secondaire de l'exécution normale, et récupère depuis ces tables au redémarrage.

### Concepts clés

| Concept | Définition |
|---|---|
| **`@DBOS.workflow()`** | Décorateur rendant une fonction Python durable  -  l'état est persisté avant chaque étape |
| **`@DBOS.step()`** | Unité de travail dans un workflow ; s'exécute au moins une fois mais jamais après complétion |
| **Workflow ID** | La clé d'idempotence ; lancer deux fois le même ID de workflow est sans danger |
| **`DBOS.set_event()`** | Publie une valeur nommée depuis l'intérieur d'un workflow pour les consommateurs externes |
| **`DBOS.get_event()`** | Interroge un workflow pour une valeur d'événement nommée avec timeout optionnel |
| **Base système** | La base compatible PostgreSQL où DBOS stocke l'état des workflows, les completions d'étapes et les événements |

---

## Architecture

DBOS gère trois catégories de tables dans la base système :

<img src="/assets/img/dbos-schema.png" alt="Schéma de la base système DBOS" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**Schéma de la base système DBOS  -  l'état des workflows vit dans votre base, pas dans un service séparé**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

- **Table de statut des workflows**  -  une ligne par exécution, suivant l'ID, le statut et les entrées de la fonction
- **Table des sorties d'opérations**  -  une ligne par étape complétée, stockant la valeur de retour sérialisée pour la reprise
- **Table d'événements**  -  paires clé-valeur nommées publiées dans les workflows et consommées via `get_event`

Quand un processus crashe et redémarre, DBOS rejoue la fonction de workflow contre les sorties d'étapes sauvegardées. Toute étape dont le résultat est déjà en base est **ignorée instantanément**  -  seules les étapes incomplètes sont ré-exécutées. Le résultat est une sémantique d'exécution exactement-une-fois sans service d'orchestration dédié.

---

## Pourquoi CockroachDB pour DBOS ?

DBOS utilisant le protocole filaire PostgreSQL, il se connecte à CockroachDB directement sans modification de driver. Ce que CockroachDB ajoute par rapport à un PostgreSQL mono-nœud, c'est le niveau de persistance que vous avez toujours voulu mais que vous ne pouviez pas justifier d'opérer séparément :

- **Isolation sérialisable**  -  les exécutions de workflow concurrentes ne produisent jamais de mises à jour perdues ni de lectures fantômes
- **Réplication active-active multi-région**  -  l'état des workflows est durable à travers les défaillances de data center sans intervention manuelle
- **Scalabilité horizontale**  -  la base système passe à l'échelle avec votre application sans re-sharding
- **Basculement automatique**  -  les défaillances de nœuds CockroachDB sont transparentes pour DBOS, qui réessaie simplement sur le nœud suivant disponible

Pour les équipes souhaitant des workflows agentiques résilients globalement sans la complexité d'un cluster Temporal, DBOS + CockroachDB est le chemin à moindre overhead.

---

## Déployer DBOS sur CockroachDB

Deux modifications de configuration sont nécessaires lors de l'utilisation de CockroachDB à la place de PostgreSQL.

### 1. Désactiver `LISTEN/NOTIFY`

Le mécanisme `LISTEN/NOTIFY` de PostgreSQL est utilisé par DBOS pour réveiller les workflows en attente sans polling. CockroachDB n'implémente pas ce mécanisme et il doit être désactivé explicitement  -  DBOS bascule automatiquement sur le polling :

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
    # CockroachDB ne supporte pas LISTEN/NOTIFY  -  utiliser le polling
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

L'exemple suivant implémente un workflow d'agent durable en trois étapes adossé à CockroachDB. Le workflow publie des événements de progression après chaque étape qu'un frontend peut interroger en temps réel. Si le processus crashe en cours d'exécution, le redémarrer reprend depuis la dernière étape complétée  -  pas de refacturation, pas d'écriture en double, pas de perte de contexte.

```python
import os
import time
import uvicorn
from dbos import DBOS, DBOSConfig, SetWorkflowID
from fastapi import FastAPI
from sqlalchemy import create_engine

app = FastAPI()

# ── Connexion CockroachDB ───────────────────────────────────────────────────
database_url = os.environ["DBOS_COCKROACHDB_URL"]
engine = create_engine(database_url)

config: DBOSConfig = {
    "name": "agent-workflow",
    "system_database_url": database_url,
    "system_database_engine": engine,
    "use_listen_notify": False,   # Requis : CockroachDB n'a pas de LISTEN/NOTIFY
}
DBOS(config=config)

STEPS_EVENT = "steps_event"

# ── Étapes du workflow ──────────────────────────────────────────────────────

@DBOS.step()
def retrieve_context(task: str) -> str:
    """Étape 1  -  récupère le contexte pertinent depuis la base de connaissances."""
    time.sleep(3)
    DBOS.logger.info(f"Contexte récupéré pour : {task}")
    return f"context_for_{task}"

@DBOS.step()
def call_agent(context: str) -> str:
    """Étape 2  -  invoque le LLM/agent avec le contexte."""
    time.sleep(3)
    DBOS.logger.info("Invocation de l'agent terminée")
    return f"agent_response_given_{context}"

@DBOS.step()
def persist_result(response: str) -> None:
    """Étape 3  -  écrit la sortie de l'agent dans la base applicative."""
    time.sleep(3)
    DBOS.logger.info(f"Résultat persisté : {response}")

# ── Workflow durable ────────────────────────────────────────────────────────

@DBOS.workflow()
def agent_workflow(task: str) -> None:
    context = retrieve_context(task)
    DBOS.set_event(STEPS_EVENT, 1)

    response = call_agent(context)
    DBOS.set_event(STEPS_EVENT, 2)

    persist_result(response)
    DBOS.set_event(STEPS_EVENT, 3)

# ── Endpoints HTTP ──────────────────────────────────────────────────────────

@app.post("/agent/{task_id}")
def start_agent(task_id: str, task: str) -> dict:
    """Lance de manière idempotente un workflow d'agent durable."""
    with SetWorkflowID(task_id):
        DBOS.start_workflow(agent_workflow, task)
    return {"workflow_id": task_id, "status": "démarré"}

@app.get("/agent/{task_id}/progression")
def get_progress(task_id: str) -> dict:
    """Interroge la progression du workflow (0-3 étapes complétées)."""
    try:
        step = DBOS.get_event(task_id, STEPS_EVENT, timeout_seconds=0)
    except KeyError:
        return {"etapes_completees": 0}
    return {"etapes_completees": step if step is not None else 0}

if __name__ == "__main__":
    DBOS.launch()
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Installez les dépendances et lancez :

```bash
pip install "dbos[otel]==2.15.0" "fastapi[standard]"
export DBOS_COCKROACHDB_URL="postgresql://dbos_user:pass@localhost:26257/dbos_system?sslmode=disable"
python3 app/main.py
```

---

## Bénéfices clés

| Capacité | DBOS + CockroachDB |
|---|---|
| **Pas d'infrastructure supplémentaire** | L'exécution durable s'exécute dans votre processus FastAPI / applicatif |
| **Étapes exactement-une-fois** | Les étapes ne sont jamais ré-exécutées après que leur sortie est validée dans CockroachDB |
| **Lancements idempotents** | Le même ID de workflow retourne toujours l'exécution existante |
| **Durabilité globale** | La réplication multi-région de CockroachDB protège l'état des workflows entre régions |
| **Zéro modification de driver** | Protocole filaire PostgreSQL  -  pas de SDK CockroachDB spécifique requis |
| **Progression observable** | `set_event` / `get_event` exposent la complétion des étapes aux frontends en temps réel |

Les deux modifications de configuration  -  `use_listen_notify: False` et une URL de connexion CockroachDB  -  sont tout ce qui est nécessaire pour rendre la base système DBOS distribuée globalement et tolérante aux pannes.

---

## Voir aussi

- [Documentation DBOS](https://docs.dbos.dev/)
- [Tutoriel workflow Python DBOS](https://docs.dbos.dev/python/tutorials/workflow-tutorial)
- [CockroachDB Cloud](https://cockroachlabs.cloud/)
- [SQL distribué CockroachDB](https://www.cockroachlabs.com/blog/what-is-distributed-sql/)
- [Temporal + CockroachDB  -  Orchestration basée sur un cluster](/2026-04-23-temporal-cockroachdb/)
