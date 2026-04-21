---
layout: post
title: "Online Recommendation Engines with CockroachDB"
subtitle: "Building real-time, personalised recommendation systems on a distributed SQL database"
cover-img: /assets/img/cover-ai-recom.webp
thumbnail-img: /assets/img/cover-ai-recom.webp
share-img: /assets/img/cover-ai-recom.webp
tags: [cockroachdb-ai, CockroachDB, GenAI, vector search, recommendation engine, embeddings]
comments: true
---

Recommendation engines have become the invisible backbone of the modern digital economy. Every time Netflix surfaces the next series you cannot stop watching, Spotify generates a playlist that fits your mood, or Amazon shows you the product you were about to search for, a recommendation system is at work — silently processing your behaviour, preferences, and context to predict what you want next.

These systems are not just a convenience feature. Research consistently shows that recommendations drive 35% of Amazon's revenue, 75% of what people watch on Netflix, and more than half of all clicks on YouTube's homepage. At that scale, a slow, stale, or inaccurate recommendation is not just a missed opportunity — it is a direct loss of business.

This article explains how to build a **real-time, personalised recommendation engine on CockroachDB**, leveraging its native vector indexing capabilities. We will cover the theoretical foundations of recommendation systems, the role of vector embeddings, how CockroachDB's C-SPANN index enables low-latency similarity search at scale, and a complete implementation you can run today.

---

## Overview of Recommendation Systems

### Definition and Significance

A recommendation engine is a statistical model that analyses user data — browsing history, purchase behaviour, explicit ratings, demographics — to surface personalised suggestions. The goal is to reduce the decision burden on the user: instead of navigating a catalogue of millions of items, the system predicts the handful that are most relevant to that individual at that moment.

The business case is straightforward. Personalised recommendations increase engagement, reduce churn, and improve conversion rates. The engineering challenge is equally straightforward to state and difficult to solve: how do you deliver accurate, fresh recommendations across millions of users and billions of items, in milliseconds?

### Historical Evolution

Recommendation systems emerged in the mid-1990s as early e-commerce platforms began accumulating user behaviour data. The first generation was rule-based — explicit ratings, manually curated associations, simple heuristics like "customers who bought X also bought Y." Amazon's item-to-item collaborative filtering, introduced in 2003, marked a step change: by analysing purchase patterns across the entire user base rather than individual profiles, it could surface non-obvious associations at scale.

The next generation introduced machine learning models — matrix factorisation, gradient boosted trees, factorisation machines — that could capture latent user preferences without explicit rules. Deep learning brought a further leap: neural networks, and eventually transformer-based architectures, learn rich embeddings that represent users and items as points in a high-dimensional vector space, where proximity encodes semantic similarity. Today, state-of-the-art systems combine dense vector representations with real-time retrieval to deliver personalised results in tens of milliseconds.

### Types of Recommendation Systems

**Content-Based Filtering**

Content-based systems recommend items similar to those a user has previously interacted with, based on the attributes of the items themselves. If a user has watched several action films, the system recommends other films with similar genre, director, cast, or plot keywords. The approach works well for new users (cold-start is handled by item attributes) and provides transparent, explainable recommendations, but it is limited to items similar to what the user already knows — it cannot surface genuine surprises.

**Collaborative Filtering**

Collaborative filtering ignores item attributes entirely and instead identifies patterns in collective user behaviour. Two variants exist:

- **User-Based:** Finds users with similar taste profiles and recommends items they liked that the target user has not yet seen.
- **Item-Based:** Finds items that are frequently liked together across the user base and recommends items similar to those the target user has interacted with.

Collaborative filtering excels at serendipitous discovery — it can recommend items the user would never have searched for — but suffers from the cold-start problem for new users and new items with no interaction history.

**Context-Aware Systems**

Context-aware systems factor in situational signals — time of day, location, device, weather, current activity — alongside user preferences. The same user might want energetic workout music at 7am and ambient background music at 9pm. A travel recommendation system might weight proximity differently depending on whether the user is planning a trip or already on location. Context awareness significantly improves relevance but requires richer input signals and more complex models.

**Hybrid Systems**

Hybrid systems combine multiple approaches to compensate for their individual weaknesses. A typical architecture uses content-based filtering to handle cold-start, collaborative filtering to leverage collective patterns for established users, and a neural reranker to blend signals and apply business rules (inventory, margins, freshness) before the final result is served.

