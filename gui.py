"""
Desktop UI for Nocturna, built with Tkinter (ships with Python -- no extra
install beyond what's already in requirements.txt).

This does NOT reimplement any assistant logic. It calls the exact same
speech_io.listen() and main.respond() functions the command-line version
(main.py) uses, so the knowledge base, intent routing, and logging all
behave identically -- only the input/output presentation differs.

Listening runs on a background thread so the window stays responsive while
waiting for the microphone (Tkinter locks up if you block its main thread).

Run with:
    python gui.py
"""

import queue
import threading
import tkinter as tk
from tkinter import scrolledtext

import main as assistant
import reminders
import speech_io

_ui_queue = queue.Queue()


def _on_speak(text: str) -> None:
    """Registered with speech_io so every speak() call also reaches the UI."""
    _ui_queue.put(("assistant", text))


speech_io.register_listener(_on_speak)


class NocturnaGUI:
    BG = "#11141c"
    PANEL = "#1b1f2b"
    ACCENT = "#5bc0be"
    TEXT = "#e8e8f0"
    MUTED = "#8a8fa3"
    YOU_TAG = "#5bc0be"
    ASSISTANT_TAG = "#f2c14e"

    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Nocturna — UTG Student Assistant")
        root.geometry("540x600")
        root.configure(bg=self.BG)
        root.minsize(420, 480)

        tk.Label(
            root, text="🌙 Nocturna", font=("Segoe UI", 20, "bold"),
            fg=self.TEXT, bg=self.BG,
        ).pack(pady=(18, 0))

        tk.Label(
            root, text="UTG Student Voice Assistant", font=("Segoe UI", 10),
            fg=self.MUTED, bg=self.BG,
        ).pack(pady=(0, 10))

        self.status_var = tk.StringVar(value="Idle — click Listen to start")
        self.status_label = tk.Label(
            root, textvariable=self.status_var, font=("Segoe UI", 10, "italic"),
            fg=self.ACCENT, bg=self.BG,
        )
        self.status_label.pack(pady=(0, 8))

        self.transcript = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, font=("Segoe UI", 10), bg=self.PANEL, fg=self.TEXT,
            insertbackground=self.TEXT, relief=tk.FLAT, padx=12, pady=12, bd=0,
        )
        self.transcript.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 14))
        self.transcript.tag_config("you", foreground=self.YOU_TAG, font=("Segoe UI", 10, "bold"))
        self.transcript.tag_config("assistant", foreground=self.ASSISTANT_TAG, font=("Segoe UI", 10, "bold"))
        self.transcript.config(state=tk.DISABLED)

        self.listen_button = tk.Button(
            root, text="🎤  Listen", font=("Segoe UI", 12, "bold"),
            bg=self.ACCENT, fg=self.BG, activebackground="#4aa9a7",
            relief=tk.FLAT, padx=24, pady=10, cursor="hand2",
            command=self.start_listening,
        )
        self.listen_button.pack(pady=(0, 18))

        self._append("assistant", "Hello, I'm Nocturna, your UTG student assistant. "
                                   "Click Listen and ask me something.")

        due = reminders.get_due_reminders()
        if due:
            count_phrase = "1 reminder" if len(due) == 1 else f"{len(due)} reminders"
            items = "; ".join(r["description"] for r in due)
            self._append("assistant", f"You have {count_phrase} due: {items}.")

        self.root.after(100, self._poll_queue)

    def _append(self, who: str, text: str) -> None:
        self.transcript.config(state=tk.NORMAL)
        label = "You" if who == "you" else "Nocturna"
        self.transcript.insert(tk.END, f"{label}: ", who)
        self.transcript.insert(tk.END, f"{text}\n\n")
        self.transcript.see(tk.END)
        self.transcript.config(state=tk.DISABLED)

    def _poll_queue(self) -> None:
        """Runs on the main thread; drains messages the background thread posted."""
        try:
            while True:
                who, text = _ui_queue.get_nowait()
                self._append(who, text)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)

    def start_listening(self) -> None:
        self.listen_button.config(state=tk.DISABLED, text="🎙  Listening…")
        self.status_var.set("Listening…")
        threading.Thread(target=self._listen_and_respond, daemon=True).start()

    def _listen_and_respond(self) -> None:
        """Runs on a background thread -- must not touch Tkinter widgets directly."""
        voice_data = speech_io.listen()
        if voice_data:
            _ui_queue.put(("you", voice_data))
            self.root.after(0, lambda: self.status_var.set("Thinking…"))
        # Note: respond()'s return value (False on "goodbye") is ignored here
        # on purpose -- closing the whole window on a spoken "goodbye" isn't
        # the behaviour you want in a GUI. Say it and the assistant replies,
        # but the window stays open; close it with the window controls.
        assistant.respond(voice_data)
        self.root.after(0, self._reset_button)

    def _reset_button(self) -> None:
        self.listen_button.config(state=tk.NORMAL, text="🎤  Listen")
        self.status_var.set("Idle — click Listen to start")


def main():
    root = tk.Tk()
    NocturnaGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
