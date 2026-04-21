---
layout: post
lang: fr
title: "Déployer Keycloak sur CockroachDB avec Phase Two"
subtitle: "Un Guide Complet"
cover-img: /assets/img/cover-iam-p5.webp
thumbnail-img: /assets/img/cover-iam-p5.webp
share-img: /assets/img/cover-iam-p5.webp
tags: [iam, security, CockroachDB, Keycloak, Phase Two, authorization, identity]
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

Les produits SaaS d'aujourd'hui font face à deux exigences simultanées : la couche d'identité numérique doit être transparente et de niveau entreprise, et la couche de données doit s'adapter à l'échelle mondiale tout en restant de manière fiable cohérente. Pendant ce temps, les clients s'attendent à l'Authentification Unique (SSO), à l'intégration multi-locataires et à un contrôle d'accès à grain fin transparent, tandis que les équipes d'ingénierie doivent garantir l'isolation des données, des performances mondiales, et maintenir à la fois la disponibilité et la cohérence forte.

Équilibrer ces deux exigences est notoirement difficile. Les systèmes d'identité sont complexes à gérer et à sécuriser ; les bases de données multi-locataires peuvent facilement devenir des goulots d'étranglement ou des risques de conformité si elles sont mal conçues.

C'est pourquoi la collaboration entre [Phase Two](https://phasetwo.io/) et [CockroachDB](https://www.cockroachlabs.com/product/overview/) est si convaincante. Phase Two fournit une plateforme [Keycloak](https://www.keycloak.org/) gérée qui gère l'authentification, l'autorisation et la fédération des identités. CockroachDB fournit une base de données SQL distribuée à l'échelle mondiale qui garantit la cohérence transactionnelle et l'isolation des locataires à grande échelle. Combinées, elles offrent une base puissante pour les plateformes SaaS multi-locataires qui sont sécurisées, résilientes et évolutives.

## Présentation de Phase Two

Phase Two offre un hébergement entièrement géré, un support entreprise et des opérations pour Keycloak, qui est un système de gestion des identités et des accès (IAM) open-source de niveau entreprise. Parce que Phase Two gère l'infrastructure, les mises à niveau, les sauvegardes et les correctifs de sécurité, les équipes peuvent se concentrer sur les fonctionnalités produit plutôt que sur la gestion des serveurs IAM. Les fonctionnalités clés de Phase Two incluent :

- Gestion des identités tenant compte des multi-locataires : realms, clients, rôles, connexions SSO
- Support des fournisseurs d'identité fédérés : Google, Azure AD, SAML, OIDC
- Portails d'administration, libre-service utilisateur, capacité d'extension
- Infrastructure gérée : correctifs, mises à niveau, haute disponibilité, sauvegardes

<img src="/assets/img/iam-p5-01.png" alt="PhaseTwo: a fully-managed identity toolset" style="width:100%">

{: .mx-auto.d-block :}
**PhaseTwo : une boîte à outils d'identité entièrement gérée**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Pour les constructeurs de SaaS, le plus grand avantage est la rapidité de mise sur le marché. Avec Phase Two, ils peuvent livrer une authentification sécurisée et un SSO d'entreprise en heures, pas en semaines.

## Présentation de Keycloak

Keycloak est une solution open-source de gestion des identités et des accès conçue pour les applications et services modernes. Il prend en charge l'authentification, l'autorisation, la liaison d'identité fédérée et la gestion des utilisateurs prêts à l'emploi. À son cœur, Keycloak se positionne entre vos applications et vos utilisateurs : il gère la connexion via des protocoles standards tels qu'OpenID Connect (OIDC) ou SAML, émet des tokens de sécurité (tels que les JWT), et gère les sessions, les rôles et les permissions.

Pour une utilisation en production, la documentation de Keycloak souligne que la base de données sous-jacente est critique pour les performances, la disponibilité et l'intégrité, et qu'un déploiement en cluster (avec deux instances Keycloak ou plus) est requis pour la haute disponibilité. Keycloak prend en charge les architectures à haute disponibilité et les déploiements multi-sites, permettant la résilience entre les zones ou les régions.

<img src="/assets/img/iam-p5-02.png" alt="Identity and Access Control Features in PhaseTwo" style="width:100%">

