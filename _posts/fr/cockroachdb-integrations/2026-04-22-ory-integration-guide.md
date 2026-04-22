---
layout: post
lang: fr
title: "Intégrer CockroachDB avec Ory"
subtitle: "Guide pas-à-pas pour déployer Ory Hydra, Kratos et Keto avec CockroachDB"
thumbnail-img: /assets/img/cockroachdb.webp
share-img: /assets/img/cockroachdb.webp
tags: [cockroachdb-integrations, CockroachDB, ory, iam, kubernetes, oauth2, helm, identity]
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

Chaque service étant sans état, toute la persistance réside dans CockroachDB. La mise à l'échelle horizontale, les mises à jour progressives et les déploiements multi-régions deviennent simples — sans sessions collantes ni caches distribués à coordonner.

---

## Ory Hydra

Ory Hydra implémente le [framework d'autorisation OAuth 2.0](https://oauth.net/2/) et les spécifications [OpenID Connect Core 1.0](https://openid.net/connect/). Il gère les clients OAuth2, les sessions de consentement et les tokens avec une cohérence forte pour prévenir les attaques par rejeu et les autorisations dupliquées.

Le processus d'autorisation implique quatre acteurs :

1. **Client** — l'application demandant l'accès
2. **Propriétaire de la ressource** — l'utilisateur final
3. **Ory Hydra** — le serveur d'autorisation
4. **Serveur de ressources** — l'API hébergeant les ressources protégées

Le flux : le client redirige l'utilisateur vers l'écran de connexion/consentement d'Hydra. Après approbation, l'utilisateur octroie un code d'autorisation. Le client l'échange contre un token d'accès, puis présente ce token au serveur de ressources pour accéder aux ressources protégées.

CockroachDB stocke tous les clients OAuth2, les codes d'autorisation, les tokens d'accès et les sessions de consentement — durablement et avec cohérence linéarisable.

---

## Ory Kratos

Ory Kratos gère tout ce qui concerne l'identité utilisateur : inscription, connexion, déconnexion, paramètres, récupération de compte, vérification d'adresse et authentification multi-facteurs.

Chaque enregistrement d'identité utilisateur est stocké dans des tables transactionnelles CockroachDB :

- **`identities`** — enregistrement d'identité principal avec schéma et état
- **`identity_credentials`** — mots de passe, connexions sociales et autres méthodes d'authentification
- **`sessions`** — tokens de session actifs et données d'expiration
- **`verification_tokens`** — flux de vérification email/téléphone

Flux pris en charge : Inscription et Connexion/Déconnexion, Paramètres utilisateur, Récupération de compte, Vérification d'adresse, 2FA/MFA, et Gestion des erreurs.

---

## Ory Keto

Ory Keto permet un contrôle d'accès basé sur les relations (ReBAC) scalable via des tuples de relations — le même modèle utilisé par [Google Zanzibar](https://research.google/pubs/pub48190/). Les décisions d'autorisation reposent sur :

- **Les données dans CockroachDB** — ex. « l'utilisateur Bob est propriétaire du document X »
- **Les règles de permission** — ex. « les propriétaires de documents peuvent le consulter »

Les tuples de relations sont stockés dans la table `keto_relation_tuples` de CockroachDB et interrogés à la demande, offrant un contrôle d'accès granulaire et auditable qui évolue avec vos données.

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

Une seule région cloud contient trois zones de disponibilité (`us-east-1a`, `us-east-1b`, `us-east-1c`). La conception assure :

- **VPC Ory** — cluster Amazon EKS avec nœuds workers distribués entre les zones, exécutant les pods Hydra, Kratos et Keto avec routage ingress et service
- **VPC CRDB** — nœuds CockroachDB sur les zones formant un cluster logique unique utilisant le consensus Raft pour la réplication des données
- **Network Load Balancer** — achemine le trafic vers les nœuds sains avec basculement automatique

---

## Prérequis

- Compte AWS avec permissions EKS et EC2
- Profil AWS CLI configuré
- Installés : Terraform, kubectl, eksctl et Helm (v3+)
- Connaissances de base de Kubernetes
- (Optionnel) Domaine et configuration DNS pour l'exposition publique
- **Temps d'installation estimé :** 45–60 minutes

---

## Étape 1 : Provisionner un Cluster CockroachDB

Choisissez l'une des méthodes de déploiement :

- **Local** — cluster auto-hébergé multi-nœuds avec le binaire CockroachDB
- **AWS EC2** — cluster auto-hébergé sur Amazon EC2 avec load-balancing AWS géré
- **CockroachDB Cloud** — service entièrement géré par Cockroach Labs avec crédits d'essai

> **Important :** Créez un cluster **sécurisé** — la création d'utilisateurs l'exige.

---

## Étape 2 : Créer les Bases de Données pour les Services Ory

Des bases de données séparées isolent les données entre les composants Ory.

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

## Étape 3 : Provisionner un Cluster Kubernetes

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

Le provisionnement prend 10–15 minutes. Ajoutez le dépôt Helm d'Ory :

```bash
helm repo add ory https://k8s.ory.sh/helm/charts
helm repo update
```

---

## Étape 4 : Déployer les Services Ory

### Déployer Ory Hydra

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

### Déployer Ory Kratos

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

### Déployer Ory Keto

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

## Étape 5 : Tester l'Intégration

### Tester Ory Hydra

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

### Tester Ory Kratos

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

Vérifiez l'identité dans CockroachDB :

```sql
SELECT i.id, i.schema_id, i.traits, i.created_at, ict.name AS identity_type
FROM public.identities i
JOIN public.identity_credentials ic ON i.id = ic.identity_id
JOIN public.identity_credential_types ict ON ic.identity_credential_type_id = ict.id;
```

---

### Tester Ory Keto

Créez un tuple de relation accordant à Alice l'accès en lecture à un document :

```bash
curl -i -X PUT "$KETO_WRITE_REMOTE/admin/relation-tuples" \
  -H "Content-Type: application/json" \
  -d '{"namespace":"documents","object":"doc-123","relation":"viewer","subject_id":"user:alice"}'
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
