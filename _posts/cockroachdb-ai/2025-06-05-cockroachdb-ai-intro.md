---
layout: post
title: "Getting Started with GenAI Using CockroachDB"
cover-img: /assets/img/cover-ai-intro.webp
thumbnail-img: /assets/img/cover-ai-intro.webp
share-img: /assets/img/cover-ai-intro.webp
tags: [cockroachdb-ai, CockroachDB, GenAI, vector embeddings, vector search, LLM, pgvector, RAG]
comments: true
---

Information today is generated and consumed in unprecedented magnitudes. With every click, swipe, and transaction, massive amounts of data are collected, waiting to be harnessed for insights, decision-making, and innovation. Today, more than 80% of the data that organizations generate is unstructured – and the amount of this data type will only grow in the coming decades.

Unstructured data is high-dimensional and noisy, making it more challenging for traditional databases to analyze and interpret using traditional methods.

## Let's go inside GenAI

Enter the world of Generative AI (GenAI) – a groundbreaking technology that's revolutionized how we store, query, and analyze data. Behind the magic of GenAI lies a deep stack of technology, data structures, and mathematical innovations.

One of the most foundational — yet often overlooked — components is the use of vector embeddings. These high-dimensional representations allow GenAI models to understand, organize, and generate meaningful content. To make sense of these embeddings at scale, we need specialized systems like vector databases. These databases are not just an evolution of their predecessors; they represent an extraordinary leap in data management.

This is the first of several articles I'm writing that will take you on a journey into vector databases. As the Sr. Partner Solutions Architect at Cockroach Labs, I routinely engineer distributed database deployments within diverse data ecosystems. I love sharing what I've learned in the process, such as with my [Mainframe to Distributed SQL article series](/2025-02-05-mainframe-to-distributed-sql-part-6/).

Throughout, we'll explore the GenAI realm, its foundational principles, applications and how the resilient infrastructure offered by CockroachDB represents an exciting addition to this field.

This article explores the journey from generative AI to vector embeddings, vector search, and the underlying architecture that powers it all. We'll unpack complex concepts like vector search, embedding models, and data consistency, showing how they solve real-world problems in search, classification, and recommendations.

Whether you're a data enthusiast, a business leader seeking a competitive edge, or a developer curious about the next frontier in data storage and retrieval, this article is your gateway to understanding the power and potential of CockroachDB as a vector database.

## What Is Generative AI?

Generative AI represents a class of artificial intelligence algorithms capable of creating original content – text, images, music, code, or even videos. Unlike traditional AI systems that make predictions based on fixed outputs and/or can merely analyze or classify existing data, generative models can produce new and contextually relevant outputs based on prompts and inputs.

<img src="/assets/img/ai-intro-01.png" alt="AI Taxonomy" style="width:100%">

{: .mx-auto.d-block :}
**AI Taxonomy**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

These systems learn the underlying probability distributions of the data they're trained on and then generate new examples that resemble the original data without directly copying it. The "generative" part comes from sampling these learned distributions to produce new outputs. This ability to "create" rather than "recognize" represents a significant advancement in the field of AI.

This process isn't random — it's guided by mathematical representations of data called Vector Embeddings, and a set of retrieval techniques called Vector Similarity (VecSim).

### Vector Embeddings

Generative AI models don't "understand" language the way humans do. To understand human text (also called natural language), Large Language Models (LLMs) are Natural Language Processing (NLP) models designed to understand and generate natural language in advanced ways. These models are typically based on neural networks. They can process large amounts of text data to perform various tasks, such as machine translation, text generation, sentiment analysis, text comprehension, question answering, and more.

However, LLMs need a way to represent, navigate, and search this text. This is where the concept of Vector comes in. Vectors are mathematical representations of data points where each vector dimension (embeddings) corresponds to a specific feature or attribute of the data — to determine relationships and generate plausible continuations of input prompts.

Think of vector embeddings as GPS coordinates for meaning. Just as GPS helps locate a physical place, embeddings help locate the meaning of content in a multidimensional space, enabling similarity comparison, clustering, and retrieval.

<img src="/assets/img/ai-intro-02.png" alt="Vector embeddings as GPS coordinates for meaning" style="width:100%">

