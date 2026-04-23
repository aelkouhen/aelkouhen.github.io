---
date: 2025-01-23
layout: post
lang: fr
title: "Du Mainframe au SQL Distribué, Partie 5"
subtitle: "Transition vers une Architecture Distribuée"
cover-img: /assets/img/cover-mainframe-p5.webp
thumbnail-img: /assets/img/cover-mainframe-p5.webp
share-img: /assets/img/cover-mainframe-p5.webp
tags: [mainframe, CockroachDB, migration, modernization, architecture, rehosting, replatforming, refactoring]
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

Alors que les entreprises exigent de plus en plus scalabilité, résilience et flexibilité, la transition des systèmes centralisés traditionnels vers des architectures distribuées est devenue un mouvement stratégique incontournable.

Les architectures distribuées offrent des avantages incomparables, notamment la capacité à gérer des charges de travail massives, à assurer une haute disponibilité et à soutenir des opérations mondiales transparentes. Cependant, effectuer cette transition requiert une planification réfléchie, des stratégies robustes et une compréhension approfondie de la façon d'adapter les systèmes existants à un modèle distribué.

Cet article explore :

1. Les aspects clés de la transition vers une architecture distribuée
2. Les stratégies de migration des bases de données mainframe
3. La manière de surmonter les défis courants et d'exploiter pleinement le potentiel des systèmes distribués

Que vous cherchiez à moderniser une infrastructure existante, à adopter le cloud ou à faire évoluer vos opérations pour répondre à une demande croissante, vous trouverez ici des éclairages pour vous guider dans votre parcours vers une architecture distribuée et prête pour l'avenir.

---

## Approches de migration des bases de données mainframe

La migration des bases de données mainframe vers des systèmes distribués modernes est une étape cruciale pour atteindre scalabilité, efficacité des coûts et agilité. Cependant, l'approche choisie impacte significativement la complexité, le calendrier et le succès final de la transition. Cette section compare les stratégies de migration courantes — **réhébergement, re-platforming**, **refactoring** et **réécriture** (aussi appelé **reconstruction**) — puis examine leurs implications pour l'adoption de bases de données distribuées.

### Migration par réhébergement

Qu'est-ce que le réhébergement ? L'approche de migration par réhébergement ou « lift-and-shift » consiste à déplacer une application existante et ses données associées du mainframe vers une infrastructure moderne (par exemple le cloud) avec des modifications minimales de son architecture ou de son code. Cette approche résout le problème de la maintenance coûteuse en déplaçant le système de son matériel existant vers des solutions d'hébergement modernes.

Si pour une raison quelconque vos données doivent être hébergées sur site, vous pouvez migrer des anciens mainframes vers du matériel plus moderne. Cela peut résoudre le problème des faibles performances ainsi que de la maintenance coûteuse sans modifier l'environnement de travail des employés.

Par exemple, cette approche se concentre souvent sur la réplication de l'environnement sur site au sein de l'infrastructure cloud, permettant aux organisations de migrer rapidement sans efforts de redéveloppement extensifs.

L'approche met l'accent sur la réplication de l'infrastructure, où les machines virtuelles, les serveurs et les configurations sont reproduits dans le cloud, permettant une transition transparente tout en préservant les fonctionnalités existantes de l'application.

<img src="/assets/img/mainframe-p5-rehosting.gif" alt="Diagramme de migration par réhébergement" style="width:100%">
{: .mx-auto.d-block :}
**Diagramme de migration par réhébergement**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Malgré ses avantages, le réhébergement présente également plusieurs inconvénients que les organisations doivent prendre en compte. Un inconvénient majeur est que les applications conçues pour des environnements sur site peuvent ne pas pleinement exploiter les fonctionnalités cloud-native, telles que l'auto-scaling, les capacités serverless ou les services gérés, conduisant à une utilisation sous-optimale du cloud. Cela peut entraîner des coûts d'exploitation plus élevés, car l'utilisation des ressources peut ne pas être optimisée pour l'environnement cloud.

De plus, les améliorations de performances sont souvent limitées puisque l'application n'est pas re-architecturée pour exploiter les capacités spécifiques au cloud. Des défis liés aux dépendances peuvent également survenir, notamment si l'application repose sur des systèmes existants difficiles à répliquer ou à intégrer dans le cloud. Ces limitations peuvent impacter l'efficacité et la rentabilité à long terme de l'approche de réhébergement.

### Migration par re-platforming

Qu'est-ce que le re-platforming ? L'approche de re-platforming consiste à déplacer la base de données mainframe vers un environnement moderne avec des modifications minimales de la structure de la base de données ou de la logique applicative, tout en effectuant des optimisations ciblées. L'objectif est de répliquer les fonctionnalités du mainframe dans une nouvelle infrastructure, souvent basée sur le cloud ou distribuée. Cela peut inclure le passage de modèles de bases de données hiérarchiques ou en réseau vers des systèmes relationnels ou NoSQL, l'ajustement du schéma, ou la modification des requêtes applicatives pour une meilleure compatibilité.

L'adoption de bases de données distribuées a des implications significatives pour les organisations qui transitionnent depuis des systèmes existants. Bien qu'une optimisation minimale lors du re-platforming puisse laisser certaines limitations de l'architecture existante intactes, des modifications stratégiques des schémas et des applications peuvent considérablement améliorer l'intégration avec les systèmes distribués. Ces optimisations permettent aux organisations d'exploiter les fonctionnalités clés des bases de données distribuées, telles que le partitionnement des données, la réplication et le basculement, améliorant la scalabilité, la fiabilité et la résilience globale du système dans les environnements modernes.

La migration vers des bases de données distribuées via l'approche de re-platforming offre plusieurs avantages, en faisant un choix attrayant pour les organisations.