{: .mx-auto.d-block :}
**Fonctionnalités de Contrôle d'Identité et d'Accès dans PhaseTwo**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Avec Keycloak seul, une organisation dispose d'une plateforme d'identité mature et open-source. Mais l'exécuter à grande échelle, surtout dans un environnement SaaS où de nombreux locataires et de nombreuses régions doivent être supportés, exige une couche de données capable de correspondre à la disponibilité et à la cohérence du système d'identité. C'est là qu'interviennent les améliorations de Phase Two et l'intégration avec CockroachDB.

## Pourquoi Phase Two + CockroachDB ?

Combiner Keycloak avec CockroachDB débloque des avantages techniques majeurs :

- Évolutivité : L'architecture de CockroachDB permet aux déploiements Keycloak de s'adapter horizontalement, gérant de grands volumes d'utilisateurs et de trafic d'authentification.
- Haute Disponibilité et Tolérance aux Pannes : Avec le noyau tolérant aux pannes de CockroachDB, même en cas de pannes matérielles ou régionales, le système d'identité reste disponible.
- Cohérence Forte : Les systèmes d'identité ne doivent pas avoir de split-brain ni de données obsolètes ; le modèle SQL distribué de CockroachDB garantit la cohérence entre les nœuds.
- Efficacité des Coûts : La mise à l'échelle horizontale permet une croissance des coûts d'infrastructure plus prévisible que l'ajout d'instances de base de données verticales plus puissantes.
- Performances : Des métriques de latence impressionnantes en production : latence au 99ème percentile inférieure à 10 ms, au 90ème percentile inférieure à 5 ms.

En bref : Phase Two gère « qui accède à quoi et quand », tandis que CockroachDB gère « où vivent les données et comment elles sont accédées ». C'est une combinaison puissante pour l'architecture SaaS multi-locataires.

<img src="/assets/img/iam-p5-03.png" alt="PhaseTwo + CockroachDB joint architecture" style="width:100%">

{: .mx-auto.d-block :}
**Architecture conjointe PhaseTwo + CockroachDB**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Lorsque vous concevez une plateforme d'identité à fort volume nécessitant une disponibilité mondiale, une cohérence forte et une mise à l'échelle transparente, l'architecture est centrée sur la couche applicative et la couche d'identité. Dans ce scénario, la couche d'identité est fournie par Phase Two, soutenue par CockroachDB comme backend de stockage.

Phase Two fournit une plateforme de gestion centralisée permettant aux équipes de configurer et surveiller les clusters d'identité. Depuis la console de gestion, accessible sur [dash.phasetwo.io](http://dash.phasetwo.io), les administrateurs gèrent tout ce qui concerne l'infrastructure et la gestion des identités :

- La Gestion d'Équipe, la Facturation et la Surveillance permettent aux administrateurs de superviser l'utilisation, les coûts et la santé opérationnelle.
- APIs/.tf indique l'accès Terraform et API, permettant le provisionnement programmatique des clusters et des ressources.
- La Gestion des Realms donne le contrôle sur les realms Keycloak, les utilisateurs et les configurations d'identité.
- La Configuration des Clusters, la Gestion des Clusters, les Ressources des Clusters et l'Accès aux Clusters sont utilisés pour déployer, mettre à l'échelle et se connecter aux clusters gérés.

Essentiellement, cette couche est le plan de contrôle — elle régit la façon dont les clusters sous-jacents et les instances d'identité sont créés, maintenus et intégrés. Ce plan de contrôle simplifie le déploiement et la gestion qui nécessiteraient autrement des connaissances DevOps et une gestion des releases.

Chaque client exécute son propre environnement, géré et hébergé par Phase Two pour l'isolation et la conformité. Au sein de chaque cluster, Keycloak stocke et récupère les données des utilisateurs, des sessions et des realms depuis CockroachDB. Chaque cluster opère de manière indépendante — les données et configurations d'identité des clients ne se chevauchent pas.

Phase Two orchestre ces déploiements, s'assurant que Keycloak et CockroachDB restent synchronisés, hautement disponibles et performants.

## Tout mettre ensemble : Un tutoriel rapide

