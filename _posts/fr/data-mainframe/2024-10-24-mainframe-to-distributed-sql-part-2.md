---
layout: post
lang: fr
title: "Du Mainframe au SQL Distribué, Partie 2"
subtitle: "L'Impératif du Changement"
cover-img: /assets/img/cover-mainframe-p2-final.webp
thumbnail-img: /assets/img/cover-mainframe-p2-final.webp
share-img: /assets/img/cover-mainframe-p2-final.webp
tags: [mainframe, CockroachDB, migration, modernization, cloud]
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

Dans le paysage numérique en rapide évolution d'aujourd'hui, les architectures de bases de données mainframe traditionnelles présentent des défis et des considérations spécifiques pour les organisations qui s'appuient sur ces systèmes conventionnels. Les bases de données mainframe, bien que robustes et capables de gérer des volumes substantiels de données et des débits élevés de transactions, se heurtent à des limitations en matière de scalabilité, d'intégration avec les systèmes modernes et d'efficacité des coûts.

L'évolution rapide des exigences métier et des tendances technologiques impose un virage vers des solutions de bases de données plus agiles et innovantes. Dans cet article, nous examinerons l'urgence de la modernisation des mainframes en explorant :

- les forces motrices derrière cette transformation
- les risques de l'inaction
- les considérations financières associées au maintien des architectures mainframe traditionnelles.

À travers une analyse approfondie, nous mettrons en évidence le besoin critique pour les organisations de s'adapter à des solutions de bases de données distribuées comme CockroachDB pour rester compétitives et réactives dans le paysage numérique moderne.

---

## Le besoin de changement

Tous les défis présentés précédemment confirment une vérité évidente : le besoin de changement, autrement dit, le besoin de migration mainframe.

Toutes les migrations informatiques, y compris celles des mainframes, reposent sur trois objectifs : **gagner de l'argent, économiser de l'argent** ou **atténuer les risques**. Par exemple, la décision d'une organisation d'entreprendre une migration mainframe peut répondre à l'ensemble de ces critères :

### Gagner de l'argent

Historiquement, de nombreux dirigeants d'entreprise ont résisté à investir dans la modernisation. Après tout, ces systèmes existants étaient rigides et comportaient des risques pour la modification de fonctions critiques. Cependant, la pandémie de COVID-19 a créé une urgence à changer le statu quo — une directive venue des dirigeants et responsables informatiques supérieurs. La pandémie a démontré les capacités exceptionnelles de l'homme en matière d'innovation et de créativité : des changements significatifs dans les approches des chaînes d'approvisionnement mondiales se sont produits en peu de temps. Il y a également eu une accélération de la transformation numérique.

Les environnements mainframe sont souvent perçus comme moins agiles et innovants que les architectures informatiques modernes. Les organisations cherchant à accélérer leur rythme d'innovation et à adopter les technologies émergentes peuvent choisir de migrer des mainframes vers des plateformes offrant plus de flexibilité et de scalabilité. Les systèmes mainframe peuvent rencontrer des limitations pour faire évoluer leur capacité afin de répondre aux demandes croissantes des entreprises numériques modernes. La migration vers des systèmes cloud ou distribués peut offrir aux organisations la scalabilité nécessaire pour prendre en charge des charges de travail dynamiques et accompagner la croissance financière future.

### Économiser de l'argent

Les coûts matériels, logiciels et de maintenance des mainframes peuvent être substantiels. Les organisations peuvent réduire leurs dépenses informatiques en migrant des environnements mainframe coûteux vers des alternatives plus rentables, telles que les solutions basées sur le cloud ou sur du matériel standard.

Les économistes estiment que le coût organisationnel le plus significatif est sans aucun doute le coût d'opportunité. Qu'est-ce que le coût d'opportunité ? Le « coût d'opportunité » désigne les avantages potentiels qu'une organisation renonce à obtenir en choisissant une alternative plutôt que la meilleure option disponible.

En termes simples, le coût d'opportunité est ce à quoi vous renoncez pour ne pas choisir la meilleure option. Par exemple, si vous décidez d'investir votre argent en actions, le coût d'opportunité pourrait être le rendement potentiel que vous auriez obtenu en investissant en obligations. De même, si vous dépensez votre budget informatique pour créer une nouvelle application mainframe, le coût d'opportunité pourrait être la valeur des applications cloud-native que vous auriez pu déployer à la place si vous aviez réalisé une migration mainframe.

