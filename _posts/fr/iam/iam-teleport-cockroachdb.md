---
date: 2025-07-10
layout: post
lang: fr
title: "Quand Teleport & CockroachDB ont Propulsé la Gestion des Accès Mondiaux de Niveau 0"
subtitle: "Comment un leader mondial des paiements a atteint 99,999% de disponibilité pour l'accès à l'infrastructure"
cover-img: /assets/img/cover-iam-p3.webp
thumbnail-img: /assets/img/cover-iam-p3.webp
share-img: /assets/img/cover-iam-p3.webp
tags: [iam, security, CockroachDB, Teleport, multi-region, infrastructure]
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

Dans les grandes entreprises sensibles à la sécurité, particulièrement dans le secteur financier, l'infrastructure d'accès n'est pas simplement un service parmi d'autres : c'est un fondement critique. L'accès doit être sécurisé, observable et conforme. Surtout, il doit toujours être disponible. Lorsqu'un fournisseur mondial de paiements a entrepris de standardiser [Teleport](https://goteleport.com/) comme plateforme d'accès interne, il devait satisfaire aux exigences strictes d'une classification Tier 0, qui impose une disponibilité de 99,999 % sur une empreinte distribuée à l'échelle mondiale.

Cet article explore comment ce leader mondial des paiements numériques a surmonté les limitations de son infrastructure d'accès en utilisant CockroachDB comme backend de stockage pour Teleport. En conséquence, il a pu satisfaire aux exigences rigoureuses de fiabilité et de présence mondiale d'un système Tier 0.

Nous allons non seulement parcourir la solution architecturale, mais également fournir un tutoriel pratique pour mettre en place un système de gestion des accès hautement disponible avec Teleport et CockroachDB.

---

## Le Défi : Exigences Multi-Région pour le Niveau Tier 0

En tant que grande entreprise de technologie des paiements, cette organisation opère à une échelle mondiale immense. Avec des opérations couvrant tous les continents et un réseau qui traite des centaines de milliards de transactions annuellement, leur infrastructure doit répondre à des standards exceptionnellement élevés en matière de disponibilité, d'évolutivité et de conformité.

Conçue pour la résilience dans plusieurs régions, avec des centres de données couvrant trois continents, cette empreinte mondiale permet à cette entreprise de paiements mondiale de servir des utilisateurs internes diversifiés et des équipes informatiques travaillant dans le monde entier avec une latence minimale, tout en répondant aux exigences de résidence des données et aux réglementations régionales.

<img src="/assets/img/iam-p3-global-payments.jpg" alt="Global Payments System" style="width:100%">

{: .mx-auto.d-block :}
**Système de Paiements Mondial**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Mais opérer dans un environnement aussi distribué s'accompagne de complexité, surtout en ce qui concerne l'accès à l'infrastructure. Avec des équipes situées dans différents fuseaux horaires et régions, elles ont toutes besoin d'un accès sécurisé, conforme et instantané aux systèmes pour des tâches telles que le débogage, le déploiement et la surveillance. L'accès doit être à la fois hautement sécurisé et hautement disponible, sans introduire de goulots d'étranglement ni s'appuyer sur des VPN fragiles ou des identifiants statiques.

Pour cette entreprise leader, tout outil utilisé dans son infrastructure doit être évalué par rapport à la classification interne de l'entreprise pour les applications Tier 0. Les applications Tier 0 sont les systèmes les plus critiques dans l'infrastructure informatique d'une organisation : des services fondamentaux dont dépendent tous les autres systèmes. Leur défaillance provoquerait une panne généralisée, perturberait les opérations commerciales essentielles ou compromettrait la sécurité et la conformité. En tant que tels, les applications Tier 0 doivent respecter les standards les plus élevés de disponibilité, de fiabilité et de sécurité. Dans ce contexte, l'infrastructure de gestion des accès, c'est-à-dire la manière dont les ingénieurs et les services se connectent aux ressources de calcul, de stockage et réseau, ne devient pas un simple utilitaire. C'est un fondement.

