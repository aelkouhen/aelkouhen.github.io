---
layout: post
lang: fr
title: "Intégrer CockroachDB avec Ory"
subtitle: "Guide pas-à-pas pour déployer Ory Hydra, Kratos et Keto avec CockroachDB"
thumbnail-img: /assets/img/integrate-ory-architecture-overview.png
share-img: /assets/img/integrate-ory-architecture-overview.png
tags: [integrations, CockroachDB, ory, iam, kubernetes, oauth2, OIDC, identity]
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

[Ory](https://www.ory.sh/) est une plateforme open-source de gestion des identités et des accès (IAM) fournissant des composants modulaires et cloud-natifs pour l'authentification et l'autorisation dans les systèmes distribués. Associée à CockroachDB comme couche de persistance, cette combinaison offre une infrastructure IAM entièrement scalable et résiliente, capable d'opérer sur plusieurs régions sans migrations de données complexes ni point de défaillance unique.

Ce tutoriel présente un déploiement complet des trois services Ory — Hydra, Kratos et Keto — sur Kubernetes (AWS EKS), appuyé par un cluster CockroachDB sécurisé, avec vérification SQL de chaque enregistrement IAM stocké.

---

## Composants Principaux

La plateforme Ory est composée de trois services indépendants et sans état — chacun gérant une couche distincte de la pile IAM :

| Service | Responsabilité |
|---------|---------------|
| **Ory Hydra** | Serveur d'autorisation OAuth2 et fournisseur OpenID Connect |
| **Ory Kratos** | Gestion des identités — utilisateurs, credentials, sessions, vérifications |
| **Ory Keto** | Contrôle d'accès basé sur les relations (ReBAC) via des tuples de relations |

Le diagramme suivant illustre les relations entre Ory Hydra, Kratos et Keto :

<img src="/assets/img/integrate-ory-architecture-overview.png" alt="Services Ory" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**Services Ory**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Chaque service étant sans état, toute la persistance réside dans CockroachDB. La mise à l'échelle horizontale, les mises à jour progressives et les déploiements multi-régions deviennent simples — sans sessions collantes ni caches distribués à coordonner.

---

### Ory Hydra

Ory Hydra est une implémentation serveur du [framework d'autorisation OAuth 2.0](https://oauth.net/2/) et des spécifications [OpenID Connect Core 1.0](https://openid.net/connect/). Il suit les clients, les demandes de consentement et les tokens avec cohérence forte pour prévenir les attaques par rejeu et les autorisations dupliquées.

Le framework OAuth 2.0 permet aux applications tierces d'obtenir un accès limité aux services HTTP au nom des propriétaires de ressources ou de manière indépendante.

<img src="/assets/img/integrate-ory-oauth2-flow.png" alt="Diagramme du flux OAuth 2.0" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**Diagramme du flux OAuth 2.0**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Ce diagramme de séquence illustre le flux d'autorisation OAuth 2.0 sous forme de requêtes et de réponses, en utilisant Ory Hydra comme serveur d'autorisation :

<img src="/assets/img/integrate-ory-hydra-flow.png" alt="Flux d'autorisation Ory Hydra" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**Flux d'autorisation Ory Hydra**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Le diagramme représente les interactions entre quatre composants clés :

- **Client** — une application cherchant à accéder à des ressources protégées
- **Propriétaire de la ressource** — l'utilisateur final
- **Ory Hydra** — le serveur d'autorisation
- **Serveur de ressources** — l'API ou le service hébergeant les ressources protégées

Le flux commence lorsque le Client demande une autorisation au Propriétaire de la ressource, généralement via une redirection vers un écran de connexion ou de consentement fourni par Ory Hydra. Après approbation, le Propriétaire de la ressource fournit un grant d'autorisation au Client.

Le Client utilise ce grant pour demander un token d'accès à Hydra, en s'authentifiant avec son Client ID et son secret. Hydra valide le grant et les credentials, puis émet un token d'accès.

Avec le token d'accès, le Client demande les ressources protégées au Serveur de ressources, présentant le token comme preuve d'autorisation. Le Serveur de ressources valide le token par introspection ou vérification de signature (dans le cas d'un JWT) et sert la ressource demandée.

CockroachDB stocke tous les clients OAuth2, les codes d'autorisation, les tokens d'accès et les sessions de consentement — durablement et avec cohérence linéarisable.

---

### Ory Kratos

Ory Kratos stocke les enregistrements d'identité utilisateur, les flux de récupération, les sessions et les tentatives de connexion dans des tables transactionnelles. Chaque identité est associée à un ou plusieurs credentials stockés dans la table `identity_credentials`, définissant les mécanismes d'authentification tels que les mots de passe, la connexion sociale ou d'autres méthodes.

Kratos permet aux utilisateurs de s'inscrire et de gérer leur profil sans intervention administrative, en implémentant :

- Inscription et Connexion / Déconnexion
- Paramètres utilisateur
- Récupération de compte
- Vérification d'adresse
- 2FA / MFA
- Gestion des erreurs côté utilisateur

<img src="/assets/img/integrate-ory-kratos-registration.png" alt="Flux d'inscription Ory Kratos" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**Flux d'inscription Ory Kratos**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Chaque enregistrement d'identité utilisateur est stocké dans des tables transactionnelles CockroachDB :

- **`identities`** — enregistrement d'identité principal avec schéma et état
- **`identity_credentials`** — mots de passe, connexions sociales et autres méthodes d'authentification
- **`sessions`** — tokens de session actifs et données d'expiration
- **`verification_tokens`** — flux de vérification email/téléphone

---

### Ory Keto

Ory Keto fournit un contrôle d'accès basé sur les relations (ReBAC) scalable via des tuples de relations — le même modèle utilisé par [Google Zanzibar](https://research.google/pubs/pub48190/).

L'autorisation est vérifiée en évaluant si un tuple de relation existe (directement ou via une expansion récursive) permettant à un sujet d'effectuer une relation sur un objet dans un namespace. Ce modèle de données permet une haute scalabilité et flexibilité pour des schémas d'accès complexes incluant l'appartenance à des groupes, l'héritage de rôles et les droits d'accès hiérarchiques.

Les vérifications de permissions sont répondues sur la base de :

- **Données disponibles dans CockroachDB** — ex. « l'utilisateur Bob est propriétaire du document X »
- **Règles de permission** — ex. « tous les propriétaires d'un document peuvent le consulter »

À la question « L'utilisateur Bob est-il autorisé à voir le document X ? », le système vérifie la permission de vue de Bob et confirme sa propriété. Le modèle de permission indique à Ory Keto quoi vérifier.

<img src="/assets/img/integrate-ory-permission-graph.png" alt="Graphe de permissions Ory Keto" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**Graphe de permissions Ory Keto**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

---

## Pourquoi CockroachDB ?

Chaque service Ory nécessite une base de données fiable et cohérente. Les propriétés de CockroachDB répondent directement aux exigences IAM :

- **Isolation sérialisable** — empêche la double dépense sur les tokens et les consentements dupliqués
- **Actif-actif multi-régions** — les services Ory dans n'importe quelle région peuvent écrire sur le même cluster logique
- **Scalabilité horizontale** — les tables de tokens croissent avec votre base d'utilisateurs sans re-sharding
- **Résilience** — la réplication automatique basée sur Raft tolère transparentement les pannes de nœuds et de zones

---

## Architecture de l'Intégration

L'intégration combine trois composants Ory, chacun opérant comme un service sans état adossé à CockroachDB :

| Service | Stocke |
|---------|--------|
| **Ory Hydra** | Clients OAuth2, sessions de consentement, tokens |
| **Ory Kratos** | Identités, credentials, sessions, tokens de vérification |
| **Ory Keto** | Tuples de relations pour les permissions RBAC/ABAC |

<img src="/assets/img/integrate-ory-single-region.svg" alt="Architecture Ory + CockroachDB sur une seule région" style="width:100%;margin:1.5rem 0;">
{: .mx-auto.d-block :}
**Architecture Ory + CockroachDB sur une seule région**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Ce diagramme illustre un déploiement sur une seule région cloud répartie sur trois zones de disponibilité : `us-east-1a`, `us-east-1b` et `us-east-1c`.

- **VPC Ory** — cluster Amazon EKS avec nœuds workers distribués entre les zones, exécutant les pods Hydra, Kratos et Keto avec routage ingress et service
- **VPC CRDB** — nœuds CockroachDB sur les zones formant un cluster logique unique utilisant le consensus Raft pour la réplication des données
- **Network Load Balancer** — achemine le trafic vers les nœuds sains avec basculement automatique

---

### Prérequis

- Compte AWS avec permissions EKS et EC2
- Profil AWS CLI configuré
- Installés : Terraform, kubectl, eksctl et Helm (v3+)
- Connaissances de base de Kubernetes
- (Optionnel) Domaine et configuration DNS pour l'exposition publique
- **Temps d'installation estimé :** 45–60 minutes

---

### Étape 1 : Provisionner un Cluster CockroachDB

Choisissez l'une des méthodes de déploiement :

- **Local** — cluster auto-hébergé multi-nœuds avec le binaire CockroachDB
- **AWS EC2** — cluster auto-hébergé sur Amazon EC2 avec load-balancing AWS géré
- **CockroachDB Cloud** — service entièrement géré par Cockroach Labs avec crédits d'essai

> **Important :** Créez un cluster **sécurisé** — la création d'utilisateurs l'exige.

---

### Étape 2 : Créer les Bases de Données pour les Services Ory

Des bases de données séparées isolent les données entre les composants Ory :

- **Hydra** — gère les clients OAuth2, les sessions de consentement, les tokens d'accès/rafraîchissement
- **Kratos** — gère les identités, credentials, sessions, tokens de vérification
- **Keto** — stocke les tuples de relations (données RBAC/ABAC) pour les permissions

Connectez-vous à votre client SQL CockroachDB :

```bash
cockroach sql --certs-dir={certs-dir} --host={crdb-fqdn}:26257
```

Créez les bases de données :

```sql
CREATE DATABASE hydra;
CREATE DATABASE kratos;
CREATE DATABASE keto;
```

Créez l'utilisateur partagé et accordez les privilèges :

```sql
CREATE USER ory WITH PASSWORD 'securepass';
GRANT ALL ON DATABASE hydra TO ory;
GRANT ALL ON DATABASE kratos TO ory;
GRANT ALL ON DATABASE keto TO ory;
```

---

### Étape 3 : Provisionner un Cluster Kubernetes

Créez le cluster EKS :

```bash
eksctl create cluster \
  --region us-east-1 \
  --name ory \
  --nodegroup-name standard-workers \
  --managed=false \
  --node-type m5.xlarge \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 4 \
  --node-ami auto \
  --node-ami-family AmazonLinux2023
```

Cette commande crée trois instances EKS (m5.xlarge : 4 vCPU, 16 Go de mémoire) sur plusieurs zones. Le provisionnement prend 10–15 minutes.

Ajoutez le dépôt Helm d'Ory :

```bash
helm repo add ory https://k8s.ory.sh/helm/charts
helm repo update
```

---

### Étape 4 : Déployer les Services Ory

#### Déployer Ory Hydra

Créez `hydra_values.yaml` (remplacez `{crdb-fqdn}`) :

```yaml
image:
  repository: oryd/hydra
  tag: latest
  pullPolicy: IfNotPresent
service:
  public:
    enabled: true
    type: LoadBalancer
    port: 4444
    name: hydra-http-public
  admin:
    enabled: true
    type: LoadBalancer
    port: 4445
    name: hydra-http-admin
maester:
  enabled: false
hydra:
  dev: true
  automigration:
    enabled: true
  config:
    serve:
      public:
        port: 4444
      admin:
        port: 4445
    dsn: "cockroach://ory:securepass@{crdb-fqdn}:26257/hydra?sslmode=disable"
```

Installez et vérifiez :

```bash
helm upgrade --install ory-hydra ory/hydra --namespace ory -f hydra_values.yaml
kubectl get pods     # Pod Hydra : 1/1 Running, automigrate : Completed
kubectl get svc
```

> **Note :** N'utilisez pas le flag `--wait`.

Exportez les URLs des endpoints :

```bash
hydra_admin_hostname=$(kubectl get svc --namespace ory ory-hydra-admin \
  --template "{{ range (index .status.loadBalancer.ingress 0) }}{{.}}{{ end }}")
hydra_public_hostname=$(kubectl get svc --namespace ory ory-hydra-public \
  --template "{{ range (index .status.loadBalancer.ingress 0) }}{{.}}{{ end }}")
export HYDRA_ADMIN_URL=http://$hydra_admin_hostname:4445
export HYDRA_PUBLIC_URL=http://$hydra_public_hostname:4444
```

---

#### Déployer Ory Kratos

Créez `kratos_values.yaml` (remplacez `{crdb-fqdn}`) :

```yaml
image:
  repository: oryd/kratos
  tag: latest
  pullPolicy: IfNotPresent
service:
  admin:
    enabled: true
    type: LoadBalancer
    port: 4433
    name: kratos-http-admin
  public:
    enabled: true
    type: LoadBalancer
    port: 4434
    name: kratos-http-public
kratos:
  development: true
  automigration:
    enabled: true
  config:
    serve:
      admin:
        port: 4433
      public:
        port: 4434
    dsn: "cockroach://ory:securepass@{crdb-fqdn}:26257/kratos?sslmode=disable"
    selfservice:
      default_browser_return_url: "http://127.0.0.1/home"
    identity:
      default_schema_id: default
      schemas:
        - id: default
          url: https://cockroachdb-integration-guides.s3.us-east-1.amazonaws.com/ory/kratos-schema.json
courier:
  enabled: false
```

Installez et vérifiez :

```bash
helm upgrade --install ory-kratos ory/kratos --namespace ory -f kratos_values.yaml
kubectl get pods
kubectl get svc
```

Exportez les URLs des endpoints :

```bash
kratos_admin_hostname=$(kubectl get svc --namespace ory ory-kratos-admin \
  --template "{{ range (index .status.loadBalancer.ingress 0) }}{{.}}{{ end }}")
kratos_public_hostname=$(kubectl get svc --namespace ory ory-kratos-public \
  --template "{{ range (index .status.loadBalancer.ingress 0) }}{{.}}{{ end }}")
export KRATOS_ADMIN_URL=http://$kratos_admin_hostname:4433
export KRATOS_PUBLIC_URL=http://$kratos_public_hostname:4434
```

---

#### Déployer Ory Keto

Créez `keto_values.yaml` (remplacez `{crdb-fqdn}`) :

```yaml
image:
  repository: oryd/keto
  tag: latest
  pullPolicy: IfNotPresent
service:
  read:
    enabled: true
    type: LoadBalancer
    name: ory-keto-read
    port: 4466
    appProtocol: http
    headless:
      enabled: false
  write:
    enabled: true
    type: LoadBalancer
    name: ory-keto-write
    port: 4467
    appProtocol: http
    headless:
      enabled: false
keto:
  automigration:
    enabled: true
  config:
    serve:
      read:
        port: 4466
      write:
        port: 4467
    namespaces:
      - id: 0
        name: default_namespace
      - id: 1
        name: documents
      - id: 2
        name: users
    dsn: "cockroach://ory:securepass@{crdb-fqdn}:26257/keto?sslmode=disable"
```

Installez et vérifiez :

```bash
helm upgrade --install ory-keto ory/keto --namespace ory -f keto_values.yaml
kubectl get pods
kubectl get svc
```

Exportez les URLs des endpoints :

```bash
keto_read_hostname=$(kubectl get svc --namespace ory ory-keto-read \
  --template "{{ range (index .status.loadBalancer.ingress 0) }}{{.}}{{ end }}")
keto_write_hostname=$(kubectl get svc --namespace ory ory-keto-write \
  --template "{{ range (index .status.loadBalancer.ingress 0) }}{{.}}{{ end }}")
export KETO_WRITE_REMOTE=http://$keto_write_hostname:4467
export KETO_READ_REMOTE=http://$keto_read_hostname:4466
```

---

### Étape 5 : Tester l'Intégration

#### Tester Ory Hydra

Créez un client OAuth2 :

```bash
hydra create oauth2-client \
  --endpoint $HYDRA_ADMIN_URL \
  --format json \
  --grant-type client_credentials
```

La réponse inclut un `client_id` et un `client_secret`. Générez un token d'accès :

```bash
hydra perform client-credentials \
  --endpoint $HYDRA_PUBLIC_URL \
  --client-id {client_id} \
  --client-secret {client_secret}
```

Introspectez le token :

```bash
hydra introspect token \
  --format json-pretty \
  --endpoint $HYDRA_ADMIN_URL {access_token}
```

La réponse attendue contient `"active": true`. Vérifiez dans CockroachDB :

```sql
SELECT id, client_secret, scope, token_endpoint_auth_method, created_at
FROM public.hydra_client;

SELECT signature, client_id, subject, active, expires_at
FROM public.hydra_oauth2_access;
```

---

#### Tester Ory Kratos

Initialisez le flux d'inscription API et créez un utilisateur :

```bash
flowId=$(curl -s -X GET -H "Accept: application/json" \
  $KRATOS_PUBLIC_URL/self-service/registration/api | jq -r '.id')

curl -s -X POST \
  -H "Accept: application/json" -H "Content-Type: application/json" \
  "$KRATOS_PUBLIC_URL/self-service/registration?flow=$flowId" \
  -d '{
    "method": "password",
    "password": "HelloCockro@ch123",
    "traits": {
      "email": "max@roach.com",
      "name": { "first": "Max", "last": "Roach" }
    }
  }'
```

Connectez-vous et récupérez un token de session :

```bash
flowId=$(curl -s -X GET -H "Accept: application/json" \
  $KRATOS_PUBLIC_URL/self-service/login/api | jq -r '.id')

curl -s -X POST \
  -H "Accept: application/json" -H "Content-Type: application/json" \
  "$KRATOS_PUBLIC_URL/self-service/login?flow=$flowId" \
  -d '{"identifier": "max@roach.com", "password": "HelloCockro@ch123", "method": "password"}'
```

Vérifiez la session active :

```bash
curl -s -X GET \
  -H "Accept: application/json" \
  -H "Authorization: Bearer {session_token}" \
  $KRATOS_PUBLIC_URL/sessions/whoami
```

Déconnectez-vous :

```bash
curl -s -X DELETE \
  -H "Accept: application/json" -H "Content-Type: application/json" \
  $KRATOS_PUBLIC_URL/self-service/logout/api \
  -d '{"session_token": "{session_token}"}'
```

Vérifiez l'identité dans CockroachDB :

```sql
SELECT i.id, i.schema_id, i.traits, i.created_at, ict.name AS identity_type
FROM public.identities i
JOIN public.identity_credentials ic ON i.id = ic.identity_id
JOIN public.identity_credential_types ict ON ic.identity_credential_type_id = ict.id;
```

---

#### Tester Ory Keto

Créez un tuple de relation accordant à Alice l'accès en lecture à un document :

```bash
echo '{"namespace":"documents","object":"doc-123","relation":"viewer","subject_id":"user:alice"}' \
  | keto relation-tuple create /dev/stdin --insecure-disable-transport-security
```

Ou via REST :

```bash
curl -i -X PUT "$KETO_WRITE_REMOTE/admin/relation-tuples" \
  -H "Content-Type: application/json" \
  -d '{"namespace":"documents","object":"doc-123","relation":"viewer","subject_id":"user:alice"}'
```

Développez l'arbre d'accès :

```bash
keto expand viewer documents photos --insecure-disable-transport-security
```

Vérifiez les permissions d'Alice :

```bash
keto check "user:alice" viewer documents doc-123 \
  --insecure-disable-transport-security
# Résultat attendu : allowed
```

Vérifiez les tuples de relations dans CockroachDB :

```sql
SELECT
  t.namespace,
  (SELECT m.string_representation FROM public.keto_uuid_mappings m WHERE m.id = t.object) AS object,
  t.relation,
  (SELECT m.string_representation FROM public.keto_uuid_mappings m WHERE m.id = t.subject_id) AS subject,
  t.commit_time
FROM public.keto_relation_tuples t;
```

---

## Prochaines Étapes

Avec les trois services Ory vérifiés contre CockroachDB, vous disposez d'une infrastructure IAM complète prête pour la production. Vous pouvez ensuite :

- Ajouter des nœuds CockroachDB multi-régions pour des déploiements géo-distribués
- Configurer le courier email d'Ory pour les flux de vérification
- Intégrer le fournisseur OIDC d'Hydra avec la couche d'authentification de votre application
- Définir des namespaces Keto et des modèles de permissions granulaires

## Voir Aussi

- [Documentation Ory](https://www.ory.sh/docs/)
- [CockroachDB Cloud](https://cockroachlabs.cloud/)
- [Déployer CockroachDB sur AWS EC2](https://www.cockroachlabs.com/docs/stable/deploy-cockroachdb-on-aws)
