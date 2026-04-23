---
date: 2023-06-09
layout: post
lang: fr
title: "Data & Redis, Partie 8"
subtitle: Découvrir Redis pour la Recherche par Similarité Vectorielle
thumbnail-img: https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEhGgH1gaxs8Mj60SkhlTyPDnFW5UzQaMn9GXWLbV2VoVe62C9azRjXYaEqx8AOdJCQYQIewqxJkDrSgX6BqqGEJr8iHgziuHPwA0wwurxSpvnlQ-lJNi0haib0KHz_FoBhJGri4kRHgv6hPNhSXiw2sqN21lXDlCClmwfW9aR3BttNTlavTZhJpXpGS5vU
share-img: https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEgKgxMltMyijfUL8HoJmjfpCrvLlmymW6U4FSdtHobnGARzJsxURry7UsXNsl4DGIVA5IIwW0Lz8Lx3qOxmc-wfGFsIndteJyjsOAkDksi4iMuALAg7KzR6SBPQPA-h-5ZxIqTz_RZkjNT_SOsCVH3XvwaXJFW64xcOssRGVY-Iq6cLBCz1WmpQQiIPnZw
tags: [ChatGPT,Redis,RediSearch,similarity search,transformers,vector database]
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

Dans le monde actuel axé sur les données, l'information est générée et consommée à un rythme sans précédent. À chaque clic, geste et transaction, de massives quantités de données sont collectées, attendant d'être exploitées pour obtenir des insights, prendre des décisions et innover. Aujourd'hui, plus de 80% des données générées par les organisations sont non structurées, et la quantité de ce type de données devrait croître dans les décennies à venir. Les données non structurées sont à haute dimensionnalité et bruyantes, ce qui les rend plus difficiles à analyser et à interpréter pour les bases de données traditionnelles avec les méthodes conventionnelles.

Bienvenue dans le monde des Bases de Données Vectorielles  -  une technologie révolutionnaire qui transforme la façon dont nous stockons, interrogeons et analysons les données. Ces bases de données ne sont pas seulement une évolution de leurs prédécesseurs ; elles représentent un bond quantique dans le domaine de la gestion des données. Dans cet article, nous nous lançons dans un voyage dans le domaine des bases de données vectorielles, explorant leurs principes fondamentaux, leurs applications et comment Redis Enterprise représente une addition passionnante à ce domaine.

Que vous soyez un passionné de données, un dirigeant d'entreprise cherchant un avantage compétitif, ou un développeur curieux à propos de la prochaine frontière dans le stockage et la récupération de données, cet article est votre porte d'entrée pour comprendre la puissance et le potentiel de Redis comme base de données vectorielle.

## 1. Les embeddings vectoriels

Les vecteurs sont des représentations mathématiques de points de données où chaque dimension vectorielle (embeddings) correspond à une feature ou un attribut spécifique des données. Par exemple, une image de produit peut être représentée comme un vecteur où chaque élément représente la caractéristique de ce produit (couleur, forme, taille...). De même, une description de produit peut être transformée en un vecteur où chaque élément représente la fréquence ou la présence d'un mot ou terme spécifique.

Les vecteurs sont un moyen efficace de représenter des données brutes, en particulier les données non structurées (par exemple, les langages naturels, les images, l'audio...), qui peuvent être à haute dimensionnalité et clairsemées. Les embeddings vectoriels fournissent une représentation plus efficace et compacte de ces données, facilitant leur traitement et leur analyse.

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEgQ7mCfTqlGfPJPgcQO57u1k2oViOk0P77xV89rO3btNhP0bVRbT617ZhWHzQT5ELjKV_gjArWLrVL3tXxyu2qmnl_bHlg1I9oTxeOHsnPoBWSXy301-6PvqaKGAOn0DFeTEwJaB1nnanm9GvXhFIB9ZlRYDyt_1WguNXep10j2NYduLZBvChei8kufqso){: .mx-auto.d-block :} *Embeddings vectoriels.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Les embeddings vectoriels extraient automatiquement les features pertinentes des données, réduisant ainsi le besoin d'ingénierie manuelle des features. Ils permettent la mesure de la similarité ou de la dissimilarité entre les points de données. Dans les systèmes de recommandation, par exemple, les embeddings utilisateur-article aident à identifier des utilisateurs ou des produits similaires, améliorant ainsi les recommandations.

