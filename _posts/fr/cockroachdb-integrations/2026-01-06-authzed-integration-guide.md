---
layout: post
lang: fr
title: "Intégrer CockroachDB avec AuthZed"
subtitle: "Comment CockroachDB propulse SpiceDB d'AuthZed en tant que backend d'autorisation fortement cohérent et distribué mondialement"
thumbnail-img: /assets/img/authzed-crdb-architecture.png
share-img: /assets/img/authzed-crdb-architecture.png
tags: [cockroachdb-integrations, CockroachDB, authzed, spicedb, authorization, ReBAC, permissions]
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

L'autorisation répond à la question : *Que peut faire un utilisateur une fois connecté ?* Se connecter à un système ne signifie pas un accès illimité. L'autorisation garantit que les utilisateurs n'accèdent qu'à ce qui est nécessaire à leur rôle.

Les systèmes traditionnels de contrôle d'accès basé sur les rôles (RBAC) étaient autrefois intégrés directement dans la couche applicative. Aujourd'hui, des alternatives scalables existent. Les systèmes d'autorisation modernes, inspirés du [papier Google Zanzibar](https://authzed.com/docs/spicedb/concepts/zanzibar) et implémentés par des projets comme AuthZed, distribuent les décisions d'autorisation sur des clusters de machines.

AuthZed est une plateforme d'infrastructure d'autorisation moderne qui permet aux équipes d'ingénierie d'**arrêter de construire des stacks d'autorisation personnalisées** et d'adopter à la place un système de contrôle d'accès scalable, cohérent et à granularité fine pour n'importe quelle application. AuthZed fournit à la fois des **services d'autorisation cloud gérés** et un **moteur d'autorisation open-source (SpiceDB)**, conçus pour propulser l'autorisation à grande échelle avec une forte flexibilité sémantique.

---

## Qu'est-ce qu'AuthZed ?

**AuthZed** est une plateforme focalisée exclusivement sur l'**autorisation**. Là où l'authentification vérifie l'identité, l'autorisation décide des droits d'accès aux ressources une fois l'identité connue. AuthZed centralise, unifie et met à l'échelle cette couche de sécurité fondamentale afin que les développeurs n'aient pas à implémenter leur propre logique de permissions dans chaque application.

Au cœur du système, **SpiceDB** est le moteur derrière le modèle d'autorisation de tous les produits AuthZed. Il est conçu pour être totalement agnostique aux solutions d'authentification et aux fournisseurs d'identité. SpiceDB implémente un modèle de permissions basé sur les relations qui prend en charge la cohérence forte, la réplication mondiale et une échelle extrêmement élevée, traitant des millions de requêtes d'autorisation par seconde pour les applications modernes et distribuées. SpiceDB est un moteur de graphe qui stocke de manière centralisée les données d'autorisation (relations et permissions). Les requêtes d'autorisation (ex. `checkPermission`, `lookupResources`) sont résolues via un dispatcher qui parcourt le graphe de permissions.

<img src="/assets/img/authzed-spicedb-engine.png" alt="Moteur de graphe de permissions SpiceDB" style="width:60%;display:block;margin:1.5rem auto;">

La mission d'AuthZed est de :

- Éliminer la logique d'autorisation fragmentée et spécifique à chaque application
- Fournir un **référentiel unique** pour les permissions et les politiques d'accès
- Délivrer des **performances et une cohérence de niveau entreprise** dans les environnements distribués
- Prendre en charge des exigences de contrôle d'accès complexes et évolutives sans réécrire le code

---

## Pourquoi Utiliser AuthZed ?

Les applications modernes et les systèmes distribués nécessitent une **autorisation à granularité fine, flexible et scalable**. Le RBAC traditionnel intégré aux applications peut être fragile, incohérent et difficile à maintenir à grande échelle. Ce modèle s'effondre sous une charge mondiale, où :

- Les utilisateurs existent dans plusieurs régions de données
- Les permissions dépendent de relations dynamiques entre entités
- L'évaluation des permissions nécessite un contexte provenant de plusieurs sources de données

Pour répondre à ces défis, AuthZed offre :

- Une **autorisation centralisée** pour tous les services et applications
- Une **évaluation des permissions à grande échelle** avec une faible latence
- Des **garanties de cohérence** dans les systèmes distribués
- Un **contrôle d'accès flexible basé sur les relations (ReBAC)** supportant des politiques métier complexes
- Des **options de déploiement cloud hébergé ou autogéré** selon vos besoins

---

