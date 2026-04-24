---
date: 2023-09-05
layout: post
lang: fr
title: "Data & Snowflake, Partie 1"
subtitle: Ingestion de données avec Snowflake
thumbnail-img: https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/1ecf154a-5a16-4353-ba85-c2e91a8e65fa
share-img: https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/b80c58c5-749e-4661-930f-fa5133a63a86
tags: [Guide,auto-ingest,data ingestion,dynamic tables,Kafka,Snowflake,Snowpipe,Snowpipe Streaming]
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

Les organisations connaissent une croissance significative de leurs actifs de données et s'appuient sur Snowflake pour en tirer des insights afin de développer leur activité. Ces données comprennent des données structurées, semi-structurées et non structurées arrivant en lots ou en flux.

Comme vous l'avez vu dans les articles précédents, l'ingestion de données est la première étape du cycle de vie des données. Ici, les données sont collectées à partir de diverses sources internes telles que les bases de données, les CRM, les ERP, les systèmes legacy, et de sources externes telles que les enquêtes et les fournisseurs tiers. C'est une étape importante car elle garantit le bon fonctionnement des étapes suivantes dans le cycle de vie des données.

Dans cette étape, les données brutes sont extraites d'une ou plusieurs sources de données, répliquées, puis ingérées dans un emplacement de stockage appelé `stage`. Une fois les données intégrées dans Snowflake, vous pouvez utiliser des fonctionnalités puissantes telles que Snowpark, le partage de données, et bien d'autres pour extraire de la valeur des données et les envoyer vers des outils de reporting, des partenaires et des clients.

Dans cet article, j'illustrerai l'ingestion et l'intégration de données en utilisant les méthodes natives de Snowflake pour répondre aux différents besoins des pipelines de données, de l'ingestion par lots à l'ingestion continue. Ces méthodes incluent, sans s'y limiter, `INSERT`, `COPY`, `Snowpipe`, `Snowpipe Streaming` et les `Dynamic Tables`.

![image](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/4edf0d68-ed96-46f3-8c27-ded686305e4a){: .mx-auto.d-block :} *Les options d'ingestion de Snowflake.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

# Ingestion par lots
Snowflake prend en charge l'ingestion de données dans de multiples formats et méthodes de compression, quel que soit le volume de fichiers. Des fonctionnalités telles que la détection de schema et l'évolution de schema simplifient le chargement direct des données dans des tables structurées sans avoir besoin de fractionner, fusionner ou convertir les fichiers. Les mécanismes natifs pour l'ingestion de données par lots sont `INSERT` et `COPY`.

## Insert

La commande `INSERT` est le mécanisme d'ingestion le plus simple pour importer une petite quantité de données. Elle met à jour une table en insérant une ou plusieurs lignes. Les valeurs insérées dans chaque colonne de la table ou les résultats d'une requête peuvent être explicitement spécifiés. Voici la syntaxe de l'instruction `INSERT` :

```sql
INSERT [ OVERWRITE ] INTO <target_table> [ ( <target_col_name> [ , ... ] ) ]
       {
VALUES ( { <value> | DEFAULT | NULL } [ , ... ] ) [ , ( ... ) ]  |  <query>
       }
```

Vous pouvez insérer plusieurs lignes en utilisant des valeurs explicitement spécifiées dans une liste séparée par des virgules dans la clause `VALUES` :

```sql
INSERT INTO employees
  VALUES
  ('Lysandra','Reeves','1-212-759-3751','New York',10018),
  ('Michael','Arnett','1-650-230-8467','San Francisco',94116);

SELECT * FROM employees;

+------------+-----------+----------------+---------------+-------------+
| FIRST_NAME | LAST_NAME | WORKPHONE      | CITY          | POSTAL_CODE |
|------------+-----------+----------------+---------------+-------------|
| Lysandra   | Reeves    | 1-212-759-3751 | New York      | 10018       |
| Michael    | Arnett    | 1-650-230-8467 | San Francisco | 94116       |
+------------+-----------+----------------+---------------+-------------
```

Vous pouvez également insérer plusieurs lignes en utilisant une requête `select`. Par exemple :

```sql
SELECT * FROM contractors;

+------------------+-----------------+----------------+---------------+----------+
| CONTRACTOR_FIRST | CONTRACTOR_LAST | WORKNUM        | CITY          | ZIP_CODE |
|------------------+-----------------+----------------+---------------+----------|
| Bradley          | Greenbloom      | 1-650-445-0676 | San Francisco | 94110    |
| Cole             | Simpson         | 1-212-285-8904 | New York      | 10001    |
| Laurel           | Slater          | 1-650-633-4495 | San Francisco | 94115    |
+------------------+-----------------+----------------+---------------+----------+

INSERT INTO employees(first_name, last_name, workphone, city,postal_code)
  SELECT
    contractor_first,contractor_last,worknum,NULL,zip_code
  FROM contractors
  WHERE CONTAINS(worknum,'650');

SELECT * FROM employees;

+------------+------------+----------------+---------------+-------------+
| FIRST_NAME | LAST_NAME  | WORKPHONE      | CITY          | POSTAL_CODE |
|------------+------------+----------------+---------------+-------------|
| Lysandra   | Reeves     | 1-212-759-3751 | New York      | 10018       |
| Michael    | Arnett     | 1-650-230-8467 | San Francisco | 94116       |
| Bradley    | Greenbloom | 1-650-445-0676 | NULL          | 94110       |
| Laurel     | Slater     | 1-650-633-4495 | NULL          | 94115       |
+------------+------------+----------------+---------------+-------------+
```

Vous pouvez également insérer plusieurs objets JSON dans une colonne VARIANT d'une table :
```sql
INSERT INTO prospects
  SELECT PARSE_JSON(column1)
  FROM VALUES
  ('{
    "_id": "57a37f7d9e2b478c2d8a608b",
    "name": {
      "first": "Lydia",
      "last": "Williamson"
    },
    "company": "Miralinz",
    "email": "lydia.williamson@miralinz.info",
    "phone": "+1 (914) 486-2525",
    "address": "268 Havens Place, Dunbar, Rhode Island, 7725"
  }')
  , ('{
    "_id": "57a37f7d622a2b1f90698c01",
    "name": {
      "first": "Denise",
      "last": "Holloway"
    },
    "company": "DIGIGEN",
    "email": "denise.holloway@digigen.net",
    "phone": "+1 (979) 587-3021",
    "address": "441 Dover Street, Ada, New Mexico, 5922"
  }');
```

