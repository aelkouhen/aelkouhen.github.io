---
layout: post
title: "Building RAG Applications with CockroachDB"
subtitle: "From Naive RAG to Agentic RAG — a complete tutorial using LangChain, Vertex AI, and Amazon Bedrock"
cover-img: /assets/img/cover-ai-rag.webp
thumbnail-img: /assets/img/cover-ai-rag.webp
share-img: /assets/img/cover-ai-rag.webp
tags: [cockroachdb-ai, CockroachDB, GenAI, RAG, vector search, LLM, pgvector, LangChain, GraphRAG, AgenticRAG]
comments: true
---

Large Language Models (LLMs) are transforming how we build intelligent applications, but they carry a fundamental limitation: their knowledge is frozen at training time. Ask a model about your internal documentation, your product catalogue, or last week's incident report and it will either refuse or hallucinate a plausible-sounding answer.

**Retrieval-Augmented Generation (RAG)** solves this by grounding every LLM response in your own, up-to-date, domain-specific data. Rather than relying solely on pre-trained knowledge, a RAG system retrieves the most relevant documents from a private knowledge base, injects them as context into the prompt, and only then asks the LLM to generate an answer — precise, trustworthy, and anchored in verified data.

But RAG is not a single technique. In the past two years the field has evolved rapidly from simple vector lookups to sophisticated agent-driven pipelines. This article covers:

1. **The state of the art** — Naive RAG, Graph RAG, and Agentic RAG: how they work, when to use them, and where they fall short.
2. **Why CockroachDB** is an ideal foundation for any of these paradigms.
3. **A complete, working tutorial** implementing a RAG pipeline on CockroachDB using both Google Cloud (Vertex AI) and AWS (Bedrock).

---

## The State of the Art of RAG

<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;">
  <iframe src="https://www.youtube.com/embed/zZFQ4co4HzY" title="CockroachDB for AI/ML: LLMs and RAG" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen style="position:absolute;top:0;left:0;width:100%;height:100%;"></iframe>
</div>

### Naive RAG

Naive RAG is the foundational retrieve-then-generate paradigm. It implements a straightforward three-step pipeline:

1. **Embed the query** — the user's question is converted into a vector using an embedding model.
2. **Retrieve** — cosine similarity search against a vector store returns the top-k most semantically similar document chunks.
3. **Generate** — retrieved chunks are concatenated into the prompt and the LLM produces an answer.

**Strengths:** minimal complexity, fast to deploy, low latency (< 2 s), low cost. Proven effective for straightforward factual lookup. GPT-4 accuracy on medical MCQs improved from 73% to 80% with basic RAG alone.

**Weaknesses:** struggles with multi-hop reasoning, cannot synthesize across many documents, susceptible to hallucination from noisy or contradictory context chunks, no awareness of relationships between entities.

**Use it when:** you are building a prototype, queries are simple (single-concept lookups), cost and latency are primary constraints, or the document corpus is small and well-structured.

**Avoid it when:** queries require connecting information across multiple sources, multi-step reasoning is needed, or the accuracy bar is high for complex, open-ended questions.

---

### Graph RAG

Graph RAG, pioneered by Microsoft Research in their April 2024 paper *"From Local to Global: A Graph RAG Approach to Query-Focused Summarization"*, replaces flat vector chunks with a structured knowledge graph and hierarchical community summaries.

**How it works:**

1. **Graph construction** — an LLM extracts entities (people, places, concepts) and their relationships from source documents, building a knowledge graph.
2. **Community detection** — closely related entities are clustered into communities; the LLM pre-generates a summary for each community.
3. **Query time** — instead of searching raw chunks, the query is matched against community summaries. Partial answers are generated per community then synthesised into a final comprehensive response.

**Strengths:** excels at global sensemaking and synthesis across large corpora (1M+ tokens). Microsoft testing showed 72–83% comprehensiveness vs. baseline RAG. Multi-hop reasoning and relationship tracing are first-class capabilities.

