---
layout: post
lang: fr
title: "Du Mainframe au SQL Distribué, Partie 4"
subtitle: "Planifier Votre Stratégie de Modernisation des Données"
cover-img: /assets/img/cover-mainframe-p4.webp
thumbnail-img: /assets/img/cover-mainframe-p4.webp
share-img: /assets/img/cover-mainframe-p4.webp
tags: [mainframe, CockroachDB, migration, modernization, strategy]
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

Les systèmes mainframe existants constituent depuis longtemps l'épine dorsale des opérations critiques dans la finance, la santé et le secteur public. Cependant, à mesure que la technologie évolue, ces systèmes vieillissants deviennent souvent coûteux à maintenir, difficiles à intégrer avec les applications modernes et inefficaces pour répondre aux exigences numériques actuelles. La migration des bases de données et applications mainframe vers des plateformes modernes est de plus en plus perçue comme un impératif stratégique, offrant une scalabilité, une flexibilité et des économies de coûts améliorées.

Cependant, la migration de systèmes existants présente ses propres complexités : elle implique une transition technique et la préservation de la logique métier critique et de l'intégrité des données. Les organisations doivent planifier, exécuter et valider méticuleusement le processus de migration pour minimiser les perturbations et s'assurer que le système fonctionne correctement.

Cet article explore les étapes essentielles et les meilleures pratiques pour préparer une migration réussie de bases de données et d'applications mainframe existantes, depuis l'évaluation de la maturité du système jusqu'à la garantie d'une transition transparente vers une infrastructure moderne.

---

## Évaluation et analyse

Avant d'entreprendre la migration de systèmes mainframe existants, il est essentiel de procéder à une évaluation approfondie des bases de données existantes. Ce processus aide à identifier le périmètre de la migration, les défis impliqués et la meilleure stratégie pour assurer une transition fluide. Voici les éléments clés d'une évaluation complète :

### 1. Évaluation globale

Réalisez des évaluations détaillées de vos applications et bases de données existantes afin d'obtenir des informations précieuses sur votre configuration actuelle. Cela rendra le processus de migration plus fluide et plus prévisible.

L'analyse du code source est cruciale pour découvrir les complexités cachées, les dépendances et les problèmes potentiels au sein des applications et de leurs bases de données associées. Cette analyse aide à révéler comment chaque application interagit avec la base de données, mettant en évidence les composants étroitement couplés ou les dépendances obsolètes qui pourraient entraver le processus de migration.

De même, l'évaluation de l'architecture applicative est essentielle pour identifier les zones de dette technique et les faiblesses structurelles qui peuvent nécessiter d'être traitées avant la migration. En générant des rapports complets sur la qualité du code, les flux de données et les interdépendances, les organisations peuvent efficacement planifier la remédiation, le refactoring ou même la re-architecture de composants spécifiques pour assurer un meilleur alignement avec l'environnement cible.

### 2. Analyse des structures de données, alignement des schémas

Les bases de données mainframe s'appuient souvent sur des modèles hiérarchiques ou réseau tels que les [Information Management Systems (IMS)](/2024-10-10-mainframe-to-distributed-sql-part-1/#information-management-system-ims) ou les [Integrated Database Management Systems (IDMS)](/2024-10-10-mainframe-to-distributed-sql-part-1/#integrated-database-management-system-idms), qui diffèrent considérablement des bases de données relationnelles modernes telles que SQL ou NoSQL. Comprendre la structure sous-jacente de la base de données actuelle est critique pour identifier les écarts de compatibilité entre les schémas des bases de données source et cible. Les principales considérations lors de cette phase comprennent :

- **Évaluation du modèle de données** : Examiner la structure logique et physique des bases de données, y compris les tables, les index et les relations entre les entités de données.

- **Volume et complexité** : Déterminer la taille des bases de données, la complexité des requêtes et la nature des données (structurées, non structurées ou semi-structurées) pour planifier les exigences de stockage et de performance dans le système cible.

- **Normalisation des données** : Identifier toute redondance ou inefficacité dans la structure de données qui pourrait être optimisée lors de la migration.

