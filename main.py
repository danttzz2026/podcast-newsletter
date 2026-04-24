#!/usr/bin/env python3
"""Podcast Newsletter Bot — daily digest of your favorite podcasts."""

import os
import sys
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / ".env", override=True)

from feeds import check_all_feeds, save_state
from transcribe import get_episode_content
from summarize import summarize_all
from newsletter import format_newsletter
from sender import send_newsletter


def load_config() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def main():
    print("=" * 50)
    print("🎙️  Podcast Newsletter Bot")
    print("=" * 50)

    # 1. Load config
    config = load_config()
    podcasts = config["podcasts"]

    # 2. Check all feeds for new episodes
    print("\n📡 Step 1: Checking RSS feeds...")
    new_episodes, updated_state = check_all_feeds(podcasts)

    if not new_episodes:
        print("\n✅ No new episodes found. No newsletter today.")
        return

    # 3. Get content for each episode (tiered approach)
    print(f"\n📝 Step 2: Getting content for {len(new_episodes)} episode(s)...")
    contents = []
    for episode in new_episodes:
        content = get_episode_content(episode)
        contents.append(content)

    # 4. Summarize with Claude
    print(f"\n🤖 Step 3: Generating summaries...")
    summaries = summarize_all(new_episodes, contents)

    if not summaries:
        print("\n⚠️ No summaries generated. Skipping newsletter.")
        return

    # 5. Format newsletter HTML
    print(f"\n🎨 Step 4: Formatting newsletter...")
    html = format_newsletter(summaries)

    # 6. Send email
    print(f"\n📧 Step 5: Sending newsletter...")
    try:
        send_newsletter(html, len(summaries))
    except ValueError as e:
        print(f"\n[ERROR] Email configuration error: {e}")
        return

    # 7. Save state (only after successful send)
    save_state(updated_state)
    print(f"\n✅ Done! Sent digest with {len(summaries)} episode summary(ies).")


if __name__ == "__main__":
    main()