1. Elle offre des gains de performance significatifs en améliorant l'efficacité avec des changements structurels minimaux, garantissant un processus de migration plus rapide en évitant des modifications extensives. Cette approche est également rentable, nécessitant un investissement initial plus faible par rapport aux méthodes plus complexes.
2. En réduisant la dépendance vis-à-vis d'un fournisseur unique, elle libère les organisations de leur dépendance aux technologies mainframe propriétaires.
3. De plus, la conservation de la logique métier existante minimise les perturbations opérationnelles, réduisant les risques associés à la migration.

Avec un coût et une complexité modérés, le re-platforming établit un équilibre entre les efforts de modernisation et une portée de migration gérable, en faisant une solution pratique pour de nombreuses entreprises.

Les modifications courantes effectuées lors du re-platforming d'applications incluent l'exposition des méthodes de service en tant que microservices ou macrosystèmes, l'identification et le traitement des bloqueurs de code incompatibles avec les environnements cloud en les remplaçant par des alternatives optimisées et compatibles avec le cloud, et la migration des bases de données sur site vers des bases de données distribuées si nécessaire.

<img src="/assets/img/mainframe-p5-replatforming.png" alt="Diagramme de migration par re-platforming" style="width:100%">
{: .mx-auto.d-block :}
**Diagramme de migration par re-platforming**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Ces ajustements permettent l'utilisation de fonctionnalités cloud essentielles, telles que l'auto-scaling dynamique, qui améliorent les performances et l'efficacité des ressources. Cette approche établit un équilibre en surmontant la nature chronophage de la réécriture et les limitations de fonctionnalités associées au réhébergement, permettant aux organisations d'exploiter pleinement le potentiel des environnements cloud de manière efficace.

Bien que le re-platforming vers une architecture distribuée offre de nombreux avantages, il présente ses propres défis. Une modernisation limitée peut laisser les inefficacités et la dette technique existantes intactes, entravant la pleine réalisation des améliorations potentielles. Il existe également un risque de temps d'arrêt lors de la migration, qui peut perturber les opérations si elle n'est pas gérée avec soin.

Des problèmes de compatibilité peuvent survenir, car certaines fonctionnalités ou configurations des bases de données existantes peuvent ne pas s'aligner parfaitement avec les environnements distribués. De plus, le processus nécessite une expertise technique, car la modification des requêtes et l'adaptation de l'architecture exigent du personnel qualifié pour assurer une transition réussie. Traiter ces défis est crucial pour maximiser le succès de ce type de migration.

### Migration par refactoring

Qu'est-ce que le refactoring ? Le refactoring désigne le processus d'amélioration de la structure interne ou de la conception d'un code existant sans modifier son comportement externe. L'accent est mis sur les changements au niveau du code, tels que l'amélioration de la lisibilité, la suppression des redondances ou l'optimisation des performances.

Dans le cadre de cet article, lorsque nous parlons de refactoring d'applications mainframe, nous entendons la refonte des applications pour exploiter pleinement les capacités d'un système distribué. Cette approche nécessite souvent un changement fondamental des modèles de bases de données existants vers des architectures de bases de données distribuées modernes comme [CockroachDB](https://www.cockroachlabs.com/product/overview/), et implique la décomposition d'une application monolithique et existante en une série de composants plus petits et indépendants, et la transition vers une architecture microservices. Elle peut également impliquer la migration de l'application vers une architecture serverless.

<img src="/assets/img/mainframe-p5-refactoring.png" alt="Diagramme de migration par refactoring" style="width:100%">
{: .mx-auto.d-block :}
**Diagramme de migration par refactoring**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

L'adoption de bases de données distribuées via cette approche libère leur plein potentiel, offrant des capacités puissantes telles que la scalabilité horizontale, la tolérance aux pannes et la géo-distribution. Ces fonctionnalités permettent aux organisations de construire des systèmes hautement résilients et évolutifs qui peuvent gérer de manière transparente les charges de travail croissantes et les opérations distribuées. De plus, les bases de données distribuées facilitent l'intégration avec les applications modernes et les technologies émergentes, notamment l'intelligence artificielle et l'apprentissage automatique, positionnant les organisations pour innover et prospérer dans un paysage technologique en rapide évolution.

Le refactoring est l'une des stratégies de migration les plus exigeantes en termes de temps et de coûts, mais il offre des avantages incomparables lorsqu'il s'agit d'exploiter pleinement les avantages du cloud computing distribué. Cette approche améliore considérablement les performances, la réactivité et la disponibilité, tout en réduisant la dette technique et en augmentant la flexibilité du système.

En adoptant le refactoring, les organisations peuvent pérenniser leurs applications, se positionnant pour adopter des technologies innovantes et s'étendre de manière transparente. La scalabilité améliorée des bases de données distribuées permet de gérer efficacement des charges de travail massives et des opérations géo-distribuées.

De plus, le refactoring facilite l'intégration de nouvelles fonctionnalités, ouvrant la voie à des améliorations continues et assurant une adaptabilité à long terme dans un paysage technologique en évolution.

Le refactoring présente des défis notables que les organisations doivent soigneusement considérer : sa haute complexité exige un temps, des ressources et une expertise significatifs, en faisant l'une des stratégies de migration les plus gourmandes en ressources.

De plus, il existe un risque plus élevé de perturbations opérationnelles lors de la transition, ce qui nécessite une planification et une exécution méticuleuses pour atténuer. L'investissement initial peut également être substantiel, tant financièrement qu'en termes de capital humain, rendant crucial pour les organisations d'évaluer leur maturité et leurs objectifs à long terme avant d'entreprendre cette approche.

### Migration par réécriture

Qu'est-ce que la réécriture ? En utilisant cette approche, une application existante est transformée en une version modernisée en réécrivant et/ou en re-architecturant ses composants depuis le début pour exploiter pleinement les capacités d'une plateforme moderne.

Ce processus implique de redévelopper entièrement l'application, lui permettant d'être déployée dans un environnement distribué et de tirer parti de toutes les fonctionnalités cloud-native. La réécriture implique de reconstruire l'application en utilisant la dernière pile technologique tout en refactorant son cadre pour améliorer les performances et la scalabilité.

Certaines applications et leurs dépendances sont liées à des frameworks incompatibles avec les environnements distribués. De plus, certaines applications existantes reposent sur des processus gourmands en ressources, entraînant des coûts accrus et des factures matérielles plus élevées en raison du grand volume de traitement des données. Dans de tels cas, le re-platforming ou le refactoring peuvent ne pas être des options viables pour la migration mainframe. Au lieu de cela, reconstruire l'application de zéro est souvent la meilleure approche pour optimiser l'utilisation des ressources et atteindre l'efficacité des coûts.

La réécriture d'une application mainframe offre plusieurs avantages clés, notamment dans le contexte de la migration mainframe.

Elle permet l'intégration de nouvelles fonctionnalités et améliore considérablement les performances de l'application en l'optimisant pour les environnements distribués modernes. Cette approche garantit que l'application exploite pleinement les avantages de l'écosystème d'une base de données distribuée comme CockroachDB, notamment la scalabilité, la fiabilité, la résilience et la géo-distribution.

En construisant une architecture orientée services de zéro, la réécriture permet une conception modulaire et efficace, améliorant la maintenabilité et l'adaptabilité. De plus, elle intègre les dernières technologies cloud, garantissant que l'application reste à la pointe et alignée avec les meilleures pratiques de l'industrie.

En fin de compte, la réécriture de votre système existant est une excellente opportunité de réviser le processus métier et son efficacité. Comme nous l'avons discuté dans un article précédent, « [L'Impératif du Changement](/2024-10-24-mainframe-to-distributed-sql-part-2/) », la réécriture du système existant implique d'abord une analyse détaillée du processus métier et la définition de tâches en dehors du système logiciel. De cette façon, vous pouvez détecter certaines incohérences et apporter les améliorations nécessaires.

