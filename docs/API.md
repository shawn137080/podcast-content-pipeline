# Podcast Content Engine — API Documentation

## Overview

The Podcast Content Engine ingests podcast audio, transcribes it with speaker diarization, stores the transcript in a searchable knowledge base (Open Notebook), and exposes an API to generate platform-specific content from it.

**n8n** handles ingestion + notifications.
**Open Notebook** is the content engine — it stores transcripts and runs LLM transformations.
**Telegram** is the notification layer.
**You** call the Open Notebook API to generate the content you need, in the format you need.

---

## Architecture

```
Audio URL → n8n webhook
              ↓
         Deepgram STT (diarize, timestamps)
              ↓
         Extract transcript (S1:, S2:, etc.)
              ↓
         POST /api/sources/json
              ↓
         Open Notebook (RAG + LLM transformations)
              ↓
         Telegram: "Episode X ingested. Source ID: source:abc. Ready."

YOU call Open Notebook:
              ↓
         POST /api/transformations/execute
              ↓
         LLM generates your content
              ↓
         Return to you as text
```

---

## Endpoints

### 1. Ingest a new episode

Trigger the n8n workflow. Send any audio URL (mp3, wav, m4a).

```bash
curl -X POST http://localhost:5678/webhook/process-episode
```

**Optional body** (override defaults):
```json
{
  "audio_url": "https://example.com/episode.mp3",
  "episode_title": "Episode 42: Title",
  "episode_description": "Brief description",
  "audio_duration_minutes": 45
}
```

**Returns** (via webhook response):
```json
{
  "status": "completed",
  "episode": "Episode 42: Title",
  "source_id": "source:pwehfpjwzq3goaha0y0a",
  "duration_min": 45
}
```

**Telegram notification** (sent to your bot):
```
🎙️ Episode ingested: Episode 42: Title
📊 Pipeline complete:
• STT: Deepgram (2700s)
• Storage: Open Notebook
• Duration: 45 min
• Source ID: source:pwehfpjwzq3goaha0y0a
• Transcript: 12000 chars
✅ Content engine ready...
```

---

### 2. List available content formats (transformations)

```bash
curl -X GET http://localhost:5055/api/transformations \
  -H "Authorization: Bearer <OPEN_NOTEBOOK_PASSWORD>"
```

**Returns** the 7 podcast-specific transformations (plus 6 generic ones):

| Name | Title | Output |
|------|-------|--------|
| `podcast_show_notes` | Show Notes (Bullet List) | Structured bullet list with topics, insights, quotes |
| `podcast_twitter_thread` | Twitter/X Thread | 3-7 tweets, each < 280 chars |
| `podcast_linkedin_post` | LinkedIn Post | 150-300 word professional post |
| `podcast_blog_draft` | Blog Post Draft | 500-800 word markdown article |
| `podcast_pull_quotes` | Pull Quotes | 5-8 memorable quotes with speaker labels |
| `podcast_newsletter` | Newsletter Section | 200-300 word newsletter segment |
| `podcast_summary_short` | Short Summary | 2-3 sentence episode description |

---

### 3. Generate content for a specific platform

This is the main "one-step repurpose" endpoint. Pick a transformation, send it the transcript (or the source ID), get back platform-ready content.

**Option A: Use stored source (recommended)**
```bash
# First, get the source content
curl -X GET "http://localhost:5055/api/sources/source:pwehfpjwzq3goaha0y0a" \
  -H "Authorization: Bearer <OPEN_NOTEBOOK_PASSWORD>"
```

**Option B: Generate directly from any text** (no source needed)
```bash
curl -X POST http://localhost:5055/api/transformations/execute \
  -H "Authorization: Bearer <OPEN_NOTEBOOK_PASSWORD>" \
  -H "Content-Type: application/json" \
  -d '{
    "transformation_id": "transformation:84qm6r94qkpwtecjikoz",
    "input_text": "<your transcript or any text>",
    "model_id": "model:vl90i23ymg000uowcl1y"
  }'
```

**Available transformation IDs** (pre-loaded):
- `transformation:b8pf2hqqyulewlgrjbcp` — Show Notes
- `transformation:84qm6r94qkpwtecjikoz` — Twitter/X Thread
- `transformation:4rq8ffddbjrvwospendv` — LinkedIn Post
- `transformation:e9e6lwibzvr0tp36zos2` — Blog Post Draft
- `transformation:wcvq99og28l3m8kkp412` — Pull Quotes
- `transformation:y3o7hpme7fmh42yotmty` — Newsletter Section
- `transformation:nijw84mq0f51wxjrhz4k` — Short Summary

**Returns**:
```json
{
  "output": "<the generated content>",
  "transformation_id": "transformation:84qm6r94qkpwtecjikoz",
  "model_id": "model:vl90i23ymg000uowcl1y"
}
```

**Example** (Twitter thread from grocery episode):
```json
{
  "output": "Stop saying \"I go to shop.\"\n\nThis one word separates you from sounding fluent at the supermarket 🧵\n\n---\n\n\"Supermarket\" isn't just where you buy food.\n\nThere's a whole aisle system most learners never master:...",
  ...
}
```

---

### 4. Search across all stored transcripts

Useful when you have many episodes and want to find content for repurposing.

```bash
curl -X POST http://localhost:5055/api/search \
  -H "Authorization: Bearer <OPEN_NOTEBOOK_PASSWORD>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "episode about AI safety",
    "type": "text"
  }'
```

**Returns**:
```json
{
  "results": [
    {
      "source_id": "source:abc",
      "title": "Episode 12: AI Safety",
      "snippet": "...discussion of AI alignment...",
      "score": 0.87
    }
  ],
  "total_count": 3,
  "search_type": "text"
}
```