Une évaluation complète devrait couvrir l'environnement de la base de données cible avec la même importance que celui de la source. Il est crucial de découvrir les discordances architecturales. Cela est particulièrement important lors de la migration de bases de données de systèmes sur site vers le cloud. Une telle évaluation devrait inclure :

- l'analyse des types de données
- le mapping des données
- les technologies de transformation des données
- la sécurité des données
- les formats de stockage

### 3. Identification des dépendances

Les systèmes mainframe existants sont souvent imbriqués avec d'autres applications, sous-systèmes ou services externes. Une migration réussie nécessite une compréhension approfondie de ces dépendances pour éviter de rompre des intégrations ou des flux de travail. Veuillez prendre note des informations suivantes :

- **Dépendances applicatives** : Il est important de détailler quelles applications dépendent de la base de données mainframe et comment elles interagissent. Certaines applications peuvent utiliser des connexions directes à la base de données, tandis que d'autres peuvent s'appuyer sur le traitement par lots ou les systèmes de messagerie.

- **Flux de données et modèles d'utilisation** : L'analyse de la façon dont les données sont lues, écrites ou mises à jour dans les systèmes est essentielle. Cette analyse aide à prioriser les transactions à haute fréquence et à identifier les chemins de données critiques qui doivent rester opérationnels pendant la migration.

- **Interfaces externes** : L'identification de tout système externe ou service tiers avec lequel le mainframe interagit est cruciale, tels que les services de traitement financier ou les plateformes de chaîne d'approvisionnement. Ces points d'intégration devront être soigneusement re-architecturés ou reconnectés après la migration.

### 4. Évaluation des points d'intégration

L'intégration est critique dans les environnements mainframe, car ils servent souvent de hubs centraux pour le traitement et la distribution des données sur différentes plateformes. Le succès d'une migration dépend de la capacité à préserver ou répliquer ces points d'intégration dans le nouvel environnement. Les domaines de concentration comprennent :