## Où AuthZed et CockroachDB S'imposent-ils Ensemble ?

AuthZed a choisi CockroachDB comme datastore sous-jacent pour AuthZed Dedicated et AuthZed Cloud.

Dans le domaine de l'autorisation, la disponibilité et la résilience sont essentielles. CockroachDB permet aux déploiements AuthZed et SpiceDB de survivre à une panne de nœud, de zone de disponibilité ou de région sans temps d'arrêt.

CockroachDB a été construit autour de ce principe : son modèle d'isolation sérialisable offre la garantie de cohérence transactionnelle la plus forte en SQL — pas « éventuelle », pas « read-committed », mais linéarisable sur un cluster mondial. C'est précisément cette propriété que les systèmes d'autorisation émergents recherchent désormais, mais pour les politiques plutôt que pour les données. C'est pourquoi SpiceDB utilise CockroachDB comme datastore sous-jacent : il acquiert ainsi une fondation SQL distribuée mondialement et fortement cohérente.

<img src="/assets/img/authzed-crdb-architecture.png" alt="Architecture AuthZed et CockroachDB" style="width:100%;margin:1.5rem 0;">

La réplication multi-régions et la haute disponibilité de CockroachDB garantissent que les décisions d'autorisation sont cohérentes, à faible latence et résilientes entre les géographies. Cette architecture combine le modèle d'autorisation flexible et API-first de SpiceDB avec la plateforme de base de données tolérante aux pannes de CockroachDB pour délivrer un contrôle d'accès sécurisé, à granularité fine et fortement cohérent, scalable aux charges de travail d'entreprise dans le monde entier.

De plus, l'architecture multi-active de CockroachDB permet aux déploiements AuthZed et SpiceDB de scaler les écritures horizontalement. AuthZed a pu scaler des déploiements réels à des dizaines de milliers d'écritures par seconde.

---

## Configurer un Environnement Conjoint CockroachDB/AuthZed

Nous allons montrer comment CockroachDB peut servir de source de vérité pour la cohérence des données et des politiques, en modélisant une application de gestion de projets mondiale avec des vérifications d'autorisation propulsées par AuthZed.

Imaginons que nous construisons une application de gestion de contenu mondiale qui utilise SpiceDB comme système de contrôle d'accès, adossé à CockroachDB sur plusieurs régions.

### Prérequis

Pour exécuter ce scénario, vous aurez besoin de :

- Un cluster CockroachDB sécurisé et accessible (autohébergé ou Cloud), une version CRDB actuellement supportée, et un accès réseau depuis votre runtime SpiceDB vers le port `26257`
- Une base de données dédiée `spicedb` et un utilisateur pour SpiceDB, avec suffisamment de privilèges pour exécuter ses migrations et fonctionner normalement

### Étape 1. Provisionner un Cluster CockroachDB

Choisissez l'une des méthodes suivantes pour créer un nouveau cluster CockroachDB, ou utilisez un cluster existant et passez à l'étape 2.

> **Note :** Créez un cluster **sécurisé**. C'est nécessaire pour l'étape de création d'utilisateur de ce tutoriel.

**Créer un cluster sécurisé localement** — si vous avez le binaire CockroachDB installé localement, vous pouvez déployer manuellement un cluster CockroachDB multi-nœuds et autohébergé sur votre machine.

**Créer un cluster CockroachDB autohébergé sur AWS** — déployez un cluster multi-nœuds sur Amazon EC2 en utilisant le service de load-balancing géré d'AWS.

