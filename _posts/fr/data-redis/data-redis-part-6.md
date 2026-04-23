---
date: 2023-05-10
layout: post
lang: fr
title: "Data & Redis, Partie 6"
subtitle: Détection de fraude avec Redis & AWS
thumbnail-img: assets/img/redis-fraud.png
share-img: https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEgq94kMwVFG38im1WnDmDIKr0z28a0ngHUNKc9NF4oL1c_Zl6Jouq5WVE1zmlncjLXXXdhCsZuFBP2tD4o82AEERe7J-9WF94T9ZyXpOCjdo-6vqsCsd0zr-NoLVw7qywri1WufpyoGkrOWe28iHGE0V6Eo2Voq8EXqoJ5aWBarHT7g7LUSR3yBPLfP
tags: [AWS,fraud detection,machine learning,Redis,Redis Gears,RedisBloom,RediSearch,RedisJSON,RedisTimeSeries]
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---
 
Dans la suite de cette série, je vais mettre en avant un ensemble de cas d'utilisation dans lesquels Redis apporte un réel avantage. Dans cet article, je vais présenter comment Redis Enterprise peut contribuer à implémenter un système de détection de fraude en temps réel.

Pour toute transaction donnée, ce système doit décider si elle est frauduleuse ou non et agir en conséquence en quelques secondes. Ne pas traiter la fraude de manière décisive entraîne des pertes significatives, nuit à l'image de marque des organisations, ternit leur réputation et inévitablement rebute les clients.

Malheureusement, les fraudeurs évoluent rapidement et avancent de pair avec les transformations de la banque numérique, découvrant des moyens innovants pour voler ou usurper l'identité des clients et commettre des fraudes. En conséquence, les systèmes de détection de fraude traditionnels basés sur des règles ne sont plus efficaces. Un défi majeur est de minimiser les faux positifs et d'identifier avec précision la fraude en temps réel.

Dans les sections suivantes, je vais introduire les principaux défis de la détection de fraude et comment Redis Enterprise peut aider à les relever.

## Défis de la détection de fraude

Les systèmes de détection de fraude font face à plusieurs défis qui rendent difficile l'identification précise des activités frauduleuses. Parmi ces défis :

*   Évolution des techniques de fraude : les fraudeurs s'adaptent continuellement et développent de nouvelles techniques pour échapper à la détection. Par conséquent, les systèmes de détection de fraude doivent être **_mis à jour régulièrement_** pour suivre ces techniques en constante évolution.
*   Qualité des données : la précision des systèmes de détection de fraude dépend de la qualité de leurs données. Si les données sont incomplètes, incorrectes ou incohérentes, cela peut entraîner des faux positifs ou des faux négatifs, réduisant ainsi l'efficacité du système.
*   Équilibre entre détection de fraude et expérience utilisateur : bien que les systèmes de détection de fraude visent à minimiser la fraude, ils doivent également maintenir une bonne expérience utilisateur. Des règles de détection de fraude trop strictes peuvent entraîner des **_faux positifs_**, conduisant à des clients insatisfaits.
*   Coût : la mise en place et la maintenance d'un système de détection de fraude peuvent être coûteuses. Le coût comprend l'acquisition et le traitement de grandes quantités de données, le développement et la maintenance des algorithmes et modèles, et le recrutement de personnel pour gérer le système.
*   Préoccupations de confidentialité : les systèmes de détection de fraude nécessitent un accès aux données sensibles des clients, ce qui peut soulever des préoccupations de confidentialité. Les entreprises doivent s'assurer que leurs systèmes de détection de fraude sont conformes aux réglementations sur la confidentialité et mettent en œuvre des mesures de sécurité appropriées pour protéger les données.

Dans cet article, parmi les défis ci-dessus, nous nous concentrerons sur les deux principaux  -  les faux positifs et la latence. Les deux entraînent des clients insatisfaits et des pertes substantielles pour les vendeurs.

### 1 - Faux positifs

