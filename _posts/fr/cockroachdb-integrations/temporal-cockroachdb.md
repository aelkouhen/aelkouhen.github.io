---
date: 2026-04-23
layout: post
title: "Integrate CockroachDB with Temporal"
subtitle: "A Step-By-Step Guide to Run Durable Workflow Orchestration with Temporal and CockroachDB"
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

Le schéma PostgreSQL standard introduit plusieurs incompatibilités avec CockroachDB dès la migration `v1.2` (`advanced_visibility.sql`). Contourner `temporal-sql-tool` pour la base de visibilité et appliquer directement un schéma compatible CockroachDB résout l'ensemble de ces problèmes (voir l'étape 3 ci-dessous).

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
| **Visibility Store (CockroachDB)** | Index d'exécution interrogeable ; `CREATE INVERTED INDEX` remplace les constructions GIN spécifiques à PostgreSQL |

---

## Pourquoi CockroachDB pour Temporal ?

Temporal supporte officiellement PostgreSQL, MySQL, SQLite et Cassandra. CockroachDB convient parfaitement au persistence store car il apporte :

- **SQL distribué fortement cohérent** : les mêmes garanties ACID que PostgreSQL, à n'importe quelle échelle
- **Multi-région actif-actif** : les shards d'historique Temporal se distribuent entre régions sans réplication manuelle
- **Basculement automatique** : les défaillances de nœuds sont transparentes pour les services Temporal
- **Scalabilité horizontale** : scalez lectures et écritures sans logique de sharding dans l'application
- **Protocole filaire PostgreSQL** : le plugin `postgres12` de Temporal fonctionne directement

| Capacité | Contribution de CockroachDB |
|---|---|
| **Isolation sérialisable** | Pas de mises à jour perdues ni de lectures fantômes sous exécution concurrente |
| **Réplication multi-région** | Shards d'historique durables à travers les défaillances de data center |
| **Scalabilité horizontale** | Ajoutez des nœuds pour absorber plus de workflows concurrents sans re-sharding |
| **Basculement automatique** | Défaillances de nœuds transparentes pour les quatre services Temporal |
| **Compatibilité PostgreSQL** | Aucune modification du code applicatif ; le plugin `postgres12` fonctionne directement |

CockroachDB remplace PostgreSQL directement, offrant aux services sans état de Temporal une fondation indestructible et distribuée globalement. Le seul travail de déploiement supplémentaire par rapport à une installation PostgreSQL standard est l'application d'un schéma de visibilité adapté à CockroachDB, qui résout quatre constructions PostgreSQL non supportées.

---

## Déployer Temporal sur CockroachDB

### Prérequis : Installation des outils nécessaires

Tous les binaires ci-dessous sont autonomes et ne nécessitent pas de gestionnaire de paquets. Choisissez la version correspondant à votre OS et architecture.

#### Serveur Temporal et outil SQL

Téléchargez l'archive Temporal depuis la [page des releases GitHub](https://github.com/temporalio/temporal/releases). L'archive contient `temporal-server`, `temporal-sql-tool` et `tdbg` :

```bash
VERSION="1.30.4"
curl -L -o temporal.tar.gz \
  "https://github.com/temporalio/temporal/releases/download/v${VERSION}/temporal_${VERSION}_linux_amd64.tar.gz"
tar -xzf temporal.tar.gz
chmod +x temporal-server temporal-sql-tool tdbg
sudo mv temporal-server temporal-sql-tool tdbg /usr/local/bin/
```

> Sur macOS ARM64, remplacez `linux_amd64` par `darwin_arm64`.

#### CLI Temporal

Le CLI `temporal` permet de gérer les namespaces, démarrer des workflows et vérifier l'état du cluster. Téléchargez-le séparément :

```bash
CLI_VERSION="1.3.0"
curl -L -o temporal.tar.gz \
  "https://github.com/temporalio/cli/releases/download/v${CLI_VERSION}/temporal_cli_${CLI_VERSION}_linux_amd64.tar.gz"
tar -xzf temporal.tar.gz
chmod +x temporal
sudo mv temporal /usr/local/bin/
```

#### Interface web Temporal (optionnel)

Le serveur UI autonome se connecte à votre frontend Temporal via gRPC et sert le tableau de bord dans le navigateur :

```bash
UI_VERSION="2.49.1"
curl -L -o temporal-ui.tar.gz \
  "https://github.com/temporalio/ui-server/releases/download/v${UI_VERSION}/ui-server_${UI_VERSION}_linux_amd64.tar.gz"
tar -xzf temporal-ui.tar.gz
chmod +x ui-server
sudo mv ui-server /usr/local/bin/temporal-ui-server
```

