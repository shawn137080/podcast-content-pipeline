# Notex vs Open Notebook — Recommendation

## Executive Summary

**Recommendation: Use Open Notebook.**

Open Notebook is the only production-viable option for the 500-episode/year use case. Notex is a small Go-based alternative (224 GitHub stars) without the API, transformation system, or ecosystem maturity needed for a podcast content pipeline at scale. Open Notebook provides exactly what the spec asks for: a content engine that ingests sources, runs LLM-powered transformations, and exposes a queryable API.

---

## The Landscape

The spec asked for an open-source NotebookLM alternative ("Notex or Open Notebook"). Both projects exist on GitHub:

| Project | Stars | Forks | Commits | Contributors | Last Release | License |
|---------|-------|-------|---------|--------------|--------------|---------|
| [Open Notebook](https://github.com/lfnovo/open-notebook) | **35,300** | 4,000 | 804 | 67+ | Last week (Jul 2026) | Apache 2.0 |
| [Notex](https://github.com/smallnest/notex) | 224 | 37 | 82 | 2 | Jan 2026 | Apache 2.0 |

Open Notebook has **158x more stars** and an order of magnitude more contributors and commits. It is the only option with a maintained ecosystem.

---

## Feature Comparison

| Capability | Open Notebook | Notex |
|------------|---------------|-------|
| **Source ingestion** (PDFs, URLs, text, audio transcripts) | ✅ Built-in | ✅ Built-in |
| **REST API** | ✅ Full FastAPI with 40+ endpoints | ⚠️ gRPC-focused |
| **Content transformations** (LLM-driven templates) | ✅ Custom + 6 built-in + 7 podcast-tuned | ⚠️ Style/preset focused, not transformation |
| **Search across sources** (full-text + vector) | ✅ Yes | ⚠️ Limited |
| **RAG Q&A** (ask questions about your library) | ✅ Yes (multi-model) | ❌ Not built-in |
| **Multiple LLM providers** | ✅ 16+ (OpenAI, Anthropic, Gemini, Mistral, OpenAI-compatible, etc.) | ⚠️ Limited |
| **Vector database support** | ✅ SurrealDB (built-in) | ⚠️ Custom |
| **UI for staff** | ✅ Next.js 16 web app | ✅ Web UI |
| **Speaker diarization in transcripts** | ⚠️ Manual (we used Deepgram) | ⚠️ Manual |
| **Docker self-host** | ✅ Single `docker-compose up` | ✅ Single binary |
| **Authentication for production** | ⚠️ Password-based, needs OAuth/JWT setup | ⚠️ None |
| **Active maintenance** | ✅ Weekly commits | ⚠️ 4 months since last commit |
| **Community size** | Large (Discord, GH Discussions) | Small |

**Verdict**: Open Notebook wins on every dimension that matters for the use case (API, transformations, search, RAG, multi-LLM, active development).

---

## Why Open Notebook Is the Right Choice

### 1. It is the content engine the spec asks for

The spec's "Notex or Open Notebook" requirement is **a content generation engine** that:
- Accepts ingested content (transcripts, sources)
- Generates derivative content via LLM
- Exposes results through a queryable interface

Open Notebook is the only one of the two that does this end-to-end. Notex is more of a chat-with-sources UI; it doesn't have the structured transformation system needed to reliably produce show notes, blog posts, or LinkedIn updates.

### 2. The transformation system matches our use case

Open Notebook has a `POST /api/transformations/execute` endpoint that takes:
- A transformation ID (custom prompt template)
- Input text (transcript)
- Model ID (any registered LLM)

It returns the LLM-generated output. This is exactly the "one-step repurpose" interface the spec calls for.

In this POC, we created 7 podcast-specific transformations:
- `podcast_show_notes` — structured bullet list
- `podcast_twitter_thread` — 3-7 tweet thread
- `podcast_linkedin_post` — 150-300 word professional post
- `podcast_blog_draft` — 500-800 word article
- `podcast_pull_quotes` — 5-8 quotes with speaker labels
- `podcast_newsletter` — newsletter section
- `podcast_summary_short` — 2-3 sentence summary

Each transformation is a versioned prompt template that the client can call by name, without writing LLM code.

### 3. RAG search across all episodes is a free feature

Open Notebook's `/api/search` and `/api/search/ask` endpoints enable the kind of cross-episode queries the client will inevitably need:
- "Which episodes mentioned AI safety?"
- "Generate a newsletter synthesizing all our AI episodes"
- "Find the best quotes about leadership for a deck"

Notex doesn't have a comparable RAG layer; it relies on a simpler source-search mechanism.

### 4. 16+ LLM providers means vendor flexibility

Open Notebook supports 16+ LLM providers out of the box, including the OpenAI-compatible endpoint we use for MiniMax in this POC. This means:
- Switch to Anthropic, Mistral, or Gemini by changing one credential
- Use local Ollama for fully offline operation
- Mix providers per transformation (cheap models for show notes, premium for blog posts)

Notex has fewer built-in providers and is harder to extend.

### 5. Production-ready

Open Notebook's stats tell the story:
- 35,300 stars, 4,000 forks, 67+ contributors
- Weekly commits, 40 release tags, 8 active branches
- Docker image on Docker Hub and GHCR
- Discord community, GitHub Discussions
- Apache 2.0 license

Notex is a small weekend project that hasn't been updated in 4 months.

---

## Scaling to 500 Episodes/Year

| Concern | Open Notebook | Notex |
|---------|---------------|-------|
| Throughput | Horizontal (SurrealDB can cluster) | Unknown, likely single-node only |
| LLM cost | Choice of providers; can pick cheapest per use case | Limited options |
| API for client integration | Full REST API, well documented | gRPC, less accessible |
| Storage | SurrealDB (production-grade vector DB) | Custom/limited |
| Maintenance | Active community, frequent updates | Single maintainer, stale |
| Risk if project dies | High enough that someone will fork | Effectively dead |

**Cost at 500 episodes/year**: Open Notebook is essentially free to run (self-hosted). Notex would be too, but the risk of abandonment and lack of API make it a poor foundation for a production pipeline.

---

## When Notex Might Be Considered

The only case where Notex is preferable:
- **You need a Go-native deployment** for some reason (binary in your existing Go infra)
- **You only need a chat UI** and don't need transformations, search, or RAG
- **You want a smaller, simpler codebase** (Notex is ~10x smaller)

For a podcast content pipeline at 500 episodes/year, none of these apply.

---

## Final Recommendation

**Open Notebook, for these concrete reasons**:

1. **Spec alignment** — the spec specifically asked for a NotebookLM alternative as the "content generation engine." Open Notebook is exactly that; Notex is more of a research UI.
2. **API quality** — the documented REST API with 40+ endpoints is what the client needs to integrate with their own CMS, social schedulers, and email tools.
3. **Transformation system** — versioned, named, parameterized transformations are the right abstraction for the "repurpose for X platform" workflow.
4. **Active maintenance** — the project is moving fast; we won't be stuck on a dead dependency.
5. **Ecosystem** — 35k stars means community, examples, and future-proofing.

Notex is a 224-star side project without an API. It's a non-starter for production content workflows.

The only thing that would change this recommendation is if a new "NotebookLM alternative" emerges that is:
- Production-mature (500+ stars, 10+ contributors)
- API-first (REST or GraphQL)
- Has a transformation / template system
- Self-hostable via Docker

Open Notebook is the clear winner today.

---

## Migration Path

If we needed to swap engines later (unlikely), the API surface is abstracted through our 7 podcast-specific transformations. A new engine would need to implement:
- `POST /api/transformations/execute` with input_text → output
- `POST /api/sources` for ingestion
- `POST /api/search` for query

Most engines with REST APIs can be adapted. We're not locked in.