Lorsqu'une transaction légitime d'un utilisateur est signalée comme fraude par le système, on parle de **_faux positif_**. Cette situation est très frustrante pour le client et peut s'avérer assez coûteuse pour le vendeur. Pour relever ce défi, une approche multi-couches est nécessaire pour améliorer la détection et apprendre continuellement des modèles de fraude en évolution.

L'approche multi-couches est une technique utilisée dans les systèmes de détection de fraude pour améliorer la précision et l'efficacité de la détection. Elle implique l'utilisation de plusieurs couches de méthodes et de techniques de détection de fraude pour détecter les activités frauduleuses. L'approche multi-couches comprend généralement trois couches :

*   **Couche basée sur des règles** : la première couche est un système basé sur des règles qui utilise des règles prédéfinies pour identifier les activités potentiellement frauduleuses. Ces règles sont basées sur des données historiques de fraude et sont conçues pour détecter les modèles de fraude connus. Voici quelques exemples de ces règles :
      - Mise sur liste noire des adresses IP des fraudeurs
      - Dérivation et utilisation des données de latitude et de longitude à partir des adresses IP des utilisateurs
      - Utilisation des données sur le type et la version du navigateur, ainsi que le système d'exploitation, les plugins actifs, le fuseau horaire et la langue
      - Profil d'achat par utilisateur : cet utilisateur a-t-il déjà acheté dans ces catégories ?
      - Profils d'achat généraux : ce type d'utilisateur a-t-il déjà acheté dans ces catégories ?

      Les règles peuvent être implémentées de manière à aller d'un « faible coût » à un « coût élevé ». Si un utilisateur effectue un achat dans des catégories déjà effectuées et dans des montants min/max, l'application peut étiqueter la transaction comme non frauduleuse et éliminer les cycles à dépenser sur d'autres règles et la couche ML.

*   **Couche de détection d'anomalies** : la deuxième couche est un système de détection d'anomalies qui identifie les activités inhabituelles basées sur des analyses statistiques des données transactionnelles. Cette couche utilise des algorithmes d'apprentissage automatique tels que **Random Cut Forest** pour identifier les modèles qui ne sont généralement pas observés dans les transactions légitimes.
*   **Couche de modélisation prédictive** : la troisième couche est un système de modélisation prédictive qui utilise des algorithmes d'apprentissage automatique avancés, tels que **XGBoost**, pour prédire la probabilité de fraude. Cette couche utilise des données historiques pour entraîner les modèles et peut détecter de nouveaux modèles de fraude non détectés par les couches précédentes.

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEgyJspSmD9ZcUrunyldMrQMyZEFrMDCzSuLMRscQeYli8T-lTrA8s3-LRI7-Y-WJi9m38C3CkkiYRrivybIr4YMgfSZX27v2z-T_Lz92FRbq12mujYz58S3oNJF7dGeT82wM4mfF4gjLMBA6LDCcRX0lcRGNM3IKF7jfA6_s3lMUmb3kbI3soUc2pya){: .mx-auto.d-block :} *Détection de fraude multi-couches.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

En utilisant une approche multi-couches, les systèmes de détection de fraude peuvent minimiser les faux positifs et les faux négatifs, améliorant ainsi la précision de la détection de fraude. L'approche multi-couches aide également à détecter la fraude en temps réel, permettant une action rapide pour prévenir les pertes.

### 2 - Latence

Comme mentionné dans les défis ci-dessus, les fraudeurs évoluent et deviennent plus complexes. Par conséquent, la détection ne doit pas prendre du retard, et une détection améliorée ne doit pas augmenter la latence. Si les entreprises ne peuvent pas détecter si la transaction est frauduleuse ou non en quelques secondes, elle est considérée par défaut comme authentique. C'est pourquoi la latence est un défi majeur dans la détection de fraude.

Pour résoudre ce problème, les organisations peuvent tirer parti des feature stores en ligne pour conserver et gérer les features utilisées par les modèles d'apprentissage automatique dans un environnement en ligne ou en temps réel.

