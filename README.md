# Nocturna — UTG Student Voice Assistant

A restructured version of the original single-file prototype, extended with
a retrieval-based knowledge base of University of The Gambia information.

## What changed from the original script

- **Split into modules** (`speech_io.py`, `utilities.py`, `knowledge_base.py`,
  `logger.py`, `main.py`) instead of one file, so each piece can be tested,
  extended, or swapped independently — e.g. for a future local-language ASR
  backend (see the `TODO` in `speech_io.py`).
- **Fixed the "tell me a joke" bug**: the original checked `"Tell me a joke"`
  (capitalized) against already-lowercased input, so it could never match.
  It's lowercase everywhere now.
- **Removed the hard-coded OpenWeatherMap API key.** It's read from the
  `OPENWEATHER_API_KEY` environment variable instead (see Setup below). If
  it's not set, the weather feature tells the user it isn't configured
  rather than silently failing.
- **Replaced `exit()` with a graceful loop exit**, and added a
  `KeyboardInterrupt` handler so Ctrl+C says goodbye instead of crashing out.
- **Added a UTG knowledge base** (`utg_knowledge.json`) with retrieval via
  TF-IDF + cosine similarity (`knowledge_base.py`), replacing keyword
  matching for anything UTG-specific. This is the piece your dissertation's
  RQ1 is about — you can A/B it against a pure keyword baseline.
- **Added interaction logging** (`logger.py` → `logs/interactions.csv`) so
  every query, matched intent/knowledge-base source, confidence score, and
  response time is recorded automatically. This is your evaluation data —
  no separate instrumentation needed.
- **Added a desktop UI** (`gui.py`, Tkinter) as a lightweight alternative to
  the terminal loop. It calls the exact same `speech_io.listen()` and
  `main.respond()` functions as the CLI version — no logic is duplicated,
  only the display differs. Listening runs on a background thread so the
  window doesn't freeze while waiting for the microphone.
- **Added a web UI** (`app.py` + `templates/` + `static/`, Flask) for a more
  polished, demo-ready interface: a central glowing control you tap to
  speak, an animated listening state, a conversation transcript, and a
  text-input fallback for typing a question instead of using the mic. It's
  served locally only (`127.0.0.1`) — your browser is just the display;
  listening and speaking still happen on your machine exactly as before.
  This is the one worth showing in your viva/demo.
- **Added two more retrieval methods and an evaluation harness**
  (`retrieval_methods.py`, `evaluate.py`, `eval/`). The assistant no longer
  relies on a single TF-IDF implementation — it can run on a keyword
  baseline, TF-IDF, or pretrained sentence embeddings, and `evaluate.py`
  benchmarks all three on a labelled 70-query test set so you have real
  accuracy/latency numbers to report instead of just a demo. See
  "Comparing retrieval methods" below.
- **Added a structured course catalog** (`course_catalog.py` +
  `data/programs.json`) covering Computer Science, Telecommunication, and
  Information Systems — prerequisites, credit hours, electives, and full
  semester-by-semester plans, answerable by voice or text. See "Course
  catalog" below for what was and wasn't included, and why.
- **Added personal reminders** (`reminders.py`) — "remind me to X in N
  days" (or "tomorrow" / "today" / an exact date), plus "what are my
  reminders". Due reminders are announced automatically on startup in the
  CLI, GUI, and web UI, each only once. This is the feature that most
  directly answers "why not just use email/WhatsApp" — see the section
  below.
- **Made `speak()` fail gracefully.** If text-to-speech or audio playback
  hits a network/API hiccup, the assistant now logs it and continues in
  text-only mode for that one reply instead of crashing the whole
  interaction — this mattered once there was a web request that shouldn't
  die because of one TTS error.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

**Install PyAudio first** (it needs the PortAudio C library, so a plain
`pip install` often fails on its own):

- **Windows**: `pip install pipwin && pipwin install pyaudio`
- **macOS**: `brew install portaudio && pip install pyaudio`
- **Linux (Debian/Ubuntu)**: `sudo apt-get install portaudio19-dev && pip install pyaudio`

Then install everything else:

```bash
pip install -r requirements.txt
```

Set your weather API key (optional — everything else works without it):

```bash
export OPENWEATHER_API_KEY="your_key_here"      # macOS/Linux
setx OPENWEATHER_API_KEY "your_key_here"        # Windows (new terminal after)
```

Run the command-line version:

```bash
python main.py
```