---

## Recommendation Engines with CockroachDB

### Online vs. Offline Systems

A fundamental architectural choice in any recommendation system is whether to compute recommendations offline (in a batch job that runs periodically) or online (in real time as the user interacts with the platform).

**Offline systems** pre-compute recommendations for every user and cache the results. They are simple to implement and fast to serve, but they go stale quickly. A user who just bought a laptop should not continue seeing laptop recommendations — but an offline system refreshed nightly will not know about that purchase until tomorrow. Offline systems are appropriate for cold-start scenarios and low-traffic applications where real-time personalisation is not a priority.

**Online systems** recompute or update recommendations in response to each user action. They require a database that can handle high-frequency reads and writes with low latency, strong consistency, and the ability to perform complex similarity queries on fresh data. This is where CockroachDB's architecture becomes directly relevant.

### Why CockroachDB for Online Recommendations

CockroachDB brings two capabilities that are unusually well-suited to online recommendation workloads:

**Strong Consistency**

CockroachDB operates at the serializable isolation level by default. This means the recommendation engine always sees the most accurate, up-to-date state of the data — no stale reads from a replica lag, no race conditions between the write path and the query path. When a user adds an item to their cart, that action is immediately reflected in the next recommendation query. This is the difference between a system that feels responsive and one that feels disconnected from user intent.

**Native Vector Search**

CockroachDB's native `VECTOR` type and C-SPANN distributed index bring approximate nearest-neighbour search directly into the SQL layer. User preferences, product attributes, and any other relevant signals can be represented as vectors and stored alongside operational data in the same database. There is no separate vector store to synchronise, no consistency gap between the operational database and the search index, and no additional infrastructure to operate.

---

## Vector Embeddings for Recommendations

### What Is a Vector Embedding?

A vector embedding is a mathematical representation of an entity — a product, a user, a piece of content — as a list of floating-point numbers. Two entities that are semantically similar map to vectors that are close together in the embedding space. A red running shoe and a blue running shoe will have similar embeddings; a running shoe and a garden chair will not.

The power of embeddings is that they encode meaning learned from data rather than hand-crafted rules. A model trained on millions of product interactions learns that users who buy trail running shoes also buy moisture-wicking socks and hydration vests — even if no rule was written to that effect. The embedding captures those latent associations numerically.

### Embedding Techniques

**Text Embeddings**

Product descriptions, user reviews, and search queries are embedded using pre-trained language models. Approaches range from classical TF-IDF (sparse, interpretable, no semantic understanding) to Word2Vec and GloVe (dense, capture semantic word relationships) to modern transformer models like BERT, MPNet, and sentence-transformers (dense, contextual, state-of-the-art quality).

For product descriptions, `all-mpnet-base-v2` — a BERT variant fine-tuned for semantic similarity — produces 768-dimensional embeddings that capture nuanced meaning across product text.

**Image Embeddings**

Product images are embedded using convolutional neural networks (CNNs). Models like VGG, ResNet, and EfficientNet, pre-trained on ImageNet, extract rich visual features from intermediate or output layers. `Img2Vec` (based on ResNet-18) produces compact 512-dimensional image embeddings that capture visual style, colour, texture, and shape.

**User Embeddings — Two-Tower Networks**

User preferences are modelled with a Two-Tower Neural Network. Two separate network towers process different input types in parallel — one tower processes user data (demographics, behaviour history, explicit preferences), the other processes item data (attributes, embeddings, metadata). The outputs of both towers are projected into a shared embedding space, where the dot product between a user vector and an item vector predicts affinity. This architecture scales to billions of users and items because user and item towers are computed independently and the matching step is a simple vector similarity search.

### Storing Embeddings in CockroachDB

The schema below stores both text and image embeddings for products alongside their operational attributes:

```sql
CREATE TABLE products (
  product_id          INT PRIMARY KEY,
  product_description STRING,
  category            STRING NOT NULL,
  description_vector  VECTOR(768),
  image_vector        VECTOR(512)
);
```

The `VECTOR(n)` type stores a fixed-dimension floating-point array. Both columns participate in vector similarity queries and can be indexed independently.

### Generating Embeddings with Python