Les features sont les variables ou attributs utilisés par les modèles d'apprentissage automatique pour faire des prédictions ou des classifications. Les exemples de features comprennent les données démographiques des clients, l'historique des achats, l'activité sur le site web et les préférences de produits. Un feature store en ligne stocke ces features dans un emplacement centralisé et les fournit aux modèles d'apprentissage automatique en temps réel.

Le feature store en ligne est conçu pour résoudre le défi de la gestion et du déploiement des modèles d'apprentissage automatique en temps réel. En fournissant un référentiel centralisé, les systèmes de détection de fraude peuvent rapidement accéder et réutiliser les features pour différents modèles sans avoir à les ré-ingénier ou les retraiter. Cela améliore l'efficacité et réduit la latence de détection de la fraude.

Le feature store en ligne peut également améliorer la précision des modèles d'apprentissage automatique en fournissant des mises à jour de features en temps réel. Au fur et à mesure que de nouvelles données sont collectées, le feature store peut mettre à jour les features utilisées par les modèles d'apprentissage automatique, ce qui permet des prédictions de fraude plus précises.

## Système de détection de fraude avec Redis Enterprise & AWS SageMaker

Redis Enterprise joue deux fonctions dans une solution de détection de fraude. Premièrement, il est utilisé comme base de données primaire multi-modèle qui stocke et indexe les documents JSON (représentant les transactions) et comme feature store en ligne opéré par une plateforme d'apprentissage automatique telle qu'AWS SageMaker. Un seul cluster Redis peut servir ces deux fonctions. Il n'est pas nécessaire d'avoir des clusters séparés.

Les fonctions AWS Lambda consomment les messages de Kinesis (transactions des utilisateurs finaux), appliquent les règles et les chargent dans les bases de données Redis. Redis Enterprise peut également persister les données directement dans un bucket S3 via des sauvegardes périodiques. Dans un pipeline ML, ces données sont l'entrée pour entraîner et améliorer les modèles fonctionnant sur SageMaker.

Rappelons les deux principaux défis de la détection de fraude présentés ci-dessus. Redis peut les aborder sous différents angles :

1.  Premièrement, en appliquant les règles prédéfinies pour identifier les activités potentiellement frauduleuses (couche basée sur des règles)  -  en utilisant RedisBloom/Cuckoo Filters, vous pouvez implémenter efficacement la mise sur liste noire des adresses IP. Ensuite, avec les opérations géospatiales natives de Redis comme `GEOSEARCH`, `GEORADIUS` et `GEOPOS`, vous pouvez calculer les données de latitude et de longitude à partir des adresses IP des utilisateurs. De plus, Redis peut stocker et indexer du JSON via ses modules RedisJSON et RediSearch. Cela, ainsi que les autres types de données Redis, permet à l'application d'implémenter la logique de profilage des utilisateurs et des achats.
2.  Le moteur d'apprentissage automatique doit lire rapidement les dernières valeurs de features du feature store en ligne et les utiliser au moment de l'inférence. Ensuite, basé sur les features en temps réel, le modèle ML notera la transaction. En raison de sa latence ultra-faible, Redis Enterprise est parfaitement adapté pour l'accès en ligne et en temps réel aux données de features dans le cadre d'une solution/implémentation de feature store en ligne.
3.  Enfin, les données de séries temporelles peuvent être stockées dans Redis via le module RedisTimeSeries. Ceci est important si vous souhaitez implémenter un tableau de bord en temps réel.

Le diagramme ci-dessous représente l'architecture de solution implémentée avec Redis Enterprise et AWS et les détails de son flux de données.

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEgq94kMwVFG38im1WnDmDIKr0z28a0ngHUNKc9NF4oL1c_Zl6Jouq5WVE1zmlncjLXXXdhCsZuFBP2tD4o82AEERe7J-9WF94T9ZyXpOCjdo-6vqsCsd0zr-NoLVw7qywri1WufpyoGkrOWe28iHGE0V6Eo2Voq8EXqoJ5aWBarHT7g7LUSR3yBPLfP){: .mx-auto.d-block :} *Système de détection de fraude avec Redis Enterprise et AWS.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

