---
layout: post
lang: fr
title: "Moteurs de recommandation en ligne avec CockroachDB"
subtitle: "Construire des systèmes de recommandation personnalisés avec les capacités vectorielles natives de CockroachDB"
cover-img: /assets/img/cover-ai-recom.webp
thumbnail-img: /assets/img/cover-ai-recom.webp
share-img: /assets/img/cover-ai-recom.webp
tags: [Artificial Intelligence, CockroachDB, vector search, recommendation engine, embeddings]
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

Les moteurs de recommandation ont acquis une importance considérable dans le paysage numérique d'aujourd'hui. À mesure que la concurrence mondiale s'intensifie, les entreprises font fréquemment appel aux systèmes de recommandation pour améliorer l'expérience utilisateur, stimuler l'engagement et augmenter les revenus.

Dans le secteur du commerce électronique, les moteurs de recommandation permettent des fonctions clés telles que les recommandations de produits personnalisées, la vente croisée et la vente incitative. En comprenant les préférences et l'historique d'achat des acheteurs, ces systèmes peuvent suggérer des produits et des services qui correspondent à leurs intérêts, conduisant à une plus grande satisfaction des clients et à des achats répétés.

Dans le secteur du divertissement et du streaming de contenu, par exemple, les moteurs de recommandation jouent un rôle crucial dans la suggestion de films, d'émissions de télévision, de musique ou d'articles pertinents. En analysant le comportement et les préférences d'un utilisateur, des plateformes comme [Netflix](https://www.cockroachlabs.com/customers/netflix/), Spotify et YouTube fournissent des recommandations personnalisées qui améliorent la satisfaction des utilisateurs et les encouragent à explorer davantage de contenu.

Heureusement, la mise en œuvre d'un moteur de recommandation n'a pas à être compliquée. Avec les capacités vectorielles de CockroachDB, votre entreprise peut mettre en œuvre des systèmes de recommandation complets — pour fournir des recommandations personnalisées parmi des milliards d'options possibles en un rien de temps.

Cet article vous guidera à travers le processus de conception et de construction d'un moteur de recommandation en ligne alimenté par les capacités vectorielles natives de CockroachDB :

1. Il commence par expliquer les fondamentaux des systèmes de recommandation et comment différentes approches — comme le filtrage basé sur le contenu, collaboratif et hybride — peuvent améliorer les expériences utilisateur dans des secteurs tels que le commerce électronique et le streaming de médias.

2. Vous apprendrez ensuite comment générer et stocker des embeddings d'images et de textes, implémenter la recherche par similarité en temps réel et construire des requêtes de recommandation scalables et à faible latence en utilisant l'architecture SQL distribuée de CockroachDB.

3. En cours de route, nous explorerons comment la prise en charge de l'indexation vectorielle (C-SPANN) par CockroachDB, le partitionnement par préfixe et la forte cohérence en font un choix idéal pour construire des applications IA performantes.

Que vous soyez développeur, ingénieur de données ou architecte, vous pouvez adapter cette présentation pratique à votre propre cas d'usage unique.

---

## Vue d'ensemble des systèmes de recommandation

Qu'est-ce qu'un moteur de recommandation ? Les moteurs de recommandation sont des modèles statistiques qui analysent les données des utilisateurs, telles que l'historique de navigation, le comportement d'achat, les préférences et les données démographiques, pour fournir des recommandations personnalisées. Ces recommandations peuvent prendre la forme de suggestions de produits, de recommandations de contenu ou de services pertinents.

L'importance des moteurs de recommandation réside dans leur capacité à répondre aux préférences individuelles des utilisateurs et à rationaliser les processus de prise de décision. En offrant des suggestions personnalisées, les entreprises peuvent efficacement engager les utilisateurs, les maintenir plus longtemps sur leurs plateformes et, finalement, augmenter les taux de conversion et les ventes.

