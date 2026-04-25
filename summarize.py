"""Claude API summarization."""

import os
import anthropic

PROMPT_TEMPLATE = """You are summarizing a podcast episode for a daily newsletter aimed at a tech/VC investor.

PODCAST: {podcast_name}
EPISODE TITLE: {title}
PUBLISHED: {published}

EPISODE CONTENT:
{content}

Please provide a detailed newsletter summary in the following format. Be specific and insightful — the reader wants to know exactly what was discussed without listening to the full episode.

## Overview
Write 2-3 sentences capturing the core topic and why this episode is worth knowing about.

## Key Takeaways
Provide 5-7 specific, actionable takeaways as bullet points. Each should be a complete thought, not vague.

## Notable Quotes
Include 2-3 direct quotes if available in the content. If no direct quotes are available, write "No direct quotes available from show notes."

## Why It Matters
1-2 sentences on why this episode is relevant to someone in tech/VC right now."""


def summarize_episode(episode: dict, content: str) -> dict:
    """Generate a structured summary of one episode."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    if len(content) > 80_000:
        content = content[:80_000] + "\n\n[Content truncated]"

    prompt = PROMPT_TEMPLATE.format(
        podcast_name=episode["podcast_name"],
        title=episode["title"],
        published=episode["published"],
        content=content,
    )

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    return {
        "podcast_name": episode["podcast_name"],
        "podcast_category": episode["podcast_category"],
        "episode_title": episode["title"],
        "published": episode["published"],
        "link": episode["link"],
        "summary": message.content[0].text,
    }


def summarize_all(episodes: list[dict], contents: list[str]) -> list[dict]:
    """Summarize each episode; skip ones that fail."""
    summaries = []
    for episode, content in zip(episodes, contents):
        print(f"  Summarizing: {episode['podcast_name']} — {episode['title']}")
        try:
            summaries.append(summarize_episode(episode, content))
            print(f"    ✓ Done")
        except Exception as e:
            print(f"    [ERROR] {e}")
    return summaries
