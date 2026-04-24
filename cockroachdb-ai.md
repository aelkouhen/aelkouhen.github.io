---
layout: page
title: CockroachDB & AI
subtitle: "Building AI-ready systems — RAG pipelines, vector search, and agentic workflows on distributed SQL."
wide: true
lang: en
accent-color: "#008AFF"
category-tag: "Artificial Intelligence"
category-img: "/assets/img/cockroachdb.webp"
category-icon: "🤖"
---

{% assign ai_posts = site.tags['Artificial Intelligence'] | where_exp: "post", "post.tags contains 'CockroachDB'" %}
{% include post-cards.html posts=ai_posts %}