### Atténuer les risques

Les systèmes mainframe peuvent présenter des risques liés aux défaillances matérielles, aux vulnérabilités de sécurité et à la dépendance vis-à-vis d'un fournisseur unique. La migration vers des plateformes alternatives réduit la dette technique et permet une meilleure intégration avec d'autres systèmes et services. Elle peut également aider les organisations à atténuer ces risques en diversifiant leur infrastructure informatique et en réduisant leur dépendance aux solutions d'un seul fournisseur.

Par ailleurs, le principal risque à atténuer dans le cadre des technologies mainframe est la pénurie de professionnels qualifiés. Les organisations peuvent avoir du mal à recruter et à retenir du personnel mainframe compétent, entraînant des difficultés à maintenir et à soutenir les systèmes mainframe. La migration vers des plateformes avec des viviers de talents plus larges et des compétences modernes peut résoudre ce problème.

En plus de ces trois critères, de nombreux autres facteurs peuvent pousser les organisations à migrer leur mainframe existant vers de nouvelles technologies.

---

## Risques de l'inaction : le dilemme de l'innovateur

Dans leur article fondateur [« Disruptive Technologies: Catching the Wave »](https://hbr.org/1995/01/disruptive-technologies-catching-the-wave), Joseph L. Bower et Clayton M. Christensen ont exposé les raisons fondamentales pour lesquelles une technologie peut bouleverser un secteur. L'une de leurs observations centrales était que même les entreprises solides pouvaient être vulnérables à la disruption.

Les auteurs ont nommé ce phénomène [« le dilemme de l'innovateur »](https://www.hbs.edu/faculty/Pages/item.aspx?num=46). Dans ce scénario, une entreprise établie (appelée titulaire) investit typiquement dans des innovations durables pour ses produits existants afin de maintenir la croissance de ses revenus et de ses bénéfices. En revanche, une startup, non contrainte par des produits existants, a la liberté de prendre des risques significatifs et de poursuivre des innovations révolutionnaires. Si ces innovations trouvent un écho auprès des clients, les impacts peuvent être dévastateurs pour les titulaires.

<img src="/assets/img/mainframe-p2-innovators-dilemma.png" alt="La courbe du dilemme de l'innovateur" style="width:100%">
{: .mx-auto.d-block :}
**La courbe du dilemme de l'innovateur**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Aujourd'hui, le dilemme de l'innovateur est une préoccupation tangible pour de nombreuses grandes entreprises, dont beaucoup s'appuient sur des systèmes mainframe. La conviction prévaut que l'échec à adopter des technologies plus innovantes pourrait conduire à la victoire éventuelle de concurrents émergents. Cette crainte de la disruption est un moteur important du changement dans l'industrie mainframe et souligne la demande persistante de modernisation des systèmes existants par la migration mainframe.

Pour mieux comprendre cette crainte, Jamie Dimon, PDG de JPMorgan Chase, a souligné dans la [lettre aux actionnaires de 2020](https://reports.jpmorganchase.com/investor-relations/2020/ar-ceo-letters.htm) que les technologies disruptives représentent l'une des plus grandes menaces pour son entreprise. Dimon a noté : « Les banques ont d'autres faiblesses, nées en partie de leur succès — par exemple, des 'systèmes existants' peu flexibles qui doivent être migrés vers le cloud pour rester compétitifs. »

Il a ensuite mis en évidence la menace posée par les nouvelles startups fintech qui révolutionnent les services financiers, principalement à travers l'utilisation d'applications mobiles : « Des prêts aux systèmes de paiement en passant par l'investissement, elles ont fait un excellent travail en développant des produits faciles à utiliser, intuitifs, rapides et intelligents. Nous en parlons depuis des années, mais cette concurrence est désormais partout. La capacité des fintech à fusionner les réseaux sociaux, à utiliser les données intelligemment et à s'intégrer rapidement avec d'autres plateformes (souvent sans les inconvénients d'être une vraie banque) aidera ces entreprises à conquérir des parts de marché significatives. »

Son exemple inspirera de nombreux autres dirigeants à prendre des mesures proactives. Il amplifiera l'urgence de moderniser les systèmes existants, entraînant une demande croissante de technologies disruptives et de développeurs compétents dans ces domaines.

---

## L'évolution des exigences métier : le virage vers les architectures de bases de données distribuées

L'histoire des langages de programmation, des paradigmes et des architectures logicielles a été caractérisée ces dernières décennies par un virage progressif vers la distribution. La distribution, la modularisation et le couplage faible ont émergé comme des tendances transformatrices dans le développement logiciel moderne, y compris dans les efforts de modernisation des mainframes. L'idée des microservices et du DevOps découle de ce besoin largement reconnu.

Les architectures monolithiques, caractérisées par des applications volumineuses et fortement couplées, ont traditionnellement dominé le paysage mainframe. Dans une architecture monolithique, l'ensemble d'une application est construite comme une unité unique et interconnectée, avec tous les composants étroitement couplés. Cette architecture peut entraîner des difficultés de scalabilité, de maintenabilité et de flexibilité de déploiement. De plus, toute modification ou mise à jour de l'application nécessite un redéploiement complet du monolithe, ce qui peut être long et risqué.

En revanche, l'architecture microservices décompose les applications en services plus petits et faiblement couplés, chacun responsable d'une fonction métier spécifique. Ces services communiquent entre eux via des API bien définies, permettant aux équipes de les développer, déployer et faire évoluer indépendamment. Cette architecture permet le passage à l'échelle horizontal de services individuels, permettant aux organisations de gérer des charges de travail accrues plus efficacement. Elle permet une meilleure utilisation des ressources et des performances améliorées, notamment dans des environnements dynamiques ou imprévisibles.

Le besoin de distribution a été poussé plus loin pour couvrir chaque aspect de l'application, y compris le stockage des données. Alors que les organisations cherchent à tirer parti de la flexibilité, de la scalabilité et de l'agilité offertes par les architectures microservices, l'adoption d'une architecture distribuée moderne implique la transition des bases de données centralisées existantes vers des systèmes distribués couvrant plusieurs serveurs, centres de données ou environnements cloud.

À l'instar de la couche applicative, la principale motivation pour adopter des architectures de bases de données distribuées est le besoin de scalabilité. Les bases de données mainframe traditionnelles peuvent avoir du mal à gérer les volumes croissants de données et les charges transactionnelles auxquels les organisations font face dans le paysage numérique actuel. La distribution des données sur plusieurs nœuds permet aux bases de données distribuées de passer à l'échelle horizontalement, en accommodant une demande accrue sans sacrifier les performances ou la fiabilité.

De plus, les architectures de bases de données distribuées offrent plus de flexibilité et de résilience que les bases de données mainframe centralisées. Les organisations peuvent atteindre la tolérance aux pannes et la haute disponibilité avec des données distribuées sur plusieurs nœuds en répliquant les données et en mettant en œuvre des architectures redondantes. Cela garantit que les applications restent accessibles et réactives même en cas de défaillances matérielles ou de pannes réseau.

Les bases de données distribuées sont également méticuleusement conçues pour aider les organisations à respecter des normes réglementaires strictes tout en garantissant une durabilité et une disponibilité inégalées. Par exemple, CockroachDB, une base de données SQL distribuée moderne, donne aux utilisateurs le contrôle sur la résidence et l'isolation des données. Au sein du même cluster, vous pouvez spécifier l'emplacement de stockage de vos données à différents niveaux de granularité : au niveau du nœud, au niveau de la base de données, au niveau de la table, voire au niveau de la ligne !

En effet, l'une des capacités uniques de cette base de données est sa capacité à lier les données à un emplacement. Premièrement, cela permet de localiser les données pour les utilisateurs dans un emplacement ou une région spécifique, conduisant à des latences plus faibles et donc à une meilleure expérience utilisateur.

De plus, des architectures de bases de données distribuées comme CockroachDB permettent aux organisations de tirer parti du cloud computing et des environnements cloud hybrides. En distribuant les données dans des centres de données sur site et des plateformes cloud, les organisations peuvent exploiter la scalabilité et la rentabilité de l'infrastructure cloud tout en conservant le contrôle sur les données sensibles et les exigences de conformité (RGPD européen, loi chinoise sur la cybersécurité, loi russe sur les données, etc.).

---

## L'évolution des exigences métier : le virage vers le cloud computing

Le virage vers le cloud computing est devenu une stratégie centrale pour la modernisation des mainframes, alors que les organisations cherchent à tirer parti de la scalabilité, de la résilience et de la rentabilité des technologies cloud-native. Adopter une approche cloud-native implique de repenser et de refactoriser les applications et charges de travail mainframe pour s'exécuter nativement sur des plateformes cloud, telles qu'Amazon Web Services (AWS), Microsoft Azure ou Google Cloud Platform (GCP).

Le principal avantage de la migration vers le cloud est le passage des dépenses d'investissement (CapEx) aux dépenses d'exploitation (OpEx). Qu'est-ce que le CapEx vs OpEx ? Dans ce cas, au lieu d'investir à l'avance dans du matériel, des logiciels et des infrastructures (CapEx), les organisations paient pour les services cloud sur la base d'un abonnement ou selon une tarification à l'usage (OpEx). Cela permet une gestion des coûts plus prévisible et flexible, les dépenses étant alignées sur l'utilisation et pouvant être ajustées en fonction des besoins métier.

Les avantages du cloud computing offrent plusieurs bénéfices par rapport aux environnements mainframe traditionnels. Premièrement, le cloud computing permet aux organisations de faire évoluer les ressources de manière dynamique en fonction de la demande, permettant une utilisation plus efficace des ressources et des économies de coûts. Les applications cloud-native sont intrinsèquement résilientes et tolérantes aux pannes, avec une redondance intégrée et des mécanismes de basculement pour assurer une haute disponibilité.

Par ailleurs, les technologies cloud-native facilitent des cycles de développement et de déploiement rapides, permettant aux organisations d'innover et d'itérer plus rapidement. En tirant parti de la conteneurisation et de l'architecture microservices, les applications mainframe peuvent être décomposées en composants plus petits et plus gérables, les rendant plus faciles à développer, déployer et maintenir.

La migration vers le cloud offre également des opportunités de moderniser les applications mainframe existantes en incorporant des pratiques de développement modernes, telles que le DevOps et l'intégration/déploiement continu (CI/CD). Ces pratiques permettent des tests, des déploiements et une surveillance automatisés des applications, résultant en un délai de mise sur le marché plus rapide et une meilleure qualité logicielle.

Pour le stockage de données, de nombreuses bases de données « cloud » sont disponibles, mais très peu d'entre elles offrent réellement l'agilité et l'échelle requises par ces applications modernes. Certaines initiatives de migration tentent d'utiliser une base de données relationnelle existante dans le cloud telle quelle, mais elles ne peuvent évoluer qu'à hauteur de l'instance matérielle sur laquelle elles s'exécutent. Elles ont été conçues uniquement pour un passage à l'échelle vertical.

<img src="/assets/img/mainframe-p2-cloud-native-scale.png" alt="SQL Distribué Cloud-Native vs bases de données existantes" style="width:100%">
{: .mx-auto.d-block :}
**SQL Distribué Cloud-Native vs bases de données existantes**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

D'autres initiatives tentent d'utiliser des bases de données NoSQL mais peinent avec les transactions ACID à grande échelle. Elles ont essayé d'imposer le NoSQL partout, même lorsque la charge de travail ne correspondait pas à cette technologie. La plupart des charges de travail mainframe sont conçues pour effectuer du traitement transactionnel en ligne (OLTP), donc migrer des bases de données mainframe traditionnelles vers le NoSQL n'est ni pertinent ni approprié.

Certaines bases de données existantes « augmentées » pour le cloud ont également été créées, où seule une couche de la base de données a été repensée pour être distribuée. Celles-ci peinent elles aussi avec la cohérence et la scalabilité.

Aucune de ces initiatives n'a été architecturée pour le cloud. C'est pourquoi, en 2015, trois anciens ingénieurs de Google, Spencer Kimball, Peter Mattis et Ben Darnell, ont cofondé Cockroach Labs. La base de données créée par leur nouvelle société, CockroachDB, est née de la frustration face aux bases de données open source disponibles et aux offres DBaaS cloud, et au manque de capacités répondant aux exigences des applications d'aujourd'hui. En plus des capacités de niveau entreprise, CockroachDB a émergé pour combiner l'élasticité du cloud, la cohérence des bases de données relationnelles et la scalabilité et la résilience des bases de données NoSQL.

<img src="/assets/img/mainframe-p2-cockroachdb-venn.png" alt="CockroachDB : Relationnel, NoSQL, Cloud Native et prêt pour l'entreprise" style="width:100%">
{: .mx-auto.d-block :}
**CockroachDB : Relationnel, NoSQL, Cloud Native et prêt pour l'entreprise**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

---

## Implications financières

### Coûts initiaux et récurrents élevés

Le maintien d'une infrastructure mainframe existante engendre des charges financières considérables. Les coûts initiaux élevés du matériel mainframe, les licences logicielles onéreuses et la maintenance continue peuvent peser sur les budgets informatiques. Ces dépenses sont souvent aggravées par le besoin de professionnels mainframe spécialisés, dont la rareté fait monter les salaires et les coûts de recrutement. De plus, à mesure que ces professionnels partent en retraite, les organisations font face au défi coûteux de les remplacer, nécessitant souvent des investissements substantiels dans la formation et le développement des nouvelles recrues.

En revanche, la modernisation vers des solutions de bases de données distribuées comme CockroachDB offre des avantages de coûts substantiels. Les bases de données distribuées tirent parti de matériels plus abordables et évolutifs, réduisant le besoin de grands investissements initiaux. De plus, CockroachDB et des solutions similaires sont conçues pour évoluer horizontalement, permettant aux organisations d'ajouter des ressources de manière incrémentielle et d'aligner les coûts plus étroitement avec la demande réelle. Cette flexibilité peut conduire à des économies significatives, notamment pendant les périodes de charges de travail fluctuantes.

### Réduction des coûts globaux

Les coûts opérationnels associés aux mainframes existants peuvent être substantiels en raison de leur complexité et du besoin de maintenance spécialisée continue. Les bases de données distribuées modernes simplifient les opérations grâce à des outils de gestion plus intuitifs et des fonctionnalités automatisées, réduisant le besoin d'interventions manuelles importantes. Cette simplicité réduit les dépenses opérationnelles et permet aux équipes informatiques de se concentrer sur des initiatives plus stratégiques plutôt que sur des tâches de maintenance de routine.

Bien que les coûts financiers soient critiques, le coût d'opportunité du maintien des systèmes existants peut être encore plus significatif. Les mainframes existants limitent souvent la capacité d'une organisation à innover et à s'adapter rapidement aux évolutions du marché. Ce manque d'agilité peut se traduire par des opportunités commerciales manquées et une réponse plus lente aux pressions concurrentielles. En revanche, les bases de données distribuées modernes comme CockroachDB soutiennent des cycles de développement rapides et une intégration transparente avec les applications cloud-native, permettant aux organisations d'innover plus librement et de maintenir un avantage concurrentiel.

<img src="/assets/img/mainframe-p2-real-cost.png" alt="Le vrai coût du mainframe : coût opérationnel plus coût d'opportunité" style="width:100%">
{: .mx-auto.d-block :}
**Le vrai coût du mainframe : coût opérationnel plus coût d'opportunité**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

### Coût de transition et d'intégration

Il faut reconnaître que la transition des mainframes existants vers des bases de données distribuées modernes implique des coûts de migration initiaux. Ceux-ci peuvent inclure le transfert de données, la re-ingénierie des applications et des interruptions temporaires pendant la période de transition. Cependant, les économies à long terme et les gains d'efficacité obtenus grâce à la modernisation compensent ces coûts. Une planification et une exécution minutieuses du processus de migration peuvent minimiser davantage ces dépenses transitionnelles, assurant une migration plus fluide vers une infrastructure plus rentable et scalable.

Par exemple, les avantages financiers de la modernisation des bases de données mainframe existantes vers des solutions distribuées comme CockroachDB dépassent largement l'investissement initial. Les organisations peuvent atteindre un coût total de possession (TCO) inférieur grâce à la réduction des coûts matériels et opérationnels, à l'évolutivité améliorée et à une meilleure utilisation des ressources. De plus, l'agilité accrue et les capacités d'innovation favorisées par les bases de données modernes peuvent stimuler la croissance des revenus et l'expansion des activités, offrant un retour sur investissement (ROI) substantiel.

---

## Références

1. Joseph L. Bower et Clayton M. Christensen, [Disruptive Technologies: Catching the Wave](https://hbr.org/1995/01/disruptive-technologies-catching-the-wave), Harvard Business Review, 1995.
2. Clayton M. Christensen, [The Innovator's Dilemma: When New Technologies Cause Great Firms to Fail](https://www.hbs.edu/faculty/Pages/item.aspx?num=46), Harvard Business School Press, 1997.
3. Jamie Dimon, [Lettre du Président-Directeur Général aux actionnaires](https://reports.jpmorganchase.com/investor-relations/2020/ar-ceo-letters.htm), Rapport annuel de JPMorgan Chase, 2020.
