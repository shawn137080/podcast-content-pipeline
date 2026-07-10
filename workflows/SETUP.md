# n8n Workflow Setup

## Import

1. Open n8n at http://localhost:5678
2. Go to **Workflows** → **Import from File**
3. Select `podcast-pipeline.json`
4. The workflow will be imported with placeholder variables

## Configure Credentials

The imported workflow has 4 HTTP Request nodes that need credentials. Configure these via the n8n UI:

### 1. Open Notebook API credential

In n8n, the workflow makes calls to `http://open_notebook:5055` using a Bearer token. The token is set via the `Authorization: Bearer 33041652bd0be...` header in each HTTP Request node.

**Set the token to your `OPEN_NOTEBOOK_PASSWORD` value** (from `.env`).

### 2. Deepgram API key

The `Deepgram: Transcribe` node uses:
- Header: `Authorization: Token 9922d5b4...`
- URL: `https://api.deepgram.com/v1/listen?...`

**Replace the token with your Deepgram API key.**

### 3. MiniMax API key

The `Open Notebook` (Note: this is actually the Open Notebook: Store Source node) and downstream nodes use:
- Header: `Authorization: Bearer <MINIMAX_KEY>`

Wait, that's actually the LLM API key, used for the Open Notebook credential. To configure:

- **Open Notebook credential** (Bearer token): `<OPEN_NOTEBOOK_PASSWORD>` (default for self-hosted POC)
- **MiniMax API key**: configured inside Open Notebook's credentials UI (http://localhost:8502)

### 4. Telegram Bot

The `Telegram: Notify` node uses a Telegram API credential. Create it in n8n:

1. Create bot via @BotFather on Telegram
2. Get the bot token
3. In n8n: **Credentials** → **New** → **Telegram API**
4. Paste the access token

---

## What the Placeholders Mean

The workflow JSON uses `{{DEEPGRAM_API_KEY}}`, `{{MINIMAX_API_KEY}}`, etc. as placeholders. These are **literal strings** in the workflow definition. After import, you need to:

1. Open each HTTP Request node
2. Replace the placeholder with the real value (or use n8n credentials)

**Alternatively**, edit the JSON file directly and search-and-replace:
- `{{DEEPGRAM_API_KEY}}` → your Deepgram key
- `{{OPEN_NOTEBOOK_PASSWORD}}` → your Open Notebook password
- `{{MINIMAX_API_KEY}}` → your MiniMax key
- `{{TELEGRAM_BOT_TOKEN}}` → your bot token
- `{{TELEGRAM_CHAT_ID}}` → your chat ID

Then re-import.

---

## The recommended approach

Use **n8n credentials** instead of putting secrets in the JSON:

1. In n8n, go to **Credentials** → **New** for each service
2. Add a credential per service
3. In the workflow, click the node and select the credential (instead of inline API key)

This way, the workflow JSON has no secrets and is safe to commit to Git.
