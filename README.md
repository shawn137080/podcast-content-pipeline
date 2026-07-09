# Podcast-to-Content Pipeline (POC)

> Self-hosted pipeline that ingests podcast audio, transcribes with speaker diarization, and uses **Open Notebook** as a content engine to generate platform-specific content via API.

**Live demo repo**: [github.com/shawn137080/podcast-content-pipeline](https://github.com/shawn137080/podcast-content-pipeline)

---

## What this project does

A 6-service Docker stack that:

1. **Receives** an audio URL (mp3, wav, m4a) via a webhook
2. **Transcribes** it with Deepgram, including speaker diarization (S1, S2, etc.) and timestamps
3. **Stores** the transcript in Open Notebook (a NotebookLM alternative) as a searchable source
4. **Notifies** you via Telegram that the episode is ready, including the source ID
5. **Exposes an API** to generate content in any format you need (tweets, LinkedIn, blog, newsletter, etc.) by calling one of 7 pre-loaded "transformation" templates

**The client decides what content to generate and when.** The pipeline just ingests, stores, and makes it available.

---

## Quick start

```bash
# 1. Clone
git clone https://github.com/shawn137080/podcast-content-pipeline.git
cd podcast-content-pipeline

# 2. Configure
cp .env.example .env
# Edit .env with your API keys (Deepgram, MiniMax, Telegram bot, etc.)

# 3. Start all services
docker compose up -d

# 4. Wait for healthy (~30 seconds)
docker compose ps

# 5. Trigger the pipeline
curl -X POST http://localhost:5678/webhook/process-episode
```

Telegram will get a notification with the source ID. Then:

```bash
# Generate a Twitter thread from the stored transcript
curl -X POST http://localhost:5055/api/transformations/execute \
  -H "Authorization: Bearer <OPEN_NOTEBOOK_PASSWORD>" \
  -H "Content-Type: application/json" \
  -d '{
    "transformation_id": "transformation:84qm6r94qkpwtecjikoz",
    "input_text": "...",
    "model_id": "model:vl90i23ymg000uowcl1y"
  }'
```

Full API: see [`docs/API.md`](docs/API.md).

---

## Architecture

```
Audio URL → n8n Webhook
              ↓
         Deepgram STT (diarization + timestamps)
              ↓
         Extract transcript (S1:, S2:, etc.)
              ↓
         POST /api/sources/json → Open Notebook
              ↓
         Telegram notification: source ID + API usage

Client calls Open Notebook API → LLM (MiniMax-M3) → content
```

The split is intentional:

- **n8n** = ingestion + notification. Doesn't know what content you want.
- **Open Notebook** = the content engine. Stores transcripts, runs LLM transformations on demand.
- **Telegram** = notification layer. You call the API to get the actual content.

This means the **client picks the platform and format at request time**, not when the episode is ingested. You can generate a Twitter thread today, a LinkedIn post next week, and a blog draft next month — all from the same stored transcript.

---

## Services

| Service | URL | Purpose |
|---------|-----|---------|
| n8n | http://localhost:5678 | Workflow orchestration + webhook |
| Open Notebook UI | http://localhost:8502 | Staff-facing browser UI |
| Open Notebook API | http://localhost:5055 | Programmatic content generation |
| PostgreSQL | localhost:5432 | Workflow state, run history |
| Redis | localhost:6379 | n8n queue (for production mode) |
| SurrealDB | localhost:8000 | Open Notebook's vector database |

---

## Available content formats

Seven pre-loaded transformations, all powered by MiniMax-M3:

| Name | Output | Use case |
|------|--------|----------|
| `podcast_show_notes` | Structured bullet list with topics, insights, quotes | Episode pages, podcast platforms |
| `podcast_twitter_thread` | 3-7 tweets, each < 280 chars | Twitter/X promotion |
| `podcast_linkedin_post` | 150-300 word professional post | LinkedIn company page |
| `podcast_blog_draft` | 500-800 word markdown article | Company blog, Medium |
| `podcast_pull_quotes` | 5-8 quotes with speaker labels | Social cards, marketing |
| `podcast_newsletter` | 200-300 word newsletter section | Email newsletters |
| `podcast_summary_short` | 2-3 sentence summary | Episode descriptions |

The client calls any of these via `POST /api/transformations/execute`. Add your own by `POST /api/transformations` with a custom prompt.

---

## Why this stack

- **Deepgram**: Best balance of cost and JSON-first API for diarization. $0.0089/min including speaker labels.
- **Open Notebook**: The only production-viable open-source NotebookLM alternative with a transformation API. See [`docs/NOTEX_VS_OPEN_NOTEBOOK.md`](docs/NOTEX_VS_OPEN_NOTEBOOK.md) for the detailed recommendation.
- **MiniMax (M3)**: Comparable to GPT-4o-mini quality at $0.05/1M tokens, full structured output support.
- **Telegram**: Free notification layer, integrates with everything.
- **n8n**: Open-source, self-hostable, deep HTTP/webhook support, code-less workflow editor.

### Why not direct LLM in n8n?

We tried that first. It works for single-shot content, but it doesn't give you:

- **RAG** (search across all stored transcripts)
- **Versioned transformations** (change a prompt, get the new output across 500 episodes)
- **Cross-episode synthesis** (generate a newsletter from 10 episodes at once)
- **Search/ask** (find the best quote for a specific use case)

These all require a content engine, not just an LLM call.

---

## Cost at 500 episodes/year

| Component | Cost |
|-----------|------|
| Deepgram STT | ~$135/yr (45 min avg × 500 episodes) |
| MiniMax LLM | ~$50-400/yr depending on usage |
| Open Notebook | Free (self-hosted) |
| n8n | Free (self-hosted) |
| Storage | Free (local disk) |
| **Total** | **$200-500/yr for 500 episodes** |

Roughly 100x cheaper than equivalent human-powered content production.

To scale, switch `EXECUTIONS_MODE=queue` in `.env` and add workers via `docker compose up -d --scale n8n-worker=N`.

---

## Client questions answered (per spec)

This section directly addresses the "To apply" requirements from the job spec.

### 1. Short overview of automation / AI pipeline background

I build production-grade AI pipelines that combine:

- LLM orchestration (n8n, LangChain, custom Python)
- Speech-to-text with speaker diarization
- RAG-based content engines (NotebookLM alternatives, custom vector stores)
- Multi-provider abstractions (STT, LLM, embeddings — swappable via config)
- Self-hosted infrastructure via Docker Compose

This pipeline is representative: audio → transcript → searchable knowledge base → on-demand content generation.

### 2. Specific experience with n8n + STT APIs + open-source NotebookLM alternatives

- **n8n**: Built 8-node workflow with webhook trigger, multiple HTTP Request nodes for STT/transformation/notification, Set nodes for data transformation, custom JSON body construction with expression templating. Dealt with n8n v2.29.9 quirks (e.g., the multipart-form-data bug that blocks some STT providers; the JSON body string escaping for newlines).
- **STT APIs**: Hands-on with Deepgram (chosen), Speechmatics (multipart-only API — would not work with n8n's HTTP Request node), AssemblyAI, Gladia. Deepgram won on JSON-first API + URL mode that n8n handles cleanly.
- **NotebookLM alternatives**: Evaluated both real options in the spec — Notex (224 GitHub stars, 2 contributors, Go-based, 4 months stale) and Open Notebook (35.3k stars, 67+ contributors, TypeScript+Python, weekly commits, REST API with 40+ endpoints). Selected Open Notebook after hands-on testing. Created 7 custom podcast-specific transformations using its `POST /api/transformations` endpoint.

### 3. Links to GitHub or prior workflows

**This repo**: [github.com/shawn137080/podcast-content-pipeline](https://github.com/shawn137080/podcast-content-pipeline)

The n8n workflow is committed at `workflows/podcast-pipeline.json` (with API keys replaced by placeholders — see [`workflows/SETUP.md`](workflows/SETUP.md)).

The 7 transformations are visible in Open Notebook and can be re-created by importing `docs/API.md` examples.

### 4. Notex vs Open Notebook — 2-3 sentence note

I recommend **Open Notebook**. Notex is a 224-star Go side project without an API, transformations, or active maintenance; Open Notebook has 35.3k stars, a 40+ endpoint REST API, the transformation system the spec asks for, and weekly commits. For a content engine that needs to scale to 500 episodes/year, only Open Notebook is production-viable — and it already runs cleanly in Docker.

Full analysis: [`docs/NOTEX_VS_OPEN_NOTEBOOK.md`](docs/NOTEX_VS_OPEN_NOTEBOOK.md).

### 5. Estimated turnaround time

**Actual time for this POC**: ~4 hours from spec to working pipeline, including:

- Stack research and selection (~30 min)
- Docker setup with all services (~20 min)
- Provider integration: Deepgram, MiniMax, Telegram, Open Notebook (~45 min)
- n8n workflow construction and debugging (~60 min)
- API documentation and Notex vs Open Notebook recommendation (~30 min)
- GitHub repo setup and final README (~15 min)

**For the production expansion** (client portal, human-in-the-loop editor, admin dashboard, 500+ episodes/year), estimated 6-10 weeks of part-time work or 3-4 weeks full-time.

---

## What's included

```
podcast-content-pipeline/
├── README.md                                    # This file
├── docker-compose.yml                          # 6 services
├── .env.example                                 # Configuration template
├── .gitignore                                   # Excludes secrets, volumes, caches
├── config/
│   ├── stt_providers.json                      # 5 STT providers
│   ├── stt_config.py                           # Config loader + switching
│   ├── llm_providers.json                      # 5 LLM providers
│   └── llm_config.py                           # Config loader + switching
├── workflows/
│   ├── podcast-pipeline.json                   # n8n workflow (8 nodes)
│   ├── README.md                               # Node-by-node docs
│   └── SETUP.md                                # Credential setup guide
├── scripts/
│   └── schema.sql                              # PostgreSQL schema
└── docs/
    ├── API.md                                   # Content engine API reference
    └── NOTEX_VS_OPEN_NOTEBOOK.md               # Recommendation
```

---

## Files NOT included (and why)

- `n8n_data/`, `postgres_data/`, `redis_data/`, `surrealdb_data/`, `open_notebook_data/` — Docker volumes, regenerated on `docker compose up`
- `input/` — audio files you provide
- `.env` — your actual secrets (use `.env.example` as template)
- `__pycache__/`, `.DS_Store` — dev artifacts

All excluded via `.gitignore`.

---

## License

MIT. Self-hosted, no vendor lock-in.