Enfin, si vous utilisez la clause `OVERWRITE` avec une insertion multi-lignes, l'instruction reconstruit et écrase la table avec le contenu de la clause `VALUES`.

Comme vous pouvez le constater, l'instruction `INSERT` est le moyen le plus simple d'ingérer des données dans Snowflake ; cependant, elle présente des limitations de scalabilité et de gestion des erreurs lorsqu'il s'agit de jeux de données dépassant la plage des quelques MiB. Pour les jeux de données plus importants, les ingénieurs données utilisent généralement un outil ETL/ELT pour ingérer les données, ou préférablement utilisent le stockage objet comme étape intermédiaire en complément de `COPY` ou `Snowpipe`.

## COPY

La commande `COPY` permet de charger des lots de données depuis des fichiers stagés vers une table existante. Les fichiers doivent déjà être stagés dans l'un des emplacements suivants :

- Stage interne nommé (ou stage de table/utilisateur). Les fichiers peuvent être stagés à l'aide de la commande `PUT`.
- Stage externe nommé référençant un emplacement externe (Amazon S3, Google Cloud Storage ou Microsoft Azure).
- Emplacement externe (Amazon S3, Google Cloud Storage ou Microsoft Azure).

`COPY` offre un contrôle accru par rapport à `INSERT` mais nécessite que le client gère le calcul (via des paramètres tels que la taille du warehouse et la durée du job). En fait, cette commande utilise un virtual warehouse géré par le client pour lire les données depuis le stockage distant, transformer optionnellement leur structure, et les écrire dans des tables Snowflake natives.

Ces transformations à la volée peuvent inclure :

- Réordonnancement des colonnes
- Omission de colonnes
- Casts
- Troncature de texte

COPY s'intègre bien dans une infrastructure existante où un ou plusieurs warehouses sont gérés en taille et en suspension/reprise pour obtenir le meilleur rapport qualité-prix pour diverses charges de travail, telles que les requêtes `SELECT` ou les transformations de données. Voici la syntaxe d'une commande `COPY` simple :

```sql
COPY INTO [<namespace>.]<table_name>
     FROM { internalStage | externalStage | externalLocation }
[ FILES = ( '<file_name>' [ , '<file_name>' ] [ , ... ] ) ]
[ PATTERN = '<regex_pattern>' ]
[ FILE_FORMAT = ( { FORMAT_NAME = '[<namespace>.]<file_format_name>' |
                    TYPE = { CSV | JSON | AVRO | ORC | PARQUET | XML } [ formatTypeOptions ] } ) ]
[ copyOptions ]
[ VALIDATION_MODE = RETURN_<n>_ROWS | RETURN_ERRORS | RETURN_ALL_ERRORS ]
```

Où :

```sql
internalStage ::=
    @[<namespace>.]<int_stage_name>[/<path>]
  | @[<namespace>.]%<table_name>[/<path>]
  | @~[/<path>]
```

Par exemple, pour charger des fichiers depuis un stage interne nommé dans une table, la commande est :

```sql
COPY INTO mytable
FROM @my_int_stage;
```

En utilisant la commande `CREATE STAGE`, vous pouvez charger des fichiers depuis un stage externe nommé que vous avez déjà créé. Le stage externe nommé référence un emplacement externe (Amazon S3, Google Cloud Storage ou Microsoft Azure). Par exemple :

```sql
COPY INTO mytable
  FROM s3://mybucket/data/files
  CREDENTIALS=(AWS_KEY_ID='$AWS_ACCESS_KEY_ID' AWS_SECRET_KEY='$AWS_SECRET_ACCESS_KEY')
  STORAGE_INTEGRATION = myint
  ENCRYPTION=(MASTER_KEY = 'eSx...')
  FILE_FORMAT = (FORMAT_NAME = my_csv_format);
```

```sql
COPY INTO mytable
  FROM 'gcs://mybucket/data/files'
  STORAGE_INTEGRATION = myint
  FILE_FORMAT = (FORMAT_NAME = my_csv_format);
```

```sql
COPY INTO mytable
  FROM 'azure://myaccount.blob.core.windows.net/mycontainer/data/files'
  CREDENTIALS=(AZURE_SAS_TOKEN='?sv=2016-05-31&ss=b&srt=sco&sp=rwdl&se=2018-06-27T10:05:50Z&st=2017-06-27T02:05:50Z&spr=https,http&sig=bgqQwoXwxzuD2GJfagRg7VOS8hzNr3QLT7rhS8OFRLQ%3D')
  ENCRYPTION=(TYPE='AZURE_CSE' MASTER_KEY = 'kPx...')
  FILE_FORMAT = (FORMAT_NAME = my_csv_format);
```

Pour le chargement de données avec transformation, la syntaxe de la commande est la suivante :

```sql
COPY INTO [<namespace>.]<table_name> [ ( <col_name> [ , <col_name> ... ] ) ]
     FROM ( SELECT [<alias>.]$<file_col_num>[.<element>] [ , [<alias>.]$<file_col_num>[.<element>] ... ]
            FROM { internalStage | externalStage } )
[ FILES = ( '<file_name>' [ , '<file_name>' ] [ , ... ] ) ]
[ PATTERN = '<regex_pattern>' ]
[ FILE_FORMAT = ( { FORMAT_NAME = '[<namespace>.]<file_format_name>' |
                    TYPE = { CSV | JSON | AVRO | ORC | PARQUET | XML } [ formatTypeOptions ] } ) ]
[ copyOptions ]
```

La commande `COPY` repose sur un warehouse géré par le client, aussi certains éléments sont à prendre en compte lors du choix de la taille de warehouse appropriée. L'aspect le plus critique est le degré de parallélisme, car chaque thread peut ingérer un seul fichier simultanément. Le Warehouse XS fournit huit threads, et chaque incrément de taille de warehouse double le nombre de threads disponibles. La conclusion simplifiée est que pour un nombre de fichiers significativement élevé, on peut s'attendre à un parallélisme optimal pour chaque taille de warehouse donnée, réduisant de moitié le temps d'ingestion du grand lot de fichiers à chaque étape de montée en taille. Cependant, cette accélération peut être limitée par des facteurs tels que les délais réseau ou d'E/S dans des scénarios réels. Ces facteurs doivent être pris en compte pour les jobs d'ingestion plus importants et peuvent nécessiter un benchmarking individuel lors de la phase de planification.

