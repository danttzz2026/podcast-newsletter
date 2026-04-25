#!/usr/bin/env python3
"""Podcast Newsletter Bot — daily digest of your favorite podcasts."""

import yaml
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env", override=True)

from feeds import check_all_feeds, save_state
from transcribe import get_episode_content
from summarize import summarize_all
from newsletter import format_newsletter
from sender import send_newsletter


def main():
    print("🎙️  Podcast Newsletter Bot\n")

    podcasts = yaml.safe_load((Path(__file__).parent / "config.yaml").read_text())["podcasts"]

    new_episodes, updated_state = check_all_feeds(podcasts)
    if not new_episodes:
        print("\n✅ No new episodes. Nothing to send.")
        return

    contents = [get_episode_content(ep) for ep in new_episodes]
    summaries = summarize_all(new_episodes, contents)
    if not summaries:
        print("\n⚠️ No summaries generated. Skipping newsletter.")
        return

    html = format_newsletter(summaries)
    try:
        send_newsletter(html, len(summaries))
    except ValueError as e:
        print(f"\n[ERROR] Email config: {e}")
        return

    save_state(updated_state)
    print(f"\n✅ Sent digest with {len(summaries)} summary(ies).")


if __name__ == "__main__":
    main()
