---
date: 2024-09-17
layout: post
lang: fr
title: "Du Mainframe au SQL Distribué, Une Introduction"
subtitle: "Qu'est-ce qu'un Mainframe ?"
cover-img: /assets/img/cover-mainframe.webp
thumbnail-img: /assets/img/cover-mainframe.webp
share-img: /assets/img/mainframe-diagram.png
tags: [mainframe, migration, database, CockroachDB]
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

Cet article inaugure une nouvelle série de billets consacrée à la migration des mainframes, dans une perspective d'adoption d'une architecture de base de données distribuée moderne.

Dans cette série, nous explorerons les forces et les limites des bases de données mainframe traditionnelles, en reconnaissant leur importance historique tout en prenant acte de la nécessité pressante d'évoluer face aux nouvelles exigences métier et aux tendances technologiques. Les risques de l'inaction sont évidents : réduction de l'agilité et de la capacité d'innovation, sans oublier les charges financières potentielles.

## L'héritage durable des systèmes mainframe et leur rôle central dans l'informatique d'entreprise

Depuis plus de 60 ans, l'ordinateur mainframe est le système de référence des grandes entreprises, des agences gouvernementales et des établissements d'enseignement. Aujourd'hui, cette technologie s'est répandue dans le monde entier : 92 des 100 premières banques mondiales, 10 des plus grands assureurs mondiaux, 18 des 25 premiers distributeurs et 70 % des entreprises du Fortune 500 s'appuient sur le mainframe. Si vous avez fait des achats, planifié des vacances ou effectué un paiement par carte de crédit, un mainframe a presque certainement traité votre transaction.

La Seconde Guerre mondiale a été un catalyseur majeur du développement des mainframes. Le gouvernement américain voyait dans cette technologie un moyen supérieur de calculer les trajectoires balistiques des armes et de la logistique, et de déchiffrer les codes ennemis. Le développement du Harvard Mark I — le premier mainframe, alors surnommé « The Big Iron » — débuta en 1939 et fut d'abord utilisé pour effectuer des calculs destinés au Projet Manhattan, l'effort américain de construction de la bombe nucléaire.

Qu'est-ce qu'un mainframe ? Le terme « mainframe » est apparu plus tard, en 1964, bien que son origine reste floue. Le concept s'est inspiré de l'industrie des télécommunications, plus précisément du système central d'un central téléphonique. Au fil du temps, il en est venu à désigner des systèmes informatiques de grande envergure capables de gérer d'importantes tâches de traitement de données, principalement adaptés aux besoins des entreprises et habiles à gérer des transactions à grande échelle.

En 1991, le journaliste et analyste politique américain Stewart Alsop prédit que le dernier mainframe serait débranché en 1996. À l'époque, cette prédiction n'était pas nécessairement controversée. IBM, le plus grand fournisseur de mainframes, luttait farouchement contre la montée en puissance de concurrents tels que Dell, Compaq et Sun Microsystems. Des spéculations circulaient sur la possible disparition de l'entreprise.

En réalité, la mort du mainframe a été grandement exagérée.

Bien que le mainframe soit confronté à des défis — comme le renouvellement croissant des personnels mainframe expérimentés, le côté « démodé » de la technologie sous-jacente, ou les coûts élevés liés aux postes de dépense uniques par rapport aux dépenses plus diversifiées des systèmes distribués —, il reste néanmoins, pour de nombreux cas d'usage et secteurs d'activité spécifiques, le choix optimal en termes de retour sur investissement IT. De nombreuses entreprises considéraient cette technologie comme un incontournable pour rester compétitives. Elles allaient même jusqu'à mettre en valeur leurs mainframes en les plaçant dans des salles vitrées au siège social.

<img src="/assets/img/mainframe-diagram.png" alt="Mainframe to Distributed SQL" style="width:100%">
{: .mx-auto.d-block :}
**Du Mainframe au SQL Distribué**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Cette technologie s'est avérée remarquablement durable. La fiabilité, la cohérence, la sécurité et les performances du mainframe ont solidement établi sa position comme épine dorsale de l'économie numérique. La dépendance continue à cette plateforme ne montre aucun signe de fléchissement. En 2002, Alsop a reconnu son erreur passée, admettant que les clients d'entreprise continuent de privilégier les systèmes informatiques gérés de manière centralisée et hautement fiables — précisément l'expertise qu'IBM fournit.

---

## Pourquoi le mainframe a-t-il perduré si longtemps ?