Cependant, la réécriture présente certains inconvénients que les organisations doivent prendre en compte. C'est un processus chronophage et coûteux, nécessitant un investissement significatif en ressources et en expertise. La reconstruction d'un système existant exige également une compréhension approfondie des flux de travail existants, ce qui peut être particulièrement difficile si l'application a été développée il y a de nombreuses années en utilisant des frameworks obsolètes.

<img src="/assets/img/mainframe-p5-rewriting.png" alt="Diagramme de migration par réécriture" style="width:100%">
{: .mx-auto.d-block :}
**Diagramme de migration par réécriture**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

La complexité augmente lorsque l'application réécrite dépend d'autres systèmes existants, car ces interdépendances doivent être soigneusement analysées et traitées. De plus, les équipes impliquées dans la réécriture doivent souvent mettre à niveau leurs compétences pour travailler avec les dernières technologies, ajoutant à l'effort global et à la courbe d'apprentissage.

Comme le processus est très complexe, la réécriture comporte des risques accrus de perte de données, d'erreurs de codage, de dépassements de coûts et de retards importants du projet. Par exemple, un seul bogue dans le système réécrit peut avoir de graves conséquences, perturbant potentiellement des opérations métier critiques. L'échec de réécriture le plus connu est l'ancien système de paie pour Queensland Health en Australie par IBM : le projet, estimé initialement à 6 millions AUD, [a échoué lors de son déploiement](https://www.henricodolfing.com/2019/12/project-failure-case-study-queensland-health.html), entraînant un chaos absolu dans les paiements. Au final, le gouvernement du Queensland a dépensé 1,2 milliard AUD pour résoudre la situation !

De plus, la réécriture nécessite une connaissance approfondie du domaine du système existant, ce qui peut être difficile si les développeurs d'origine ne sont plus disponibles ou si la documentation est incomplète. Il existe également le risque que le nouveau système ne réplique pas entièrement les fonctionnalités de l'ancien en raison de lacunes dans les phases de planification ou de conception, obligeant potentiellement les entreprises à exploiter les deux systèmes en parallèle, ce qui est inefficace et coûteux.

