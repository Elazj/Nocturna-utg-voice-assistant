"""
Nocturna: a voice-based assistant for University of The Gambia students.

Architecture (see dissertation Section 6):
    speech_io    -> speech-to-text / text-to-speech
    utilities    -> generic actions (weather, jokes, search, notes)
    knowledge_base -> UTG-specific Q&A retrieval
    logger       -> records every interaction for evaluation

Run with:
    python main.py
"""

import time
from time import ctime

import course_catalog as catalog
import reminders
import utilities as utils
from config import WAKE_GREETING
from knowledge_base import KnowledgeBase
from logger import log_interaction
from speech_io import listen, speak

kb = KnowledgeBase()


def handle_utility_command(voice_data: str):
    """
    Checks voice_data against the fixed set of generic commands.
    Returns (handled: bool, intent_label: str or None, should_continue: bool).
    Order matters a little (more specific phrases before generic ones), but
    this is exactly the brittle part the knowledge base is meant to replace
    for anything UTG-specific -- these are kept only for simple utilities.
    """
    if "what is your name" in voice_data:
        speak("My name is Nocturna, the UTG student assistant.")
        return True, "identity", True

    if "what time is it" in voice_data:
        speak(ctime())
        return True, "time", True

    if "joke" in voice_data:
        speak(utils.tell_joke())
        return True, "joke", True

    if "weather" in voice_data:
        city = listen("Which city do you want the weather for?")
        if city:
            speak(utils.get_weather(city))
        return True, "weather", True

    if "search" in voice_data:
        query = listen("What do you want to search for?")
        if query:
            speak(utils.web_search(query))
        return True, "web_search", True

    if "find location" in voice_data or "find the location" in voice_data:
        place = listen("What location do you want to search for?")
        if place:
            speak(utils.find_location(place))
        return True, "location", True

    if "note" in voice_data or "write" in voice_data:
        content = listen("What would you like me to write?")
        if content:
            speak(utils.save_note(content))
        return True, "note", True

    if "remind me" in voice_data or "set a reminder" in voice_data:
        # Try to parse a complete request from one line first (works for
        # typed input via the web UI without opening the mic, and is more
        # natural for voice too -- "remind me to X in three days" in one go).
        description, due_text = reminders.parse_reminder_command(voice_data)
        if description and due_text:
            success, message = reminders.add_reminder(description, due_text)
            speak(message)
        else:
            # Fell back to asking conversationally -- fine for the CLI/voice
            # flow, but note this still opens the mic even if the original
            # request came in as typed text with incomplete details.
            description = listen("What should I remind you about?")
            if description:
                due_text = listen(
                    "When should I remind you? Say a date like "
                    "twenty twenty six dash eleven dash five, or say "
                    "something like 'in three days'."
                )
                if due_text:
                    success, message = reminders.add_reminder(description, due_text)
                    speak(message)
        return True, "set_reminder", True

    if "my reminders" in voice_data or "list reminders" in voice_data or "what reminders" in voice_data:
        upcoming = reminders.get_upcoming_reminders()
        if not upcoming:
            speak("You don't have any upcoming reminders.")
        else:
            lines = [f"{r['description']} on {r['due_date']}" for r in upcoming]
            speak("Here are your upcoming reminders: " + "; ".join(lines))
        return True, "list_reminders", True

    catalog_response = catalog.handle_catalog_query(voice_data)
    if catalog_response:
        speak(catalog_response)
        return True, "course_catalog", True

    if "help" in voice_data or "what can you do" in voice_data:
        speak(
            "I can answer questions about UTG admissions, schools, fees and "
            "contacts, including detailed course information for Computer "
            "Science, Telecommunication, and Information Systems -- "
            "prerequisites, credit hours, electives, and semester plans. "
            "I can also tell you the time or a joke, check the weather, "
            "search the web, find a location, save a note, or set a "
            "reminder for a deadline. Say 'goodbye' any time to exit."
        )
        return True, "help", True

    if "exit" in voice_data or "quit" in voice_data or "goodbye" in voice_data:
        speak("Goodbye! Have a great day.")
        return True, "exit", False

    return False, None, True


def respond(voice_data: str) -> bool:
    """Returns False when the assistant should stop running."""
    if voice_data.strip() == "":
        return True

    start = time.time()
    handled, intent, should_continue = handle_utility_command(voice_data)

    if handled:
        log_interaction(voice_data, intent, "utility", 1.0, time.time() - start)
        return should_continue

    # Not a generic command -- try the UTG knowledge base.
    answer, matched_question, confidence, source = kb.search(voice_data)
    if answer:
        speak(answer)
        log_interaction(voice_data, "knowledge_base", source, confidence, time.time() - start)
    else:
        speak(
            "I'm still learning. Can you try asking that another way, or "
            "say 'help' to hear what I can do?"
        )
        log_interaction(voice_data, "unmatched", "none", confidence, time.time() - start)

    return True


def main():
    time.sleep(1)
    speak(WAKE_GREETING)

    due = reminders.get_due_reminders()
    if due:
        count_phrase = "1 reminder" if len(due) == 1 else f"{len(due)} reminders"
        items = "; ".join(r["description"] for r in due)
        speak(f"Before we start, you have {count_phrase} due: {items}.")

    running = True
    try:
        while running:
            voice_data = listen()
            running = respond(voice_data)
    except KeyboardInterrupt:
        speak("Goodbye!")


if __name__ == "__main__":
    main()