L'héritage durable des systèmes mainframe découle du rôle central qu'ils ont occupé dans l'informatique d'entreprise depuis leur création. Les mainframes ont été cruciaux pendant des décennies pour façonner le paysage numérique, stimuler l'innovation et soutenir les opérations critiques. L'une des principales raisons pour lesquelles le mainframe a perduré si longtemps est qu'il serait incroyablement coûteux de s'en débarrasser ! Il existe une idée reçue largement répandue selon laquelle migrer de tels systèmes serait risqué : les organisations craignent de perdre leur activité à cause de pannes dans les opérations critiques.

Un aspect clé de l'héritage durable du mainframe est sa fiabilité et sa résilience incomparables. Les mainframes sont reconnus pour leur fiabilité exceptionnelle. Par exemple, l'IBM z16 peut atteindre une disponibilité de neuf neuf (99,9999999 %) ou moins de 32 millisecondes d'indisponibilité par an. Ils sont construits avec des composants redondants pour se remettre rapidement des incidents et des mécanismes sophistiqués de vérification des erreurs intégrés à la fois dans le matériel et le système d'exploitation, minimisant le risque de défaillances du système et garantissant une exploitation continue. Cette fiabilité est essentielle pour les organisations opérant dans des secteurs où toute interruption est inacceptable, tels que la banque, la santé et les télécommunications.

Les mainframes fournissent des fonctionnalités de sécurité robustes, notamment le chiffrement intégré au matériel, les contrôles d'accès et les pistes d'audit, pour protéger les données sensibles et empêcher les accès non autorisés. Les derniers mainframes de la série z ont obtenu le niveau d'assurance d'évaluation des critères communs 5 (EAL5), le plus haut degré de sécurité.

De plus, les mainframes sont optimisés pour un traitement à haute vitesse et un débit de transactions élevé. Ils disposent de centaines de processeurs capables de traiter efficacement de grands volumes de données et d'exécuter des transactions complexes, ce qui les rend idéaux pour les charges de travail exigeantes. Ils sont conçus pour faire face à des demandes croissantes, ce qui les rend adaptés aux grandes entreprises et aux applications critiques.

Malgré l'émergence de nouvelles technologies et de paradigmes informatiques, les mainframes continuent de prospérer et d'évoluer grâce à leur adaptabilité et leur compatibilité avec les systèmes existants. Les mainframes offrent un support étendu pour les applications et systèmes existants, permettant aux organisations de valoriser leurs investissements antérieurs et d'éviter les migrations coûteuses. De plus, les principaux fournisseurs ont fortement investi dans l'innovation en adoptant des logiciels open source (par exemple, Linux, Python…, etc.) et en mettant en œuvre des avancées de pointe dans des domaines tels que l'IA, les intégrations et le DevOps. De nombreuses organisations s'appuient sur les mainframes pour exécuter des applications héritées et soutenir les processus métier fondamentaux, en tirant parti de leur investissement dans ces plateformes éprouvées.

<img src="/assets/img/mainframe-why-lasted.png" alt="Mainframe to Distributed SQL - Pourquoi le mainframe a-t-il perduré si longtemps ?" style="width:100%">
{: .mx-auto.d-block :}
**Du Mainframe au SQL Distribué - Pourquoi le mainframe a-t-il perduré si longtemps ?**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

En effet, les mainframes sont coûteux. Cependant, malgré l'investissement initial, ils ont démontré leur capacité à offrir des économies à long terme, en tenant compte du coût par transaction, grâce à leur sécurité, leur fiabilité et leurs performances. Ils peuvent consolider plusieurs serveurs et charges de travail, réduisant ainsi les coûts matériels, de maintenance et d'exploitation.

Les coûts énergétiques constituent le second poste de dépense le plus important pour un département informatique, après les effectifs. Les mainframes peuvent également offrir des coûts énergétiques plus faibles grâce à la centralisation du traitement. La consommation moyenne en watts par million d'instructions par seconde (MIPS) est d'environ 0,91, et ce chiffre diminue chaque année.

---

## Explorer les défis et les limites des architectures de bases de données mainframe traditionnelles dans le paysage numérique actuel

Dans le paysage numérique en rapide évolution d'aujourd'hui, les architectures de bases de données mainframe traditionnelles font face à plusieurs défis et limitations susceptibles d'entraver leur efficacité et leur adaptabilité.

### Passage à l'échelle

Bien que les bases de données mainframe puissent évoluer pour prendre en charge de grands volumes de données et un débit élevé de transactions, cette évolution peut nécessiter des ressources matérielles supplémentaires et une planification minutieuse. Le passage à l'échelle est vertical. Cela signifie que vous ne pouvez évoluer que dans les limites du mainframe. En cas de pics de demande inattendus, seule une mise à niveau matérielle planifiée peut permettre à votre base de données de gérer la charge de travail. L'évolution des bases de données mainframe sur plusieurs serveurs ou partitions peut introduire une complexité et des goulots d'étranglement potentiels en termes de performances.

