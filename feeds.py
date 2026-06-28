"""RSS feed checker — detects new podcast episodes."""

from __future__ import annotations

import json
import feedparser
from datetime import datetime, timezone, timedelta
from pathlib import Path

STATE_FILE = Path(__file__).parent / "state.json"
LOOKBACK = timedelta(hours=24)  # unseen episodes older than this are skipped


def load_state() -> dict:
    return json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


def check_feed(podcast: dict, state: dict) -> list[dict]:
    """Return new episodes from a single podcast feed."""
    name = podcast["name"]
    seen = set(state.get(name, []))
    cutoff = datetime.now(timezone.utc) - LOOKBACK

    try:
        feed = feedparser.parse(podcast["rss_url"])
    except Exception as e:
        print(f"  [ERROR] {name}: {e}")
        return []

    if feed.bozo and not feed.entries:
        print(f"  [WARN] {name}: {feed.bozo_exception}")
        return []

    new_episodes = []
    for entry in feed.entries[:20]:
        guid = entry.get("id") or entry.get("link") or entry.get("title", "")
        if guid in seen:
            continue

        published = ""
        if getattr(entry, "published_parsed", None):
            published_dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            published = published_dt.strftime("%Y-%m-%d")
            if published_dt < cutoff:
                continue

        description = ""
        if getattr(entry, "content", None):
            description = entry.content[0].get("value", "")
        description = description or entry.get("summary", "") or entry.get("description", "")

        new_episodes.append({
            "title": entry.get("title", "Unknown Title"),
            "description": description,
            "published": published,
            "link": entry.get("link", ""),
            "guid": guid,
            "podcast_name": name,
            "podcast_category": podcast.get("category", "Other"),
        })

    return new_episodes


def check_all_feeds(podcasts: list[dict]) -> tuple[list[dict], dict]:
    """Check every feed; return (new_episodes, updated_state)."""
    state = load_state()
    all_new = []

    print(f"Checking {len(podcasts)} feeds...")
    for podcast in podcasts:
        name = podcast["name"]
        new_eps = check_feed(podcast, state)
        if new_eps:
            print(f"  {name}: {len(new_eps)} new")
            all_new.extend(new_eps)
            existing = state.get(name, [])
            state[name] = (existing + [ep["guid"] for ep in new_eps])[-200:]
        else:
            print(f"  {name}: —")

    print(f"\nTotal new episodes: {len(all_new)}")
    return all_new, state
