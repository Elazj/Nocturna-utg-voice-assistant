const orb = document.getElementById("orb");
const status = document.getElementById("status");
const transcript = document.getElementById("transcript");
const textForm = document.getElementById("text-form");
const textInput = document.getElementById("text-input");

const IDLE_LABEL = "Tap to ask a question";

function appendLine(who, text) {
  const line = document.createElement("div");
  line.className = `line ${who}`;

  const speaker = document.createElement("span");
  speaker.className = "speaker";
  speaker.textContent = who === "you" ? "You" : "Nocturna";

  const p = document.createElement("p");
  p.textContent = text;

  line.appendChild(speaker);
  line.appendChild(p);
  transcript.appendChild(line);
  transcript.scrollTop = transcript.scrollHeight;
}

function setBusy(isBusy, label) {
  orb.disabled = isBusy;
  orb.classList.toggle("listening", isBusy);
  status.textContent = label;
}

function showUnreachableError() {
  appendLine(
    "assistant",
    "I couldn't reach the assistant backend. Make sure app.py is still running in your terminal."
  );
}

async function sendListen() {
  setBusy(true, "Listening…");
  try {
    const res = await fetch("/api/listen", { method: "POST" });
    const data = await res.json();
    if (data.you) {
      appendLine("you", data.you);
    }
    (data.assistant || []).forEach((text) => appendLine("assistant", text));
  } catch (err) {
    showUnreachableError();
  } finally {
    setBusy(false, IDLE_LABEL);
  }
}

async function sendText(text) {
  setBusy(true, "Thinking…");
  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const data = await res.json();
    if (data.you) {
      appendLine("you", data.you);
    }
    (data.assistant || []).forEach((t) => appendLine("assistant", t));
  } catch (err) {
    showUnreachableError();
  } finally {
    setBusy(false, IDLE_LABEL);
  }
}

async function checkDueReminders() {
  try {
    const res = await fetch("/api/due_reminders");
    const data = await res.json();
    (data.due || []).forEach((text) => appendLine("assistant", text));
  } catch (err) {
    // Non-critical -- if this fails, the rest of the app still works.
  }
}

orb.addEventListener("click", sendListen);
checkDueReminders();

textForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const value = textInput.value.trim();
  if (!value) return;
  textInput.value = "";
  sendText(value);
});