### Caractéristiques Clés des Systèmes Tier 0

- **Mission critique** : Leur disponibilité est essentielle pour la continuité des activités. Si un service Tier 0 tombe en panne, il peut entraîner la panne de plusieurs systèmes dépendants.
- **Haute disponibilité (HA)** : On s'attend généralement à ce qu'ils atteignent ou dépassent 99,999 % de disponibilité (cinq neuf), ce qui équivaut à seulement ~5 minutes de temps d'arrêt par an.
- **Contrôles de sécurité stricts** : Ces applications traitent des données sensibles ou régissent l'accès à des ressources critiques, nécessitant une authentification avancée, le chiffrement et des capacités d'audit.
- **Résilience mondiale** : Souvent déployés dans plusieurs centres de données ou régions cloud pour résister aux pannes régionales et aux variations de latence.
- **Sensibles à la conformité** : Tombent fréquemment dans le champ des standards réglementaires tels que PCI-DSS, ISO 27001, SOC 2 ou FedRAMP.

L'infrastructure interne de cette entreprise de paiements mondiale s'étend sur plusieurs continents, sert des milliers d'ingénieurs et doit répondre aux standards les plus élevés de conformité et de disponibilité. [Teleport](https://goteleport.com/) offrait un avantage clair et convaincant en rationalisant et sécurisant l'accès à travers une infrastructure diverse et distribuée à l'échelle mondiale.

Initialement, l'objectif de Teleport était d'unifier et de sécuriser l'accès à ses serveurs et applications dans quatre centres de données principaux situés sur trois continents différents. L'objectif était d'établir une couche de contrôle d'accès unique à travers toutes les régions, offrant des politiques centralisées, l'audit et l'accès basé sur l'identité. Cependant, l'implémentation initiale reposait sur un autre backend de stockage qui n'est pas conçu pour offrir des déploiements multi-région à haute disponibilité.

L'entreprise s'est rapidement heurtée à des obstacles significatifs :

- **Limitations de l'évolutivité** : Le déploiement précédent atteint un plafond d'évolutivité insuffisant pour répondre aux besoins de l'entreprise. La technologie de stockage précédente est conçue pour de petites métadonnées et manque de sharding et d'évolutivité pour les grands ensembles de données typiques des bases de données à usage général.
- **Mode multi-région non pris en charge** : L'absence de support formel de la technologie de stockage précédente dans les configurations multi-régions nécessitait une surcharge opérationnelle importante et une orchestration minutieuse.
- **Problèmes de disponibilité** : Les coupures réseau et la gigue créaient des problèmes de synchronisation et de fiabilité. La technologie de stockage précédente privilégie la cohérence par rapport à la disponibilité ; lors de partitions réseau ou de perte de quorum, le cluster devient indisponible pour éviter le split-brain.
- **Goulots d'étranglement de latence** : Les requêtes d'écriture et de lecture linéarisable doivent passer par le leader du cluster, causant des latences et des goulots d'étranglement dans les grands clusters.

---

## La Solution : Teleport et CockroachDB pour une Plateforme d'Accès Mondiale Tier 0

### Pourquoi Teleport ?

Dans l'infrastructure moderne, l'accès est la première ligne de défense. Que vous vous connectiez à un serveur Linux, un cluster Kubernetes, une base de données cloud ou une application interne, la façon dont les utilisateurs accèdent à ces systèmes détermine votre posture de sécurité globale.

**Teleport** est un plan d'accès qui consolide et sécurise l'accès à tous types d'environnements d'infrastructure. Il est conçu pour remplacer un patchwork de bastions SSH, de VPN, de fournisseurs d'identité et de proxies d'accès tout en fournissant une plateforme unique et unifiée.

<img src="/assets/img/iam-p3-teleport-identity.jpg" alt="Teleport Identity Platform" style="width:100%">

