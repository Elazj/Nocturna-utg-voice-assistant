"""
Speech input/output for Nocturna.

This wraps the same libraries as the original prototype (SpeechRecognition +
gTTS + playsound), but isolates them behind speak()/listen() so the rest of
the codebase doesn't need to know how audio I/O works. That separation is
also what makes it possible to later swap recognize_google() for a
fine-tuned local-language model (see the TODO below) without touching
anything else in the project.
"""

import os
import random

import playsound
import speech_recognition as sr
from gtts import gTTS

from config import MIC_DEVICE_INDEX

_recognizer = sr.Recognizer()

# Optional listeners notified every time speak() is called, so a UI (see
# gui.py) can display what the assistant says without main.py/utilities.py
# needing to know a UI exists. The CLI version (main.py) works unchanged
# because it just doesn't register any listeners.
_listeners = []


def register_listener(callback) -> None:
    """callback receives the text every time speak() is called."""
    _listeners.append(callback)


def speak(text: str) -> None:
    """
    Convert text to speech and play it.

    Text output (console print + any registered UI listener, see
    register_listener above) always happens, even if audio fails. Audio
    failures (no internet, gTTS/Google blocking the request, a broken audio
    driver) are caught and logged rather than raised, so one bad network
    moment degrades to text-only instead of crashing the whole assistant --
    important for the web/GUI front ends, where an unhandled exception here
    would otherwise take down the entire request.
    """
    print(f"Nocturna: {text}")
    for callback in _listeners:
        callback(text)

    try:
        tts = gTTS(text=text, lang="en")
        filename = f"audio-{random.randint(1, 10_000_000)}.mp3"
        tts.save(filename)
        try:
            playsound.playsound(filename)
        finally:
            if os.path.exists(filename):
                os.remove(filename)
    except Exception as exc:
        print(f"[speech_io] Couldn't play audio for that reply ({exc}). "
              f"Continuing in text-only mode for this response.")


def listen(prompt: str = None, timeout: int = 5) -> str:
    """
    Capture one utterance from the microphone and return it lowercased.

    Returns "" (and speaks an explanation) on timeout, unrecognized speech,
    or a speech-service error, so callers can just check `if voice_data:`.

    TODO (future language-support work): recognize_google() is English-only
    and depends on an external API. To add Wolof/local-language support,
    this is the single function to replace -- swap it for a call to a
    fine-tuned Whisper model (see the project notes on Wolof ASR) while
    keeping the same (prompt, timeout) -> str interface.
    """
    with sr.Microphone(device_index=MIC_DEVICE_INDEX) as source:
        if prompt:
            speak(prompt)
        _recognizer.adjust_for_ambient_noise(source)
        try:
            audio = _recognizer.listen(source, timeout=timeout)
            voice_data = _recognizer.recognize_google(audio)
            print(f"You said: {voice_data}")
            return voice_data.lower()
        except sr.WaitTimeoutError:
            speak("You were silent for too long. Try again.")
        except sr.UnknownValueError:
            speak("Sorry, I did not understand that.")
        except sr.RequestError:
            speak("Sorry, my speech service is down.")
        return ""
