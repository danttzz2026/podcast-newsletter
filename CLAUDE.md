# Podcast Newsletter Bot

A daily digest bot that polls RSS feeds for new podcast episodes, summarizes them with the Claude API, and sends a formatted HTML email via Gmail SMTP.

## How It Works

1. **`feeds.py`** — Checks all RSS feeds in `config.yaml` for episodes published in the last 2 days. Tracks seen episode GUIDs in `state.json` to avoid duplicates.
2. **`transcribe.py`** — Tiered content extraction:
   - Tier 1: RSS show notes (free, instant)
   - Tier 2: OpenAI Whisper transcription of audio (paid, used as fallback)
3. **`summarize.py`** — Calls the Claude API (`claude-sonnet-4-6`) to generate a structured summary: overview, key takeaways, notable quotes, why it matters.
4. **`newsletter.py`** — Formats summaries into a styled HTML email, grouped by podcast category.
5. **`sender.py`** — Sends the HTML email via Gmail SMTP. Reads credentials from environment variables.
6. **`main.py`** — Orchestrates steps 1–5. Entry point.
7. **`daemon.py`** — Optional scheduler: runs `main.py` once daily at a configured hour, with a catchup window if the scheduled time was missed.

## Project Structure

```
main.py           # Entry point — orchestrates the full pipeline
feeds.py          # RSS feed polling and episode deduplication
transcribe.py     # Tiered content extraction (show notes → Whisper)
summarize.py      # Claude API summarization
newsletter.py     # HTML email formatter
sender.py         # Gmail SMTP sender
daemon.py         # Optional daily scheduler
config.yaml       # Podcast list (name, rss_url, category)
state.json        # Runtime state — seen episode GUIDs (gitignored)
daemon_state.json # Runtime state — daemon last-run tracking (gitignored)
.env              # Secrets — never committed (see .env.example)
```

## Environment Variables

Set these in `.env` (copy from `.env.example`):

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Claude API key from console.anthropic.com |
| `GMAIL_ADDRESS` | Yes | Gmail address used to send the newsletter |
| `GMAIL_APP_PASSWORD` | Yes | Gmail App Password (not your account password) |
| `OPENAI_API_KEY` | No | For Whisper transcription fallback |
| `RECIPIENT_EMAIL` | No | Send to a different address (defaults to `GMAIL_ADDRESS`) |

## Running It

```bash
pip install -r requirements.txt
python main.py          # Send today's newsletter once
python daemon.py        # Run as a daily scheduler
```

## Key Design Decisions

- **Date filter**: Episodes from the last 2 days are included (not just today) so missed runs don't permanently lose episodes. The GUID state file prevents duplicates.
- **State is only saved after a successful send**: If summarization or sending fails, episodes will be retried on the next run.
- **Feed entries capped at 20 per feed**: Prevents very large feeds from being slow. GUIDs are capped at 200 per podcast to keep `state.json` small.
- **`load_dotenv(override=True)`**: Required because the shell may have empty env vars set that would otherwise shadow the `.env` file.

## Adding Podcasts

Edit `config.yaml` and add an entry under `podcasts`:

```yaml
- name: "My Podcast"
  rss_url: "https://example.com/feed.rss"
  category: "Core"   # Core | VC | Tech/Business | or any new category
```

## Known Limitations / Good First Issues

- `20VC` RSS feed occasionally throws `IncompleteRead` errors — this is a server-side issue with their feed, not a bug in the code.
- The HTML email template in `newsletter.py` is functional but minimal — could be improved with better typography and layout.
- No test suite yet.
- `daemon.py` has no protection against multiple simultaneous instances.