**Weaknesses:** high latency (20–24 s average), high indexing cost ($20–500 per corpus), computationally expensive to rebuild when source data changes frequently.

**Use it when:** comprehensiveness matters more than speed, the corpus has rich interconnected relationships (legal, medical, research literature), or enterprise knowledge discovery across many documents is the goal.

**Avoid it when:** real-time responses are required, the budget is tight, the corpus is small, or source data changes frequently.

---

### Agentic RAG

Agentic RAG embeds autonomous AI agents into the pipeline. The LLM acts as an intelligent orchestrator that plans, reasons iteratively, invokes tools, and adapts its retrieval strategy in real time based on intermediate results.

**How it works:**

1. **Intent and planning** — the agent analyses the request, decomposes it into sub-questions, and identifies required tools (vector search, web search, code execution, APIs).
2. **Iterative retrieval** — the agent executes multiple retrieval rounds, inspects intermediate results, and refines subsequent queries.
3. **Tool use and validation** — specialised tools are invoked; the agent critiques its own outputs and self-corrects.
4. **Synthesis** — final answer assembled from all reasoning steps and retrieved evidence.

**Strengths:** handles complex multi-step reasoning, integrates real-time data via web search and APIs, self-correcting, ideal for exploratory and discovery tasks. Accuracy of 75–90%+ on complex queries.

**Weaknesses:** high latency (10–30+ s), high cost (multiple LLM calls per query), difficult to debug, non-deterministic behaviour, overkill for simple tasks.

**Use it when:** multi-step reasoning is essential, real-time data access is required, the task is exploratory, or human-in-the-loop validation is acceptable.

**Avoid it when:** response time < 2 s, query volume is high with a tight budget, behaviour must be deterministic, or queries are simple lookups.

---

### Comparison: Choosing the Right RAG Paradigm

| | **Naive RAG** | **Graph RAG** | **Agentic RAG** |
|---|---|---|---|
| **Complexity** | Low | High | Very High |
| **Latency** | < 2 s | 20–24 s | 10–30 s |
| **Cost per query** | Low | High | Very High |
| **Reasoning depth** | Single-hop | Multi-hop (structured) | Multi-hop + branching |
| **Accuracy on complex Q** | 60–80% | 72–83% | 75–90%+ |
| **Real-time data** | No | No | Yes |
| **Best for** | Prototypes, simple lookup | Enterprise synthesis | Complex research tasks |
| **Worst for** | Complex multi-doc queries | Speed-sensitive apps | High-volume, low-latency |
| **Failure mode** | Missing context | Slow, expensive | Cascading reasoning errors |

---

## Why Build RAG on CockroachDB?

### Unified Storage

CockroachDB stores **source documents, metadata, vector embeddings, LLM caches, and conversation history in a single database**. There is no synchronisation delay between a separate vector store and your operational data.

### Scalability and Resilience

CockroachDB's distributed SQL architecture provides automatic self-healing from node failures, horizontal scale-out, and continuous availability — purpose-built for business-critical workloads at scale.

### PostgreSQL Wire Compatibility

CockroachDB is wire-compatible with PostgreSQL and ships a **pgvector-compatible vector implementation**. Any LangChain integration written for `PGVector` works out of the box.

### Security and Data Governance

RBAC, Row-Level Security, and native geo-data placement enforce fine-grained permissions over your knowledge base without changing application code.

---

## Application Architecture

<img src="/assets/img/ai-rag-crdb-architecture.png" alt="RAG application architecture — chatbot UI, FastAPI service, CockroachDB vector store" style="width:100%">

The application consists of three layers:

- **Presentation layer** — a Gradio chatbot UI for user interaction.
- **Application layer** — a FastAPI service handling query embedding, retrieval orchestration, caching, and history management.
- **Data layer** — CockroachDB storing vectors, source documents, metadata, LLM cache, and conversation history.

<img src="/assets/img/ai-rag-crdb-dataflow.png" alt="RAG data flow with CockroachDB — user question, vectorisation, similarity search, context injection, LLM response" style="width:100%">