---

### 5. Ask a question across all episodes (RAG)

```bash
curl -X POST http://localhost:5055/api/search/ask \
  -H "Authorization: Bearer <OPEN_NOTEBOOK_PASSWORD>" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Which episodes discussed machine learning?",
    "strategy_model": "model:vl90i23ymg000uowcl1y",
    "answer_model": "model:vl90i23ymg000uowcl1y",
    "final_answer_model": "model:vl90i23ymg000uowcl1y"
  }'
```

---

## Authentication

All Open Notebook API calls use the `Authorization: Bearer <token>` header. The token is set in the `.env` file:

```
OPEN_NOTEBOOK_PASSWORD=<OPEN_NOTEBOOK_PASSWORD>
```

In production, replace this with OAuth/JWT — see Open Notebook's `Security Configuration` docs.

---

## Common Workflows

### Workflow 1: Single episode → 7 platform outputs

```bash
# 1. Ingest
EPISODE=$(curl -X POST http://localhost:5678/webhook/process-episode)
SOURCE_ID=$(echo $EPISODE | jq -r '.source_id')

# 2. Get the transcript
TRANSCRIPT=$(curl -X GET "http://localhost:5055/api/sources/$SOURCE_ID" \
  -H "Authorization: Bearer $ON_KEY" | jq -r '.full_text')

# 3. Generate all 7 formats in parallel
for TRANSFORM in transformation:b8pf2hqqyulewlgrjbcp \
                transformation:84qm6r94qkpwtecjikoz \
                transformation:4rq8ffddbjrvwospendv \
                transformation:e9e6lwibzvr0tp36zos2 \
                transformation:wcvq99og28l3m8kkp412 \
                transformation:y3o7hpme7fmh42yotmty \
                transformation:nijw84mq0f51wxjrhz4k; do
  curl -X POST http://localhost:5055/api/transformations/execute \
    -H "Authorization: Bearer $ON_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"transformation_id\": \"$TRANSFORM\", \"input_text\": \"$TRANSCRIPT\", \"model_id\": \"model:vl90i23ymg000uowcl1y\"}" &
done
wait
```

### Workflow 2: Cross-episode search + synthesis

Find all episodes mentioning a topic, then generate a newsletter that synthesizes them:

```bash
# Search
RESULTS=$(curl -X POST http://localhost:5055/api/search \
  -H "Authorization: Bearer $ON_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "AI safety", "type": "text"}')

# Extract transcripts
TRANSCRIPTS=$(echo $RESULTS | jq -r '.results[].source_id' | \
  xargs -I {} curl -s "http://localhost:5055/api/sources/{}" \
    -H "Authorization: Bearer $ON_KEY" | \
  jq -r '.full_text' | head -c 30000)

# Generate synthesis newsletter
curl -X POST http://localhost:5055/api/transformations/execute \
  -H "Authorization: Bearer $ON_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"transformation_id\": \"transformation:y3o7hpme7fmh42yotmty\",
    \"input_text\": \"$TRANSCRIPTS\",
    \"model_id\": \"model:vl90i23ymg000uowcl1y\"
  }"
```

---

## Webhook Trigger Customization

To use a custom audio URL (not the default episode), pass a body to the webhook:

```bash
curl -X POST http://localhost:5678/webhook/process-episode \
  -H "Content-Type: application/json" \
  -d '{
    "audio_url": "https://your-cdn.com/episode-42.mp3",
    "episode_title": "Episode 42: Custom Title",
    "episode_description": "Description here",
    "audio_duration_minutes": 45
  }'
```

---

## Custom Transformations

Add your own transformation (e.g., for Instagram captions, YouTube descriptions, etc.):

```bash
curl -X POST http://localhost:5055/api/transformations \
  -H "Authorization: Bearer $ON_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "podcast_instagram_caption",
    "title": "Instagram Caption",
    "description": "Generate a 100-word Instagram caption with hashtags",
    "prompt": "You are a social media manager. Generate a 100-word Instagram caption..."
  }'
```

Then use it like any other transformation.

---

## Cost & Limits

| Component | Cost |
|-----------|------|
| Deepgram STT | $0.0089/min (11.4 min = ~$0.10) |
| MiniMax LLM (M3) | ~$0.10 per transformation |
| Open Notebook storage | Free (self-hosted) |
| n8n | Free (self-hosted) |
| **Per episode (1 transformation)** | **~$0.20** |
| **Per episode (all 7 transformations)** | **~$0.80** |

**500 episodes/year × $0.80 = $400/year total** (vs. ~$20-50K for human transcription + content team)

---

## Service URLs

| Service | URL |
|---------|-----|
| n8n | http://localhost:5678 |
| Open Notebook UI | http://localhost:8502 |
| Open Notebook API | http://localhost:5055 |
| SurrealDB | http://localhost:8000 |
| PostgreSQL | localhost:5432 |

In production, these would be behind a reverse proxy (Caddy/Nginx) with HTTPS.

---

## Scaling to 500 Episodes/Year

The architecture is already designed for scale:
- **STT**: Deepgram processes audio asynchronously; bottleneck is API rate limits
- **Storage**: SurrealDB (Open Notebook's DB) scales horizontally
- **LLM**: MiniMax has no practical rate limit for this volume
- **Orchestration**: Switch n8n to queue mode + workers (one config flag)

For 500 episodes/year of ~30 min each:
- **STT cost**: $135/year (Deepgram)
- **LLM cost**: ~$50/year (if you generate 1 format per episode) or $400/year (all 7 formats)
- **Total infrastructure**: Free (self-hosted)
- **Total annual cost**: ~$200-500

This is roughly **100x cheaper** than equivalent human-powered content production.
