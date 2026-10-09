"""
Lightweight reminder system for academic deadlines (registration windows,
exam dates, document submissions, etc.).

This is the one piece of this project that email and WhatsApp groups
structurally cannot do: track something specific to ONE student and
proactively resurface it, rather than broadcasting the same message to
everyone and relying on each person to remember it. A group chat can tell
300 students "registration closes Friday" -- it can't tell you, three weeks
later, "you still haven't registered and it's due tomorrow."

Reminders are stored in reminders.json -- plain JSON is enough for a
handful of personal reminders; no database needed. Each reminder has a
description, a due date, and whether it's already been announced once (so
the assistant doesn't repeat the same reminder every single time it starts
up, forever).
"""

import json
import os
import re
from datetime import date, timedelta

REMINDERS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reminders.json")


def _load():
    if not os.path.exists(REMINDERS_PATH):
        return []
    with open(REMINDERS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(reminders):
    with open(REMINDERS_PATH, "w", encoding="utf-8") as f:
        json.dump(reminders, f, indent=2)


def parse_due_date(text: str):
    """
    Deliberately simple spoken-friendly date parsing -- NOT a full natural-
    language date parser, just enough to cover realistic phrasing for a
    deadline said out loud or typed:
        "today"
        "tomorrow"
        "in 3 days" / "in 1 day"
        "2026-11-05"  (explicit ISO date -- also what the text/web UI can
                       send directly without needing to "speak" a date)
    Returns a date, or None if it couldn't be parsed.
    """
    text = text.strip().lower()

    if text == "today":
        return date.today()
    if text == "tomorrow":
        return date.today() + timedelta(days=1)

    match = re.search(r"in (\d+) days?", text)
    if match:
        return date.today() + timedelta(days=int(match.group(1)))

    match = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if match:
        try:
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            return None

    return None


_REMINDER_PATTERN = re.compile(
    r"remind me (?:to )?(.+?)\s+"
    r"(today|tomorrow|in \d+ days?|on \d{4}-\d{2}-\d{2}|\d{4}-\d{2}-\d{2})\s*$"
)


def parse_reminder_command(text: str):
    """
    Tries to parse a COMPLETE reminder request from one utterance, e.g.
        "remind me to submit my assignment in 3 days"
        "remind me to register for classes on 2026-11-05"
        "remind me to pay fees tomorrow"
    so a single typed line (or one spoken sentence) works without needing
    a follow-up microphone prompt -- important for the text/web UI, where
    opening the mic for a follow-up question would be the wrong behaviour
    for someone who just typed their request.

    Returns (description, due_text) if both were found, else (None, None)
    -- callers should fall back to asking conversationally in that case
    (fine for voice; a bare "remind me" typed with no details is a known
    edge case that still falls back to a mic prompt).
    """
    match = _REMINDER_PATTERN.search(text.strip())
    if not match:
        return None, None
    description = match.group(1).strip()
    due_text = match.group(2).strip()
    if due_text.startswith("on "):
        due_text = due_text[3:]
    if not description:
        return None, None
    return description, due_text


def add_reminder(description: str, due_text: str):
    """Returns (success: bool, message: str) -- message is spoken-ready
    either way (confirmation, or an explanation of what went wrong)."""
    due = parse_due_date(due_text)
    if due is None:
        return False, (
            "I couldn't understand that date. Try a date like "
            "twenty twenty six dash eleven dash five, or say "
            "something like 'in three days'."
        )
    reminders = _load()
    reminders.append(
        {"description": description, "due_date": due.isoformat(), "announced": False}
    )
    _save(reminders)
    return True, f"Okay, I'll remind you to {description} on {due.strftime('%B %d, %Y')}."


def get_due_reminders(mark_announced: bool = True):
    """Reminders due today or earlier that haven't been announced yet --
    this is what runs automatically when the assistant starts up."""
    reminders = _load()
    today = date.today()
    due = []
    changed = False
    for r in reminders:
        due_date = date.fromisoformat(r["due_date"])
        if due_date <= today and not r["announced"]:
            due.append(r)
            if mark_announced:
                r["announced"] = True
                changed = True
    if changed:
        _save(reminders)
    return due


def get_upcoming_reminders(within_days: int = 14):
    """Everything due within the next N days (including today) -- for when
    the student actively asks 'what are my reminders'. Doesn't mark them
    announced, since asking isn't the same as being proactively notified."""
    reminders = _load()
    today = date.today()
    cutoff = today + timedelta(days=within_days)
    upcoming = [
        r for r in reminders if today <= date.fromisoformat(r["due_date"]) <= cutoff
    ]
    upcoming.sort(key=lambda r: r["due_date"])
    return upcoming
