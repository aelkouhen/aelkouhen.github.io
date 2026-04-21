---
layout: post
lang: fr
title: "Construire des applications RAG avec CockroachDB"
subtitle: "Du RAG naïf au RAG agentique — un tutoriel complet avec LangChain, Memori, GCP Vertex AI et Amazon Bedrock"
cover-img: /assets/img/cover-ai-rag.webp
thumbnail-img: /assets/img/cover-ai-rag.webp
share-img: /assets/img/cover-ai-rag.webp
tags: [Artificial Intelligence, CockroachDB, GenAI, RAG, Memori, LangChain, Vertex AI, AWS Bedrock]
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

Les grands modèles de langage (LLMs) transforment la façon dont nous construisons des applications intelligentes, mais ils présentent une limitation fondamentale : leur connaissance est figée au moment de l'entraînement. Posez à un modèle une question sur votre documentation interne, votre catalogue de produits ou le rapport d'incident de la semaine dernière, et il refusera soit de répondre, soit hallucinations une réponse plausible.

**La Génération Augmentée par Récupération (RAG)** résout ce problème en ancrant chaque réponse du LLM dans vos propres données à jour et spécifiques à votre domaine. Plutôt que de s'appuyer uniquement sur les connaissances pré-entraînées, un système RAG récupère les documents les plus pertinents dans une base de connaissances privée, les injecte comme contexte dans le prompt, et seulement ensuite demande au LLM de générer une réponse — précise, fiable et ancrée dans des données vérifiées.

Mais le RAG n'est pas une technique unique. Au cours des deux dernières années, le domaine a rapidement évolué, passant de simples recherches vectorielles à des pipelines sophistiqués pilotés par des agents. Cet article couvre :

1. **L'état de l'art** — RAG naïf, Graph RAG et RAG agentique : comment ils fonctionnent, quand les utiliser et où ils montrent leurs limites.
2. **Pourquoi CockroachDB** est une fondation idéale pour l'un ou l'autre de ces paradigmes.
3. **Un tutoriel complet et fonctionnel** implémentant un pipeline RAG sur CockroachDB utilisant à la fois Google Cloud (Vertex AI) et AWS (Bedrock).

---

## L'état de l'art du RAG

Le RAG a évolué à travers trois générations distinctes, chacune répondant aux limitations de la précédente. Le **RAG naïf** a établi le modèle fondamental de récupération puis génération — simple, rapide et efficace pour les recherches directes, mais fragile lorsque les requêtes nécessitent de connecter des faits à travers plusieurs documents. Le **Graph RAG** a remplacé les morceaux de vecteurs plats par un graphe de connaissances structuré, permettant une compréhension globale sur de grands corpus au prix d'une latence plus élevée et d'une indexation plus coûteuse. Le **RAG agentique** est allé encore plus loin, intégrant des agents autonomes qui planifient, récupèrent de manière itérative, invoquent des outils externes et se corrigent — échangeant la prévisibilité contre la capacité à traiter des tâches de raisonnement multi-étapes véritablement ouvertes.

Choisir entre eux n'est pas une question de « plus récent est meilleur » — c'est une question d'adéquation entre le paradigme et la complexité de la requête, le budget de latence et l'enveloppe de coût de votre cas d'usage spécifique. Les sections ci-dessous détaillent chaque approche pour que vous puissiez faire ce choix en toute confiance.

<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;">
  <iframe src="https://www.youtube.com/embed/zZFQ4co4HzY" title="CockroachDB for AI/ML: LLMs and RAG" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen style="position:absolute;top:0;left:0;width:100%;height:100%;"></iframe>
</div>

### RAG naïf

Le RAG naïf est le paradigme fondamental de récupération puis génération. Il se déroule en deux phases distinctes — un **pipeline d'ingestion hors ligne** (étapes 1 à 3) et un **pipeline de récupération et génération en ligne** (étapes 4 à 7) — connectés par un magasin vectoriel partagé.

1. **Découpage** — les documents bruts (PDFs, CSVs, HTML) sont divisés en segments de texte de taille fixe avec chevauchement par un découpeur.
2. **Encodage** — chaque segment est converti en un vecteur de haute dimension par un modèle d'embedding qui capture sa signification sémantique.
3. **Indexation** — les vecteurs résultants sont stockés et indexés dans le Vector Store CockroachDB, prêts pour la recherche par similarité.
4. **Encodage de la requête** — la question de l'utilisateur est passée à travers le même modèle d'embedding pour produire un vecteur de requête.
5. **Recherche par similarité** — CockroachDB compare le vecteur de requête à tous les vecteurs de segments indexés en utilisant la distance cosinus et retourne les k correspondances les plus proches.
6. **Assemblage du contexte** — les segments récupérés sont combinés avec la requête originale en un seul bloc de contexte.
7. **Génération** — le LLM reçoit le contexte + la requête comme prompt et produit une réponse ancrée.

