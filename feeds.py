"""RSS feed checker — detects new podcast episodes."""

from __future__ import annotations

import json
import os
import feedparser
from datetime import datetime, timezone, timedelta
from pathlib import Path

STATE_FILE = Path(__file__).parent / "state.json"


def load_state() -> dict:
    """Load previously seen episode GUIDs."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(state: dict):
    """Persist seen episode GUIDs."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def check_feed(podcast: dict, state: dict) -> list[dict]:
    """
    Check a single podcast RSS feed for new episodes.

    Args:
        podcast: dict with keys: name, rss_url, category
        state: dict mapping podcast name -> list of seen GUIDs

    Returns:
        List of new episode dicts with: title, description, audio_url,
        published, link, podcast_name, podcast_category
    """
    name = podcast["name"]
    rss_url = podcast["rss_url"]
    seen_guids = set(state.get(name, []))

    try:
        feed = feedparser.parse(rss_url)
    except Exception as e:
        print(f"  [ERROR] Failed to parse feed for {name}: {e}")
        return []

    if feed.bozo and not feed.entries:
        print(f"  [WARN] Feed error for {name}: {feed.bozo_exception}")
        return []

    new_episodes = []
    # Use UTC for date comparison — feedparser normalizes published_parsed to UTC
    two_days_ago = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")

    for entry in feed.entries[:20]:
        guid = entry.get("id") or entry.get("link") or entry.get("title", "")
        if guid in seen_guids:
            continue

        # Parse published date
        published = ""
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d")

        # Only include episodes from the last 2 days (handles missed runs + timezone edge cases)
        if published and published < two_days_ago:
            continue

        # Extract audio URL from enclosures
        audio_url = None
        for enclosure in entry.get("enclosures", []):
            if "audio" in enclosure.get("type", ""):
                audio_url = enclosure.get("href")
                break

        # Get the fullest description available
        description = ""
        if hasattr(entry, "content") and entry.content:
            description = entry.content[0].get("value", "")
        if not description:
            description = entry.get("summary", "") or entry.get("description", "")

        new_episodes.append({
            "title": entry.get("title", "Unknown Title"),
            "description": description,
            "audio_url": audio_url,
            "published": published,
            "link": entry.get("link", ""),
            "guid": guid,
            "podcast_name": name,
            "podcast_category": podcast.get("category", "Other"),
        })

    return new_episodes


def check_all_feeds(podcasts: list[dict]) -> tuple[list[dict], dict]:
    """
    Check all podcast feeds for new episodes.

    Returns:
        (new_episodes, updated_state)
    """
    state = load_state()
    all_new = []

    print(f"Checking {len(podcasts)} podcast feeds...")
    for podcast in podcasts:
        print(f"  Checking: {podcast['name']}")
        new_eps = check_feed(podcast, state)
        if new_eps:
            print(f"    → {len(new_eps)} new episode(s) today")
            all_new.extend(new_eps)

            # Update state with new GUIDs, cap to last 200 to prevent unbounded growth
            name = podcast["name"]
            existing = state.get(name, [])
            state[name] = (existing + [ep["guid"] for ep in new_eps])[-200:]
        else:
            print(f"    → No new episodes today")

    print(f"\nTotal new episodes: {len(all_new)}")
    return all_new, state