The data flow: user submits a question → it is vectorised → CockroachDB performs similarity search → top-k relevant documents are retrieved → context is injected into the prompt → the LLM generates a grounded answer.

---

## Tutorial: Building the RAG Pipeline

<img src="/assets/img/ai-rag-naive.png" alt="Naive RAG pipeline — Ingestion (documents, chunker, embedding model, CockroachDB vector store) and Retrieval & Generation (user query, embedding, similarity search, context + LLM)" style="width:100%">

The tutorial is structured in two parts. Part 1 uses Google Cloud's **Vertex AI** (PaLM embeddings + text-bison generation). Part 2 uses Amazon Web Services' **Bedrock** (Titan Embeddings + Claude v2). The CockroachDB layer and LangChain pipeline are identical between the two — only the embedding and LLM clients change.

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

loaders = [PyPDFLoader(f) for f in glob("docs/pdf/*.pdf")]
for loader in loaders:
    pages.extend(loader.load())

df = pd.read_csv("docs/csv/blogs.csv")
pages.extend(DataFrameLoader(df, page_content_column="text").load())

splitter = RecursiveCharacterTextSplitter(
    chunk_size=5000,
    chunk_overlap=100,
    separators=["\n\n", "\n", "(?<=\\. )", " ", ""],
)
docs = splitter.split_documents(pages)
print(f"{len(docs)} chunks ready for indexing")
```

### Create the CockroachDB Vector Store

`PGVector` handles table creation, embedding storage, and index management automatically.

<img src="/assets/img/ai-rag-graph.png" alt="Graph RAG pipeline — Indexing phase (source docs, LLM entity extraction, knowledge graph, community clusters and summaries) and Retrieval & Generation phase (vector DB, community summaries, graph DB traversal, LLM synthesis)" style="width:100%">

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

<img src="/assets/img/ai-rag-agentic.png" alt="Agentic RAG pipeline — Planning (agent planner, sub-questions, tool selector), Multi-source Retrieval (vector DB, web search, APIs, code executor), and Iterative Reasoning (LLM reasoner, draft answer, self-correction loop, evaluator, final answer)" style="width:100%">

```python
generation_model = TextGenerationModel.from_pretrained("text-bison@001")

PROMPT = """You are a helpful virtual assistant. Use the sources below as context \
to answer the question. If you don't know the answer, say so.

SOURCES:
{sources}

QUESTION: {query}

ANSWER:"""

def rag(query: str, verbose: bool = True) -> str:
    relevant = vector_store.similarity_search_with_score(query, k=3)
    sources  = "\n---\n".join(doc.page_content for doc, _ in relevant)
    return generation_model.predict(
        prompt=PROMPT.format(sources=sources, query=query)
    ).text
```

### Standard LLM Cache (CockroachDB)

Exact-match cache: if the same query was asked before, return the stored answer without calling the LLM.

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
            print("Cache hit — exact match")
            return cached
        result = fn(query)
        cache_put(query, result)
        return result
    return wrapper

@standard_llmcache
def ask_vertex(query): return rag(query, verbose=False)
```

### Semantic LLM Cache (CockroachDB)

Rephrased versions of a previous question also return the cached answer, using vector similarity to detect near-duplicate queries.

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

<img src="/assets/img/ai-rag-04.png" alt="E-commerce RAG chatbot — product catalogue embeddings, CockroachDB vector store, LangChain application backend" style="width:100%">

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

### Create the CockroachDB Vector Store

```python
bedrock_embeddings = BedrockEmbeddings(
    model_id="amazon.titan-embed-text-v1",
    client=bedrock_runtime
)

vector_store = PGVector.from_documents(
    documents=docs,          # same chunked docs as Part 1
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

QUESTION: {query}

Answer:"""

def rag(query: str, verbose: bool = True) -> str:
    relevant = vector_store.similarity_search_with_score(query, k=3)
    sources  = "\n---\n".join(doc.page_content for doc, _ in relevant)
    llm      = Bedrock(model_id="anthropic.claude-v2", client=bedrock_runtime)
    chain    = ConversationChain(llm=llm, verbose=False, memory=ConversationBufferMemory())
    return chain.predict(input=PROMPT.format(sources=sources, query=query))
```