Or run the web UI instead — a polished browser interface with a central
"tap to speak" control, a live conversation transcript, and a text-input
fallback for when you don't want to rely on the mic (handy for demos):

```bash
python app.py
```

Then open **http://127.0.0.1:5000** in your browser. This runs entirely on
your own machine — it is not exposed to the internet — and still uses your
real microphone and speakers exactly like `main.py` does; the browser just
renders the interface.

There's also a simpler Tkinter desktop window if you'd rather not run a
local web server:

```bash
python gui.py
```

`gui.py` uses Tkinter, which ships with Python on Windows and macOS. On
Linux it's sometimes a separate package:

```bash
sudo apt-get install python3-tk    # Debian/Ubuntu
```

## Where the knowledge-base data came from

`utg_knowledge.json` was built from publicly available pages on
**utg.edu.gm** (Home, Schools & Faculties, the School of ICT page,
Undergraduate Admissions, and the Students Guide), accessed **1 October
2026**. Each entry is a paraphrased summary with a `source` field noting
which page it came from — the answers are rewritten for spoken delivery,
not copied text.

**Important before you rely on this for real students or for your final
submission:**
- Fees, admission requirements, and contact details on a university website
  change. Verify each fact with the relevant office (Registry, School of
  ICT, Admissions) before presenting this as authoritative — your ethics
  section already commits to getting institutional sign-off, and this is
  exactly the kind of content that needs it.
- This is a **small pilot set (20 entries)**, deliberately scoped to the
  Schools & Faculties / ICT / Admissions area as a starting point. Expanding
  it with the academic calendar, student handbook, and examination rules
  (once you have those documents) is the natural next step, and is already
  in your proposal's Phase 1.

## How to use the logs for your evaluation chapter

Every query appends a row to `logs/interactions.csv`:

| column | meaning |
|---|---|
| `query` | what the user said (lowercased transcript) |
| `intent` | `utility` command name, `knowledge_base`, or `unmatched` |
| `source` | which KB entry answered it (or blank) |
| `confidence` | similarity score (0–1) |
| `response_time_s` | time from query to spoken response |

Load this into pandas or Excel after a test session to compute intent
accuracy, hit rate, and latency distributions directly.

## Course catalog: prerequisites, credit hours, electives, semester plans

Beyond the general FAQ knowledge base, the assistant now has a **structured
course catalog** (`course_catalog.py` + `data/programs.json`) covering all
three SITC departments -- Computer Science, Telecommunication, and
Information Systems (full 4-year study plans, 47-133 courses each,
electives, and programme-level credit-hour requirements).

This is deliberately a *different* system from the FAQ retrieval methods
(`retrieval_methods.py`): "what is the prerequisite for CPS 402" needs an
exact structured answer, not a similarity match against a bank of Q&A
pairs, so it's answered by direct lookup instead. Try asking (by voice or
typed):

- "What is the prerequisite for CPS 402?"
- "How many credit hours is ICT 210?"
- "What are the major requirements for computer science?"
- "What are the information systems electives?"
- "What courses are in year 3 semester 1 for information systems?"
- "Tell me about INS 403."

### Where the data came from, and what was deliberately left out

