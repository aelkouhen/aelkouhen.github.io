---
layout: post
lang: fr
title: "Détection de fraude à grande échelle avec CockroachDB et AWS AI"
subtitle: "Comment l'indexation vectorielle permet une réponse intelligente aux menaces à faible latence à l'échelle mondiale"
cover-img: /assets/img/cover-ai-fraud.webp
thumbnail-img: /assets/img/cover-ai-fraud.webp
share-img: /assets/img/cover-ai-fraud.webp
tags: [Artificial Intelligence, CockroachDB, GenAI, vector search, fraud detection, AWS]
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

Dans la course aux armements contre la fraude financière, les millisecondes comptent. Pour toute transaction donnée, les systèmes de détection de fraude doivent décider si elle est frauduleuse ou non et agir immédiatement en conséquence. Ne pas traiter définitivement la fraude entraîne des pertes significatives, nuit à l'image de marque des organisations, ternit leur réputation et inévitablement repousse les clients.

L'incidence de la fraude a atteint des niveaux records. Les [estimations](https://www.cyberdefensemagazine.com/the-true-cost-of-cybercrime-why-global-damages-could-reach-1-2-1-5-trillion-by-end-of-year-2025/) pour le coût mondial de la fraude — incluant la cybercriminalité, la fraude financière et les pertes associées — varient de 1 200 à plus de 1 500 milliards de dollars par an d'ici fin 2025.

Pendant ce temps, les fraudeurs évoluent rapidement et progressent en parallèle avec les transformations de la banque numérique, inventant des moyens astucieux de voler ou de falsifier les identités des clients et de commettre des fraudes à haute vélocité. En conséquence, les systèmes de détection de fraude traditionnels basés sur des règles (hors ligne) ne sont plus efficaces, car ils s'appuient sur des heuristiques statiques et un traitement par lots qui ne peuvent pas suivre le rythme des tactiques de fraude adaptatives en temps réel.

Les systèmes de détection de fraude doivent ingérer des volumes massifs de données transactionnelles, les évaluer par rapport à des ensembles de règles dynamiques et prendre des décisions en temps réel — tout cela en opérant sur une infrastructure mondiale. Les bases de données traditionnelles s'effondrent souvent sous cette pression et offrent de mauvaises performances de prévention de la fraude, en raison de stratégies d'accès aux données inefficaces.

