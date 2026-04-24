#!/usr/bin/env python3
"""
Persistent daemon that runs the podcast newsletter at 9 AM daily.
- Catch-up: if Mac was asleep at 9 AM, runs on wake (if before noon)
- Retry: 3 attempts with 30s delay on network/API errors
- Once-per-day guard: reads/writes daemon_state.json
"""

from __future__ import annotations

import json
import logging
import sys
import time
from datetime import date, datetime
from pathlib import Path

import schedule

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
STATE_FILE = BASE_DIR / "daemon_state.json"
LOG_FILE = Path.home() / "Library/Logs/podcast-newsletter-daemon.log"

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
SCHEDULE_HOUR = 9
CATCHUP_UNTIL_HOUR = 12
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 30


# ── State helpers ─────────────────────────────────────────────────────────────
def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"last_run_date": None}


def save_state(run_date: str) -> None:
    STATE_FILE.write_text(json.dumps({"last_run_date": run_date}, indent=2))


def already_ran_today() -> bool:
    return load_state().get("last_run_date") == str(date.today())


# ── Newsletter runner with retry ──────────────────────────────────────────────
def run_newsletter() -> None:
    if already_ran_today():
        log.info("Already ran today — skipping.")
        return

    # Deferred import so daemon starts fast even during boot
    from main import main as newsletter_main

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log.info(f"Attempt {attempt}/{MAX_RETRIES}: running newsletter...")
            newsletter_main()
            save_state(str(date.today()))
            log.info("Newsletter completed successfully.")
            return
        except Exception as e:
            log.warning(f"Attempt {attempt} failed: {e}")
            if attempt < MAX_RETRIES:
                log.info(f"Retrying in {RETRY_DELAY_SECONDS}s...")
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                log.error("All retries exhausted. Will try again tomorrow at 9 AM.")


# ── Catch-up on startup ───────────────────────────────────────────────────────
def catchup_if_needed() -> None:
    now = datetime.now()
    if SCHEDULE_HOUR <= now.hour < CATCHUP_UNTIL_HOUR:
        if not already_ran_today():
            log.info(f"Catch-up: it's {now.strftime('%H:%M')} and newsletter hasn't run today. Running now.")
            run_newsletter()
        else:
            log.info("Catch-up check: already ran today.")
    else:
        log.info(f"Catch-up check: {now.strftime('%H:%M')} is outside window (9 AM–noon). Waiting for 9 AM.")


# ── Entry point ───────────────────────────────────────────────────────────────
def main() -> None:
    log.info("Podcast newsletter daemon starting.")
    schedule.every().day.at("09:00").do(run_newsletter)
    log.info("Scheduled daily job at 09:00.")
    catchup_if_needed()
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