{: .mx-auto.d-block :}
**Plateforme d'Identité Teleport**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Teleport fournissait une couche de contrôle d'accès unifiée capable de gérer les permissions à travers des systèmes hétérogènes. Son architecture sans agent, tirant parti de protocoles standards comme SSH et HTTPS, simplifiait le déploiement et éliminait le besoin de logiciels supplémentaires sur les systèmes cibles. Teleport offrait également une visibilité d'audit en temps réel, permettant aux équipes de sécurité et aux responsables de la conformité de surveiller les événements d'accès et l'activité des sessions avec précision. Avec l'authentification basée sur des certificats et la rotation automatique des certificats, il supprimait les risques associés aux identifiants de longue durée. Enfin, l'intégration SSO profonde avec le fournisseur d'identité interne de l'entreprise garantissait une authentification transparente et centralisée, renforçant à la fois la sécurité et l'efficacité opérationnelle.

Teleport offre :

- L'accès basé sur l'identité via SSO (SAML, OIDC, GitHub, etc.)
- Des certificats de courte durée pour tous les accès (pas de clés statiques ni de mots de passe)
- Un audit complet de toutes les activités, y compris les enregistrements de sessions
- Des politiques RBAC et ABAC pour un contrôle d'accès à grain fin
- Un support multi-protocoles, incluant SSH, Kubernetes, les bases de données (PostgreSQL, MySQL, MongoDB, CockroachDB), les applications web internes et Windows RDP

L'architecture de Teleport est spécialement conçue pour sécuriser l'accès à l'infrastructure dans des environnements dynamiques et distribués. À son cœur, Teleport fonctionne comme un système modulaire et distribué, lui permettant de s'adapter à des topologies d'infrastructure diverses tout en maintenant de solides garanties de sécurité et d'observabilité.

L'architecture de Teleport est construite de fond en comble avec la Sécurité Zéro Confiance à l'esprit, un modèle qui suppose qu'il n'y a pas de confiance implicite, même à l'intérieur du périmètre réseau. Cette approche est particulièrement vitale dans les environnements distribués et cloud natifs où les frontières de sécurité réseau traditionnelles ne s'appliquent plus.

Au cœur de l'implémentation Zéro Confiance de Teleport se trouve le principe de l'identité par rapport au réseau. Au lieu de s'appuyer sur des adresses IP, des VPN ou des sous-réseaux de confiance, chaque requête vers l'infrastructure, qu'il s'agisse d'un serveur Linux, d'une base de données ou d'un cluster Kubernetes, est authentifiée et autorisée uniquement en fonction de l'identité et du rôle de l'utilisateur. Cela garantit que l'accès est strictement délimité, contextuel et entièrement traçable.

Regardons de plus près les composants clés de l'architecture de Teleport.

<img src="/assets/img/iam-p3-teleport-architecture.jpg" alt="Teleport Architecture" style="width:100%">

{: .mx-auto.d-block :}
**Architecture Teleport**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

1. **Serveur `auth`** – le Serveur Auth est l'autorité centrale dans chaque déploiement Teleport. Il agit comme le cerveau du cluster, stockant l'état critique et appliquant les politiques d'authentification, d'autorisation et d'audit. Les responsabilités clés du Serveur Auth incluent :
   - La gestion des définitions des utilisateurs et des rôles
   - L'émission de certificats de courte durée pour l'authentification des utilisateurs et des services
   - Le stockage des événements de session, des demandes d'accès et des journaux d'audit
   - Agir en tant qu'API pour l'enregistrement des ressources et les décisions d'accès

   Parce qu'il est à état et piloté par des politiques, le Serveur Auth repose sur des backends de stockage durables et cohérents. Dans les déploiements multi-régions, ces backends de stockage doivent être distribués, hautement disponibles tout en préservant une cohérence forte. C'est là que CockroachDB devient un acteur clé, garantissant que l'état du Serveur Auth est globalement cohérent et répliqué à travers les géographies.

