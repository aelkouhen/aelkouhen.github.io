---
date: 2025-06-12
layout: post
lang: fr
title: "Dans la Pile IAM Toujours Disponible d'OpenAI avec Ory et CockroachDB"
subtitle: "Comment OpenAI a construit une plateforme CIAM multi-région résiliente"
cover-img: /assets/img/cover-iam-p2.png
thumbnail-img: /assets/img/cover-iam-p2.png
share-img: /assets/img/cover-iam-p2.png
tags: [iam, security, authentication, authorization, CockroachDB, OpenAI, Ory]
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

À mesure que les organisations se développent à l'échelle mondiale et que les utilisateurs s'attendent à un accès transparent et en temps réel depuis n'importe où dans le monde, les systèmes de [gestion des identités et des accès (IAM)](https://www.cockroachlabs.com/solutions/usecases/identity-access-management/) traditionnels deviennent souvent un goulot d'étranglement. Ces solutions héritées, généralement construites sur des architectures monolithiques liées à des régions spécifiques, peinent à offrir la résilience, les performances et la flexibilité requises dans les environnements distribués et cloud natifs. Elles manquent souvent de support pour la réplication multi-région, offrent une observabilité limitée et sont difficiles à adapter à l'évolution des besoins produits. Surtout, elles n'offrent pas aux entreprises le contrôle dont elles ont besoin sur leur architecture à mesure que leur activité se développe.

Lorsqu'un système IAM tombe en panne  -  même brièvement  -  il peut bloquer les connexions des utilisateurs, interrompre l'accès aux API et perturber les fonctionnalités principales de l'application. Dans le monde numérique d'aujourd'hui, où l'identité est la porte d'entrée de chaque expérience produit, le temps d'arrêt n'est pas envisageable. Une identité toujours disponible  -  capable de survivre aux pannes régionales et de se mettre à l'échelle sans effort avec la croissance des utilisateurs  -  n'est plus un luxe ; c'est une exigence critique pour les applications modernes opérant à l'échelle mondiale.

