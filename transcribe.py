"""Tiered transcript pipeline — get episode content for summarization."""

from __future__ import annotations

import os
import re
import tempfile
import requests
from bs4 import BeautifulSoup

# Minimum chars for a description to be considered "good enough"
MIN_CONTENT_LENGTH = 500


def clean_html(html: str) -> str:
    """Strip HTML tags and clean up text."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n")
    # Collapse multiple newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def get_content_from_show_notes(episode: dict) -> str | None:
    """Tier 1: Extract content from RSS description/show notes."""
    description = episode.get("description", "")
    if not description:
        return None

    cleaned = clean_html(description)
    if len(cleaned) >= MIN_CONTENT_LENGTH:
        return cleaned
    return None


def get_content_from_whisper(episode: dict) -> str | None:
    """
    Tier 2: Download audio and transcribe via OpenAI Whisper API.
    Only used when show notes are insufficient.
    """
    audio_url = episode.get("audio_url")
    if not audio_url:
        return None

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print(f"    [SKIP] No OpenAI key for Whisper transcription")
        return None

    try:
        print(f"    Downloading audio...")
        # Download audio to temp file (first 30 min max to limit cost)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            response = requests.get(audio_url, stream=True, timeout=60)
            response.raise_for_status()
            # Download up to ~30MB (roughly 30 min of podcast audio)
            max_bytes = 30 * 1024 * 1024
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                tmp.write(chunk)
                downloaded += len(chunk)
                if downloaded >= max_bytes:
                    break
            tmp_path = tmp.name

        print(f"    Transcribing with Whisper API...")
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        with open(tmp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )

        os.unlink(tmp_path)
        return transcript if len(transcript) >= MIN_CONTENT_LENGTH else None

    except Exception as e:
        print(f"    [ERROR] Whisper transcription failed: {e}")
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except:
            pass
        return None


def get_episode_content(episode: dict) -> str:
    """
    Get the best available content for an episode using tiered approach:
    1. RSS show notes (free, instant)
    2. Whisper API transcription (paid, slower)
    3. Fall back to whatever description we have
    """
    podcast = episode["podcast_name"]
    title = episode["title"]
    print(f"  Getting content for: {podcast} — {title}")

    # Tier 1: Show notes
    content = get_content_from_show_notes(episode)
    if content:
        print(f"    ✓ Using show notes ({len(content)} chars)")
        return content

    # Tier 2: Whisper API (skip if no audio URL or no API key)
    content = get_content_from_whisper(episode)
    if content:
        print(f"    ✓ Using Whisper transcript ({len(content)} chars)")
        return content

    # Fallback: use whatever description we have, even if short
    fallback = clean_html(episode.get("description", ""))
    if fallback:
        print(f"    ⚠ Using short description ({len(fallback)} chars)")
        return fallback

    print(f"    ✗ No content available")
    return f"Episode: {title} by {podcast}. No detailed content available."
