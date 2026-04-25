# Podcast Newsletter Bot

A daily digest bot that polls RSS feeds for new podcast episodes, summarizes them with the Claude API, and sends a formatted HTML email via Gmail SMTP. Runs daily on **GitHub Actions** (no local machine required).

## Pipeline

1. **`feeds.py`** — checks all RSS feeds in `config.yaml` for episodes published in the last 2 days. Tracks seen episode GUIDs in `state.json` to avoid duplicates.
2. **`transcribe.py`** — extracts and cleans show-notes text from RSS descriptions.
3. **`summarize.py`** — calls Claude (`claude-sonnet-4-6`) to generate a structured summary: overview, key takeaways, notable quotes, why it matters.
4. **`newsletter.py`** — formats the summaries into a styled HTML email, grouped by category.
5. **`sender.py`** — sends the email via Gmail SMTP.
6. **`main.py`** — orchestrates the pipeline. Entry point.

## Project Structure

```
main.py           # Entry point
feeds.py          # RSS polling + GUID dedup
transcribe.py    # Show-notes extraction
summarize.py      # Claude summarization
newsletter.py    # HTML formatting
sender.py         # Gmail SMTP
config.yaml       # Podcast list (name, rss_url, category)
state.json        # Seen GUIDs — committed so cloud runs have memory
.env              # Secrets — gitignored (see env vars below)
.github/workflows/daily.yml   # Daily cron at 13:00 UTC (9 AM EDT)
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Claude API key from console.anthropic.com |
| `GMAIL_ADDRESS` | Yes | Gmail address used to send the newsletter |
| `GMAIL_APP_PASSWORD` | Yes | Gmail App Password (not the account password) |
| `RECIPIENT_EMAIL` | No | Send to a different address (defaults to `GMAIL_ADDRESS`) |

In production these come from GitHub Secrets. Locally they come from `.env`.

## Running It

```bash
pip install -r requirements.txt
python main.py
```

Or trigger the cloud run manually: GitHub → Actions → Daily Newsletter → Run workflow.

## Key Design Decisions

- **2-day lookback window**: episodes from the last 2 days are included so missed runs don't permanently lose episodes. GUID state prevents duplicates.
- **State saves only after a successful send**: failed runs are retried on the next run.
- **Feed entries capped at 20 per feed; GUIDs capped at 200 per podcast**: keeps `state.json` small and feed parsing fast.
- **`load_dotenv(override=True)`**: needed because the shell may have empty env vars that would otherwise shadow `.env`.

## Adding Podcasts

Edit `config.yaml`:

```yaml
- name: "My Podcast"
  rss_url: "https://example.com/feed.rss"
  category: "Core"
```
