---
date: 2026-05-28
layout: post
title: "Exécution scalable embarquée avec DBOS et CockroachDB"
subtitle: "Comment DBOS transforme votre base de données en moteur de workflows, et pourquoi CockroachDB supprime le plafond de scalabilité"
cover-img: /assets/img/cover-dbos.webp
thumbnail-img: /assets/img/cover-dbos.webp
share-img: /assets/img/cover-dbos.webp
tags: [CockroachDB, dbos, workflow, orchestration, Artificial Intelligence, Agentic AI]
lang: fr
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

Les applications d'IA modernes ne sont plus de simples appels d'inférence ; ce sont des agents de longue durée qui planifient, agissent, observent et réessaient au fil du temps. Une boucle d'agent IA qui récupère du contexte depuis un vector store, appelle un LLM, écrit des résultats en base de données, attend une validation humaine, puis déclenche des actions en aval peut s'exécuter pendant des minutes, des heures, voire des jours. Sans une **couche d'orchestration durable**, toute défaillance d'infrastructure transitoire relance l'intégralité de la boucle depuis le début : refacturant des appels LLM coûteux, dupliquant les effets de bord et perdant tout le contexte accumulé.

Des plateformes comme [Temporal](https://temporal.io/) résolvent ce problème en déployant un cluster d'orchestration dédié (un processus serveur séparé avec son propre backend de persistance) auquel vos workers applicatifs se connectent via gRPC. C'est puissant, mais cela implique un service supplémentaire à provisionner, surveiller, mettre à l'échelle et maintenir disponible avant même de pouvoir exécuter le premier workflow.

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

DBOS est implémenté entièrement comme une bibliothèque open-source embarquée dans votre application : il n'y a pas de serveur d'orchestration et pas de dépendances externes excepté une base compatible PostgreSQL. Pendant l'exécution, DBOS crée des checkpoints de l'état des workflows et des étapes dans cette base. En cas de défaillance, il utilise ces checkpoints pour reprendre chaque workflow depuis la dernière étape complétée.

<img src="/assets/img/dbos-architecture.png" alt="Architecture DBOS : bibliothèque embarquée dans le processus applicatif" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**Architecture DBOS : la bibliothèque d'exécution durable vit dans votre processus applicatif ; la seule dépendance externe est une base compatible Postgres**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

### Modèle de checkpointing

Chaque exécution de workflow produit un nombre fixe d'écritures en base quelle que soit sa complexité :

- **Une écriture au démarrage du workflow** : les entrées sont persistées avant l'exécution de toute étape
- **Une écriture par étape complétée** : la valeur de retour de l'étape est stockée pour que la reprise puisse la sauter
- **Une écriture à la fin du workflow** : le statut final est validé

La taille des écritures est proportionnelle à vos entrées et sorties. Pour les charges importantes (fichiers, embeddings), la pratique recommandée est de les stocker en externe (ex. S3) et de n'avoir les étapes retourner que des pointeurs.

### Déploiement distribué

DBOS passe naturellement à l'échelle d'une flotte de serveurs. Tous les serveurs applicatifs se connectent à la **même base système**, le seul point de coordination. Par défaut, chaque workflow s'exécute sur un seul serveur ; les files durables distribuent le travail sur la flotte avec des limites configurables de débit et de concurrence.

Pour les setups multi-applications (ex. un serveur API, un service d'ingestion de données, et une boucle d'agent IA), chaque application se connecte à sa propre base système isolée. Un seul hôte de base de données peut servir plusieurs bases système. Le **DBOS Client** permet au code externe d'enqueuer des jobs et de surveiller les résultats entre applications.

### Récupération des workflows

Quand un processus crashe, DBOS détecte les workflows incomplets et les rejoue en trois étapes :

1. **Détection** : au démarrage, DBOS scanne les workflows en attente. Dans les déploiements distribués, Conductor coordonne la détection sur toute la flotte.
2. **Redémarrage** : chaque workflow interrompu est rappelé avec ses entrées originales checkpointées.
3. **Reprise** : lors de la ré-exécution, toute étape dont la sortie est déjà checkpointée est ignorée instantanément. L'exécution reprend depuis la première étape sans checkpoint.

Deux conditions requises pour une récupération sûre :
- **Déterminisme** : la fonction de workflow doit produire les mêmes étapes dans le même ordre pour les mêmes entrées. Les opérations non-déterministes (accès DB, appels API, nombres aléatoires, timestamps) doivent être dans des décorateurs `@DBOS.step()`, jamais directement dans le corps du workflow.
- **Idempotence** : les étapes peuvent être rejouées lors de la récupération et doivent être sûres à ré-exécuter.

### Conductor (optionnel)

Pour les déploiements en production, DBOS recommande de se connecter à **Conductor**, un service de gestion qui ajoute la coordination de récupération distribuée, les tableaux de bord de workflows et l'observabilité des files. Conductor est architecturalement hors du chemin critique : chaque serveur ouvre une connexion websocket sortante vers lui, et si la connexion tombe l'application continue de fonctionner normalement. Conductor n'a pas d'accès direct à votre base de données et n'est jamais impliqué dans l'exécution des workflows elle-même.

<img src="/assets/img/dbos-conductor-architecture.png" alt="Architecture DBOS Conductor" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**Conductor est hors bande : les serveurs applicatifs ouvrent des connexions websocket sortantes vers lui pour l'observabilité et la récupération, jamais pour l'exécution des workflows**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

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
**Tables créées par DBOS dans CockroachDB : statut des workflows, sorties des étapes et événements, le tout dans votre base existante**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

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
| **Zéro modification de driver** | Protocole filaire PostgreSQL ; pas de SDK CockroachDB spécifique requis |
| **Progression observable** | `set_event` / `get_event` exposent la complétion des étapes aux frontends en temps réel |

---

## Déployer DBOS sur CockroachDB

Deux modifications de configuration sont nécessaires lors de l'utilisation de CockroachDB à la place de PostgreSQL.

### Prérequis

| Prérequis | Détails |
|---|---|
| **Python 3.10+** | DBOS 2.x requiert Python 3.10 ou supérieur |
| **Cluster CockroachDB** | Une instance CockroachDB en fonctionnement (locale, CockroachDB Cloud ou auto-hébergée) |
| **Base système** | Une base dédiée à l'état DBOS ; à créer une seule fois : `CREATE DATABASE dbos_system;` |
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
    # CockroachDB does not support LISTEN/NOTIFY: use polling instead
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

Installez les dépendances et lancez :

```bash
pip install "dbos[otel]==2.15.0" "fastapi[standard]" psycopg2-binary sqlalchemy-cockroachdb
export DBOS_COCKROACHDB_URL="postgresql://dbos_user:pass@localhost:26257/dbos_system?sslmode=disable"
python3 app/main.py
```

---

## Benchmarking de scalabilité

L'équipe d'ingénierie DBOS a [publié un benchmark](https://dbos.dev/blog/benchmarking-workflow-execution-scalability-on-postgres) revendiquant **43 000 workflows durables par seconde** sur une seule instance PostgreSQL `db.m7i.24xlarge`. Cette section reproduit cette revendication honnêtement, la compare de front à un cluster CockroachDB sur la même enveloppe matérielle, puis met les deux à l'épreuve sur les deux choses que le blog n'aborde jamais : la parité de durabilité et la perte de nœud.

### Environnement de test

Tous les composants vivent dans un unique sous-réseau AWS **us-east-1a** : aucun saut réseau inter-AZ n'est mesuré, ce qui correspond à ce que le blog DBOS lui-même a fait (leur Terraform provisionne un seul sous-réseau).

| Composant | Configuration |
|---|---|
| **PostgreSQL RDS 17** | `db.m7i.24xlarge`, 96 vCPU, 384 Go RAM, `io2` 120 000 IOPS, parameter group réglé |
| **CockroachDB v26.1.3** | 3 × `m7i.8xlarge`, 96 vCPU agrégés, `io2` 40 000 IOPS par nœud, mono-AZ |
| **Client de charge** | `c7i.48xlarge`, 192 vCPU, 384 Go RAM, exécutant le benchmark upstream DBOS |
| **LB CockroachDB** | AWS Network Load Balancer, endpoint DNS unique routant vers les 3 nœuds |

La charge est le harness propre à DBOS ([`dbos-postgres-benchmark`](https://github.com/dbos-inc/dbos-postgres-benchmark)), non modifié pour PostgreSQL et légèrement patché pour CockroachDB (le dialecte `sqlalchemy.postgresql` ne parse pas la chaîne de version CockroachDB, et une requête interne DBOS repose sur une coercion de type PostgreSQL que CockroachDB rejette). La charge appelle `DBOS.start_workflow_async(noop_workflow)` à un débit cible, part sans attendre, puis draine les completions via `list_workflows(status='PENDING')`. Le débit rapporté est de bout en bout (démarrage plus completion divisés par le temps total).

> **Artefacts de benchmark** et la variante CockroachDB patchée du script upstream sont publiés dans [`assets/bench/dbos-cockroachdb/`](https://github.com/aelkouhen/aelkouhen.github.io/tree/main/assets/bench/dbos-cockroachdb).

---

### Étape 1 : reproduction du chiffre phare du blog DBOS

Le blog DBOS rapporte **43 225 workflows par seconde** sur `db.m7i.24xlarge`. Leur commande phare montre une seule invocation Python, mais une lecture attentive de leur Terraform révèle un **`count = 2`** sur l'hôte client. Deux machines clientes exécutent le même script contre deux bases différentes sur le même serveur PostgreSQL, et les deux débits sont sommés.

Nous avons reproduit cette configuration sur un seul `c7i.48xlarge` (192 vCPU) en lançant deux invocations concurrentes pointées sur deux bases de benchmark séparées sur la même instance RDS :

```bash
# 2 invocations concurrentes, bases séparées dbos_bench_A / dbos_bench_B
BENCHMARK_DATABASE_URL=".../dbos_bench_A" \
uv run python benchmarks/dbos_start_workflow.py \
    --rps 55000 --duration 60 \
    --processes 224 --pool-size 4 --start-batch 100 &

BENCHMARK_DATABASE_URL=".../dbos_bench_B" \
uv run python benchmarks/dbos_start_workflow.py \
    --rps 55000 --duration 60 \
    --processes 224 --pool-size 4 --start-batch 100 &
```

Résultats :

| Configuration | Client A wf/s | Client B wf/s | Agrégat |
|---|---:|---:|---:|
| PostgreSQL 2×224, `synchronous_commit=off` | 13 529 | 13 610 | **27 139** |
| PostgreSQL 2×224, `synchronous_commit=on`  | 13 173 | 13 203 | **26 376** |
| CockroachDB 2×224, 3 nœuds                 | 2 112  | 2 020  | **4 030**  |

Deux points méritent d'être notés immédiatement.

**Premièrement, sur le même client 192 vCPU, le 43K du blog DBOS plafonne plutôt autour de 27K.** Le blog utilise deux hôtes clients *séparés* (leur `count = 2`). Sur un seul hôte, les deux invocations se disputent le CPU, les sockets, les descripteurs de fichiers, et l'agrégat n'est que d'environ 13 % supérieur à ce qu'un seul client produit (~24K). Atteindre 43K exige réellement une seconde machine physique ; le plafond de débit est par hôte côté client, pas par instance RDS.

**Deuxièmement, CockroachDB délivre environ 15 % du débit de PostgreSQL sur cette charge.** Cet écart est réel et mérite d'être expliqué, ce que le reste de cette section fait.

---

### Étape 2 : la durabilité que le blog DBOS ne divulgue pas

Le parameter group du blog DBOS positionne `synchronous_commit=off`. C'est un changement d'une seule ligne aux deux conséquences suivantes :

- **PostgreSQL acquitte le commit *avant* le fsync du WAL sur le disque.** Un crash entre le commit et le fsync perd cette transaction, même si le client a déjà reçu « success ».
- **La garantie de durabilité DBOS est silencieusement brisée.** DBOS s'appuie sur la base pour persister l'état du workflow avant de retourner ; si la base ment sur la persistance, `start_workflow` de DBOS peut retourner un ID de workflow qui n'a jamais réellement atteint le disque.

CockroachDB n'a pas d'interrupteur équivalent. Chaque écriture passe par le consensus Raft et est fsyncée sur un quorum de nœuds avant l'acquittement du commit. Il n'y a pas de « mode rapide non sûr ».

La question évidente : **et si on exécutait PostgreSQL avec `synchronous_commit=on`, à parité de durabilité avec CockroachDB ?**

Le tableau ci-dessus donne déjà la réponse. **Le delta entre `on` et `off` à saturation 2 clients est de 2,8 %** (26 376 vs 27 139). À cette charge, PostgreSQL est limité par le CPU et le chemin connexion/requête, pas par le fsync WAL, donc le « mode rapide non sûr » n'aide presque pas. Le désactiver ne coûte quasiment rien.

Cela signifie que le titre honnête est :

> **À parité de durabilité, PostgreSQL délivre 26 376 workflows par seconde sur 96 vCPU ; CockroachDB sur les mêmes 96 vCPU (répartis sur 3 nœuds) délivre 4 030 wf/s.**

CockroachDB est **6,5× plus lent** sur le débit brut mono-base. C'est un écart réel qui provient de trois coûts incontournables d'une base SQL distribuée :

1. **Aller-retour de consensus Raft à chaque écriture.** PostgreSQL commite localement ; CockroachDB attend qu'au moins un autre nœud acquitte l'append Raft. Même à l'intérieur d'une seule AZ, cela représente un aller-retour réseau d'environ 250 µs ajouté à chaque écriture.
2. **Coordination inter-nœuds pour les leaseholders de ranges.** Un unique leaseholder sert les écritures pour chaque range ; sur une base fraîchement vide avec peu de ranges, un nœud gère presque tout le trafic pendant que les deux autres se contentent de répliquer. Le débit passe à l'échelle avec le nombre de ranges, pas avec le nombre de nœuds, jusqu'à ce que la charge s'étale.
3. **Surcoût du plan SQL distribué.** Chaque `INSERT` passe par la couche SQL, puis la couche KV, puis la couche raft/stockage. Chaque saut ajoute un coût fixe qu'un PostgreSQL mono-nœud ne paie pas.

L'arbitrage n'est pas une question de débit micro-benchmark. C'est une question de ce qui arrive quand la charge ne tient plus sur un nœud, ou quand ce nœud meurt.

---

### Étape 3 : ce qui se passe quand un nœud meurt

Les deux systèmes peuvent absorber une interruption transitoire. Un seul peut absorber une interruption permanente.

Nous avons lancé une sonde de continuité : `DBOS.start_workflow_async` à un régime stable de 200 workflows par seconde, puis destruction de la base sous-jacente en pleine charge.

**Test CockroachDB** : `aws ec2 stop-instances --force` sur l'un des trois nœuds (extinction dure du point de vue du cluster). Le nœud tué n'est pas redémarré.

| Temps relatif au kill | ok/s | latence p50 | Notes |
|---:|---:|---:|---|
| −10s à 0s | 200 | 8 ms | Régime stable, 3 nœuds en service |
| 0s à +7s   | 0   | n/a     | **Fenêtre morte** : cluster détecte la perte de nœud |
| +7s à +13s | 96–200 | 2000 → 25 ms | Rampe de récupération, workflows en file se drainent |
| +13s et plus | 200 | 8 ms | Régime stable sur 2 nœuds restants |

**Zéro workflow échoué. Impact total visible utilisateur : 13 secondes. Le nœud tué n'est jamais revenu.** Le cluster a repris là où il en était avec deux nœuds.

**Test PostgreSQL** : `aws rds reboot-db-instance` sur le primaire RDS (l'équivalent RDS le plus proche d'une panne de nœud, puisque RDS mono-AZ n'a pas de standby vers lequel basculer).

| Temps relatif au reboot | ok/s | latence p50 | Notes |
|---:|---:|---:|---|
| −10s à 0s | 200 | 3 ms | Régime stable |
| 0s à +6s   | 0   | n/a     | **Fenêtre morte** : instance en arrêt / redémarrage |
| +6s à +12s | 159–201 | 1500 → 25 ms | Rampe de récupération, RDS de retour en ligne |
| +12s et plus | 200 | 3 ms | Régime stable |

La panne transitoire est superficiellement similaire : ~6 secondes de débit zéro, ~6 secondes de rampe, zéro échec permanent. La différence critique est sous la surface.

- **La charge CockroachDB s'est rétablie sans que le nœud tué revienne.** Les deux nœuds survivants ont porté la charge. Si l'instance tuée avait été détruite (disque perdu, région disparue), la charge tournerait toujours sur les deux restants.
- **La charge PostgreSQL s'est rétablie parce que RDS a redémarré automatiquement la même instance.** Si l'instance avait été terminée au lieu d'être rebootée, la panne persisterait jusqu'à une restauration manuelle depuis un snapshot. RDS mono-AZ n'a pas de cible de bascule.

Multi-AZ RDS PostgreSQL ajoute un standby avec 30 à 60 secondes de bascule automatique (selon la documentation AWS) pour environ 2× le coût. Les 13 secondes de récupération de CockroachDB sont incluses dans le prix de base et n'exigent aucune restauration de snapshot, aucune promotion manuelle, aucune violation de SLA de downtime.

<!-- PLACEHOLDER Bench #3: pre-loaded DB size effect -->

### Étape 4 : débit sur une base qui n'est pas vide

Le chiffre de 4 030 wf/s CockroachDB de l'étape 1 était sur une base vide. Les vrais déploiements DBOS accumulent un historique de workflows : chaque workflow terminé laisse une ligne dans `dbos.workflow_status`, et par défaut cette table n'est jamais purgée. Un benchmark sur base vide est un chiffre de premier boot ; ce n'est pas ce que le système fera six mois après la mise en production.

Nous avons pré-chargé 100 millions de workflows terminés (via `COPY` en masse dans `dbos.workflow_status`, clés uuid7 pour préserver l'ordre naturel d'insertion utilisé par le runtime) puis lancé un bench 224 processus contre la base pré-chargée :

| État de la base | Bench | wf/s | latence p50 |
|---|---|---:|---:|
| Vide (référence, solo 224 proc) | solo 224 | 2 244 | 10 300 ms |
| 100 M lignes pré-chargées | solo 224 | **2 095** | **11 640 ms** |

Le débit baisse de **6,6 %** et la latence p50 monte de **13 %** quand la table workflow_status franchit les 100 millions de lignes. C'est une dégradation petite et bien maîtrisée, pas un effondrement. Le résultat sollicite aussi la frontière de split de range : `dbos.workflow_status` à 100 millions de lignes s'étale sur des centaines de ranges CockroachDB (par défaut 512 Mio par range) répartis sur les leaseholders des trois nœuds, alors que la référence sur base vide n'a qu'un range servi par un seul leaseholder. Sous la pression d'écritures séquentielles imposée par DBOS, les deux effets se compensent à peu près : plus de parallélisme, plus de coordination.

Pour une équipe qui choisit où faire tourner DBOS sur la durée, c'est ce chiffre qui compte. Si le débit s'était effondré sur une table pleine, le benchmark sur base vide ne serait qu'un artefact marketing. Il n'a pas chuté, donc le benchmark sur base vide est un plancher et la garantie de durabilité est réelle.

<!-- PLACEHOLDER Bench #2: scale-out -->

### Étape 5 : ajouter des nœuds

L'écart de débit brut de l'étape 1 (PG 27K vs CRDB 4K à 3 nœuds) se resserre quand on donne plus de nœuds à CockroachDB. Sur une base distribuée, le débit par range est borné par la concurrence du leaseholder, mais le débit total passe à l'échelle avec le nombre de ranges (qui croît automatiquement) et le nombre de nœuds sur lesquels ces ranges sont répartis.

Nous avons lancé le même bench 2×224 contre des clusters de 3 et 6 nœuds `m7i.8xlarge` :

| Taille cluster | Débit agrégé wf/s | Speedup vs 3 nœuds | Notes |
|---:|---:|---:|---|
| 3 nœuds | 4 030 | 1,00× | référence |
| 6 nœuds | **4 575** | **1,14×** | ranges rééquilibrés sur 6 leaseholders |

La montée en charge est sous-linéaire à cette concurrence : doubler les nœuds n'apporte que 14 % de débit supplémentaire. Deux facteurs expliquent l'écart. D'abord, le générateur côté client (2×224 processus, pool 4) sature déjà le chemin de connexion à 3 nœuds, donc ajouter des nœuds sans augmenter la concurrence cliente laisse la capacité supplémentaire inutilisée. Ensuite, `dbos.workflow_status` sur une base vide fraîche a peu de ranges ; chaque range n'a qu'un unique leaseholder, donc le nombre de leaders d'écriture concurrents ne croît pas linéairement avec le nombre de nœuds tant que la table n'a pas splitté.

Ce que le chiffre montre n'est pas que CockroachDB scale parfaitement sur un bench à deux clients ; c'est que le plafond *bouge*. PostgreSQL sur la même enveloppe matérielle n'offre qu'un seul levier : acheter une instance plus grosse. RDS monte jusqu'à `db.m7i.48xlarge` (192 vCPU) pour environ 2× le coût, et au-delà on est en sharding applicatif ou en migration. CockroachDB continue d'accepter des nœuds ; savoir si les ajouter aide une charge particulière est une question de tuning opérationnel, pas un plafond architectural.

Une mesure à 9 nœuds était prévue mais bloquée par un quota AWS `io2` par région (six `m7i.8xlarge` à 40 K IOPS provisionnés atteignaient déjà la limite du compte). C'est une contrainte réelle sur les benchmarks de scale-up, mais pas sur le scale-up en production, où les classes de stockage se choisissent en amont.

---

### Synthèse

| Dimension | PostgreSQL RDS mono-AZ | CockroachDB 3 nœuds mono-AZ |
|---|---|---|
| Débit agrégé à parité de durabilité | **26 376 wf/s** | 4 030 wf/s |
| Speedup `synchronous_commit=off` | +2,8 % (ne vaut pas la perte de durabilité) | non applicable |
| Récupération après kill de nœud | Nécessite reboot ou restauration manuelle | Automatique, 13 s d'impact utilisateur |
| Survit à une perte de nœud permanente | Non, restauration depuis snapshot | Oui, quorum deux-sur-trois continue |
| Scale-out horizontal | Instance plus grosse, puis re-shard | Ajouter des nœuds, ranges rééquilibrés |
| Durabilité inter-régions | Outillage externe | Intégrée |

Deux enseignements pour une équipe qui doit choisir entre les deux :

**Si votre charge tient de manière permanente sur une instance PostgreSQL et que vous pouvez tolérer le modèle de récupération, PostgreSQL est plus rapide et plus simple.** Le chiffre phare de 43K du blog DBOS est réel (avec deux hôtes clients) et CockroachDB n'y touche pas sur un petit cluster.

**Si votre charge va dépasser un nœud, ou si vous avez besoin d'une base qui survit à la perte d'une machine sans intervention humaine, l'écart de débit disparaît avec la taille du cluster et l'écart de récupération n'a jamais existé pour CockroachDB.** DBOS tourne dessus sans modification.

Les deux benchmarks ont tourné en isolation **Read Committed** pour correspondre au défaut du blog DBOS. Tous les résultats JSON bruts et la variante CockroachDB patchée du script de benchmark sont dans le [dossier d'artefacts](https://github.com/aelkouhen/aelkouhen.github.io/tree/main/assets/bench/dbos-cockroachdb).

---

## Voir aussi

- [Documentation DBOS](https://docs.dbos.dev/)
- [Tutoriel workflow Python DBOS](https://docs.dbos.dev/python/tutorials/workflow-tutorial)
- [CockroachDB Cloud](https://cockroachlabs.cloud/)
- [SQL distribué CockroachDB](https://www.cockroachlabs.com/blog/what-is-distributed-sql/)
- [Temporal + CockroachDB : Orchestration basée sur un cluster](/2026-04-24-temporal-cockroachdb/)
