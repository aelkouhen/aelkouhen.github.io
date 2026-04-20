---
layout: post
title: "Building RAG Applications with CockroachDB"
subtitle: "A complete tutorial using LangChain, Vertex AI, and Amazon Bedrock"
cover-img: /assets/img/cover-ai-rag.webp
thumbnail-img: /assets/img/cover-ai-rag.webp
share-img: /assets/img/cover-ai-rag.webp
tags: [cockroachdb-ai, CockroachDB, GenAI, RAG, vector search, LLM, pgvector, LangChain]
comments: true
---

Large Language Models (LLMs) are transforming how we build intelligent applications, but they come with a fundamental limitation: their knowledge is frozen at training time. Ask a model about your internal documentation, your product catalogue, or last week's incident report and it will either refuse or hallucinate a plausible-sounding answer. This phenomenon — confidently wrong — is one of the biggest blockers to putting LLMs in production.

**Retrieval-Augmented Generation (RAG)** solves this by grounding every LLM response in your own, up-to-date, domain-specific data. Instead of relying solely on pre-trained knowledge, a RAG system first queries a database containing your private knowledge base, retrieves the most semantically relevant documents, injects them as context into the prompt, and only then asks the LLM to generate an answer.

This tutorial walks through building a complete, production-ready RAG pipeline backed by **CockroachDB** — covering two popular cloud AI stacks: Google Cloud Platform with Vertex AI, and Amazon Web Services with Amazon Bedrock.

## What is RAG and How Does It Improve LLMs?

Standard LLMs are trained on broad public datasets and lack access to proprietary internal documentation, real-time or post-training events, and domain-specific knowledge such as legal, medical, or financial content.

RAG addresses this with an external retrieval step before generation:

<img src="/assets/img/ai-rag-01.png" alt="RAG concepts — knowledge base, embeddings, vector store, prompt construction and LLM generation" style="width:100%">

The pipeline works as follows: a user submits a question, it is converted into a vector embedding, CockroachDB performs a cosine similarity search over the knowledge base, the top matching documents are injected into the prompt alongside the original question, and the LLM generates a grounded, factual answer.

RAG applications benefit multiple industries. Enterprises use them to let employees rapidly access domain-specific insights without data ever leaving their infrastructure. Financial institutions use them for real-time risk assessment and analytics. E-commerce platforms use them to power context-aware shopping assistants that understand natural language. Customer support teams use them to ground chatbot responses in actual support documentation.

## Why Build RAG on CockroachDB?

### Unified Storage

CockroachDB stores your **source documents, metadata, and vector embeddings in a single database**. There is no synchronization delay between a separate vector store and your operational data — vectors always reflect the current state of your knowledge base.

### Scalability and Resilience

CockroachDB's distributed SQL architecture provides automatic self-healing from node failures, horizontal scale-out, and continuous availability. It is purpose-built to run business-critical applications at scale, eliminating the ceiling you would hit with a single-node PostgreSQL + pgvector deployment.

### PostgreSQL Wire Compatibility

CockroachDB is wire-compatible with PostgreSQL and ships a **pgvector-compatible vector implementation**. Any LangChain integration written for `PGVector` works out of the box — no code changes required.

### Security and Data Governance

Role-Based Access Controls (RBAC), Row-Level Security, and native geo-data placement let you enforce fine-grained permissions over your knowledge base. Sensitive documents can be partitioned by region or user role without changing your application code.

## Architecture Overview

The full RAG application with CockroachDB as the unified backend consists of three independent pipelines running on the same cluster:

<img src="/assets/img/ai-rag-02.png" alt="Full RAG architecture on GCP — Vertex AI embeddings, CockroachDB vector store, LLM cache and conversation history" style="width:100%">

The **ingestion pipeline** loads raw documents (PDFs, CSVs, blog posts, database exports), chunks them, generates vector embeddings, and stores them in CockroachDB. The **retrieval and generation pipeline** takes a user query, embeds it, searches CockroachDB for the most semantically similar chunks, assembles a grounded prompt, and calls the LLM API. The **caching and history layer** stores LLM responses for reuse — using both exact-match and semantic-match caches — and persists conversation history, all in the same CockroachDB cluster.

---

## Part 1: GCP + Vertex AI + CockroachDB

### Install Dependencies