Voici un tutoriel de démarrage simplifié pour faire fonctionner la solution conjointe Phase Two + CockroachDB. Il suppose que vous utilisez soit le service Keycloak géré de Phase Two, soit que vous déployez leur distribution améliorée vous-même, et que vous disposez d'un cluster CockroachDB (auto-hébergé ou cloud).

### Étape 1a. Configurer et démarrer un Keycloak auto-hébergé

Vous pouvez également déployer la distribution Keycloak améliorée de Phase Two (qui a un support intégré pour CockroachDB et des extensions axées sur le SaaS). Vous pouvez récupérer l'image Docker comme décrit dans le [dépôt GitHub de Phase Two](https://github.com/p2-inc) :

```bash
docker pull quay.io/phasetwo/keycloak-crdb:latest
```

Cette image est basée sur Keycloak standard mais intègre des extensions et supporte CockroachDB comme backend.

Vous pouvez déployer deux instances Keycloak ou plus (pour la redondance) derrière un équilibreur de charge. Le guide de haute disponibilité de Keycloak précise que de tels déploiements doivent garantir une faible latence, une réplication synchrone des données entre les sites, et que la base de données elle-même tolère les pannes de zone. Pour cette démonstration, nous n'aurons besoin de démarrer qu'une seule instance de Keycloak pour montrer comment elle fonctionne avec CockroachDB.

Tout d'abord, vous devez configurer la propriété `useCockroachMetadata=true` dans la variable d'environnement `KC_DB_URL_PROPERTIES`. De plus, elle doit être exécutée avec quelques options de configuration définies :

```
KC_DB=cockroach
KC_TRANSACTION_XA_ENABLED=false
KC_TRANSACTION_JTA_ENABLED=false
```

Depuis un terminal, entrez la commande suivante pour démarrer Keycloak :

```bash
docker run --name phasetwo_test --rm -p 8080:8080 \
-e KC_BOOTSTRAP_ADMIN_USERNAME=admin -e KC_BOOTSTRAP_ADMIN_PASSWORD=admin \
-e KC_HTTP_RELATIVE_PATH=/auth -e KC_DB=cockroach -e KC_DB_PASSWORD='' \
-e KC_DB_SCHEMA=public -e KC_DB_URL_DATABASE=keycloak \
-e KC_DB_URL_HOST=$CRDB_HOST -e KC_DB_URL_PORT=26257 \
-e KC_DB_URL_PROPERTIES='?sslmode=disable&useCockroachMetadata=true' \
-e KC_DB_USERNAME=root -e KC_TRANSACTION_XA_ENABLED='false' \
-e KC_TRANSACTION_JTA_ENABLED='false' \
quay.io/phasetwo/keycloak-crdb:latest \
start-dev
```

Cette commande démarre Keycloak exposé sur le port local `8080` et crée un utilisateur admin initial avec le nom d'utilisateur `admin` et le mot de passe `admin`.

<img src="/assets/img/iam-p5-04.png" alt="Keycloak started with CockroachDB" style="width:100%">
{: .mx-auto.d-block :}
**Keycloak démarré avec CockroachDB**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Une fois le conteneur opérationnel, vous pouvez configurer votre realm, vos clients, vos fournisseurs d'identité, vos rôles et votre fédération d'utilisateurs comme d'habitude.

### Étape 1b. Configurer et démarrer un Keycloak géré avec Phase Two

