"""
Standalone microphone diagnostic.

Run this BY ITSELF first, before troubleshooting the full assistant:
    python mic_test.py              # uses the OS default input device
    python mic_test.py 19           # tests device index 19 specifically

It isolates three separate failure points: can PyAudio see a microphone at
all, can it actually capture audio from it, and can the recognition service
understand what was captured. Each prints a distinct message so you know
exactly which stage is failing.

If the default device test captures audio but recognition fails every time,
the most common cause on Windows with multiple audio devices (built-in mic,
Bluetooth headset, etc.) is that the OS default input isn't the device
you're actually speaking into. Pass an explicit index to test each
candidate device until one works, then set that device as your Windows
default (Settings > Sound > Input) so the assistant doesn't need the index
hard-coded.
"""

import sys

import speech_recognition as sr

print("=== Available microphones ===")
mic_names = sr.Microphone.list_microphone_names()
if not mic_names:
    print("No microphones detected at all. This is a driver/OS-level issue,")
    print("not a code issue -- check your OS sound settings before anything else.")
    raise SystemExit(1)

for i, name in enumerate(mic_names):
    print(f"  [{i}] {name}")

device_index = None
if len(sys.argv) > 1:
    try:
        device_index = int(sys.argv[1])
        print(f"\n=== Capture test (device index {device_index}: {mic_names[device_index]}) ===")
    except (ValueError, IndexError):
        print(f"\nInvalid device index: {sys.argv[1]!r}. Pick a number from the list above.")
        raise SystemExit(1)
else:
    print("\n=== Capture test ===")
    print("Using the DEFAULT microphone (no index given).")
    print("If this fails, try a specific index, e.g.: python mic_test.py 19")

print("\nSpeak clearly in the next 5 seconds...")

r = sr.Recognizer()
with sr.Microphone(device_index=device_index) as source:
    r.adjust_for_ambient_noise(source, duration=1)
    print(f"Ambient noise calibration done. Energy threshold: {r.energy_threshold:.1f}")
    try:
        audio = r.listen(source, timeout=5)
        print("Captured some audio. Sending to the recognition service...")
        text = r.recognize_google(audio)
        print(f"\nSUCCESS -- recognized: {text!r}")
        print("Your microphone and recognition pipeline both work.")
    except sr.WaitTimeoutError:
        print("\nFAILED at capture: no speech detected within 5 seconds.")
        print("Likely causes: mic is muted, OS denied Python mic permission,")
        print("or the wrong device is set as default. See README troubleshooting.")
    except sr.UnknownValueError:
        print("\nFAILED at recognition: audio was captured but not understood.")
        print("Try speaking louder/closer to the mic, reduce background noise,")
        print("or check that the right input device is selected.")
    except sr.RequestError as e:
        print(f"\nFAILED at recognition service: {e}")
        print("Check your internet connection -- recognize_google() needs it.")

# To test a specific microphone instead of the default one, uncomment below
# and set the index from the list printed above:
#
# with sr.Microphone(device_index=1) as source:
#     ...