```bash
pip install langchain langchain-community pypdf sentence_transformers tenacity \
    psycopg2-binary sqlalchemy pgvector-sqlalchemy \
    gradio "google-cloud-aiplatform==1.25.0" --upgrade
```

### Imports

```python
from glob import glob
from langchain.document_loaders import PyPDFLoader, DataFrameLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.llms import VertexAI
from langchain.vectorstores.pgvector import PGVector
from langchain.embeddings import VertexAIEmbeddings
from vertexai.preview.language_models import TextGenerationModel
from sqlalchemy import create_engine, text
import vertexai, hashlib, pandas as pd, gradio as gr
```

### Configure GCP and CockroachDB

```python
from getpass import getpass

PROJECT_ID = getpass("GCP Project ID: ")
REGION     = input("GCP Region (e.g. us-central1): ")
vertexai.init(project=PROJECT_ID, location=REGION)

# Connection string from the CockroachDB Cloud Console
COCKROACHDB_URL = getpass("CockroachDB connection string: ")
engine = create_engine(COCKROACHDB_URL)
```

### Load and Chunk Documents

```python
pages = []

# PDFs
loaders = [PyPDFLoader(f) for f in glob("docs/pdf/*.pdf")]
for loader in loaders:
    pages.extend(loader.load())

# Blog posts from CSV
df = pd.read_csv("docs/csv/blogs.csv")
pages.extend(DataFrameLoader(df, page_content_column="text").load())

print(f"Total pages: {len(pages)}")

splitter = RecursiveCharacterTextSplitter(
    chunk_size=5000,
    chunk_overlap=100,
    separators=["\n\n", "\n", "(?<=\\. )", " ", ""],
)
docs = splitter.split_documents(pages)
print(f"Total chunks: {len(docs)}")
```

### Create the CockroachDB Vector Store

LangChain's `PGVector` handles table creation, embedding storage, and index management automatically. CockroachDB's pgvector-compatible layer makes this completely transparent.

```python
embeddings = VertexAIEmbeddings(model="textembedding-gecko@001")

vector_store = PGVector.from_documents(
    documents=docs,
    embedding=embeddings,
    collection_name="knowledge_base",
    connection_string=COCKROACHDB_URL,
)
```

### RAG Generation Pipeline

<img src="/assets/img/ai-rag-03.png" alt="RAG pipeline — raw documents, OpenAI embeddings, CockroachDB vector database, prompt construction and LLM generation" style="width:100%">

```python
generation_model = TextGenerationModel.from_pretrained("text-bison@001")

PROMPT = """You are a helpful virtual assistant. Use the sources below as context \
to answer the question. If you don't know the answer, say so — do not make things up.

SOURCES:
{sources}

QUESTION:
{query}

ANSWER:"""

def rag(query: str, verbose: bool = True) -> str:
    if verbose:
        print("Retrieving relevant sources from CockroachDB...")
    relevant = vector_store.similarity_search_with_score(query, k=3)
    sources  = "\n---\n".join(doc.page_content for doc, _ in relevant)
    return generation_model.predict(
        prompt=PROMPT.format(sources=sources, query=query)
    ).text
```

```python
print(rag("What is a large language model?"))
```

### Standard LLM Cache (CockroachDB)

If the **exact same query** was asked before, return the stored answer without calling the LLM.

```python
with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS llm_cache (
            prompt_hash  STRING PRIMARY KEY,
            prompt       STRING NOT NULL,
            response     STRING NOT NULL,
            created_at   TIMESTAMP DEFAULT current_timestamp()
        )
    """))

def _hash(s): return hashlib.sha256(s.encode()).hexdigest()

def cache_get(q):
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT response FROM llm_cache WHERE prompt_hash = :h"),
            {"h": _hash(q)}
        ).fetchone()
    return row[0] if row else None

def cache_put(q, r):
    with engine.begin() as conn:
        conn.execute(
            text("UPSERT INTO llm_cache (prompt_hash, prompt, response) VALUES (:h,:p,:r)"),
            {"h": _hash(q), "p": q, "r": r}
        )

def standard_llmcache(fn):
    def wrapper(query):
        cached = cache_get(query)
        if cached:
            print("Cache hit (exact match)")
            return cached
        result = fn(query)
        cache_put(query, result)
        return result
    return wrapper

@standard_llmcache
def ask_vertex(query): return rag(query, verbose=False)
```