- `BSc_Computer_Science.docx` and `BSc_Telecom_2022.docx` (semester-by-
  semester study plans) and the Information Systems study plan PDF are the
  full source for `data/programs.json`. `data/build_catalog.py` is the
  transcription script, kept for auditability -- every semester's credit
  total is checked by assertion against the "Total" row printed in its own
  source document (and the Information Systems section additionally checks
  against that PDF's own printed "148 credits, 47 courses" summary). All
  checks passed.
- Two photographed "Major/Minor Requirements" sheets were **not** used for
  their detailed course-code tables. The student confirmed those photos are
  from a different catalog year than the docx/PDF study plans, and their
  tables used different course codes and credit hours for what should be
  the same courses (e.g. "ICT 205 Data Structure & Algorithms" in the photo
  vs. "ICT 210 Data Structure & Algorithms" in the docx) -- merging them
  would have risked giving students a wrong course code. Only the short
  overview paragraphs at the top of those photos (total credit hours
  required, GER/DER/core/elective structure) were kept, as
  `major_requirements_overview` / `minor_overview` text in
  `data/programs.json` -- those don't name specific course codes, so they
  don't carry the same risk.
- A Computer Science **minor** exists (confirmed by that overview text) but
  has no structured course-by-course lookup here, for the same reason --
  the only source for its specific course list was the unreliable
  photographed table.

### Extending this later

Once you have the current, verified Computer Science minor course list
(or if the department confirms the docx study plans are themselves
outdated), add it the same way: extend `data/build_catalog.py` following
the existing pattern, with an assertion checking your transcription against
the source's own printed totals, then re-run it to regenerate
`data/programs.json`.

## Why this isn't redundant with email/WhatsApp

UTG already pushes academic updates to students by email and WhatsApp
group, so "the assistant tells you things" isn't by itself a reason to use
it. The actual differentiation is structural, not cosmetic:

1. **Pull vs. push.** Email and WhatsApp are broadcast channels — one
   message, sent once, to everyone, in chronological order. Finding "what
   did the registrar say about deferment three weeks ago" means scrolling.
   This assistant is a standing index: the same fact, answerable instantly,
   whenever you ask, for as long as it's in the knowledge base.

2. **Personal, proactive reminders** (`reminders.py`, new this round) — the
   one thing a group broadcast genuinely cannot do. A WhatsApp group can
   tell 300 students "registration closes Friday." It can't tell *you*,
   specifically, three weeks later, that you still haven't registered and
   it's due tomorrow. `remind me to <thing> in <N> days` does exactly that,
   and the assistant checks and announces due reminders on startup.

3. **One interface instead of three.** Right now a student's academic life
   is split across email, a WhatsApp group, and the registrar's office.
   Once populated with real handbook/calendar content, this assistant
   becomes a single place to ask, regardless of which channel the original
   information came from.

4. **Accessible hands-free**, which matters concretely for late-night
   studying (the whole reason for the Nocturna framing) and for anyone who
   finds navigating text-heavy admin pages inconvenient.

What this does **not** claim: it isn't trying to replace official
communication, and it isn't claiming to have better or more current
information than the Registry — it's a faster way to retrieve and be
reminded of things that are otherwise scattered and easy to lose track of.
That's the honest version of the pitch, and it's the one worth defending.

### Extending with real procedural content

I looked for UTG's own published transcript/deferment/add-drop procedures
to add to the knowledge base and found nothing on the public website —
every result was from a different university entirely. That content almost
certainly exists only in a printed or internal student handbook. Rather
than invent steps, fees, or deadlines for something students could get
real consequences from getting wrong, `utg_knowledge.json` is ready for you
to add real entries once you have that handbook (see your proposal's Phase
1). The format is simple — just append objects shaped like:

```json
{
  "question": "how do i apply for deferment",
  "answer": "<the real, verified procedure, written for spoken delivery>",
  "source": "UTG Student Handbook, obtained from Registry, <date>"
}
```

That's the single highest-value content addition left for this project,
and it's a content task, not an engineering one — the retrieval system
already handles it.

## Comparing retrieval methods (the evaluation that makes this a thesis, not a demo)

The assistant now has **three interchangeable retrieval methods**
(`retrieval_methods.py`), all sharing one interface so they can be
benchmarked against each other on the same labelled test set:

| Method | What it does | Needs internet? |
|---|---|---|
| `keyword` | Token-overlap scoring — a fair, generalised version of the *original* prototype's `"x" in voice_data` approach. This is your baseline. | No |
| `tfidf` | TF-IDF + cosine similarity. What the assistant used right before this upgrade. | No |
| `embeddings` | Pretrained sentence-embedding similarity (`all-MiniLM-L6-v2`), matches on *meaning* rather than shared words. | Yes, first run only (downloads ~90MB, then cached) |

### Running the evaluation

```bash
python evaluate.py
```

This runs all three methods against `eval/test_set.json` — 70 labelled
queries across four categories (direct, paraphrased, noisy/spoken-style,
and out-of-scope) — and produces:

- `eval/results.csv` — every (method, query) pair, with what it matched,
  its confidence score, and whether it was correct. **This is your
  error-analysis data** — filter to `correct == False` for one method to
  see exactly what it gets wrong and why.
- `eval/summary.csv` — one row per method: overall accuracy, per-category
  accuracy, and average latency.
- `eval/comparison_chart.png` — bar chart of overall accuracy, ready to
  drop into your results chapter.

I ran `keyword` and `tfidf` already (my dev environment's network doesn't
reach Hugging Face, so I couldn't download the embedding model here) —
real results, not estimates:

| Method | Overall | Direct | Paraphrase | Noisy | Out-of-scope |
|---|---|---|---|---|---|
| keyword | 78.6% | 100% | 60% | 80% | 75% |
| tfidf | 81.4% | 100% | 70% | 90% | 70% |
| embeddings | *run it yourself* | | | | |

Notice TF-IDF doesn't win on *everything* — it's better at paraphrase and
noisy queries but slightly worse on out-of-scope rejection (more false
positives on queries that happen to share words like "utg"). That
trade-off, not just a single accuracy number, is the actual finding worth
discussing. Run `python evaluate.py` yourself to get the real embeddings
numbers, then decide — don't assume embeddings "should" win; report what
the data shows.

### Using the result

Once you know which method performs best, set it as the live assistant's
default in `config.py`:

```python
RETRIEVAL_METHOD = "embeddings"   # or "tfidf" / "keyword"
```

`main.py`, `gui.py`, and `app.py` all pick this up automatically through
`knowledge_base.py` — nothing else needs to change.

### Extending the test set

70 queries is a reasonable starting evaluation set for a tight timeline,
but it's hand-authored by me as a starting point, not independently
validated — `eval/test_set.json` is a plain JSON list, so adding more
queries (ideally ones real students actually ask, once you have pilot
users) is just appending more
`{"query": ..., "expected_question": ..., "category": ...}` objects.
`expected_question` must exactly match a `question` field in
`utg_knowledge.json`, or be `null` for an out-of-scope query.

## About the web UI's design

The look is deliberately a calm, late-night "study companion" aesthetic
(deep indigo background, a single warm glowing orb) rather than a generic
dashboard — it leans into the Nocturna name itself. It's a single dark
theme by design, not a light/dark toggle. If you want to reskin it:
colors are CSS variables at the top of `static/style.css`, so changing the
palette is a matter of editing a handful of hex values in one place rather
than hunting through the file.

## Troubleshooting: "I'm not getting any voice commands"

Run `python mic_test.py` by itself first — it isolates which stage is
failing before you touch the full assistant:

1. **No microphones listed at all** → OS/driver issue, not this code. Check
   your system sound settings recognize the mic before anything else.
2. **"WaitTimeoutError" / nothing captured** → almost always one of:
   - **macOS**: System Settings → Privacy & Security → Microphone → make
     sure Terminal (or your IDE) is checked. macOS silently denies mic
     access to apps that aren't approved — no error dialog, it just
     captures silence.
   - **Windows**: Settings → Privacy & Security → Microphone → make sure
     "Let apps access your microphone" is on.
   - **Wrong input device selected**: if you have multiple microphones
     (e.g., a webcam mic and a headset), `sr.Microphone()` uses the OS
     default, which may not be the one you're speaking into. Run
     `mic_test.py` to see the device list, then test a specific one with
     `sr.Microphone(device_index=N)` (the file has a commented example at
     the bottom).
   - **Mic muted at the hardware or OS level.**
3. **Audio is captured but "UnknownValueError"** → the mic works, but
   recognition failed. Try speaking louder/closer, reduce background noise,
   or check you're not picking up a low-quality device (e.g., a laptop's
   built-in mic from across the room).
4. **"RequestError"** → `recognize_google()` needs internet access; check
   your connection or firewall.

If `mic_test.py` succeeds but the full assistant still doesn't respond,
the mic itself is fine and the issue is elsewhere in `main.py`/`speech_io.py`
— that's worth reporting separately with the terminal output you see.

## Known limitations

- Speech recognition (`recognize_google`) is English-only and depends on an
  external, unofficial Google API — it needs internet access and has
  informal rate limits. This is the same dependency the original prototype
  had; it's flagged in the proposal's Scope and Limitations section.
- The similarity threshold (`KB_SIMILARITY_THRESHOLD` in `config.py`, 
  currently `0.45`) was tuned on a handful of manual test queries, not a
  validated test set. Re-tune it once you've built your real evaluation
  question set.
- No local-language (Wolof) support yet — `speech_io.listen()` is the single
  function to replace when you get there.

## Suggested next steps

1. Expand `utg_knowledge.json` with academic calendar and handbook content
   once you have institutional permission to use it.
2. Build your 100–300 question evaluation set and re-tune the similarity
   threshold against it.
3. Add a UI (Tkinter for a quick desktop app, or Streamlit for a browser
   demo) — the modular split here makes that a matter of calling `respond()`
   from button/input callbacks instead of the `while True` loop in `main.py`.
4. When ready, swap `speech_io.listen()` for a fine-tuned Wolof Whisper
   model as discussed separately.
