"""
Generic utility commands carried over from the original prototype:
weather, jokes, web search, map lookup, and note-taking.

These are kept separate from the UTG knowledge base (knowledge_base.py)
because they're general-purpose actions, not retrieved facts -- the
distinction matters for your evaluation, since accuracy for these should be
measured as "did it do the right action," not "did it retrieve the right
passage."
"""

import os
import time
import webbrowser
from urllib.parse import quote

import pyjokes
import requests

from config import NOTES_DIR, OPENWEATHER_API_KEY


def get_weather(city: str) -> str:
    if not OPENWEATHER_API_KEY:
        return (
            "Weather lookup isn't configured yet. Set the OPENWEATHER_API_KEY "
            "environment variable to enable it."
        )
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": OPENWEATHER_API_KEY, "units": "metric"}
    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        if str(data.get("cod")) != "200":
            return f"Sorry, I couldn't find the weather for {city}."
        weather = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        return f"The weather in {city} is {weather} with a temperature of {temp} degrees Celsius."
    except requests.RequestException:
        return "Sorry, I couldn't fetch the weather right now."


def tell_joke() -> str:
    return pyjokes.get_joke()


def web_search(query: str) -> str:
    url = "https://www.google.com/search?q=" + quote(query)
    webbrowser.get().open(url)
    return f"Here's what I found for {query}."


def find_location(place: str) -> str:
    url = "https://www.google.com/maps/place/" + quote(place)
    webbrowser.get().open(url)
    return f"Here's the location for {place}."


def save_note(content: str) -> str:
    os.makedirs(NOTES_DIR, exist_ok=True)
    filename = os.path.join(NOTES_DIR, f"note_{int(time.time())}.txt")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return f"I've saved your note as {os.path.basename(filename)}"