**Créer un cluster CockroachDB Cloud** — CockroachDB Cloud est un service entièrement géré par Cockroach Labs. [Inscrivez-vous](https://cockroachlabs.cloud/) et créez un cluster avec des crédits d'essai.

### Étape 2. Créer une Base de Données pour AuthZed

Avant d'intégrer AuthZed avec CockroachDB, configurez une base de données dédiée.

Connectez-vous à votre client SQL CockroachDB :

```bash
cockroach sql --certs-dir={certs-dir} --host={crdb-fqdn}:26257
```

Créez la base de données :

```sql
CREATE DATABASE spicedb;
```

Créez un utilisateur et accordez-lui les privilèges :

```sql
CREATE USER authz WITH PASSWORD 'securepass';
GRANT ALL ON DATABASE spicedb TO authz;
```

### Étape 3. Installer les Binaires SpiceDB

Installez le binaire SpiceDB :

```bash
sudo apt update && sudo apt install -y curl ca-certificates gpg
curl https://pkg.authzed.com/apt/gpg.key | sudo apt-key add -
sudo echo "deb https://pkg.authzed.com/apt/ * *" > /etc/apt/sources.list.d/fury.list
sudo apt update && sudo apt install -y spicedb
```

Exécutez la migration du schéma SpiceDB :

```bash
spicedb datastore migrate head \
  --datastore-engine=cockroachdb \
  --datastore-conn-uri="postgres://authz:securepass@CRDB_URI:26257/spicedb?sslmode=disable"
```

Démarrez le service SpiceDB :

```bash
spicedb serve \
  --grpc-preshared-key="<preshared_key>" \
  --http-enabled=true \
  --datastore-engine=cockroachdb \
  --datastore-conn-uri="postgres://authz:securepass@CRDB_URI:26257/spicedb?sslmode=disable"
```

Installez le CLI `zed` (l'outil en ligne de commande d'AuthZed) :

```bash
brew install authzed/tap/zed
```

Connectez le CLI à votre instance SpiceDB. Pour le développement local, utilisez le flag `--insecure`. Utilisez le même `preshared_key` que dans la commande `spicedb serve` :

```bash
zed context set my_context <SpiceDB_IP>:50051 <preshared_key> --insecure
```

Vérifiez la connexion :

```bash
zed version
```

En cas de connexion réussie, vous devriez voir :

```
client: zed v0.31.1
service: v1.45.4
```

Si la version du serveur affiche "unknown", vérifiez votre `preshared_key`, l'adresse IP et le port.

---

## Tester l'Intégration CockroachDB/AuthZed

Une fois CockroachDB et AuthZed provisionnés, configurés et accessibles sur le réseau, validez que tous les composants fonctionnent ensemble comme prévu.

### 1. Définir le Schéma

La rédaction d'une ou plusieurs définitions de types d'objets est la première étape du développement d'un schéma de relations d'autorisation.

<img src="/assets/img/authzed-schema-diagram.png" alt="Diagramme de définition de schéma SpiceDB" style="width:60%;display:block;margin:1.5rem auto;">

Dans l'exemple ci-dessus, nous définissons les concepts `user` et `document`. L'utilisateur peut être `viewer`, `editor` ou `admin`. La définition donne la permission `remove` uniquement au rôle `admin`. Pour `edit` un fichier, l'utilisateur doit être soit `editor` soit `admin`. La permission de `view` un document est accordée aux rôles viewer, editor et admin.

```
definition user {}

definition document {
    relation editor: user
    relation viewer: user
    relation admin: user

    permission view = viewer + editor + admin
    permission edit = editor + admin
    permission remove = admin
}
```

Sauvegardez le schéma sous `schema.zed` et écrivez-le dans SpiceDB :

```bash
zed schema write ./schema.zed
```

Vérifiez qu'il a été sauvegardé :

```bash
zed schema read
```

Vous pouvez également écrire le schéma via l'API REST :

```bash
curl --location 'http://<SpiceDB_IP>:8443/v1/schema/write' \
--header 'Content-Type: application/json' \
--header 'Accept: application/json' \
--header 'Authorization: Bearer <preshared_key>' \
--data '{
"schema": "definition user {} \n definition document { \n relation editor: user \n relation viewer: user \n relation admin: user \n permission view = viewer + editor + admin \n permission edit = editor + admin \n permission remove = admin \n}"
}'

# sortie :
# {"writtenAt":{"token":"GhUKEzE3NTgxMjkyOTM0MDE2MDYxNDA="}}
```

### 2. Créer des Relations

Dans SpiceDB, les relations sont représentées sous forme de tuples de relations. Chaque tuple contient une ressource, une relation et un sujet. Dans notre cas, la ressource est le nom d'un document, la relation est soit `admin`, `viewer` ou `editor`, et le sujet est le nom d'un utilisateur.

Simulons un nouveau flux de création de contenu : l'utilisateur `amine` crée un nouveau document `doc1` et en devient l'`admin`, ce qui signifie qu'il peut tout faire sur `doc1` (voir, éditer et supprimer). L'utilisateur `jake` obtient le rôle `viewer` pour `doc1` :

```bash
zed relationship touch document:doc1 admin user:amine
zed relationship touch document:doc1 viewer user:jake
```

Vous pouvez également utiliser l'API REST. Pour ajouter l'utilisateur `evan` comme `editor` de `doc1` :

```bash
curl --location 'http://<SpiceDB_IP>:8443/v1/relationships/write' \
--header 'Content-Type: application/json' \
--header 'Accept: application/json' \
--header 'Authorization: Bearer <preshared_key>' \
--data '{
    "updates": [
        {
            "operation": "OPERATION_TOUCH",
            "relationship": {
                "resource": {
                    "objectType": "document",
                    "objectId": "doc1"
                },
                "relation": "editor",
                "subject": {
                    "object": {
                        "objectType": "user",
                        "objectId": "evan"
                    }
                }
            }
        }
    ]
}'

# sortie :
# {"writtenAt":{"token":"GhUKEzE3NTgxMjk3MDg2NTc4MDQ5ODk="}}
```

### 3. Vérifier les Permissions

Pour vérifier que le schéma fonctionne correctement, émettez des requêtes de vérification de permissions. Comme `jake` est uniquement `viewer` pour `doc1`, nous attendons qu'il ait la permission `view` mais pas `edit` ou `remove` :

```bash
zed permission check document:doc1 view user:jake
# sortie : true
zed permission check document:doc1 edit user:jake
# sortie : false
```

Vous pouvez également vérifier les permissions via l'API REST. Vérifions que `jake` n'a pas la permission `remove` sur `doc1` :

```bash
curl --location 'http://<client IP>:8443/v1/permissions/check' \
--header 'Content-Type: application/json' \
--header 'Accept: application/json' \
--header 'Authorization: Bearer <preshared_key>' \
--data '{
  "consistency": {
    "minimizeLatency": true
  },
  "resource": {
    "objectType": "document",
    "objectId": "doc1"
  },
  "permission": "remove",
  "subject": {
    "object": {
      "objectType": "user",
      "objectId": "jake"
    }
  }
}'

# sortie :
# {"checkedAt":{"token":"GhUKEzE3NTgxMjk5NTAwMDAwMDAwMDA="}, "permissionship":"PERMISSIONSHIP_NO_PERMISSION"}
```

À l'inverse, comme `amine` est `admin`, nous attendons qu'il ait toutes les permissions :

```bash
zed permission check document:doc1 view user:amine
# sortie : true
zed permission check document:doc1 remove user:amine
# sortie : true
zed permission check document:doc1 edit user:amine
# sortie : true
```

### 4. Accéder aux Données AuthZed avec CockroachDB SQL

Dans votre client SQL CockroachDB, exécutez la requête suivante pour vérifier l'accessibilité du schéma AuthZed dans CockroachDB :

```sql
SELECT namespace, serialized_config FROM public.namespace_config;
```

Le jeu de résultats contient des données sur le schéma de permissions :

```
-[ RECORD 1 ]
namespace         | document
serialized_config | \x0a08646f63756d656e74...

-[ RECORD 2 ]
namespace         | user
serialized_config | \x0a04757365722200

Time: 4ms total (execution 4ms / network 0ms)
```

Exécutez ensuite la requête suivante pour vérifier l'accessibilité des données de contrôle d'accès AuthZed via CockroachDB :

```sql
SELECT namespace, object_id, relation, userset_namespace, userset_object_id, timestamp, expires_at
FROM public.relation_tuple;
```

Le jeu de résultats contient les données de permissions correspondant aux tuples de relations créés :

```
  namespace | object_id | relation | userset_namespace | userset_object_id |         timestamp          | expires_at
------------+-----------+----------+-------------------+-------------------+----------------------------+-------------
  document  | doc1      | admin    | user              | amine             | 2026-01-06 18:28:21.12613  | NULL
  document  | doc1      | editor   | user              | evan              | 2026-01-06 18:29:40.131476 | NULL
  document  | doc1      | viewer   | user              | jake              | 2026-01-06 18:28:23.226998 | NULL
(3 rows)

Time: 4ms total (execution 3ms / network 0ms)
```

---

## Prochaines Étapes

Les tests ci-dessus confirment que chaque composant AuthZed de ce déploiement est correctement connecté en utilisant CockroachDB comme couche de données partagée. Vous pouvez maintenant commencer à construire des fonctionnalités d'autorisation et de contrôle d'accès avec CockroachDB et AuthZed.

## Voir Aussi

- [Documentation AuthZed](https://authzed.com/docs/)
- [SpiceDB GitHub](https://github.com/authzed/spicedb)
- [CockroachDB Cloud](https://cockroachlabs.cloud/)
- [Déployer CockroachDB sur AWS EC2](https://www.cockroachlabs.com/docs/stable/deploy-cockroachdb-on-aws)