A. En pré-requis, vous devez mettre des jeux de données historiques de transactions par carte de crédit dans un bucket Amazon Simple Storage Service (Amazon S3). Ces données servent à entraîner et à tester les algorithmes d'apprentissage automatique qui détectent la fraude et les anomalies.

B. Une instance de notebook Amazon SageMaker avec différents modèles ML s'entraînera sur les jeux de données historiques. Amazon SageMaker est un service de workflow d'apprentissage automatique (ML) pour développer, entraîner et déployer des modèles. Il est livré avec de nombreux algorithmes prédéfinis. Vous pouvez également créer vos propres algorithmes en fournissant des images Docker, une image d'entraînement pour entraîner votre modèle et un modèle d'inférence à déployer sur un point d'accès REST. Dans notre solution, nous avons choisi l'algorithme Random Cut Forest pour la détection d'anomalies et XGBoost pour la prédiction de fraude :

*   **Random Cut Forest** (RCF) est un algorithme non supervisé qui détecte les points de données anormaux dans un jeu de données. Les anomalies sont des observations de données qui dévient du modèle ou de la structure attendus. Elles peuvent apparaître comme des pics inattendus dans des données de séries temporelles, des interruptions de périodicité ou des points de données inclassables. Ces anomalies sont souvent facilement distinguables des données régulières lorsqu'elles sont vues dans un graphique.

    RCF attribue un score d'anomalie à chaque point de données. Des scores bas indiquent que le point de données est normal, tandis que des scores élevés indiquent la présence d'une anomalie. Le seuil de ce qui est considéré comme « bas » ou « élevé » dépend de l'application, mais généralement les scores au-delà de trois écarts-types de la moyenne sont considérés comme anormaux.

*   **xGBoost**, abréviation d'eXtreme Gradient Boosting, est une implémentation open-source largement utilisée de l'algorithme de gradient boosting des arbres. Le gradient boosting est une méthode d'apprentissage supervisé qui vise à prédire une variable cible en combinant des estimations d'un ensemble de modèles plus simples et plus faibles. L'algorithme XGBoost est très efficace dans les compétitions d'apprentissage automatique grâce à sa capacité à gérer divers types de données, distributions et relations, ainsi que la large gamme d'hyperparamètres qui peuvent être réglés finement.

1\. Le flux de données commence avec les utilisateurs finaux (clients mobiles et web) invoquant l'API REST Amazon API Gateway pour les prédictions à l'aide de requêtes HTTP signées.

2\. Amazon Kinesis Data Streams est utilisé pour capturer des données d'événements en temps réel. Amazon Kinesis est un service entièrement géré pour le traitement de données de stream à n'importe quelle échelle. Il fournit une plateforme serverless qui collecte, traite et analyse facilement les données en temps réel afin que vous puissiez obtenir des insights opportuns et réagir rapidement aux nouvelles informations. Kinesis peut gérer n'importe quelle quantité de données en streaming et traiter des données provenant de centaines de milliers de sources avec de faibles latences.

3\. AWS Lambda est un service de calcul serverless et événementiel qui vous permet d'exécuter du code pour pratiquement n'importe quel type d'application ou de service backend sans provisionner ni gérer de serveurs. Vous pouvez déclencher Lambda à partir de plus de 200 services AWS et d'applications Software as a Service (SaaS) et ne payer que pour ce que vous utilisez. Dans notre solution, la fonction Lambda est déclenchée par Kinesis pour lire le stream et effectuer les actions suivantes :

4\. Persister les données transactionnelles dans RedisJSON pour permettre l'indexation et l'interrogation des transactions à faible latence.

{% highlight python linenos %}
def persistTransactionalData(payload_dict):
    print("** persistTransactionalData - START")
    now = datetime.datetime.now() # current date and time
    trans_date_trans_time = now.strftime("%Y/%m/%d-%H:%M:%S")
    key = "fraud:" + trans_date_trans_time

    redis_client.json().set(key, Path.root_path(), payload_dict)
    result = redis_client.json().get(key)
    print(result)
    print("** persistTransactionalData - END")
{% endhighlight %}