Si vous souhaitez vous débarrasser de toute difficulté de provisionnement d'infrastructure, vous pouvez opter pour le déploiement de vos clusters Keycloak en utilisant Phase Two. Tout d'abord, inscrivez-vous sur le [tableau de bord Phase Two](https://dash.phasetwo.io/) et créez un nouveau compte. Vous serez redirigé vers la page principale du tableau de bord.

<img src="/assets/img/iam-p5-05.png" alt="Phase Two dashboard" style="width:100%">
{: .mx-auto.d-block :}
**Tableau de bord Phase Two**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Ici, vous pouvez déployer des clusters, créer des équipes et créer des realms comme vous pourriez le faire avec le Keycloak open-source.

### Étape 2a. Créer un realm dans un Keycloak auto-hébergé

Un realm dans Keycloak est équivalent à un locataire. Chaque realm permet à un administrateur de créer des groupes isolés d'applications et d'utilisateurs. Initialement, Keycloak inclut un seul realm, appelé `master`. Utilisez ce realm uniquement pour gérer Keycloak et non pour gérer les applications.

Suivez ces étapes pour créer votre propre realm :

- Ouvrez la [Console d'Administration Keycloak](http://localhost:8080/admin) dans votre navigateur.
- Dans le menu supérieur gauche, localisez le Realm Actuel et cliquez sur Créer un Realm à côté.

<img src="/assets/img/iam-p5-06.png" alt="Create realm in Keycloak admin console" style="width:100%">
{: .mx-auto.d-block :}
**Créer un realm dans la console d'administration Keycloak**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

- Dans le champ Nom du Realm, entrez `crdb-realm`.
- Cliquez sur Créer pour finaliser.

<img src="/assets/img/iam-p5-07.png" alt="Realm name configuration" style="width:100%">
{: .mx-auto.d-block :}
**Configuration du nom du realm**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

### Étape 2b. Créer un realm dans Phase Two

Créer un realm dans PhaseTwo offre un moyen rapide de démarrer avec Keycloak. Dans le menu Créer un Realm, vous devez définir le nom du realm, la région où le realm doit être situé et l'organisation dans laquelle votre realm sera provisionné.

<img src="/assets/img/iam-p5-08.png" alt="Create realm in Phase Two" style="width:100%">
{: .mx-auto.d-block :}
**Créer un realm dans Phase Two**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Une fois le realm créé et actif, vous pouvez cliquer sur le menu Console dans le coin supérieur droit du tableau de bord pour ouvrir la console Keycloak.

<img src="/assets/img/iam-p5-09.png" alt="Keycloak console in Phase Two" style="width:100%">
{: .mx-auto.d-block :}
**Console Keycloak dans Phase Two**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Pour les étapes restantes de ce guide, vous effectuerez les actions suivantes dans la console Keycloak de manière similaire au déploiement auto-hébergé.

### Étape 3. Créer un utilisateur

Lorsque vous créez un realm pour la première fois, il ne contient aucun utilisateur. Pour en ajouter un, assurez-vous que vous êtes toujours dans le realm `crdb-realm` (vérifiez à côté du Realm Actuel).

Dans le menu de gauche, cliquez sur Utilisateurs, cliquez sur Créer un nouvel utilisateur et remplissez le formulaire comme suit :

- Nom d'utilisateur : `crdb-user`
- Prénom : tout nom de votre choix
- Nom de famille : tout nom de votre choix

Ensuite, cliquez sur Créer pour ajouter le nouvel utilisateur.

<img src="/assets/img/iam-p5-10.png" alt="Create new user in Keycloak" style="width:100%">
{: .mx-auto.d-block :}
**Créer un nouvel utilisateur dans Keycloak**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Cet utilisateur a besoin d'un mot de passe pour se connecter. Pour définir le mot de passe initial, cliquez sur Identifiants en haut de la page, remplissez le formulaire Définir le mot de passe avec un mot de passe et basculez Temporaire sur `Off` pour que l'utilisateur n'ait pas besoin de mettre à jour ce mot de passe à la première connexion.

Pour Keycloak auto-hébergé, vous pouvez maintenant vous connecter à la [Console de Compte locale](http://localhost:8080/realms/crdb-realm/account/) pour vérifier que cet utilisateur est configuré correctement. Pour cela, ouvrez la [Console de Compte Keycloak](http://localhost:8080/realms/myrealm/account) (sur le port `8080`), puis connectez-vous avec `crdb-user` et le mot de passe que vous avez créé précédemment.

Si vous choisissez un Keycloak géré, vous pouvez simplement vous connecter à la [console de compte distante](https://euc1.auth.ac/auth/realms/crdb-realm/account/) puis vous connecter avec les identifiants de `crdb-user`.

En tant qu'utilisateur dans la Console de Compte, vous pouvez gérer votre compte, notamment modifier votre profil, ajouter une authentification à deux facteurs et inclure des comptes de fournisseurs d'identité.

<img src="/assets/img/iam-p5-11.png" alt="Keycloak Account Console" style="width:100%">
{: .mx-auto.d-block :}
**Console de Compte Keycloak**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

### Étape 4. Créer et sécuriser votre première application.

Pour sécuriser la première application, vous commencez par enregistrer l'application auprès de votre instance Keycloak. Pour cela, ouvrez la [console d'administration locale](http://localhost:8080) de Keycloak ou la [console d'administration distante](https://euc1.auth.ac/auth/admin/crdb-realm/console), selon le mode de déploiement de Keycloak, cliquez sur `crdb-realm` à côté du Realm Actuel, puis sur l'onglet Clients et cliquez sur Créer un client. Enfin, remplissez le formulaire avec les valeurs suivantes :

- Type de client : `OpenID Connect`
- ID Client : `my-app`

Confirmez que le flux Standard est activé et effectuez ces changements sous les paramètres de connexion :

- Définissez les URLs de redirection valides sur `https://www.keycloak.org/app/*`
- Définissez les origines Web sur `https://www.keycloak.org`

Notez que nous avons défini ces URLs parce que nous utiliserons l'application de test SPA sur le site web de Keycloak ([www.keycloak.org](http://www.keycloak.org)). Pour une utilisation spécifique, vous devez modifier ces valeurs en conséquence.

<img src="/assets/img/iam-p5-12.png" alt="Create and configure a Keycloak client" style="width:100%">
{: .mx-auto.d-block :}
**Créer et configurer un client Keycloak**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

### Étape 5. Tester le flux standard

Pour confirmer que le client a été créé avec succès, vous pouvez utiliser l'application de test SPA sur le [site web de Keycloak](https://www.keycloak.org/app/). Définissez la configuration selon les valeurs que vous avez déjà définies (c'est-à-dire l'URL du Serveur Keycloak, le Realm et l'ID Client) et enregistrez.

<img src="/assets/img/iam-p5-13.png" alt="SPA testing application configuration" style="width:100%">
{: .mx-auto.d-block :}
**Configuration de l'application de test SPA**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Ensuite, cliquez sur « Se connecter » pour vous authentifier à cette application en utilisant l'utilisateur `crdb-user` que vous avez créé précédemment. Une fois connecté avec succès, vous devriez avoir l'écran d'accueil suivant :

<img src="/assets/img/iam-p5-14.png" alt="Successful login greeting screen" style="width:100%">
{: .mx-auto.d-block :}
**Écran d'accueil de connexion réussie**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Puisque nous avons sélectionné le Flux Standard lors de la création du client, les étapes suivantes ont lieu lorsque l'utilisateur tente de se connecter :

- L'utilisateur se connecte via l'application cliente.
- Keycloak authentifie l'utilisateur et génère un Code d'Autorisation.
- L'agent utilisateur est redirigé vers l'application avec ce code.
- L'application envoie le Code d'Autorisation avec ses identifiants clients au point de terminaison token de Keycloak.
- Keycloak renvoie un Token d'Accès, un Token de Rafraîchissement et un Token d'Identité à l'application.

Le diagramme ci-dessous montre les étapes qui se déroulent en séquence et quels composants sont impliqués.

<img src="/assets/img/iam-p5-15.png" alt="Standard flow authorization sequence diagram" style="width:100%">
{: .mx-auto.d-block :}
**Diagramme de séquence d'autorisation du flux standard**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Le flux est destiné aux applications web, mais est également recommandé pour les applications natives, y compris les applications mobiles, où il est possible d'intégrer un agent utilisateur.

## Phase Two et CockroachDB : Une Pile Complémentaire

Dans cet article, nous avons vu comment Phase Two, une plateforme Keycloak gérée, converge avec CockroachDB, une base de données SQL globalement distribuée et fortement cohérente, pour créer une solide base d'identité et de données pour les applications SaaS multi-locataires.

Ensemble, Phase Two et CockroachDB fournissent une pile complémentaire. Phase Two simplifie la gestion des identités sécurisée et multi-locataires, tandis que CockroachDB garantit un stockage de données durable, cohérent et évolutif. Cette combinaison permet aux équipes de livrer des expériences SaaS fiables plus rapidement avec une surcharge opérationnelle significativement réduite.