Par exemple, dans le domaine du Traitement du Langage Naturel (**NLP**), les embeddings vectoriels capturent les relations sémantiques entre les points de données. Les mots ou les phrases ayant des significations similaires sont représentés comme des vecteurs qui sont proches les uns des autres dans l'espace d'embedding. Cela permet aux modèles de comprendre et de raisonner sur la signification des mots et du texte.

## 2. Redis comme base de données vectorielle

Une base de données vectorielle est un type de base de données qui stocke des données non structurées sous forme d'embeddings vectoriels. Les algorithmes de Machine Learning sont ce qui permet cette transformation de données non structurées en représentations numériques (vecteurs) qui capturent le sens et le contexte, bénéficiant des avancées dans le traitement du langage naturel et la vision par ordinateur.

La fonctionnalité clé d'une base de données vectorielle est la Recherche par Similarité Vectorielle (VSS). C'est le processus de recherche des points de données similaires à un vecteur de requête donné dans une base de données vectorielle.

En tant que datastore polyvalent, Redis offre les fondations techniques pour stocker, indexer et interroger les embeddings vectoriels. Il permet aux développeurs de stocker des vecteurs aussi facilement que des Hashes ou des documents JSON. Ensuite, la capacité de Recherche par Similarité Vectorielle (VSS) est intégrée comme une nouvelle fonctionnalité du module RediSearch. Elle fournit des capacités avancées d'indexation et de recherche nécessaires pour effectuer des recherches à faible latence dans de grands espaces vectoriels, allant généralement de dizaines de milliers à des centaines de millions de vecteurs distribués sur plusieurs machines.

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEgKgxMltMyijfUL8HoJmjfpCrvLlmymW6U4FSdtHobnGARzJsxURry7UsXNsl4DGIVA5IIwW0Lz8Lx3qOxmc-wfGFsIndteJyjsOAkDksi4iMuALAg7KzR6SBPQPA-h-5ZxIqTz_RZkjNT_SOsCVH3XvwaXJFW64xcOssRGVY-Iq6cLBCz1WmpQQiIPnZw){: .mx-auto.d-block :} *Redis comme base de données vectorielle.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

## 3. RediSearch et la Recherche par Similarité Vectorielle

La Recherche par Similarité Vectorielle se concentre sur la détermination de la similarité ou de la dissimilarité entre deux vecteurs. Une fois que vous avez créé vos embeddings et les avez stockés dans Redis, vous devez créer une structure de données d'index pour permettre une recherche intelligente par similarité qui équilibre la vitesse et la qualité de recherche. Redis prend en charge deux types d'indexation vectorielle :

*   **FLAT** : une approche par force brute utilisant la recherche K-Nearest Neighbor (KNN) à travers tous les vecteurs possibles. Cette indexation est simple et efficace pour les petits jeux de données ou les cas où l'interprétabilité est importante ;
*   **Hierarchical Navigable Small Worlds (HNSW)** : une recherche approximative (ANN) qui donne des résultats plus rapides avec une précision moindre. C'est plus adapté pour les tâches complexes nécessitant la capture de modèles et de relations complexes, en particulier avec de grands jeux de données.

Le choix entre Flat et HNSW dépend uniquement de votre utilisation, de vos caractéristiques de données et de vos exigences. Les index ne doivent être créés qu'une seule fois et seront automatiquement ré-indexés à mesure que de nouveaux hashes sont stockés dans Redis. Les deux méthodes d'indexation ont les mêmes paramètres obligatoires : Type, Dimension et Métrique de Distance.

### A. Stockage des vecteurs