5\. La première couche de l'approche multi-couches de détection de fraude est un système basé sur des règles qui utilise des règles prédéfinies pour identifier les activités potentiellement frauduleuses. Les règles peuvent être implémentées de manière à aller d'un « faible coût » à un « coût élevé ». Par exemple, en utilisant RedisBloom/Cuckoo Filters, vous pouvez implémenter efficacement la mise sur liste noire des adresses IP. Ensuite, avec les opérations géospatiales natives de Redis comme `GEOSEARCH`, `GEORADIUS` et `GEOPOS`, vous pouvez identifier les données de latitude et de longitude à partir des adresses IP des utilisateurs et les comparer avec l'adresse de l'utilisateur dans les enregistrements. Ainsi, vous pouvez appliquer une détection d'anomalies préliminaire sans utiliser l'inférence ML.

5b. Lorsqu'une anomalie basée sur des règles est identifiée, vous pouvez utiliser Redis Gears pour déclencher d'autres actions.

5c. Vous pouvez implémenter une fonction Gears qui notifie l'utilisateur final et demande une validation pour la transaction.

6\. Pour éviter les faux positifs et les faux négatifs, la fonction Lambda appelle les points d'accès des modèles SageMaker pour attribuer des scores d'anomalie et des scores de classification aux transactions entrantes.

{% highlight python linenos %}
def makeInferences(data_payload):
    print("** makeInferences - START")
    output = {}
    output["anomaly_detector"] = get_anomaly_prediction(data_payload)
    output["fraud_classifier"] = get_fraud_prediction(data_payload)
    print(output)
    print("** makeInferences - END")
    return output
{% endhighlight %}

\- Détection d'anomalies :


{% highlight python linenos %}
def get_anomaly_prediction(data):
    sagemaker_endpoint_name = 'random-cut-forest-endpoint'
    sagemaker_runtime = boto3.client('sagemaker-runtime')
    response = sagemaker_runtime.invoke_endpoint(EndpointName=sagemaker_endpoint_name, ContentType='text/csv', Body=data)
    print("response from get_anomaly_prediction=")
    print(response)
    # Extract anomaly score from the endpoint response
    anomaly_score = json.loads(response['Body'].read().decode())["scores"][0]["score"]
    print("anomaly score: {}".format(anomaly_score))
    return {"score": anomaly_score}
    
{% endhighlight %}

\- Prédiction de fraude :

{% highlight python linenos %}
def get_fraud_prediction(data, threshold=0.5):
    sagemaker_endpoint_name = 'fraud-detection-endpoint'
    sagemaker_runtime = boto3.client('sagemaker-runtime')
    response = sagemaker_runtime.invoke_endpoint(EndpointName=sagemaker_endpoint_name, ContentType='text/csv', Body=data)
    print("response from get_fraud_prediction=")
    print(response)
    pred_proba = json.loads(response['Body'].read().decode())
    print(pred_proba)
    prediction = 0 if pred_proba < threshold else 1
    # Note: XGBoost returns a float as a prediction, a linear learner would require different handling.
    print("classification pred_proba: {}, prediction: {}".format(pred_proba, prediction))

    return {"pred_proba": pred_proba, "prediction": prediction}
{% endhighlight %}

7\. La fonction AWS Lambda exploite également Redis Enterprise Cloud comme feature store en ligne à faible latence.

8\. La fonction AWS Lambda persiste ensuite les résultats des prédictions dans Redis Enterprise. Optionnellement, les résultats, ainsi que les détails transactionnels, peuvent également être stockés dans une base de données de séries temporelles pour des visualisations de données ultérieures à l'aide de Grafana.