![image](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/ee7bf73b-ac4d-480d-883f-0a66ad29e1d6){: .mx-auto.d-block :} *Chargement parallèle de fichiers dans Snowflake.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Il existe un coût fixe par fichier pour Snowpipe en plus des coûts d'utilisation du calcul. En conséquence, pour des fichiers de taille inférieure à quelques MiB, Snowpipe peut être moins rentable (en crédits/TiB) que `COPY`, selon le taux d'arrivée des fichiers, la taille du warehouse et l'utilisation de la couche Cloud Services hors COPY. En parallèle, des fichiers plus grands d'au moins 100 MiB sont généralement plus efficaces.

En général, nous recommandons des tailles de fichiers supérieures à 10 MiB, la plage de 100 à 250 MiB offrant généralement le meilleur rapport qualité-prix. En conséquence, nous recommandons d'agréger les fichiers de données plus petits pour l'ingestion par lots. Nous recommandons également de ne pas dépasser des tailles de fichiers de 5 GiB et de les diviser en fichiers plus petits pour tirer parti de la parallélisation. Avec un fichier plus grand, un enregistrement erroné à la fin peut provoquer l'échec et le redémarrage d'un job d'ingestion selon l'option `ON_ERROR`.

Enfin, l'utilisation du chemin le plus explicite permet à `COPY` de lister et charger les données sans parcourir l'ensemble du bucket, économisant ainsi le calcul et l'utilisation du réseau.

# Ingestion de données continue

