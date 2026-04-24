"""Claude API summarization — generates detailed episode summaries."""

import os
import anthropic


def summarize_episode(episode: dict, content: str) -> dict:
    """
    Generate a detailed summary of a podcast episode using Claude.

    Returns:
        dict with: overview, takeaways, quotes, why_it_matters
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Truncate very long content to stay within reasonable token limits
    max_chars = 80_000  # ~20k tokens
    if len(content) > max_chars:
        content = content[:max_chars] + "\n\n[Content truncated for length]"

    prompt = f"""You are summarizing a podcast episode for a daily newsletter aimed at a tech/VC investor.

PODCAST: {episode['podcast_name']}
EPISODE TITLE: {episode['title']}
PUBLISHED: {episode['published']}

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

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    summary_text = message.content[0].text

    return {
        "podcast_name": episode["podcast_name"],
        "podcast_category": episode["podcast_category"],
        "episode_title": episode["title"],
        "published": episode["published"],
        "link": episode["link"],
        "summary": summary_text,
    }


def summarize_all(episodes: list[dict], contents: list[str]) -> list[dict]:
    """Summarize all episodes."""
    summaries = []
    for episode, content in zip(episodes, contents):
        print(f"  Summarizing: {episode['podcast_name']} — {episode['title']}")
        try:
            summary = summarize_episode(episode, content)
            summaries.append(summary)
            print(f"    ✓ Done")
        except Exception as e:
            print(f"    [ERROR] Failed to summarize: {e}")
    return summaries