{: .mx-auto.d-block :}
**Vector embeddings as GPS coordinates for meaning**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

In machine learning and natural language processing, text, images, or other unstructured data can be represented as vector embeddings – each embedding captures an attribute of this data. For example, a product image can be represented as a vector, where each embedding represents a specific characteristic of this product (brand, color, shape, size…, etc.).

Vectors efficiently represent raw unstructured data that can be high-dimensional and sparse (e.g., natural languages, images, audio…). Vector embeddings solve a fundamental problem in AI: how to represent non-numerical data (like text or images) in a form that algorithms can process mathematically. This transformation allows:

- Capturing semantics - The meaning and nuances of data are preserved
- Performing calculations - We can measure similarities, perform conceptual additions or subtractions
- Reducing dimensionality - Complex concepts are represented in a compact and efficient manner

Thanks to advances in deep learning, model providers such as OpenAI, Anthropic, HuggingFace, Cohere, and other data scientists around the world have built models — called transformers — capable of transforming almost any data "entity" into its vector representation. Next, using mathematical approaches, these representations are compared in a vector search space to measure how closely related two pieces of data are.

<img src="/assets/img/ai-intro-03.png" alt="Transforming Unstructured Data to Vector Embeddings" style="width:100%">

{: .mx-auto.d-block :}
**Transforming Unstructured Data to Vector Embeddings**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

### Vector Similarity Search

Vector search, also known as "similarity search," finds items in a dataset that are closest to a query based on their embeddings.