Par ailleurs, l'investissement élevé en temps, en argent et en ressources fait de la réécriture une entreprise risquée, notamment pour les entreprises sans feuille de route claire pour l'implémentation et les tests. Selon le [Standish Group](https://www.standishgroup.com/sample_research_files/CHAOSReport2015-Final.pdf), plus de 70 % des réécritures d'applications existantes ne réussissent pas. Le rapport [Barometer](https://www.businesswire.com/news/home/20200528005186/en/74-Of-Organizations-Fail-to-Complete-Legacy-System-Modernization-Projects-New-Report-From-Advanced-Reveals) 2020 sur la modernisation des mainframes a révélé que 74 % des organisations ont lancé un projet de modernisation de systèmes existants, mais n'ont pas réussi à le mener à bien.

_« Réécrire une application métier est aussi ardu que l'ancien processus de réédition d'un manuscrit, sinon plus. » TMAXSOFT_

### Choisir la bonne approche

Voyons les choses d'un autre angle — la représentation visuelle ci-dessous illustre la dynamique des coûts et des économies associées aux différentes approches de migration de bases de données mainframe au fil du temps.

L'axe vertical représente l'impact financier : les valeurs négatives indiquent les dépenses budgétaires, tandis que les valeurs positives représentent les économies réalisées. L'axe horizontal mesure le temps en mois, montrant la nature à long terme des projets de migration, qui s'étendent généralement sur plusieurs années.

<img src="/assets/img/mainframe-p5-cost-savings.png" alt="Dynamique des coûts et des économies des approches de migration au fil du temps" style="width:100%">
{: .mx-auto.d-block :}
**Dynamique des coûts et des économies des approches de migration au fil du temps**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Le graphique illustre comment les différentes approches de migration impactent les dépenses budgétaires et les économies sur des durées spécifiques :

1. **Re-platforming (15 mois)** : L'option de migration la moins coûteuse à court terme après le réhébergement, elle implique des modifications minimales de l'architecture existante, en faisant un choix rentable pour les organisations. Le re-platforming permet une transition rapide des dépenses budgétaires initiales vers des économies de coûts significatives, affichant souvent une trajectoire ascendante prononcée dans les avantages financiers dans les 15 mois. Cette approche est particulièrement bien adaptée aux organisations avec des budgets limités, ou à celles qui donnent la priorité à un processus de migration rapide avec un minimum de perturbation des opérations en cours.

2. **Refactoring (8 mois après le re-platforming)** : L'approche de migration par refactoring implique des optimisations ciblées qui vont au-delà du re-platforming, nécessitant un investissement supplémentaire. Bien que les économies mettent plus de temps à se matérialiser, commençant généralement après la marque des 24 mois, ce retour sur investissement progressif en fait une option adaptée aux organisations visant à améliorer les performances du système sans entreprendre une refonte architecturale complète.

3. **Réécriture (20 mois après le re-platforming)** : La reconstruction représente une refonte architecturale complète qui implique des coûts initiaux significatifs mais offre des avantages substantiels à long terme. Les économies apparaissent généralement après 36 mois, reflétant les avantages d'un système entièrement modernisé. Cette approche est idéale pour les organisations cherchant à exploiter les capacités des bases de données distribuées et à atteindre une architecture hautement évolutive et pérenne.

4. **Remplacement (48 mois et plus)** : Le remplacement est l'approche de migration la plus coûteuse et la plus longue, impliquant le remplacement complet des systèmes existants. Bien que des économies significatives apparaissent généralement après 60 mois, cela met en évidence sa valeur à long terme pour les entreprises prêtes à adopter des systèmes entièrement nouveaux. Il convient mieux aux organisations dont les systèmes mainframe sont dépassés et incapables de répondre aux exigences modernes.

Chaque approche de migration offre des économies progressivement plus élevées à mesure que l'étendue de la modernisation augmente. À la marque des 60 mois, des stratégies comme la réécriture et le remplacement des systèmes existants offrent les rendements les plus élevés, bien qu'elles nécessitent un investissement initial significatif pour atteindre ces bénéfices à long terme.

L'adoption de bases de données distribuées lors de la modernisation des systèmes mainframe varie en complexité et en avantages selon les stratégies de migration :

- Le re-platforming sert de point d'entrée, permettant des gains rapides avec des changements minimaux mais limitant les avantages complets des architectures distribuées, tels que l'élasticité et la résilience.
- Le refactoring optimise les systèmes pour mieux utiliser les fonctionnalités distribuées comme le partitionnement et la scalabilité horizontale.
- La réécriture assure une compatibilité totale avec les bases de données distribuées, concevant des systèmes pour des performances élevées, la tolérance aux pannes et la distribution mondiale.

Comprendre les compromis entre le lift-and-shift, le re-platforming et la re-architecture est crucial pour une migration réussie des bases de données mainframe. Alors que le lift-and-shift offre une solution rapide, le re-platforming et la re-architecture offrent des avantages de modernisation plus profonds qui s'alignent mieux avec les capacités des bases de données distribuées. Les organisations doivent évaluer soigneusement leurs besoins uniques et leur maturité pour adopter des systèmes distribués, assurant une stratégie de migration qui offre à la fois des résultats immédiats et une valeur à long terme.

Le choix de la bonne stratégie de migration dépend de divers facteurs, notamment les objectifs de l'organisation, sa maturité technique et son budget :

- **Réhébergement** : Idéal pour les organisations cherchant une migration rapide et à faible risque pour réduire leur dépendance aux mainframes tout en reportant la modernisation complète
- **Re-platforming** : Adapté aux entreprises visant un équilibre entre modernisation et complexité, notamment lors de l'exploitation de bases de données distribuées pour des charges de travail spécifiques
- **Refactoring** : Meilleur pour les efforts de transformation à long terme, où la scalabilité, la résilience et l'intégration avec des technologies avancées sont des priorités
- **Réécriture** : Particulièrement bien adapté aux organisations nécessitant des améliorations significatives des performances, de la scalabilité et exploitant les capacités cloud-native tout en révisant les processus métier, en traitant les problèmes de sécurité et de conformité

Lorsque vous décidez comment moderniser votre système existant, il est crucial de comprendre les carrefours avec tous les chemins possibles, leurs cas d'usage spécifiques et leurs avantages respectifs. Devriez-vous réécrire votre système ? Devriez-vous envisager de refactoriser votre système ? Ou devriez-vous simplement changer la façon dont votre application est hébergée ou déployée ?

<img src="/assets/img/mainframe-p5-decision-tree.png" alt="Arbre de décision pour la transition de base de données" style="width:100%">
{: .mx-auto.d-block :}
**Arbre de décision pour la transition de base de données**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Cependant, connaître simplement les principes de modernisation logicielle n'est pas suffisant ; sans expérience préalable dans le domaine, prendre la bonne décision peut être exceptionnellement difficile. N'hésitez pas à contacter nos architectes de solutions chez [Cockroach Labs](http://www.cockroachlabs.com) pour vous aider à vous orienter dans la bonne direction. Nous pouvons réaliser des analyses approfondies de la base technique, des performances et des processus métier du projet pour vous aider à analyser l'état actuel du logiciel, produire un rapport détaillé, établir une liste des améliorations nécessaires et prioriser l'approche de modernisation. Chaque cas est unique et nécessite une stratégie individuelle.

---

## Outils et technologies

La transition vers une architecture distribuée implique des processus complexes qui nécessitent les bons outils, frameworks et méthodologies pour garantir le succès. L'exploitation de la pile technologique appropriée simplifie non seulement la migration mais minimise également les risques, optimise les performances et garantit que le nouveau système répond aux exigences modernes de scalabilité et de fiabilité. Voici un aperçu des outils et technologies clés qui jouent un rôle central dans la facilitation du processus de migration.

### Suites de modernisation mainframe

L'automatisation est au cœur des stratégies de migration modernes. Les outils conçus pour la migration analysent non seulement l'état actuel des systèmes existants, mais facilitent également la conversion des bases de code obsolètes, des structures de données et des processus en formats évolutifs et distribués. Ces outils éliminent le besoin d'une intervention manuelle extensive, garantissant précision et rapidité.

Par exemple, des outils comme la [suite de modernisation mainframe LIBER*M de mLogica](https://www.cockroachlabs.com/blog/cockroach-labs-and-mlogica-accelerate-mainframe-modernization/) sont une plateforme de bout en bout qui automatise les phases critiques du processus de migration. La suite comprend :

- **LIBER\*DAHLIA** : Cet outil effectue des évaluations détaillées des systèmes existants pour identifier les dépendances, les complexités et les composants nécessitant une migration.
- **LIBER\*TULIP** : Ce composant automatise la génération du DDL (data definition language) cible, permettant des migrations de bases de données fluides.
- **Bridge Program Generators** : Ces outils créent des interfaces temporaires entre les systèmes existants et les nouvelles plateformes, assurant des opérations ininterrompues pendant la migration.

<img src="/assets/img/mainframe-p5-mlogica.png" alt="Suite de modernisation mainframe mLogica LIBER*M" style="width:100%">
{: .mx-auto.d-block :}
**Suite de modernisation mainframe mLogica LIBER*M**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Les solutions de mLogica mettent l'accent sur un temps d'arrêt minimal, ce qui est crucial pour les systèmes critiques. En tirant parti de ces outils, les organisations peuvent transformer des mainframes sur site complexes en architectures cloud distribuées agiles.

D'autres outils comme BluAge — maintenant intégré dans le cadre du service de migration mainframe AWS — se concentrent sur l'automatisation de la réingénierie des systèmes existants. Leur suite technologique est conçue pour convertir le code et les données existants en langages et frameworks modernes. Les fonctionnalités incluent :

- **Analyse du code source** : BluAge identifie les dépendances, les redondances et les opportunités d'optimisation au sein de la base de code existante.
- **Conversion automatisée** : Le code existant est converti en langages modernes, tels que Java ou C#, assurant la compatibilité avec les architectures distribuées.
- **Modernisation des données** : Les outils transforment les données existantes en formats optimisés pour les bases de données distribuées, permettant des fonctionnalités comme la scalabilité horizontale et le partitionnement.

L'approche de BluAge a été mise en œuvre dans plus de 100 projets à grande échelle, démontrant sa fiabilité et son efficacité dans la réduction des risques et des délais de projet.

<img src="/assets/img/mainframe-p5-bluage.png" alt="Suite technologique BluAge" style="width:100%">
{: .mx-auto.d-block :}
**Suite technologique BluAge**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Les suites de modernisation mainframe sont équipées de fonctionnalités conçues pour rationaliser et améliorer le processus de transition. Elles fournissent des évaluations complètes pour analyser l'architecture, les dépendances et les flux de données des systèmes existants, permettant la création de plans de migration détaillés. Les outils automatisés de conversion de code et de données réécrivent les applications et les modèles de données en formats compatibles avec les systèmes distribués.

De nombreux outils incluent des solutions de pontage intérimaire qui permettent aux architectures existantes et modernes de coexister pendant la phase de migration. Des capacités supplémentaires comme les tests de scalabilité et l'intégration transparente avec les plateformes cloud améliorent encore la valeur de ces outils pour permettre des migrations fluides.

L'exploitation d'outils de migration avancés offre de nombreux avantages aux organisations. L'automatisation accélère le processus de migration, réduisant le délai de mise sur le marché et permettant aux entreprises de réaliser rapidement les avantages des systèmes modernisés. En minimisant l'intervention manuelle, ces outils réduisent considérablement le risque d'erreurs et de perturbations. L'efficacité des coûts est un autre avantage clé, car l'automatisation réduit le travail et le temps requis pour la migration. De plus, les systèmes réingéniés sont optimisés pour les environnements distribués, offrant des performances, une scalabilité et une résilience améliorées pour répondre aux demandes futures.

Bien que les outils de migration présentent de nombreux avantages, ils comportent également des défis que les organisations doivent traiter :

1. Les systèmes existants plus anciens avec une documentation limitée peuvent compliquer le processus de migration.
2. Assurer la maturité organisationnelle est également crucial, car l'adoption réussie des architectures distribuées nécessite des équipes qualifiées et une volonté d'embrasser le changement.
3. De plus, bien que ces outils conduisent finalement à des économies significatives, les coûts initiaux pour les outils, la formation et l'infrastructure peuvent être substantiels, nécessitant une planification minutieuse et une allocation des ressources.

### Outils de migration de données

D'autres outils cloud-native peuvent également être utilisés pour différentes tâches dans le parcours de modernisation. Par exemple, vous pouvez utiliser des outils de migration de données disponibles dans les différentes plateformes cloud pour transférer des données de manière transparente des systèmes existants vers des bases de données distribuées tout en assurant l'intégrité, la cohérence et un temps d'arrêt minimal. Des outils comme AWS Database Migration Service (DMS) facilitent les migrations de diverses bases de données vers des systèmes distribués basés sur le cloud avec une réplication en temps réel utilisant le [Change Data Capture](https://www.cockroachlabs.com/blog/change-data-capture/) (CDC).

Qu'est-ce que le Change Data Capture ? Le CDC est une technique utilisée pour identifier et suivre les changements dans une base de données en temps réel ou quasi-réel. Il capture les événements d'insertion, de mise à jour et de suppression au fur et à mesure qu'ils se produisent, enregistrant ces changements dans un système ou pipeline séparé. Cela permet à d'autres applications de traiter les données sans impacter la base de données source. Le CDC est essentiel pour des tâches comme la migration de bases de données car il permet une synchronisation des données en temps opportun entre les systèmes, soutient le mouvement incrémental des données et aide à maintenir la cohérence des données dans les environnements distribués.

<img src="/assets/img/mainframe-p5-cdc.png" alt="Diagramme du Change Data Capture" style="width:100%">
{: .mx-auto.d-block :}
**Diagramme du Change Data Capture**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

D'autres outils cloud-agnostiques comme Qlik Replicate ou Debezium offrent des capacités de migration de données en masse rapide et de change data capture (CDC), les rendant adaptés aux architectures distribuées. Ils diffusent les changements de bases de données vers des plateformes comme Kafka, permettant des mises à jour en temps réel. Les fonctionnalités clés de ces outils comprennent la synchronisation des données en temps réel, le support de divers types de bases de données et des options pour les migrations de données incrémentales et complètes, assurant une transition fluide vers les systèmes modernes.

### Outils de conversion de schéma et de compatibilité

Les outils de conversion de schéma et de compatibilité sont essentiels pour migrer des bases de données des systèmes existants vers des architectures distribuées modernes. Ces outils simplifient le processus d'adaptation des schémas de bases de données pour s'aligner sur les exigences des plateformes cibles. En automatisant l'analyse, la conversion et la validation des schémas, ils réduisent l'effort manuel, minimisent les erreurs et assurent une transition transparente.

Une fonctionnalité clé de ces outils est l'analyse et la conversion automatisées des schémas, qui évalue les schémas de bases de données existants, identifie les différences structurelles et les incompatibilités, et les convertit en formats adaptés au système cible. De plus, ils effectuent des vérifications de compatibilité pour valider le schéma converti par rapport aux exigences des environnements distribués. De nombreux outils fournissent également un support de restauration et de gestion des versions, permettant une gestion efficace des changements de schéma tout au long du processus de migration.

Plusieurs outils de conversion de schéma populaires sont largement utilisés dans l'industrie. L'AWS Schema Conversion Tool (AWS SCT) automatise la conversion de schéma pour migrer des bases de données vers des services cloud AWS comme Amazon RDS ou Aurora. Il identifie les incompatibilités potentielles et fournit des recommandations pour une intégration transparente.

<img src="/assets/img/mainframe-p5-schema-conversion.png" alt="Diagramme de conversion de schéma" style="width:100%">
{: .mx-auto.d-block :}
**Diagramme de conversion de schéma**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

[Liquibase](https://www.liquibase.com/), un outil open source, permet aux équipes de suivre, versionner et déployer des mises à jour de schéma tout en offrant des fonctionnalités de restauration pour corriger les erreurs lors de la migration. [Flyway](https://www.red-gate.com/products/flyway/community/), un framework léger, prend en charge les migrations de schéma sous contrôle de version et s'intègre bien avec les pipelines CI/CD, en faisant un excellent choix pour les workflows modernes. Le SCT MOLT (Migrate Off Legacy Technology) de Cockroach Labs se spécialise dans l'automatisation de la migration des schémas et des requêtes vers des architectures distribuées, validant les schémas convertis pour assurer une fonctionnalité optimale.

Les avantages de l'utilisation d'outils de conversion de schéma sont significatifs. Ils réduisent la complexité de l'adaptation des schémas, même pour les bases de données très complexes, tout en accélérant le processus de migration en automatisant les tâches répétitives. Cela économise du temps et permet aux équipes de se concentrer sur d'autres activités critiques. La validation automatisée améliore la précision, assurant que les schémas sont compatibles avec les systèmes distribués et optimisés pour les performances et la scalabilité.

### Outils d'orchestration et de déploiement

Les outils d'orchestration et de déploiement sont essentiels pour gérer la complexité des systèmes distribués. Ils garantissent que les applications sont efficacement déployées, surveillées et orchestrées dans divers environnements, du développement à la production.

Ces outils puissants rationalisent les opérations, permettant une infrastructure évolutive, tolérante aux pannes et cohérente pour les architectures distribuées. En automatisant les processus de déploiement, ils minimisent l'effort manuel, réduisent les erreurs et améliorent la fiabilité des systèmes distribués, notamment lors de la migration depuis des systèmes existants.

<img src="/assets/img/mainframe-p5-orchestration.png" alt="Outils d'orchestration et de déploiement" style="width:100%">
{: .mx-auto.d-block :}
**Outils d'orchestration et de déploiement**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Les outils d'orchestration et de déploiement comme Kubernetes, Terraform et Helm sont essentiels pour gérer la complexité des systèmes distribués. Ils permettent des déploiements évolutifs, tolérants aux pannes et cohérents dans des environnements divers, réduisant la charge opérationnelle et améliorant la fiabilité. À mesure que les architectures distribuées continuent de gagner en importance, l'exploitation de ces outils est devenue une nécessité pour les organisations visant à maintenir des infrastructures modernes et compétitives.

### Outils de surveillance et d'observabilité

Les outils de surveillance et d'observabilité sont essentiels pour maintenir la santé, les performances et le bon fonctionnement des systèmes distribués après la migration. Ces solutions offrent une visibilité approfondie sur le comportement du système, aidant les équipes à identifier et résoudre rapidement les problèmes. En collectant et en analysant les métriques, les journaux et les traces, ils permettent une gestion et une optimisation proactives des architectures distribuées.

<img src="/assets/img/mainframe-p5-monitoring.png" alt="Outils de surveillance et d'observabilité des bases de données" style="width:100%">
{: .mx-auto.d-block :}
**Outils de surveillance et d'observabilité des bases de données**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

En tirant parti d'outils comme [Prometheus](https://prometheus.io/), [Grafana](https://grafana.com/) et [Datadog](https://www.datadoghq.com/), les organisations peuvent gérer efficacement les complexités des architectures distribuées et s'assurer que leurs systèmes apportent une valeur cohérente. Ces outils sont conçus pour collecter et analyser des métriques, offrant des capacités de requête robustes qui facilitent la détection et le diagnostic des anomalies système. Ils fournissent également des tableaux de bord dynamiques qui permettent aux équipes de surveiller les performances du système et d'identifier visuellement les goulots d'étranglement.

### Méthodologies et frameworks

Le choix de la bonne méthodologie ou du bon framework pour migrer des bases de données existantes dépend d'une variété de facteurs, notamment :

- la complexité du système
- le volume de données
- les priorités organisationnelles telles que la tolérance aux temps d'arrêt et les objectifs de modernisation

En tirant parti d'outils et de frameworks avancés adaptés aux cas d'usage spécifiques, les organisations peuvent assurer une transition fluide vers des environnements de bases de données modernes tout en minimisant les risques et en maximisant l'efficacité. Voici quelques approches couramment utilisées, leurs avantages et leurs stratégies d'implémentation.

<img src="/assets/img/mainframe-p5-methodologies.png" alt="Méthodologies de migration de bases de données" style="width:100%">
{: .mx-auto.d-block :}
**Méthodologies de migration de bases de données**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

#### 1. Migration Big Bang

Cette méthode implique de migrer toutes les données de la source vers le système cible en un seul événement. C'est une approche encadrée dans le temps, adaptée aux ensembles de données plus petits ou aux systèmes moins complexes où les temps d'arrêt sont acceptables. L'avantage réside dans sa durée de projet plus courte et sa complexité de synchronisation réduite. Cependant, elle nécessite une planification et des tests minutieux pour minimiser les risques tels que les problèmes d'intégrité des données et les temps d'arrêt significatifs pendant le processus de migration.

L'approche lift-and-shift est une implémentation technique de l'approche de migration Big Bang. Elle implique de déplacer la base de données vers un nouvel environnement avec des modifications minimales de l'architecture ou du code applicatif existant. Cette stratégie est souvent utilisée pour des transitions rapides des systèmes sur site vers les environnements cloud. Bien qu'elle soit rentable et rapide, elle peut faire face à des défis de compatibilité, des différences de performances et à la nécessité de paramètres de sécurité mis à jour. Des outils comme MOLT Fetch et MOLT Verify de Cockroach Labs aident à rationaliser ce processus, assurant la cohérence des données et réduisant les temps d'arrêt.

**La sauvegarde et restauration** est également une approche Big Bang qui implique la création d'une sauvegarde de la base de données dans l'environnement source, son transfert vers le système cible et sa restauration là-bas. Elle est idéale pour les migrations homogènes (même SGBD), la reprise après sinistre ou les configurations d'environnements de test. Les méthodes de sauvegarde et restauration sont simples et offrent un meilleur contrôle sur le processus de migration. Cependant, elles peuvent impliquer des temps d'arrêt significatifs et une potentielle obsolescence des données, particulièrement dans les environnements à transactions élevées. La compatibilité entre les versions de bases de données est une autre considération critique pour cette méthode.

Enfin, les techniques **d'import et export** sont couramment utilisées pour les migrations inter-plateformes où les données doivent se déplacer entre différents SGBDs ou environnements avec des formats différents. Cette approche permet un contrôle granulaire, permettant des migrations partielles de données ou des transformations de données pendant le processus. Elle prend en charge une large gamme de formats tels que CSV, JSON ou les fichiers de dump SQL, la rendant très flexible. Cependant, l'import et l'export peuvent être chronophages pour les grands ensembles de données et nécessitent une gestion soigneuse des dépendances relationnelles et des risques potentiels de perte de données.

<img src="/assets/img/mainframe-p5-import-export.png" alt="Migration de base de données par import et export" style="width:100%">
{: .mx-auto.d-block :}
**Migration de base de données par import et export**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

#### 2. Migration en ligne (ou migration parallèle)

La migration en ligne est une approche par phases de la migration de données qui implique d'exécuter les systèmes source et cible en parallèle tout en transférant progressivement les données au fil du temps. Cette méthode commence souvent par un chargement initial de données, suivi de mises à jour continues jusqu'à ce que le nouveau système remplace entièrement l'ancien.

La migration en ligne offre plusieurs avantages, notamment la capacité de tester et valider entièrement le nouveau système avant une bascule complète, équilibrant une migration rapide avec la flexibilité de gérer les mises à jour incrémentales. Elle minimise les risques en maintenant l'ancien système jusqu'à ce que le nouveau soit stable et opérationnel.

Cependant, cette approche peut être intensive en ressources et coûteuse, car l'exécution de systèmes parallèles nécessite une synchronisation soigneuse pour assurer la cohérence des données. La migration en ligne est particulièrement adaptée aux scénarios impliquant de grands ensembles de données ou des applications critiques où les temps d'arrêt doivent être minimaux ou évités complètement.

La stratégie de migration **Blue-Green** est une approche de migration en ligne qui minimise les temps d'arrêt et les risques en maintenant deux environnements identiques — l'un actif (bleu) et l'autre inactif (vert). Les données sont migrées et testées dans l'environnement inactif avant de basculer le trafic vers celui-ci. Cette approche assure un service ininterrompu et fournit un mécanisme de restauration facile en cas de problèmes. Le coût du maintien d'environnements dupliqués et l'effort impliqué dans la synchronisation sont des défis importants avec cette méthode.

Il y a également la migration **Red-Black** qui est une dérivation de la stratégie de migration Blue-Green. Dans cette approche, deux environnements sont maintenus : l'environnement « Red » (actif) et l'environnement « Black » (en attente). La base de données cible est déployée dans l'environnement Black tandis que l'environnement Red reste actif. Une fois que l'environnement Black est testé et vérifié, le trafic est basculé de l'environnement Red vers l'environnement Black. La seule différence entre cette stratégie et le Blue-Green est que vous n'avez pas besoin de maintenir les deux bases de données servant les utilisateurs en même temps.

<img src="/assets/img/mainframe-p5-red-black.gif" alt="Stratégie de migration de base de données Red-Black" style="width:100%">
{: .mx-auto.d-block :}
**Stratégie de migration de base de données Red-Black**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

En fin de compte, le CDC est une méthode de migration en ligne qui capture les changements dans la base de données source et les synchronise avec le système cible. Des outils comme [Debezium](https://debezium.io/), [Oracle GoldenGate](https://www.oracle.com/integration/goldengate/) et [Striim](https://www.striim.com/) facilitent ce processus, assurant la cohérence des données entre les environnements.

#### 3. Migration incrémentale

L'approche Strangler Fig, également connue sous le nom de déploiement par phases, migre une portion de vos utilisateurs, charges de travail ou tables au fil du temps. Jusqu'à ce que tous les utilisateurs, charges de travail et/ou tables soient migrés, l'application continuera d'écrire dans les deux bases de données.

Cette approche s'inspire de la façon dont un [figuier étrangleur](https://www.britannica.com/plant/strangler-fig-tree) prend progressivement le dessus sur un arbre, le remplaçant au fil du temps. Dans ce contexte, elle fait référence à la migration incrémentale des composants de base de données, permettant à l'ancien système de base de données de continuer à fonctionner aux côtés du nouveau jusqu'à ce que la transition soit complète. Cette approche minimise les perturbations en déplaçant progressivement les données et les fonctionnalités vers le nouveau système, plutôt que d'effectuer une migration complète d'un coup.

L'approche Strangler Fig est particulièrement bien adaptée aux bases de données grandes ou complexes où migrer tout en même temps poserait des risques significatifs ou causerait des perturbations majeures. En décomposant la migration en parties plus petites et gérables, cette méthode facilite la gestion des systèmes complexes de manière incrémentale.

<img src="/assets/img/mainframe-p5-strangler-fig.png" alt="Méthode de migration de données Strangler Fig" style="width:100%">
{: .mx-auto.d-block :}
**Méthode de migration de données Strangler Fig**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Elle est également très efficace pour la modernisation des systèmes existants, permettant aux organisations de passer progressivement des systèmes dépassés vers des plateformes modernes sans nécessiter de temps d'arrêt. Cette approche est idéale pour les systèmes critiques, où le maintien d'une opération continue est essentiel, car elle permet à la migration de se dérouler par étapes tout en maintenant le système existant entièrement fonctionnel, minimisant ainsi l'impact sur l'activité.

L'approche Strangler Fig offre plusieurs avantages clés, en faisant une option attrayante pour la migration de bases de données. L'un des plus grands avantages est le temps d'arrêt minimal, car l'ancien système continue de fonctionner tout au long du processus de migration, réduisant les perturbations typiquement associées au passage à une nouvelle base de données.

Elle atténue également les risques en permettant des migrations incrémentales, ce qui signifie que les problèmes potentiels peuvent être identifiés et traités dans des sections plus petites et gérables avant d'impacter l'ensemble du système. Cette méthode offre également de la flexibilité, donnant aux organisations la capacité d'étaler les efforts de migration dans le temps, ce qui réduit la pression et permet une planification soigneuse.

---

## Un voyage transformateur

Moderniser d'une architecture mainframe vers une architecture distribuée est un voyage parsemé de défis — mais regorgeant d'opportunités de transformation !

En suivant les meilleures pratiques — telles que la planification stratégique, la migration par phases, une surveillance robuste et la montée en compétences des équipes — et en tirant les leçons des expériences de l'industrie, les organisations peuvent assurer une transition transparente. En fin de compte, la sélection des outils et techniques appropriés en fonction des besoins spécifiques de votre organisation est déterminante pour le succès de l'effort de modernisation.

---

## Références

1. [Why Rewriting Legacy Applications Can Be a Costly Mistake and How to Avoid It](https://www.tmaxsoft.com/en/press/view?seq=250&pageIndex=1&pageUnit=12&searchKeyword=Why+Rewriting+Legacy+Applications+&searchUseYn=Y), TMaxSoft.
2. [Should You Rehost, Rebuild, or Rewrite a Legacy Application With Latest Software?](https://modlogix.com/blog/software-system-upgrading-to-rehost-rewrite-or-rebuild/), ModLogix.