<img src="/assets/img/ai-rag-naive.png" alt="Naive RAG pipeline — Ingestion (documents, chunker, embedding model, CockroachDB vector store) and Retrieval & Generation (user query, embedding, similarity search, context + LLM)" style="width:100%">
{: .mx-auto.d-block :}
**Pipeline RAG naïf — Ingestion (documents, découpeur, modèle d'embedding, Vector Store CockroachDB) et Récupération et Génération (requête utilisateur, embedding, recherche par similarité, contexte + LLM)**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

- **Points forts :** complexité minimale, déploiement rapide, faible latence (< 2 s), faible coût. Prouvé efficace pour les recherches factuelles simples. La précision de GPT-4 sur les QCM médicaux est passée de 73 % à 80 % avec le RAG de base seul.

- **Faiblesses :** difficultés avec le raisonnement multi-sauts, incapacité à synthétiser sur de nombreux documents, susceptible aux hallucinations à partir de segments de contexte bruités ou contradictoires, aucune connaissance des relations entre entités.

- **À utiliser quand :** vous construisez un prototype, les requêtes sont simples (recherches à concept unique), le coût et la latence sont des contraintes primaires, ou le corpus de documents est petit et bien structuré.

- **À éviter quand :** les requêtes nécessitent de connecter des informations provenant de plusieurs sources, un raisonnement multi-étapes est nécessaire, ou la barre de précision est élevée pour des questions complexes et ouvertes.

---

### Graph RAG

Le Graph RAG, pionnier de Microsoft Research dans leur article d'avril 2024 *"From Local to Global: A Graph RAG Approach to Query-Focused Summarization"*, remplace les segments de vecteurs plats par un graphe de connaissances structuré et des résumés de communautés hiérarchiques. Le pipeline se déroule en deux phases — **indexation hors ligne** (étapes 1 à 5) et **récupération et génération en ligne** (étapes 6 à 10).

1. **Découpage** — les documents sources sont divisés en segments de texte, comme dans le RAG naïf.
2. **Extraction d'entités** — un LLM lit chaque segment et identifie les entités nommées (personnes, lieux, concepts) et les relations entre elles.
3. **Graphe de connaissances** — les entités et relations extraites sont assemblées en un graphe stocké dans une base de données graphe dédiée.
4. **Clustering de communautés** — un algorithme de détection de communautés regroupe les entités étroitement liées en clusters.
5. **Résumés de communautés** — le LLM pré-génère un résumé en langage naturel pour chaque cluster ; les résumés sont stockés à la fois dans la base de données graphe et dans une base de données vectorielle pour une recherche rapide.
6. **Encodage de la requête** — la requête utilisateur est convertie en vecteur.
7. **Recherche vectorielle** — la base de données vectorielle est interrogée pour trouver les résumés de communautés les plus sémantiquement pertinents.
8. **Parcours du graphe** — pour chaque communauté correspondante, la base de données graphe est parcourue pour récupérer les relations d'entités et les preuves à grain fin.
9. **Synthèse par le LLM** — tous les résumés récupérés et le contexte du graphe sont transmis au LLM pour composer une réponse complète.
10. **Réponse** — la réponse finale est ancrée à la fois dans des preuves au niveau des communautés et au niveau des entités sur l'ensemble du corpus.

<img src="/assets/img/ai-rag-graph.png" alt="Graph RAG pipeline — Indexing phase (source docs, LLM entity extraction, knowledge graph, community clusters and summaries) and Retrieval & Generation phase (vector DB, community summaries, graph DB traversal, LLM synthesis)" style="width:100%">
{: .mx-auto.d-block :}
**Pipeline Graph RAG — Phase d'indexation (documents sources, extraction d'entités LLM, graphe de connaissances, clusters et résumés de communautés) et phase Récupération et Génération (base de données vectorielle, résumés de communautés, parcours de la base de données graphe, synthèse LLM)**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

- **Points forts :** excelle dans la compréhension globale et la synthèse sur de grands corpus (1M+ tokens). Les tests Microsoft ont montré une compréhensibilité de 72 à 83 % par rapport au RAG de base. Le raisonnement multi-sauts et le traçage des relations sont des capacités de premier ordre.

- **Faiblesses :** haute latence (20 à 24 s en moyenne), coût d'indexation élevé (20 à 500 $ par corpus), coûteux en calcul à reconstruire lorsque les données sources changent fréquemment.

- **À utiliser quand :** la complétude est plus importante que la vitesse, le corpus a des relations interconnectées riches (juridique, médical, littérature de recherche), ou la découverte de connaissances d'entreprise sur de nombreux documents est l'objectif.

- **À éviter quand :** des réponses en temps réel sont requises, le budget est serré, le corpus est petit ou les données sources changent fréquemment.

---

### RAG agentique

Le RAG agentique intègre des agents IA autonomes dans le pipeline. Le LLM agit comme un orchestrateur intelligent qui planifie, raisonne de manière itérative, invoque des outils et adapte sa stratégie de récupération en temps réel en fonction des résultats intermédiaires. Le pipeline se déroule sur trois axes — **Planification** (étapes 1 à 3), **Récupération multi-sources** (étapes 4 à 5) et **Raisonnement itératif et auto-correction** (étapes 6 à 9).