C'est là qu'intervient [CockroachDB](https://www.cockroachlabs.com/product/overview/), une base de données SQL distribuée conçue pour la scalabilité, la résilience et la performance. En ce qui concerne la dernière génération de systèmes de détection de fraude alimentés par l'IA, le cœur de l'avantage de CockroachDB réside dans ses [capacités avancées d'indexation vectorielle](/2025-11-23-cockroachdb-ai-spann/). En plus des index géo-partitionnés et inversés existants, CockroachDB permet aux développeurs de construire des systèmes de détection de fraude en ligne à la fois rapides et intelligents.

Cet article explore comment ces nouvelles fonctionnalités d'indexation vectorielle permettent la détection d'anomalies à faible latence, l'alerte en temps réel et la prise de décision sensible à la région — sans compromettre la justesse ou la scalabilité.

---

## Défis de la détection de fraude

Les systèmes de détection de fraude font face à plusieurs défis qui rendent difficile l'identification précise des activités frauduleuses. Certains de ces défis sont :

- **Évolution des techniques de fraude** : Les fraudeurs s'adaptent continuellement et développent de nouvelles techniques pour échapper à la détection. En conséquence, les systèmes de détection de fraude doivent être mis à jour régulièrement pour suivre l'évolution des schémas.

- **Qualité des données** : La précision des systèmes de détection de fraude dépend de la qualité de leurs données. Si les données sont incomplètes, incorrectes ou incohérentes, cela peut entraîner des faux positifs ou des faux négatifs, réduisant l'efficacité du système.

- **Équilibre entre détection de fraude et expérience utilisateur** : Bien que les systèmes de détection de fraude visent à minimiser la fraude, ils doivent également maintenir une bonne expérience utilisateur. Des règles de détection de fraude trop strictes peuvent entraîner des faux positifs et une friction accrue, conduisant à des clients mécontents.

- **Coût** : La mise en œuvre et la maintenance d'un système de détection de fraude peuvent être coûteuses. Le coût comprend l'acquisition et le traitement de grandes quantités de données, le développement et la maintenance des algorithmes et des modèles, et l'embauche de personnel pour gérer le système.

- **Problèmes de confidentialité** : Les systèmes de détection de fraude nécessitent l'accès à des données clients sensibles, ce qui peut soulever des problèmes de confidentialité. Les entreprises doivent s'assurer que leurs systèmes de détection de fraude respectent les réglementations sur la vie privée et mettre en œuvre des mesures de sécurité appropriées pour protéger les données.

Ensuite, nous nous concentrerons sur les deux principaux défis mentionnés ci-dessus : les faux positifs et la latence. Les deux conduisent à des clients mécontents et à des pertes substantielles.

### 1 - Faux positifs

Qu'est-ce qu'un faux positif ? Lorsqu'une transaction légitime est signalée comme fraude, cela est connu sous le nom de « faux positif ». Cette situation est très frustrante pour les clients et peut s'avérer assez coûteuse pour les entreprises. Pour relever ce défi, une approche multicouche est nécessaire pour améliorer la détection et apprendre continuellement des modèles de fraude en évolution.

L'approche multicouche est une technique utilisée dans les systèmes de détection de fraude pour améliorer la précision et l'efficacité de la détection de fraude. Elle implique l'utilisation de plusieurs couches de méthodes et techniques de détection de fraude pour détecter les activités frauduleuses. L'approche multicouche comprend généralement trois couches :

- ***Couche basée sur les règles*** : La première couche est un système basé sur des règles qui utilise des règles prédéfinies pour identifier les activités potentiellement frauduleuses. Ces règles sont basées sur des données historiques de fraude et sont conçues pour détecter des modèles de fraude connus. Quelques exemples de ces règles :

  - Mise en liste noire des adresses IP des fraudeurs
  - Dérivation et utilisation des données de latitude et de longitude à partir des adresses IP des utilisateurs
  - Utilisation des données sur le type et la version du navigateur, ainsi que sur le système d'exploitation, les plugins actifs, le fuseau horaire et la langue
  - Profil d'achat par utilisateur : cet utilisateur a-t-il déjà acheté dans ces catégories ?
  - Profils d'achat généraux : ce type d'utilisateur a-t-il déjà acheté dans ces catégories ?

Les règles peuvent être implémentées de manière à pouvoir aller d'un « faible coût » à un « coût élevé ». Si un utilisateur effectue un achat dans des catégories déjà connues et dans les montants de transaction min/max, l'application peut étiqueter la transaction comme non frauduleuse et sauter les étapes de détection ultérieures.

- ***Couche de détection d'anomalies*** : La deuxième couche est un système de détection d'anomalies qui identifie une activité inhabituelle basée sur des analyses statistiques des données transactionnelles. Cette couche utilise des algorithmes d'apprentissage automatique (ML) tels que [Random Cut Forest](https://docs.aws.amazon.com/sagemaker/latest/dg/randomcutforest.html) pour identifier des modèles qui ne sont généralement pas observés dans les transactions légitimes. Cette couche implique d'abord la conversion des données en un espace vectoriel de haute dimension à l'aide de techniques d'embedding — ici les embeddings représentent les différents attributs/règles de fraude comme la localisation, le montant de la transaction, le profil utilisateur, les adresses IP… puis l'entraînement d'un modèle Random Forest sur ces embeddings pour identifier les anomalies comme des points de données qui s'écartent significativement de la norme.

- ***Couche de modélisation prédictive*** : La troisième couche est un système de modélisation prédictive qui utilise des algorithmes d'apprentissage automatique avancés, tels que [XGBoost](https://www.nvidia.com/en-us/glossary/xgboost/), pour prédire la probabilité de fraude. Cette couche utilise des données historiques pour entraîner les modèles et peut détecter de nouveaux modèles de fraude qui ne sont pas détectés par les couches précédentes. Cette couche peut également être efficacement utilisée pour prédire les anomalies lorsqu'elle est combinée avec des vector embeddings.

<img src="/assets/img/ai-fraud-01.jpg" alt="Multi-Layered Fraud Detection" style="width:100%">
{: .mx-auto.d-block :}
**Détection de fraude multicouche**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

En utilisant une approche multicouche, les systèmes de détection de fraude peuvent minimiser les faux positifs et les faux négatifs, améliorant ainsi la précision de la détection de fraude. L'approche multicouche contribue également à détecter la fraude avec précision, empêchant l'insatisfaction des clients lorsqu'ils sont faussement signalés comme fraudeurs.

### 2 - Latence

Comme mentionné précédemment, les fraudeurs évoluent et deviennent plus complexes. Par conséquent, la détection ne doit pas prendre de retard, et une détection améliorée ne doit pas augmenter la latence. Si les entreprises ne peuvent pas détecter si la transaction est frauduleuse ou non en quelques millisecondes, par défaut, elle est considérée comme authentique. C'est pourquoi la latence est un défi important dans la détection de fraude.

Pour résoudre ce problème, les organisations peuvent exploiter la recherche par similarité vectorielle pour conserver et gérer les embeddings utilisés par les systèmes de détection de fraude en ligne (c'est-à-dire en temps réel).

Les embeddings sont les attributs utilisés par les modèles d'apprentissage automatique pour faire des prédictions ou des classifications. Des exemples du vecteur de transaction peuvent inclure les données démographiques des clients, l'historique d'achats, l'activité sur le site web et les préférences de produits. Une base de données vectorielle stocke ces vecteurs dans un emplacement centralisé et les fournit aux modèles d'apprentissage automatique avec une faible latence.

Bien que les bases de données vectorielles natives fournissent une recherche par similarité efficace grâce à des structures d'indexation avancées comme HNSW ou IVF, les bases de données relationnelles traditionnelles avec prise en charge vectorielle manquent souvent d'indexation vectorielle sophistiquée. Ces bases de données ont généralement recours à la recherche par force brute pour les opérations de similarité vectorielle. Par conséquent, lorsque le nombre de transactions à évaluer augmente à des millions ou même des milliards, les recherches vectorielles deviennent prohibitivement lentes et le système de détection de fraude perd sa capacité en temps réel.

CockroachDB répond à ce problème de performance fondamental avec la version 25.2, qui inclut un [support d'indexation haute performance pour les vecteurs multidimensionnels](/2025-11-23-cockroachdb-ai-spann/). L'optimiseur intègre des index vectoriels secondaires dans les plans de requête, et le moteur d'exécution implémente ce nouveau type d'index. Les utilisateurs peuvent écrire des requêtes qui recherchent efficacement à la fois des données relationnelles et vectorielles, même dans la même requête.

En [utilisant CockroachDB comme base de données vectorielle distribuée](/2025-10-05-cockroachdb-ai-intro/), les systèmes de détection de fraude peuvent accéder rapidement et réutiliser les données historiques (vecteurs) pour différents modèles sans les réingénierer ou les retraiter. À mesure que de nouvelles données sont collectées, la base de données peut mettre à jour les embeddings utilisés par les modèles d'apprentissage automatique, résultant en des prédictions de fraude plus précises. Cela améliore l'efficacité et réduit la latence lors de la détection de fraude.

---

## Système de détection de fraude avec CockroachDB et AWS AI

CockroachDB joue deux rôles dans le système de détection de fraude :

1. En tant que base de données OLTP (traitement des transactions en ligne) mondiale qui stocke et indexe les transactions financières.

2. En tant que base de données vectorielle opérée par les services AWS AI [Bedrock](https://aws.amazon.com/bedrock/) et [Sagemaker](https://aws.amazon.com/sagemaker/). Les deux rôles sont interdépendants et peuvent coexister sur un seul cluster.

En prérequis, des transactions historiques (données d'entraînement) sont transmises à AWS Sagemaker pour entraîner ses modèles ML. Une fois les transactions signalées comme frauduleuses, elles sont stockées dans CockroachDB sous forme de vector embeddings.

Le système de détection de fraude est démarré lorsqu'une fonction [AWS Lambda](https://aws.amazon.com/lambda/) consomme le flux de transactions en temps réel depuis [Kinesis](https://aws.amazon.com/kinesis/), applique les règles, crée les vector embeddings à l'aide des modèles de fondation AWS Bedrock, et déverse les données transactionnelles et vectorielles dans CockroachDB.

CockroachDB charge également les données historiques directement depuis un bucket S3 à l'aide de l'instruction `IMPORT INTO`. Les données peuvent ainsi entrer dans le pipeline de détection de fraude, en servant d'entrée pour entraîner et améliorer les modèles exécutés sur AWS SageMaker.

Rappelons les deux principaux défis de détection de fraude présentés ci-dessus, les faux positifs et la latence. CockroachDB peut répondre aux deux sous différents angles :

Premièrement, il applique des règles prédéfinies pour identifier les activités potentiellement frauduleuses (couche basée sur les règles). Cela garantit une mise en liste noire précise et cohérente des adresses IP en implémentant la limitation de débit et en utilisant les capacités géospatiales natives, pour calculer et évaluer la localisation de l'utilisateur. Ainsi, nous pouvons éviter tout faux positif en appliquant ces pré-filtres sur le trafic entrant.

Deuxièmement, pour fournir un système de détection de fraude à faible latence, le moteur doit rapidement lire le dernier vecteur inséré dans CockroachDB, rechercher parmi des milliards de vecteurs historiques étiquetés comme frauduleux et calculer la distance entre cette nouvelle transaction et les transactions frauduleuses. Ensuite, en se basant sur cette distance, le modèle ML classifiera la transaction.

<img src="/assets/img/ai-fraud-02.jpg" alt="GenAI-based Fraud Detection System" style="width:100%">
{: .mx-auto.d-block :}
**Système de détection de fraude basé sur le GenAI**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Cependant, même avec un bon backend de stockage, l'intégration du système de détection d'anomalies dans une base de données SQL distribuée comme CockroachDB n'est pas simple. Pour prendre en charge la scalabilité élastique, la tolérance aux pannes et la disponibilité multi-régions, CockroachDB a conçu l'indexation vectorielle avec une approche novatrice :

- Premièrement, elle doit fonctionner sans coordinateur central — chaque nœud du cluster doit pouvoir gérer les lectures et les écritures indépendamment, évitant les goulots d'étranglement ou les points de défaillance uniques.

- L'index doit également éviter de s'appuyer sur de grandes structures en mémoire ; au lieu de cela, son état doit être stocké de manière persistante pour s'adapter aux environnements serverless et à faible mémoire sans longs temps de démarrage.

- L'index doit éviter les points chauds en distribuant uniformément la charge de travail sur le cluster, même sous des insertions ou des requêtes à volume élevé.

- Enfin, il doit prendre en charge les mises à jour incrémentielles — gérant les insertions et les suppressions en temps réel sans bloquer les requêtes ou nécessiter des reconstructions complètes. Ces exigences ont éliminé de nombreuses stratégies d'indexation conventionnelles, incitant à la conception d'une nouvelle approche adaptée à l'architecture distribuée de CockroachDB.

<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;">
<iframe src="https://www.youtube.com/embed/j2ElRBAH8vM" title="CockroachDB For AI/ML: Vector Indexing" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen style="position:absolute;top:0;left:0;width:100%;height:100%;"></iframe>
</div>

Cet algorithme d'indexation vectorielle (appelé C-SPANN) est conçu pour organiser les vecteurs en partitions basées sur la similarité, chaque partition contenant généralement des dizaines à des centaines de vecteurs.

Chacune de ces partitions est représentée par un **centroïde** — la moyenne de tous les vecteurs qu'elle contient — servant de « centre de masse » pour ce groupe. Ces centroïdes sont ensuite regroupés récursivement en partitions de niveau supérieur, formant une structure arborescente à plusieurs niveaux (un arbre K-means hiérarchique).

Cette organisation hiérarchique permet à l'index de réduire rapidement l'espace de recherche en parcourant des clusters larges vers des sous-ensembles de plus en plus spécifiques. Le résultat est une efficacité et une vitesse considérablement améliorées des recherches vectorielles.

<img src="/assets/img/ai-fraud-03.jpg" alt="C-SPANN: Hierarchical K-means tree" style="width:100%">
{: .mx-auto.d-block :}
**C-SPANN : arbre K-means hiérarchique**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

À mesure que de nouveaux vecteurs sont insérés dans l'index, ils sont naturellement distribués sur plusieurs partitions, qui sont elles-mêmes réparties dans le cluster. Cette conception garantit qu'aucun nœud ou plage unique ne devient un goulot d'étranglement, empêchant efficacement la formation de points chauds et permettant au système de faire évoluer le débit d'écriture.

La division d'une partition améliore l'efficacité de la recherche en maintenant un regroupement serré des vecteurs. La division d'une plage aide à équilibrer le stockage des données et l'accès dans le cluster. Ensemble, ces mécanismes réduisent les points chauds et contribuent à répartir plus uniformément la charge des requêtes et des insertions.

Lorsque des nœuds sont ajoutés au système, les plages contenant des partitions d'index sont automatiquement distribuées sur les nouveaux nœuds. Cela permet à la charge de travail totale d'évoluer avec le cluster à des taux quasi-linéaires.

Le diagramme ci-dessous illustre l'architecture de la solution de détection de fraude implémentée avec [CockroachDB et AWS](https://www.cockroachlabs.com/partners/amazon-web-services-aws/) :

<img src="/assets/img/ai-fraud-04.jpg" alt="Reference Architecture of Fraud Detection with CockroachDB and AWS" style="width:100%">
{: .mx-auto.d-block :}
**Architecture de référence pour la détection de fraude avec CockroachDB et AWS**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

**A.** En prérequis, vous devez placer les jeux de données historiques de transactions par carte de crédit dans un bucket Amazon S3. Ces données servent à entraîner et tester les algorithmes d'apprentissage automatique qui détectent la fraude et les anomalies.

**B.** Amazon SageMaker est un service de workflow ML pour le développement, l'entraînement et le déploiement de modèles. Il est fourni avec de nombreux algorithmes prédéfinis. Vous pouvez également créer vos propres algorithmes en fournissant des images Docker, une image d'entraînement pour entraîner votre modèle et un modèle d'inférence à déployer sur un endpoint REST. Dans CockroachDB, nous avons choisi l'algorithme Random Cut Forest pour la détection d'anomalies et XGBoost pour la prédiction de fraude :

- Random Cut Forest (RCF) est un algorithme non supervisé qui détecte les points de données anormaux dans un jeu de données. Les anomalies sont des observations de données qui s'écartent du modèle ou de la structure attendus. Elles peuvent apparaître comme des pics inattendus dans les données de séries temporelles, des interruptions de périodicité ou des points de données non classifiables. Ces anomalies sont souvent facilement distinguables des données régulières lorsqu'elles sont visualisées dans un graphique.

RCF attribue un score d'anomalie à chaque point de données. Des scores faibles indiquent que le point de données est normal, tandis que des scores élevés indiquent la présence d'une anomalie. Le seuil de ce qui est considéré comme « faible » ou « élevé » dépend de l'application, mais généralement les scores au-delà de trois écarts types (**3σ**) de la moyenne sont considérés comme anormaux.

<img src="/assets/img/ai-fraud-05.png" alt="Anomaly score" style="width:100%">
{: .mx-auto.d-block :}
**Score d'anomalie**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

- [xGBoost](https://www.nvidia.com/en-us/glossary/xgboost/), abréviation de eXtreme Gradient Boosting, est une implémentation open-source largement utilisée de l'algorithme d'arbres à gradient boosté. Le gradient boosting est une méthode d'apprentissage supervisé qui vise à prédire une variable cible en combinant des estimations d'un ensemble de modèles plus simples et plus faibles.

L'algorithme XGBoost est très efficace dans les compétitions d'apprentissage automatique en raison de sa capacité à gérer divers types de données, distributions et relations, ainsi que la large gamme d'hyperparamètres qui peuvent être finement ajustés.

La fonction Lambda appelle les endpoints des modèles AWS SageMaker pour attribuer des scores d'anomalie et des scores de classification aux transactions historiques.

```python
def makeInferences(data_payload):
   print("** makeInferences - START")
   output = {}
   output["anomaly_detector"] = get_anomaly_prediction(data_payload)
   output["fraud_classifier"] = get_fraud_prediction(data_payload)
   print("** makeInferences - END")
   return output
```

- Détection d'anomalies :

```python
def get_anomaly_prediction(data):
   sagemaker_endpoint_name = 'random-cut-forest-endpoint'
   sagemaker_runtime = boto3.client('sagemaker-runtime')
  response=sagemaker_runtime.invoke_endpoint(EndpointName=sagemaker_endpoint_name, ContentType='text/csv', Body=data)
   print("response from get_anomaly_prediction=")
   # Extract anomaly score from the endpoint response
   anomaly_score=json.loads(response['Body'].read().decode())["scores"][0]["score"]
   print("anomaly score: {}".format(anomaly_score))
   return {"score": anomaly_score}
```

- Prédiction de fraude :

```python
def get_fraud_prediction(data, threshold=0.5):
   sagemaker_endpoint_name = 'fraud-detection-endpoint'
   sagemaker_runtime = boto3.client('sagemaker-runtime')
   response=sagemaker_runtime.invoke_endpoint(EndpointName=sagemaker_endpoint_name, ContentType='text/csv', Body=data)
   print("response from get_fraud_prediction=")
   pred_proba = json.loads(response['Body'].read().decode())
   prediction = 0 if pred_proba < threshold else 1
   # Note: XGBoost returns a float as a prediction, a linear learner would require different handling.
   print("classification pred_proba: {}, prediction: {}".format(pred_proba, prediction))
   return {"pred_proba": pred_proba, "prediction": prediction}
```

**C.** Une instance de notebook appelle un modèle d'embedding personnalisé d'AWS Bedrock pour vectoriser les jeux de données historiques entraînés et scorés par AWS Sagemaker. Ensuite, les transactions frauduleuses sont stockées sous forme de vecteurs dans CockroachDB (Étape 0 dans le diagramme).

**1.** Le flux de données commence avec les utilisateurs finaux (clients mobiles et web) invoquant l'API REST d'Amazon API Gateway.

**2.** Qu'est-ce qu'Amazon Kinesis Data Streams ? Ces flux sont utilisés pour capturer des données d'événements en temps réel. [Amazon Kinesis](https://aws.amazon.com/kinesis/) est un service entièrement géré pour le traitement de données en flux à n'importe quelle échelle. Il fournit une plateforme serverless qui collecte, traite et analyse facilement les données en temps réel pour vous permettre d'obtenir des informations opportunes et de réagir rapidement aux nouvelles informations. Kinesis peut gérer n'importe quelle quantité de données en streaming et traiter des données provenant de centaines de milliers de sources avec de faibles latences.

**3.** Qu'est-ce qu'AWS Lambda ? C'est un service de calcul serverless et piloté par les événements qui vous permet d'exécuter du code pour pratiquement n'importe quel type d'application ou de service backend sans provisionner ni gérer de serveurs. Dans notre solution, la fonction Lambda est déclenchée par Kinesis pour lire le flux et effectuer les actions suivantes :

**3a.** Persister les données transactionnelles dans CockroachDB pour permettre l'indexation et l'interrogation à faible latence des transactions. Pour cela, le schéma suivant a été créé dans la base de données `FRAUD_DB` :

```sql
CREATE TABLE FRAUD_DB.transactions (
    transaction_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id         UUID NOT NULL,
    merchant_id        UUID,
    transaction_type   TEXT NOT NULL CHECK (transaction_type IN ('debit', 'credit', 'refund', 'chargeback')),
    amount             BIGINT NOT NULL CHECK (amount_cents >= 0),
    currency_code      CHAR(3) NOT NULL,
    status             TEXT NOT NULL CHECK (status IN ('pending', 'completed', 'failed', 'reversed')),
    transaction_time   TIMESTAMPTZ NOT NULL DEFAULT now(),
    location_ip        INET,
    location           POINT,
    metadata           JSONB,
    created_at         TIMESTAMPTZ DEFAULT now(),
    updated_at         TIMESTAMPTZ DEFAULT now(),
    transaction_vector VECTOR(24)
);
```

**3b.** La première couche dans l'approche de détection de fraude est un système basé sur des règles qui applique des règles prédéfinies pour identifier les activités potentiellement frauduleuses. Les règles peuvent être implémentées de manière à aller d'un « faible coût » à un « coût élevé ».

Par exemple, vous pouvez implémenter une fonction de limitation de débit dans CockroachDB qui vérifie les adresses IP et met en liste noire toute adresse qui se connecte plus qu'une certaine limite. Ainsi, vous pouvez appliquer une détection d'anomalies préliminaire sans utiliser l'inférence ML.

**3c.** Lorsqu'une anomalie basée sur des règles est identifiée, un trigger CockroachDB notifie l'utilisateur final et demande une validation pour la transaction.

**4.** Pour éviter les faux positifs et les faux négatifs, un autre trigger CockroachDB exécute une fonction qui calcule la distance entre les nouveaux vecteurs de transactions entrants et les milliards de transactions frauduleuses historiques stockées sous forme de vecteurs. La fonction enregistre ensuite les résultats de la recherche dans CockroachDB.

Lorsque nous effectuons une recherche par similarité sans un index vectoriel approprié, le principal défi est que votre moteur de base de données effectuera un scan complet de toutes vos données et calculera les métriques de similarité pour trouver les vecteurs les plus proches de votre requête.

Pour vérifier cela, vous pouvez utiliser l'instruction EXPLAIN qui retourne le plan de requête de CockroachDB. Vous pouvez utiliser ces informations pour optimiser la requête et éviter de scanner l'intégralité de la table, ce qui est la façon la plus lente d'accéder aux données.

Appliquons cette instruction à la requête de recherche par similarité :

```sql
EXPLAIN SELECT transaction_id, transaction_vector <-> new_trancation_vector AS l2_distance FROM fraudulent_transactions ORDER BY l2_distance DESC;
```

La sortie montre la structure arborescente du plan de l'instruction, dans ce cas un tri et un scan :

```
info -----------------------------------------------------------------------
distribution: full
vectorized: true
• sort
│ estimated row count: 3.000.000
│ order: -l2_distance
│ └── • render
│     └── • scan
        estimated row count: 3.000.000 (100% of the table; stats collected 2 minutes ago)
        table: fraudulent_transactions@transaction_id
        spans: FULL SCAN
```

Créons maintenant un index vectoriel sur le vecteur de transaction :

```sql
CREATE VECTOR INDEX trx_vector_idx ON transactions (transaction_vector);
```

Une fois l'index vectoriel affiné, le prochain appel `EXPLAIN` démontre que la portée du scan est maintenant `LIMITED SCAN`. Cela indique que la table sera scannée sur un sous-ensemble des plages de clés d'index.

```
info -----------------------------------------------------------------------
distribution: local
vectorized: true
• sort
│ estimated row count: 294.547
│ order: -l2_distance
│ └── • render
│     └── • vector search
        table: fraudulent_transactions@trx_vector_idx
        target count: 294.547
        spans: LIMITED SCAN
```

Comme vous pouvez l'observer, le nombre de lignes estimé est d'environ 10 % du nombre total de lignes de la table. Cela améliore considérablement le temps d'exécution de la recherche vectorielle, et la latence globale du système de détection de fraude.

Notez que la précision de la recherche dépend fortement de facteurs de charge de travail tels que :

- la taille des partitions
- le nombre de dimensions `VECTOR`
- dans quelle mesure les embeddings reflètent la similarité sémantique
- la distribution des vecteurs dans le jeu de données.

**5.** Optionnellement, les résultats de la recherche par similarité, avec les détails transactionnels, peuvent également être stockés dans une base de données de séries temporelles pour des visualisations de données ultérieures en utilisant la plateforme d'observabilité [Grafana](https://grafana.com/).

Ci-dessous se trouve le tableau de bord Grafana qui montre les scores de fraude en temps réel pour les transactions entrantes. Sur une échelle de 0 à 1 et pour toute transaction donnée, si le score de fraude dépasse 0,8, elle est considérée comme frauduleuse et affichée en rouge. De plus, d'autres graphiques sont utilisés pour visualiser l'activité de fraude au fil du temps ou pour comparer les transactions frauduleuses par rapport aux non-frauduleuses (côté inférieur).

<img src="/assets/img/ai-fraud-06.gif" alt="Real-Time Fraud Monitoring using Grafana" style="width:100%">
{: .mx-auto.d-block :}
**Surveillance de fraude en temps réel avec Grafana**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

---

## Comment vaincre la fraude

L'architecture distribuée et les capacités d'indexation vectorielle de CockroachDB débloquent quelque chose de puissant : un nouveau niveau de vitesse et d'intelligence pour la détection de fraude en temps réel.

Associé aux services AWS AI comme Bedrock, SageMaker et Lambda, vous pouvez construire un pipeline robuste et scalable qui détecte les anomalies tôt, les classifie avec précision et répond en quelques secondes. Ce système réduit non seulement le risque de fraude, mais évite également de bloquer les utilisateurs légitimes — maintenant la sécurité et la confiance des utilisateurs, pour que les entreprises puissent croître.

---

## Ressources

- [Documentation de la recherche vectorielle CockroachDB](https://www.cockroachlabs.com/docs/stable/vector-search.html)
- [C-SPANN : Indexation en temps réel pour des milliards de vecteurs](/2025-11-23-cockroachdb-ai-spann/)
- [Article original : Détection de fraude à grande échelle avec CockroachDB et AWS AI](https://www.cockroachlabs.com/blog/fraud-detection-at-scale/)
- [Le vrai coût de la cybercriminalité](https://www.cyberdefensemagazine.com/the-true-cost-of-cybercrime-why-global-damages-could-reach-1-2-1-5-trillion-by-end-of-year-2025/)
- [La recherche vectorielle rencontre le SQL distribué](https://www.cockroachlabs.com/guides/vector-search-meets-distributed-sql/)
- [Amazon Kinesis Data Streams](https://aws.amazon.com/kinesis/data-streams/)
- [AWS Lambda](https://aws.amazon.com/lambda/)
- [Amazon SageMaker](https://aws.amazon.com/sagemaker/)
- [Amazon Bedrock](https://aws.amazon.com/bedrock/)
