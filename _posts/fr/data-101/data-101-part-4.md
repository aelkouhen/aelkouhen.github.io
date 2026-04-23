---
date: 2023-02-03
layout: post
lang: fr
title: "Data 101, Partie 4"
subtitle: Le parcours de données
thumbnail-img: https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEiGVfhxhGXNWmcz3KjVzMDqz-tzg9eoB8cM5FOM0MB0gb8Qq9K4JMHl8klMWGUKlv00JDq-3QWMP5o30iXbZQs4UKzdFmlmk_0zI_nNthrmckHdqMybOayDxOg3QVYn847k6810U_ObpOoll_eXzMRbfEkKIcAh-A0v5qpSm0c0HJEYDqTSSe1qeLYG
share-img: https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEiGVfhxhGXNWmcz3KjVzMDqz-tzg9eoB8cM5FOM0MB0gb8Qq9K4JMHl8klMWGUKlv00JDq-3QWMP5o30iXbZQs4UKzdFmlmk_0zI_nNthrmckHdqMybOayDxOg3QVYn847k6810U_ObpOoll_eXzMRbfEkKIcAh-A0v5qpSm0c0HJEYDqTSSe1qeLYG
tags: [data journey,data lifecycle,data value chain,data ingestion,data storage,data processing,data serving,data101]
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

Dans le dernier épisode, nous avons vu que les stratégies de données réussies nécessitent de revoir les plateformes de données existantes et d'analyser comment les utilisateurs métier peuvent en tirer parti. De plus, toute stratégie de données nécessite les bons outils et technologies pour fonctionner comme prévu. Ici, l'architecture de données est centrale dans le choix des bons outils et processus qui vous permettent de concevoir une plateforme de données adéquate pour votre organisation.

Dans cet article, j'introduirai le concept du parcours de données et comment les données brutes augmentent en valeur au fil de leurs multiples étapes.

## Vue d'ensemble

Le parcours de données ou la chaîne de valeur des données décrit les différentes étapes par lesquelles les données passent depuis leur création jusqu'à leur éventuelle suppression. Dans le contexte des plateformes de données, il comprend l'acquisition, le stockage, le traitement et la diffusion (partage, visualisation, monétisation...). Ce processus vise à garantir que la bonne information est disponible au bon moment pour la prise de décision, tout en protégeant contre l'accès non autorisé ou l'utilisation abusive.

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEiGVfhxhGXNWmcz3KjVzMDqz-tzg9eoB8cM5FOM0MB0gb8Qq9K4JMHl8klMWGUKlv00JDq-3QWMP5o30iXbZQs4UKzdFmlmk_0zI_nNthrmckHdqMybOayDxOg3QVYn847k6810U_ObpOoll_eXzMRbfEkKIcAh-A0v5qpSm0c0HJEYDqTSSe1qeLYG){: .mx-auto.d-block :} *Une architecture de données moderne représente toutes les étapes du parcours de données ©Semantix.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}  

Pour créer un parcours de données performant et adéquat pour les utilisateurs métier, les architectes de données se concentrent sur la façon dont les outils technologiques permettent à votre organisation et, par conséquent, à vos collaborateurs d'être plus data-driven (voir [Data 101 - partie 2](https://aelkouhen.github.io/data-101/2023-01-24-data-101-part-2/)). Loin de l'état d'esprit commun qui consiste à moderniser pour moderniser, il s'appuie sur quelques règles strictes :