- **Middleware et systèmes de messagerie** : Évaluer le rôle du middleware (comme IBM MQ ou d'autres courtiers de messagerie) dans la configuration actuelle. Ces systèmes facilitent souvent la communication entre le mainframe et les services ou applications externes, et leurs configurations doivent être répliquées dans l'architecture cible.

- **Points d'entrée API** : Identifier les APIs qui fournissent l'accès aux données mainframe pour d'autres systèmes. Moderniser ces APIs ou en créer de nouvelles peut être nécessaire pour assurer la compatibilité avec les plateformes modernes.

- **Planifications des traitements par lots** : Évaluer les traitements par lots qui s'appuient sur le mainframe pour le traitement des données. Ces traitements peuvent nécessiter d'être repensés pour la nouvelle plateforme afin de s'assurer que leur timing et leurs dépendances sont pris en compte pendant la migration.

Les organisations peuvent construire une base solide pour leurs efforts de migration en réalisant cette évaluation complète de la base de données mainframe. Elle garantit que les éléments critiques tels que l'intégrité des données, les dépendances et les points d'intégration sont bien compris et traités, minimisant le risque de perturbation et maximisant le succès du processus de migration. Cependant, cet exercice n'est valide que s'il est associé à une définition du périmètre pour la migration, que nous expliquons plus loin dans la section suivante.

---

## Identification des cibles de modernisation

Une étape critique dans une migration réussie de systèmes existants est l'identification et la priorisation des applications et bases de données à moderniser en premier. Compte tenu de la complexité et de l'étendue de nombreux environnements mainframe, migrer tout en même temps est impraticable. Sur la base d'un ensemble de considérations, les organisations peuvent prioriser les systèmes en fonction de leur impact métier, de leur complexité technique et de leur alignement avec les objectifs stratégiques à long terme.

### 1. Évaluation de la criticité métier

La valeur métier d'une application ou d'une base de données est l'un des facteurs les plus importants pour déterminer sa priorité de migration. Les systèmes essentiels aux opérations quotidiennes ou aux processus orientés clients devraient souvent être à l'avant-plan de tout effort de modernisation. À cette étape, vous devez vous demander : « Pourquoi dois-je changer le statu quo ? » Cette migration vise-t-elle à gagner de l'argent ? Économiser de l'argent ? Atténuer les risques ? Ou tout cela à la fois ?

La priorisation des systèmes critiques garantit que l'activité continue de fonctionner sans heurts tout en tirant parti des avantages du nouvel environnement. Les principales considérations comprennent :

- **Impact sur les revenus** : Les systèmes directement liés à la génération de revenus, tels que les plateformes de transactions financières, devraient figurer en tête de la liste des priorités pour une migration précoce.

- **Engagement client** : Les applications qui interagissent avec les clients, telles que les portails en ligne ou les systèmes d'assistance, doivent être modernisées tôt pour maintenir un avantage concurrentiel.

- **Dépendance opérationnelle** : Pour minimiser les perturbations, les systèmes fondamentaux qui affectent la capacité d'une entreprise à fonctionner, tels que la gestion de la chaîne d'approvisionnement ou les systèmes de paie, devraient également être priorisés dans le processus de migration.

### 2. Évaluation de la complexité technique

La complexité technique d'une application ou d'une base de données influence le niveau d'effort requis pour la migration. Les systèmes plus complexes peuvent nécessiter un refactoring, une re-architecture ou un re-platforming extensifs pour assurer la compatibilité avec les environnements modernes. Les organisations peuvent développer des chronologies réalistes et allouer efficacement les ressources en évaluant les défis techniques en amont. Considérez les éléments suivants :

- **Complexité du code** : Les applications avec de grandes bases de code monolithiques ou des personnalisations complexes peuvent être plus difficiles à migrer et nécessitent un effort significatif pour découpler et moderniser.

- **Dépendances existantes** : Les systèmes qui reposent sur des technologies obsolètes ou propriétaires, telles que COBOL ou PL/I, nécessitent souvent une attention supplémentaire lors de la migration, y compris une potentielle réécriture ou un remplacement du code.

- **Complexité d'intégration** : Les applications profondément intégrées avec de multiples sous-systèmes ou services externes peuvent nécessiter un travail supplémentaire pour assurer une intégration fluide après la migration.

### 3. Alignement avec les objectifs stratégiques et la feuille de route

La stratégie métier doit être « LE MOTEUR » de votre projet de modernisation. Une stratégie de migration réussie doit renforcer votre stratégie métier globale et traiter en premier lieu les besoins métier pour générer une valeur précise et discernable.

Les efforts de modernisation devraient s'aligner sur les objectifs stratégiques plus larges de l'organisation. Les organisations peuvent s'assurer que leurs investissements en migration génèrent des résultats significatifs en se concentrant sur les systèmes qui sont au cœur de la réalisation de la croissance métier ou des objectifs de transformation numérique. Cela implique d'aligner la migration des applications avec la vision future et les feuilles de route technologiques de l'entreprise :

- **Stratégie de passage au cloud** : Si l'organisation se dirige vers une architecture cloud-first ou hybride, priorisez les applications et bases de données qui sont bien adaptées aux environnements cloud ou qui nécessitent scalabilité et élasticité.

- **Agilité et innovation** : Les applications qui soutiennent l'innovation, telles que celles permettant l'analyse de données, l'apprentissage automatique ou les plateformes mobiles, devraient être priorisées pour stimuler les initiatives de transformation numérique.

- **Conformité réglementaire et sécurité** : Les systèmes nécessitant des fonctionnalités de sécurité améliorées ou une conformité avec des réglementations en évolution peuvent nécessiter une migration plus rapide pour répondre aux exigences de gouvernance dans les architectures modernes.

Notez que tout désalignement avec une stratégie métier pourrait entraîner la priorisation des mauvais projets, la génération d'informations fausses ou inutiles, ou le gaspillage de temps et d'argent en allouant des ressources rares à des activités non rentables. Pire encore, cela pourrait conduire à une perte d'intérêt et de confiance dans toute initiative de migration au sein de l'organisation !

Le second élément important dans la construction d'une stratégie de migration est la définition d'objectifs mesurables. Lors de la construction d'une stratégie de modernisation, il est essentiel de fixer des objectifs quantifiables à court et à long terme. En tant que responsable d'une initiative de migration, vous êtes chargé d'atteindre le succès dans trois domaines clés : la croissance des revenus, l'efficacité opérationnelle et la gestion des risques de sécurité/confidentialité. En établissant des indicateurs de succès, vous priorisez en fonction de ce qui compte le plus pour votre organisation en ce moment.

N'oubliez pas d'inclure les contraintes suivantes dans la feuille de route de votre stratégie de modernisation :

- disponibilité du personnel et ressources externes nécessaires
- processus de budgétisation avec considérations d'investissement en capital
- projets concurrents et simultanés qui pourraient limiter les ressources disponibles
- jalons et carrefours majeurs de l'entreprise comme les nouvelles sorties de produits ou les fusions-acquisitions

### 4. Équilibre entre gains rapides et valeur à long terme

Chaque objectif que vous fixez doit avoir un plan d'action pour l'atteindre. Les plans doivent être spécifiques et inclure des considérations clés telles que :

- qui est responsable de l'objectif
- quelles technologies et processus ils utiliseront
- le coût pour atteindre l'objectif
- le temps nécessaire pour réaliser l'objectif
- le résultat attendu à la réalisation de l'objectif

Les plans doivent également rester flexibles pour tenir compte des circonstances imprévues ou des changements inattendus.

Bien que les grands projets de migration se concentrent souvent sur la valeur à long terme, il est bénéfique d'obtenir des succès rapides. La priorisation des applications ou bases de données à faible complexité mais à fort impact peut fournir des succès rapides et visibles qui créent un élan pour l'ensemble de l'initiative de migration. Ces gains rapides peuvent aider à obtenir l'adhésion des parties prenantes et à démontrer les avantages tangibles de la modernisation au début du processus.

<img src="/assets/img/mainframe-p4-prioritization-matrix.png" alt="La matrice de priorisation de la modernisation des données" style="width:100%">

{: .mx-auto.d-block :}
**La matrice de priorisation de la modernisation des données**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

---

## Engagement des parties prenantes

Toute stratégie de modernisation et/ou de migration ne pourra pas réussir sans le soutien de la direction. Les dirigeants de votre organisation ne soutiendront votre initiative que s'il existe un alignement clair entre votre stratégie de modernisation et la stratégie métier globale.

Cela signifie que la première étape d'une stratégie de modernisation réussie consiste à démontrer comment la migration des bases de données mainframe peut soutenir leurs objectifs et plans. Ensuite, identifiez et encouragez des champions métier à considérer les bases de données cibles, comme CockroachDB, comme des actifs précieux pour leurs départements ou fonctions spécifiques. À cette fin, établissez des objectifs clairs et des indicateurs mesurables pour votre stratégie de données qui servent votre stratégie métier plus large.

La deuxième étape consiste à obtenir le soutien et l'alignement des principales parties prenantes de l'organisation pour l'initiative de modernisation. L'alignement de la stratégie de modernisation avec la stratégie métier est un bon point de départ, mais ce n'est pas suffisant si vous n'alignez pas votre initiative avec les capacités organisationnelles.

Les départements ou équipes devraient avoir leurs propres objectifs locaux, qui peuvent être plus ou moins alignés avec votre initiative de modernisation. Par exemple, chaque département/fonction doit répondre à la question : « Que voulons-nous accomplir d'ici l'année prochaine ? » avec un plan d'action décrivant comment ils peuvent s'intégrer dans votre plan de migration pour atteindre leur(s) résultat(s) souhaité(s).

La feuille de route résulte de tout votre travail acharné rassemblant les objectifs à court et long terme, l'identification des objectifs globaux et locaux, et la négociation des priorités de ces mesures, rendant possible la mise en œuvre de vos plans. Vous savez où vous êtes et où vous voulez être. Cependant, les activités doivent d'abord être priorisées avant de commencer tout processus de conception, de construction ou de formation, ou lors de la modification d'une procédure métier.

Pour assurer une approche unifiée, les organisations doivent activement engager les parties prenantes et communiquer clairement la valeur de la modernisation. Voici plusieurs stratégies pour y parvenir :

- **Communiquer la valeur stratégique de la modernisation** : L'un des moyens les plus efficaces pour obtenir le soutien des parties prenantes est d'articuler clairement la valeur stratégique de la modernisation. Cela comprend la mise en évidence de la façon dont la migration s'aligne sur les objectifs à long terme de l'organisation, tels que l'amélioration de l'agilité, la réduction des coûts opérationnels, l'amélioration des expériences clients ou l'activation de futures innovations.

- **Engager les parties prenantes tôt et souvent** : Impliquer les parties prenantes dès le début de l'initiative de modernisation est essentiel pour favoriser la collaboration et assurer l'alignement au sein de l'organisation. L'engagement précoce permet aux parties prenantes d'exprimer leurs préoccupations, de fournir des avis et de devenir des participants actifs dans le processus de planification.

- **Démontrer des gains rapides et des succès précoces** : Une façon de gagner de l'élan et de renforcer la confiance dans l'initiative de modernisation est de démontrer des victoires précoces. Ces succès rapides fournissent des preuves tangibles de la valeur que la modernisation peut apporter, ce qui peut motiver les parties prenantes à continuer leur soutien.

- **Mettre en évidence l'impact sur les employés et les opportunités de montée en compétences** : Une initiative de modernisation peut souvent soulever des préoccupations quant à l'impact sur les employés, notamment dans les départements informatiques. Il est important d'aborder ces préoccupations en mettant en évidence les opportunités de croissance et de développement des employés.

---

## Construire votre dossier

Comme vous pouvez le constater, une préparation précoce et complète est essentielle pour une stratégie de modernisation réussie ! La migration vers une nouvelle base de données doit être guidée par **un solide argumentaire métier.** Un argumentaire métier bien conçu est essentiel pour obtenir l'adhésion des parties prenantes. L'argumentaire métier doit clairement exposer les avantages financiers, opérationnels et stratégiques de l'initiative de modernisation ainsi que les risques de l'inaction.

Vous devriez présenter une analyse détaillée des coûts liés au maintien des systèmes existants par rapport à l'investissement requis pour la modernisation. Mettez en évidence les économies potentielles liées à la réduction des coûts de maintenance, à l'amélioration de l'efficacité opérationnelle ou à la réduction de la dette technique.

Traitez les risques potentiels associés à la migration, tels que les temps d'arrêt ou les perturbations, et décrivez les stratégies d'atténuation. Démontrer un plan proactif de gestion des risques peut rassurer les parties prenantes et augmenter leur confiance dans l'initiative. Examinez les cas d'usage et évaluez les indicateurs de performance clés tels que la vitesse des requêtes, la latence, l'utilisation des ressources et les facteurs budgétaires tels que le stockage, les licences et les coûts d'ingestion des données pour les environnements actuels et cibles.

Une évaluation approfondie garantit également que vos données sont prêtes pour la migration. Cela aide à identifier les technologies de transformation les plus appropriées et les méthodes de chiffrement pour protéger les données contre les risques de sécurité potentiels, à la fois en transit et dans le nouvel environnement.

Enfin, montrez le retour sur investissement projeté dans le temps, illustrant comment la modernisation apportera de la valeur à court et à long terme. Incluez des avantages quantitatifs tels que l'augmentation de la productivité, la réduction des temps d'arrêt et la baisse des coûts d'infrastructure. Prendre ces mesures mettra votre organisation sur la voie du succès en matière de modernisation des données.

---

## Références

1. Christina Salmi, [7 Elements of a Data Strategy](https://www.analytics8.com/blog/7-elements-of-a-data-strategy), Analytics8 Blog.
2. Leandro DalleMule et Thomas H. Davenport, [What's Your Data Strategy?](https://hbr.org/2017/05/whats-your-data-strategy), Harvard Business Review, mai-juin 2017.