Ci-dessous, un exemple de similarité sémantique est montré qui décrit les embeddings vectoriels créés avec la bibliothèque **sentence_transformers** (de [HuggingFace](https://huggingface.co/sentence-transformers)).

Prenons les phrases suivantes :
* `That is a happy girl`
* `That is a very happy person`
* `I love dogs`

Chacune de ces phrases peut être transformée en un embedding vectoriel. Ci-dessous, une représentation simplifiée met en évidence la position de ces exemples de phrases dans un espace vectoriel à 2 dimensions l'une par rapport à l'autre. Ceci est utile pour évaluer visuellement comment nos embeddings représentent efficacement la signification sémantique du texte.

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEhgQ1qOn2DeB_pt5jeqieetRym_3S8HsEmvUni6bkzPXcwtn5uFlInciuiuSJQNpkSTZZ1BhWXWiekEDBKoFx9kwzVV5FogwvmfKVlhT-rEX0JIumZ7a7Ho-2Ph21BAm5HUGyjvWLP7-QaRiUlg3BWJM3IKJm5CrrAYu2rBhjtJzwkuHrox02M3s8ooR6g){: .mx-auto.d-block :} *Les phrases sont présentées comme des vecteurs.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Les packages comme **sentence_transformers**, également de HuggingFace, fournissent des modèles faciles à utiliser pour des tâches comme la recherche par similarité sémantique, la recherche visuelle et bien d'autres. Pour créer des embeddings avec ces modèles, seulement quelques lignes de Python sont nécessaires :

{% highlight python linenos %}
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

sentences = [
  "That is a happy girl",
  "That is a very happy person",
  "I love dogs"
]
embeddings = model.encode(sentences)
{% endhighlight %}

Ensuite, stockons ces embeddings vectoriels dans Redis :

{% highlight python linenos %}
import redis 

# Redis connection params
redis_url = "redis://redis-12000.cluster.dev-vss.demo.redislabs.com:12000"

# Create Redis client
redis_client = redis.from_url(redis_url)

redis_client.hset('sentence:1', mapping={"text": "That is a happy girl", "embedding": convert_to_bytes(embeddings[0])})
redis_client.hset('sentence:2', mapping={"text": "That is a very happy person", "embedding": convert_to_bytes(embeddings[1])})
redis_client.hset('sentence:3', mapping={"text": "I love dogs", "embedding": convert_to_bytes(embeddings[3])})
{% endhighlight %}

### B. Indexation des vecteurs

Nous devons créer un index sur ces vecteurs stockés pour permettre la recherche, l'interrogation et la récupération. Pour cela, vous devez choisir la métrique de distance pertinente pour votre application.

Les métriques de distance fournissent un moyen fiable et mesurable de calculer la similarité ou la dissimilarité de deux vecteurs. Il existe de nombreuses métriques de distance que vous pouvez utiliser (figure ci-dessous), mais actuellement, seules les métriques [Euclidienne](https://en.wikipedia.org/wiki/Euclidean_distance) (L2), [Produit Intérieur](https://en.wikipedia.org/wiki/Inner_product_space) (IP) et [Similarité Cosinus](https://en.wikipedia.org/wiki/Cosine_similarity) sont disponibles dans Redis.

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEheKTicWPBFMSoK53LHeSvikn9ZOklHrGfUYk0DXjDJXOrCaUd4Oeb_Nuam_xrKlTj8JvNgk2nQn9FYeKEYVE9aylJKDmNLUjiKz0uht6jOVC_HhI-qqFKGHhBDmOVddPrZsqCELjFe8H2f3vAbe1DRF5KGega_Gr4Y-DNOjAVHF2Wahsmu1BMA0wDl){: .mx-auto.d-block :} *Métriques de Distance.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Voici un exemple de création d'un index avec `redis-py` après le chargement des vecteurs dans Redis.

{% highlight python linenos %}
from redis import Redis
from redis.commands.search.field import VectorField, TagField

# Function to create a flat (brute-force) search index with Redis/RediSearch
# Could also be a HNSW index
def create_flat_index(redis_conn: Redis, number_of_vectors: int, distance_metric: str='COSINE'):
		
	text_field = VectorField("sentence_vector",
	                          "FLAT", {"TYPE": "FLOAT32",
	                                   "DIM": 512,
                                 	   "DISTANCE_METRIC": distance_metric,
                                 	   "INITIAL_CAP": number_of_vectors,
	                                   "BLOCK_SIZE": number_of_vectors})
	redis_conn.ft().create_index([text_field])
{% endhighlight %}

Les index ne doivent être créés qu'une seule fois et seront automatiquement ré-indexés à mesure que de nouveaux hashes sont stockés dans Redis. Après le chargement des vecteurs dans Redis et la création de l'index, des requêtes peuvent être formulées et exécutées pour toutes sortes de tâches de recherche basées sur la similarité.

Toutes les fonctionnalités RediSearch existantes, comme la recherche par texte, étiquette et géographique, peuvent fonctionner conjointement avec la capacité VSS. C'est ce qu'on appelle les _requêtes hybrides_. Avec les requêtes hybrides, les fonctionnalités de recherche traditionnelles peuvent être utilisées comme pré-filtre pour la recherche vectorielle, ce qui peut aider à limiter l'espace de recherche.

### C. Interrogation des vecteurs

Supposons que nous voulions comparer les trois phrases ci-dessus avec une nouvelle : `That is a happy boy`.

Premièrement, nous créons l'embedding vectoriel pour la phrase de requête.

{% highlight python linenos %}
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# create the vector embedding for the query
query_embedding = model.encode("That is a happy boy")
{% endhighlight %}

Une fois les vecteurs chargés dans Redis et l'index créé, des requêtes peuvent être formulées et exécutées pour toutes sortes de tâches de recherche basées sur la similarité.

Voici un exemple de requête avec **[redis_py](https://github.com/redis/redis-py)** qui retourne les 3 phrases les plus similaires à la nouvelle (`That is a happy boy`), triées par score de pertinence (distance cosinus).

{% highlight python linenos %}
from redis.commands.search.query import Query

def create_query(
    return_fields: list,
    search_type: str="KNN",
    number_of_results: int=3,
    vector_field_name: str="sentence_vector"
):

    base_query = f'*=>[{search_type} {number_of_results} @{vector_field_name} $vec_param AS vector_score]'
    return Query(base_query)\
        .sort_by("vector_score")\
        .paging(0, number_of_results)\
        .return_fields(*return_fields)\
        .dialect(2)
{% endhighlight %}

En exécutant ce calcul entre notre vecteur de requête et les trois autres vecteurs dans le graphique ci-dessus, nous pouvons déterminer la similarité des phrases entre elles.

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEg8eSKJpAEasHPS_mdp0aCJWFdV9NLS2OhSgkNW-tpt8_1oPXDIXIdlYA4KcBqzA0IWOjbKh5dWQ7dHFXlZ5kVzT6rI8sa2lgGP0zlBgE2yizDNgvXQkpHjq_SRdRLxWhVgDXgwImD9fRxtQHid51O4oIMtCaczKwP46HHEDT5Lj0ROgdHZ_GBJDa_jCgI){: .mx-auto.d-block :} *Calcul de la distance cosinus entre vecteurs.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}  