Créez un fichier de configuration minimal et démarrez-le :

```bash
mkdir -p ~/temporal-ui/config
cat > ~/temporal-ui/config/development.yaml <<EOF
temporalGrpcAddress: "localhost:7233"
host: "0.0.0.0"
port: 8080
enableUi: true
EOF

temporal-ui-server --root ~/temporal-ui start
```

L'interface est ensuite accessible à `http://localhost:8080`.

#### Omes — outil de test de charge

[Omes](https://github.com/temporalio/omes) nécessite Go 1.21+. Installez Go si nécessaire :

```bash
# macOS
brew install go

# Linux (ajustez la version si besoin)
curl -L https://go.dev/dl/go1.21.0.linux-amd64.tar.gz | sudo tar -C /usr/local -xzf -
export PATH=$PATH:/usr/local/go/bin
```

Clonez et compilez Omes :

```bash
git clone https://github.com/temporalio/omes.git
cd omes
go build -o omes ./cmd/main.go
sudo mv omes /usr/local/bin/
```

#### Client psql

`psql` est utilisé pour appliquer directement le schéma de visibilité compatible CockroachDB. Il est fourni avec les outils client PostgreSQL :

```bash
# macOS
brew install libpq && brew link --force libpq

# Debian / Ubuntu
sudo apt-get install -y postgresql-client

# RHEL / Amazon Linux
sudo yum install -y postgresql
```

---

### Étape 1 : Provisionnement des bases et de l'utilisateur

```sql
CREATE DATABASE temporal;
CREATE DATABASE temporal_visibility;
CREATE USER temporal WITH PASSWORD 'your-password';
GRANT ALL ON DATABASE temporal TO temporal;
GRANT ALL ON DATABASE temporal_visibility TO temporal;
```

Définissez le même mot de passe que la variable d'environnement `TEMPORAL_DB_PASSWORD` utilisée aux étapes 2 et 4.

### Étape 2 : Initialisation du schéma de persistance

Le schéma principal fonctionne avec CockroachDB sans modification via l'outil SQL de Temporal. Téléchargez `temporal-sql-tool` depuis les [releases GitHub de Temporal](https://github.com/temporalio/temporal/releases) avec `temporal-server`. Les fichiers de schéma se trouvent dans l'archive source sous `schema/postgresql/v12/temporal/versioned/`.

> **Important :** passez le nom d'hôte et le port en flags séparés (`--ep <host> --port 26257`). `temporal-sql-tool` supporte plusieurs backends de base de données dont MySQL, et sa logique interne d'analyse des ports traite une chaîne `host:port` combinée comme un endpoint MySQL — ajoutant silencieusement `:3306` au lieu d'utiliser le port spécifié.

```bash
temporal-sql-tool \
  --plugin postgres12 \
  --ep "<crdb-host>" \
  --port 26257 \
  --db temporal \
  --user temporal \
  --tls \
  --tls-ca-file /certs/ca.crt \
  --tls-cert-file /certs/client.temporal.crt \
  --tls-key-file /certs/client.temporal.key \
  setup-schema -v 0.0

temporal-sql-tool \
  --plugin postgres12 \
  --ep "<crdb-host>" \
  --port 26257 \
  --db temporal \
  --user temporal \
  --tls \
  --tls-ca-file /certs/ca.crt \
  --tls-cert-file /certs/client.temporal.crt \
  --tls-key-file /certs/client.temporal.key \
  update-schema -d ./schema/postgresql/v12/temporal/versioned
```

### Étape 3 : Correction du schéma de visibilité pour CockroachDB

> **Cette étape nécessite de contourner complètement `temporal-sql-tool` pour la base de visibilité.** La migration `v1.2` (`advanced_visibility.sql`) introduit quatre incompatibilités avec CockroachDB qui font échouer l'outil. Appliquer directement un schéma adapté via `psql` est la bonne approche.

`btree_gin` reste bien l'une des incompatibilités : CockroachDB ne supporte pas cette extension. Mais la documentation originale pointait vers la migration `v1.1` comme source du problème et traitait `btree_gin` comme le seul obstacle. Ces deux affirmations sont incorrectes. L'appel à l'extension se trouve dans un bloc anonyme `DO LANGUAGE 'plpgsql'` situé dans `v1.2`. CockroachDB rejette le bloc `DO` lui-même avant même d'atteindre la ligne de l'extension : le premier message d'erreur n'est donc pas « extension introuvable » mais « blocs de code anonymes non supportés ». Deux incompatibilités supplémentaires attendent dans le même fichier après cela.

Les quatre incompatibilités, toutes présentes dans `schema/postgresql/v12/visibility/versioned/v1.2/advanced_visibility.sql` :

| Incompatibilité | Cause racine | Correctif |
|---|---|---|
| `DO LANGUAGE 'plpgsql' $$...$$` | Les blocs de code anonymes ne sont pas supportés dans CockroachDB | Supprimer entièrement ; aucune configuration d'extension n'est nécessaire |
| Type de colonne `TSVECTOR` | Non supporté dans CockroachDB | Remplacer par `VARCHAR(4096)` |
| `(s::timestamptz AT TIME ZONE 'UTC')` dans les colonnes calculées `STORED` | Cast dépendant du contexte ; CockroachDB le rejette dans les colonnes calculées stockées | Utiliser `parse_timestamp(s)` à la place |
| `USING GIN (namespace_id, col jsonb_path_ops)` | Index GIN multi-colonnes avec `jsonb_path_ops` non supporté | Utiliser `CREATE INVERTED INDEX (col)` sur la seule colonne JSONB |

Le schéma doit également couvrir toutes les migrations jusqu'en v1.13, ce qu'exige la vérification de version au démarrage de Temporal. Sauvegardez le contenu suivant dans `crdb_visibility_schema.sql` et appliquez-le directement :

```sql
-- Schema version tracking tables (required for Temporal's startup version check)
CREATE TABLE IF NOT EXISTS schema_version (
  version_partition       INT NOT NULL,
  db_name                 VARCHAR(255) NOT NULL,
  creation_time           TIMESTAMP,
  curr_version            VARCHAR(64),
  min_compatible_version  VARCHAR(64),
  PRIMARY KEY (version_partition, db_name)
);

CREATE TABLE IF NOT EXISTS schema_update_history (
  version_partition INT NOT NULL,
  year              INT NOT NULL,
  month             INT NOT NULL,
  update_time       TIMESTAMP,
  description       VARCHAR(255),
  manifest_md5      VARCHAR(64),
  new_version       VARCHAR(64),
  old_version       VARCHAR(64),
  PRIMARY KEY (version_partition, year, month, update_time)
);

-- executions_visibility with all columns through v1.13
-- TSVECTOR -> VARCHAR ; parse_timestamp() remplace ::timestamp ; btree_gin inutile
CREATE TABLE executions_visibility (
  namespace_id         CHAR(64)      NOT NULL,
  run_id               CHAR(64)      NOT NULL,
  start_time           TIMESTAMP     NOT NULL,
  execution_time       TIMESTAMP     NOT NULL,
  workflow_id          VARCHAR(255)  NOT NULL,
  workflow_type_name   VARCHAR(255)  NOT NULL,
  status               INTEGER       NOT NULL,
  close_time           TIMESTAMP     NULL,
  history_length       BIGINT,
  history_size_bytes   BIGINT        NULL,
  execution_duration   BIGINT        NULL,
  state_transition_count BIGINT      NULL,
  memo                 BYTEA,
  encoding             VARCHAR(64)   NOT NULL,
  task_queue           VARCHAR(255)  DEFAULT '' NOT NULL,
  search_attributes    JSONB         NULL,
  parent_workflow_id   VARCHAR(255)  NULL,
  parent_run_id        VARCHAR(255)  NULL,
  root_workflow_id     VARCHAR(255)  NOT NULL DEFAULT '',
  root_run_id          VARCHAR(255)  NOT NULL DEFAULT '',
  _version             BIGINT        NOT NULL DEFAULT 0,

  -- Attributs de recherche prédéfinis (calculés depuis le blob JSONB search_attributes)
  TemporalChangeVersion      JSONB         AS (search_attributes->'TemporalChangeVersion')                                       STORED,
  BinaryChecksums            JSONB         AS (search_attributes->'BinaryChecksums')                                             STORED,
  BuildIds                   JSONB         AS (search_attributes->'BuildIds')                                                     STORED,
  BatcherUser                VARCHAR(255)  AS (search_attributes->>'BatcherUser')                                                STORED,
  TemporalScheduledStartTime TIMESTAMP     AS (parse_timestamp(search_attributes->>'TemporalScheduledStartTime'))                STORED,
  TemporalScheduledById      VARCHAR(255)  AS (search_attributes->>'TemporalScheduledById')                                      STORED,
  TemporalSchedulePaused     BOOLEAN       AS ((search_attributes->'TemporalSchedulePaused')::boolean)                           STORED,
  TemporalNamespaceDivision  VARCHAR(255)  AS (search_attributes->>'TemporalNamespaceDivision')                                  STORED,
  TemporalPauseInfo          JSONB         AS (search_attributes->'TemporalPauseInfo')                                           STORED,
  TemporalWorkerDeploymentVersion    VARCHAR(255)  AS (search_attributes->>'TemporalWorkerDeploymentVersion')                    STORED,
  TemporalWorkflowVersioningBehavior VARCHAR(255)  AS (search_attributes->>'TemporalWorkflowVersioningBehavior')                 STORED,
  TemporalWorkerDeployment           VARCHAR(255)  AS (search_attributes->>'TemporalWorkerDeployment')                           STORED,
  TemporalReportedProblems           JSONB         AS (search_attributes->'TemporalReportedProblems')                            STORED,
  TemporalBool01         BOOLEAN       AS ((search_attributes->'TemporalBool01')::boolean)                                       STORED,
  TemporalBool02         BOOLEAN       AS ((search_attributes->'TemporalBool02')::boolean)                                       STORED,
  TemporalDatetime01     TIMESTAMP     AS (parse_timestamp(search_attributes->>'TemporalDatetime01'))                            STORED,
  TemporalDatetime02     TIMESTAMP     AS (parse_timestamp(search_attributes->>'TemporalDatetime02'))                            STORED,
  TemporalDouble01       DECIMAL(20,5) AS ((search_attributes->'TemporalDouble01')::decimal)                                     STORED,
  TemporalDouble02       DECIMAL(20,5) AS ((search_attributes->'TemporalDouble02')::decimal)                                     STORED,
  TemporalInt01          BIGINT        AS ((search_attributes->'TemporalInt01')::bigint)                                         STORED,
  TemporalInt02          BIGINT        AS ((search_attributes->'TemporalInt02')::bigint)                                         STORED,
  TemporalKeyword01      VARCHAR(255)  AS (search_attributes->>'TemporalKeyword01')                                              STORED,
  TemporalKeyword02      VARCHAR(255)  AS (search_attributes->>'TemporalKeyword02')                                              STORED,
  TemporalKeyword03      VARCHAR(255)  AS (search_attributes->>'TemporalKeyword03')                                              STORED,
  TemporalKeyword04      VARCHAR(255)  AS (search_attributes->>'TemporalKeyword04')                                              STORED,
  TemporalKeywordList01  JSONB         AS (search_attributes->'TemporalKeywordList01')                                           STORED,
  TemporalKeywordList02  JSONB         AS (search_attributes->'TemporalKeywordList02')                                           STORED,
  TemporalLowCardinalityKeyword01 VARCHAR(255) AS (search_attributes->>'TemporalLowCardinalityKeyword01')                        STORED,
  TemporalUsedWorkerDeploymentVersions JSONB   AS (search_attributes->'TemporalUsedWorkerDeploymentVersions')                    STORED,

  -- Attributs de recherche personnalisés pré-alloués
  Bool01     BOOLEAN       AS ((search_attributes->'Bool01')::boolean)      STORED,
  Bool02     BOOLEAN       AS ((search_attributes->'Bool02')::boolean)      STORED,
  Bool03     BOOLEAN       AS ((search_attributes->'Bool03')::boolean)      STORED,
  Datetime01 TIMESTAMP     AS (parse_timestamp(search_attributes->>'Datetime01')) STORED,
  Datetime02 TIMESTAMP     AS (parse_timestamp(search_attributes->>'Datetime02')) STORED,
  Datetime03 TIMESTAMP     AS (parse_timestamp(search_attributes->>'Datetime03')) STORED,
  Double01   DECIMAL(20,5) AS ((search_attributes->'Double01')::decimal)    STORED,
  Double02   DECIMAL(20,5) AS ((search_attributes->'Double02')::decimal)    STORED,
  Double03   DECIMAL(20,5) AS ((search_attributes->'Double03')::decimal)    STORED,
  Int01      BIGINT        AS ((search_attributes->'Int01')::bigint)        STORED,
  Int02      BIGINT        AS ((search_attributes->'Int02')::bigint)        STORED,
  Int03      BIGINT        AS ((search_attributes->'Int03')::bigint)        STORED,
  Keyword01  VARCHAR(255)  AS (search_attributes->>'Keyword01')             STORED,
  Keyword02  VARCHAR(255)  AS (search_attributes->>'Keyword02')             STORED,
  Keyword03  VARCHAR(255)  AS (search_attributes->>'Keyword03')             STORED,
  Keyword04  VARCHAR(255)  AS (search_attributes->>'Keyword04')             STORED,
  Keyword05  VARCHAR(255)  AS (search_attributes->>'Keyword05')             STORED,
  Keyword06  VARCHAR(255)  AS (search_attributes->>'Keyword06')             STORED,
  Keyword07  VARCHAR(255)  AS (search_attributes->>'Keyword07')             STORED,
  Keyword08  VARCHAR(255)  AS (search_attributes->>'Keyword08')             STORED,
  Keyword09  VARCHAR(255)  AS (search_attributes->>'Keyword09')             STORED,
  Keyword10  VARCHAR(255)  AS (search_attributes->>'Keyword10')             STORED,
  Text01     VARCHAR(4096) AS (search_attributes->>'Text01')                STORED,
  Text02     VARCHAR(4096) AS (search_attributes->>'Text02')                STORED,
  Text03     VARCHAR(4096) AS (search_attributes->>'Text03')                STORED,
  KeywordList01 JSONB      AS (search_attributes->'KeywordList01')          STORED,
  KeywordList02 JSONB      AS (search_attributes->'KeywordList02')          STORED,
  KeywordList03 JSONB      AS (search_attributes->'KeywordList03')          STORED,

  PRIMARY KEY (namespace_id, run_id)
);

-- Standard expression indexes (COALESCE open/close window pattern)
CREATE INDEX default_idx           ON executions_visibility (namespace_id, (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_execution_time     ON executions_visibility (namespace_id, execution_time,     (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_workflow_id        ON executions_visibility (namespace_id, workflow_id,        (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_workflow_type      ON executions_visibility (namespace_id, workflow_type_name, (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_status             ON executions_visibility (namespace_id, status,             (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_history_length     ON executions_visibility (namespace_id, history_length,     (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_history_size_bytes ON executions_visibility (namespace_id, history_size_bytes, (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_execution_duration ON executions_visibility (namespace_id, execution_duration, (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_state_transition_count ON executions_visibility (namespace_id, state_transition_count, (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_task_queue         ON executions_visibility (namespace_id, task_queue,         (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_parent_workflow_id ON executions_visibility (namespace_id, parent_workflow_id, (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_parent_run_id      ON executions_visibility (namespace_id, parent_run_id,      (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_root_workflow_id   ON executions_visibility (namespace_id, root_workflow_id,   (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_root_run_id        ON executions_visibility (namespace_id, root_run_id,        (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_batcher_user       ON executions_visibility (namespace_id, BatcherUser,        (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_temporal_scheduled_start_time ON executions_visibility (namespace_id, TemporalScheduledStartTime, (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_temporal_scheduled_by_id      ON executions_visibility (namespace_id, TemporalScheduledById,     (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_temporal_schedule_paused      ON executions_visibility (namespace_id, TemporalSchedulePaused,    (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_temporal_namespace_division   ON executions_visibility (namespace_id, TemporalNamespaceDivision, (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_temporal_worker_deployment_version ON executions_visibility (namespace_id, TemporalWorkerDeploymentVersion, (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_temporal_workflow_versioning_behavior ON executions_visibility (namespace_id, TemporalWorkflowVersioningBehavior, (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_temporal_worker_deployment ON executions_visibility (namespace_id, TemporalWorkerDeployment, (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_temporal_bool_01     ON executions_visibility (namespace_id, TemporalBool01,   (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_temporal_bool_02     ON executions_visibility (namespace_id, TemporalBool02,   (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_temporal_datetime_01 ON executions_visibility (namespace_id, TemporalDatetime01, (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_temporal_datetime_02 ON executions_visibility (namespace_id, TemporalDatetime02, (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_temporal_double_01   ON executions_visibility (namespace_id, TemporalDouble01,  (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_temporal_double_02   ON executions_visibility (namespace_id, TemporalDouble02,  (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_temporal_int_01      ON executions_visibility (namespace_id, TemporalInt01,     (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_temporal_int_02      ON executions_visibility (namespace_id, TemporalInt02,     (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_temporal_keyword_01  ON executions_visibility (namespace_id, TemporalKeyword01, (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_temporal_keyword_02  ON executions_visibility (namespace_id, TemporalKeyword02, (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_temporal_keyword_03  ON executions_visibility (namespace_id, TemporalKeyword03, (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_temporal_keyword_04  ON executions_visibility (namespace_id, TemporalKeyword04, (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_temporal_low_cardinality_keyword_01 ON executions_visibility (namespace_id, TemporalLowCardinalityKeyword01, (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_bool_01  ON executions_visibility (namespace_id, Bool01,  (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_bool_02  ON executions_visibility (namespace_id, Bool02,  (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_bool_03  ON executions_visibility (namespace_id, Bool03,  (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_datetime_01 ON executions_visibility (namespace_id, Datetime01, (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_datetime_02 ON executions_visibility (namespace_id, Datetime02, (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_datetime_03 ON executions_visibility (namespace_id, Datetime03, (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_double_01   ON executions_visibility (namespace_id, Double01,   (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_double_02   ON executions_visibility (namespace_id, Double02,   (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_double_03   ON executions_visibility (namespace_id, Double03,   (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_int_01      ON executions_visibility (namespace_id, Int01,      (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_int_02      ON executions_visibility (namespace_id, Int02,      (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_int_03      ON executions_visibility (namespace_id, Int03,      (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_keyword_01  ON executions_visibility (namespace_id, Keyword01,  (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_keyword_02  ON executions_visibility (namespace_id, Keyword02,  (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_keyword_03  ON executions_visibility (namespace_id, Keyword03,  (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_keyword_04  ON executions_visibility (namespace_id, Keyword04,  (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_keyword_05  ON executions_visibility (namespace_id, Keyword05,  (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_keyword_06  ON executions_visibility (namespace_id, Keyword06,  (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_keyword_07  ON executions_visibility (namespace_id, Keyword07,  (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_keyword_08  ON executions_visibility (namespace_id, Keyword08,  (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_keyword_09  ON executions_visibility (namespace_id, Keyword09,  (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);
CREATE INDEX by_keyword_10  ON executions_visibility (namespace_id, Keyword10,  (COALESCE(close_time, '9999-12-31 23:59:59')) DESC, start_time DESC, run_id);

-- CockroachDB inverted indexes replace multi-column GIN (namespace_id, col jsonb_path_ops)
CREATE INVERTED INDEX by_temporal_change_version     ON executions_visibility (TemporalChangeVersion);
CREATE INVERTED INDEX by_binary_checksums            ON executions_visibility (BinaryChecksums);
CREATE INVERTED INDEX by_build_ids                   ON executions_visibility (BuildIds);
CREATE INVERTED INDEX by_temporal_pause_info         ON executions_visibility (TemporalPauseInfo);
CREATE INVERTED INDEX by_temporal_reported_problems  ON executions_visibility (TemporalReportedProblems);
CREATE INVERTED INDEX by_temporal_keyword_list_01    ON executions_visibility (TemporalKeywordList01);
CREATE INVERTED INDEX by_temporal_keyword_list_02    ON executions_visibility (TemporalKeywordList02);
CREATE INVERTED INDEX by_keyword_list_01             ON executions_visibility (KeywordList01);
CREATE INVERTED INDEX by_keyword_list_02             ON executions_visibility (KeywordList02);
CREATE INVERTED INDEX by_keyword_list_03             ON executions_visibility (KeywordList03);
CREATE INVERTED INDEX by_used_deployment_versions    ON executions_visibility (TemporalUsedWorkerDeploymentVersions);

-- Set the schema version so Temporal's startup compatibility check passes
INSERT INTO schema_version (version_partition, db_name, creation_time, curr_version, min_compatible_version)
VALUES (0, 'temporal_visibility', now(), '1.13', '0.1')
ON CONFLICT DO NOTHING;
```

Appliquez-le avec `psql` (le CLI `cockroach` n'est pas nécessaire) :

```bash
PGPASSWORD="${TEMPORAL_DB_PASSWORD}" psql \
  "postgresql://temporal@<crdb-host>:26257/temporal_visibility?sslmode=verify-full&sslrootcert=/certs/ca.crt&sslcert=/certs/client.temporal.crt&sslkey=/certs/client.temporal.key" \
  --file ./crdb_visibility_schema.sql
```

### Étape 4 : Configurer et démarrer le serveur Temporal

Sauvegardez le contenu suivant dans `base.yaml`. La configuration doit être dans un fichier ; le flag `--config-file` accepte un chemin absolu ou relatif au répertoire courant :

```yaml
log:
  stdout: true
  level: "info"

persistence:
  defaultStore: crdb-default
  visibilityStore: crdb-visibility
  numHistoryShards: 4
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
          serverName: "<crdb-host>"

global:
  membership:
    maxJoinDuration: 30s
    broadcastAddress: "127.0.0.1"

services:
  frontend:
    rpc:
      grpcPort: 7233
      membershipPort: 6933
      bindOnLocalHost: true
  matching:
    rpc:
      grpcPort: 7235
      membershipPort: 6935
      bindOnLocalHost: true
  history:
    rpc:
      grpcPort: 7234
      membershipPort: 6934
      bindOnLocalHost: true
  worker:
    rpc:
      grpcPort: 7239
      membershipPort: 6939
      bindOnLocalHost: true

clusterMetadata:
  enableGlobalNamespace: false
  failoverVersionIncrement: 10
  masterClusterName: "active"
  currentClusterName: "active"
  clusterInformation:
    active:
      enabled: true
      initialFailoverVersion: 1
      rpcAddress: "127.0.0.1:7233"

dcRedirectionPolicy:
  policy: "noop"

archival:
  history:
    state: "disabled"
  visibility:
    state: "disabled"

namespaceDefaults:
  archival:
    history:
      state: "disabled"
    visibility:
      state: "disabled"
```

Démarrez le serveur avec `--allow-no-auth` (requis quand aucun autoriseur n'est configuré) :

```bash
temporal-server --config-file ./base.yaml --allow-no-auth start
```

### Étape 5 : Initialisation du cluster

Une fois le serveur démarré, créez le namespace par défaut et vérifiez le cluster :

```bash
# Create the application namespace
temporal --address localhost:7233 operator namespace create default

# Confirm the cluster is healthy
temporal --address localhost:7233 operator cluster health

# List internal system workflows to confirm the visibility store is connected
temporal --address localhost:7233 -n temporal-system workflow list
```

Le health check doit renvoyer `SERVING` et la liste doit afficher deux workflows système en cours (`temporal-sys-history-scanner` et `temporal-sys-tq-scanner`).

### Étape 6 : Premier workflow d'agent IA durable

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

## Tests de charge et de performance

### Benchmarking avec Omes

[Omes](https://github.com/temporalio/omes) est l'outil officiel de test de charge de Temporal (successeur de Maru, désormais déprécié). Il génère des volumes configurables de workflows et d'activités contre un cluster en production et rapporte le débit, la latence et les taux d'erreur. Avec un backend CockroachDB, il permet d'observer comment le niveau de persistance se comporte à mesure que la concurrence augmente.

Compilez Omes depuis les sources et lancez le scénario `throughput_stress` :

```bash
git clone https://github.com/temporalio/omes.git
cd omes

# Register the custom search attribute Omes requires
temporal operator search-attribute create \
  --namespace default \
  --name OmesExecutionID \
  --type Keyword

# Run: 50 concurrent workflows, 5-minute duration
go run ./cmd/main.go run-scenario-with-worker \
  --scenario throughput_stress \
  --language go \
  --server-address localhost:7233 \
  --namespace default \
  --duration 5m \
  --max-concurrent 50
```

Autres scénarios utiles :

| Scénario | Ce qu'il teste |
|---|---|
| `workflow_with_single_noop_activity` | Aller-retour minimal : un workflow, une activité no-op |
| `throughput_stress` | Débit d'écriture soutenu vers le store de persistance |
| `state_transitions_steady` | Taux de transitions d'état constant ; utilisez `--option state-transitions-per-second=N` |
| `ebb_and_flow` | Backlog oscillant entre un minimum et un maximum de workflows concurrents |

> **La co-localisation est essentielle.** Omes utilise l'API [Workflow Update](https://docs.temporal.io/workflows#update) de Temporal en interne, ce qui nécessite des allers-retours sous la seconde entre le client, le serveur et le store de persistance. Exécutez Omes depuis une machine dans le même datacenter ou VPC que votre cluster CockroachDB. Une connexion à CockroachDB via un WAN fait monter chaque opération d'écriture à 3–6 secondes de latence (contre <100 ms en local), ce qui déclenche les timeouts internes d'Omes avant la fin des scénarios.

Pour une mesure de latence de persistance rapide, utilisez directement le SDK Go de Temporal pour mesurer le débit brut de `StartWorkflowExecution` :

```go
package main

import (
    "context"
    "fmt"
    "sort"
    "sync"
    "time"
    "go.temporal.io/sdk/client"
)

func main() {
    c, _ := client.Dial(client.Options{HostPort: "localhost:7233", Namespace: "default"})
    defer c.Close()

    const total, concurrency = 20, 3
    latencies := make([]time.Duration, 0, total)
    var mu sync.Mutex
    var wg sync.WaitGroup
    sem := make(chan struct{}, concurrency)

    t0 := time.Now()
    for i := 0; i < total; i++ {
        wg.Add(1); sem <- struct{}{}
        go func(i int) {
            defer wg.Done(); defer func() { <-sem }()
            start := time.Now()
            c.ExecuteWorkflow(context.Background(), client.StartWorkflowOptions{
                ID: fmt.Sprintf("bench-%d-%d", time.Now().UnixMicro(), i),
                TaskQueue: "bench-queue",
            }, "BenchWorkflow", i)
            mu.Lock(); latencies = append(latencies, time.Since(start)); mu.Unlock()
        }(i)
    }
    wg.Wait()
    elapsed := time.Since(t0)

    sort.Slice(latencies, func(i, j int) bool { return latencies[i] < latencies[j] })
    fmt.Printf("Throughput: %.1f/sec | p50: %v | p95: %v\n",
        float64(len(latencies))/elapsed.Seconds(),
        latencies[len(latencies)*50/100].Round(time.Millisecond),
        latencies[len(latencies)*95/100].Round(time.Millisecond))
}
```

Avec cette configuration, vous pouvez :

- **Mesurer le débit de workflows** : workflows démarrés par seconde à différents niveaux de concurrence
- **Observer la latence de persistance** : la latence p50/p95 reflète directement les performances d'écriture de CockroachDB ; un cluster co-localisé délivre typiquement un p50 <100 ms, tandis qu'un cluster distant en WAN affiche 3–6 s par écriture
- **Valider le comportement de récupération** : supprimez un nœud CockroachDB en cours d'exécution et confirmez que les workflows en cours reprennent automatiquement une fois le cluster rétabli, sans intervention manuelle et sans perte de workflow

### Observabilité

Deux tableaux de bord offrent des vues complémentaires de la même charge :

**L'interface web Temporal** (`http://localhost:8080` avec la configuration Docker par défaut) permet d'inspecter les exécutions de workflows individuels en temps réel : historique des événements, statut des activités, compteurs de réessais et profondeur actuelle des task queues. Pendant un run Omes, vous pouvez observer le nombre d'exécutions ouvertes monter et descendre, et accéder à tout workflow échoué pour voir exactement quelle activité a expiré.

<img src="/assets/img/temporal-ui-bench-workflows.gif" alt="Interface web Temporal : 72 exécutions BenchWorkflow passant de l'état running à completed" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**Interface web Temporal : 72 exécutions BenchWorkflow adossées à CockroachDB — les workflows passent à l'état complété et l'interface défile jusqu'à l'historique d'événements d'une exécution terminée**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

**La console d'administration CockroachDB** (`http://<crdb-host>:8080`) expose la vue au niveau de la base de données :

| Panneau | Ce qu'il faut surveiller |
|---|---|
| **SQL Activity** | Requêtes par seconde, latence p50/p99 ; une latence élevée sur `INSERT INTO executions` signale une contention en écriture |
| **Ranges** | Distribution des plages de données entre nœuds ; une distribution inégale signifie qu'un nœud est un point chaud pour les écritures de shards d'historique |
| **Node Map** | CPU, IOPS et réseau par nœud ; vérifiez qu'aucun nœud n'est saturé pendant que les autres sont inactifs |

Cette combinaison donne une vue complète : Temporal indique *quels* workflows sont lents ; CockroachDB explique *pourquoi* au niveau du stockage.

<img src="/assets/img/crdb-admin-sql-metrics.png" alt="Tableau de bord SQL de la console d'administration CockroachDB" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**Console d'administration CockroachDB (v24.3.8) : tableau de bord SQL montrant les sessions ouvertes et le taux de connexion sur le cluster à 3 nœuds pendant le benchmark Temporal. Le panneau Summary affiche 5,2 QPS et une latence p99 de 8,9 ms.**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

---

## Passage à l'échelle en production

À mesure que la charge augmente, quelques pratiques permettent de maintenir les performances :

- **Ajuster le nombre de shards Temporal** : `numHistoryShards` dans `base.yaml` contrôle le parallélisme des écritures. L'augmenter distribue les écritures d'historique sur davantage de ranges CockroachDB, réduisant la contention. Commencez à 4 en développement et montez à 512 ou plus en production.
- **Surveiller les hot ranges** : utilisez la page **Hot Ranges** de la console d'administration CockroachDB pour identifier les ranges qui reçoivent une part disproportionnée des écritures. Les hot ranges apparaissent généralement quand un petit nombre de shards d'historique Temporal correspond au même range CockroachDB.
- **Exploiter le splitting et la distribution des ranges** : CockroachDB divise et rééquilibre automatiquement les ranges à mesure que les données croissent, mais vous pouvez pré-diviser les tables `executions` et `executions_visibility` pour une distribution prévisible des écritures à fort nombre de shards.
- **Envisager un backend de visibilité dédié pour les charges analytiques lourdes** : le visibility store Temporal gère toutes les requêtes `ListWorkflowExecutions`. Sous une forte charge de requêtes analytiques, router la visibilité vers une base CockroachDB séparée — ou un cluster Elasticsearch — isole la pression des requêtes du chemin d'écriture de l'historique.

Ces pratiques reflètent les approches utilisées avec succès avec d'autres bases de données horizontalement scalables, et s'appliquent directement à CockroachDB sans modification du code Temporal, uniquement par configuration.

---

## Voir aussi

- [Documentation Temporal](https://docs.temporal.io/)
- [Concevoir un moteur de workflow depuis les premiers principes](https://temporal.io/blog/workflow-engine-principles)
- [SQL distribué CockroachDB](https://www.cockroachlabs.com/blog/what-is-distributed-sql/)