2. **`proxy`** – la passerelle entre les clients externes et les ressources internes. Il achemine les requêtes, termine les connexions TLS et sert l'interface web de Teleport. Les clients s'authentifient et se connectent au Proxy, qui ensuite :
   - Effectue des tunnels inversés vers les nœuds internes
   - Proxifie le trafic pour SSH, Kubernetes, les bases de données, les applications et Windows RDP
   - Applique la MFA et l'intégration SSO
   - Enregistre les sessions pour l'audit et la relecture

   Cette conception garantit un accès sans agent, basé sur navigateur et en ligne de commande depuis n'importe où dans le monde, sans nécessiter d'accès entrant ni de VPN.

3. **Agents Teleport** : Teleport est construit autour du concept d'agents de ressources, chacun conçu pour connecter un type spécifique d'infrastructure au cluster :
   - L'agent `node` connecte les serveurs Linux via SSH
   - L'agent `kube` intègre les clusters Kubernetes en utilisant l'API Kubernetes
   - L'agent `db` fournit l'accès aux bases de données SQL/NoSQL comme PostgreSQL, MySQL et CockroachDB lui-même
   - L'agent `app` expose les applications HTTP internes derrière SSO et l'audit de sessions sécurisés
   - L'agent `windows` (disponible en entreprise) permet l'accès aux serveurs Windows via RDP

   Ces agents « appellent à la maison » vers le Serveur Auth et le Proxy, formant des tunnels inversés et évitant le besoin d'IPs publiques ou de modifications du pare-feu.

4. **Shell Teleport (`tsh`)** – le client en ligne de commande de Teleport, est la façon dont les utilisateurs s'authentifient et interagissent avec le système. Il offre une UX rationalisée pour :
   - Se connecter avec SSO
   - Accéder aux serveurs et clusters
   - Ouvrir des sessions de base de données et Kubernetes
   - Demander des privilèges élevés ou l'accès à des rôles
   - Afficher l'historique des sessions et les journaux

   En coulisses, `tsh` obtient un certificat de courte durée pour l'identité de l'utilisateur et la portée de la ressource, le rendant intrinsèquement plus sûr que la gestion des clés SSH ou des identifiants statiques.

Ensemble, ces capacités font de Teleport un choix naturel pour les équipes DevSecOps opérant dans des environnements multi-régions et sensibles à la conformité. Que vous vous orientiez vers des standards comme PCI-DSS, FedRAMP ou ISO 27001, Teleport fournit une base d'accès sécurisée, flexible et conviviale pour l'audit.

### Architecture Conjointe Teleport + CockroachDB

Pour répondre aux exigences Tier 0, ce fournisseur mondial de paiements a effectué un pivot stratégique vers CockroachDB, une base de données SQL géo-distribuée conçue pour la résilience et la cohérence multi-régions. Ce changement a simplifié les opérations, permis des déploiements actif-actif de Teleport, et garanti que l'infrastructure d'accès pouvait survivre aux partitions réseau, aux défaillances de nœuds et à la charge mondiale, sans compromettre la sécurité ni la conformité.

<img src="/assets/img/iam-p3-joint-architecture.jpg" alt="Multi-region Teleport + CockroachDB Joint Architecture" style="width:100%">

{: .mx-auto.d-block :}
**Architecture Conjointe Multi-Région Teleport + CockroachDB**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Chacun des composants de Teleport s'appuyait sur CockroachDB pour stocker leur état de manière cohérente et durable, leur permettant de fonctionner correctement même en présence de pannes partielles ou de partitions réseau régionales.