Comme vous l'avez peut-être supposé, `That is a happy boy` est la phrase la plus similaire à `That is a very happy person` et `That is a happy girl`, et très éloignée de `I love dogs`. Cet exemple ne capture qu'un des nombreux cas d'utilisation possibles pour les embeddings vectoriels : la _Recherche par Similarité Sémantique_.

Les instructions ci-dessus sont un bref aperçu pour démontrer les éléments de base de la Recherche par Similarité Vectorielle avec Redis. Vous pouvez l'essayer avec le notebook référencé ici : [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://github.com/aelkouhen/redis-vss/blob/main/1-%20Text%20Vector%20Search.ipynb)

Restez à l'écoute pour les prochains articles qui parleront des capacités avancées de Redis et du VSS.

## Résumé

Redis prend en charge des capacités diverses qui peuvent considérablement réduire la complexité des applications tout en offrant des performances constamment élevées, même à grande échelle. Parce que c'est une base de données en mémoire, Redis offre un très haut débit avec une latence inférieure à la milliseconde, en utilisant le moins de ressources computationnelles possible.

Avec la fonctionnalité de Recherche par Similarité Vectorielle, Redis débloque plusieurs applications révolutionnaires pour les entreprises en temps réel basées sur la similarité et le calcul de distance. Dans les prochains articles, nous verrons comment vous pouvez utiliser ces éléments de base pour différentes applications.

## Références
* [Vector-Similarity-Search from Basics to Production](https://mlops.community/vector-similarity-search-from-basics-to-production/), Sam Partee.
* [Documentation VSS](https://redis.io/docs/stack/search/reference/vectors/), redis.io
