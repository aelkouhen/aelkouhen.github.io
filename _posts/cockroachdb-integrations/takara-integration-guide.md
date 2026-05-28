---
date: 2026-06-15
layout: post
title: "Integrate CockroachDB with Takara DS1"
subtitle: "A step-by-step guide to using Takara DS1 embeddings with CockroachDB's native vector store and C-SPANN index"
cover-img: /assets/img/cover-takara-integration.jpg
thumbnail-img: /assets/img/share-takara-integration.png
share-img: /assets/img/share-takara-integration.png
tags: [Guide, CockroachDB, takara, ds1, embeddings, vector search, semantic search, C-SPANN]
lang: en
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

[Takara DS1](https://takara.ai/ds1) is a hosted text embedding model designed for low-latency, low-cost vector generation. It returns 512-dimensional L2-normalised vectors and is exposed both as a public HTTPS endpoint and as an AWS SageMaker model. When paired with [CockroachDB](https://www.cockroachlabs.com/) v25.2+, which ships a native `VECTOR` column type and a distributed approximate-nearest-neighbour index called **C-SPANN**, the two form a complete semantic-search stack inside a single transactional SQL database. This guide walks through that integration end to end: provisioning the database, calling the DS1 API to embed text, storing the resulting vectors next to your business data, querying them with both SQL and vector similarity, and benchmarking the result with the open-source [`takara-ai/ds1-cockroach-db-performance`](https://github.com/takara-ai/ds1-cockroach-db-performance) suite.

---

## What Is Takara DS1?

Takara DS1 is a production text embedding model published by [Takara.ai](https://takara.ai/). It maps free-form text to a fixed-size dense vector that captures semantic meaning, suitable for semantic search, retrieval-augmented generation (RAG), clustering, classification, deduplication and recommendation workloads.

### Why DS1?

DS1 is positioned as a low-latency, low-cost alternative to general-purpose embedding APIs. The publicly stated properties matter for an integration with an operational database:

- **512-dimensional output.** Smaller than most general-purpose models (which sit at 768 to 3072), so storage, index size and query distance computation are all cheaper.
- **L2-normalised vectors.** Cosine similarity reduces to a dot product, which is the operation every modern vector index accelerates.
- **GPU-free serving.** DS1 is designed to run on CPU-class hardware, both in Takara's hosted endpoint and on customer-managed SageMaker instances.
- **Two access modes.** A public HTTPS endpoint at `https://tldr.takara.ai/api/search` for prototyping and lightweight workloads, plus an AWS SageMaker deployment for production usage with private networking and IAM-based authentication.
- **Marketed performance.** Takara reports roughly 10x lower latency and 70% lower cost than OpenAI's `text-embedding-3-small` baseline (see [DS1 product page](https://takara.ai/ds1)). The benchmark section of this guide measures DS1 end-to-end against a CockroachDB cluster on a representative workload.

### DS1 API surface

The HTTPS endpoint is intentionally minimal. Embedding one or many texts is a single `GET` request with the text(s) passed as repeated query parameters:

```bash
# Single text
curl "https://tldr.takara.ai/api/search?text=hello%20world"
# → [0.029, -0.013, 0.044, ... 512 floats ...]

# Batch (max 20 texts per request)
curl "https://tldr.takara.ai/api/search?text=first%20doc&text=second%20doc"
# → [[0.029, ...], [0.011, ...]]
```

The response shape changes with the input size: a flat array for a single text, a list of arrays for a batch. Client code that always wants the same shape should wrap the single-text response in a list.

For private or high-throughput deployments, Takara also ships DS1 on the [AWS Marketplace](https://aws.amazon.com/marketplace/pp/prodview-yixnpliihlkee), invokable through `boto3` and `sagemaker-runtime`. The request body in the SageMaker path is `{"inputs": ["text1", "text2", ...]}` with `ContentType: application/json`, and the response is either a list of vectors or a dict with an `"embeddings"` key. The two access modes return semantically equivalent vectors; pick the HTTPS endpoint for the prototyping done in this guide and switch to SageMaker when you need VPC isolation, dedicated throughput or per-request IAM auth.

---

## Why CockroachDB for Vector Workloads?

A semantic search query is rarely "find the nearest 10 by cosine." It is "find the nearest 10 that are in stock, ship to FR, cost less than 100€ and are not in the restricted category." Most pure vector stores force you to round-trip those filters through a separate OLTP system. CockroachDB evaluates both predicates in the same SQL plan, against the same transactional row.

CockroachDB is a particularly good fit for DS1's output because:

- **Native `VECTOR(n)` column type** since v24.2, with a typed dimension that the planner enforces at insert time.
- **C-SPANN distributed ANN index** since v25.2, with no in-memory centralised structure: any node can serve any read, and the index is split, merged and rebalanced like any other CockroachDB range. See the companion post on [real-time vector indexing in CockroachDB](/2025-11-23-cockroachdb-ai-spann/) for the full design.
- **Operator-driven distance functions.** A single C-SPANN index serves cosine (`<=>`), L2 (`<->`) and inner product (`<#>`). Because DS1 returns L2-normalised vectors, cosine and inner product produce the same ranking; pick whichever reads more clearly in your SQL.
- **Transactional freshness.** A product whose description changed two seconds ago must be searchable now, with the new embedding. CockroachDB updates the index incrementally under `SERIALIZABLE` isolation by default. There is no lagging indexer pipeline to babysit.
- **Multi-region survival.** The same table can be regional-by-row, follower-read or globally consistent depending on the SLA, without forking schemas.
- **One operational footprint.** Backups, RBAC, audit, CDC, point-in-time restore: the business data and the embeddings share the same lifecycle.

---

## Takara DS1 + CockroachDB Joint Architecture

The integration has three components on the hot path of every query:

1. **The DS1 endpoint** (HTTPS or SageMaker) that turns a query string into a 512-d vector.
2. **A CockroachDB table** that stores business rows alongside their embedding column.
3. **A C-SPANN index** on that column that serves nearest-neighbour ranking in sub-linear time.

At write time, the application encodes the document text with DS1, then issues a single `INSERT` (or `UPSERT`) that writes the business row and the vector together. CockroachDB transparently maintains the C-SPANN index for the new row.

At read time, the application encodes the user query with DS1, then issues a single `SELECT … ORDER BY embedding <=> $1 LIMIT k` (optionally with `WHERE` predicates). The planner uses C-SPANN to retrieve the candidate set, then applies the predicates and returns the top-k rows. No second store, no application-side fan-out.

---

## Set Up a Joint CockroachDB / Takara DS1 Environment

The remainder of this guide is a runnable walk-through. The example uses an illustrative product catalogue of 25 rows. The catalogue itself is not a Takara artifact: it is a small, semantically diverse sample built for the guide. Swap it for your own data without changing any of the code below.

### Prerequisites

- CockroachDB **v25.2 or later**. Earlier versions support the `VECTOR` column type but not C-SPANN, so reads fall back to sequential scan.
- Python 3.10+ with `httpx`, `psycopg[binary]` and `tenacity`.
- Network access to `https://tldr.takara.ai/api/search`. For the SageMaker variant, an AWS account with the [Takara DS1 marketplace subscription](https://aws.amazon.com/marketplace/pp/prodview-yixnpliihlkee).
- About ten minutes.

### Step 1. Provision a CockroachDB Cluster

For local exploration, a single-node insecure cluster is enough:

```bash
cockroach start-single-node --insecure --listen-addr=localhost:26257 --background
cockroach sql --insecure --url "postgresql://root@localhost:26257/defaultdb"
```

For a multi-node or production deployment, follow the [self-hosted](https://www.cockroachlabs.com/docs/stable/install-cockroachdb.html) or [Cloud](https://cockroachlabs.cloud/) install paths. Either way, enable the vector index feature once per cluster:

```sql
SET CLUSTER SETTING feature.vector_index.enabled = true;
```

### Step 2. Create the Schema

Keep the business columns and the embedding in the same table. This is deliberate: every semantic query benefits from being able to filter on price, stock, category or region in the same plan, and there is no advantage to splitting the embedding into a side table when the lifecycle is identical.

```sql
CREATE DATABASE IF NOT EXISTS shop;
USE shop;

CREATE TABLE products (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku         TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    description TEXT NOT NULL,
    category    TEXT NOT NULL,
    price_eur   DECIMAL(10, 2) NOT NULL,
    in_stock    BOOL NOT NULL DEFAULT true,
    attributes  JSONB NOT NULL DEFAULT '{}'::JSONB,
    embedding   VECTOR(512),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX products_category_idx ON products (category);
CREATE INDEX products_price_idx    ON products (price_eur);

CREATE VECTOR INDEX products_embedding_idx
    ON products (embedding)
    WITH (min_partition_size = 16, max_partition_size = 128);
```

Three intentional choices:

1. **`VECTOR(512)`** matches the dimension that DS1 returns. CockroachDB will reject any insert whose vector length differs.
2. **`JSONB attributes`** holds the long tail of product fields (size, colour, material) without forcing a schema migration. It is fully filterable in SQL alongside the vector predicate.
3. **The C-SPANN index has no explicit metric.** The distance function is chosen at query time by the operator (`<=>` for cosine, `<->` for L2, `<#>` for inner product). The same index serves all three.

### Step 3. Embed and Ingest with the Takara DS1 API

The example dataset is 25 products across five categories. Save it as `products.csv`:

```csv
sku,name,description,category,price_eur,attributes
SHO-001,Trail Runner Pro,Lightweight trail running shoes with grippy outsole and breathable mesh upper for long-distance comfort on uneven ground.,Footwear,129.00,"{""size"": ""42"", ""colour"": ""black""}"
SHO-002,Urban Walker,Cushioned everyday sneakers designed for hours of city walking with arch support and shock absorption.,Footwear,89.00,"{""size"": ""41"", ""colour"": ""grey""}"
SHO-003,Alpine Hiker,Waterproof mid-cut hiking boots with reinforced ankle support and aggressive lugs for rocky terrain.,Footwear,189.00,"{""size"": ""43"", ""colour"": ""brown""}"
SHO-004,Beach Sandal,Quick-drying summer sandals with adjustable straps for warm-weather travel.,Footwear,39.00,"{""size"": ""42"", ""colour"": ""tan""}"
SHO-005,Studio Sneaker,Minimalist white leather sneakers suitable for office and casual wear.,Footwear,109.00,"{""size"": ""44"", ""colour"": ""white""}"
APP-101,Merino Base Layer,Long-sleeve merino wool base layer for cold-weather hiking and skiing; odour-resistant and quick-drying.,Apparel,79.00,"{""size"": ""M"", ""material"": ""merino""}"
APP-102,Rain Shell,Three-layer waterproof and breathable rain jacket with pit zips and a helmet-compatible hood.,Apparel,229.00,"{""size"": ""L"", ""colour"": ""navy""}"
APP-103,Cotton Tee,Soft cotton crew-neck T-shirt for everyday wear.,Apparel,19.00,"{""size"": ""M"", ""colour"": ""white""}"
APP-104,Down Puffer,Lightweight 700-fill goose down jacket for cold dry conditions; packs into its own pocket.,Apparel,259.00,"{""size"": ""M"", ""colour"": ""olive""}"
APP-105,Yoga Leggings,High-waisted four-way-stretch leggings for yoga and low-impact training.,Apparel,59.00,"{""size"": ""S"", ""colour"": ""black""}"
ELE-201,Noise-Cancelling Headphones,Over-ear wireless headphones with active noise cancellation and 30-hour battery life for travel and focused work.,Electronics,349.00,"{""colour"": ""black"", ""bluetooth"": ""5.3""}"
ELE-202,True-Wireless Earbuds,Compact in-ear earbuds with adaptive noise cancellation and a pocketable charging case.,Electronics,229.00,"{""colour"": ""white""}"
ELE-203,Action Camera,4K waterproof action camera with image stabilisation for cycling and water sports.,Electronics,419.00,"{""resolution"": ""4K""}"
ELE-204,E-Reader,High-contrast e-ink reader with weeks of battery life and an adjustable warm front light for night reading.,Electronics,189.00,"{""screen"": ""7in""}"
ELE-205,Mechanical Keyboard,75% layout hot-swappable mechanical keyboard with tactile switches; ideal for long typing sessions.,Electronics,179.00,"{""switches"": ""tactile""}"
HOM-301,French Press,1L double-walled stainless steel French press that keeps coffee hot for hours.,Home,49.00,"{""capacity"": ""1L""}"
HOM-302,Cast-Iron Skillet,Pre-seasoned 26 cm cast-iron skillet for stove and oven cooking; lasts a lifetime.,Home,59.00,"{""diameter"": ""26cm""}"
HOM-303,Memory-Foam Pillow,Contoured memory-foam pillow with a cooling gel layer for side and back sleepers.,Home,69.00,"{""firmness"": ""medium""}"
HOM-304,LED Desk Lamp,Dimmable LED desk lamp with three colour temperatures and a USB charging port.,Home,79.00,"{""colour_temperature"": ""variable""}"
HOM-305,Smart Plug,Wi-Fi smart plug with energy monitoring and voice-assistant integration.,Home,24.00,"{""protocol"": ""wifi""}"
BOO-401,Distributed Systems for Practitioners,A field guide to building resilient distributed systems with real-world incident write-ups and architectural patterns.,Books,39.00,"{""pages"": 412}"
BOO-402,The Cooking Lab Notebook,Modernist techniques explained from first principles for home cooks who like to experiment.,Books,29.00,"{""pages"": 280}"
BOO-403,Mountain Photography Field Guide,Composition and exposure techniques for outdoor and alpine landscape photography.,Books,34.00,"{""pages"": 220}"
BOO-404,Marathon Training Plan,Sixteen-week beginner-to-finisher marathon plan with nutrition and recovery chapters.,Books,19.00,"{""pages"": 180}"
BOO-405,Calm Mornings,Short essays on building a slower, intentional morning routine.,Books,17.00,"{""pages"": 140}"
```

#### A thin client for the DS1 endpoint

The HTTPS endpoint accepts one or many `text=` query parameters per request and returns a flat array (single text) or a list of arrays (batch). The client below standardises the two shapes and retries transient failures with exponential backoff:

```python
# takara_ds1.py
import asyncio
import logging
from typing import List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class TakaraDS1Client:
    """Async client for the Takara DS1 hosted embedding endpoint."""

    def __init__(
        self,
        endpoint: str = "https://tldr.takara.ai/api/search",
        timeout: float = 30.0,
        max_batch_size: int = 20,
    ):
        self.endpoint = endpoint
        self.timeout = timeout
        self.max_batch_size = max_batch_size

    @retry(
        retry=retry_if_exception_type(httpx.HTTPError),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
        reraise=True,
    )
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if len(texts) > self.max_batch_size:
            raise ValueError(
                f"Batch of {len(texts)} exceeds max {self.max_batch_size}; "
                "split before calling embed_batch()."
            )

        params = [("text", t) for t in texts]
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.get(self.endpoint, params=params)
            r.raise_for_status()
            data = r.json()

        # Single text: flat list of floats. Wrap so the caller always sees [[...], ...].
        if texts and len(texts) == 1 and data and isinstance(data[0], float):
            return [data]
        return data

    async def embed(self, text: str) -> List[float]:
        batch = await self.embed_batch([text])
        return batch[0]
```

The 20-text batch limit is the hosted endpoint's. The SageMaker variant accepts larger batches; the [official quickstart](https://ds1.takara.ai/getting-started/quickstart.html) recommends 16 to 32 documents per request as a balance between latency and throughput.

#### Ingest the catalogue

The ingest script reads the CSV, builds the text the model sees (concatenation of name and description: the name alone is too sparse, the description alone loses brand cues), embeds in DS1's preferred batch size, and writes the row plus the vector in a single `INSERT` per chunk.

```python
# ingest_products.py
import asyncio
import csv
import json
import os
from itertools import islice

import psycopg
from takara_ds1 import TakaraDS1Client

DSN = os.environ.get(
    "CRDB_DSN", "postgresql://root@localhost:26257/shop?sslmode=disable"
)
BATCH = 20  # matches DS1's hosted endpoint cap


def chunked(it, size):
    it = iter(it)
    while batch := list(islice(it, size)):
        yield batch


async def main() -> None:
    client = TakaraDS1Client()

    with open("products.csv", newline="") as f:
        rows = list(csv.DictReader(f))

    inserted = 0
    with psycopg.connect(DSN, autocommit=False) as conn, conn.cursor() as cur:
        for batch in chunked(rows, BATCH):
            texts = [f"{r['name']}. {r['description']}" for r in batch]
            vectors = await client.embed_batch(texts)

            args = [
                (
                    r["sku"], r["name"], r["description"], r["category"],
                    r["price_eur"], json.loads(r["attributes"]), v,
                )
                for r, v in zip(batch, vectors)
            ]
            cur.executemany(
                """
                INSERT INTO products
                    (sku, name, description, category, price_eur, attributes, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s::vector)
                ON CONFLICT (sku) DO UPDATE SET
                    name        = EXCLUDED.name,
                    description = EXCLUDED.description,
                    category    = EXCLUDED.category,
                    price_eur   = EXCLUDED.price_eur,
                    attributes  = EXCLUDED.attributes,
                    embedding   = EXCLUDED.embedding,
                    updated_at  = now();
                """,
                args,
            )
            inserted += len(args)
        conn.commit()
    print(f"Upserted {inserted} products.")


if __name__ == "__main__":
    asyncio.run(main())
```

Two implementation details worth flagging:

- **`%s::vector`** is required because CockroachDB's pgwire layer does not currently accept the binary `VECTOR` representation. The driver sends the array as a text literal and the cast happens on the server side. This is the only piece of pgvector-style ergonomics that does not work transparently.
- **No client-side normalisation step.** DS1 returns L2-normalised vectors directly, so cosine similarity is exactly the dot product. There is nothing to do at insert time beyond passing the vector through.

Run the script:

```bash
python ingest_products.py
# Upserted 25 products.
```

### Step 4. Query with SQL and Vector Similarity

The three patterns below cover every realistic shape in semantic search: pure SQL filter, pure vector ranking, and the hybrid that combines them.

#### 4.1 Pure SQL: faceted filter

The classical e-commerce query, untouched by vectors. It is the obvious first thing you would already run on the table, now sitting next to the embedding column.

```sql
SELECT sku, name, price_eur
FROM   products
WHERE  category = 'Footwear'
  AND  price_eur < 150
  AND  in_stock
ORDER  BY price_eur ASC
LIMIT 10;
```

```
     sku      |       name        | price_eur
--------------+-------------------+-----------
  SHO-004     | Beach Sandal      |    39.00
  SHO-002     | Urban Walker      |    89.00
  SHO-005     | Studio Sneaker    |   109.00
  SHO-001     | Trail Runner Pro  |   129.00
```

The plan uses `products_category_idx` and `products_price_idx`. No vector touched.

#### 4.2 Pure semantic search: rank by meaning

The user types *"comfortable shoes for long walks"*. The client embeds the query with DS1, then asks CockroachDB for the ten nearest products by cosine distance. C-SPANN serves the `ORDER BY embedding <=> $1` clause from the vector index without scanning the table.

```python
# search.py
import asyncio
import os
import sys

import psycopg
from takara_ds1 import TakaraDS1Client


async def main() -> None:
    query = sys.argv[1] if len(sys.argv) > 1 else "comfortable shoes for long walks"

    client = TakaraDS1Client()
    qvec = await client.embed(query)

    dsn = os.environ.get(
        "CRDB_DSN", "postgresql://root@localhost:26257/shop?sslmode=disable"
    )
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT sku, name, category, price_eur,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM   products
            ORDER  BY embedding <=> %s::vector
            LIMIT  10;
            """,
            (qvec, qvec),
        )
        for sku, name, cat, price, sim in cur.fetchall():
            print(f"{sim:.3f}  {sku}  [{cat:<11}]  {name}  €{price}")


if __name__ == "__main__":
    asyncio.run(main())
```

```
$ python search.py "comfortable shoes for long walks"
0.681  SHO-002  [Footwear   ]  Urban Walker            €89.00
0.642  SHO-001  [Footwear   ]  Trail Runner Pro        €129.00
0.611  SHO-003  [Footwear   ]  Alpine Hiker            €189.00
0.572  SHO-005  [Footwear   ]  Studio Sneaker          €109.00
0.534  BOO-404  [Books      ]  Marathon Training Plan  €19.00
```

Notice the marathon training plan in fifth place. Nothing in the *name* contains the word "shoes" or "walks", but the description is semantically adjacent. That is the signal a `LIKE` query simply cannot produce.

#### 4.3 Hybrid: vector ranking with SQL constraints

The pattern you will actually deploy. Apply business constraints (`in_stock`, region, price ceiling) as a `WHERE` clause, then order by vector distance. The CockroachDB planner pushes the predicate down so C-SPANN scans only the candidate set that survives the filter.

```sql
PREPARE find_shoes AS
SELECT sku, name, category, price_eur,
       1 - (embedding <=> $1::vector) AS similarity
FROM   products
WHERE  in_stock
  AND  price_eur < 150
  AND  category IN ('Footwear', 'Apparel')
ORDER  BY embedding <=> $1::vector
LIMIT 10;

EXECUTE find_shoes ('[...512 floats from the DS1 endpoint...]');
```

This is the query that makes "vector store inside an OLTP database" worth the trouble. The same row that holds `in_stock` and `price_eur` also holds the vector, so the planner can intersect both predicates without leaving the storage layer.

#### 4.4 Tuning recall vs latency

CockroachDB exposes the per-query beam size as a session variable. Wrap the search in a transaction and set it with `SET LOCAL` so it scopes to that query only:

```sql
BEGIN;
SET LOCAL vector_search_beam_size = 32;   -- default is decided by CockroachDB
SELECT sku, name FROM products
ORDER BY embedding <=> $1::vector LIMIT 10;
COMMIT;
```

Higher beam values increase recall at the cost of latency. Long-tail discovery queries benefit from a higher beam; type-ahead suggestion queries should keep the default.

### Step 5. Benchmark the Integration

The functional walk-through above is enough to prove the pieces fit. To answer "how fast can it go under load?", use the open-source [`takara-ai/ds1-cockroach-db-performance`](https://github.com/takara-ai/ds1-cockroach-db-performance) harness, which exercises exactly the DS1 plus CockroachDB combination on a corpus of short text documents.

> The published reference run uses a corpus of about 7,890 short text posts collected from the [Bluesky](https://bsky.app/) jetstream. The workload shape (text in, 512-d vector out, cosine ANN top-K over a few thousand to a few million rows) matches the product-search workload above. The exact numbers depend on the corpus, the embedding dimension, and the network topology between client, DS1 endpoint and database. Re-run the suite against your own data before quoting numbers in a customer conversation.

Takara's own [single-request bake-off](https://takara.ai/blog/embedding-benchmark-analysis-report) reports DS1 at roughly 28 ms average latency on a dedicated SageMaker `ml.t2.medium`, the lowest of the eight embedding models tested. That report deliberately discards the vectors and excludes storage, retrieval, and concurrency from its scope. The numbers below extend that picture to a concurrent end-to-end shape against CockroachDB, so the DS1 latencies you see here are higher than the isolated single-request figure: they include the public-internet hop to `tldr.takara.ai` and the queueing effect of multiple readers driving the same hosted endpoint.

#### Reference cluster

The published baseline ran on a three-node CockroachDB v26.1.3 cluster in `us-east-1`:

| Component           | Spec                                                     |
| ------------------- | -------------------------------------------------------- |
| Nodes               | 3 × `m6a.2xlarge` (8 vCPU / 32 GB), one per AZ           |
| Storage             | 500 GB gp3 EBS per node                                  |
| CockroachDB version | v26.1.3, insecure mode, public NLB                       |
| Workbench           | `m6a.large` bastion in the same VPC                      |
| Vector index        | C-SPANN on `VECTOR(512)`, cosine                         |
| Embedding service   | Takara DS1 via the hosted HTTPS endpoint                 |
| Dataset             | 7,890 unique Bluesky posts, split into four ingest chunks |

#### Reproducing the run

On the bastion:

```bash
cd /home/ubuntu/ds1-cockroach-db-performance
source runners/benchmark/venv/bin/activate

# 1. Seed a corpus (3 min → ~7-8k posts) from the Bluesky firehose.
cd collector
python -m src.main \
    --enable-file-collection \
    --file-collection-path ../data/initial_load_posts.jsonl \
    --duration 180 --log-level WARNING --no-uri
cd ..
python splitter/splitter.py --chunks 4

# 2. Truncate the embeddings table between runs.
cockroach sql --insecure \
    --url "postgresql://root@<NLB>:26257/bluesky" \
    -e "TRUNCATE posts CASCADE;"

# 3. Graduated load runs: baseline, mid, push.
./run-benchmark.sh --readers 4 --writers 4 --qps 10  --concurrency 8  --duration 1 --skip-init
./run-benchmark.sh --readers 4 --writers 4 --qps 50  --concurrency 8  --duration 2 --skip-init
./run-benchmark.sh --readers 4 --writers 4 --qps 100 --concurrency 16 --duration 2 --skip-init
```

The harness emits per-batch and per-query metrics under `runners/benchmark/results/`, broken down by **vector-search latency** (the time CockroachDB spent serving the `ORDER BY <=>` query) and **DS1 latency** (the embedding round-trip).

> Two patches are required for the numbers below to be reproducible. They live in [PR #2 on the upstream repo](https://github.com/takara-ai/ds1-cockroach-db-performance/pull/2): an `async` rate limiter inside the reader coroutine (the original used blocking `time.sleep`, which silently serialised the consumer), and exposing `--qps RATE` on `run-benchmark.sh` (it was hardcoded to `10.0`). Without those patches the reader spends minutes after `--duration` draining a self-inflicted backlog and the percentiles are unusable.

#### Results

Three graduated runs against the reference cluster, four readers and four writers each, on 2026-05-21 with the PR #2 patches applied. Each run had roughly 8,000 rows already in the `embeddings` table.

| Run        | Target QPS | Achieved QPS | Total P50 / P95 / P99 (ms) | Vector P50 / P95 (ms) | DS1 P50 (ms) | Success rate |
| ---------- | ---------- | ------------ | --------------------------- | --------------------- | ------------ | ------------ |
| Baseline   | 40         | 40           | **70 / 118 / 210**          | 12 / 20               | 58           | 100 %        |
| Mid load   | 200        | 164          | **168 / 273 / 340**         | 28 / 84               | 132          | 100 %        |
| Push       | 400        | 184          | **296 / 488 / 585**         | 42 / 184              | 231          | 100 %        |

Three things stand out:

- **CockroachDB has visible headroom across all three runs.** The vector-search component contributed 12 to 22 % of the end-to-end latency at every load level. Even at the saturated 184 QPS push run, the C-SPANN P95 of 184 ms sits well within budget for an interactive search workload.
- **End-to-end latency is dominated by the embedding step.** This is the expected shape of any text-to-vector pipeline: the embedding service is a network hop, the database read is a local operation. Concurrent calls to the hosted DS1 endpoint cause its P50 to grow from 58 ms (baseline) to 231 ms (push) under the configured load profile. For higher throughput, switch DS1 to the SageMaker variant inside the same VPC as the cluster, which removes the public-internet round-trip and lets you scale the endpoint instance count independently.
- **Saturation follows Little's law.** At the push run, four readers × 16 concurrency / ~295 ms per query gives a theoretical 54 QPS-per-reader ceiling. The run achieved 46. Capacity planning for this stack is therefore a function of the (concurrency, per-query latency) pair, not just raw QPS.

A client-side embedding cache is **not** a fair fix for the API-side latency in this benchmark: the suite reuses only 55 distinct query strings, so caching inflates the numbers without representing real user behaviour. For a real product-search workload with high query diversity, cache hit rate will be much lower and the picture above is the honest one.

#### Reading the numbers for your own workload

For a real-world catalogue, what matters is the ratio between the three latency components (DB query, embedding generation, network) and how they shift as the table grows.

- **At a few dozen rows** (the tutorial above) the C-SPANN index is irrelevant. The query plan falls back to scan and finishes in microseconds.
- **At ~10,000 rows** (the benchmark) the table above is your reference. Expect tens of milliseconds at vector-search P95 and the embedding step to dominate the rest.
- **At ~1M rows** (a mature catalogue) C-SPANN partition counts climb and per-query work grows roughly logarithmically. The companion [C-SPANN deep dive](/2025-11-23-cockroachdb-ai-spann/) shows the index curve under that load.

The single most leveraged knob in all three regimes is **where the embedding model runs**. The cluster has more headroom than the reference numbers suggest. What you saturate first is whatever hop sits between the user, the embedding service and the database.

---

## Operational Tips

A short, opinionated list distilled from running this loop end-to-end:

- **Keep the embedding column in the business table.** The "embeddings live in a side table joined by id" pattern doubles the planner's work for no benefit when the lifecycles are identical.
- **Pin the dimension early.** Changing it later forces a full re-embed and a `DROP / CREATE` of the C-SPANN index. DS1's 512 is a defensible default for catalogues under a few million rows.
- **Tune `vector_search_beam_size` per query class, not globally.** Set `SET LOCAL` inside a transaction, scoped to the query.
- **Treat the embedding endpoint as a capacity-planning dependency.** As the benchmark shows, on most realistic workloads the embedding service decides the QPS ceiling. Plan deployment topology accordingly: SageMaker-in-VPC for high throughput, the hosted endpoint for prototyping.
- **Re-embed on description change, not on schedule.** Add an `embedded_at` column and a background job that re-encodes any row whose `updated_at > embedded_at`. The C-SPANN index updates incrementally.
- **Use retries with exponential backoff at the client.** The DS1 client in this guide uses `tenacity` with four attempts and a 0.5–8 s backoff window, which is a sensible default for any HTTPS embedding API.

---

## What's Next

- [**Real-Time Indexing for Billions of Vectors**](/2025-11-23-cockroachdb-ai-spann/) covers the C-SPANN internals and the scaling curve past a million vectors.
- [**Building RAG Applications with CockroachDB**](/2026-02-20-cockroachdb-ai-rag/) reuses the same vector store for an LLM that grounds its answers in your data.
- The full source for this guide (schema, DS1 client, ingest script, search helper, benchmark recipe) is published alongside the open-source [`takara-ai/ds1-cockroach-db-performance`](https://github.com/takara-ai/ds1-cockroach-db-performance) suite. Patches and re-runs against your own data are very welcome.
