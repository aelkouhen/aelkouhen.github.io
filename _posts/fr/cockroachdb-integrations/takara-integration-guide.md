---
date: 2026-06-15
layout: post
lang: fr
title: "Intégrer CockroachDB avec Takara DS1"
subtitle: "Guide pas-à-pas pour utiliser les embeddings Takara DS1 avec le stockage vectoriel natif et l'index C-SPANN de CockroachDB"
cover-img: /assets/img/cover-takara-integration.jpg
thumbnail-img: /assets/img/share-takara-integration.png
share-img: /assets/img/share-takara-integration.png
tags: [Guide, CockroachDB, takara, ds1, embeddings, recherche vectorielle, recherche sémantique, C-SPANN]
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

[Takara DS1](https://takara.ai/ds1) est un modèle d'embedding de texte hébergé, conçu pour produire des vecteurs à faible latence et à faible coût. Il retourne des vecteurs de 512 dimensions normalisés en L2 et il est exposé à la fois sous forme d'endpoint HTTPS public et de modèle AWS SageMaker. Couplé à [CockroachDB](https://www.cockroachlabs.com/) v25.2+, qui embarque un type de colonne `VECTOR` natif et un index distribué de recherche approchée des plus proches voisins (ANN) appelé **C-SPANN**, les deux forment une stack complète de recherche sémantique au sein d'une même base de données SQL transactionnelle. Ce guide parcourt cette intégration de bout en bout : provisionner la base, appeler l'API DS1 pour embedder du texte, stocker les vecteurs obtenus aux côtés de vos données métier, les interroger à la fois en SQL et par similarité vectorielle, puis benchmarker le résultat avec la suite open-source [`takara-ai/ds1-cockroach-db-performance`](https://github.com/takara-ai/ds1-cockroach-db-performance).

---

## Qu'est-ce que Takara DS1 ?

Takara DS1 est un modèle d'embedding de texte de production publié par [Takara.ai](https://takara.ai/). Il transforme un texte libre en un vecteur dense de taille fixe qui capture le sens sémantique, adapté à la recherche sémantique, à la génération augmentée par récupération (RAG), au clustering, à la classification, à la déduplication et aux moteurs de recommandation.

### Pourquoi DS1 ?

DS1 se positionne comme une alternative à faible latence et faible coût aux APIs d'embedding généralistes. Les propriétés publiques annoncées comptent particulièrement pour une intégration avec une base de données opérationnelle :

- **Sortie en 512 dimensions.** Plus petite que la plupart des modèles généralistes (qui se situent entre 768 et 3072 dimensions), donc le stockage, la taille de l'index et le calcul de distance à la requête sont tous moins coûteux.
- **Vecteurs normalisés en L2.** La similarité cosinus se réduit à un produit scalaire, opération que tout index vectoriel moderne accélère.
- **Service sans GPU.** DS1 est conçu pour fonctionner sur du matériel CPU, aussi bien dans l'endpoint hébergé par Takara que sur des instances SageMaker gérées par le client.
- **Deux modes d'accès.** Un endpoint HTTPS public sur `https://tldr.takara.ai/api/search` pour le prototypage et les charges légères, plus un déploiement AWS SageMaker pour la production avec réseau privé et authentification IAM.
- **Performance annoncée.** Takara rapporte une latence environ 10 fois plus faible et un coût 70 % inférieur à celui de la baseline `text-embedding-3-small` d'OpenAI (voir la [page produit DS1](https://takara.ai/ds1)). La section benchmark de ce guide mesure DS1 de bout en bout contre un cluster CockroachDB sur une charge représentative.

### Surface d'API DS1

L'endpoint HTTPS est volontairement minimaliste. Embedder un ou plusieurs textes se fait via une seule requête `GET` avec le(s) texte(s) passés en paramètres de requête répétés :

```bash
# Texte unique
curl "https://tldr.takara.ai/api/search?text=hello%20world"
# → [0.029, -0.013, 0.044, ... 512 floats ...]

# Batch (max 20 textes par requête)
curl "https://tldr.takara.ai/api/search?text=first%20doc&text=second%20doc"
# → [[0.029, ...], [0.011, ...]]
```

La forme de la réponse change avec la taille de l'entrée : un tableau plat pour un texte unique, une liste de tableaux pour un batch. Tout code client qui veut une forme constante doit encapsuler la réponse à texte unique dans une liste.

Pour les déploiements privés ou à haut débit, Takara propose également DS1 sur l'[AWS Marketplace](https://aws.amazon.com/marketplace/pp/prodview-yixnpliihlkee), invocable via `boto3` et `sagemaker-runtime`. Le corps de la requête sur la voie SageMaker est `{"inputs": ["text1", "text2", ...]}` avec `ContentType: application/json`, et la réponse est soit une liste de vecteurs, soit un dictionnaire avec une clé `"embeddings"`. Les deux modes d'accès renvoient des vecteurs sémantiquement équivalents : choisissez l'endpoint HTTPS pour le prototypage de ce guide, puis basculez sur SageMaker quand vous avez besoin d'isolation VPC, de débit dédié ou d'authentification IAM par requête.

---

## Pourquoi CockroachDB pour les charges vectorielles ?

Une requête de recherche sémantique est rarement « trouve les 10 plus proches par cosinus ». C'est « trouve les 10 plus proches qui sont en stock, livrables en FR, coûtent moins de 100 € et ne sont pas dans la catégorie restreinte ». La plupart des magasins vectoriels purs vous obligent à faire transiter ces filtres par un système OLTP séparé. CockroachDB évalue les deux prédicats dans le même plan SQL, contre la même ligne transactionnelle.

CockroachDB est particulièrement bien adapté à la sortie de DS1 parce que :

- **Type de colonne natif `VECTOR(n)`** depuis la v24.2, avec une dimension typée que le planificateur impose à l'insertion.
- **Index ANN distribué C-SPANN** depuis la v25.2, sans structure centralisée en mémoire : n'importe quel nœud peut servir n'importe quelle lecture, et l'index est splitté, mergé et rééquilibré comme n'importe quelle autre range CockroachDB. Voir le billet compagnon sur [l'indexation vectorielle temps-réel dans CockroachDB](/2025-11-23-cockroachdb-ai-spann/) pour la conception complète.
- **Fonctions de distance pilotées par l'opérateur.** Un seul index C-SPANN sert le cosinus (`<=>`), le L2 (`<->`) et le produit interne (`<#>`). Puisque DS1 retourne des vecteurs normalisés en L2, cosinus et produit interne produisent le même classement : choisissez celui qui se lit le mieux dans votre SQL.
- **Fraîcheur transactionnelle.** Un produit dont la description a changé il y a deux secondes doit être recherchable maintenant, avec le nouveau embedding. CockroachDB met à jour l'index de manière incrémentale sous isolation `SERIALIZABLE` par défaut. Pas de pipeline d'indexation en retard à surveiller.
- **Survie multi-région.** La même table peut être regional-by-row, en lecture follower ou globalement cohérente selon le SLA, sans dupliquer le schéma.
- **Une seule empreinte opérationnelle.** Backups, RBAC, audit, CDC, restauration à un instant t : les données métier et les embeddings partagent le même cycle de vie.

---

## Architecture conjointe Takara DS1 + CockroachDB

L'intégration comporte trois composants sur le chemin chaud de chaque requête :

1. **L'endpoint DS1** (HTTPS ou SageMaker) qui transforme une chaîne de requête en vecteur de 512 dimensions.
2. **Une table CockroachDB** qui stocke les lignes métier aux côtés de leur colonne d'embedding.
3. **Un index C-SPANN** sur cette colonne qui sert le classement des plus proches voisins en temps sous-linéaire.

À l'écriture, l'application encode le texte du document avec DS1, puis émet un unique `INSERT` (ou `UPSERT`) qui écrit la ligne métier et le vecteur ensemble. CockroachDB maintient l'index C-SPANN de la nouvelle ligne de manière transparente.

À la lecture, l'application encode la requête utilisateur avec DS1, puis émet un unique `SELECT … ORDER BY embedding <=> $1 LIMIT k` (éventuellement avec des prédicats `WHERE`). Le planificateur utilise C-SPANN pour récupérer l'ensemble candidat, applique les prédicats et renvoie les top-k lignes. Pas de second magasin, pas de fan-out côté application.

---

## Mettre en place un environnement conjoint CockroachDB / Takara DS1

Le reste de ce guide est un parcours exécutable. L'exemple utilise un catalogue produit illustratif de 25 lignes. Le catalogue lui-même n'est pas un artefact Takara : c'est un échantillon réduit et sémantiquement diversifié construit pour ce guide. Remplacez-le par vos propres données sans changer une ligne de code ci-dessous.

### Prérequis

- CockroachDB **v25.2 ou ultérieure**. Les versions antérieures supportent le type de colonne `VECTOR` mais pas C-SPANN, donc les lectures retombent sur un balayage séquentiel.
- Python 3.10+ avec `httpx`, `psycopg[binary]` et `tenacity`.
- Un accès réseau vers `https://tldr.takara.ai/api/search`. Pour la variante SageMaker, un compte AWS avec l'[abonnement marketplace Takara DS1](https://aws.amazon.com/marketplace/pp/prodview-yixnpliihlkee).
- Environ dix minutes.

### Étape 1. Provisionner un cluster CockroachDB

Pour l'exploration locale, un cluster mono-nœud insecure suffit :

```bash
cockroach start-single-node --insecure --listen-addr=localhost:26257 --background
cockroach sql --insecure --url "postgresql://root@localhost:26257/defaultdb"
```

Pour un déploiement multi-nœud ou de production, suivez les chemins d'installation [self-hosted](https://www.cockroachlabs.com/docs/stable/install-cockroachdb.html) ou [Cloud](https://cockroachlabs.cloud/). Dans tous les cas, activez la fonctionnalité d'index vectoriel une seule fois par cluster :

```sql
SET CLUSTER SETTING feature.vector_index.enabled = true;
```

### Étape 2. Créer le schéma

Gardez les colonnes métier et l'embedding dans la même table. C'est délibéré : toute requête sémantique gagne à pouvoir filtrer sur prix, stock, catégorie ou région dans le même plan, et il n'y a aucun avantage à séparer l'embedding dans une table secondaire quand le cycle de vie est identique.

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

Trois choix volontaires :

1. **`VECTOR(512)`** correspond à la dimension que DS1 retourne. CockroachDB rejettera toute insertion dont la longueur de vecteur diffère.
2. **`JSONB attributes`** stocke la longue traîne des champs produit (taille, couleur, matière) sans imposer de migration de schéma. Il est entièrement filtrable en SQL aux côtés du prédicat vectoriel.
3. **L'index C-SPANN n'a pas de métrique explicite.** La fonction de distance est choisie à la requête par l'opérateur (`<=>` pour cosinus, `<->` pour L2, `<#>` pour produit interne). Le même index sert les trois.

### Étape 3. Embedder et ingérer avec l'API Takara DS1

Le jeu de données d'exemple est 25 produits répartis sur cinq catégories. Sauvegardez-le sous `products.csv` :

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

#### Un client léger pour l'endpoint DS1

L'endpoint HTTPS accepte un ou plusieurs paramètres `text=` par requête et renvoie un tableau plat (texte unique) ou une liste de tableaux (batch). Le client ci-dessous uniformise les deux formes et retente les échecs transitoires avec un backoff exponentiel :

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

La limite de 20 textes par batch est celle de l'endpoint hébergé. La variante SageMaker accepte des batchs plus grands ; le [quickstart officiel](https://ds1.takara.ai/getting-started/quickstart.html) recommande 16 à 32 documents par requête comme bon compromis entre latence et débit.

#### Ingérer le catalogue

Le script d'ingestion lit le CSV, construit le texte que voit le modèle (concaténation de `name` et `description` : le nom seul est trop pauvre, la description seule perd les repères de marque), embedde dans la taille de batch préférée par DS1, puis écrit la ligne et le vecteur via un unique `INSERT` par chunk.

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

Deux détails d'implémentation à souligner :

- **`%s::vector`** est requis parce que la couche pgwire de CockroachDB n'accepte pas actuellement la représentation binaire de `VECTOR`. Le driver envoie le tableau sous forme de littéral texte et le cast se fait côté serveur. C'est le seul élément d'ergonomie façon pgvector qui ne fonctionne pas de manière transparente.
- **Aucune étape de normalisation côté client.** DS1 retourne directement des vecteurs normalisés en L2, donc la similarité cosinus est exactement le produit scalaire. Il n'y a rien à faire à l'insertion au-delà de passer le vecteur tel quel.

Exécutez le script :

```bash
python ingest_products.py
# Upserted 25 products.
```

### Étape 4. Interroger en SQL et par similarité vectorielle

Les trois patrons ci-dessous couvrent toutes les formes réalistes en recherche sémantique : filtre SQL pur, classement vectoriel pur, et l'hybride qui combine les deux.

#### 4.1 SQL pur : filtre à facettes

La requête e-commerce classique, sans vecteur. C'est la première chose évidente que vous lanceriez déjà sur la table, désormais voisine de la colonne d'embedding.

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

Le plan utilise `products_category_idx` et `products_price_idx`. Aucun vecteur n'est touché.

#### 4.2 Recherche sémantique pure : classer par le sens

L'utilisateur tape *« chaussures confortables pour longues marches »*. Le client embedde la requête avec DS1, puis demande à CockroachDB les dix produits les plus proches par distance cosinus. C-SPANN sert la clause `ORDER BY embedding <=> $1` depuis l'index vectoriel sans balayer la table.

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

Remarquez le plan d'entraînement marathon en cinquième position. Rien dans le *nom* ne contient le mot « shoes » ou « walks », mais la description est sémantiquement adjacente. C'est le signal qu'une requête `LIKE` ne peut tout simplement pas produire.

#### 4.3 Hybride : classement vectoriel avec contraintes SQL

Le patron que vous déploierez vraiment. Appliquez les contraintes métier (`in_stock`, région, plafond de prix) en clause `WHERE`, puis ordonnez par distance vectorielle. Le planificateur CockroachDB pousse le prédicat vers le bas, donc C-SPANN ne balaye que l'ensemble candidat qui survit au filtre.

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

C'est cette requête qui rend la formule « magasin vectoriel dans une base OLTP » digne de l'effort. La même ligne qui porte `in_stock` et `price_eur` porte aussi le vecteur, donc le planificateur peut intersecter les deux prédicats sans sortir de la couche de stockage.

#### 4.4 Régler le compromis rappel / latence

CockroachDB expose la taille de beam par requête comme variable de session. Encapsulez la recherche dans une transaction et fixez-la avec `SET LOCAL` pour qu'elle ne s'applique qu'à cette requête :

```sql
BEGIN;
SET LOCAL vector_search_beam_size = 32;   -- default is decided by CockroachDB
SELECT sku, name FROM products
ORDER BY embedding <=> $1::vector LIMIT 10;
COMMIT;
```

Des valeurs de beam plus élevées augmentent le rappel au prix de la latence. Les requêtes de découverte de longue traîne bénéficient d'un beam élevé ; les requêtes de suggestion en saisie doivent garder la valeur par défaut.

### Étape 5. Benchmarker l'intégration

Le parcours fonctionnel ci-dessus suffit à prouver que les pièces s'emboîtent. Pour répondre à « jusqu'où ça monte sous charge ? », utilisez le harnais open-source [`takara-ai/ds1-cockroach-db-performance`](https://github.com/takara-ai/ds1-cockroach-db-performance), qui exerce précisément la combinaison DS1 plus CockroachDB sur un corpus de courts documents texte.

> Le run de référence publié utilise un corpus d'environ 7 890 messages courts collectés depuis le jetstream [Bluesky](https://bsky.app/). La forme de la charge (texte en entrée, vecteur 512-d en sortie, ANN cosinus top-K sur quelques milliers à quelques millions de lignes) correspond à la charge de recherche produit ci-dessus. Les chiffres exacts dépendent du corpus, de la dimension d'embedding et de la topologie réseau entre client, endpoint DS1 et base. Relancez la suite contre vos propres données avant de citer des chiffres dans une discussion client.

Le propre [benchmark single-request de Takara](https://takara.ai/blog/embedding-benchmark-analysis-report) rapporte DS1 à environ 28 ms de latence moyenne sur une instance SageMaker `ml.t2.medium` dédiée, la plus basse des huit modèles d'embedding testés. Ce rapport jette délibérément les vecteurs et exclut le stockage, la récupération et la concurrence de son périmètre. Les chiffres ci-dessous étendent ce tableau à une forme concurrente de bout en bout contre CockroachDB : les latences DS1 que vous y voyez sont donc plus élevées que le chiffre isolé du single-request, parce qu'elles incluent le saut Internet public vers `tldr.takara.ai` et l'effet de file d'attente créé par plusieurs readers qui pilotent le même endpoint hébergé.

#### Cluster de référence

La baseline publiée a tourné sur un cluster CockroachDB v26.1.3 à trois nœuds en `us-east-1` :

| Composant            | Spec                                                       |
| -------------------- | ---------------------------------------------------------- |
| Nœuds                | 3 × `m6a.2xlarge` (8 vCPU / 32 Go), un par AZ              |
| Stockage             | 500 Go gp3 EBS par nœud                                    |
| Version CockroachDB  | v26.1.3, mode insecure, NLB public                         |
| Workbench            | bastion `m6a.large` dans le même VPC                       |
| Index vectoriel      | C-SPANN sur `VECTOR(512)`, cosinus                         |
| Service d'embedding  | Takara DS1 via l'endpoint HTTPS hébergé                    |
| Jeu de données       | 7 890 messages Bluesky uniques, découpés en quatre chunks  |

#### Reproduire le run

Sur le bastion :

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

Le harnais émet des métriques par batch et par requête sous `runners/benchmark/results/`, décomposées entre **latence de recherche vectorielle** (le temps que CockroachDB a passé à servir la requête `ORDER BY <=>`) et **latence DS1** (l'aller-retour d'embedding).

> Deux patches sont nécessaires pour que les chiffres ci-dessous soient reproductibles. Ils vivent dans la [PR #2 du dépôt upstream](https://github.com/takara-ai/ds1-cockroach-db-performance/pull/2) : un rate limiter `async` à l'intérieur de la coroutine reader (la version d'origine utilisait un `time.sleep` bloquant, qui sérialisait silencieusement le consommateur), et l'exposition de `--qps RATE` sur `run-benchmark.sh` (il était figé à `10.0`). Sans ces patches, le reader passe des minutes après `--duration` à vider un backlog auto-infligé et les centiles deviennent inutilisables.

#### Résultats

Trois runs graduels contre le cluster de référence, quatre readers et quatre writers chacun, le 2026-05-21 avec les patches de la PR #2 appliqués. Chaque run avait environ 8 000 lignes déjà présentes dans la table `embeddings`.

| Run        | QPS cible | QPS atteint | Total P50 / P95 / P99 (ms) | Vector P50 / P95 (ms) | DS1 P50 (ms) | Taux de succès |
| ---------- | --------- | ----------- | --------------------------- | --------------------- | ------------ | -------------- |
| Baseline   | 40        | 40          | **70 / 118 / 210**          | 12 / 20               | 58           | 100 %          |
| Mid load   | 200       | 164         | **168 / 273 / 340**         | 28 / 84               | 132          | 100 %          |
| Push       | 400       | 184         | **296 / 488 / 585**         | 42 / 184              | 231          | 100 %          |

Trois observations ressortent :

- **CockroachDB conserve une marge visible sur les trois runs.** La composante recherche vectorielle a contribué entre 12 et 22 % de la latence end-to-end à chaque niveau de charge. Même au run push saturé à 184 QPS, le P95 de C-SPANN à 184 ms reste largement dans le budget d'une charge de recherche interactive.
- **La latence end-to-end est dominée par l'étape d'embedding.** C'est la forme attendue de tout pipeline texte-vers-vecteur : le service d'embedding est un saut réseau, la lecture base est une opération locale. Des appels concurrents à l'endpoint DS1 hébergé font passer son P50 de 58 ms (baseline) à 231 ms (push) sous le profil de charge configuré. Pour un débit plus élevé, basculez DS1 sur la variante SageMaker dans le même VPC que le cluster : cela retire l'aller-retour Internet public et permet de scaler le nombre d'instances de l'endpoint de façon indépendante.
- **La saturation suit la loi de Little.** Au run push, quatre readers × 16 de concurrence / ~295 ms par requête donnent un plafond théorique de 54 QPS par reader. Le run a atteint 46. Le dimensionnement de cette stack est donc fonction du couple (concurrence, latence par requête), pas du QPS brut.

Un cache d'embeddings côté client n'est **pas** un remède honnête à la latence côté API dans ce benchmark : la suite ne réutilise que 55 chaînes de requête distinctes, donc le cache gonfle les chiffres sans représenter le comportement utilisateur réel. Pour une vraie charge de recherche produit avec une grande diversité de requêtes, le taux de hit du cache sera bien plus bas et le tableau ci-dessus est le portrait honnête.

#### Lire ces chiffres pour votre propre charge

Pour un catalogue réel, ce qui compte est le rapport entre les trois composantes de latence (requête base, génération d'embedding, réseau) et la façon dont elles évoluent quand la table grossit.

- **À quelques dizaines de lignes** (le tutoriel ci-dessus) l'index C-SPANN est sans objet. Le plan tombe sur un balayage et termine en microsecondes.
- **À ~10 000 lignes** (le benchmark) le tableau ci-dessus est votre référence. Attendez-vous à des dizaines de millisecondes au P95 de la recherche vectorielle et à l'étape d'embedding qui domine le reste.
- **À ~1 M de lignes** (un catalogue mûr) le nombre de partitions C-SPANN augmente et le travail par requête croît à peu près de manière logarithmique. Le [deep dive C-SPANN](/2025-11-23-cockroachdb-ai-spann/) montre la courbe de l'index sous cette charge.

Le levier unique le plus impactant dans les trois régimes est **l'endroit où tourne le modèle d'embedding**. Le cluster a plus de marge que ne le suggèrent les chiffres de référence. Ce que vous saturez en premier est le saut qui se trouve entre l'utilisateur, le service d'embedding et la base.

---

## Conseils opérationnels

Une courte liste, assumée, distillée de l'exécution de cette boucle de bout en bout :

- **Gardez la colonne d'embedding dans la table métier.** Le patron « les embeddings vivent dans une table secondaire jointe par id » double le travail du planificateur pour aucun bénéfice quand les cycles de vie sont identiques.
- **Fixez la dimension tôt.** La changer plus tard force un re-embedding complet et un `DROP / CREATE` de l'index C-SPANN. Le 512 de DS1 est une valeur par défaut défendable pour des catalogues sous quelques millions de lignes.
- **Réglez `vector_search_beam_size` par classe de requête, pas globalement.** Posez `SET LOCAL` dans une transaction, scopé à la requête.
- **Traitez l'endpoint d'embedding comme une dépendance de dimensionnement.** Comme le montre le benchmark, sur la plupart des charges réalistes, c'est le service d'embedding qui décide du plafond de QPS. Planifiez la topologie de déploiement en conséquence : SageMaker-dans-VPC pour le haut débit, l'endpoint hébergé pour le prototypage.
- **Re-embeddez sur changement de description, pas selon un calendrier.** Ajoutez une colonne `embedded_at` et un job en arrière-plan qui ré-encode toute ligne dont `updated_at > embedded_at`. L'index C-SPANN se met à jour de manière incrémentale.
- **Utilisez des retries avec backoff exponentiel côté client.** Le client DS1 de ce guide utilise `tenacity` avec quatre tentatives et une fenêtre de backoff de 0,5 à 8 s, valeur par défaut raisonnable pour toute API d'embedding HTTPS.

---

## Pour aller plus loin

- [**Indexation temps-réel pour des milliards de vecteurs**](/2025-11-23-cockroachdb-ai-spann/) couvre les internals de C-SPANN et la courbe de scaling au-delà du million de vecteurs.
- [**Construire des applications RAG avec CockroachDB**](/2026-02-20-cockroachdb-ai-rag/) réutilise le même magasin vectoriel pour un LLM qui ancre ses réponses dans vos données.
- Le code source complet de ce guide (schéma, client DS1, script d'ingestion, helper de recherche, recette de benchmark) est publié aux côtés de la suite open-source [`takara-ai/ds1-cockroach-db-performance`](https://github.com/takara-ai/ds1-cockroach-db-performance). Les patches et les re-runs contre vos propres données sont les bienvenus.
