---
layout: post
title: Data & Redis series - part 9
subtitle:  RedisCover Redis in Vector Similarity Search
thumbnail-img: https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEhGgH1gaxs8Mj60SkhlTyPDnFW5UzQaMn9GXWLbV2VoVe62C9azRjXYaEqx8AOdJCQYQIewqxJkDrSgX6BqqGEJr8iHgziuHPwA0wwurxSpvnlQ-lJNi0haib0KHz_FoBhJGri4kRHgv6hPNhSXiw2sqN21lXDlCClmwfW9aR3BttNTlavTZhJpXpGS5vU
share-img: https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEgKgxMltMyijfUL8HoJmjfpCrvLlmymW6U4FSdtHobnGARzJsxURry7UsXNsl4DGIVA5IIwW0Lz8Lx3qOxmc-wfGFsIndteJyjsOAkDksi4iMuALAg7KzR6SBPQPA-h-5ZxIqTz_RZkjNT_SOsCVH3XvwaXJFW64xcOssRGVY-Iq6cLBCz1WmpQQiIPnZw
tags: [ChatGPT,Cosine,embeddings,Hugging Face,KNN,LLM,Redis,RediSearch,similarity search,transformers,vector database]
comments: true
---

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://github.com/aelkouhen/redis-vss/blob/main/1-%20Text%20Vector%20Search%20-%20BigData.ipynb)

In today's data-driven world, information is generated and consumed at an unprecedented pace. With every click, swipe, and transaction, massive amounts of data are collected, waiting to be harnessed for insights, decision-making, and innovation. Today, more than 80% of the data organizations generate is unstructured, and the amount of this kind of data is expected to grow in the coming decades. Unstructured data is high-dimensional and noisy, making it more challenging for traditional databases to analyze and interpret using traditional methods.

Enter the world of Vector Databases – a groundbreaking technology that is revolutionizing how we store, query, and analyze data. These databases are not just an evolution of their predecessors; they represent a quantum leap in the field of data management. In this blog post, we embark on a journey into the realm of vector databases, exploring their fundamental principles, applications, and how Redis Enterprise represents an exciting addition to this field.

Whether you're a data enthusiast, a business leader seeking a competitive edge, or a developer curious about the next frontier in data storage and retrieval, this post is your gateway to understanding the power and potential of Redis as a vector database.

## 1. Vector embeddings

Vectors are mathematical representations of data points where each vector dimension (embeddings) corresponds to a specific feature or attribute of the data. For example, a product image can be represented as a vector where each element represents the characteristic of this product (color, shape, size...). Similarly, a product description can be transformed into a vector where each element represents the frequency or presence of a specific word or term. 

Vectors are an efficient way to represent raw data, especially unstructured ones (e.g., natural languages, images, audio...), that can be high-dimensional and sparse. Vector embeddings provide a more efficient and compact representation of this data, making it easier to process and analyze.

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEgQ7mCfTqlGfPJPgcQO57u1k2oViOk0P77xV89rO3btNhP0bVRbT617ZhWHzQT5ELjKV_gjArWLrVL3tXxyu2qmnl_bHlg1I9oTxeOHsnPoBWSXy301-6PvqaKGAOn0DFeTEwJaB1nnanm9GvXhFIB9ZlRYDyt_1WguNXep10j2NYduLZBvChei8kufqso){: .mx-auto.d-block :} *Vector Embeddings.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Vector embeddings automatically extract relevant features from data, reducing the need for manual feature engineering. They enable the measurement of similarity or dissimilarity between data points. In recommendation systems, for instance, user-item embeddings help identify similar users or products, improving recommendations.

For example, in the Natural Language Processing (**NLP**) field, vector embeddings capture semantic relationships between data points. Words or phrases with similar meanings are represented as vectors that are close to each other in the embedding space. This enables models to understand and reason about the meaning of words and text.

## 2. Redis as a Vector Database

A vector database is a type of database that stores unstructured data as vector embeddings. Machine Learning algorithms are what is enabling this transformation of unstructured data into numeric representations (vectors) that capture meaning and context, benefiting from advances in natural language processing and computer vision.

The key feature of a vector database is Vector Similarity Search (VSS). It is the process of finding data points that are similar to a given query vector in a vector database. 

As a versatile data store, Redis offers the technical foundations to store, index, and query vector embeddings. It allows developers to store vectors as easily as Hashes or JSON documents. Then, the Vector Similarity Search (VSS) capability is built as a new feature of the RediSearch module. It provides advanced indexing and search capabilities required to perform low-latency search in large vector spaces, typically ranging from tens of thousands to hundreds of millions of vectors distributed across a number of machines.

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEgKgxMltMyijfUL8HoJmjfpCrvLlmymW6U4FSdtHobnGARzJsxURry7UsXNsl4DGIVA5IIwW0Lz8Lx3qOxmc-wfGFsIndteJyjsOAkDksi4iMuALAg7KzR6SBPQPA-h-5ZxIqTz_RZkjNT_SOsCVH3XvwaXJFW64xcOssRGVY-Iq6cLBCz1WmpQQiIPnZw){: .mx-auto.d-block :} *Redis as a Vector database.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

## 3. RediSearch and Vector Similarity Search

Vector Similarity Search focuses on finding out how alike or different two vectors are. Once you have created your embeddings and stored them in Redis, you must create an index data structure to enable intelligent similarity search that balances search speed and search quality. Redis supports two types of vector indexing: 

*   **FLAT**: A brute force approach using the K-Nearest Neighbor (KNN) search through all possible vectors. This indexing is simple and effective for small datasets or cases where interpretability is important;
*   **Hierarchical Navigable Small Worlds (HNSW):** An approximate search (ANN) that yields faster results with lower accuracy. This is more suitable for complex tasks that require capturing intricate patterns and relationships, especially with large datasets.

