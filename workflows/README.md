# n8n Workflow Import Guide

## How to Import This Workflow

1. Open n8n at http://localhost:5678
2. Click "Workflows" → "Import from File"
3. Select the workflow JSON file
4. Configure credentials (see below)
5. Activate workflow

## Required Credentials

### Telegram Bot
1. Create a bot via @BotFather on Telegram
2. Get your bot token
3. In n8n: Credentials → Telegram → Add token
4. Get your chat_id (send a message to your bot, then:
   `curl https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`)

### Speechmatics
1. Sign up at https://www.speechmatics.com
2. Get API key from dashboard
3. In n8n: Credentials → HTTP Request (Generic) → Add key

### MiniMax (LLM)
1. Sign up at https://platform.minimax.chat
2. Get API key
3. In n8n: Credentials → HTTP Request (Generic) → Add key

### Open Notebook
1. Set via OPEN_NOTEBOOK_ENCRYPTION_KEY in .env
2. In n8n: Credentials → HTTP Request (Generic) → Add bearer token
   (password = whatever you set in OPEN_NOTEBOOK_ENCRYPTION_KEY)

## Workflow Nodes Reference

### Node 1: Manual Trigger
- Type: "n8n-nodes-base.manualTrigger"
- Purpose: Start workflow manually for POC demo

### Node 2: Audio URL Input
- Type: "n8n-nodes-base.set"
- Purpose: Define audio_url, episode_title, episode_description
- Edit in n8n UI before running

### Node 3: Speechmatics STT
- Type: "n8n-nodes-base.httpRequest"
- Method: POST
- Endpoint: https://asr.api.speechmatics.com/v2/jobs
- Auth: Bearer token (Speechmatics API key)

### Node 4: Wait + Poll Speechmatics
- Type: "n8n-nodes-base.wait"
- Purpose: Poll for STT completion (Speechmatics is async)
- Polling interval: 5 seconds, max 5 retries

### Node 5: Get Speechmatics Result
- Type: "n8n-nodes-base.httpRequest"
- Method: GET
- Endpoint: https://asr.api.speechmatics.com/v2/jobs/{job_id}

### Node 6: Create Open Notebook Source
- Type: "n8n-nodes-base.httpRequest"
- Method: POST
- Endpoint: http://localhost:5055/sources
- Auth: Bearer token (Open Notebook password)
- Body: transcript text as a text source

### Node 7: Generate Content via LLM
- Type: "n8n-nodes-base.httpRequest"
- Method: POST
- Endpoint: MiniMax API (https://api.minimax.chat/v1/text/chatcompletion_v2)
- Auth: Bearer token (MiniMax API key)
- System prompt: content generation prompt

### Node 8: Format Output
- Type: "n8n-nodes-base.set"
- Purpose: Parse LLM response into structured sections

### Node 9: Send to Telegram
- Type: "n8n-nodes-base.telegram"
- Operation: Send Message
- Chat ID: Your Telegram chat ID

### Node 10: Log to PostgreSQL
- Type: "n8n-nodes-base.postgres"
- Operation: Insert Row
- Table: pipeline_runs