*   _Pertinence_ : qui utilisera la technologie, et répondra-t-elle à leurs besoins ? La technologie doit servir les utilisateurs métier et non l'inverse. Assurez-vous également que chaque étape du parcours de données dispose de la bonne technologie et des bons processus pour maintenir l'intégrité des données et produire le maximum de valeur. Plutôt que d'identifier une approche universelle de premier rang, utilisez une sélection d'outils personnalisée en fonction des caractéristiques des données (voir [Data 101 - partie 1](https://aelkouhen.github.io/data-101/2023-01-22-data-101-part-1/)), de la taille de votre équipe et du niveau de maturité de votre organisation.
*   _Accessibilité_ : les architectes de données doivent considérer les outils et technologies qui permettent à tous les membres de l'organisation de prendre des décisions data-driven sans obstacles lors de l'accès aux données.
*   _Performance_ : les technologies puissantes disponibles sur le marché accélèrent le processus de transformation des données. Privilégiez les outils qui permettront aux utilisateurs métier d'être proactifs et non réactifs.

## Étapes du parcours de données

Le parcours de données comprend de nombreuses étapes. Les principales sont l'ingestion, le stockage, le traitement et le service. Chaque étape a son propre ensemble d'activités et de considérations. Le parcours de données comporte également une notion d'activités « transversales » : des activités critiques s'étendant à l'ensemble du cycle de vie. Celles-ci incluent la sécurité, la gestion des données, le DataOps, l'orchestration et l'ingénierie logicielle.

Comprendre chaque étape du cycle de vie des données vous aidera à faire de meilleurs choix concernant les outils et processus que vous appliquez à vos actifs de données, en fonction de ce que vous attendez de la plateforme de données. Je vous présenterai ensuite brièvement les différentes étapes qui forment le parcours de données. Des détails supplémentaires sur chaque étape seront développés dans les prochains articles de blog.

### 1 - Ingestion des données

L'ingestion des données est la première étape du cycle de vie des données. C'est là que les données sont collectées à partir de diverses sources internes comme les bases de données, les CRM, les ERP, les systèmes legacy, et de sources externes telles que les enquêtes et les fournisseurs tiers. Il est important de s'assurer que les données acquises sont exactes et à jour pour être utilisées efficacement dans les étapes suivantes du cycle.

Dans cette étape, les données brutes sont extraites d'une ou plusieurs sources de données, répliquées, puis ingérées dans un support de stockage d'atterrissage. Vous devez ensuite prendre en compte les caractéristiques des données que vous souhaitez acquérir pour vous assurer que l'étape d'ingestion des données dispose de la bonne technologie et des bons processus pour atteindre ses objectifs.

Dans le prochain article, je plongerai en profondeur dans l'ingestion des données, ses principales activités et considérations. Comme je l'ai expliqué dans [Data 101 - partie 1](https://aelkouhen.github.io/data-101/2023-01-22-data-101-part-1/), les données ont quelques caractéristiques innées. Les plus pertinentes pour cette étape sont : le Volume, la Variété et la Vélocité.

### 2 - Stockage des données

Le stockage désigne la façon dont les données sont conservées une fois qu'elles ont été acquises. Les données doivent être stockées de manière sécurisée sur une plateforme fiable avec des systèmes de sauvegarde appropriés pour la reprise après sinistre. Des mesures de contrôle d'accès doivent également être mises en place pour protéger les informations sensibles des utilisateurs non autorisés ou des acteurs malveillants qui pourraient tenter d'y accéder illégalement.

Le choix d'une solution de stockage est crucial pour le succès du cycle de vie des données, mais il peut aussi être un processus complexe en raison de plusieurs facteurs. Le stockage des données présente quelques caractéristiques, telles que le cycle de vie du stockage (comment les données vont évoluer), les options de stockage (comment les données peuvent être stockées efficacement), les couches de stockage, les formats de stockage (comment les données doivent être stockées en fonction de la fréquence d'accès aux données) et les technologies de stockage dans lesquelles les données sont conservées.

Bien que le stockage soit une étape distincte du parcours de données, il s'intersecte avec d'autres phases comme l'ingestion, la transformation et le service. Le stockage s'étend à l'ensemble du parcours de données, apparaissant souvent à plusieurs endroits dans un pipeline de données, avec des systèmes de stockage qui se recoupent avec les systèmes sources, l'ingestion, la transformation et le service. À bien des égards, la façon dont les données sont stockées influence leur utilisation à toutes les étapes du parcours de données.

### 3 - Traitement des données

Après avoir ingéré et stocké les données, vous devez en faire quelque chose. L'étape suivante du cycle de vie du parcours de données est la transformation, ce qui signifie que les données doivent être transformées de leur forme originale en quelque chose d'utile pour les cas d'usage en aval.

Le traitement implique de transformer les données brutes en insights précieux via une série de transformations de base. Celles-ci jouent un rôle vital dans le pipeline de traitement des données, en veillant à ce que les données soient représentées avec précision dans les types de données corrects. Cela implique la conversion des données de type chaîne, telles que les dates et les valeurs numériques, vers leurs types de données respectifs. Les transformations de base impliquent également la standardisation des enregistrements de données, l'élimination des entrées erronées et la garantie que les données respectent les normes de formatage requises.

Au fur et à mesure que le pipeline de traitement des données progresse, des transformations plus avancées peuvent être nécessaires, telles que la transformation ou la normalisation du schema des données. Plus en aval dans le pipeline, nous pouvons agréger des données à grande échelle à des fins de reporting ou transformer des données en vecteurs de caractéristiques pour une utilisation dans des processus de machine learning.

Les principaux défis ici sont l'exactitude et l'efficacité, car cette étape nécessite une puissance de calcul significative, qui pourrait devenir coûteuse au fil du temps sans stratégies d'optimisation appropriées.

### 4 - Service des données

Vous avez atteint la dernière étape du parcours de données. Maintenant que les données ont été ingérées, stockées et traitées en structures cohérentes et précieuses, il est temps d'en extraire de la valeur.

Le service des données est la partie la plus passionnante du parcours de données. C'est là que la magie opère. Ici, les ingénieurs BI, les ingénieurs ML et les data scientists peuvent appliquer les techniques les plus avancées pour extraire la valeur ajoutée des données. Par exemple, l'analytique est l'une des activités de données les plus connues. Elle consiste à interpréter et à tirer des insights des données traitées pour prendre des décisions éclairées ou faire des prédictions sur les tendances futures. De plus, des outils de visualisation des données peuvent être utilisés ici pour présenter les données de manière plus significative.

## Activités transversales du parcours de données

L'ingénierie des données a évolué au-delà des outils et de la technologie et comprend désormais une variété de pratiques et de méthodologies visant à optimiser l'ensemble du parcours de données, telles que la gestion des données, la sécurité, l'optimisation des coûts et des pratiques plus récentes comme le DataOps.

1. La sécurité est une considération critique dans tout projet de données. Les ingénieurs de données doivent prioriser la sécurité dans leur travail, car les échecs peuvent avoir de graves conséquences. Ils doivent avoir une compréhension approfondie de la sécurité des données et des accès, et adhérer au principe du moindre privilège.

   Le principe du moindre privilège est un principe de sécurité fondamental qui limite l'accès aux données à ceux qui sont nécessaires pour effectuer des fonctions spécifiques. Cette approche limite les dommages potentiels qui pourraient résulter d'une violation de sécurité. En exerçant le principe du moindre privilège, les ingénieurs de données peuvent aider à garantir que les données sensibles ne sont accessibles qu'au personnel autorisé et sont protégées contre l'accès non autorisé ou l'utilisation abusive.

2. Optimisation des coûts : considérez le coût global et le retour sur investissement (ROI) de votre plateforme de données. Ce coût peut rapidement devenir un obstacle pour toute future initiative de données si elle ne vaut pas la peine de dépenser trop pour trop peu de valeur en retour. Comme la sécurité, le prix est critique et doit être analysé et évalué avant de décider quels outils et technologies vous choisissez.

3. La gestion des données démontre que les organisations doivent considérer les données comme un actif précieux de la même façon qu'elles considèrent d'autres ressources telles que les actifs financiers, l'immobilier ou les produits finis. Des pratiques efficaces de gestion des données établissent un cadre cohérent que toutes les parties prenantes peuvent suivre pour s'assurer que l'organisation tire de la valeur de ses données et les gère de manière appropriée. Ce cadre comprend de multiples aspects, tels que la gouvernance des données, la découverte des données, la lignée des données, la responsabilité des données, la qualité des données, la gestion des données maîtres (MDM), la modélisation et la conception des données, et la confidentialité des données.

   Sans un cadre complet pour la gestion des données, les ingénieurs de données sont isolés, se concentrant uniquement sur les aspects techniques sans comprendre pleinement le contexte organisationnel plus large des données. Les ingénieurs de données ont besoin d'une perspective plus large de l'utilité des données dans toute l'organisation, depuis les systèmes sources jusqu'à la direction et partout entre les deux. En adoptant un cadre complet de gestion des données, les ingénieurs de données peuvent aider à garantir que l'organisation exploite efficacement ses données, permettant une meilleure prise de décision et améliorant l'efficacité opérationnelle globale.

4. Le DataOps est une méthodologie qui intègre les meilleures pratiques de la méthodologie Agile, du DevOps et du contrôle statistique des processus (SPC) pour gérer les données efficacement. Alors que le DevOps se concentre principalement sur l'amélioration de la qualité et de la mise en production des logiciels, le DataOps applique des principes similaires aux produits de données.

   En adoptant le DataOps, les organisations peuvent s'assurer que les produits de données sont livrés dans les délais, respectent les normes de qualité et sont disponibles pour les parties prenantes quand elles en ont besoin. Cette méthodologie met l'accent sur l'observabilité, la collaboration, l'automatisation et l'amélioration continue, garantissant que les processus de données sont rationalisés et efficaces. De plus, en appliquant les principes du contrôle statistique des processus, le DataOps aide à identifier et à atténuer les problèmes ou les erreurs dans le pipeline de données.

5. Orchestration : à mesure que la complexité des pipelines de données augmente, un système d'orchestration robuste devient essentiel. Dans ce contexte, l'orchestration désigne la coordination de nombreuses tâches (responsables des flux de données) pour s'exécuter aussi rapidement et efficacement que possible selon un calendrier planifié.

## Chaîne de valeur des données

Rappelons les rôles de données que nous avons introduits dans [Data 101 - partie 2](https://aelkouhen.github.io/data-101/2023-01-24-data-101-part-2/) de cette série. Mettons chaque rôle dans la perspective du parcours de données. Nous pouvons observer que chacun a des tâches prédéfinies, des compétences et des contrats d'interface avec les autres. La valeur des données augmente à travers le paysage du parcours de données grâce à cette synergie. Tout au long du processus, d'un bout à l'autre de la chaîne de valeur et en retour, il doit y avoir une rétroaction constante entre les producteurs et les parties prenantes.

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEjkZGn38BoudzHV0HRD_fABWFPVyrE8l-n2EfMQvQVC2m72A_fLF45bY4WsdYvJd4xeR0vl36HQjnz2hsjKUX8x2ETyqDuSPUsqtT93HYkqd6P8xyUoxZ1_K10mjOyh0Lg0mxBYTB6xRrak2jtty6rwsVNBN-th9Xrk48YYCOeoElqGA67ZPEbrC7c-){: .mx-auto.d-block :} *Rôles de données dans la chaîne de valeur des données*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"} 
  
L'ingénieur de plateforme (DataOps) construit l'infrastructure de la plateforme de données pour les autres professionnels de données impliqués.

*  L'ingénieur de données exploite l'infrastructure de la plateforme de données pour construire et déployer des pipelines qui extraient les données de sources externes, les nettoient, garantissent leur qualité et les transmettent pour une modélisation ultérieure. Si un traitement plus complexe est nécessaire, la responsabilité des ingénieurs de données se déplacerait en aval en conséquence.
*  L'analyste de données communique avec les parties prenantes métier pour créer un modèle de données précis et intuitivement utilisable pour les analyses ultérieures. Il utilise ensuite ces données modélisées pour mener des analyses exploratoires (EDA) et des analyses descriptives afin de répondre aux questions liées à l'activité à l'aide de tableaux de bord et de rapports.

Les ingénieurs MLOps construisent l'infrastructure d'une plateforme de machine learning pouvant être utilisée par les ingénieurs ML et les data scientists.

*  Les data scientists exploitent les ensembles de données de la plateforme de données pour explorer leurs insights prédictifs et construire des modèles de machine learning. Dans les organisations plus matures, vous trouverez également des feature stores.
*  Les ingénieurs ML exploitent les capacités de la plateforme ML pour déployer des modèles de machine learning construits par les data scientists en assurant les meilleures pratiques MLOps. Ils communiquent avec les ingénieurs MLOps pour s'aligner sur, aider à améliorer et industrialiser les capacités de la plateforme ML.

Où s'inscrivent tous ces rôles de données dans la data science ? Par exemple, il y a un débat, certains soutenant que l'ingénierie des données est une sous-discipline de la data science. Honnêtement, je pense que l'ingénierie des données est distincte de la data science et de l'analytique. Elles se complètent, mais sont distinctement différentes. L'ingénierie des données se situe en amont de la data science, ce qui signifie que les ingénieurs de données fournissent les entrées utilisées par les data scientists (en aval de l'ingénierie des données), qui convertissent ces entrées en quelque chose d'utile.

{: .box-warning}
**Attention :** Se trouver plus en amont de la chaîne de valeur des données ne signifie pas que votre valeur est moindre. Bien au contraire : toute erreur en amont multiplie l'impact des applications en aval, ce qui fait que les rôles en amont ont le plus grand impact sur la valeur finale.

Pour soutenir ce raisonnement, je considère la hiérarchie des besoins en data science (figure ci-dessous). En 2017, **_Monica Rogati_** a publié cette hiérarchie dans un [article](https://hackernoon.com/the-ai-hierarchy-of-needs-18f111fcc007) montrant où l'IA et le machine learning (ML) se situent près des tâches plus « banales » telles que la collecte de données, la transformation et l'infrastructure.

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEieHV4go-Nww19E2ng4QmwQeShHuWqu_F-d3zVRht74dFjm4-I_iPE7RftbXHClHJkg73r_3kCINxZvaTRNxIcHXcK_w1mJYMv9Q2LK6kWGEnd6fWzej-1HY6gZ-bskwX0OkzvhnCRYHCibPP8WkDCwlXGjxdNc7dHn89iiAxFfiB2ngCmJ7darjLHj){: .mx-auto.d-block :} *Hiérarchie des besoins en data science*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"} 

Bien que de nombreux data scientists puissent être enthousiastes à l'idée de développer et d'affiner des modèles de machine learning, la vérité est qu'environ 70 % à 80 % de leur temps est consacré aux trois niveaux inférieurs de la hiérarchie (collecte de données, nettoyage des données et traitement des données), avec seulement une infime fraction de leur temps allouée à l'analyse et au machine learning. Pour y remédier, **_Rogati_** soutient que les entreprises doivent établir une solide base de données aux niveaux inférieurs de la hiérarchie avant de se lancer dans des domaines tels que l'IA et le ML.

Les data scientists ont généralement besoin d'une formation pour créer des systèmes de données de qualité production et effectuent ce travail de manière désorganisée parce qu'ils manquent d'assistance et de ressources de la part d'un ingénieur de données. Idéalement, les data scientists devraient consacrer plus de 90 % de leur temps aux niveaux supérieurs de la hiérarchie, y compris l'analytique, l'expérimentation et le machine learning. Lorsque les ingénieurs de données se concentrent sur ces parties inférieures de la hiérarchie, ils établissent une base solide pour que les data scientists excellent.

## Résumé

Dans cet article, nous avons introduit le concept du parcours de données (chaîne de valeur des données) et comment on peut utiliser des outils technologiques modernes pour permettre aux organisations et aux personnes d'être plus data-driven. Ainsi, nous avons détaillé les différentes étapes de ce paysage et observé qu'une analyse architecturale approfondie est nécessaire pour choisir la bonne technologie pour le bon usage.

Enfin, nous avons mis les rôles de l'équipe de données dans la perspective du parcours de données. Nous avons observé que la valeur des données augmente grâce aux interactions entre chacune des équipes de données. Cependant, les activités en amont de la chaîne de valeur des données ne signifient pas moins de valeur. Au contraire, chaque étape du parcours de données a un impact immédiat sur les étapes en aval et, par conséquent, sur la valeur finale.

## Références

*   Reis, J. and Housley M. Fundamentals of data engineering: Plan and build robust data systems. O'Reilly Media (2022).
*   ["Data Lake Governance Best Practices"](https://dzone.com/articles/data-lake-governance-best-practices), Parth Patel, Greg Wood, and Adam Diaz (DZone).