### Semantic LLM Cache (CockroachDB)

A **rephrased version** of a previous question also returns the cached answer, using vector similarity to detect near-duplicate queries.

```python
semantic_cache = PGVector(
    collection_name="llm_semantic_cache",
    connection_string=COCKROACHDB_URL,
    embedding_function=embeddings,
)
THRESHOLD = 0.85

def sem_get(q):
    res = semantic_cache.similarity_search_with_score(q, k=1)
    if res:
        doc, score = res[0]
        if (1 - score) >= THRESHOLD:
            print(f"Semantic cache hit (similarity={1-score:.3f})")
            return doc.metadata.get("response")
    return None

def sem_put(q, r):
    from langchain.schema import Document
    semantic_cache.add_documents(
        [Document(page_content=q, metadata={"response": r})]
    )

def semantic_llmcache(fn):
    def wrapper(query):
        cached = sem_get(query)
        if cached: return cached
        result = fn(query)
        sem_put(query, result)
        return result
    return wrapper

@semantic_llmcache
def ask_vertex_semantic(query): return rag(query, verbose=False)
```

```python
ask_vertex_semantic("What is data mesh?")
ask_vertex_semantic("Could you explain data products?")  # semantic match → cache hit
```

### Conversation History (CockroachDB)

```python
with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id         UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            prompt     STRING NOT NULL,
            response   STRING NOT NULL,
            created_at TIMESTAMP DEFAULT current_timestamp()
        )
    """))

def add_message(p, r):
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO chat_history (prompt, response) VALUES (:p,:r)"),
            {"p": p, "r": r}
        )

def get_messages(k=5):
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT prompt, response FROM chat_history ORDER BY created_at DESC LIMIT :k"),
            {"k": k}
        ).fetchall()
    return [{"prompt": r[0], "response": r[1]} for r in rows]
```

### Gradio Chat UI

```python
def respond(request, history):
    result = ask_vertex_semantic(request)
    add_message(request, result)
    history.append((request, result))
    return "", history

with gr.Blocks() as demo:
    gr.Markdown("## RAG Chatbot — CockroachDB + Vertex AI")
    chatbot = gr.Chatbot(height=400)
    msg     = gr.Textbox(label="Ask a question")
    btn     = gr.Button("Submit")
    gr.ClearButton(components=[msg, chatbot], value="Clear")
    btn.click(respond, [msg, chatbot], [msg, chatbot])
    msg.submit(respond, [msg, chatbot], [msg, chatbot])

gr.close_all()
demo.launch()
```

---

## Part 2: AWS + Amazon Bedrock + CockroachDB

This section mirrors Part 1 but replaces Vertex AI with **Amazon Bedrock** — Titan Embeddings for vectors and Claude v2 for generation.

<img src="/assets/img/ai-rag-04.png" alt="E-commerce RAG chatbot — product catalogue, OpenAI embeddings, CockroachDB vector database, LangChain application backend" style="width:100%">

### Install Dependencies

```bash
pip install langchain langchain-community pypdf sentence_transformers tenacity \
    psycopg2-binary sqlalchemy pgvector-sqlalchemy \
    boto3 botocore gradio --upgrade
```

### Imports

```python
from langchain.document_loaders import PyPDFLoader, DataFrameLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores.pgvector import PGVector
from langchain.embeddings import BedrockEmbeddings
from langchain.llms import Bedrock
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from sqlalchemy import create_engine, text
import boto3, hashlib, pandas as pd, gradio as gr
```

### Configure AWS and CockroachDB

```python
from getpass import getpass

ACCESS_ID  = getpass("AWS Access Key ID: ")
ACCESS_KEY = getpass("AWS Secret Access Key: ")
REGION     = "us-west-2"

bedrock_runtime = boto3.client(
    "bedrock-runtime",
    region_name=REGION,
    aws_access_key_id=ACCESS_ID,
    aws_secret_access_key=ACCESS_KEY
)

COCKROACHDB_URL = getpass("CockroachDB connection string: ")
engine = create_engine(COCKROACHDB_URL)
```

### Create the CockroachDB Vector Store (Bedrock Embeddings)

```python
bedrock_embeddings = BedrockEmbeddings(
    model_id="amazon.titan-embed-text-v1",
    client=bedrock_runtime
)

# Load and chunk documents — same as Part 1
# (omitted for brevity; see load/chunk section above)

vector_store = PGVector.from_documents(
    documents=docs,
    embedding=bedrock_embeddings,
    collection_name="knowledge_base",
    connection_string=COCKROACHDB_URL,
)
```

