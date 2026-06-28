# Podcast Newsletter Bot

A daily digest bot that polls RSS feeds for new podcast episodes, summarizes them with the Claude API, and sends a formatted HTML email via Gmail SMTP. Runs daily on **GitHub Actions** (no local machine required).

## Pipeline

1. **`feeds.py`** — checks all RSS feeds in `config.yaml` for episodes published in the last 24 hours. Tracks seen episode GUIDs in `state.json` to avoid duplicates.
2. **`transcribe.py`** — extracts and cleans show-notes text from RSS descriptions.
3. **`summarize.py`** — calls Gemini (`gemini-2.0-flash`) to generate a structured summary: overview, key takeaways, notable quotes, why it matters.
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
.github/workflows/daily.yml   # Backup cron at 10 AM ET
run.sh            # Local 9 AM job (git pull → send → push state)
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Gemini API key from ai.google.dev |
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

- **24-hour lookback window**: only episodes published in the last 24 hours are included. GUID state prevents duplicates across runs.
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


## Scheduling

- **Primary:** macOS LaunchAgent runs `run.sh` every day at **9:00 AM local time** (your Mac must be awake).
- **Backup:** GitHub Actions runs at **10:00 AM ET** if the local job did not send anything (e.g. Mac was asleep). `state.json` dedup prevents double emails.