```python
from PIL import Image
from img2vec_pytorch import Img2Vec
from sentence_transformers import SentenceTransformer
import psycopg2, numpy as np

img2vec = Img2Vec(cuda=False, model="resnet18")
text_model = SentenceTransformer("all-mpnet-base-v2")

def embed_product(product_id, description, category, image_path, conn):
    # Text embedding
    desc_vector = text_model.encode(description).tolist()

    # Image embedding
    img = Image.open(image_path).convert("RGB")
    img_vector = img2vec.get_vec(img).tolist()

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO products (product_id, product_description, category,
                                  description_vector, image_vector)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (product_id) DO UPDATE
              SET description_vector = EXCLUDED.description_vector,
                  image_vector       = EXCLUDED.image_vector
            """,
            (product_id, description, category,
             desc_vector, img_vector)
        )
    conn.commit()
```

---

## Vector Indexing with C-SPANN

### Why Standard Indexes Don't Work for Vectors

Vectors have no natural total ordering. There is no sense in which a 768-dimensional product embedding comes "before" or "after" another in the way that integers or strings do. Traditional B-tree indexes, which rely on ordered comparisons, cannot help. A brute-force scan computing the distance from the query vector to every row works at small scale but becomes prohibitively slow beyond tens of thousands of items.

Approximate Nearest Neighbour (ANN) indexes address this by trading a small, bounded amount of accuracy for a large gain in performance. They partition the vector space so that similarity search can skip the vast majority of the dataset and focus on the regions most likely to contain the nearest neighbours.

### C-SPANN: CockroachDB's Distributed Vector Index

CockroachDB's vector index, C-SPANN, is built on ideas from Microsoft's SPANN and SPFresh papers, extended to operate natively in a distributed SQL environment. Its core data structure is a **hierarchical K-means tree**: vectors are grouped into partitions based on similarity, each partition has a centroid (its centre of mass), and those centroids are themselves partitioned recursively, forming a tree.

At query time, the search starts at the root and descends through the tree by comparing the query vector to partition centroids. At each level, only the most promising branches are followed. Because the tree is wide and shallow (fanout ≈ 100), an index covering 1 billion vectors requires only five levels, and the root partition can be cached in memory to reduce round-trips.

Key properties that make C-SPANN suitable for production recommendation workloads:

- **No central coordinator** — any node can serve queries or handle inserts without coordination.
- **No large in-memory structures** — the index lives in persistent storage; no warm-up cost, no RAM pressure.
- **Real-time updates** — inserts, updates, and deletes are reflected immediately; no batch rebuild required.
- **Auto-scaling** — as partitions grow, they are automatically split and redistributed across nodes, maintaining linear scalability.
- **RaBitQ quantization** — vectors stored in the index are compressed by ~94% using single-bit quantization per dimension, with a reranking step against full-precision vectors to preserve accuracy.

### Creating the Vector Index

```sql
-- Enable vector indexing (first-time cluster setup)
SET CLUSTER SETTING feature.vector_index.enabled = true;

-- Index by category prefix + image similarity
CREATE VECTOR INDEX ON products (category, image_vector);

-- Index by category prefix + description similarity
CREATE VECTOR INDEX ON products (category, description_vector);
```

The `category` prefix column is critical. It partitions the index by category, so a query for running shoes only searches the running shoes partition rather than the entire catalogue. Performance scales with the number of items in a category, not the total catalogue size.

---

## Vector Similarity Search

### Finding Similar Products

With embeddings stored and indexed, similarity search is a single SQL query:

```sql
-- Find the 10 products most visually similar to a query image, within a category
SELECT product_id, product_description
FROM products
WHERE category = $1
ORDER BY image_vector <-> $2
LIMIT 10;
```

The `<->` operator computes Euclidean distance between the stored vector and the query vector `$2`. CockroachDB supports three distance operators:

| Operator | Metric | Typical use |
|---|---|---|
| `<->` | Euclidean (L2) | Image similarity, spatial proximity |
| `<#>` | Inner Product (IP) | Two-tower model affinity scores |
| `<=>` | Cosine Similarity | Text embeddings, normalised vectors |

### Hybrid Search: Combining Filters and Vectors

The real power comes from combining vector similarity with standard SQL predicates. A recommendation query for a fashion platform might look like:

```sql
SELECT product_id, product_description, price
FROM products
WHERE category    = 'running-shoes'
  AND price       BETWEEN 50 AND 150
  AND in_stock    = true
ORDER BY image_vector <-> $1
LIMIT 10;
```

CockroachDB evaluates the scalar filters first, reducing the candidate set before applying the vector search. This dramatically improves both performance and result quality — the recommendation is not just visually similar, it is also affordable and available.

### Real-Time Personalisation

A full personalisation loop combines user embeddings with product embeddings:

```python
import psycopg2, numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-mpnet-base-v2")

def recommend_for_user(user_id: int, category: str, conn, k: int = 10):
    # Fetch the user's preference embedding (updated in real time from behaviour)
    with conn.cursor() as cur:
        cur.execute(
            "SELECT preference_vector FROM users WHERE user_id = %s",
            (user_id,)
        )
        user_vector = cur.fetchone()[0]

    # Find the k products most aligned with this user's preferences
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT product_id, product_description
            FROM   products
            WHERE  category = %s
            ORDER  BY description_vector <=> %s
            LIMIT  %s
            """,
            (category, user_vector, k)
        )
        return cur.fetchall()
```

Because CockroachDB provides strong consistency, `user_vector` reflects the latest update — including actions taken moments ago in the current browsing session. The recommendation is always fresh.

---

## Scaling to Billions of Items

### Per-Entity Partitioning with Prefix Columns

In multi-tenant platforms — marketplaces, SaaS applications, regional deployments — vectors belong to distinct entities. A query for user A's recommendations should never scan user B's products. CockroachDB handles this with **prefix columns** on the vector index.

```sql
CREATE TABLE products (
  tenant_id    UUID,
  product_id   INT,
  category     STRING,
  image_vector VECTOR(512),
  PRIMARY KEY  (tenant_id, product_id),
  VECTOR INDEX (tenant_id, category, image_vector)
);
```

With `tenant_id` and `category` as prefix columns, the index maintains a separate K-means tree for each `(tenant, category)` combination. A similarity query scoped to a specific tenant and category only touches its own partition — performance is proportional to that tenant's catalogue size, not the global total.

### Multi-Region Deployments

CockroachDB's `REGIONAL BY ROW` feature extends this further. By adding a `crdb_region` column as the leading prefix, each tenant's data is pinned to their home region. A European retailer's product catalogue lives in EU nodes; an American retailer's in US nodes. Vector similarity queries are served locally, with sub-millisecond access to the relevant index partition and no cross-region round-trips.

```sql
ALTER TABLE products SET LOCALITY REGIONAL BY ROW;
```

---

## Conclusion

Recommendation engines have evolved from rule-based heuristics to sophisticated neural systems capable of real-time personalisation at planetary scale. The key ingredients — vector embeddings that encode meaning, approximate nearest-neighbour search that finds similarity at speed, and a consistent data layer that reflects user behaviour instantly — are now all available in a single system.

CockroachDB's native `VECTOR` type and C-SPANN index bring approximate nearest-neighbour search directly into the SQL layer, eliminating the operational complexity of a separate vector store. Its strong consistency guarantees that recommendations are always grounded in the latest user behaviour. Its distributed architecture and prefix-column partitioning ensure that performance scales linearly as the catalogue and user base grow — whether you are serving thousands of users from a single region or tens of millions from every continent.

Regardless of how complex your recommendation strategy is — content-based, collaborative, contextual, or hybrid — CockroachDB provides the infrastructure to deliver accurate, fresh, personalised results at scale.

---

## Resources

- [CockroachDB vector search documentation](https://www.cockroachlabs.com/docs/stable/vector-search.html)
- [C-SPANN: Real-Time Indexing for Billions of Vectors](/2025-11-23-cockroachdb-ai-spann/)
- [Original article: Online Recommendation Engines with CockroachDB](https://www.cockroachlabs.com/blog/recommendation-engines-cockroachdb/)
- [Sentence Transformers — all-mpnet-base-v2](https://huggingface.co/sentence-transformers/all-mpnet-base-v2)
- [Img2Vec — Image embeddings with PyTorch](https://github.com/christiansafka/img2vec)
- [SPANN: Highly-Efficient Billion-scale ANN Search (Microsoft Research)](https://www.microsoft.com/en-us/research/wp-content/uploads/2021/11/SPANN_finalversion1.pdf)