Cette option est conçue pour charger de petits volumes de données (c'est-à-dire des micro-batches) et les rendre progressivement disponibles pour l'analyse. Par exemple, Snowpipe charge les données en quelques minutes après que les fichiers ont été ajoutés à un stage et soumis pour ingestion. Cela garantit que les utilisateurs disposent des derniers résultats dès que les données brutes sont disponibles.

## Snowpipe

Snowpipe est un service serverless qui permet de charger des données depuis des fichiers dès qu'ils sont disponibles dans un stage Snowflake (emplacements où les fichiers de données sont stockés pour le chargement/déchargement). Snowpipe peut charger des données depuis des fichiers en micro-batches plutôt qu'en exécutant des instructions `COPY` selon un calendrier. Contrairement à `COPY`, qui est un processus synchrone renvoyant le statut du chargement, l'ingestion de fichiers Snowpipe est asynchrone, et le statut de traitement doit être observé explicitement.

Snowpipe utilise des ressources de calcul fournies par Snowflake (un modèle de calcul serverless). Ces ressources fournies par Snowflake sont automatiquement redimensionnées et mises à l'échelle à la hausse ou à la baisse selon les besoins, et elles sont facturées et détaillées selon une facturation à la seconde. L'ingestion de données est facturée en fonction des charges de travail réelles.

Un pipe est un objet Snowflake nommé de premier ordre qui contient une instruction `COPY` utilisée par Snowpipe. L'instruction `COPY` identifie l'emplacement source des fichiers de données (c'est-à-dire un stage) et une table cible, et prend en charge les mêmes options de transformation que lors du chargement de données en masse. Tous les types de données sont pris en charge, y compris les types de données semi-structurées tels que JSON et Avro.

De plus, les pipelines de données peuvent tirer parti de Snowpipe pour charger en continu des micro-batches de données dans des tables de staging pour la transformation et l'optimisation à l'aide de tâches automatisées et des informations de capture des modifications de données (CDC) dans les streams. Par exemple, Snowpipe en auto-ingestion est l'approche préférée. Cette approche charge en continu de nouvelles données vers la table cible en réagissant aux nouveaux fichiers créés dans le bucket source.

![image](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/ccc7186f-f8bf-470e-b974-6cdb90f46fbb){: .mx-auto.d-block :} *Configuration de Snowpipe en auto-ingestion.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Dans l'exemple ci-dessus, Snowpipe s'appuie sur le système de distribution d'événements spécifique au fournisseur cloud, tel qu'AWS SQS ou SNS, Azure Event Grid ou GCP Pub/Sub. Cette configuration nécessite les privilèges correspondants sur le compte cloud pour délivrer les notifications d'événements depuis le bucket source vers Snowpipe.

L'exemple suivant crée un stage nommé `mystage` dans le schema actif pour la session utilisateur. L'URL de stockage cloud inclut les fichiers du chemin. Le stage référence une intégration de stockage nommée `my_storage_int`. D'abord, nous créons l'intégration de stockage S3 et le stage :

``` sql
CREATE STORAGE INTEGRATION my_storage_int
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::001234567890:role/myrole'
  STORAGE_ALLOWED_LOCATIONS = ('s3://mybucket1/mypath1/', 's3://mybucket2/mypath2/')
  STORAGE_BLOCKED_LOCATIONS = ('s3://mybucket1/mypath1/sensitivedata/', 's3://mybucket2/mypath2/sensitivedata/');
```

``` sql
USE SCHEMA snowpipe_db.public;
```

``` sql
CREATE STAGE mystage
  URL = 's3://mybucket/load/files'
  STORAGE_INTEGRATION = my_storage_int;
```

Ensuite, nous créons un pipe nommé `mypipe` dans le schema actif pour la session utilisateur. Le pipe charge les données depuis les fichiers stagés dans le stage `mystage` vers la table `mytable` et s'abonne au topic SNS ARN qui propage la notification :

``` sql
create pipe snowpipe_db.public.mypipe
  auto_ingest=true
  aws_sns_topic='<sns_topic_arn>'
  as
    copy into snowpipe_db.public.mytable
    from @snowpipe_db.public.mystage
  file_format = (type = 'JSON');
```

Mais dans les cas où un service d'événements ne peut pas être configuré, ou lorsqu'une infrastructure de pipeline de données existante est en place, un Snowpipe déclenché par API REST est une alternative appropriée. C'est actuellement la seule option si un stage interne est utilisé pour stocker les fichiers bruts. Le plus souvent, l'approche API REST est utilisée par les outils ETL/ELT qui ne souhaitent pas imposer la création d'un stockage objet à l'utilisateur final et utilisent à la place un Stage Interne géré par Snowflake.

![image](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/cea02511-e0b3-4b98-8e1a-c115d23f0c64){: .mx-auto.d-block :} *Configuration de Snowpipe déclenché par API.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Comme pour la configuration en auto-ingestion, vous devez créer un stage et une intégration vers le stockage S3. Le pipe est créé sans le topic SNS ARN ni le mot-clé `auto_ingest`.

``` sql
create pipe snowpipe_db.public.mypipe as
    copy into snowpipe_db.public.mytable
    from @snowpipe_db.public.mystage
  file_format = (type = 'JSON');
```

Ensuite, nous créons un utilisateur avec une authentification par paire de clés. Les credentials de l'utilisateur seront utilisées lors des appels aux endpoints API Snowpipe :

``` sql
use role securityadmin;
```

``` sql
create user snowpipeuser 
  login_name = 'snowpipeuser'
  default_role = SYSADMIN
  default_namespace = snowpipe_test.public
  rsa_public_key = '<RSA Public Key value>' ;
```

La connexion via SnowSQL permet de valider que l'utilisateur a été créé avec succès. Utilisez le paramètre `--private-key-path` pour indiquer à SnowSQL d'utiliser l'authentification par paire de clés.

```bash
snowsql -a sedemo.us-east-1-gov.aws -u snowpipeuser --private-key-path rsa_key.p8
```

L'authentification via l'endpoint REST attend un JSON Web Token (JWT) valide. Ces tokens sont généralement valides environ 60 minutes et doivent être régénérés. Si vous souhaitez tester l'API REST en utilisant `Postman` ou `curl`, vous devez en générer un à partir du certificat RSA.

Une fois le JWT généré, l'endpoint REST doit référencer votre compte Snowflake et le nom de pipe entièrement qualifié. L'appel que vous testez est un `POST` vers la méthode `insertFiles`.

```bash
curl -H 'Accept: application/json' -H "Authorization: Bearer ${TOKEN}" -d @path/to/data.csv https://sedemo.us-east-1-gov.aws.snowflakecomputing.com/v1/data/pipes/snowpipe_db.public.mypipe/insertFiles
```

Le responseCode doit être `SUCCESS`. Il est important de se rappeler que Snowpipe n'ingèrera pas le même fichier deux fois. L'appel réussira, mais aucune donnée ne sera ingérée. C'est voulu. Pour retester, utilisez soit un nom de fichier différent, soit supprimez et recréez la table.

L'ingestion devrait déjà être terminée, vous pouvez donc retourner dans l'interface Snowflake et exécuter une instruction select sur la table.

## Snowpipe Streaming

Snowpipe Streaming permet l'ingestion de données en streaming serverless directement dans les tables Snowflake sans nécessiter de fichiers stagés (en contournant le stockage objet cloud) avec une livraison exactement-une-fois et ordonnée. Cette architecture permet des latences plus faibles et des coûts correspondants réduits pour charger tout volume de données, ce qui en fait un outil puissant pour gérer les flux de données quasi temps réel.

L'API est destinée à compléter Snowpipe, non à le remplacer. Utilisez l'API Snowpipe Streaming dans les scénarios de streaming où les données sont transmises sous forme de lignes (par exemple, les topics Apache Kafka) au lieu d'être écrites dans des fichiers. L'API s'intègre dans un workflow d'ingestion, y compris une application Java personnalisée existante qui produit ou reçoit des enregistrements. L'API élimine le besoin de créer des fichiers pour charger des données dans les tables Snowflake et permet le chargement automatique et continu de flux de données dans Snowflake à mesure qu'ils deviennent disponibles. Vous bénéficiez également de nouvelles fonctionnalités, telles que la livraison exactement-une-fois, l'ingestion ordonnée et la gestion des erreurs avec prise en charge de la dead-letter queue (DLQ).

Snowpipe Streaming est également disponible pour le Connecteur Snowflake pour Kafka, qui offre un chemin de mise à niveau facile pour tirer parti de la latence plus faible et des coûts de chargement réduits.

![image](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/b80c58c5-749e-4661-930f-fa5133a63a86){: .mx-auto.d-block :} *API Snowpipe Streaming.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

L'API ingère des lignes via un ou plusieurs channels. Un channel représente une connexion de streaming logique et nommée vers Snowflake pour le chargement de données dans une table. Un seul channel correspond à exactement une table dans Snowflake ; cependant, plusieurs channels peuvent pointer vers la même table. Le SDK client peut ouvrir plusieurs channels vers plusieurs tables ; cependant, le SDK ne peut pas ouvrir des channels entre plusieurs comptes. L'ordre des lignes et leurs tokens d'offset correspondants sont préservés au sein d'un channel mais pas entre les channels pointant vers la même table.

Les channels sont destinés à être de longue durée lorsqu'un client insère activement des données et doivent être réutilisés car les informations de token d'offset sont conservées. Les données à l'intérieur du channel sont automatiquement vidées toutes les 1 seconde par défaut et n'ont pas besoin d'être fermées.

![image](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/ebb8d629-c17a-4002-a732-bd60c9f6525c){: .mx-auto.d-block :} *Channels de streaming.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

### Ingestion de topics Kafka dans des tables Snowflake

Les fichiers sont un dénominateur commun entre les processus qui produisent des données, qu'ils soient sur site ou dans le cloud. La plupart des ingestions se font par lots, où un fichier constitue un lot physique et parfois logique. Aujourd'hui, l'ingestion basée sur des fichiers utilisant COPY ou Snowpipe en auto-ingestion est la principale source de données ingérées dans Snowflake.

Kafka (ou ses équivalents spécifiques au cloud) fournit une infrastructure supplémentaire de collecte et de distribution de données pour écrire et lire des flux d'enregistrements. Si les enregistrements d'événements doivent être distribués vers plusieurs destinations, principalement sous forme de flux, alors une telle organisation a du sens. Le traitement de flux (par opposition au traitement par lots) permet généralement des volumes de données plus faibles à des intervalles plus fréquents pour une latence quasi temps réel.

Dans le cas du Connecteur Snowflake pour Kafka, la même considération de taille de fichier mentionnée précédemment s'applique toujours en raison de son utilisation de Snowpipe pour l'ingestion des données. Cependant, il peut y avoir un compromis entre la latence maximale souhaitée et une taille de fichier plus grande pour l'optimisation des coûts. La taille de fichier appropriée pour votre application peut ne pas correspondre aux recommandations ci-dessus, et c'est acceptable tant que les implications de coût sont mesurées et prises en compte.

De plus, la quantité de mémoire disponible dans un nœud de cluster Kafka Connect peut limiter la taille du buffer et, par conséquent, la taille du fichier. Dans ce cas, la configuration de la valeur du timer (buffer.flush.time) est toujours une bonne idée pour s'assurer que les fichiers plus petits que la taille du buffer sont moins probables.

Deux éléments (Buffer.flush.time et Buffer.flush.size) déterminent le nombre total de fichiers par minute que vous envoyez à Snowflake via le connecteur Kafka. Ainsi, l'ajustement de ces paramètres est très bénéfique en termes de performances. Voici deux exemples :
- Si vous définissez buffer.flush.time à 240 secondes au lieu de 120 secondes sans rien changer d'autre, cela réduira le taux de base de fichiers/minute d'un facteur 2 (atteindre la taille du buffer avant le temps affectera ces calculs).
- Si vous augmentez le Buffer.flush.size à 100 Mo sans rien changer d'autre, le taux de base de fichiers/minute sera réduit de 20 (atteindre la taille maximale du buffer avant le temps maximum du buffer affectera ces calculs).

Pour tester cette configuration localement, vous aurez besoin :
- d'Apache Kafka open-source 2.13-3.1.0 installé localement,
- du Snowflake Kafka Connector 1.9.1.jar (ou version plus récente),
- d'OpenJDK <= 15.0.2,
- d'un utilisateur Snowflake pour le streaming Snowpipe avec une clé SSH définie comme méthode d'authentification.

D'abord, vous devez créer un utilisateur distinct que vous utiliserez pour le Streaming Snowpipe. N'oubliez pas de remplacer <YOURPUBLICKEY> par les détails correspondants. Dans ce cas, vous devez supprimer les lignes de commentaire de début/fin du fichier de clé (ex. : -----BEGIN PUBLIC KEY-----), mais veuillez conserver les caractères de nouvelle ligne.

```sql
create user snowpipe_streaming_user password='',  default_role = accountadmin, rsa_public_key='<YOURPUBLICKEY>';
grant role accountadmin  to user snowpipe_streaming_user;
```

Ici, vous allez créer la base de données que vous utiliserez ultérieurement.

```sql
CREATE OR REPLACE DATABASE hol_streaming;
USE DATABASE hol_streaming;
CREATE OR REPLACE WAREHOUSE hol_streaming_wh WITH WAREHOUSE_SIZE = 'XSMALL' MIN_CLUSTER_COUNT = 1 MAX_CLUSTER_COUNT = 1 AUTO_SUSPEND = 60;
```

Ensuite, ouvrons le terminal et exécutons les commandes suivantes pour télécharger Kafka et le connecteur Kafka Snowflake :

``` bash
mkdir HOL_kafka
cd HOL_kafka

curl https://archive.apache.org/dist/kafka/3.3.1/kafka_2.13-3.3.1.tgz --output kafka_2.13-3.3.1.tgz
tar -xzf kafka_2.13-3.3.1.tgz

cd kafka_2.13-3.3.1/libs
curl https://repo1.maven.org/maven2/com/snowflake/snowflake-kafka-connector/1.9.1/snowflake-kafka-connector-1.9.1.jar --output snowflake-kafka-connector-1.9.1.jar
```

Créez le fichier de configuration `config/SF_connect.properties` avec les paramètres suivants. N'oubliez pas de remplacer `<YOURACCOUNT>` et `<YOURPRIVATEKEY>` par les détails correspondants. Veuillez également noter que lors de l'ajout d'une clé privée, vous devez supprimer tous les caractères de nouvelle ligne ainsi que les commentaires de début et de fin (ex. : -----BEGIN PRIVATE KEY-----) :

```properties
name=snowpipe_streaming_ingest
connector.class=com.snowflake.kafka.connector.SnowflakeSinkConnector
tasks.max=1
topics=customer_data_topic
snowflake.topic2table.map=customer_data_topic:customer_data_stream_stg
buffer.count.records=1
buffer.flush.time=10
buffer.size.bytes=20000000
snowflake.url.name=<YOURACCOUNT>.snowflakecomputing.com:443
snowflake.user.name=SNOWPIPE_STREAMING_USER
snowflake.private.key=<YOURPRIVATEKEY>
snowflake.database.name=HOL_STREAMING
snowflake.schema.name=PUBLIC
snowflake.role.name=ACCOUNTADMIN
snowflake.ingestion.method=SNOWPIPE_STREAMING
key.converter=org.apache.kafka.connect.json.JsonConverter
value.converter=org.apache.kafka.connect.json.JsonConverter
key.converter.schemas.enable=false
value.converter.schemas.enable=false
```

Maintenant que c'est réglé, lançons tout ensemble. Veuillez noter que vous pourriez obtenir des erreurs pour cette étape si vous utilisez JDK>=v15. Et vous pourriez avoir besoin de plusieurs sessions de terminal séparées :

Session 1 :
```bash
bin/zookeeper-server-start.sh config/zookeeper.properties
```
Session 2 :
```bash
bin/kafka-server-start.sh config/server.properties
```
Session 3 :
```bash
bin/connect-standalone.sh ./config/connect-standalone.properties ./config/SF_connect.properties
```

Maintenant, ouvrez une autre session terminal (Session 4) et exécutez le kafka-console-producer. Cet utilitaire vous permet de saisir manuellement des données dans le topic.

```bash
bin/kafka-console-producer.sh --topic customer_data_topic --bootstrap-server localhost:9092
```

Retournons dans Snowsight et exécutons la requête suivante pour générer des exemples de données client au format JSON :

```sql
SELECT object_construct(*)
  FROM snowflake_sample_data.tpch_sf10.customer limit 200;
```

Comme vous pouvez le voir, Snowpipe Streaming est une nouvelle capacité fantastique qui peut réduire significativement la latence d'intégration et améliorer l'efficacité du pipeline. Elle ouvre également de nouvelles opportunités pour votre entreprise, fournissant des insights quasi temps réel et des rapports opérationnels, entre autres avantages.

![image](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/45297412-ed21-4725-b641-3a39f722e6f0)

### Snowpipe Streaming et Tables Dynamiques pour l'ingestion en temps réel

Les [tables dynamiques](https://docs.snowflake.com/en/user-guide/dynamic-tables-about) sont les blocs de construction des pipelines de transformation de données déclaratifs. Elles simplifient considérablement l'ingénierie des données dans Snowflake et offrent une façon fiable, rentable et automatisée de transformer vos données pour la consommation. Au lieu de définir les étapes de transformation des données comme une série de tâches et de devoir surveiller les dépendances et la planification, vous pouvez déterminer l'état final de la transformation à l'aide de tables dynamiques et laisser Snowflake gérer la complexité du pipeline.

![](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/0ce85521-7009-49bc-937e-25446bfd6960){: .mx-auto.d-block :} *Tables dynamiques.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"} 

Ci-après, nous vous guiderons à travers un scénario d'utilisation du Snowpipe Streaming de Snowflake pour ingérer un flux simulé. Ensuite, nous utiliserons les tables dynamiques pour transformer et préparer les payloads JSON bruts ingérés en jeux de données prêts pour l'analyse. Ce sont deux des puissantes innovations en ingénierie des données de Snowflake pour l'ingestion et la transformation.

Le flux de données simulé sera constitué d'ordres à cours limité sur actions, avec des ordres nouveaux, modifiés et annulés représentés sous forme de journaux de transactions SGBD capturés à partir d'événements INSERT, UPDATE et DELETE de base de données. Ces événements seront transmis sous forme de payloads JSON et atterriront dans une table Snowflake avec une colonne de données de type variant. C'est le même type d'ingestion de flux généralement créé par les agents de Change-Data-Capture (CDC) qui analysent les journaux de transactions d'une base de données ou les mécanismes de notification d'événements des applications modernes. Cependant, cela pourrait simuler tout type de flux dans n'importe quel secteur. Ce cas d'usage d'ingestion en streaming a été modélisé de manière similaire à un cas précédemment traité avec le Connecteur Kafka de Snowflake. Cependant, aucun Kafka n'est nécessaire pour ce cas d'usage, car un client Snowpipe Streaming peut permettre de remplacer l'infrastructure middleware Kafka, économisant ainsi des coûts et de la complexité. Une fois les données arrivées, les tables dynamiques sont des objets Snowflake spécialement conçus pour l'ingénierie des données afin de transformer les données brutes en données prêtes pour les insights.

![](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/7da648bd-b99b-4834-a9c9-f3947e8d1bc7){: .mx-auto.d-block :} *API Snowpipe Streaming et Tables Dynamiques pour la Capture des Modifications de Données.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"} 

Notre "base de données" source contient des échanges d'actions pour le Dow Jones Industrials, [30 actions américaines](https://www.nyse.com/quote/index/DJI). En moyenne, 200 à 400 millions d'échanges d'actions sont exécutés par jour. Notre agent capturera les événements de transactions d'ordres à cours limité pour ces 30 actions, qui sont des nouveaux ordres, des mises à jour d'ordres (modifications de quantité ou du prix limite), et des ordres annulés. Pour cette simulation, il y a trois nouveaux ordres pour chaque deux mises à jour et une annulation. Le flux de données de ce scénario reproduira d'abord une charge de travail intense d'une session d'ouverture de marché et un flux continu plus modeste. Les consommateurs de données Snowflake souhaitent voir trois perspectives sur les ordres à cours limité : la liste "actuelle" des ordres qui filtre les ordres périmés et annulés, une table historique montrant chaque événement sur la source (dans un format de dimension à variation lente traditionnel), et les ordres actuels résumés par symbole boursier et par position longue ou courte. La latence doit être minimisée, 1 à 2 minutes serait idéal pour le processus de bout en bout.

D'autres capacités Snowflake peuvent enrichir davantage vos données entrantes en utilisant les données du Snowflake Data Marketplace, entraîner et déployer des modèles d'apprentissage automatique, effectuer la détection de fraudes et d'autres cas d'usage. Nous couvrirons ceux-ci dans de futurs articles.

D'abord, vous devez extraire ce [fichier](https://sfquickstarts.s3.us-west-1.amazonaws.com/data_engineering_CDC_snowpipestreaming_dynamictables/CDCSimulatorApp.zip), créant un répertoire `CDCSimulatorApp` et de nombreux fichiers à l'intérieur.

Depuis votre terminal, naviguez vers votre répertoire de travail, puis vers le répertoire extrait (`CDCSimulatorApp`), et exécutez ces deux commandes :

```bash
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
```

Dans Snowflake, créez un rôle dédié pour votre application de streaming. Pour cela, exécutez ces commandes en utilisant la clé publique générée à l'étape précédente (le contenu de `rsa_key.pub`) :

```sql
create role if not exists VHOL_CDC_AGENT;
create or replace user vhol_streaming1 COMMENT="Creating for VHOL";
alter user vhol_streaming1 set rsa_public_key='<Paste Your Public Key Here>';
```

Vous devrez modifier le fichier snowflake.properties pour qu'il corresponde au nom de votre compte Snowflake (deux endroits) :

```properties
user=vhol_streaming1
role=VHOL_CDC_AGENT
account=<MY_SNOWFLAKE_ACCOUNT>
warehouse=VHOL_CDC_WH
private_key_file=rsa_key.p8
host=<ACCOUNT_IDENTIFIER>.snowflakecomputing.com
database=VHOL_ENG_CDC
schema=ENG
table=CDC_STREAMING_TABLE
channel_name=channel_1
AES_KEY=O90hS0k9qHdsMDkPe46ZcQ==
TOKEN_KEY=11
DEBUG=FALSE
SHOW_KEYS=TRUE
NUM_ROWS=1000000
```

Créez de nouveaux rôles pour ce tutoriel et accordez les permissions :

```sql
use role ACCOUNTADMIN;
set myname = current_user();
create role if not exists VHOL;
grant role VHOL to user identifier($myname);
grant role VHOL_CDC_AGENT to user vhol_streaming1;
```

Créez un virtual warehouse de calcul dédié (taille XS), puis créez la base de données utilisée tout au long de ce tutoriel :

```sql
create or replace warehouse VHOL_CDC_WH WAREHOUSE_SIZE = XSMALL, AUTO_SUSPEND = 5, AUTO_RESUME= TRUE;
grant all privileges on warehouse VHOL_CDC_WH to role VHOL;
```

```sql
create database VHOL_ENG_CDC;
use database VHOL_ENG_CDC;
grant ownership on schema PUBLIC to role VHOL;
revoke all privileges on database VHOL_ENG_CDC from role ACCOUNTADMIN;
grant ownership on database VHOL_ENG_CDC to role VHOL;
```

```sql
use role VHOL;
use database VHOL_ENG_CDC;
create schema ENG;
use VHOL_ENG_CDC.ENG;
use warehouse VHOL_CDC_WH;
grant usage on database VHOL_ENG_CDC to role VHOL_CDC_AGENT;
grant usage on schema ENG to role VHOL_CDC_AGENT;
grant usage on database VHOL_ENG_CDC to role PUBLIC;
grant usage on schema PUBLIC to role PUBLIC;
```

Créez une table de staging/atterrissage où toutes les données entrantes arriveront initialement. Chaque ligne contiendra une transaction, mais le JSON sera stocké en tant que type de données `VARIANT` dans Snowflake.

```sql
create or replace table ENG.CDC_STREAMING_TABLE (RECORD_CONTENT variant);
grant insert on table ENG.CDC_STREAMING_TABLE to role VHOL_CDC_AGENT;
```

Vous pouvez exécuter `Test.sh` pour vous assurer que tout est correctement configuré. Vous êtes maintenant prêt à streamer des données dans Snowflake !

Pour exécuter le simulateur de streaming, exécutez `Run_MAX.sh`.

```shell
./Run_MAX.sh
```

Ce qui devrait prendre 10 à 20 secondes et retourner :

![image](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/5b50cd73-2a8c-4d5b-8f66-48e66725801a)

Ensuite, vous avez 1 million d'enregistrements dans la table `CDC_STREAMING_TABLE`.

![image](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/f4218a7f-ea55-4857-a54d-25a6e170c5eb)

Chaque enregistrement est un payload JSON reçu via l'API d'ingestion Snowpipe Streaming et stocké dans une table Snowflake sous forme de lignes et de champs de données variant.

Maintenant, vous pouvez créer une table dynamique plus élaborée alimentée depuis la table d'atterrissage qui reflète l'"ÉTAT ACTUEL" de la table source. Dans ce pattern, pour chaque table source, vous créez une table dynamique :

```sql
CREATE OR REPLACE DYNAMIC TABLE ENG.LIMIT_ORDERS_CURRENT_DT
LAG = '1 minute'
WAREHOUSE = 'VHOL_CDC_WH'
AS
SELECT * EXCLUDE (score,action) from (  
  SELECT
    RECORD_CONTENT:transaction:primaryKey_tokenized::varchar as orderid_tokenized,
    RECORD_CONTENT:transaction:record_after:orderid_encrypted::varchar as orderid_encrypted,
    TO_TIMESTAMP_NTZ(RECORD_CONTENT:transaction:committed_at::number/1000) as lastUpdated,
    RECORD_CONTENT:transaction:action::varchar as action,
    RECORD_CONTENT:transaction:record_after:client::varchar as client,
    RECORD_CONTENT:transaction:record_after:ticker::varchar as ticker,
    RECORD_CONTENT:transaction:record_after:LongOrShort::varchar as position,
    RECORD_CONTENT:transaction:record_after:Price::number(38,3) as price,
    RECORD_CONTENT:transaction:record_after:Quantity::number(38,3) as quantity,
    RANK() OVER (
        partition by orderid_tokenized order by RECORD_CONTENT:transaction:committed_at::number desc) as score
  FROM ENG.CDC_STREAMING_TABLE 
    WHERE 
        RECORD_CONTENT:transaction:schema::varchar='PROD' AND RECORD_CONTENT:transaction:table::varchar='LIMIT_ORDERS'
) 
WHERE score = 1 and action != 'DELETE';
```

{: .box-warning}
**Avertissement :** Si vous exécutez ceci immédiatement, un avertissement s'affichera indiquant que la table n'est pas encore prête. Vous devez attendre un peu la période de rafraîchissement et que la table dynamique soit construite.

Attendez la période de lag (1 minute), puis vérifiez la table :

```sql
SELECT count(*) FROM LIMIT_ORDERS_CURRENT_DT;
```

Travaillons avec des données dynamiques à partir de maintenant et retournons au simulateur de flux pour fournir un flux continu. Exécutez `Run_Slooow.sh`, et l'application streamra 10 enregistrements/seconde jusqu'à ce que vous arrêtiez l'application (en utilisant Ctrl-C). Si vous voulez plus de volume, exécutez `Run_Sloow.sh` pour 100/seconde ou `Run_Slow.sh` pour un débit de 1000/seconde. Notez que le simulateur est conçu pour n'exécuter qu'un seul de ces scripts simultanément (le nom du channel est configuré dans le fichier de propriétés).

Le streaming de la première table est parfaitement réalisé, mais vous pouvez également analyser comment les ordres/enregistrements ont changé et conserver un enregistrement historique, par exemple dans une Dimension à Variation Lente (SCD). Dans ce cas, vous pouvez le faire en ajoutant des champs supplémentaires à chaque enregistrement pour les suivre et les regrouper :

```sql
CREATE OR REPLACE DYNAMIC TABLE ENG.LIMIT_ORDERS_SCD_DT
LAG = '1 minute'
WAREHOUSE = 'VHOL_CDC_WH'
AS
SELECT * EXCLUDE score from ( SELECT *,
  CASE when score=1 then true else false end as Is_Latest,
  LAST_VALUE(score) OVER (
            partition by orderid_tokenized order by valid_from desc)+1-score as version
  FROM (  
      SELECT
        RECORD_CONTENT:transaction:primaryKey_tokenized::varchar as orderid_tokenized,
        --IFNULL(RECORD_CONTENT:transaction:record_after:orderid_encrypted::varchar,RECORD_CONTENT:transaction:record_before:orderid_encrypted::varchar) as orderid_encrypted,
        RECORD_CONTENT:transaction:action::varchar as action,
        IFNULL(RECORD_CONTENT:transaction:record_after:client::varchar,RECORD_CONTENT:transaction:record_before:client::varchar) as client,
        IFNULL(RECORD_CONTENT:transaction:record_after:ticker::varchar,RECORD_CONTENT:transaction:record_before:ticker::varchar) as ticker,
        IFNULL(RECORD_CONTENT:transaction:record_after:LongOrShort::varchar,RECORD_CONTENT:transaction:record_before:LongOrShort::varchar) as position,
        RECORD_CONTENT:transaction:record_after:Price::number(38,3) as price,
        RECORD_CONTENT:transaction:record_after:Quantity::number(38,3) as quantity,
        RANK() OVER (
            partition by orderid_tokenized order by RECORD_CONTENT:transaction:committed_at::number desc) as score,
        TO_TIMESTAMP_NTZ(RECORD_CONTENT:transaction:committed_at::number/1000) as valid_from,
        TO_TIMESTAMP_NTZ(LAG(RECORD_CONTENT:transaction:committed_at::number/1000,1,null) over 
                         (partition by orderid_tokenized order by RECORD_CONTENT:transaction:committed_at::number desc)) as valid_to
      FROM ENG.CDC_STREAMING_TABLE
      WHERE 
            RECORD_CONTENT:transaction:schema::varchar='PROD' AND RECORD_CONTENT:transaction:table::varchar='LIMIT_ORDERS'
    ))
;
```

Attendez la période de lag (~1 minute), puis revérifiez la table. Vous devriez maintenant voir plus d'un million d'enregistrements initiaux chargés.

Ces données sont maintenant prêtes pour un usage public ! Pour créer l'accès aux utilisateurs consommateurs, utilisons des vues pour permettre l'accès (note : la syntaxe des chemins JSON n'est pas visible ni nécessaire depuis la table d'atterrissage). Pour notre table "Vue Actuelle" :

``` sql
create or replace view PUBLIC.CURRENT_LIMIT_ORDERS_VW
  as select orderid_tokenized, lastUpdated, client, ticker, position, quantity, price
  FROM ENG.LIMIT_ORDERS_CURRENT_DT order by orderid_tokenized;
```

```sql
grant select on view PUBLIC.CURRENT_LIMIT_ORDERS_VW to role PUBLIC;
```

Pas besoin d'attendre... Vos consommateurs peuvent maintenant visualiser et analyser les ordres à cours limité en temps réel !

```sql
select * from PUBLIC.CURRENT_LIMIT_ORDERS_VW limit 1000;
```

# Résumé

Snowflake offre divers blocs de construction pour travailler à la fois avec des données en lot et en streaming. Il n'existe pas d'approche universelle, il est donc important de comprendre les différences pour répondre efficacement aux exigences. Dans cet article, nous avons exploré les options d'ingestion, les meilleures pratiques et comment vous pouvez implémenter chacune concrètement.

![image](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/75118283-457e-4440-98b7-5707a6845797)

Quelle que soit la méthode d'ingestion choisie, la question épineuse qui reste légitime est celle du temps et du coût d'ingestion. Les deux dépendent de divers facteurs, notamment :

- La taille du fichier : le temps d'ingestion de base est relatif au contenu, donc les coûts tendent à être proportionnels au nombre d'enregistrements et à la taille du fichier, mais sans corrélation exacte.
- La quantité de pré-traitement requise : Certains jobs d'ingestion invoquent des UDFs complexes qui prennent un temps significatif par ligne et peuvent parfois même manquer de mémoire si la taille des données n'est pas correctement anticipée.
- Le format de fichier, la compression, les structures imbriquées, etc., ont un impact sur l'efficacité avec laquelle nous pouvons décompresser et charger les données. Un fichier non compressé avec un grand nombre de colonnes peut prendre le même temps qu'un fichier compressé avec un petit nombre de colonnes mais comportant des structures de données fortement imbriquées.
  
Par conséquent, il est impossible de répondre à la question du temps et du coût sans le mesurer pour chaque cas spécifique.

Enfin, comme mentionné dans les articles précédents, il existe de nombreuses approches pour l'ingestion de données, mais la meilleure pratique consiste à réduire la complexité tout en atteignant vos exigences métier. L'ingestion par lots et l'ingestion en streaming peuvent fonctionner ensemble pour fournir la solution la plus simple et la plus rentable pour vos pipelines de données. L'ingestion en streaming n'est pas destinée à remplacer l'ingestion basée sur des fichiers, mais plutôt à la compléter pour les scénarios de chargement de données qui correspondent mieux à vos besoins métier.

# Références
- [Best Practices for Data Ingestion with Snowflake: Part 1](https://www.snowflake.com/blog/best-practices-for-data-ingestion), Xin Huang and Anton Huck, Snowflake Blog. 
- [Best Practices for Data Ingestion with Snowflake: Part 2](https://www.snowflake.com/blog/best-practices-for-data-ingestion-part-2), Xin Huang, Snowflake Blog.
- [Best Practices for Data Ingestion with Snowflake: Part 3](https://www.snowflake.com/blog/data-ingestion-best-practices-part-three), Xin Huang and Revi Cheng, Snowflake Blog.
- [Best practices to optimize data ingestion spend in Snowflake](https://medium.com/snowflake/data-ingestion-into-snowflake-and-best-practices-to-optimize-associated-spend-82a0325fff94), Samartha Chandrashekar, Medium.
- [Best Practices of Different Data Ingestion Options in Snowflake](https://snowflakewiki.medium.com/best-practices-of-different-data-ingestion-options-in-snowflake-7a9f452b5fb8), Snowflake Wiki, Medium.
- [Invoking the Snowpipe REST API from Postman](https://medium.com/snowflake/invoking-the-snowpipe-rest-api-from-postman-141070a55337), Paul Horan, Medium.
- [Streaming Data Integration with Snowflake](https://quickstarts.snowflake.com/guide/data_engineering_streaming_integration), Snowflake Labs.
- [Snowpipe Streaming and Dynamic Tables for Real-Time Ingestion](https://quickstarts.snowflake.com/guide/CDC_SnowpipeStreaming_DynamicTables), Snowflake Labs.
- [Snowpipe Streaming](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-streaming-overview), Snowflake Documentation. 
- [Automating Snowpipe for Amazon S3](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-auto-s3), Snowflake Documentation. 