{% highlight python linenos %}
def persistMLScores(output):
    print("** persistMLScores - START")
    print(output)

    fraud_score = round(random.uniform(0.1, 1.0), 10)
    print ("**** fraud_score = %2.2f" % (fraud_score))

    key = 'fraud-ts'
    now = datetime.datetime.now() # current date and time
    timestamp = int(round(now.timestamp()))
    print(timestamp)

    redis_client.ts().add(key,timestamp,fraud_score,duplicate_policy='last')
    if (fraud_score >= 0.7 ):
        redis_client.ts().add("fraudulent_ts","*",fraud_score,duplicate_policy='last', labels={'type': "fraud_score"})
        print("*** adding to fraudulent series with current timestamp")
    else:
        redis_client.ts().add("non-fraudulent_ts","*",fraud_score,duplicate_policy='last', labels={'type': "fraud_score"})
        print("*** adding to non-fraudulent series with current timestamp")

    print("** persistMLScores - END")
{% endhighlight %}

Ci-dessous se trouve le tableau de bord Grafana qui affiche les scores de fraude en temps réel pour les transactions entrantes. Pour toute transaction donnée, si le score dépasse 0,8, elle est considérée comme frauduleuse et affichée en rouge. De plus, d'autres graphiques sont utilisés pour visualiser l'activité frauduleuse dans le temps ou pour comparer les transactions frauduleuses et non frauduleuses (côté bas).

![](https://lh6.googleusercontent.com/cpabKTP9YhhdOnt22k7vGbX5uyY8PhmmgtwiAR3fEhuY6Cly33Fyif1BeYijOG_OGv8h7sfan0jsJV3xWk4ioy2BCJthWM_meaLWmm3lKbVp7YFa9DuT_DKlNwm--FqSrm8DuCiPOc5nhywxpBuuwz3mGA){: .mx-auto.d-block :} *Surveillance de la fraude en temps réel avec Grafana.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Le code source de cette solution de détection de fraude est disponible dans le [dépôt Github](https://github.com/Redislabs-Solution-Architects/aws-fraud-detection) suivant.

## Résumé

L'incidence de la fraude a atteint des niveaux records. L'[étude PwC](https://www.pwc.com/gx/en/services/forensics/economic-crime-survey.html) a révélé que la fraude a causé des pertes de 42 milliards de dollars en 2020, un chiffre qui continue d'augmenter à mesure que les volumes de transactions augmentent. Cependant, assurer une expérience utilisateur optimale est crucial et ne devrait jamais être compromis dans la lutte contre la fraude.

Les entreprises ont besoin de données en temps réel et de mécanismes de détection plus précis pour combattre ce problème sans engendrer des coûts d'implémentation et de latence supplémentaires. Redis Enterprise est une base de données en mémoire qui offre une solution rentable, en temps réel et à faible latence, étroitement intégrée aux services AWS. Voici un bref aperçu de Redis Enterprise et de la façon dont il peut aider à combattre la fraude :

*   Géré comme un service via AWS Marketplace, Redis Enterprise permet une mise à l'échelle transparente sans dégradation des performances.
*   Les fonctionnalités d'analyse statistique à haute vitesse telles que les filtres Bloom, les séries temporelles et d'autres structures de données dans Redis Enterprise permettent des vérifications efficaces des transactions par rapport aux modèles connus, réduisant les coûts et minimisant le besoin d'analyses forensiques étendues.
*   Au moment de l'inférence, la solution prend en charge la récupération rapide des dernières valeurs de features depuis le feature store en ligne, permettant au moteur ML, comme SageMaker, de fonctionner efficacement.

Avec les services à haut débit et à faible latence de Redis et AWS, la solution répond aux exigences strictes de performance du secteur des services financiers.

Références
----------

*   [Redis Enterprise and AWS Fraud Detection](https://redis.com/wp-content/uploads/2022/05/Redis-Enterprise-and-AWS-Fraud-Detection-Solution-Overview.pdf) : Vue d'ensemble de la solution.
*   [PwC's Global Economic Crime and Fraud Survey 2022](https://www.pwc.com/gx/en/services/forensics/economic-crime-survey.html), Enquêtes PwC.
