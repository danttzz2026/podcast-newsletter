"""Get episode content from RSS show notes."""

from __future__ import annotations

import re
from bs4 import BeautifulSoup


def clean_html(html: str) -> str:
    """Strip HTML tags and collapse extra whitespace."""
    text = BeautifulSoup(html, "html.parser").get_text(separator="\n")
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def get_episode_content(episode: dict) -> str:
    """Return cleaned show-notes text, or a stub if there's nothing usable."""
    title, podcast = episode["title"], episode["podcast_name"]
    print(f"  Getting content: {podcast} — {title}")

    content = clean_html(episode.get("description", ""))
    if content:
        print(f"    ✓ {len(content)} chars from show notes")
        return content

    print(f"    ✗ No content available")
    return f"Episode: {title} by {podcast}. No detailed content available."