### Caching and History

The cache and history implementations are **identical to Part 1** — only the embedding client changes. Replace `embeddings` with `bedrock_embeddings` in the semantic cache initialisation:

```python
semantic_cache = PGVector(
    collection_name="llm_semantic_cache",
    connection_string=COCKROACHDB_URL,
    embedding_function=bedrock_embeddings,   # Titan instead of Gecko
)

@standard_llmcache
def ask_claude(query): return rag(query, verbose=False)

@semantic_llmcache
def ask_claude_semantic(query): return rag(query, verbose=False)
```

### Gradio Chat UI

```python
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

## GCP Vertex AI vs AWS Bedrock: Choosing Your Cloud AI Stack

Both integrations produce identical results from CockroachDB's perspective — the vector store, caching, and history layers are unchanged. The decision comes down to your cloud strategy, model preferences, and compliance requirements.

| | **GCP Vertex AI** | **AWS Bedrock** |
|---|---|---|
| **Embedding model** | `textembedding-gecko@001` (768 dims) | `amazon.titan-embed-text-v1` (1536 dims) |
| **Generation model** | `text-bison@001` / Gemini | `anthropic.claude-v2` / Claude 3 |
| **Vector dimensionality** | 768 | 1536 |
| **LangChain class** | `VertexAIEmbeddings` | `BedrockEmbeddings` |
| **Auth mechanism** | GCP service account / ADC | AWS IAM access keys / role |
| **Best for** | GCP-native stacks, BigQuery integration | AWS-native stacks, multi-model choice |
| **Model variety** | Google models (PaLM, Gemini) | AI21, Anthropic, Cohere, Meta, Amazon |
| **Pricing model** | Per-character input/output | Per-token input/output |
| **Compliance** | GDPR, HIPAA, SOC 2 | GDPR, HIPAA, SOC 2, FedRAMP |
| **Latency** | ~200–400 ms (embedding) | ~300–600 ms (embedding) |

**Choose Vertex AI if** you are already on GCP, use BigQuery as a data source, or need tight Gemini integration. **Choose Bedrock if** you are on AWS, want access to multiple third-party foundation models (Anthropic, Cohere, Meta) from a single API, or need FedRAMP compliance.

Both are equally well-suited to any of the three RAG paradigms described above — Naive, Graph, or Agentic — with CockroachDB serving as the unified data layer across all of them.

---

## Resources

- [CockroachDB vector search documentation](https://www.cockroachlabs.com/docs/stable/vector-search.html)
- [Tutorial: Augment your AI use case with RAG on CockroachDB](https://www.cockroachlabs.com/blog/tutorial-rag-with-cockroachdb/)
- [LangChain PGVector integration](https://python.langchain.com/docs/integrations/vectorstores/pgvector)
- [From Local to Global: Microsoft GraphRAG paper (arXiv 2404.16130)](https://arxiv.org/abs/2404.16130)
- [Agentic RAG survey (arXiv 2501.09136)](https://arxiv.org/abs/2501.09136)
- [Amazon Bedrock model catalogue](https://aws.amazon.com/bedrock/)
- [Google Vertex AI — Generative AI](https://cloud.google.com/vertex-ai/generative-ai/docs)
- [Original RAG notebook — GCP](https://github.com/aelkouhen/redis-vss/blob/main/4-%20Retrieval-Augmented%20Generation%20(RAG)%20-%20GCP.ipynb)
- [Original RAG notebook — AWS](https://github.com/aelkouhen/redis-vss/blob/main/4bis-%20Retrieval-Augmented%20Generation%20(RAG)%20-%20AWS.ipynb)