C'est là qu'intervient [Ory](https://www.ory.sh/). Cette solution de gestion des identités et des accès (IAM) de premier plan aide les organisations à moderniser leurs piles d'authentification et d'autorisation avec une approche composable et cloud native. Ory s'est imposé comme un pionnier dans la fourniture d'outils IAM flexibles, évolutifs et conviviaux pour les développeurs d'applications modernes.

Parmi les entreprises qui tirent parti d'Ory pour répondre à ces exigences figure [OpenAI](https://www.ory.sh/case-studies/openai), qui avait besoin d'une infrastructure IAM résiliente et multi-région pour soutenir l'accès mondial des utilisateurs à ChatGPT. Cet article explore comment OpenAI a intégré Ory avec CockroachDB pour construire un système d'authentification toujours disponible, ainsi que les leçons apprises lors de la construction d'une solution IAM hautement disponible.

---

## Résumé Exécutif

- **Les applications modernes exigent une identité toujours disponible :** Les systèmes de gestion des identités et des accès (IAM) hérités ne peuvent pas répondre aux attentes des utilisateurs mondiaux, toujours connectés d'aujourd'hui. Un temps d'arrêt dans l'IAM peut paralyser les expériences produits.
- **Ory redéfinit l'IAM pour l'ère cloud native :** Ory fournit des composants IAM modulaires, open-source et orientés API qui se mettent à l'échelle indépendamment et prennent en charge des cas d'usage complexes comme le contrôle d'accès à grain fin, la connexion sans mot de passe et les connexions sociales.
- **Le défi d'OpenAI, la mise à l'échelle de l'IAM :** Avec la croissance explosive de ChatGPT, OpenAI avait besoin d'une plateforme CIAM résiliente et multi-région capable de fonctionner de manière transparente à travers les géographies, de soutenir une itération rapide et de rester neutre vis-à-vis des fournisseurs.
- **La solution Ory + CockroachDB :** OpenAI a déployé la pile d'identités d'Ory sur CockroachDB, notre base de données SQL distribuée connue pour sa résilience de niveau entreprise, afin d'obtenir une cohérence mondiale, un basculement automatisé et une haute disponibilité entre les régions.
- **IAM sécurisée, évolutive et toujours disponible :** L'architecture décrite garantit que l'authentification et le contrôle d'accès restent cohérents et en ligne même lors de pannes régionales, permettant à OpenAI de servir des millions d'utilisateurs avec des expériences ininterrompues.
- **Principaux enseignements :** L'IAM toujours disponible est désormais une exigence de base pour les applications destinées aux clients. L'architecture pour la résilience et l'évolutivité, comme démontré par le partenariat Ory et CockroachDB, est essentielle pour répondre aux demandes modernes.

---

## Présentation d'Ory : IAM Moderne, Flexible et Évolutif

Ory fournit une suite puissante d'outils de gestion des identités et des accès, conçus dès le départ pour prendre en charge les systèmes distribués et les architectures cloud natives. Au cœur des [offres](https://www.ory.sh/deployment-solutions) d'Ory se trouve un ensemble de services modulaires orientés API conçus pour traiter divers aspects de la gestion des identités et des accès. Ils comprennent des composants tels que :

- [Ory Kratos](https://www.ory.sh/kratos) pour la gestion des identités (y compris les utilisateurs, les groupes et les organisations)
- [Ory Hydra](https://www.ory.sh/hydra) pour les flux OAuth2 et OIDC
- [Ory Keto](https://www.ory.sh/keto) pour le contrôle d'accès à grain fin et le contrôle d'accès basé sur les relations (ReBAC, inspiré de Google Zanzibar)
- [Ory Oathkeeper](https://www.ory.sh/oathkeeper) pour l'authentification en périphérie et le contrôle d'accès au niveau des requêtes avec un Proxy d'Identité et d'Accès

Chacun de ces services est conçu pour se mettre à l'échelle indépendamment et s'intégrer de manière transparente, offrant aux équipes la flexibilité d'adapter leurs systèmes IAM à leurs besoins exacts. En découplant les préoccupations telles que [l'identité, l'autorisation et la fédération](/2025-05-23-iam-guide/), Ory permet aux organisations d'adopter un modèle de sécurité composable qui est à la fois robuste et extensible.

L'engagement d'Ory envers les principes open-source a favorisé une communauté de développeurs et de contributeurs dynamique. [Les projets de l'entreprise](https://github.com/ory) ont suscité une attention considérable, avec plus de 35 000 étoiles GitHub et une présence dans plus de 50 000 déploiements actifs dans le monde. Cette approche pilotée par la communauté garantit une amélioration continue, la transparence et l'adaptabilité aux besoins évolutifs du paysage numérique.

En plus de ses offres open-source, Ory fournit une solution SaaS entièrement gérée via le [Réseau Ory](https://www.ory.sh/network)  -  une plateforme IAM mondiale à haute disponibilité qui offre des services d'identité à faible latence. Cette plateforme prend en charge une gamme de méthodes d'authentification, y compris les passkeys, la connexion sans mot de passe, l'authentification multi-facteurs et les connexions sociales, répondant aux diverses exigences des applications modernes. Pour les organisations où l'infrastructure d'identité devient critique, et où vous avez besoin d'une fiabilité de niveau entreprise, Ory propose la Licence Entreprise Ory (OEL) qui fait le pont entre la flexibilité auto-hébergée et le support entreprise  -  vous donnant un support entreprise pour la préparation à la production et des releases extensivement testées qui maintient votre entreprise sécurisée et en mouvement.

<img src="/assets/img/iam-p2-ory-architecture.png" alt="Ory Architecture Overview" style="width:100%">

{: .mx-auto.d-block :}
**Figure 1 : Vue d'ensemble de l'Architecture Ory**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

---

## Le Cas d'Usage OpenAI : CIAM Multi-Région à Grande Échelle

Lorsqu'OpenAI a lancé ChatGPT en novembre 2022, il est rapidement devenu l'une des applications à la croissance la plus rapide de l'histoire  -  atteignant 1 million d'utilisateurs en cinq jours et dépassant 100 millions d'utilisateurs actifs mensuels en janvier 2023. En décembre 2024, ChatGPT comptait plus de 400 millions d'utilisateurs actifs hebdomadaires. Cette échelle sans précédent a engendré un besoin urgent d'une plateforme moderne et fiable de gestion des identités et des accès client (CIAM).

L'expansion rapide a exposé les limites des solutions CIAM traditionnelles, qui reposent souvent sur des architectures fermées et peu flexibles qui entravent la personnalisation, la transparence et l'auto-hébergement. Ces systèmes hérités ne pouvaient tout simplement pas répondre aux exigences d'OpenAI en matière de vélocité d'innovation, de contrôle de l'expérience utilisateur et d'intégration cloud native.

<img src="/assets/img/iam-p2-chatgpt-visits.png" alt="ChatGPT Daily Visits rapid expansion" style="width:100%">

{: .mx-auto.d-block :}
**Figure 2 : L'expansion rapide de ChatGPT**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Pour suivre la croissance du produit et l'évolution des attentes des utilisateurs, OpenAI avait besoin d'une solution CIAM capable de se mettre à l'échelle sans effort, de prendre en charge des analyses avancées et de fonctionner de manière transparente dans les environnements cloud. Il ne s'agissait pas seulement d'authentification  -  il s'agissait de construire une base pour des expériences sécurisées et centrées sur l'utilisateur à grande échelle.

Lorsqu'OpenAI s'est lancé dans la construction d'un système IAM multi-région, les exigences étaient claires : le système devait être résilient aux pannes régionales, capable de soutenir des bases d'utilisateurs mondiales, et cohérent dans l'application du contrôle d'accès et la gestion des sessions à travers ses services. Pour répondre à ces besoins, OpenAI a recherché une solution qui s'alignait sur son état d'esprit orienté produit  -  modulaire, transparente et sans [dépendance vis-à-vis des fournisseurs](https://www.cockroachlabs.com/blog/multi-cloud-deployment-distributed-sql/). Il avait besoin d'une infrastructure IAM capable d'évoluer aussi rapidement que les produits qu'elle supportait.

---

## La Solution : Ory et CockroachDB pour un CIAM Évolutif

OpenAI a choisi de s'associer à Ory pour apporter flexibilité et contrôle à son infrastructure d'identité. Au cœur de cette intégration se trouvait [Ory Hydra](https://www.ory.sh/hydra), un fournisseur OAuth2 et OpenID Connect à l'échelle du web, capable de gérer les autorisations à l'échelle mondiale. Ory se distinguait parmi les autres plateformes IAM comme la solution idéale. Sa conception modulaire, ses fondements open-source et sa compatibilité cloud native s'alignaient parfaitement avec les besoins d'OpenAI.

Cependant, pour atteindre une véritable disponibilité mondiale, il était essentiel d'associer les capacités IAM d'Ory à une base de données SQL distribuée capable de répondre aux exigences de la réplication inter-régions, des garanties de cohérence forte et de la tolérance aux pannes. C'est là que [CockroachDB](https://www.cockroachlabs.com/product/overview/) est entré en jeu.

CockroachDB est une base de données SQL distribuée conçue pour l'échelle mondiale et la haute disponibilité. Depuis qu'elle est devenue la première base de données SQL distribuée disponible commercialement, CockroachDB est connue pour sa résilience de niveau entreprise. Elle réplique les données dans plusieurs régions tout en offrant l'isolation sérialisable, la cohérence forte et le basculement automatique. En déployant les composants Ory sur CockroachDB, OpenAI a pu garantir que les données d'identité et de contrôle d'accès restaient cohérentes et toujours disponibles  -  même [lors de perturbations d'infrastructure](https://www.cockroachlabs.com/blog/database-testing-performance-under-adversity/). Par exemple, un utilisateur se connectant depuis l'Europe, alors qu'un centre de données aux États-Unis connaît une panne, pouvait toujours s'authentifier et autoriser des requêtes sans problème. Ce niveau de résilience était essentiel pour maintenir des expériences utilisateurs transparentes à travers les géographies.

<img src="/assets/img/iam-p1-cloud-portability.png" alt="How CockroachDB Enables Cloud Portability" style="width:100%">

{: .mx-auto.d-block :}
**Comment CockroachDB permet la portabilité dans le cloud**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

> **Mesurer ce qui compte**  -  Les benchmarks traditionnels ne testent que quand tout fonctionne parfaitement. Mais vous devez savoir ce qui se passe quand tout échoue. Le benchmark de CockroachDB, « Performance sous Adversité », teste des scénarios réels : partitions réseau, pannes régionales, blocages disque, et bien plus encore. [Voir en action](https://www.cockroachlabs.com/performance-under-adversity/?referralid=blogs_pua_launch_bottom_card)

Les tests approfondis du Réseau Ory avec CockroachDB ont démontré la capacité de la solution à offrir performances, résilience et élasticité sous une charge importante et un trafic inter-régions. Cette architecture a permis à OpenAI d'innover plus rapidement, tout en garantissant un accès sécurisé et ininterrompu pour des millions d'utilisateurs dans le monde. Grâce à une Licence Entreprise Ory, OpenAI a eu accès à des capacités d'autorisation avancées, ainsi qu'à la possibilité d'auto-héberger, d'affiner les configurations et de maintenir un contrôle total sur sa pile CIAM. Associée à la base de données résiliente et répliquée à l'échelle mondiale de CockroachDB, la solution offre une base IAM moderne qui évolue au rythme du développement d'OpenAI  -  soutenant la sécurité, la conformité et des expériences utilisateurs transparentes à grande échelle.

---

## Comment les Composants IAM Utilisent CockroachDB

L'intégration s'est concentrée sur trois services Ory principaux. Ory Kratos gérait la gestion des identités, y compris les identifiants des utilisateurs, les métadonnées de profil et les sessions. Ory Hydra servait de fournisseur OAuth2 et OIDC, gérant l'émission des tokens, les flux de consentement et l'enregistrement des clients. Ory Keto implémentait le contrôle d'accès à grain fin basé sur les relations inspirées de Google Zanzibar.

Chacun de ces composants s'appuyait sur CockroachDB pour stocker leur état de manière cohérente et durable, leur permettant de fonctionner correctement même en présence de pannes partielles ou de partitions réseau régionales. L'architecture d'Ory est bien adaptée pour fonctionner avec CockroachDB en raison de sa conception sans état et de sa philosophie orientée API. Chaque composant peut être déployé en tant que service sans état, sa seule exigence de persistance étant [la base de données SQL sous-jacente](https://www.cockroachlabs.com/blog/what-is-distributed-sql/). Cela facilite la mise à l'échelle horizontale des services, les mises à jour progressives, ou le déploiement de nouvelles régions sans avoir à orchestrer des migrations de données complexes. CockroachDB, à son tour, fournit la couche de base de données toujours cohérente qui garantit que les identités des utilisateurs, les règles de contrôle d'accès et les tokens de session sont toujours précis  -  quelle que soit la région qui sert une requête.

<img src="/assets/img/iam-p2-multi-region-architecture.png" alt="Ory CockroachDB Multi-Region Deployment Architecture" style="width:100%">

{: .mx-auto.d-block :}
**Figure 3 : Architecture de Déploiement Multi-Région Ory, CockroachDB**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

D'un point de vue technique, l'identité et l'autorisation dans ce système sont modélisées comme des entités structurées au sein de CockroachDB. L'utilisation des [transactions](https://www.cockroachlabs.com/docs/stable/transactions) fortement cohérentes de CockroachDB garantit que les opérations IAM restent correctes, même lorsqu'elles sont émises simultanément depuis différentes régions ou sous pression réseau.

### 1. Kratos

Kratos stocke les enregistrements d'identités des utilisateurs, les flux de récupération, les sessions et les tentatives de connexion dans des tables transactionnelles. Le diagramme ci-dessous illustre le modèle de données utilisé par Ory Kratos, le composant de gestion des identités et des utilisateurs de la pile Ory. Au cœur de ce schéma se trouve la table `identities`, qui représente les utilisateurs individuels dans le système. Presque toutes les autres tables du schéma se connectent à cette entité centrale, reflétant les différents aspects du cycle de vie de l'identité d'un utilisateur  -  des identifiants de connexion et des sessions aux flux de récupération et de vérification.

<img src="/assets/img/iam-p2-kratos-data-model.png" alt="Ory Kratos Data Model" style="width:100%">

{: .mx-auto.d-block :}
**Figure 4 : Modèle de Données Ory Kratos**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Chaque identité peut être associée à un ou plusieurs identifiants, stockés dans la table `identity_credentials`. Ces identifiants définissent comment un utilisateur s'authentifie auprès du système, par exemple via un mot de passe, une connexion sociale ou d'autres mécanismes. Le type de chaque identifiant  -  qu'il s'agisse d'un mot de passe, d'un token OpenID Connect ou d'une autre méthode  -  est défini dans la table `identity_credential_types`, garantissant une façon cohérente et extensible de catégoriser les mécanismes d'authentification. Pour prendre en charge des options de connexion flexibles, la table `identity_credential_identifiers` stocke des identifiants uniques tels que les noms d'utilisateur ou les adresses e-mail qui sont liés à des identifiants spécifiques.

Au-delà de l'authentification, Ory Kratos prend également en charge des flux complets de récupération et de vérification de compte. La table `identity_recovery_addresses` stocke des points de contact tels que les adresses e-mail de récupération qui peuvent être utilisées pour initier la récupération de compte. Associés à ceux-ci se trouvent les `identity_recovery_tokens`, qui représentent des tokens à usage unique émis lors des flux de récupération, permettant des opérations de réinitialisation ou de re-vérification sécurisées. De même, la table `identity_verifiable_addresses` suit les adresses vérifiables  -  généralement des e-mails  -  qui nécessitent une confirmation avant d'être approuvées par le système.

La table `sessions` garde une trace des sessions de connexion des utilisateurs, associant chaque session active à une identité spécifique. Cela permet au système de gérer le cycle de vie des sessions, l'expiration et les vérifications liées à la sécurité de manière distribuée et évolutive. Le flux d'interaction typique entre un client basé sur navigateur, une application backend et Ory Kratos est structuré comme suit :

<img src="/assets/img/iam-p2-kratos-flow.png" alt="Interaction flow using Ory Kratos" style="width:100%">

{: .mx-auto.d-block :}
**Figure 5 : Flux d'interaction avec Ory Kratos**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Le diagramme de séquence ci-dessus illustre un flux d'identité en libre-service typique utilisant Ory Kratos, impliquant une application frontend, une application backend et le service d'identité Kratos. Ce flux est courant dans des scénarios tels que la connexion des utilisateurs, l'inscription ou les mises à jour de profil, où le frontend gère l'interface utilisateur tandis que Kratos gère la logique d'identité.

Le processus commence lorsque l'application frontend initie un flux en libre-service en envoyant une requête GET à Ory Kratos  -  par exemple, au point de terminaison `/self-service/login/browser` ou `/self-service/registration/browser`. En réponse, Kratos renvoie un statut HTTP 200 OK avec un payload JSON qui décrit le flux. Ce payload contient les informations nécessaires pour afficher le formulaire approprié, telles que les champs requis et les données de configuration.

À l'aide de ce payload, le frontend affiche un formulaire avec lequel l'utilisateur peut interagir. L'utilisateur remplit ensuite le formulaire  -  que ce soit pour se connecter, s'inscrire ou mettre à jour son profil  -  et le soumet. L'application frontend transmet ensuite les données du formulaire soumis au point de terminaison en libre-service correspondant, en passant l'identifiant du flux comme paramètre de requête. Le payload contient les données d'entrée de l'utilisateur. Kratos valide ensuite le payload soumis. Si les données sont valides, il effectue l'action appropriée : par exemple, il peut créer un nouvel utilisateur, mettre à jour une adresse e-mail ou émettre un cookie de session pour connecter l'utilisateur. Si le payload est invalide  -  peut-être en raison de champs manquants ou de valeurs incorrectes  -  Kratos met à jour le flux avec des erreurs de validation et renvoie une réponse 400 Bad Request. Le frontend affiche ensuite à nouveau le formulaire avec les retours de validation, permettant à l'utilisateur de corriger ses entrées et de soumettre à nouveau.

Une fois que l'utilisateur a complété avec succès le flux et reçu un cookie de session de Kratos, le frontend peut utiliser ce cookie de session pour effectuer des requêtes authentifiées à l'application backend. Quand le backend reçoit ces requêtes, il délègue la validation de session à Kratos, qui confirme si la session est valide avant d'autoriser l'accès aux ressources protégées.

### 2. Hydra

Après avoir couvert la gestion des identités, voyons comment l'autorisation sécurisée est gérée avec Ory Hydra. Ory Hydra est une implémentation serveur du cadre d'autorisation OAuth 2.0 et d'OpenID Connect Core 1.0. Il suit les clients, les demandes de consentement et les tokens avec une cohérence forte pour prévenir les attaques par rejeu ou les autorisations en double.

Le cadre d'autorisation OAuth 2.0 permet à une application tierce d'obtenir un accès limité à un service HTTP, soit au nom d'un propriétaire de ressource en orchestrant une interaction d'approbation entre le propriétaire de la ressource et le service HTTP, soit en permettant à l'application tierce d'obtenir un accès en son propre nom.

<img src="/assets/img/iam-p2-oauth2-flow.png" alt="OAuth2 Flow" style="width:100%">

{: .mx-auto.d-block :}
**Figure 6 : Flux OAuth2**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Le flux d'autorisation OAuth 2.0 impliquant une application cliente, le propriétaire de la ressource, Ory Hydra (en tant que serveur d'autorisation) et le serveur de ressources est structuré comme suit :

<img src="/assets/img/iam-p2-hydra-flow.png" alt="Interaction flow using Ory Hydra" style="width:100%">

{: .mx-auto.d-block :}
**Figure 7 : Flux d'interaction avec Ory Hydra**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Le diagramme de séquence représente les interactions entre quatre composants clés : le Client, le Propriétaire de la Ressource (généralement l'utilisateur), Ory Hydra et le Serveur de Ressources (l'API ou le service qui héberge les ressources protégées).

Le flux commence lorsque le Client  -  une application cherchant à accéder à des ressources protégées  -  initie une demande d'autorisation auprès du Propriétaire de la Ressource. Cela prend généralement la forme d'une redirection vers un écran de connexion ou de consentement fourni par le Serveur d'Autorisation (Ory Hydra). Le Propriétaire de la Ressource examine la demande et, après avoir accordé l'accès, fournit un accord d'autorisation (souvent un code d'autorisation) au client.

Ensuite, le Client utilise cet accord d'autorisation pour demander un token d'accès à Ory Hydra. Avec l'accord, le client s'authentifie également (en utilisant des identifiants tels qu'un identifiant client et un secret). Ory Hydra valide l'accord d'autorisation et les identifiants du client. Si tout est en ordre, il répond en émettant un token d'accès au client.

Armé du token d'accès, le Client effectue ensuite une requête au Serveur de Ressources, présentant le token comme preuve d'autorisation. Le Serveur de Ressources valide le token d'accès  -  souvent en l'inspectant via Hydra ou en vérifiant sa signature s'il s'agit d'un JWT (JSON Web Token)  -  et, s'il est valide, sert la ressource protégée demandée au client.

Ce flux encapsule le modèle standard de Code d'Autorisation dans OAuth 2.0, avec Ory Hydra remplissant le rôle d'un serveur d'autorisation sécurisé et conforme aux standards qui gère l'émission des tokens, la validation et l'application des politiques. Il est conçu pour séparer les préoccupations entre les applications et les services, permettant un accès délégué évolutif et sécurisé.

Le modèle de données suivant représente l'implémentation du flux OAuth2 dans Ory Hydra. Ce schéma décrit comment les flux OAuth2 et OIDC sont gérés, depuis l'enregistrement des clients jusqu'à l'émission des tokens d'accès, des tokens de rafraîchissement, des codes d'autorisation et la gestion des sessions d'authentification.

<img src="/assets/img/iam-p2-hydra-data-model.png" alt="Ory Hydra Data Model" style="width:100%">

{: .mx-auto.d-block :}
**Figure 8 : Modèle de Données Ory Hydra**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Au cœur de ce schéma se trouve la table `hydra_client`, qui définit les clients OAuth2/OIDC enregistrés au sein d'un Réseau Hydra. Ces clients représentent des applications qui peuvent initier des flux d'autorisation et demander des tokens d'accès. Chaque flux majeur  -  code d'autorisation, token d'accès, token de rafraîchissement et autorisation de dispositif  -  est lié à un client spécifique.

La table `hydra_oauth2_flow` modélise le cycle de vie d'un flux d'autorisation OAuth2. Elle sert d'entité unificatrice qui relie les différentes étapes d'une transaction OAuth2 : codes d'autorisation, codes de dispositifs, tokens d'accès et tokens de rafraîchissement. Ce modèle centré sur les flux offre une traçabilité sur tous les identifiants émis et garantit une gestion cohérente des décisions d'autorisation.

La table `hydra_oauth2_code` stocke les codes d'autorisation de courte durée émis lors du Flux de Code d'Autorisation OAuth2. Ces codes sont échangés par les clients contre des tokens d'accès et de rafraîchissement. Chaque code est lié à un flux et un client spécifiques, et indirectement à la session d'authentification de l'utilisateur lorsqu'elle est présente.

Pour prendre en charge OpenID Connect, la table `hydra_oauth2_oidc` stocke des informations spécifiques à OIDC telles que les données de token d'identité ou les valeurs nonce. Ces entrées sont liées à un flux et un client, garantissant la conformité avec les spécifications OIDC superposées à OAuth2. Les flux d'authentification basés sur les dispositifs sont gérés par la table `hydra_oauth2_device_auth_codes`. Cela prend en charge l'Accord d'Autorisation de Dispositif OAuth2, permettant la connexion sur des dispositifs aux capacités d'entrée limitées.

Les tokens d'accès sont stockés dans la table `hydra_oauth2_access`, qui inclut des informations sur la portée du token, l'expiration et le flux associé. Ces tokens sont émis après une autorisation réussie et constituent le principal moyen par lequel les clients accèdent aux ressources protégées. Pour les sessions de longue durée, Hydra prend en charge les tokens de rafraîchissement, qui sont stockés dans la table `hydra_oauth2_refresh`. Ces tokens permettent aux clients de demander de nouveaux tokens d'accès sans ré-authentifier l'utilisateur.

L'état d'authentification est géré dans la table `hydra_oauth2_authentication_session`. Cette relation optionnelle lie un flux à une session d'authentification spécifique, suivant des détails comme l'heure à laquelle l'utilisateur s'est authentifié et si une ré-authentification est nécessaire. Cela aide à appliquer des politiques comme `prompt=login` ou l'expiration de session.

Ensemble, ces tables forment un schéma hautement normalisé qui s'aligne sur les standards OAuth2 et OIDC tout en offrant une visibilité et un contrôle complets sur chaque partie du processus d'autorisation. La table `hydra_oauth2_flow` sert de point de coordination central, garantissant que tous les tokens, codes et sessions font partie d'un flux traçable et auditable  -  idéal pour les systèmes d'identité conformes à grande échelle.

### 3. Keto

Keto exprime le contrôle d'accès sous forme de relations, mappant les sujets, les objets et les permissions d'une manière qui permet des vérifications de permissions efficaces même à très grande échelle. Le diagramme ci-dessous montre le modèle de données principal utilisé par Ory Keto, le service d'autorisation d'Ory inspiré de Google Zanzibar. Keto modélise le contrôle d'accès à grain fin via les `keto_relation_tuples`, qui expriment les permissions comme des relations entre les sujets et les objets. Chaque ligne dans cette table est un *tuple de relation*, décrivant qui (sujet) peut faire quoi (relation) sur quelle ressource (objet) au sein d'un espace de noms défini.

<img src="/assets/img/iam-p2-keto-data-model.png" alt="Ory Keto Data Model" style="width:100%">

{: .mx-auto.d-block :}
**Figure 9 : Modèle de Données Ory Keto**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Dans Ory Keto, l'autorisation est vérifiée en évaluant si un tuple de relation existe (directement ou par expansion récursive) qui permet à un sujet donné d'effectuer une relation sur un objet dans un espace de noms. Ce modèle de données est conçu pour une haute évolutivité et flexibilité, permettant des modèles d'accès complexes tels que l'appartenance à des groupes, l'héritage de rôles et les droits d'accès hiérarchiques.

Une interaction typique entre un utilisateur, une application, Ory Kratos et Ory Keto ressemble à ceci :

<img src="/assets/img/iam-p2-keto-kratos-flow.png" alt="Interaction flow between Ory Keto and Ory Kratos" style="width:100%">

{: .mx-auto.d-block :}
**Figure 10 : Flux d'interaction entre Ory Keto et Ory Kratos**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Le processus commence lorsque le sujet initie une demande d'accès à une ressource via l'application. Après avoir reçu la demande, l'application délègue d'abord la tâche de vérification de l'identité de l'utilisateur à Ory Kratos, qui est responsable de l'authentification des utilisateurs. Kratos authentifie le sujet  -  généralement en validant les identifiants, les tokens de session ou les cookies  -  et répond à l'application en confirmant l'identité de l'utilisateur.

Une fois l'authentification réussie, l'application doit alors déterminer si le sujet authentifié dispose des permissions nécessaires pour accéder à la ressource demandée. Pour ce faire, elle envoie une requête d'autorisation à Ory Keto, en demandant si le sujet est autorisé à effectuer une action spécifique (dans ce cas, « lire ») sur la ressource spécifiée (par exemple, « ressource x »). Ory Keto évalue la requête par rapport à ses politiques d'autorisation stockées. Si le sujet est autorisé à effectuer l'action demandée, Keto répond avec une réponse « Permissions Accordées ». Avec l'authentification et l'autorisation toutes deux terminées avec succès, l'application procède à la restitution de la ressource demandée au sujet.

- Ory Kratos gère **qui est l'utilisateur**
- Ory Keto détermine **ce que l'utilisateur est autorisé à faire**

Ce flux assure une séparation claire des préoccupations, formant un modèle sécurisé et évolutif pour la gestion des accès dans les applications modernes.

---

## Ory et CockroachDB : La Combinaison pour la Gestion des Identités de Nouvelle Génération

OpenAI fait évoluer rapidement son infrastructure d'identité, atteignant déjà des taux de connexion record tout en maintenant des niveaux de transparence des données et de flexibilité d'infrastructure qui étaient auparavant inaccessibles avec les solutions de fournisseurs traditionnels. Cette transformation reflète un changement fondamental vers une architecture d'identité moderne et centrée sur les développeurs  -  une architecture qui priorise la vitesse, la visibilité et l'adaptabilité.

En adoptant Ory et CockroachDB, OpenAI a acquis la capacité d'innover rapidement, en développant et en itérant sur des solutions d'identité adaptées à une large gamme de cas d'usage à travers son écosystème de produits en expansion. La conception modulaire et extensible de la plateforme permet à OpenAI de répondre rapidement aux nouvelles exigences sans être contraint par des systèmes rigides ou opaques. L'évolutivité a également été un avantage critique. À mesure que la demande mondiale pour les services d'IA continue d'augmenter, OpenAI peut faire évoluer ses systèmes d'identité de manière transparente, garantissant des performances et une fiabilité constantes à grande échelle. Une observabilité approfondie des flux d'authentification et des opérations IAM permet à l'équipe d'optimiser proactivement l'expérience utilisateur, de renforcer la sécurité et de résoudre les goulots d'étranglement de performance avec précision.

Peut-être plus important encore, la résilience a été un facteur déterminant. Même au milieu d'une croissance exponentielle des utilisateurs, l'architecture d'Ory couplée à un backend de stockage résilient comme CockroachDB permet des services d'identité fiables et toujours disponibles qui soutiennent un accès ininterrompu et un engagement sécurisé. Alors qu'OpenAI continue de se développer, le besoin d'une plateforme d'identité hautement disponible, transparente et observable ne fera que s'intensifier  -  et les capacités CIAM modernes d'Ory sont bien positionnées pour relever ce défi, surpassant largement les limitations des systèmes hérités.

> *« Pour les entreprises mondiales, l'IAM ne peut pas être une réflexion après coup. L'IAM moderne exige un accès sécurisé, conforme et multi-région dès le premier jour, sans les goulots d'étranglement des bases de données héritées. Nous avons construit Ory sur CockroachDB pour son architecture intrinsèquement distribuée, permettant de véritables déploiements multi-régions et la localisation des données  -  essentiels pour une infrastructure d'identité critique. »*
>  -  Aenas Rekkas, CTO d'Ory

<img src="/assets/img/iam-p2-uninterrupted-access.png" alt="Uninterrupted access management with CockroachDB" style="width:100%">

{: .mx-auto.d-block :}
**Figure 11 : Gestion des accès ininterrompue avec CockroachDB**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Le déploiement d'OpenAI s'étend sur des centres de données distincts, chacun contenant un ensemble de nœuds CockroachDB. Bien que physiquement distribués, ces nœuds forment une base de données unifiée et logiquement cohérente. Malgré la défaillance d'un nœud ou d'un centre de données entier, le système global reste pleinement opérationnel. Cela est rendu possible par l'utilisation par CockroachDB du [protocole de consensus Raft](https://www.cockroachlabs.com/docs/stable/architecture/replication-layer.html#raft), qui permet à la base de données de continuer à traiter les lectures et les écritures tant qu'un quorum de répliques est disponible. Dans cette configuration, le cluster est toujours capable de servir le trafic d'authentification mondial d'OpenAI via les nœuds fonctionnels dans les centres de données sains, sans incohérence des données ni interruption de service.

---

## Intégration Ory et CockroachDB : Principaux Enseignements

Tout au long du processus d'intégration d'Ory avec CockroachDB, plusieurs leçons clés ont émergé. Premièrement, garantir la compatibilité des schémas et minimiser les latences inter-régions est essentiel pour les charges de travail sensibles aux performances comme l'authentification. L'optimisation des charges de travail transactionnelles pour éviter les points chauds et l'exploitation des [capacités multi-régions de CockroachDB](https://www.cockroachlabs.com/docs/stable/multiregion-overview)  -  telles que les [lectures suiveur](https://www.cockroachlabs.com/docs/stable/follower-reads) et le [géo-partitionnement](https://www.cockroachlabs.com/docs/stable/partitioning)  -  ont été essentielles pour atteindre des performances optimales.

<img src="/assets/img/iam-p2-data-locality.png" alt="Data locality  -  common patterns for table locality with CockroachDB" style="width:100%">

{: .mx-auto.d-block :}
**Figure 12 : Localité des données  -  modèles courants de localité de tables avec CockroachDB**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Deuxièmement, la [surveillance et l'observabilité](https://www.cockroachlabs.com/docs/stable/monitoring-and-alerting.html) étaient indispensables. La combinaison des journaux, des métriques et des traces distribuées a aidé à identifier les goulots d'étranglement et à optimiser les chemins de latence à travers les services et les régions. Enfin, l'adoption d'une plateforme IAM modulaire et basée sur les standards comme Ory a accéléré l'implémentation et facilité le raisonnement sur les domaines de défaillance et les dépendances entre services.

<img src="/assets/img/iam-p2-distributed-iam.png" alt="Distributed identity and access management (IAM) platform" style="width:100%">

{: .mx-auto.d-block :}
**Figure 13 : Plateforme de gestion des identités et des accès (IAM) distribuée**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Pour les organisations cherchant à construire des architectures similaires, la combinaison d'Ory et de CockroachDB offre un modèle puissant : une IAM composable et évolutive soutenue par une base de données SQL résiliente et distribuée à l'échelle mondiale. Que vous serviez des utilisateurs dans une seule région ou que vous couvriez plusieurs continents, cette approche fournit une base solide pour construire des systèmes d'identité sécurisés, disponibles et cohérents. Le parcours d'OpenAI met en évidence la valeur d'investir dans des technologies cloud natives et open-source qui travaillent ensemble pour offrir une authentification véritablement toujours disponible.