Les moteurs de recommandation ont considérablement évolué depuis leur création au milieu des années 1990. Les premiers systèmes étaient largement basés sur des règles, s'appuyant sur des évaluations explicites des utilisateurs et des associations organisées manuellement pour suggérer du contenu. L'un des premiers exemples notables fut le [filtrage collaboratif d'article à article d'Amazon](https://www.cs.umd.edu/~samir/498/Amazon-Recommendations.pdf), qui a révolutionné les recommandations de produits en analysant les modèles de comportement des utilisateurs à grande échelle.

À mesure que l'utilisation du web et les volumes de données ont augmenté, la sophistication de ces systèmes a également progressé — passant d'approches heuristiques à des modèles d'apprentissage automatique capables de capturer des modèles plus profonds dans les préférences des utilisateurs. L'émergence du deep learning a marqué un tournant, permettant l'utilisation de réseaux de neurones et d'embeddings pour représenter les utilisateurs et les articles dans des espaces vectoriels de haute dimension.

Plus récemment, les architectures basées sur les transformers et la recherche vectorielle en temps réel ont encore amélioré la personnalisation et la réactivité des recommandations en ligne. Aujourd'hui, les moteurs de recommandation sont une partie critique de presque toutes les plateformes numériques — du commerce électronique aux services de streaming — jouant un rôle central dans l'engagement des utilisateurs, la rétention et la génération de revenus.

Il existe plusieurs types de systèmes de recommandation couramment utilisés :

**Filtrage basé sur le contenu** : Cette approche recommande des articles aux utilisateurs en fonction de leurs préférences et caractéristiques. Elle analyse le contenu et les attributs des articles avec lesquels les utilisateurs ont interagi ou qu'ils ont évalués positivement et suggère des articles similaires. Par exemple, si un utilisateur apprécie les films d'action dans un système de recommandation de films, le système recommanderait d'autres films d'action.

<img src="/assets/img/ai-recom-01.png" alt="Content-Based Filtering" style="width:100%">
{: .mx-auto.d-block :}
**Filtrage basé sur le contenu**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

**Filtrage collaboratif** : Cette méthode recommande des articles en se basant sur les similarités et les modèles trouvés dans le comportement et les préférences de plusieurs utilisateurs. Elle identifie les utilisateurs ayant des goûts similaires et recommande des articles que ces utilisateurs ont aimés ou bien évalués. Le filtrage collaboratif peut être divisé en deux sous-types :

- **Filtrage collaboratif basé sur les utilisateurs** : Il identifie les utilisateurs ayant des préférences similaires et recommande des articles que les utilisateurs ayant des goûts similaires ont appréciés (Scénarios A & B).

- **Filtrage collaboratif basé sur les articles** : Il identifie les articles similaires en fonction du comportement des utilisateurs et recommande des articles similaires à ceux avec lesquels l'utilisateur a précédemment interagi (Scénario C).

<img src="/assets/img/ai-recom-02.png" alt="Collaborative Filtering" style="width:100%">
{: .mx-auto.d-block :}
**Filtrage collaboratif**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

**Systèmes contextuels** : Ces systèmes prennent en compte des informations contextuelles, telles que l'heure, l'emplacement et le contexte de l'utilisateur, pour fournir des recommandations plus pertinentes. Par exemple, un service de streaming musical pourrait recommander des playlists d'entraînement énergiques le matin et de la musique relaxante le soir. De même, un site de commerce électronique suggérera des articles spécifiques lors du Black Friday ou de Noël, différents de ce qu'il pourrait recommander à d'autres périodes de l'année.

<img src="/assets/img/ai-recom-03.png" alt="Context-Aware Filtering" style="width:100%">
{: .mx-auto.d-block :}
**Filtrage contextuel**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

**Systèmes de recommandation hybrides** : Ces systèmes combinent plusieurs techniques de recommandation pour fournir des recommandations plus précises et diversifiées. Ils exploitent les forces de différentes approches, telles que le filtrage basé sur le contenu et le filtrage collaboratif, pour surmonter leurs limites et offrir des suggestions plus efficaces.

---

## Moteurs de recommandation avec CockroachDB

Contrairement aux moteurs de recommandation hors ligne qui génèrent des recommandations personnalisées basées sur des données historiques, un moteur de recommandation idéal devrait prioriser l'efficacité des ressources, fournir des mises à jour en temps réel à haute performance (en ligne) et proposer des choix précis et pertinents aux utilisateurs. Par exemple, il peut être inefficace de suggérer à un client un article qu'il a déjà acheté simplement parce que votre système de recommandation n'était pas au courant des dernières actions du client.

<img src="/assets/img/ai-recom-04.png" alt="Offline Recommendation Systems" style="width:100%">
{: .mx-auto.d-block :}
**Systèmes de recommandation hors ligne**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Les moteurs en ligne doivent réagir aux actions des clients pendant qu'ils naviguent encore sur votre site, et recalculer les recommandations en conséquence. Cela donnerait aux clients le sentiment d'avoir un assistant commercial dédié, rendant leurs expériences plus personnalisées.

<img src="/assets/img/ai-recom-05.png" alt="Online Recommendation Systems" style="width:100%">
{: .mx-auto.d-block :}
**Systèmes de recommandation en ligne**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Pour cela, vous avez clairement besoin d'un backend cohérent à faible latence pour mettre en œuvre un tel système, avec deux capacités importantes.

1. Premièrement, vous devez présenter les attributs et les préférences des utilisateurs d'une manière spécifique qui permet leur classification en groupes. Ensuite, vous avez besoin d'une représentation performante des produits qui fournit le calcul de similarité et des requêtes avec une latence très faible.

La mise en œuvre de tels systèmes avec la base de données SQL distribuée [CockroachDB](https://www.cockroachlabs.com/product/overview/) est une tâche simple. Étant donné la forte cohérence et le niveau d'isolation sérialisable fournis par défaut, CockroachDB expose toujours l'état le plus précis au moteur de recommandation, évitant toute donnée périmée qui pourrait résulter d'interactions entre des transactions concurrentes.

2. Deuxièmement, vous considéreriez les préférences des utilisateurs, les attributs des produits et tout autre paramètre de filtrage comme des vecteurs. Ensuite, grâce aux [capacités d'indexation vectorielle fournies par CockroachDB](https://www.cockroachlabs.com/blog/distributed-vector-indexing-cockroachdb/), vos moteurs de recommandation peuvent effectuer des calculs de distance (scores d'affinité) entre ces vecteurs et faire des recommandations basées sur ces scores.

Un [vector embedding](https://www.cockroachlabs.com/blog/genai-using-cockroachdb/#Vector-Embeddings) est une représentation mathématique de quelque chose (comme du texte ou des images) sous forme de liste de nombres, où la proximité des nombres signifie la proximité du sens. Ces embeddings sont mappés dans un espace multidimensionnel pour effectuer des calculs de proximité afin de comprendre la relation entre la signification des articles.

<img src="/assets/img/ai-recom-06.png" alt="Product descriptions presented as vectors" style="width:100%">
{: .mx-auto.d-block :}
**Descriptions de produits représentées sous forme de vecteurs**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Les représentations vectorielles des données permettent aux algorithmes d'apprentissage automatique de traiter et d'analyser l'information efficacement. Ces algorithmes reposent souvent sur des opérations mathématiques effectuées sur des vecteurs, telles que les produits scalaires, l'addition de vecteurs et la normalisation, pour calculer les similarités, les distances et les transformations.

Mais surtout, les représentations vectorielles facilitent la comparaison et le clustering des points de données dans un espace multidimensionnel. Les [mesures de similarité](https://www.cockroachlabs.com/blog/genai-using-cockroachdb/#ChatGPT:-How-it-works), telles que la similarité cosinus ou la distance euclidienne, peuvent être calculées entre les vecteurs pour déterminer la similarité ou la dissimilarité entre les points de données. Ainsi, votre moteur de recommandation peut exploiter les vecteurs pour :

- regrouper et classer les clients selon leurs préférences et attributs (âge, genre, emploi, localisation, revenu…) — cela peut aider à trouver des similitudes entre les clients (Filtrage collaboratif).

- suggérer des produits similaires en se basant sur leurs images et descriptions textuelles (Filtrage basé sur le contenu).

<img src="/assets/img/ai-recom-07.png" alt="Online Recommendation Engine using CockroachDB" style="width:100%">
{: .mx-auto.d-block :}
**Moteur de recommandation en ligne avec CockroachDB**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Dans la prochaine section, vous apprendrez comment générer et stocker des embeddings d'images et de textes, implémenter la recherche par similarité en temps réel et construire des requêtes de recommandation scalables et à faible latence en utilisant l'architecture SQL distribuée de CockroachDB.

### 1 - Création des Vector Embeddings

Pour comprendre comment les vector embeddings sont créés, une brève introduction aux modèles modernes de deep learning est utile.

Il est essentiel de convertir les données non structurées en représentations numériques pour les rendre compréhensibles par les modèles d'apprentissage automatique. Autrefois, cette conversion était effectuée manuellement par l'ingénierie des caractéristiques.

Le deep learning a introduit un changement de paradigme dans ce processus. Plutôt que de s'appuyer sur l'ingénierie manuelle, les modèles de deep learning — appelés transformers — apprennent de manière autonome les interactions de caractéristiques complexes dans des données complexes. À mesure que les données traversent un transformer, il génère de nouvelles représentations des données d'entrée, chacune avec des formes et des tailles variables. Chaque couche du transformer se concentre sur différents aspects de l'entrée. Cette capacité du deep learning à générer automatiquement des représentations de caractéristiques à partir des entrées forme la base de la création de vector embeddings.

<img src="/assets/img/ai-recom-08.gif" alt="Two-tower neural network model - Source: Google Search" style="width:100%">
{: .mx-auto.d-block :}
**Modèle de réseau de neurones à deux tours - Source : Google Search**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Les Vector Embeddings sont créés par un processus d'embedding qui mappe des données discrètes ou catégorielles en représentations vectorielles continues. Le processus de création d'embeddings dépend du contexte spécifique et du type de données. Voici quelques techniques courantes :

**Embeddings de texte** — utilisent des méthodes telles que la fréquence des termes-fréquence inverse des documents ([TF-IDF](https://www.learndatasci.com/glossary/tf-idf-term-frequency-inverse-document-frequency)) pour calculer la fréquence des mots dans un corpus de texte et attribuer des poids à chaque mot en conséquence. Ils peuvent utiliser d'autres algorithmes populaires basés sur des réseaux de neurones comme [Word2Vec](https://www.tensorflow.org/text/tutorials/word2vec) ou [GloVe](https://nlp.stanford.edu/projects/glove/) pour apprendre des embeddings de mots en entraînant des réseaux de neurones sur de grands corpus de texte. Ces algorithmes capturent les relations sémantiques entre les mots en se basant sur leurs modèles de cooccurrence.

**Embeddings d'images** — utilisent des réseaux de neurones convolutifs ([CNN](https://fr.mathworks.com/videos/introduction-to-deep-learning-what-are-convolutional-neural-networks--1489512765771.html)) tels que [VGG](https://datascientest.com/en/unveiling-the-secrets-of-the-vgg-model-a-deep-dive-with-daniel), [ResNet](https://arxiv.org/abs/1512.03385) ou [Inception](https://www.geeksforgeeks.org/machine-learning/ml-inception-network-v1/), qui sont couramment utilisés pour l'extraction de caractéristiques d'images. Les activations des couches intermédiaires ou la sortie des couches entièrement connectées peuvent servir d'embeddings d'images.

**Embeddings de données séquentielles** — utilisent des réseaux de neurones récurrents ([RNN](https://stanford.edu/~shervine/teaching/cs-230/cheatsheet-recurrent-neural-networks)) : les RNN, tels que la mémoire à long terme et à court terme ([LSTM](https://www.geeksforgeeks.org/deep-learning/deep-learning-introduction-to-long-short-term-memory/)) ou l'unité récurrente à portail ([GRU](https://towardsdatascience.com/gru-recurrent-neural-networks-a-smart-way-to-predict-sequences-in-python-80864e4fe9f6/)), peuvent apprendre des embeddings pour les données séquentielles en capturant les dépendances et les modèles temporels. Ils peuvent également utiliser le modèle Transformer lui-même ou ses variantes comme [BERT](https://huggingface.co/docs/transformers/en/model_doc/bert) ou [GPT](https://huggingface.co/docs/transformers/en/model_doc/openai-gpt), qui peuvent générer des embeddings contextualisés pour des données séquentielles.

**Embeddings d'utilisateurs** — L'activité d'un utilisateur sur une marketplace de commerce électronique ne se limite pas à la seule consultation d'articles. Les utilisateurs peuvent également effectuer des actions telles que faire une recherche, ajouter un article à leur panier, ajouter un article à leur liste de surveillance, etc. Ces actions fournissent des signaux précieux pour la génération de recommandations personnalisées. Vous pouvez utiliser un réseau de neurones récurrent (RNN) ou des unités récurrentes à portail (GRU) pour encoder les informations d'ordonnancement des événements historiques. Pour créer des embeddings d'utilisateurs, vous pouvez exploiter l'approche des réseaux de neurones à deux tours comme celui implémenté par [eBay](https://arxiv.org/pdf/2102.06156.pdf) : il consiste en deux modèles de réseaux de neurones distincts, souvent appelés « tours », qui traitent différents types de données d'entrée en parallèle.

Les deux tours du réseau reçoivent généralement différents types d'informations liées aux interactions utilisateur-article. Par exemple, un tour pourrait traiter des données spécifiques à l'utilisateur, telles que des informations démographiques ou des préférences passées, tandis que l'autre tour traite des données spécifiques à l'article, telles que des descriptions de produits ou des attributs. Chaque tour apprend indépendamment des représentations ou des caractéristiques à partir de ses données d'entrée respectives en utilisant plusieurs couches de neurones artificiels interconnectés. La sortie de la couche finale de chaque tour est ensuite combinée ou fusionnée pour générer une représentation commune qui capture la relation entre les utilisateurs et les articles. Par souci de simplicité, j'omettrai cette relation utilisateur-article dans le reste de l'article et me concentrerai uniquement sur les embeddings d'images et de textes.

<img src="/assets/img/ai-recom-09.png" alt="Example of the Two-tower Architecture" style="width:100%">
{: .mx-auto.d-block :}
**Exemple de l'architecture à deux tours**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Dans notre implémentation, nous utiliserons une variante de BERT appelée [all-mpnet-base-v2](https://huggingface.co/sentence-transformers/all-mpnet-base-v2) pour créer des embeddings de données séquentielles pour les descriptions de produits. Pour générer des embeddings d'images de produits, nous utilisons le modèle [Img2Vec](https://github.com/christiansafka/img2vec) (une implémentation de Resnet-18). Les deux modèles sont hébergés et utilisables en ligne, sans expertise ni installation requise. Mais d'abord, nous devons créer le schéma de la table avant d'y insérer des données :

```sql
CREATE TABLE products (product_id INT PRIMARY KEY, product_description STRING, category STRING NOT NULL, description_vector VECTOR(768), image_vector VECTOR(512));
```

Ensuite, stockons ces produits et leurs embeddings respectifs dans CockroachDB. Le script Python suivant génère et stocke des vector embeddings pour les produits, en utilisant des données d'images et de textes. Il utilise des bibliothèques pour le traitement des images ([PIL](https://he-arc.github.io/livre-python/pillow/index.html), [img2vec\_pytorch](https://pypi.org/project/img2vec-pytorch/)), les embeddings de texte ([sentence\_transformers](https://huggingface.co/sentence-transformers)) et la connexion à la base de données ([psycopg2](https://www.psycopg.org/docs/)).

Pour les embeddings de texte, la fonction `generate_text_vectors` utilise un modèle basé sur BERT ([all-mpnet-base-v2](https://huggingface.co/sentence-transformers/all-mpnet-base-v2)) pour créer des vector embeddings sémantiques à partir des descriptions de produits. La fonction `generate_image_vectors` télécharge les images des produits, les redimensionne et utilise un modèle [ResNet-18](https://docs.pytorch.org/vision/main/models/generated/torchvision.models.resnet18.html) pour créer des embeddings d'images. La fonction `vectorize_products` appelle les fonctions précédentes et combine les vecteurs de texte et d'image pour chaque produit dans un dictionnaire. Ensuite, la fonction `store_product_vectors` stocke les vecteurs de produits dans la table `products` de CockroachDB.

```python
import os
import psycopg2
# data prep
import pandas as pd
import numpy as np
# for creating image vector embeddings
import urllib.request
from PIL import Image
from img2vec_pytorch import Img2Vec
# for creating semantic (text-based) vector embeddings
from sentence_transformers import SentenceTransformer
def generate_text_vectors(products):
  text_vectors = {}

  # Bert variant to create text embeddings
  text_model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
  # generate text vector
  for index, row in products.iterrows():
     text_vector = text_model.encode(row["description"])
     text_vectors[index] = text_vector.astype(np.float32)
  return text_vectors
def generate_image_vectors(products):
  img_vectors={}
  images=[]  
  converted=[]
  # Resnet-18 to create image embeddings
  image_model = Img2Vec()
  # generate image vector
  for index, row in products.iterrows():
     tmp_file = str(index) + ".jpg"
     urllib.request.urlretrieve(row["image_url"], tmp_file)
     img = Image.open(tmp_file).convert('RGB')
     img = img.resize((224, 224))
     images.append(img)
     converted.append(index)
  vec_list = image_model.get_vec(images)
  img_vectors = dict(zip(converted, vec_list))
  return img_vectors

def load_product_catalog():
  # initialize product
  dataset = {
          'id': [1253, 9976, 3626, 2746, 5735, 9982, 4322, 1978, 1736],
          'description': ['Herringbone Brown Classic', 'Herringbone Wool Suit Navy Blue', 'Peaky Blinders Tweed Outfit', 'Cable Knitted Scarf and Bobble Hat', 'ADIDAS Men White Pluto Sports Shoes', 'ADIDAS Unisex White Shoes', 'Nike STAR RUNNER 4', 'Adidas SL 72 Unisex Shoes', 'Adidas Adizero F50 2 M Mens Running Jogging Shoes'],
          'category': ['Suits', 'Suits', 'Suits', 'Hats', 'Shoes', 'Shoes', 'Shoes', 'Shoes', 'Shoes'],
          'image_url': [
                'https://raw.githubusercontent.com/aelkouhen/aelkouhen.github.io/main/assets/img/donegal-herringbone-tweed-men_s-jacket.jpeg',
                'https://raw.githubusercontent.com/aelkouhen/aelkouhen.github.io/main/assets/img/Mens-Herringbone-Tweed-Check-3-Piece-Wool-Suit-Navy-Blue.webp',
                'https://raw.githubusercontent.com/aelkouhen/aelkouhen.github.io/main/assets/img/Marc-Darcy-Enzo-Mens-Herringbone-Tweed-Check-3-Piece-Suit.jpeg',
                'https://raw.githubusercontent.com/aelkouhen/aelkouhen.github.io/main/assets/img/Mocara_MaxwellFlat_900x.jpg',
                'https://raw.githubusercontent.com/aelkouhen/aelkouhen.github.io/main/assets/data/products/men/393e9315126350d97000721f330aa964.jpg',
                'https://raw.githubusercontent.com/aelkouhen/aelkouhen.github.io/main/assets/data/products/men/6d62ba4de5c73b36d44f6bff05d2457e.jpg',
                'https://raw.githubusercontent.com/aelkouhen/aelkouhen.github.io/main/assets/data/products/men/7185ef5d96833937481c19a47edac96a.jpg',
                'https://raw.githubusercontent.com/aelkouhen/aelkouhen.github.io/main/assets/data/products/men/8cf52572340c3592e5f0ede116a0206f.jpg',
                'https://raw.githubusercontent.com/aelkouhen/aelkouhen.github.io/main/assets/data/products/men/b3d19377041615d8a7cf46b96ef67c4c.jpg'
                ]
          }

  # Create DataFrame
  products = pd.DataFrame(dataset).set_index('id')
  return products
def vectorize_products(catalog):  
  products = []
  img_vectors = generate_image_vectors(catalog)
  text_vectors = generate_text_vectors(catalog)
  for index, row in catalog.iterrows():
     _id = index
     text_vector = text_vectors[_id].tolist()
     img_vector = img_vectors[_id].tolist()
     vector_dict = {
         "description_vector": text_vector,
         "image_vector": img_vector,
         "product_id": _id,
         "category": row.category,
         "product_description": row.description
     }
     products.append(vector_dict)
  return products
def store_product_vectors(crdb_url, products):
   with psycopg2.connect(crdb_url) as conn:
       # Open a cursor to perform database operations
       with conn.cursor() as cursor:
           for product in products:
               query = f'''INSERT INTO products (product_id, product_description, category, description_vector, image_vector) VALUES ({product["product_id"]}, '{product["product_description"]}', '{product["category"]}','{product["description_vector"]}', '{product["image_vector"]}')''' 
               cursor.execute(query)
               print(f'''Inserted product: {product["product_id"]}, {product["product_description"]}''')

def create_crdb_url():
  host = os.environ.get("CRDB_HOST", "localhost")
  port = os.environ.get("CRDB_PORT", 26257)
  db = os.environ.get("CRDB_DATABASE", "defaultdb")
  username = os.environ.get("CRDB_USERNAME", "root")
  url = f'''postgresql://{username}@{host}:{port}/{db}'''
  return url
# Create a CockroachDB connection string
crdb_url = create_crdb_url()
# Load a few products
catalog = load_product_catalog()
# Create vector embeddings for products
products = vectorize_products(catalog)
# Store vectors in CockroachDB
store_product_vectors(crdb_url, products)
```

Le choix de la technique d'embedding dépend du type de données spécifique, de la tâche et des ressources disponibles. Le [Huggingface Model Hub](https://huggingface.co/models) contient de nombreux modèles qui peuvent créer des embeddings pour différents types de données.

### 2 - Indexation vectorielle

Une fois que vous avez créé des vector embeddings pour vos produits, vous pouvez choisir de les stocker et de les interroger dans une base de données vectorielle comme [Pinecone](https://www.pinecone.io/), [Milvus](https://milvus.io), [Weaviate](https://weaviate.io/), ou [Qdrant](https://qdrant.tech/) — chacune optimisée pour la recherche rapide par similarité. Bien que ces systèmes privilégient souvent la performance à la forte cohérence, CockroachDB offre une forte cohérence, un haut niveau d'isolation, une scalabilité horizontale et prend désormais en charge les types de données vectorielles et les requêtes de similarité approximative. Cela en fait une bonne option lorsque des [garanties transactionnelles](https://www.cockroachlabs.com/guides/vector-search-meets-distributed-sql/) sont nécessaires parallèlement aux opérations vectorielles.

De plus, le nouveau système d'indexation vectorielle **C-SPANN** de CockroachDB intègre des idées des articles [SPANN](https://www.microsoft.com/en-us/research/publication/spann-highly-efficient-billion-scale-approximate-nearest-neighbor-search/) et [SPFresh](https://www.microsoft.com/en-us/research/publication/spfresh-incremental-in-place-update-for-billion-scale-vector-search/) de Microsoft, ainsi que du projet [ScaNN](https://research.google/blog/announcing-scann-efficient-vector-similarity-search/) de Google. Il a été conçu pour prendre en charge une recherche sémantique rapide et en temps réel sur des milliards d'éléments de données — tels que des photos ou des documents — dans un environnement hautement distribué et transactionnel.

Contrairement aux solutions traditionnelles qui s'appuient sur des jeux de données en mémoire ou des écritures par lots, C-SPANN est conçu pour fonctionner sur plusieurs régions avec une forte cohérence, une faible latence et une scalabilité linéaire. Il prend en charge la recherchabilité immédiate des nouvelles données, évite la coordination centrale et s'adapte naturellement au modèle de stockage clé-valeur distribué de CockroachDB.

<img src="/assets/img/ai-recom-10.png" alt="C-SPANN" style="width:100%">
{: .mx-auto.d-block :}
**C-SPANN**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Pour maintenir les coûts de stockage et de calcul faibles, C-SPANN intègre **RaBitQ**, une technique de quantification qui réduit la taille des vecteurs d'environ 94 %. Les vecteurs quantifiés sont analysés rapidement à l'aide d'instructions optimisées [SIMD](https://www.sciencedirect.com/topics/computer-science/single-instruction-multiple-data), et une étape de rerankage garantit une haute précision en vérifiant à nouveau les meilleurs candidats par rapport aux vecteurs originaux en pleine précision. Le système prend également en charge l'indexation par utilisateur et multi-régions via des colonnes de préfixe, permettant une isolation fine et une localité des données. Cela garantit des expériences de recherche scalables, sécurisées et à faible latence quel que soit le nombre d'utilisateurs ou de régions impliqués.

CockroachDB utilise une métrique de distance pour mesurer la similarité entre deux vecteurs (c'est-à-dire à quel point deux vecteurs sont « proches » ou « éloignés »). Actuellement, seuls les opérateurs **<->** [Distance Euclidienne](https://en.wikipedia.org/wiki/Euclidean_distance) (L2), **<#>** [Produit Intérieur](https://en.wikipedia.org/wiki/Inner_product_space) (IP) et **<=>** [Similarité Cosinus](https://en.wikipedia.org/wiki/Cosine_similarity) sont disponibles dans CockroachDB.

<img src="/assets/img/ai-recom-11.png" alt="Distance Metrics" style="width:100%">
{: .mx-auto.d-block :}
**Métriques de distance**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Nous avons décrit comment C-SPANN peut regrouper efficacement de grands volumes de vecteurs tout en maintenant l'index à jour grâce à des mises à jour incrémentielles en temps réel. Cependant, il y a une nuance importante dans les applications pratiques : les vecteurs appartiennent généralement à des entités distinctes — telles que des utilisateurs, des clients ou des catégories de produits — et la plupart des requêtes sont destinées à opérer dans le périmètre d'une seule entité. Inclure des vecteurs de propriétaires non liés diluera la pertinence dans la recherche vectorielle.

CockroachDB répond à cela élégamment en prenant en charge les **colonnes de préfixe** dans les index vectoriels. Cette fonctionnalité permet de partitionner logiquement l'index par propriété — ou tout autre critère — garantissant à la fois l'isolation et l'efficacité des requêtes. Voici un exemple de création de l'index vectoriel d'images dans CockroachDB basé sur la table `products` créée précédemment.

```sql
CREATE VECTOR INDEX ON products (category, image_vector);
```

Si vous créez des index vectoriels pour la première fois dans votre cluster, vous devrez configurer le paramètre `feature.vector_index.enabled` :

```sql
SET CLUSTER SETTING feature.vector_index.enabled = true;
```

Après avoir chargé les vecteurs de produits dans CockroachDB et créé les index vectoriels, le moteur de recommandation peut exécuter toutes sortes de requêtes de recherche par similarité.

### 3 - Recherche par similarité vectorielle

Au cœur de l'indexation vectorielle de CockroachDB se trouve un arbre K-means hiérarchique qui [organise les vecteurs](https://www.cockroachlabs.com/blog/semantic-search-using-cockroachdb/#Semantic-search-in-CockroachDB) en partitions basées sur la similarité. Ces partitions sont stockées dans l'architecture basée sur des plages de CockroachDB, permettant la division automatique, la fusion et l'équilibrage de charge. Pour maintenir la précision de l'index dans le temps, C-SPANN prend en charge les divisions de partitions en arrière-plan, les fusions et les réassignations de vecteurs, garantissant que les vecteurs se trouvent toujours dans leur cluster le plus pertinent. Cette conception élimine le besoin de reconstructions complètes coûteuses de l'index, même après des millions de mises à jour incrémentielles.

Ce système d'indexation débloque des capacités de recherche avancées comme la recherche des « top K » vecteurs les plus similaires, l'exécution de recherches à faible latence dans de grands espaces vectoriels allant de dizaines de milliers à des centaines de millions de vecteurs distribués sur plusieurs machines.

Par conséquent, CockroachDB expose la fonctionnalité de recherche habituelle, combinant du texte intégral, des pré-filtres numériques et géographiques avec la recherche vectorielle K-voisins les plus proches (KNN) : avec CockroachDB, vous pouvez interroger des produits stockés sous forme de vecteurs tout en pré-filtrant par localisation, prix et description, et choisir les métriques de distance vectorielle pertinentes pour calculer à quel point deux produits sont « similaires » ou « dissemblables ».

<img src="/assets/img/ai-recom-12.png" alt="Calculating Cosine Similarity between Product Descriptions" style="width:100%">
{: .mx-auto.d-block :}
**Calcul de la similarité cosinus entre les descriptions de produits**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

La requête ci-dessous retourne les 10 produits similaires — dont les vecteurs sont stockés dans le champ `image_vector` — à un vecteur d'image de requête. Vous pouvez également définir un pré-filtre concernant sa catégorie, sa plage de prix ou son lieu de vente.

```sql
SELECT product_id, product_description FROM products WHERE category = $1 ORDER BY (image_vector <-> $2) LIMIT 10;
```

Par exemple, si vous recherchez un produit avec des emplacements de magasin associés et des images de produits (encodées sous forme de vecteurs) dans une seule table, vous pouvez créer un index secondaire sur la colonne d'emplacement du magasin pour pré-filtrer les données avant d'effectuer une recherche vectorielle.

Cela signifie qu'au lieu de scanner l'ensemble du jeu de données, le système réduit d'abord la recherche aux emplacements pertinents — tels que « _Casablanca_ » — puis applique la recherche par similarité vectorielle uniquement dans ce sous-ensemble. Une telle approche de recherche hybride améliore considérablement les performances des requêtes et l'efficacité des ressources, facilitant la création d'applications IA intelligentes et performantes à grande échelle en utilisant la syntaxe SQL familière.

Voici un exemple de création d'une requête qui retourne les trois produits les plus similaires (par image) à celui présenté ci-dessous, triés par score de pertinence (Distance Euclidienne définie dans les index créés précédemment).

```python
def create_query_vector():
  query_image_url = "https://raw.githubusercontent.com/aelkouhen/aelkouhen.github.io/main/assets/data/products/2eca615a43d0098f4bb5fc90004c3678.jpg"
  # Resnet-18 to create image embeddings
  image_model = Img2Vec()
  # generate image vector
  tmp_file = "query_image.jpg"
  urllib.request.urlretrieve(query_image_url, tmp_file)
  img = Image.open(tmp_file).convert('RGB')
  img = img.resize((224, 224))
  vector = image_model.get_vec(img)
  query_vector = np.array(vector, dtype=np.float32).tolist()
  return query_vector
def fetch_similar_products(crdb_url, category, query_vector, limit=5):
   with psycopg2.connect(crdb_url) as conn:
       # Open a cursor to perform database operations
       with conn.cursor() as cursor:
           query = f'''SELECT product_id, product_description
                       FROM products
                       WHERE category = '{category}'
                       ORDER BY image_vector <-> '{query_vector}'
                       LIMIT {limit}'''
           cursor.execute(query)
           results = cursor.fetchall()
           print("The most similar product are: ")
           for row in results:
               print(f"The Product ID: {row[0]}, Description: {row[1]}")
query_vector = create_query_vector()
fetch_similar_products(crdb_url, "Shoes", query_vector, limit=3)
```

Même si l'index contient des milliards de produits, cette requête ne recherchera que le sous-ensemble associé à une catégorie de produits spécifique. Les performances d'insertion et de recherche évoluent avec le nombre de vecteurs étiquetés dans cette catégorie — et non le volume total de vecteurs dans le système. Cet isolement réduit la contention entre les produits, car les requêtes opèrent sur des partitions d'index et des lignes séparées.

En coulisses, l'index maintient un arbre K-means indépendant pour chaque catégorie. Du point de vue du système, il y a peu de différence entre la gestion d'un milliard de vecteurs dans un seul arbre ou leur distribution sur un million d'arbres plus petits. Dans les deux cas, les vecteurs sont affectés à des partitions et stockés dans des plages dans la couche clé-valeur de CockroachDB. Ces plages sont automatiquement divisées, fusionnées et distribuées sur les nœuds, permettant une scalabilité quasi-linéaire à mesure que l'utilisation augmente.

<img src="/assets/img/ai-recom-13.png" alt="Partitioned vector indexing" style="width:100%">
{: .mx-auto.d-block :}
**Indexation vectorielle partitionnée**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Les instructions ci-dessus sont un bref aperçu pour démontrer les éléments de base d'un moteur de recommandation en ligne utilisant CockroachDB. Vous pouvez essayer cela avec le notebook référencé [ici](https://colab.research.google.com/drive/15ibk5BoLmldi06UJ6a4gewEc5zxxCTZ9?usp=sharing) (installez [Google Colab](https://colab.research.google.com/) pour l'ouvrir).

---

## Un moteur de recommandation IA haute performance

CockroachDB prend en charge des capacités diverses qui peuvent réduire considérablement la complexité des applications tout en offrant des performances constamment élevées, même à grande échelle.

Avec les capacités vectorielles, CockroachDB a débloqué plusieurs applications IA impactantes basées sur le calcul de similarité et de distance en quasi temps réel avec une haute précision. Les moteurs de recommandation sont un exemple de telles applications.

Si vous souhaitez fournir des recommandations interactives basées sur le contenu, vous pourriez vouloir tirer parti de CockroachDB comme base de données vectorielle et moteur de recherche par similarité. Quelle que soit la complexité de votre moteur de recommandation : collaboratif, basé sur le contenu, contextuel ou même hybride, CockroachDB vous aide à fournir les meilleures recommandations pour une expérience utilisateur réussie.


---

## Ressources

- [Documentation de la recherche vectorielle CockroachDB](https://www.cockroachlabs.com/docs/stable/vector-search.html)
- [C-SPANN : Indexation en temps réel pour des milliards de vecteurs](/2025-11-23-cockroachdb-ai-spann/)
- [Article original : Moteurs de recommandation en ligne avec CockroachDB](https://www.cockroachlabs.com/blog/recommendation-engines-cockroachdb/)
- [Filtrage collaboratif d'article à article d'Amazon](https://www.cs.umd.edu/~samir/498/Amazon-Recommendations.pdf)
- [Notebook Google Colab](https://colab.research.google.com/drive/15ibk5BoLmldi06UJ6a4gewEc5zxxCTZ9?usp=sharing)
- [Sentence Transformers — all-mpnet-base-v2](https://huggingface.co/sentence-transformers/all-mpnet-base-v2)
- [Img2Vec — Embeddings d'images avec PyTorch](https://github.com/christiansafka/img2vec)
- [SPANN : Recherche ANN à milliards d'échelle hautement efficace (Microsoft Research)](https://www.microsoft.com/en-us/research/publication/spann-highly-efficient-billion-scale-approximate-nearest-neighbor-search/)
- [SPFresh : Mise à jour incrémentielle en place pour la recherche vectorielle à milliards d'échelle](https://www.microsoft.com/en-us/research/publication/spfresh-incremental-in-place-update-for-billion-scale-vector-search/)
- [ScaNN : Recherche efficace par similarité vectorielle (Google Research)](https://research.google/blog/announcing-scann-efficient-vector-similarity-search/)
- [La recherche vectorielle rencontre le SQL distribué](https://www.cockroachlabs.com/guides/vector-search-meets-distributed-sql/)