Vector similarity metrics enable the measurement of similarity or dissimilarity between data points. Unlike keyword-based search, which relies on exact matches, vector search captures [semantic relationships](https://www.cockroachlabs.com/blog/semantic-search-using-cockroachdb/) between data points. Words or phrases with similar meanings (semantics) are represented as vectors that are close to each other in the embedding space. This enables models to understand and reason about the meaning of words and text and solves the following problems:

- Ambiguity in queries: Users don't need precise terms; vector search understands intent.
- Multimodal data: It handles text, images, or audio by comparing embeddings across formats.
- Scalability: It efficiently processes large datasets, like e-commerce catalogs or media libraries.

<img src="/assets/img/ai-intro-04.png" alt="Distance (similarity) between vectors in a vector search space" style="width:100%">

{: .mx-auto.d-block :}
**Distance (similarity) between vectors in a vector search space**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

### ChatGPT: How it works

In fact, when you submit a prompt into an LLM (let's consider a ChatGPT prompt), first it's broken down into tokens (units smaller than words, often subwords). Each token is then converted into an initial embedding vector. This initial layer of embeddings captures basic lexical information.

The Transformer architectures that underpin these models use attention mechanisms to enrich these initial embeddings with contextual information. At each neural network layer, the embeddings are refined to incorporate more context, reflecting deeper semantic understanding and creating what we call "contextual embeddings." The final layer outputs new embeddings, which are decoded into words or actions.

When generating text, the LLM uses the contextual embeddings of previous tokens to predict the most probable next token. This process happens by:

- Transforming the contextual embedding into a probability distribution over the vocabulary
- Sampling this distribution to select the next token
- Calculating a new embedding for this token
- Repeating the process to generate a coherent sequence

<img src="/assets/img/ai-intro-05.png" alt="How do LLMs work?" style="width:100%">

{: .mx-auto.d-block :}
**How do LLMs work?**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

This intelligent use of embeddings allows LLMs to produce text that maintains coherence, respects grammatical rules, and remains relevant to the context. It enables powerful use cases like semantic search and classification, where it's essential to find not just exact matches but also conceptually similar content. By leveraging vector similarity, systems can understand and retrieve relevant information even when the exact wording or structure differs.

Vector similarity search also powers applications like recommendation engines, allowing personalized recommendations based on deep similarity to a user's past interests. This delivers personalized and context-aware experiences beyond simple filters or rules (e.g., [Netflix](https://www.cockroachlabs.com/blog/netflix-dbaas-roachfest24-recap/) suggesting shows).

It can also help categorize content, detect spam, analyze sentiment, retrieve images (finding visually similar photos), and map data into a space where similar items group naturally, even without labels. VSS relies on distance metrics like [cosine similarity](https://www.geeksforgeeks.org/cosine-similarity/) or [Euclidean distance](https://www.geeksforgeeks.org/euclidean-distance/) to compare embeddings and determine how alike they are.

GenAI systems use Vector Similarity Search (VSS) as a mathematical backbone to retrieve content based on semantic similarity rather than exact data matching: When a user enters a query, it is converted into an embedding. The system then finds the most similar vectors — and thus the most relevant results — from a Feature Store or, commonly, a Vector Database.

<img src="/assets/img/ai-intro-06.png" alt="Vector databases" style="width:100%">

{: .mx-auto.d-block :}
**Vector databases**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

## Storage and Retrieval of Embeddings

### Why do vector databases matter?

Vector databases are designed to store unstructured data as vectors and to handle a large volume of vector embeddings. They use specialized indexing techniques, like approximate nearest neighbor (ANN) search, to quickly find stored vectors similar to a query vector. For example, in a recommendation system, a vector database can retrieve products with embeddings closest to a user's profile in milliseconds, even across millions of items.

Vector databases must also support hybrid search, combining vector similarity with traditional filters and enhancing flexibility. Just imagine that you are looking for a specific product by its image using a vector similarity search, but you want to enhance your search by adding some other search parameters like your current location or a price range.

Without vector databases, managing embeddings would be slow and resource-intensive, limiting the scalability of GenAI systems. Their ability to store, index, and retrieve embeddings efficiently makes them indispensable for modern AI workflows.

### Challenges of OLTP databases in handling vector embeddings

Vector search, once a niche capability confined to specialized vector databases, is rapidly becoming a commodity feature in traditional databases. As the use of embeddings expands across applications like semantic search, recommendation engines, and AI-driven insights, more developers and organizations expect their traditional databases to directly support operations like nearest neighbor search, hybrid search and cosine similarity.

However, storing and retrieving embeddings efficiently is critical for traditional databases. It often requires workarounds, like serializing vectors into blobs, which complicates retrieval. Enterprise-grade AI applications handle vectors that are high-dimensional, often containing hundreds or thousands of dimensions, making them challenging to manage at scale. This volume poses considerable challenges such as:

- Efficient storage of large quantities of high-dimensional vectors
- Fast retrieval for nearest neighbors
- Continuous updating of vector collections

Moreover, Online Transaction Processing (OLTP) databases, like Oracle or SQL Server, present significant scaling limitations for the billions of vectors needed in modern AI applications, making them the worst choice for AI workloads. In fact, as datasets grow, dynamic scalability becomes critical to maintain performance without rearchitecting the GenAI system.

Another key issue is [metadata management](https://www.cockroachlabs.com/glossary/distributed-db/metadata-management/), where systems need to associate vectors with rich metadata to enable hybrid search and advanced filtering. Additionally, vector indices can be memory-intensive, leading to high resource consumption. Frequent updates, such as adding new vectors, can also trigger costly index rebuilds or maintenance, impacting latency and availability.

### The Critical Role of Data Consistency in GenAI

Data consistency is the foundation of reliable AI, particularly for GenAI. Inconsistent data—mismatched embeddings, outdated vectors, or corrupted inputs—can lead to poor model performance, generating irrelevant or incorrect outputs.

For LLMs, consistency ensures that training and inference data align. If embeddings used during training differ from those at inference (e.g., due to preprocessing errors), the model may misinterpret inputs, reducing accuracy. In recommendation systems, inconsistent user or item embeddings can result in irrelevant suggestions, eroding trust.

GenAI applications often involve real-time data, such as user interactions or live content. Vector databases must maintain consistency across updates to ensure embeddings reflect the latest information. For example, in a news recommendation system, failing to update article embeddings promptly could lead to outdated suggestions.

Consistency also matters for multimodal GenAI, where text, images, and audio embeddings must align. Inconsistent data pipelines can cause mismatches, like pairing an image with the wrong caption. Robust data governance, versioned embeddings, and atomic updates in vector databases help mitigate these risks, ensuring GenAI delivers reliable, high-quality results.

## CockroachDB as a Vector Database

Integrating CockroachDB in your technological stack is a strategic move for modernizing legacy systems and preparing for the demands of AI-driven applications. With its built-in Vector datatype, the strong consistency, and a 99.999% SLA in its cloud offering, [CockroachDB](https://www.cockroachlabs.com/product/overview/) delivers the performance and availability required for today's next-gen workloads.

To meet this demand, CockroachDB's [Vector Search implementation](https://www.cockroachlabs.com/blog/vector-search-pgvector-cockroachdb/) uses the same interface as that of PostgreSQL pgvector's and aims to be compatible with its API. This evolution eliminates the need for separate vector databases in many use cases, enabling teams to leverage familiar tools while adding AI-native capabilities — effectively blurring the lines between classical OLTP systems and modern AI infrastructure.

Additionally, CockroachDB's limitless horizontal scalability allows you to store and query hundreds of millions or even billions of vector embeddings without sacrificing performance or reliability, which are essential for real-time GenAI applications. These fast queries are made possible with our implementation of Cockroach-SPANN, an internally developed distributed vector indexing algorithm that was [made available in v25.2](https://www.cockroachlabs.com/blog/cockroachdb-252-performance-vector-indexing/). As your data footprint expands, CockroachDB automatically scales out — eliminating the need for manual sharding or complex reconfiguration while ensuring seamless performance and operational simplicity.

Beyond CockroachDB's resilience and data domiciling capabilities, its distributed architecture enables powerful, SQL-native operations on vector data — bringing analytical depth to your generative AI applications.

For example, if you store items with associated store locations and product images (encoded as vectors) in a single table, you can create a secondary index on the store location column to pre-filter data before performing a Vector Search. This means that instead of scanning the entire dataset, the system first narrows down the search to relevant locations — such as "Casablanca" — and then applies vector similarity search only within that subset. This hybrid search approach significantly improves query performance and resource efficiency, making it easier to build intelligent, high-performance AI applications at scale using familiar SQL syntax.

As a highly resilient distributed database, CockroachDB offers the technical foundations to store, index, and query vector embeddings. It allows developers to store vectors as easily as structured relational data. Then, the Vector Search capabilities provide advanced indexing and search capabilities required to perform low-latency search at scale, typically ranging from tens of thousands to hundreds of millions of vectors distributed across a cluster of machines.

<img src="/assets/img/ai-intro-07.png" alt="CockroachDB as a Vector Database" style="width:100%">

### How does Semantic Similarity Search work?

Let's take the following example. It depicts how Semantic Similarity Search works in the context of Large Language Models (LLMs). Following are three different sentences we want to represent in a vector search space – each one is transformed into a vector embedding using the `sentence_transformers` library (from [HuggingFace](https://huggingface.co/sentence-transformers)):

- `That is a happy girl`
- `That is a very happy person`
- `I love dogs`

Packages like HuggingFace's `sentence_transformers` provide easy-to-use models for tasks like semantic similarity search, visual search, and many others. To create embeddings with these models, only a few lines of Python are needed:

```python
from sentence_transformers import SentenceTransformer

# 1. Load a pretrained Sentence Transformer model.
# This model encodes text into a vector of 384 dimensions.
model = SentenceTransformer("all-MiniLM-L6-v2")

# The sentences to encode
sentences = [
  "That is a happy girl",
  "That is a very happy person",
  "I love dogs"
]
```

```python
# 2. Calculate embeddings by calling model.encode()
vectors = model.encode(sentences).astype(np.float32)
```

First we need to create the table schema before inserting data on it:

```sql
CREATE TABLE sentences IF NOT EXISTS (
    text String,
    text_vector VECTOR(384)
);
```

Next, let's store these sentences and their respective embeddings in CockroachDB:

```python
import psycopg2

# Connect to CRDB
with psycopg2.connect(crdb_cluster_endpoint) as conn:
   # Open a cursor to perform database operations
   with conn.cursor() as cursor:
       data = [(sentence, vector) for sentence, vector in zip(sentences, vectors)]
       for d in data:
         cursor.execute("INSERT INTO sentences (text, text_vector) VALUES (%s, %s)", d)

        # Make the changes to the database persistent
        conn.commit()
```

The graph below highlights the position of these example sentences in 2-dimensional vector search space relative to one another. This is useful in order to visually gauge how effectively our embeddings represent the semantic meaning of text.

<img src="/assets/img/ai-intro-08.png" alt="Sentences represented as vectors" style="width:100%">

{: .mx-auto.d-block :}
**Sentences represented as vectors**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Let's assume that we want to compare the three sentences above to a new one: `That is a happy boy`. We need to use the same model we used for the previous sentences, then create the vector embedding for the query sentence.

```python
# create the vector embedding for the query sentence
query_sentence = "That is a happy boy"
query_vector = model.encode(query_sentence).astype(np.float32)
```

Once the vectors are loaded into CockroachDB, queries can be formed and executed for all kinds of similarity-based search tasks. For this, you need to leverage distance metrics which provide a reliable and measurable way to calculate the similarity or dissimilarity of two vectors.

There exist many distance metrics you can choose depending on your use case, but currently, only the operators `<->` [Euclidean Distance](https://en.wikipedia.org/wiki/Euclidean_distance) (L2), `<#>` [Inner Product](https://en.wikipedia.org/wiki/Inner_product_space) (IP), and `<=>` [Cosine Similarity](https://en.wikipedia.org/wiki/Cosine_similarity) are available in CockroachDB.

<img src="/assets/img/ai-intro-09.png" alt="Distance metrics" style="width:100%">

{: .mx-auto.d-block :}
**Distance metrics**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Below is a query that returns the most similar sentences to the new one (`That is a happy boy`), sorted by distance (cosine similarity):

```python
# Connect to an existing database
with psycopg2.connect(crdb_url) as conn:

   # Open a cursor to perform database operations
   with conn.cursor() as cursor:
       # Query the database and obtain data as Python objects.
       cursor.execute('SELECT text, 1 - (text_vector <=> ' + query_vector + ') AS cosine_similarity FROM sentences ORDER BY cosine_similarity DESC')
```

Let's take a look at this query:

```sql
SELECT text, 1 - (text_vector <=> query_vector) AS cosine_similarity FROM sentences ORDER BY cosine_similarity DESC;
```

In this query, we ask the CockroachDB vector search engine to calculate the cosine similarity between the query vector and each one of the vectors already stored in the sentences table, so we can determine how similar the sentences are to each other.

The sentence `That is a happy boy` is the most similar sentence to `That is a happy girl` (76% of similarity) and `That is a very happy person` (70% of similarity), but very far from `I love dogs` (only 24%).

<img src="/assets/img/ai-intro-10.png" alt="Cosine similarity results" style="width:100%">

Running this calculation between our query vector and the other three vectors in the plot above, we can determine how the sentences are semantically similar to each other.

<img src="/assets/img/ai-intro-11.png" alt="Calculating distance (similarity) between vectors" style="width:100%">

{: .mx-auto.d-block :}
**Calculating distance (similarity) between vectors**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

The instructions above represent a brief overview of how to use and retrieve vector embeddings and demonstrate the building blocks for Vector Similarity Search using CockroachDB. You can try this out with [the notebook referenced here](https://colab.research.google.com/drive/12O82LhPIWNx_3d__QNERqsGlZBaZJqZz#scrollTo=6ffPF-SldwXk) (install [Google Colab](https://colab.research.google.com/) to open).

CockroachDB's support for the pgvector API enables smooth integration with popular AI frameworks like LangChain, Bedrock and Hugging Face, making it simple to incorporate real-time data into your machine learning workflows. This seamless compatibility positions CockroachDB as a powerful backend for Retrieval-Augmented Generation (RAG) systems, delivering fresh, scalable and consistent data to enrich AI-generated content, all that in the same database you already use for your relational and transactional data.

At Cockroach Labs, we've also actively developed support for native vector indexing in the latest release of CockroachDB, v25.2. This enhancement enables the database to efficiently narrow the search space during similarity queries, significantly accelerating execution times and reducing computational overhead.

With vector indexing, CockroachDB further improves the performance of AI and machine learning workloads, reinforcing its position as a powerful, scalable solution for managing large-scale, data-intensive AI applications. So stay tuned for the next articles in this series! We will delve further into the advanced capabilities of CockroachDB as a vector database.