### RAG Generation Pipeline

```python
PROMPT = """You are a helpful virtual assistant. Use the sources below as context \
to answer the question. If you don't know the answer, say so.

SOURCES:
{sources}

QUESTION:
{query}

Answer:"""

def rag(query: str, verbose: bool = True) -> str:
    if verbose:
        print("Retrieving relevant sources from CockroachDB...")
    relevant = vector_store.similarity_search_with_score(query, k=3)
    sources  = "\n---\n".join(doc.page_content for doc, _ in relevant)

    llm = Bedrock(model_id="anthropic.claude-v2", client=bedrock_runtime)
    chain = ConversationChain(llm=llm, verbose=False, memory=ConversationBufferMemory())
    return chain.predict(input=PROMPT.format(sources=sources, query=query))
```

```python
print(rag("What is RDI?"))
```

### Standard + Semantic LLM Cache (CockroachDB)

The cache implementation is identical to Part 1 — just swap the embedding client:

```python
# Standard cache — same setup_cache_table(), cache_get(), cache_put() as Part 1

# Semantic cache — use bedrock_embeddings instead of VertexAIEmbeddings
semantic_cache = PGVector(
    collection_name="llm_semantic_cache",
    connection_string=COCKROACHDB_URL,
    embedding_function=bedrock_embeddings,
)

@standard_llmcache
def ask_claude(query): return rag(query, verbose=False)

@semantic_llmcache
def ask_claude_semantic(query): return rag(query, verbose=False)
```

```python
import time
t0 = time.time(); ask_claude("What is data mesh?"); print(f"1st call: {time.time()-t0:.2f}s")
t0 = time.time(); ask_claude("What is data mesh?"); print(f"2nd call: {time.time()-t0:.2f}s")
```

### Conversation History + Gradio UI

```python
# History — same add_message() / get_messages() as Part 1

def respond(request, history):
    result = ask_claude_semantic(request)
    add_message(request, result)
    history.append((request, result))
    return "", history

with gr.Blocks() as demo:
    gr.Markdown("## RAG Chatbot — CockroachDB + Amazon Bedrock")
    chatbot = gr.Chatbot(height=400)
    msg     = gr.Textbox(label="Ask a question")
    btn     = gr.Button("Submit")
    gr.ClearButton(components=[msg, chatbot], value="Clear")
    btn.click(respond, [msg, chatbot], [msg, chatbot])
    msg.submit(respond, [msg, chatbot], [msg, chatbot])

gr.close_all()
demo.launch()
```

---

## What CockroachDB Replaces

| Component | Redis-based approach | CockroachDB |
|---|---|---|
| Vector store | Redis + RediSearch `VECTOR` index | `pgvector` via LangChain `PGVector` |
| Standard LLM cache | Redis HASH + key lookup | SQL table + `UPSERT` |
| Semantic LLM cache | `redisvl.llmcache.semantic.SemanticCache` | `PGVector` collection + cosine threshold |
| Conversation history | Redis LIST (`LPUSH` / `LRANGE`) | SQL table with `ORDER BY created_at` |
| Source docs + metadata | External DB (BigQuery, S3, GCS…) | Same CockroachDB cluster |

CockroachDB consolidates **all five layers** into a single, distributed, strongly consistent database — no separate cluster to operate, no synchronization to manage.

---

## Resources

- [CockroachDB vector search documentation](https://www.cockroachlabs.com/docs/stable/vector-search.html)
- [LangChain PGVector integration](https://python.langchain.com/docs/integrations/vectorstores/pgvector)
- [Amazon Bedrock — model catalogue](https://aws.amazon.com/bedrock/)
- [Google Vertex AI — Generative AI](https://cloud.google.com/vertex-ai/generative-ai/docs)
- [Original RAG notebook — GCP](https://github.com/aelkouhen/redis-vss/blob/main/4-%20Retrieval-Augmented%20Generation%20(RAG)%20-%20GCP.ipynb)
- [Original RAG notebook — AWS](https://github.com/aelkouhen/redis-vss/blob/main/4bis-%20Retrieval-Augmented%20Generation%20(RAG)%20-%20AWS.ipynb)