1. La **requête utilisateur** arrive au **planificateur d'agent**, qui analyse l'intention et la portée.
2. Le planificateur décompose la requête en **sous-questions**, chacune adressable par une source de récupération ou un outil spécifique.
3. Le **sélecteur d'outils** achemine chaque sous-question vers le backend approprié.
4. La récupération s'exécute en parallèle sur quatre sources : **base de données vectorielle** (CockroachDB pour la recherche sémantique), **recherche web** (en temps réel), **APIs et outils** (données structurées) et **exécuteur de code** (calculs programmatiques).
5. Tous les résultats sont agrégés dans un paquet de **contexte récupéré** transmis à l'axe de raisonnement.
6. Le **raisonnneur LLM** traite le contexte et produit une **ébauche de réponse**.
7. Une porte de décision demande : **« Besoin de plus d'informations ? »** — si OUI, l'agent boucle vers l'étape 3 avec une sous-question affinée et relance la récupération.
8. Si NON, l'**agent évaluateur** évalue la qualité : **« Pertinent et complet ? »** — si NON, la réponse est affinée et réévaluée.
9. Si OUI, la **réponse finale** est retournée à l'utilisateur.

<img src="/assets/img/ai-rag-agentic.png" alt="Agentic RAG pipeline — Planning (agent planner, sub-questions, tool selector), Multi-source Retrieval (vector DB, web search, APIs, code executor), and Iterative Reasoning (LLM reasoner, draft answer, self-correction loop, evaluator, final answer)" style="width:100%">
{: .mx-auto.d-block :}
**Pipeline RAG agentique — Planification (planificateur d'agent, sous-questions, sélecteur d'outils), Récupération multi-sources (base de données vectorielle, recherche web, APIs, exécuteur de code) et Raisonnement itératif (raisonnneur LLM, ébauche de réponse, boucle d'auto-correction, évaluateur, réponse finale)**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

- **Points forts :** gère le raisonnement multi-étapes complexe, intègre des données en temps réel via la recherche web et les APIs, auto-correctif, idéal pour les tâches exploratoires et de découverte. Précision de 75 à 90 %+ sur les requêtes complexes.

- **Faiblesses :** haute latence (10 à 30+ s), coût élevé (plusieurs appels LLM par requête), difficile à déboguer, comportement non déterministe, excessif pour les tâches simples.

- **À utiliser quand :** le raisonnement multi-étapes est essentiel, l'accès aux données en temps réel est requis, la tâche est exploratoire, ou la validation humaine dans la boucle est acceptable.

- **À éviter quand :** le temps de réponse est < 2 s, le volume de requêtes est élevé avec un budget serré, le comportement doit être déterministe, ou les requêtes sont de simples recherches.

---

### Comparaison : choisir le bon paradigme RAG

| | **RAG naïf** | **Graph RAG** | **RAG agentique** |
|---|---|---|---|
| **Complexité** | Faible | Élevée | Très élevée |
| **Latence** | < 2 s | 20–24 s | 10–30 s |
| **Coût par requête** | Faible | Élevé | Très élevé |
| **Profondeur de raisonnement** | Mono-saut | Multi-sauts (structuré) | Multi-sauts + branchement |
| **Précision sur questions complexes** | 60–80 % | 72–83 % | 75–90 %+ |
| **Données en temps réel** | Non | Non | Oui |
| **Idéal pour** | Prototypes, recherche simple | Synthèse d'entreprise | Tâches de recherche complexes |
| **À éviter pour** | Requêtes multi-documents complexes | Applications sensibles à la vitesse | Volume élevé, faible latence |
| **Mode d'échec** | Contexte manquant | Lent, coûteux | Erreurs de raisonnement en cascade |

---

## Pourquoi construire un RAG sur CockroachDB ?

### Stockage unifié

CockroachDB stocke les **documents sources, les métadonnées, les vector embeddings, les caches LLM et l'historique des conversations dans une seule base de données**. Il n'y a pas de délai de synchronisation entre un magasin vectoriel séparé et vos données opérationnelles.

### Scalabilité et résilience

L'architecture SQL distribuée de CockroachDB fournit une auto-réparation automatique à partir des défaillances de nœuds, une mise à l'échelle horizontale et une disponibilité continue — conçue spécifiquement pour les charges de travail critiques à grande échelle.

### Vector Store natif — Pas d'infrastructure supplémentaire

CockroachDB est livré avec un type `VECTOR` natif soutenu par l'**index distribué C-SPANN** — conçu spécifiquement pour les systèmes distribués, pas seulement un wrapper pgvector. Capacités clés qui comptent pour les charges de travail RAG :

- **Index C-SPANN** — un arbre K-means hiérarchique stocké dans la couche clé-valeur de CockroachDB ; pas de goulot d'étranglement sur un seul nœud, pas de coût de démarrage, divisions automatiques à mesure que les données croissent (voir [Indexation en temps réel pour des milliards de vecteurs](/2025-11-23-cockroachdb-ai-spann/)).
- **Filtrage avancé des métadonnées** — filtrez par n'importe quelle colonne avec la similarité vectorielle dans une seule requête SQL.
- **Multi-tenant avec colonnes de préfixe** — chaque utilisateur ou tenant obtient sa propre partition d'index ; les performances sont proportionnelles aux données de ce tenant, pas au corpus total.

### Intégration LangChain dédiée

Le package `langchain-cockroachdb` fournit une intégration asynchrone de première classe avec `AsyncCockroachDBVectorStore` — supportant l'ingestion de documents, la recherche par similarité et le filtrage des métadonnées, entièrement compatible avec n'importe quelle chaîne ou agent LangChain. Installez-le avec :

```bash
pip install langchain-cockroachdb
```

Dès qu'une application a besoin de récupérer des données, de maintenir un contexte conversationnel ou de raisonner sur plusieurs étapes, la quantité de code de liaison personnalisé augmente rapidement. LangChain fournit un moyen structuré d'orchestrer ces workflows — et `langchain-cockroachdb` fait de CockroachDB une source vectorielle plug-and-play pour n'importe quel pipeline LangChain.

### Sécurité et gouvernance des données

Le RBAC, la Sécurité au Niveau des Lignes et le placement géo-natif des données appliquent des permissions granulaires sur votre base de connaissances sans modifier le code de l'application.

---

## Les outils

### LangChain

[LangChain](https://python.langchain.com/) est un framework open-source pour construire des applications alimentées par des grands modèles de langage. Plutôt que d'écrire des appels d'API bruts et d'assembler une plomberie personnalisée, LangChain vous offre un ensemble d'abstractions composables — chargeurs de documents, découpeurs de texte, modèles d'embedding, magasins vectoriels, récupérateurs, chaînes et agents — qui couvrent tout le cycle de vie d'une application LLM.

Son atout clé pour le RAG est le **pipeline de récupération** :

- Les **chargeurs de documents** ingèrent du contenu à partir de PDFs, CSVs, bases de données, Notion, Google Drive, Slack et des dizaines d'autres sources dans un objet `Document` standardisé.
- Les **découpeurs de texte** divisent les grands documents en segments plus petits et récupérables indépendamment — une étape critique car les modèles d'embedding ont des limites de longueur de contexte et les segments plus petits donnent des correspondances de similarité plus précises.
- Les **modèles d'embedding** convertissent chaque segment en un vecteur de haute dimension. LangChain prend en charge plus de 30 fournisseurs d'embedding incluant Google Vertex AI, Amazon Bedrock, OpenAI, Cohere et Ollama — tous derrière la même interface, de sorte que changer de fournisseur nécessite de modifier une seule ligne.
- Les **magasins vectoriels** stockent et indexent ces embeddings pour une recherche sémantique rapide. LangChain s'intègre avec plus de 40 backends, incluant l'`AsyncCockroachDBVectorStore` natif fourni par le package `langchain-cockroachdb`.
- Les **récupérateurs** se placent au-dessus des magasins vectoriels et exposent une seule interface `.invoke(query)` — que la recherche sous-jacente soit basée sur la similarité, MMR ou hybride avec des seuils de score.
- Les **chaînes et agents** relient les récupérateurs, les prompts et les LLMs en des workflows de bout en bout. Les chaînes suivent un chemin d'exécution fixe ; les agents laissent le LLM décider dynamiquement quels outils appeler et dans quel ordre — l'épine dorsale du RAG agentique.

```python
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_cockroachdb import AsyncCockroachDBVectorStore

# Load → Split → Embed → Store
docs   = PyPDFLoader("report.pdf").load()
chunks = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200).split_documents(docs)
store  = AsyncCockroachDBVectorStore(engine=engine, embeddings=VertexAIEmbeddings(model="gemini-embedding-001"), collection_name="kb")
await store.aadd_documents(chunks)

# Retrieve
results = await store.asimilarity_search_with_score("What is the Q3 revenue?", k=3)
```

Cette composabilité est la raison pour laquelle LangChain est le standard de facto pour le RAG : vous pouvez échanger n'importe quel composant — fournisseur d'embedding, backend vectoriel, LLM — sans réécrire le pipeline.

### Memori

[Memori](https://memorilabs.ai/) est une couche de mémoire native SQL et agnostique aux LLM pour les agents IA en production. Là où LangChain gère le pipeline de récupération et de génération, Memori gère **ce que l'agent mémorise entre les sessions** — transformant des conversations brutes en connaissances structurées et interrogeables qui persistent dans votre propre base de données.

À chaque appel LLM, Memori capture automatiquement l'échange et le classifie en quatre types de mémoire :

| Type de mémoire | Ce qu'il stocke | Exemple |
|---|---|---|
| **Faits** | Déclarations vérifiées sur le monde ou l'utilisateur | « Le plan du compte de l'utilisateur est Entreprise » |
| **Préférences** | Préférences exprimées ou inférées | « Préfère des réponses concises » |
| **Règles** | Contraintes et instructions | « Ne jamais recommander des produits concurrents » |
| **Résumés** | Historique de conversation compressé | « Discussion des étapes d'intégration lors de la session #4 » |

Lors des appels ultérieurs, Memori injecte uniquement les mémoires **pertinentes** comme contexte — pas l'historique complet — en utilisant son propre moteur de **rappel sans token**. C'est le mécanisme derrière sa prétendue réduction de 98 % des dépenses LLM : au lieu de rejouer des journaux de conversation entiers dans la fenêtre de contexte à chaque tour, seuls les extraits sémantiquement pertinents sont récupérés en quelques millisecondes depuis CockroachDB.

L'intégration est un seul appel SDK :

```python
from memori import Memori

with sql_engine.raw_connection() as conn:
    mem = Memori(conn=conn).llm.register(vertexai)
    mem.attribution(entity_id="user-123", process_id="my-app")
    mem.config.storage.build()
```

Après `mem.llm.register(client)`, Memori intercepte automatiquement tous les appels LLM — sans décorateur, sans recherche manuelle dans le cache, sans code d'injection de conversation. Il fournit également un **graphe de mémoire** interactif qui visualise comment les faits, les préférences et les relations évoluent au fil des sessions, ainsi qu'un **tableau de bord analytique** qui suit les taux de création de mémoire, les taux de succès du cache et l'utilisation du rappel.

Pour les déploiements en entreprise, Memori est conforme PCI et SOC 2, prend en charge le RBAC avec SSO/OAuth, la rétention de données configurable et la purge automatique, et des pistes d'audit complètes — avec toutes les données restant dans votre propre base de données par défaut.

---

## Tutoriel : construire le pipeline RAG

Le tutoriel est structuré en deux parties. La partie 1 utilise **Vertex AI** de Google Cloud (Gemini Embeddings + génération Gemini 2.5 Flash). La partie 2 utilise **Bedrock** d'Amazon Web Services (Titan Embed Text v2 + Claude Sonnet 4.6). La couche CockroachDB et le pipeline LangChain sont identiques entre les deux — seuls les clients d'embedding et de LLM changent.

<img src="/assets/img/ai-rag-crdb-dataflow.png" alt="RAG data flow with CockroachDB — user question, vectorisation, similarity search, context injection, LLM response" style="width:100%">
{: .mx-auto.d-block :}
**Flux de données RAG avec CockroachDB — question utilisateur, vectorisation, recherche par similarité, injection de contexte, réponse LLM**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Le flux de données : l'utilisateur soumet une question → elle est vectorisée → CockroachDB effectue une recherche par similarité → les k documents les plus pertinents sont récupérés → le contexte est injecté dans le prompt → le LLM génère une réponse ancrée.

---

## Partie 1 : CockroachDB + GCP Vertex AI + Memori

### Installation des dépendances

```bash
pip install langchain langchain-community langchain-cockroachdb langchain-google-vertexai \
    pypdf tenacity psycopg2-binary sqlalchemy memori "google-cloud-aiplatform>=1.60.0" --upgrade
```

### Imports

```python
from glob import glob
from memori import Memori
from langchain.document_loaders import PyPDFLoader, DataFrameLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_cockroachdb import AsyncCockroachDBVectorStore, CockroachDBEngine
from langchain_google_vertexai import VertexAIEmbeddings
from vertexai.generative_models import GenerativeModel
from sqlalchemy import create_engine, text
import vertexai, hashlib, pandas as pd
```

### Configuration de GCP Vertex AI, Memori et CockroachDB

```python
from getpass import getpass

PROJECT_ID = getpass("GCP Project ID: ")
REGION     = input("GCP Region (e.g. us-central1): ")
vertexai.init(project=PROJECT_ID, location=REGION)

# Connection string from the CockroachDB Cloud Console
# Format: cockroachdb://user:pass@host:26257/db?sslmode=verify-full
COCKROACHDB_URL = getpass("CockroachDB connection string: ")
engine     = CockroachDBEngine.from_connection_string(COCKROACHDB_URL)
sql_engine = create_engine(COCKROACHDB_URL.replace("cockroachdb://", "postgresql://"))

with sql_engine.raw_connection() as conn:
    cursor = conn.cursor()
    mem = Memori(conn=conn).llm.register(vertexai)
    mem.config.storage.build()
```

### Chargement et découpage des documents

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

### Création du Vector Store CockroachDB

`AsyncCockroachDBVectorStore` gère automatiquement l'initialisation de la table, le stockage des embeddings et la gestion de l'index C-SPANN via l'intégration `langchain-cockroachdb`.

```python
embeddings = VertexAIEmbeddings(model="gemini-embedding-001")

# gemini-embedding-001 produces up to 3072-dimensional vectors
await engine.ainit_vectorstore_table(
    table_name="knowledge_base",
    vector_dimension=3072,
)
vector_store = AsyncCockroachDBVectorStore(
    engine=engine,
    embeddings=embeddings,
    collection_name="knowledge_base",
)
await vector_store.aadd_documents(docs)
print(f"{len(docs)} chunks indexed in CockroachDB")
```

### Pipeline de génération RAG

```python
generation_model = GenerativeModel("gemini-2.5-flash")

PROMPT = """You are a helpful virtual assistant. Use the sources below as context \
to answer the question. If you don't know the answer, say so.

SOURCES:
{sources}

QUESTION: {query}

ANSWER:"""

async def rag(query: str) -> str:
    relevant = await vector_store.asimilarity_search_with_score(query, k=3)
    sources  = "\n---\n".join(doc.page_content for doc, _ in relevant)
    return generation_model.generate_content(
        PROMPT.format(sources=sources, query=query)
    ).text
```

### Cache LLM standard (SQLAlchemyCache)

L'approche la plus propre pour utiliser un cache LLM sur CockroachDB est le `SQLAlchemyCache` intégré à LangChain, qui s'intègre de manière transparente avec tous les appels LLM — aucun code de hachage/UPSERT manuel n'est nécessaire. Utilisez le `sql_engine` que vous avez déjà :

```python
from langchain.globals import set_llm_cache                                                                                                           from langchain.cache import SQLAlchemyCache                                

set_llm_cache(SQLAlchemyCache(sql_engine))
```

C'est tout ! LangChain intercepte chaque appel LLM, vérifie la table de cache (`llm_cache`) dans CockroachDB automatiquement et retourne la réponse stockée en cas de succès.

Cache par correspondance exacte : si la même requête a déjà été posée, `SQLAlchemyCache` retourne en interne la réponse stockée sans appeler le LLM.
Cela remplace tout le bloc de cache manuel (`cache_get`, `cache_put`, décorateur `@standard_llmcache`, etc.). Une fois que `set_llm_cache` est appelé, il s'applique globalement à tous les appels LLM ultérieurs, y compris à l'intérieur des chaînes et des agents.

### Cache LLM sémantique et historique des conversations (Memori)

Une fois que `mem.llm.register(client)` est appelé, Memori intercepte automatiquement tous les appels LLM sans aucun décorateur ni recherche manuelle dans le cache. Il capture les faits, les préférences et les résumés dans CockroachDB et injecte le contexte pertinent à chaque appel ultérieur.

Cela remplace à la fois le cache standard et les blocs d'historique de conversation dans le tutoriel. Memori gère la mémoire structurée, le rappel et la mise en cache dans une seule couche.

Le cache sémantique de Memori est intégré — ce n'est pas un composant séparé à configurer. Il fonctionne à deux niveaux :

1. Rappel sans token (remplace votre cache sémantique) : lorsqu'une requête est sémantiquement similaire à une précédente, Memori récupère uniquement les extraits de contexte en cache pertinents depuis CockroachDB — pas d'appel LLM, pas de dépense de tokens. C'est la prétention de « réduction des coûts de 98 % ». Cela se produit automatiquement une fois que `mem.llm.register(client)` est appelé.
2. Augmentation avancée (s'exécute en arrière-plan) : Il convertit les conversations en triplets sémantiques structurés (faits, préférences, règles, relations) stockés dans CockroachDB. Les requêtes futures sont appariées sémantiquement à ce magasin structuré — plus précis que la simple similarité d'embedding.

Ainsi, par rapport à l'approche manuelle dans le tutoriel :

| | **Configuration manuelle** | **Memori** |
|---|---|---|
| **Cache exact** | Hachage SHA-256 → SQL UPSERT | Intégré |
| **Cache sémantique** | `asimilarity_search_with_score` + seuil | Rappel sans token intégré |
| **Historique des conversations** | Table `chat_history` + injection manuelle | Mémoire de session intégrée |
| **Configuration requise** | `Similarity Threshold`, décorateur, wrapper | Aucune - intercepté automatiquement |

L'intégralité du bloc de cache + historique manuel dans le tutoriel se réduit à :

```python                                                          
mem = Memori(conn=get_conn).llm.register(client)
mem.attribution(entity_id="user-123", process_id="my-app")
mem.config.storage.build()
```
> **_NOTE :_** Vous ne pouvez pas ajuster directement le seuil de similarité, celui-ci est abstrait dans le moteur de rappel de Memori.

---
## Partie 2 : CockroachDB + Amazon Bedrock
### Installation des dépendances

```bash
pip install langchain langchain-community langchain-cockroachdb langchain-aws \
    pypdf tenacity psycopg2-binary sqlalchemy boto3 botocore --upgrade
```

### Imports

```python
from langchain.document_loaders import PyPDFLoader, DataFrameLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_cockroachdb import AsyncCockroachDBVectorStore, CockroachDBEngine
from langchain_aws import BedrockEmbeddings, ChatBedrock
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from sqlalchemy import create_engine, text
import boto3, hashlib, pandas as pd
```

### Configuration d'AWS et CockroachDB

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

# Format: cockroachdb://user:pass@host:26257/db?sslmode=verify-full
COCKROACHDB_URL = getpass("CockroachDB connection string: ")
engine     = CockroachDBEngine.from_connection_string(COCKROACHDB_URL)
sql_engine = create_engine(COCKROACHDB_URL.replace("cockroachdb://", "postgresql://"))
```

### Création du Vector Store CockroachDB

```python
bedrock_embeddings = BedrockEmbeddings(
    model_id="amazon.titan-embed-text-v2:0",
    client=bedrock_runtime
)

# amazon.titan-embed-text-v2:0 produces 1024-dimensional vectors
await engine.ainit_vectorstore_table(
    table_name="knowledge_base",
    vector_dimension=1024,
)
vector_store = AsyncCockroachDBVectorStore(
    engine=engine,
    embeddings=bedrock_embeddings,
    collection_name="knowledge_base",
)
await vector_store.aadd_documents(docs)
```

### Pipeline de génération RAG

```python
PROMPT = """You are a helpful virtual assistant. Use the sources below as context \
to answer the question. If you don't know the answer, say so.

SOURCES:
{sources}

QUESTION: {query}

Answer:"""

async def rag(query: str) -> str:
    relevant = await vector_store.asimilarity_search_with_score(query, k=3)
    sources  = "\n---\n".join(doc.page_content for doc, _ in relevant)
    llm      = ChatBedrock(model_id="anthropic.claude-sonnet-4-6", client=bedrock_runtime)
    chain    = ConversationChain(llm=llm, verbose=False, memory=ConversationBufferMemory())
    return chain.predict(input=PROMPT.format(sources=sources, query=query))
```

### Cache et historique

Les implémentations du cache standard et de l'historique sont **identiques à la Partie 1** (en utilisant `sql_engine`). Seul le client d'embedding du magasin vectoriel change — utilisez `bedrock_embeddings` (1024 dims) au lieu des embeddings Vertex AI :

```python
await engine.ainit_vectorstore_table(
    table_name="llm_semantic_cache",
    vector_dimension=1024,
)
semantic_cache = AsyncCockroachDBVectorStore(
    engine=engine,
    embeddings=bedrock_embeddings,   # Titan v2 instead of Gemini
    collection_name="llm_semantic_cache",
)

@standard_llmcache
async def ask_claude(query): return await rag(query)

@semantic_llmcache
async def ask_claude_semantic(query): return await rag(query)
```
---

## GCP Vertex AI vs AWS Bedrock : choisir votre pile IA cloud

Les deux intégrations produisent des résultats identiques du point de vue de CockroachDB — les couches de magasin vectoriel, de cache et d'historique sont inchangées. La décision dépend de votre stratégie cloud, de vos préférences de modèles et de vos exigences de conformité.

| | **GCP Vertex AI** | **AWS Bedrock** |
|---|---|---|
| **Modèle d'embedding** | `gemini-embedding-001` (3072 dims) | `amazon.titan-embed-text-v2:0` (1024 dims) |
| **Modèle de génération** | `gemini-2.5-flash` | `anthropic.claude-sonnet-4-6` |
| **Dimensionnalité vectorielle** | 3072 | 1024 |
| **Classe LangChain** | `VertexAIEmbeddings` (langchain-google-vertexai) | `BedrockEmbeddings` / `ChatBedrock` (langchain-aws) |
| **Mécanisme d'authentification** | Compte de service GCP / ADC | Clés d'accès AWS IAM / rôle |
| **Idéal pour** | Piles natives GCP, intégration BigQuery | Piles natives AWS, choix multi-modèles |
| **Variété de modèles** | Gemini 2.0, Gemma, Imagen | Anthropic, Cohere, Meta, Amazon, Mistral |
| **Modèle de tarification** | Par caractère d'entrée/sortie | Par token d'entrée/sortie |
| **Conformité** | GDPR, HIPAA, SOC 2 | GDPR, HIPAA, SOC 2, FedRAMP |
| **Latence** | ~200–400 ms (embedding) | ~300–600 ms (embedding) |

**Choisissez Vertex AI si** vous êtes déjà sur GCP, utilisez BigQuery comme source de données ou avez besoin d'une intégration étroite avec Gemini 2.5. **Choisissez Bedrock si** vous êtes sur AWS, voulez accéder à plusieurs modèles de fondation tiers (Anthropic Claude Sonnet 4.6, Cohere, Meta Llama) depuis une seule API, ou avez besoin de la conformité FedRAMP.

Les deux sont également bien adaptés à l'un des trois paradigmes RAG décrits ci-dessus — naïf, graphe ou agentique — avec CockroachDB servant de couche de données unifiée pour tous.

---

## Ce que le RAG débloque : cas d'usage concrets

Les modèles RAG et l'infrastructure décrits ci-dessus ne sont pas des exercices académiques — ils permettent directement une classe d'applications qui seraient impossibles ou peu fiables sans récupération ancrée. Voici deux exemples concrets qui illustrent l'étendue de ce qui devient possible une fois que vous disposez d'un pipeline RAG fonctionnel sur CockroachDB.

### Assistants conversationnels spécialisés

<img src="/assets/img/ai-rag-00.png" alt="RAG pipeline for domain-specific conversational assistant — knowledge base (web content, documents, database), semantic search layer, context retrieval, LLM answering user questions" style="width:100%">
{: .mx-auto.d-block :}
**Pipeline RAG pour assistant conversationnel spécialisé — base de connaissances (contenu web, documents, base de données), couche de recherche sémantique, récupération de contexte, LLM répondant aux questions des utilisateurs**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

L'application la plus directe est un assistant conversationnel ancré dans une base de connaissances privée. La base de connaissances peut être n'importe quoi : documentation interne, FAQ de support, dossiers réglementaires, articles de recherche, ou une combinaison de contenu web, de documents bruts et d'enregistrements de bases de données structurées. Les utilisateurs posent des questions en langage naturel — *« Comment configurer l'authentification à deux facteurs ? »*, *« Que dit la clause 4.3 de notre SLA ? »*, *« Résumez les trois rapports d'incidents les plus récents »* — et le pipeline RAG récupère uniquement le contexte pertinent avant de demander au LLM de composer une réponse.

L'avantage critique par rapport à un modèle affiné est la **fraîcheur** : la base de connaissances se met à jour en temps réel à mesure que des documents sont ajoutés ou révisés, sans réentraînement. Avec CockroachDB comme magasin vectoriel, une seule upsert indexe immédiatement le nouveau contenu, et la prochaine requête en bénéficiera déjà. Associé à la mémoire de session de Memori, l'assistant mémorise également le contexte de l'utilisateur au fil des conversations — le rendant véritablement adaptatif plutôt que sans état.

Les déploiements courants dans ce modèle incluent :
- **Bots de support client** qui répondent aux questions sur les produits ou les politiques à partir d'un corpus de documentation en direct
- **Assistants juridiques et de conformité** qui font remonter les clauses contractuelles ou les exigences réglementaires pertinentes
- **Bases de connaissances internes** où les employés interrogent les politiques RH, les runbooks d'ingénierie ou les guides d'intégration
- **Assistants de recherche** qui synthétisent des résultats à partir de centaines d'articles sans nécessiter une révision manuelle

### Recommandations e-commerce personnalisées

<img src="/assets/img/ai-rag-03.png" alt="RAG for e-commerce chatbot — product catalogue embeddings in vector database, user natural language query, LangChain application backend, personalised product recommendation via chat dialog" style="width:100%">
{: .mx-auto.d-block :}
**RAG pour chatbot e-commerce — embeddings du catalogue de produits dans la base de données vectorielle, requête en langage naturel de l'utilisateur, backend d'application LangChain, recommandation de produit personnalisée via dialogue de chat**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Le e-commerce est un terrain naturel pour le RAG car les catalogues de produits sont grands, changent fréquemment et portent un contenu sémantique riche — descriptions, avis, attributs — que la recherche par mots-clés gère mal. Plutôt que de s'appuyer sur des menus de filtres fragiles ou des moteurs de recommandation précalculés, un assistant d'achat alimenté par RAG permet aux utilisateurs de décrire ce dont ils ont besoin en langage naturel et retourne des produits qui correspondent véritablement à l'intention.

Dans l'architecture ci-dessus, les descriptions de produits, les avis et les attributs sont intégrés et indexés dans le magasin vectoriel CockroachDB. La requête d'un utilisateur — *« Je veux une nouvelle chemise pour paraître en forme au mariage de mon frère »* — est intégrée au moment de la requête, mise en correspondance avec le catalogue de produits via la recherche sémantique par similarité, et les meilleurs candidats sont transmis au LLM avec l'historique de chat de l'utilisateur. Le résultat est une recommandation personnalisée avec une explication : *« Je vous suggère cette chemise — nous l'avons en différentes couleurs qui pourraient bien convenir. »*

Ce qui rend cela viable à grande échelle est précisément le modèle multi-tenant de CockroachDB : l'historique des préférences de chaque client, les interactions passées et les embeddings personnalisés vivent dans leur propre partition d'index, de sorte que les performances sont proportionnelles aux données de cet utilisateur plutôt qu'à la taille du catalogue complet. À mesure que le catalogue croît, l'index C-SPANN se divise et se rééquilibre automatiquement sans aucune intervention opérationnelle.

Au-delà de la mode, cette même architecture alimente :
- **La recherche de produits B2B** sur de grands catalogues techniques où les numéros de pièces et les spécifications nécessitent une correspondance sémantique
- **La découverte de médias et de contenu** qui fait remonter des articles, vidéos ou podcasts basés sur les intérêts nuancés des utilisateurs
- **La recherche immobilière** où les requêtes en langage naturel comme *« quartier calme, bonnes écoles, praticable à pied »* se mappent sur des annonces structurées
- **Les moteurs de recommandation de voyage et d'hospitalité** qui personnalisent les offres à partir d'un inventaire en direct

### Le fil conducteur

Les deux cas d'usage partagent la même infrastructure : CockroachDB stocke le corpus de connaissances ou de produits, sert d'index vectoriel, met en cache les réponses LLM pour réduire les coûts et persiste la mémoire de session via Memori. LangChain fournit la couche d'orchestration qui relie les embeddings, la récupération et la génération en un pipeline cohérent. La pile IA cloud — Vertex AI ou Bedrock — fournit les modèles d'embedding et de génération.

Ce qui change entre un bot de support et un assistant d'achat, c'est uniquement les données du domaine et le prompt. L'architecture, les propriétés de scalabilité et les garanties opérationnelles restent les mêmes — ce qui est précisément la valeur de construire sur une base de données distribuée à usage général plutôt qu'un magasin vectoriel dédié.

---

## Ressources

- [Documentation de la recherche vectorielle CockroachDB](https://www.cockroachlabs.com/docs/stable/vector-search.html)
- [langchain-cockroachdb — Intégration LangChain pour CockroachDB](https://pypi.org/project/langchain-cockroachdb/)
- [Développement d'agents avec CockroachDB via LangChain](https://www.cockroachlabs.com/blog/agent-development-cockroachdb-langchain/)
- [Du local au global : article Microsoft GraphRAG (arXiv 2404.16130)](https://arxiv.org/abs/2404.16130)
- [Enquête RAG agentique (arXiv 2501.09136)](https://arxiv.org/abs/2501.09136)
- [Catalogue de modèles Amazon Bedrock](https://aws.amazon.com/bedrock/)
- [Google Vertex AI — IA générative](https://cloud.google.com/vertex-ai/generative-ai/docs)
- [Notebook RAG original — GCP](https://github.com/aelkouhen/redis-vss/blob/main/4-%20Retrieval-Augmented%20Generation%20(RAG)%20-%20GCP.ipynb)
- [Notebook RAG original — AWS](https://github.com/aelkouhen/redis-vss/blob/main/4bis-%20Retrieval-Augmented%20Generation%20(RAG)%20-%20AWS.ipynb)
- [Memori Labs](https://memorilabs.ai/)
- [Dépôt GitHub Memori Labs](https://github.com/MemoriLabs/Memori)