### Accès aux données et intégrations

L'intégration des bases de données mainframe traditionnelles avec les systèmes cloud modernes et distribués peut s'avérer complexe et fastidieuse. Des problèmes de protocoles hérités, de formats de données et de compatibilité peuvent surgir, entraînant des défis d'interopérabilité et des silos de données au sein de l'organisation.

De plus, l'accès et l'extraction de données depuis les bases de données mainframe traditionnelles peuvent poser des difficultés, notamment pour les utilisateurs et les applications extérieurs à l'environnement mainframe. Le support limité pour les API standard, les formats de données et les langages de requête modernes peut entraver l'accessibilité des données et l'interopérabilité avec d'autres systèmes.

Par ailleurs, les bases de données mainframe offrent une compatibilité cloud très limitée. Bien qu'IBM propose des versions cloud de DB2, telles qu'IBM Db2 on Cloud, le passage des déploiements DB2 sur site existants vers le cloud peut nécessiter une planification minutieuse et des stratégies de migration adaptées. Les problèmes de compatibilité, les coûts de transfert de données et les considérations de performance peuvent influer sur la faisabilité du déplacement des charges de travail DB2 vers le cloud.

### Coût

Enfin, la maintenance et la modernisation des architectures de bases de données mainframe traditionnelles peuvent être onéreuses. Les coûts initiaux élevés liés au matériel mainframe, aux licences logicielles et à la maintenance continue peuvent peser sur les budgets informatiques, en particulier pour les organisations disposant de ressources limitées.

En réalité, la dépense informatique la plus importante est principalement liée à la pénurie de professionnels du mainframe. De nombreux professionnels du mainframe approchent de l'âge de la retraite, entraînant une perte de connaissances institutionnelles et d'expertise. À mesure que les professionnels expérimentés partent en retraite, il y a une pénurie d'individus qualifiés pour prendre leur relève.

Cette pénurie est également accentuée par le manque de programmes de formation formels et d'opportunités pédagogiques axés sur la technologie mainframe. La technologie mainframe est souvent perçue comme dépassée ou peu attrayante par rapport aux technologies plus récentes telles que le cloud computing et le développement mobile. Le rythme rapide de l'innovation technologique a entraîné une concurrence accrue pour les talents informatiques, de nombreux professionnels choisissant de travailler avec des technologies plus récentes perçues comme plus passionnantes ou innovantes que les mainframes. Par conséquent, les individus ont moins d'opportunités d'acquérir les compétences spécialisées et les connaissances nécessaires pour travailler avec les systèmes mainframe.

Mais, même lorsque les organisations parviennent à recruter des professionnels du mainframe, les fidéliser peut s'avérer difficile. Les professionnels du mainframe peuvent être attirés par des salaires plus élevés ou des opportunités plus séduisantes dans d'autres domaines de l'informatique.

---

## À propos de cette série, « Du Mainframe au SQL Distribué »

Les bases de données distribuées comme CockroachDB offrent scalabilité, performances, tolérance aux pannes et résilience, répondant à bon nombre des lacunes des systèmes de bases de données mainframe. La transition vers une architecture distribuée nécessite un examen minutieux des approches de migration, des outils, des meilleures pratiques, une gestion du changement robuste et des stratégies d'atténuation des risques. Les bénéfices sont toutefois substantiels, avec des opportunités d'innovation, d'agilité et d'avantage concurrentiel pour ceux qui embrassent l'avenir des bases de données distribuées.

En regardant vers l'avenir, l'appel à l'action est clair : il est temps d'embrasser l'avenir en exploitant la puissance de CockroachDB comme épine dorsale des architectures distribuées modernes. Ce faisant, les organisations peuvent se positionner pour réussir dans un monde de plus en plus dynamique et numérique.

Êtes-vous prêt à en apprendre davantage sur la migration réussie d'un mainframe vers une base de données distribuée cloud-native ? Visitez cette page pour me contacter.

---

## Références

1. [État du Mainframe, Blog BMC](https://www.bmc.com/blogs/state-of-mainframe/)
2. [Harvard Mark I, Wikipedia](https://en.wikipedia.org/wiki/Harvard_Mark_I)
3. [Que sont devenus les mainframes, Computer History Museum (CHM)](https://computerhistory.org/)
4. [IBM z16, TechChannel](https://techchannel.com/)
5. [Certifications IBM z-Series, IBM](https://www.ibm.com/)
6. Tom Taulli, *Modern Mainframe Development*, O'Reilly Media, 2022
