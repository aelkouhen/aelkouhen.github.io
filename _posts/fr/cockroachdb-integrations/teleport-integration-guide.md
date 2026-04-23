---
date: 2026-04-23
layout: post
lang: fr
title: "Intégrer CockroachDB avec Teleport"
subtitle: "Guide pas-à-pas pour déployer Teleport Enterprise avec CockroachDB comme backend d'accès distribué mondialement et fortement cohérent"
cover-img: /assets/img/cover-teleport-integration.webp
thumbnail-img: /assets/img/cover-teleport-integration.webp
share-img: /assets/img/cover-teleport-integration.webp
tags: [integrations, CockroachDB, teleport, iam, kubernetes, security, zero-trust]
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

[Teleport](https://goteleport.com/) est une autorité de certification et un proxy d'accès orienté identité qui implémente des protocoles tels que SSH, RDP, HTTPS, l'API Kubernetes, ainsi qu'une variété de protocoles de bases de données SQL et NoSQL. Il est totalement transparent pour les outils côté client et conçu pour s'intégrer à l'ensemble de l'écosystème DevOps actuel. Couplé à CockroachDB comme datastore persistant, il offre une plateforme d'accès à l'infrastructure entièrement scalable et résiliente, capable de fonctionner sur plusieurs régions sans migrations de données complexes ni point de défaillance unique.

---

## Qu'est-ce que Teleport ?

Teleport est un plan d'accès qui consolide et sécurise l'accès à tous les types d'environnements d'infrastructure. Il est conçu pour remplacer un assemblage hétéroclite de bastions SSH, VPNs, fournisseurs d'identité et proxies d'accès, tout en fournissant une plateforme unique et unifiée.

<img src="/assets/img/teleport-identity-platform.png" alt="Plateforme d'identité Teleport" style="width:100%;margin:1.5rem 0;">

{: .mx-auto.d-block :}
**Plateforme d'identité Teleport.**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

### Authentification par Certificat

L'authentification par certificat est la forme d'authentification la plus sécurisée, mais historiquement aussi la plus complexe à gérer. Teleport automatise de manière sécurisée l'émission de certificats, rendant cette authentification simple. Teleport opère plusieurs autorités de certification (CA) internes. Chaque certificat sert à prouver l'identité, l'appartenance au cluster et à gérer les accès. Les administrateurs peuvent configurer une durée de vie (TTL) pour les certificats et effectuer des rotations de CA pour invalider les certificats précédemment émis.

Les clients s'authentifient auprès de Teleport et reçoivent un certificat client qui fonctionne automatiquement pour toutes les ressources protégées. Après authentification, les commandes `ssh`, `kubectl`, `psql`, `mysql` et autres sont configurées avec l'identité de l'utilisateur. Teleport propose une base d'utilisateurs intégrée et peut s'intégrer, en production, avec des SSO d'entreprise basés sur Okta, GitHub, Google Workspace, Active Directory et autres fournisseurs d'identité.

### Pourquoi Teleport ?

Teleport offre :

- Accès basé sur l'identité avec SSO (SAML, OIDC, GitHub, etc.)
- Certificats à courte durée de vie pour tous les accès (pas de clés statiques ni de mots de passe)
- Audit complet de toute l'activité, y compris les enregistrements de sessions
- Politiques RBAC et ABAC pour un contrôle d'accès à granularité fine
- Support multi-protocoles : SSH, Kubernetes, bases de données (PostgreSQL, MySQL, MongoDB, CockroachDB), applications web internes, et Windows RDP

L'architecture de Teleport est conçue de fond en comble pour sécuriser l'accès à l'infrastructure dans des environnements dynamiques et distribués. Son architecture à agents minimaux s'appuie sur des protocoles standard comme SSH et HTTPS, simplifiant le déploiement et éliminant le besoin de logiciels supplémentaires sur les systèmes cibles. Grâce à l'authentification par certificat et à la rotation automatique des CA, elle supprime les risques liés aux identifiants à longue durée de vie.

L'architecture de Teleport est construite avec la **Sécurité Zero Trust** comme principe fondateur, un modèle qui ne suppose aucune confiance implicite, même au sein du périmètre réseau. Au lieu de s'appuyer sur des adresses IP, des VPNs ou des sous-réseaux de confiance, chaque requête vers l'infrastructure est authentifiée et autorisée uniquement sur la base de l'identité et du rôle de l'utilisateur.

---

## Architecture de Teleport

<img src="/assets/img/teleport-architecture.png" alt="Architecture Teleport" style="width:100%;margin:1.5rem 0;">

{: .mx-auto.d-block :}
**Architecture Teleport.**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Le concept clé de l'architecture de Teleport est le **cluster**. Les utilisateurs et les serveurs doivent tous rejoindre le même cluster avant qu'un accès puisse être accordé. Pour rejoindre un cluster, les deux parties doivent s'authentifier. Ce modèle empêche les attaques de type honeypot et élimine le problème de confiance au premier usage. Les clusters Teleport peuvent être configurés pour se faire mutuellement confiance, permettant aux utilisateurs d'une organisation d'accéder à des serveurs désignés dans l'environnement d'une autre.

Un cluster Teleport se compose des éléments suivants :

<img src="/assets/img/teleport-cluster-animation.gif" alt="Composants du cluster Teleport" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**Composants du cluster Teleport**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

### Service d'Authentification Teleport (Auth Service)

L'autorité de certification du cluster. Il émet des certificats aux utilisateurs et aux services Teleport, et maintient un journal d'audit. Ses responsabilités clés comprennent :

- La gestion des définitions d'utilisateurs et de rôles
- L'émission de certificats à courte durée de vie pour l'authentification des utilisateurs et des services
- Le stockage des événements de session, des demandes d'accès et des journaux d'audit
- La fonction d'API pour l'enregistrement des ressources et les décisions d'accès

Étant stateful et piloté par des politiques, le serveur d'authentification s'appuie sur des backends de stockage durables et cohérents. Dans les déploiements multi-régions, ces backends doivent être distribués, hautement disponibles tout en préservant la cohérence forte. C'est là que CockroachDB devient un facteur clé, garantissant que l'état du serveur d'authentification est globalement cohérent et répliqué entre les géographies.

### Service Proxy Teleport

Permet l'accès aux ressources du cluster depuis l'extérieur. Il est généralement le seul service accessible depuis le réseau public. Il achemine le trafic client vers et depuis les ressources de votre infrastructure :

- Effectue le tunneling inverse vers les nœuds internes
- Proxifie le trafic SSH, Kubernetes, bases de données, applications et Windows RDP
- Applique MFA et l'intégration SSO
- Journalise les sessions pour audit et rejeu

Cette conception assure un accès sans agent, via navigateur ou CLI, depuis n'importe où dans le monde, sans accès entrant ni VPN.

### Agents Teleport

Un Agent Teleport s'exécute dans le même réseau qu'une ressource cible et parle son protocole natif. Chaque agent connecte un type spécifique d'infrastructure au cluster :

- **node agent** : connecte les serveurs Linux via SSH
- **kube agent** : intègre les clusters Kubernetes via l'API Kubernetes
- **db agent** : donne accès aux bases de données SQL/NoSQL comme PostgreSQL, MySQL et CockroachDB
- **app agent** : expose des applications HTTP internes derrière SSO sécurisé et audit de sessions
- **windows agent** : permet l'accès aux serveurs Windows via RDP (Enterprise)

### Accès pour les Réseaux Edge

Teleport permet aux utilisateurs d'accéder à des ressources situées n'importe où dans le monde, y compris sur des réseaux tiers, des serveurs derrière NAT, ou des appareils connectés via une connexion cellulaire.

<img src="/assets/img/teleport-remote-nodes.png" alt="Nœuds distants Teleport via tunnel inverse" style="width:100%;margin:1.5rem 0;">

{: .mx-auto.d-block :}
**Nœuds distants Teleport via tunnel inverse**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

La technologie sous-jacente est le tunnel inverse, une connexion sécurisée établie par un site edge vers un cluster Teleport via le proxy du cluster. Cette approche adhère aux principes Zero Trust, où les réseaux, y compris les VPN, sont considérés comme intrinsèquement non fiables.

### Journal d'Audit

Le service d'authentification Teleport maintient un journal d'audit de toute l'activité dans le cluster, composé de deux éléments :

- **Le journal d'audit** : enregistrements JSON bien documentés des événements de sécurité (tentatives de connexion, transferts de fichiers, exécutions de code, activité réseau).
- **Sessions enregistrées** : enregistrements des sessions interactives établies via `ssh`, `RDP` et `kubectl exec`. Les sessions peuvent être rejouées via une interface web avec pause et retour arrière.

---

## Architecture Conjointe Teleport + CockroachDB

Pour répondre aux exigences de niveau Tier 0, Teleport et CockroachDB offrent une valeur ajoutée conjointe pour la résilience et la cohérence multi-régions. Cette architecture permet des déploiements actif-actif de Teleport, garantissant que l'infrastructure d'accès peut survivre à des partitions réseau, des défaillances de nœuds et une charge mondiale, sans compromettre la sécurité ni la conformité.

<img src="/assets/img/teleport-crdb-architecture.png" alt="Architecture conjointe multi-régions Teleport et CockroachDB" style="width:100%;margin:1.5rem 0;">

{: .mx-auto.d-block :}
**Architecture conjointe multi-régions Teleport et CockroachDB**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Chaque composant Teleport s'appuie sur CockroachDB pour stocker son état de manière cohérente et durable, permettant un fonctionnement correct même en présence de pannes partielles ou de partitions réseau régionales. Le service d'authentification Teleport est particulièrement bien adapté à CockroachDB en raison de sa conception sans état et de sa philosophie API-first : chaque service peut être déployé de manière stateless, avec pour seul prérequis de persistance la base de données SQL sous-jacente.

<img src="/assets/img/teleport-crdb-distributed-sql.png" alt="Fondation SQL distribuée CockroachDB" style="width:100%;margin:1.5rem 0;">

{: .mx-auto.d-block :}
**Fondation SQL distribuée CockroachDB**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

CockroachDB est une base de données SQL distribuée conçue pour l'échelle mondiale et la haute disponibilité. Elle réplique les données sur plusieurs régions tout en offrant l'isolation sérialisable, la cohérence forte et le basculement automatique. Teleport supporte officiellement CockroachDB comme backend de stockage pour de bonnes raisons :

- **Support multi-régions intégré** : conçu pour les déploiements géographiquement distribués
- **Haute disponibilité** : maintient la cohérence et les garanties de disponibilité même lors de partitions réseau
- **Scalabilité horizontale** : montée en charge des lectures et écritures sans sharding ni intervention manuelle
- **Cohérence des données** : la cohérence forte par défaut garantit la fiabilité de l'état du cluster Teleport dans toutes les régions

---

## Configurer un Environnement Conjoint CockroachDB/Teleport

Ce guide présente une implémentation concrète de niveau production utilisant Teleport et CockroachDB dans un déploiement multi-régions. Dans cette architecture, CockroachDB joue deux rôles distincts :

1. **Backend de stockage Teleport** : persistance de l'état du contrôle d'accès, des métadonnées d'identité et des informations de session.
2. **Ressource protégée par Teleport** : l'accès au cluster CockroachDB lui-même est sécurisé via le Database Service de Teleport.

### Prérequis

Pour exécuter un déploiement Teleport multi-régions, vous devez disposer de :

- 3 VPCs régionaux avec peering (ex. AWS) ou 1 VPC global (ex. Google Cloud)
- 1 cluster Kubernetes par région avec des **CIDRs de pods non-chevauchants**
- Un fichier de licence Teleport Enterprise
- Un nom de domaine enregistré et un sous-domaine par région (requis pour la vérification TLS)
- Connectivité mesh entre pods : les instances du Proxy Service Teleport doivent pouvoir se contacter sur le port 3021
- Un GeoDNS (ex. Route53) avec une politique de routage par proximité géographique
- Un cluster CockroachDB multi-régions
- Les outils `tctl` et `tsh` installés sur un hôte client

### Étape 1. Provisionner un Cluster CockroachDB

Choisissez l'une des méthodes suivantes pour créer un nouveau cluster CockroachDB, ou utilisez un cluster existant et passez à l'étape 2.

> **Note :** Créez impérativement un cluster **sécurisé**. C'est nécessaire pour les étapes suivantes de ce tutoriel.

**Créer un cluster sécurisé localement** : si vous avez le binaire CockroachDB installé localement, vous pouvez déployer manuellement un cluster multi-nœuds autohébergé sur votre machine.

**Créer un cluster CockroachDB autohébergé sur AWS** : déployez un cluster multi-nœuds sur Amazon EC2 en utilisant le service de load-balancing géré d'AWS.

**Créer un cluster CockroachDB Cloud** : CockroachDB Cloud est un service entièrement géré par Cockroach Labs. [Inscrivez-vous](https://cockroachlabs.cloud/) et créez un cluster avec des crédits d'essai.

### Étape 2. Configurer CockroachDB comme Backend de Stockage pour Teleport

Connectez-vous à votre client SQL CockroachDB :

```bash
cockroach sql --certs-dir={certs-dir} --host={crdb-fqdn}:26257
```

Créez la base de données, l'utilisateur et les privilèges :

```sql
CREATE DATABASE teleport_backend;
CREATE USER teleport;
GRANT ALL ON DATABASE teleport_backend TO teleport;
```

Déclarez les zones et régions, et configurez la tolérance aux pannes régionales :

```sql
ALTER DATABASE teleport_backend SET PRIMARY REGION <region1>;
ALTER DATABASE teleport_backend ADD REGION IF NOT EXISTS <region2>;
ALTER DATABASE teleport_backend ADD REGION IF NOT EXISTS <region3>;
ALTER DATABASE teleport_backend SET SECONDARY REGION <region2>;
ALTER DATABASE teleport_backend SURVIVE REGION FAILURE;
```

> **Note :** Si les régions primaire et secondaire sont éloignées l'une de l'autre (ex. sur des continents différents), cela ralentira les opérations d'écriture CockroachDB.

Signez un certificat pour l'utilisateur `teleport` :

```bash
cockroach cert create-ca --certs-dir=~/certs --ca-key=~/my-safe-directory/ca.key
cockroach cert create-client teleport --certs-dir=~/certs --ca-key=~/my-safe-directory/ca.key
```

Vous obtiendrez trois fichiers nécessaires à l'étape 3 : `client.teleport.crt`, `client.teleport.key` et `ca.crt`.

### Étape 3. Déployer Teleport sur Kubernetes

Ajoutez le dépôt Helm Teleport :

```bash
helm repo add teleport https://charts.releases.teleport.dev
helm repo update
```

Créez le namespace `teleport` et enregistrez les certificats CockroachDB comme secret Kubernetes :

```bash
kubectl create namespace teleport --dry-run=client -o yaml | kubectl apply -f -
kubectl config set-context --current --namespace teleport
kubectl create secret generic cockroach-certs \
  --from-file=ca.crt=~/certs/ca.crt \
  --from-file=client.teleport.crt=~/certs/client.teleport.crt \
  --from-file=client.teleport.key=~/certs/client.teleport.key \
  -n teleport --dry-run=client -o yaml | kubectl apply -f -
```

Pour exécuter Teleport Enterprise, vous avez besoin d'un fichier de licence. Rendez-vous sur votre tableau de bord de compte Teleport pour en générer un :

<img src="/assets/img/teleport-license-generate.png" alt="Génération de licence Teleport" style="width:80%;display:block;margin:1.5rem auto;">

{: .mx-auto.d-block :}
**Génération de licence Teleport**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Créez le secret de licence :

```bash
kubectl -n teleport create secret generic license --from-file=~/license.pem
```

Déployez Teleport via le chart Helm `teleport-cluster` (créez un fichier de valeurs par cluster Kubernetes régional) :

```yaml
chartMode: standalone
clusterName: ${CLUSTER_NAME}
enterprise: true
persistence:
  enabled: false

auth:
  teleportConfig:
    teleport:
      storage:
        type: cockroachdb
        conn_string: postgres://teleport@${CRDB_FQDN}:26257/teleport_backend?pool_max_conns=20&sslmode=verify-full&sslcert=/var/lib/db-certs/client.teleport.crt&sslkey=/var/lib/db-certs/client.teleport.key&sslrootcert=/var/lib/db-certs/ca.crt

    auth_service:
      enabled: yes
      listen_addr: 0.0.0.0:3025
      cluster_name: ${CLUSTER_NAME}
      proxy_listener_mode: multiplex
    ssh_service:
      enabled: yes
    proxy_service:
      enabled: yes
      web_listen_addr: 0.0.0.0:443
      public_addr: ${CLUSTER_NAME}:443

  extraVolumes:
    - name: db-certs
      secret:
        secretName: cockroach-certs
        defaultMode: 0600
  extraVolumeMounts:
    - name: db-certs
      mountPath: /var/lib/db-certs
      readOnly: true

highAvailability:
  replicaCount: 2
  requireAntiAffinity: true
```

Installez le chart :

```bash
helm upgrade --install teleport-cluster teleport/teleport-cluster --namespace teleport -f ~/values_teleport_us-east.yaml
```

Après une minute, vérifiez que les pods du Auth Service et du Proxy Service sont en cours d'exécution :

```bash
kubectl -n teleport get pods

# NAME                                          READY   STATUS    RESTARTS   AGE
# pod/teleport-cluster-auth-7bd79b87dc-gp5r5    1/1     Running   0          16m
# pod/teleport-cluster-auth-7bd79b87dc-kqm4h    1/1     Running   0          15m
# pod/teleport-cluster-proxy-5945bf8c4b-qpmfp   1/1     Running   0          32m
```

<img src="/assets/img/teleport-k8s-cluster.png" alt="Cluster Teleport fonctionnant sur Kubernetes" style="width:100%;margin:1.5rem 0;">

{: .mx-auto.d-block :}
**Cluster Teleport fonctionnant sur Kubernetes**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

### Étape 4. Configurer les Enregistrements DNS

Le chart Helm `teleport-cluster` expose le Proxy Service via un service Kubernetes qui configure un load balancer externe avec votre fournisseur cloud.

Obtenez l'adresse du load balancer :

```bash
kubectl get services/teleport-cluster
```

Pour chaque région, créez deux enregistrements DNS :

- Un enregistrement CNAME `<region>.teleport.example.com` pointant vers le domaine de votre load balancer
- Un CNAME wildcard `*.<region>.teleport.example.com` pour les applications web enregistrées dans Teleport

Vérifiez que le cluster fonctionne :

```bash
curl https://<region>.teleport.example.com/webapi/ping
```

Testez ensuite que Teleport utilise bien CockroachDB comme backend en inspectant le schéma :

```bash
cockroach sql --url postgresql://teleport@{crdb-fqdn}:26257/teleport_backend --certs-dir={certs-dir}
```

```sql
SHOW TABLES;
```

```
schema_name |   table_name    | type  |  owner   | estimated_row_count
------------+-----------------+-------+----------+--------------------
public      | backend_version | table | teleport |                   0
public      | kv              | table | teleport |                  71
(2 rows)
```

Teleport crée deux tables : `backend_version` (version du cluster et timestamp de création) et `kv` (métadonnées de gestion des accès sous forme de clé-valeur avec timestamps d'expiration et révisions).

### Étape 5. Configurer le Database Service Teleport

Teleport peut fournir un accès sécurisé à CockroachDB via le Teleport Database Service, permettant un contrôle d'accès à granularité fine via le système RBAC de Teleport. Le Database Service s'authentifie auprès de CockroachDB en utilisant le TLS mutuel, éliminant le besoin d'identifiants à longue durée de vie.

<img src="/assets/img/teleport-db-service-agent.png" alt="Architecture de l'agent Database Service Teleport" style="width:100%;margin:1.5rem 0;">

{: .mx-auto.d-block :}
**Architecture de l'agent Database Service Teleport**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Générez un token de jonction pour le Database Agent :

```bash
tctl tokens add --type=db --format=text
# abcd123-insecure-do-not-use-this
```

Installez le Teleport Kube Agent avec la configuration du Database Service :

```yaml
roles: db
proxyAddr: {CLUSTER_NAME}:443
enterprise: true
authToken: {AUTH_TOKEN}
joinParams:
  method: token

databases:
- name: roach
  uri: {CRDB_FQDN}:26257
  protocol: cockroachdb
  tls:
    mode: verify-full
    ca_cert_file: /var/lib/db-certs/ca.crt

extraVolumes:
  - name: db-certs
    secret:
      secretName: cockroach-certs
      defaultMode: 0600
extraVolumeMounts:
  - name: db-certs
    mountPath: /var/lib/db-certs
    readOnly: true
```

### Étape 6. Créer un Utilisateur Teleport

Teleport utilise l'authentification mTLS avec CockroachDB. Créez d'abord un utilisateur de base de données avec authentification par certificat uniquement :

```sql
CREATE USER danielle WITH PASSWORD NULL;
```

> **Note :** La clause `WITH PASSWORD NULL` empêche l'authentification par mot de passe et impose l'authentification par certificat client.

Créez maintenant un utilisateur Teleport local avec les rôles access et requester :

```bash
tctl users add danielle --roles=access,requester --db-users="*" --db-names="*"
```

Vous recevrez un lien d'invitation pour finaliser la configuration de l'utilisateur :

<img src="/assets/img/teleport-user-setup-form.png" alt="Formulaire de configuration utilisateur Teleport" style="width:60%;display:block;margin:1.5rem auto;">

{: .mx-auto.d-block :}
**Formulaire de configuration utilisateur Teleport**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Associez ensuite une application d'authentification en scannant le QR code généré :

<img src="/assets/img/teleport-mfa-setup.png" alt="Configuration MFA Teleport par QR code" style="width:60%;display:block;margin:1.5rem auto;">

{: .mx-auto.d-block :}
**Configuration MFA Teleport par QR code**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

### Étape 7. Configurer le TLS Mutuel

Pour finaliser la configuration mTLS, les nœuds CockroachDB doivent faire confiance à la CA `db_client` de Teleport afin que les utilisateurs Teleport puissent s'authentifier comme clients de base de données.

Copiez votre certificat CA CockroachDB et ajoutez-y la CA `db_client` de Teleport :

```bash
cp ~/certs/ca.crt ~/certs/ca-client.crt
tctl auth export --type=db-client >> ~/certs/ca-client.crt
```

Copiez `ca-client.crt` sur chaque nœud CockroachDB et rechargez les certificats sans redémarrage :

```bash
pkill -SIGHUP -x cockroach
```

> **Note :** Envoyez le signal SIGHUP en tant que même utilisateur qui a démarré le processus `cockroach`.

> **Avertissement :** Ne faites pas tourner ou remplacer une CA CockroachDB existante en production.

### Étape 8. Se Connecter

Connectez-vous à votre cluster Teleport et vérifiez l'accès aux bases de données :

```bash
tsh login --proxy=us-east.teleport.example.com --user=danielle
tsh db ls
```

Connectez-vous directement au cluster CockroachDB via Teleport :

```bash
tsh db connect --db-user=danielle roach
```

Vous pouvez également accéder à vos bases de données CockroachDB via l'interface Web de Teleport :

<img src="/assets/img/teleport-web-ui.png" alt="Interface Web Teleport donnant accès à CockroachDB" style="width:100%;margin:1.5rem 0;">

{: .mx-auto.d-block :}
**Interface Web Teleport donnant accès à CockroachDB**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

---

## Prochaines Étapes

Les tests ci-dessus confirment que chaque composant Teleport de ce déploiement est correctement connecté en utilisant CockroachDB comme couche de données partagée. Ensemble, ils permettent des systèmes d'accès à l'infrastructure qui restent corrects et disponibles, même en cas de panne régionale ou de partition réseau. Vous pouvez maintenant commencer à construire un contrôle d'accès à granularité fine sur vos actifs d'infrastructure avec CockroachDB et Teleport.

## Voir Aussi

- [Documentation Teleport](https://goteleport.com/docs/)
- [Charts Helm Teleport](https://github.com/gravitational/teleport/tree/master/examples/chart)
- [CockroachDB Cloud](https://cockroachlabs.cloud/)
- [Déployer CockroachDB sur AWS EC2](https://www.cockroachlabs.com/docs/stable/deploy-cockroachdb-on-aws)
- [CockroachDB Distributed SQL](https://www.cockroachlabs.com/blog/what-is-distributed-sql/)