Par exemple, le service Auth de Teleport est bien adapté pour fonctionner avec CockroachDB en raison de sa conception sans état et de sa philosophie orientée API. Chaque service peut être déployé en tant que service sans état, sa seule exigence de persistance étant [la base de données SQL sous-jacente](https://www.cockroachlabs.com/blog/what-is-distributed-sql/). Cela facilite la mise à l'échelle horizontale des services, les mises à jour progressives, ou le déploiement de nouvelles régions sans avoir à orchestrer des migrations de données complexes. CockroachDB, à son tour, fournit la couche de base de données toujours cohérente qui garantit que les identités des utilisateurs, les règles de contrôle d'accès et les tokens de session sont toujours précis, quelle que soit la région qui sert une requête.

Pour atteindre une véritable disponibilité mondiale, il était essentiel d'associer les capacités de Teleport à une base de données SQL distribuée capable de répondre aux exigences de la réplication inter-régions, des garanties de cohérence forte et de la tolérance aux pannes. C'est là que CockroachDB est entré en jeu.

<img src="/assets/img/iam-p3-cockroachdb-attributes.jpg" alt="CockroachDB attributes for Teleport" style="width:100%">

{: .mx-auto.d-block :}
**Attributs de CockroachDB pour Teleport**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

[CockroachDB](https://www.cockroachlabs.com/product/overview/) est une base de données SQL distribuée conçue pour l'échelle mondiale et la haute disponibilité. Depuis qu'elle est devenue la première base de données SQL distribuée disponible commercialement, CockroachDB est connue pour sa résilience de niveau entreprise. Elle réplique les données dans plusieurs régions tout en offrant l'isolation sérialisable, la cohérence forte et le basculement automatique. En déployant les composants Teleport sur CockroachDB, l'entreprise mondiale de paiements a pu garantir que les données de contrôle d'accès à l'infrastructure restaient cohérentes et toujours disponibles, même [lors de perturbations d'infrastructure](https://www.cockroachlabs.com/blog/database-testing-performance-under-adversity/). Par exemple, une équipe DevSecOps se connectant depuis le Royaume-Uni, alors qu'un centre de données aux États-Unis connaît une panne, pouvait toujours utiliser les actifs d'infrastructure sans problème. Ce niveau de résilience était essentiel pour maintenir des expériences utilisateurs transparentes à travers les géographies.

Teleport supporte officiellement [CockroachDB en tant que backend de stockage](https://goteleport.com/docs/reference/backends/#cockroachdb), et pour de bonnes raisons :

- **Support multi-région intégré** : CockroachDB est conçu pour les déploiements géographiquement distribués.
- **Haute disponibilité** : Même lors de partitions réseau, CockroachDB maintient la cohérence et les garanties de disponibilité.
- **Évolutivité horizontale** : Mettez facilement à l'échelle les lectures et les écritures sans sharding ni intervention manuelle.
- **Cohérence des données** : La cohérence forte par défaut garantit que l'état du cluster Teleport reste fiable à travers toutes les régions.

Les tests approfondis de la pile Teleport avec CockroachDB ont démontré la capacité de la solution à offrir performances, résilience et élasticité sous une charge importante et un trafic inter-régions. Cette architecture a permis à l'entreprise d'innover plus rapidement, tout en satisfaisant aux exigences Tier 0 d'un accès sécurisé et ininterrompu pour les équipes internes du monde entier.

Avec les décisions architecturales en place, passons à une configuration réelle qui reflète cette approche en utilisant Teleport et CockroachDB dans un [déploiement multi-régional](https://goteleport.com/docs/admin-guides/deploy-a-cluster/multi-region-blueprint/).

---

## Comment Configurer un Déploiement Teleport Multi-Région pour Sécuriser l'Accès à l'Infrastructure Mondiale

Le guide suivant vous explique comment configurer un déploiement Teleport multi-région avec CockroachDB, garantissant que votre accès à l'infrastructure est non seulement sécurisé mais aussi hautement disponible et évolutif. Dans ce guide, CockroachDB jouera deux rôles : le premier en tant que backend de stockage pour Teleport et le second en tant que [Ressource Protégée Teleport (TPR)](https://goteleport.com/docs/enroll-resources/database-access/enroll-self-hosted-databases/cockroachdb-self-hosted/). Que vous soyez un développeur cherchant à implémenter l'authentification pour une seule application ou une entreprise cherchant une solution distribuée à l'échelle mondiale, le tutoriel suivant vous aidera à atteindre vos objectifs.

### Prérequis

Pour exécuter un déploiement Teleport multi-région, vous devez :

- Créer 3 VPC régionaux appairés (par exemple, sur AWS) ou 1 VPC global (par exemple, sur GKE).
- Créer 1 cluster Kubernetes dans chaque région ; les CIDRs des Pods ne doivent pas se chevaucher.
- Les instances du Service Proxy Teleport doivent pouvoir se contacter par adresse IP. Cela signifie que vous avez une connectivité Pod/Instance inter-régions, généralement obtenue avec le VPC peering et/ou un maillage de services.
- Des stockages d'objets multi-régions (par exemple, AWS S3) pour les enregistrements de sessions, avec les politiques IAM requises et une réplication bidirectionnelle configurée entre les stockages d'objets.
- Un GeoDNS (par exemple, Route53) avec une politique de routage par géoproximité pour acheminer les utilisateurs et les agents Teleport vers le cluster Teleport le plus proche.
- Un cluster CockroachDB multi-région. Vous pouvez utiliser [cet outil](https://github.com/amineelkouhen/tf-roach) pour provisionner un déploiement multi-région.
- Les outils `tctl` et `tsh` installés sur un hôte client (par exemple, une instance Amazon EC2).

### Étape 1 : Configurer CockroachDB comme Backend de Stockage

Créez d'abord les bases de données et l'utilisateur Teleport dans CockroachDB :

```sql
CREATE DATABASE teleport_backend;
CREATE DATABASE teleport_audit;
CREATE USER teleport;
GRANT CREATE ON DATABASE teleport_backend TO teleport;
GRANT CREATE ON DATABASE teleport_audit TO teleport;
SET CLUSTER SETTING kv.rangefeed.enabled = true;
```

Pour une configuration de type production, vous devez configurer l'authentification TLS mutuelle et vous assurer que :

- Teleport fait confiance aux certificats présentés par les nœuds CockroachDB.
- Les nœuds CockroachDB font confiance aux certificats clients signés à la fois par votre CA CockroachDB et par le CA `db_client` de votre cluster Teleport.

Vous pouvez signer un certificat pour l'utilisateur `teleport` avec [la commande cockroach certs](https://www.cockroachlabs.com/docs/stable/cockroach-cert). Vous devez vous retrouver avec trois fichiers :

- `client.teleport.crt`
- `client.teleport.key`
- `ca.crt`

Ensuite, déclarez les zones et régions à CockroachDB et configurez la tolérance aux pannes régionales sur la base de données :

```sql
ALTER DATABASE teleport_backend SET PRIMARY REGION <region1>;
ALTER DATABASE teleport_backend ADD REGION IF NOT EXISTS <region2>;
ALTER DATABASE teleport_backend ADD REGION IF NOT EXISTS <region3>;
ALTER DATABASE teleport_backend SET SECONDARY REGION <region2>;
ALTER DATABASE teleport_backend SURVIVE REGION FAILURE;
ALTER DATABASE teleport_audit SET PRIMARY REGION <region1>;
ALTER DATABASE teleport_audit ADD REGION IF NOT EXISTS <region2>;
ALTER DATABASE teleport_audit ADD REGION IF NOT EXISTS <region3>;
ALTER DATABASE teleport_audit SET SECONDARY REGION <region2>;
ALTER DATABASE teleport_audit SURVIVE REGION FAILURE;
```

Note : si les régions primaire et secondaire sont éloignées l'une de l'autre (par exemple, sur des continents différents), cela ralentira les opérations d'écriture de CockroachDB.

### Étape 2 : Configurer le Cluster K8S Teleport

Teleport fournit des [charts Helm](https://github.com/gravitational/teleport/tree/master/examples/chart) pour installer le Service de Base de Données Teleport dans les clusters Kubernetes. Pour permettre à Helm d'installer des charts hébergés dans le dépôt Helm Teleport, ajoutez le dépôt teleport :

```bash
helm repo add teleport https://charts.releases.teleport.dev
helm repo update
```

Une fois toutes les dépendances Teleport configurées, déployez Teleport via le chart Helm `teleport-cluster`. Vous devez créer une release par cluster Kubernetes. Voici un exemple de valeurs pour une région spécifique :

```yaml
chartMode: standalone
clusterName: teleport-multi-region.cluster.cockroachlabs.com
persistence:
  enabled: false
enterprise: true
auth:
  teleportConfig:
    # Configure CockroachDB
    teleport:
      storage:
        type: cockroachdb
        conn_string: "postgres://teleport@nlb-2025061618161615980000000c-d25a41afe9be1bd5.elb.us-east-1.amazonaws.com:26257/teleport_backend?sslmode=verify-full&pool_max_conns=20"
      audit_events_uri:
        - "postgres://teleport@nlb-2025061618161615980000000c-d25a41afe9be1bd5.elb.us-east-1.amazonaws.com:26257/teleport_audit?sslmode=verify-full"
      audit_sessions_uri: "uri://teleport-crdb-demo.s3.us-east-1.amazonaws.com/session_records?complete_initiators=teleport-crdb-iam-upload-role"
      ttl_job_cron: '*/20 * * * *'
    # Configure le peering proxy
    auth_service:
      tunnel_strategy:
        type: proxy_peering
        agent_connection_count: 2
    # Montez les certs CockroachDB et faites en sorte que Teleport les utilise (via les variables d'env par défaut)
    extraVolumes:
      - name: db-certs
        secret:
          secretName: cockroach-certs
    extraVolumeMounts:
      - name: db-certs
        mountPath: /var/lib/db-certs
        readOnly: true
    extraEnv:
      - name: PGSSLROOTCERT
        value: /var/lib/db-certs/ca.crt
      - name: PGSSLCERT
        value: /var/lib/db-certs/client.teleport.crt
      - name: PGSSLKEY
        value: /var/lib/db-certs/client.teleport.key
    tls:
      existingSecretName: proxy-cert
    highAvailability:
      replicaCount: 2
```

Vous pouvez maintenant tester votre déploiement multi-régional. CockroachDB est défini comme Backend de Stockage pour le Cluster Teleport. Pour vérifier que vous pouvez vous connecter à votre cluster Teleport, connectez-vous avec `tsh login`, puis vérifiez que vous pouvez exécuter des commandes `tctl` avec vos identifiants actuels :

```bash
tsh login --proxy=teleport-multi-region.cluster.cockroachlabs.com --user=amine@cockroachlabs.com
tctl status
Cluster teleport-multi-region.cluster.cockroachlabs.com
Version 18.1.0
CA pin sha256: ....
```

### Étape 3 : Configurer le Service de Base de Données Teleport

Le Service de Base de Données nécessite un token de jonction valide pour rejoindre votre cluster Teleport. Exécutez la commande `tctl` suivante et sauvegardez la sortie du token :

```bash
tctl tokens add --type=db --format=text
```

Installez l'Agent Kube Teleport dans votre Cluster Kubernetes avec la configuration du Service de Base de Données Teleport. Ci-après, vous trouverez la configuration CockroachDB pour la base de données `demo-assets`, celle que vous souhaitez sécuriser l'accès avec Teleport (ne la confondez pas avec la base de données du backend de stockage) :

```bash
helm install teleport-kube-agent teleport/teleport-kube-agent \
  --create-namespace \
  --namespace teleport-agent \
  --set roles=db \
  --set proxyAddr=teleport-multi-region.cluster.cockroachlabs.com:443 \
  --set authToken=${JOIN_TOKEN?} \
  --set "databases[0].name=demo-assets" \
  --set "databases[0].uri=http://20250516154447737700000007-27042aa4022d3b9a.elb.us-east-1.amazonaws.com/:26257" \
  --set "databases[0].protocol=cockroachdb" \
  --set "databases[0].static_labels.env=dev" \
  --version 18.1.0
```

### Étape 4 : Créer un Utilisateur Teleport

Créez un utilisateur Teleport local avec les rôles intégrés `access` et `requester` :

```bash
tctl users add \
  --roles=access,requester \
  --db-users="*" \
  --db-names="*" \
  danielle
```

### Étape 5 : Créer un Utilisateur CockroachDB

Teleport utilise l'authentification TLS mutuelle avec CockroachDB. L'authentification par certificat client est disponible pour tous les utilisateurs CockroachDB. Si vous n'en avez pas, connectez-vous à votre cluster Cockroach et créez-en un. Vous pouvez également empêcher l'utilisateur d'utiliser l'authentification par mot de passe et exiger l'authentification par certificat client en utilisant la clause `WITH PASSWORD NULL` :

```sql
CREATE USER danielle WITH PASSWORD NULL;
```

Maintenant, connectez-vous à votre cluster Teleport. Votre cluster CockroachDB devrait apparaître dans la liste des bases de données disponibles :

```bash
tsh login --proxy=teleport-multi-region.cluster.cockroachlabs.com --user=danielle
tsh db ls
Name            Description              Labels
-----           ---------------          -------
demo-assets     Example CockroachDB      env=dev
```

### Étape 6 : Se Connecter à CockroachDB (TPR DB)

Pour récupérer les identifiants d'une base de données et s'y connecter :

```bash
tsh db connect demo-assets
```

Vous pouvez optionnellement spécifier le nom de la base de données et l'utilisateur à utiliser par défaut lors de la connexion au serveur de base de données :

```bash
tsh db connect --db-user=danielle demo-assets
```

En suivant ce guide, vous avez mis en place avec succès un système d'accès à l'infrastructure mondiale avec Teleport et CockroachDB. Cette configuration garantit l'évolutivité, la haute disponibilité et la résilience tout en sécurisant vos actifs d'infrastructure d'entreprise.

---

## Résumé

En utilisant Teleport et CockroachDB, un leader mondial des paiements a non seulement résolu un problème technique de mise à l'échelle, mais a également créé une base pour un accès à l'infrastructure à l'épreuve du temps, auditable et conforme aux réglementations régionales à travers ses équipes d'ingénierie mondiales.

Leur histoire d'infrastructure va au-delà du simple choix technologique : il s'agit d'aligner l'architecture sur les objectifs critiques de l'entreprise, et de construire des systèmes capables de maintenir la confiance d'une base mondiale de clients qui dépend de cette entreprise à chaque seconde de chaque jour. En tirant parti de CockroachDB, ce leader mondial des paiements a permis une présence multi-régionale, une résilience aux perturbations réseau et un contrôle d'accès cohérent à travers les continents.

Dans cet article, nous avons également fourni un guide pratique pour vous aider à reproduire ce cas d'usage. Nous avons utilisé CockroachDB comme backend de stockage pour sauvegarder les états internes du plan de contrôle Teleport, mais aussi comme [Ressource Protégée Teleport (TPR)](https://goteleport.com/docs/enroll-resources/database-access/enroll-self-hosted-databases/cockroachdb-self-hosted/) que nous sécurisons en utilisant Teleport lui-même. Que vous gériez l'accès à l'ingénierie interne ou que vous mettiez à l'échelle une infrastructure à l'échelle de l'entreprise tenant compte des identités, Teleport et CockroachDB offrent une base puissante pour une gestion des accès à l'infrastructure sécurisée et toujours disponible.