The choice between Flat and HNSW depends only on your usage, data characteristics, and requirements. Indexes only need to be created once and will automatically re-index as new hashes are stored in Redis. Both indexing methods have the same mandatory parameters: Type, Dimension, and Distance Metric. 

### A. Storing Vectors

Below, an example of semantic similarity is shown that outlines the vector embeddings created with the **sentence_transformers** library (from [HuggingFace](https://huggingface.co/sentence-transformers)).

Let’s take the following sentences:
– `That is a happy girl`
– `That is a very happy person`
– `I love dogs`

Each of these sentences can be transformed into a vector embedding. Below, a simplified representation highlights the position of these example sentences in 2-dimensional vector space relative to one another. This is useful in order to visually gauge how effectively our embeddings represent the semantic meaning of text.

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEhgQ1qOn2DeB_pt5jeqieetRym_3S8HsEmvUni6bkzPXcwtn5uFlInciuiuSJQNpkSTZZ1BhWXWiekEDBKoFx9kwzVV5FogwvmfKVlhT-rEX0JIumZ7a7Ho-2Ph21BAm5HUGyjvWLP7-QaRiUlg3BWJM3IKJm5CrrAYu2rBhjtJzwkuHrox02M3s8ooR6g){: .mx-auto.d-block :} *Sentences are presented as vectors.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Packages like **sentence_transformers**, also from HuggingFace, provide easy-to-use models for tasks like semantic similarity search, visual search, and many others. To create embeddings with these models, only a few lines of Python are needed:

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

Then, let's store these vector embeddings in Redis:

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

### B. Indexing Vectors

We need to create an index on these stored vectors to allow search, querying, and retrieval. For this, you need to choose the relevant distance metric for your application.

Distance metrics provide a reliable and measurable way to calculate the similarity or dissimilarity of two vectors. There are many Distance metrics you can use (figure below), but currently, only the [Euclidean](https://en.wikipedia.org/wiki/Euclidean_distance) (L2), [Inner Product](https://en.wikipedia.org/wiki/Inner_product_space) (IP), and [Cosine Similarity](https://en.wikipedia.org/wiki/Cosine_similarity) metrics are available in Redis.

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEheKTicWPBFMSoK53LHeSvikn9ZOklHrGfUYk0DXjDJXOrCaUd4Oeb_Nuam_xrKlTj8JvNgk2nQn9FYeKEYVE9aylJKDmNLUjiKz0uht6jOVC_HhI-qqFKGHhBDmOVddPrZsqCELjFe8H2f3vAbe1DRF5KGega_Gr4Y-DNOjAVHF2Wahsmu1BMA0wDl){: .mx-auto.d-block :} *Distance Metrics.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Below is an example of creating an index with `redis-py` after loading the vectors into Redis.

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

Indexes only need to be created once and will automatically re-index as new hashes are stored in Redis. After vectors are loaded into Redis, and the index has been created, queries can be formed and executed for all kinds of similarity-based search tasks.

All the existing RediSearch features, like text, tag, and geographic-based search, can work together with the VSS capability. This is called _hybrid queries_. With hybrid queries, traditional search functionality can be used as a pre-filter for vector search, which can help bind the search space.

### C. Querying Vectors

Assume we want to compare the three sentences above to a new one: `That is a happy boy`. 

First, we create the vector embedding for the query sentence.

{% highlight python linenos %}
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# create the vector embedding for the query
query_embedding = model.encode("That is a happy person")
{% endhighlight %}

Once the vectors are loaded into Redis, and the index is created, queries can be formed and executed for all kinds of similarity-based search tasks.

Below is an example of a query with **[redis_py](https://github.com/redis/redis-py)** that returns the 3 most similar sentences to the new one (`That is a happy boy`), sorted by relevance score (cosine distance).

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

Running this calculation between our query vector and the other three vectors in the plot above, we can determine how similar the sentences are to each other.

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEg8eSKJpAEasHPS_mdp0aCJWFdV9NLS2OhSgkNW-tpt8_1oPXDIXIdlYA4KcBqzA0IWOjbKh5dWQ7dHFXlZ5kVzT6rI8sa2lgGP0zlBgE2yizDNgvXQkpHjq_SRdRLxWhVgDXgwImD9fRxtQHid51O4oIMtCaczKwP46HHEDT5Lj0ROgdHZ_GBJDa_jCgI){: .mx-auto.d-block :} *Calculating Cosine distance between vectors.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}  

As you might have assumed, `That is a very happy person` is the most similar sentence to `That is a happy boy` and `That is a happy girl`, and very far from `I love dogs`. This example captures only one of many possible use cases for vector embeddings: _Semantic Similarity Search_.

The instructions above are a brief overview to demonstrate the building blocks for Vector Similarity Search using Redis. You can try this out with the notebook referenced in the head of this post. Stay tuned for the next blog posts that will talk about the advanced capabilities of Redis and VSS.

## Summary
Redis supports diverse capabilities that can significantly reduce application complexity while delivering consistently high performance, even on a large scale. Because it is an in-memory database, Redis provides very high throughput with sub-millisecond latency, using the lowest possible computational resources.

With the Vector Similarity Search feature, Redis unlocks several real-time business-revolutionizing applications based on similarity and distance calculation. In the following posts, we will see how you can use these building blocks for different applications.

## References
* [Vector-Similarity-Search from Basics to Production](https://mlops.community/vector-similarity-search-from-basics-to-production/), Sam Partee.
* [VSS documentation](https://redis.io/docs/stack/search/reference/vectors/), redis.io
