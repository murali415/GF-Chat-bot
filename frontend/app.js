// Priya frontend — backend serves both API + this page, so same-origin
// works everywhere: local uvicorn (:8000) and Vercel.
const API = "";

const $ = (id) => document.getElementById(id);
const messagesEl = $("messages"), inputEl = $("input");

const MOOD_COLORS = {
  romantic: "#e91e63", happy: "#ff6fa5", playful: "#ff9f43",
  neutral: "#a29bfe", annoyed: "#f39c12", upset: "#636e72", angry: "#d63031",
};

// page background tint per mood — happy keeps the default body gradient
const MOOD_BG = {
  romantic: "linear-gradient(135deg,#ffe0ea,#ffc2d9 45%,#f0c8f5)",
  happy: "",
  playful: "linear-gradient(135deg,#fff4e2,#ffe3b8 45%,#ffd9e8)",
  neutral: "linear-gradient(135deg,#eef0fa,#dfe3f5 45%,#d8e9ff)",
  annoyed: "linear-gradient(135deg,#fff3dc,#ffe0ae 45%,#ffd9c2)",
  upset: "linear-gradient(135deg,#edf1f7,#dbe2ef 45%,#cfd9e8)",
  angry: "linear-gradient(135deg,#ffe3e3,#ffc9c9 45%,#f2b8c6)",
};
let moodLayer = 0;
function applyMoodBg(label) {
  const a = $("moodBgA"), b = $("moodBgB");
  if (!a || !b) return;
  const g = MOOD_BG[label];
  if (!g) {
    // default mood: fade both tint layers out, body gradient shows
    a.classList.remove("show");
    b.classList.remove("show");
    return;
  }
  // crossfade: paint the hidden layer, then flip visibility (smooth always)
  const showEl = moodLayer % 2 === 0 ? a : b;
  const hideEl = moodLayer % 2 === 0 ? b : a;
  showEl.style.background = g;
  showEl.classList.add("show");
  hideEl.classList.remove("show");
  moodLayer++;
}

// airy background: a few floating emojis + soft CSS bokeh (no emoji font needed)
(() => {
  const bg = $("bgHearts");
  const rnd = (a, b) => a + Math.random() * (b - a);
  // 1) minimal emojis, small and faint
  const glyphs = ["💖", "🌸", "✨", "💕", "⭐", "🦋"];
  for (let i = 0; i < 10; i++) {
    const s = document.createElement("span");
    s.textContent = glyphs[i % glyphs.length];
    s.style.left = rnd(2, 98) + "vw";
    s.style.bottom = "-40px";
    s.style.fontSize = rnd(11, 20) + "px";
    s.style.animationDelay = rnd(0, 11) + "s";
    s.style.animationDuration = rnd(9, 15) + "s";
    bg.appendChild(s);
  }
  // 2) soft blurred pastel blobs (radial-gradient in CSS — no filter:blur, cheap to animate)
  const blobs = ["#ffc4d6", "#e3c8f5", "#ffd9e8", "#cfe4ff", "#ffe3b3"];
  for (let i = 0; i < 7; i++) {
    const b = document.createElement("i");
    const sz = rnd(40, 110);
    b.style.width = b.style.height = sz + "px";
    b.style.left = rnd(0, 95) + "vw";
    b.style.top = rnd(5, 90) + "vh";
    b.style.color = blobs[i % blobs.length];
    b.style.animationDelay = rnd(0, 6) + "s";
    bg.appendChild(b);
  }
  // 3) tiny outline bubbles
  for (let i = 0; i < 6; i++) {
    const b = document.createElement("b");
    const sz = rnd(8, 26);
    b.style.width = b.style.height = sz + "px";
    b.style.left = rnd(0, 96) + "vw";
    b.style.top = rnd(10, 90) + "vh";
    b.style.animationDelay = rnd(0, 8) + "s";
    bg.appendChild(b);
  }
})();

function addMsg(text, who, meta = "", scroll = true) {
  const d = document.createElement("div");
  d.className = "msg " + who;
  d.innerHTML = `<div>${escapeHtml(text)}</div>` + (meta ? `<div class="meta">${meta}</div>` : "");
  messagesEl.appendChild(d);
  pruneMessages();
  if (scroll) {
    // one layout per frame, not per message — smooth even on software rendering
    requestAnimationFrame(() => {
      messagesEl.scrollTop = messagesEl.scrollHeight;
    });
  }
  return d;
}
// cap live DOM: long sessions appended forever (400+ nodes = janky scroll)
function pruneMessages() {
  const MAX_NODES = 120; // ~60 turns, matches history window
  while (messagesEl.children.length > MAX_NODES) {
    messagesEl.removeChild(messagesEl.firstChild);
  }
}
function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
}

function setMood(m) {
  $("moodEmoji").textContent = m.emoji || "🥰";
  $("moodLabel").textContent = m.label || "happy";
  $("moodScore").textContent = m.score ?? 70;
  $("moodPill").style.background = MOOD_COLORS[m.label] || "#2b2b3a";
  $("loveBar").style.width = (m.score ?? 70) + "%";
  $("lovePct").textContent = Math.round(m.score ?? 70) + "%";
  applyMoodBg(m.label || "happy");
}

function setMemories(mems) {
  // memories panel removed from UI — kept as no-op for compatibility
}

async function refreshState() {
  try {
    const r = await fetch(API + "/api/history?limit=50");
    const d = await r.json();
    // batch: old code appended + forced layout (scrollTop) 60x = load jank.
    // Build off-DOM, append once, scroll once.
    messagesEl.innerHTML = "";
    const frag = document.createDocumentFragment();
    const paint = (text, who, meta) => {
      const el = document.createElement("div");
      el.className = "msg " + who;
      el.innerHTML = `<div>${escapeHtml(text)}</div>` + (meta ? `<div class="meta">${meta}</div>` : "");
      frag.appendChild(el);
    };
    if (!d.history.length) {
      paint("Hii babe!! 🥺💖 I've missed you... talk to me? Tell me how your day went, I wanna hear everything!", "gf", "Priya • just now");
    }
    d.history.slice(-30).forEach((t) => {
      paint(t.bf, "bf", "You");
      paint(t.gf, "gf", `Priya • ${t.mood || ""}`);
    });
    messagesEl.appendChild(frag);
    pruneMessages();
    requestAnimationFrame(() => {
      messagesEl.scrollTop = messagesEl.scrollHeight;
    });
    setMood(d.mood);
  } catch (e) {
    addMsg("⚠️ Backend not running. Start it with:  cd gf-chatbot/backend && uvicorn app:app --port 8000", "gf");
  }
}

async function send(text) {
  const name = $("bfName").value || "babe";
  addMsg(text, "bf", "You");
  inputEl.value = "";
  const typing = addMsg("Priya is typing... 💭", "gf", "");
  typing.classList.add("typing");
  $("peek").classList.add("show"); // 👧 pops up while she types
  try {
    const r = await fetch(API + "/api/chat", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, boyfriend_name: name }),
    });
    const d = await r.json();
    typing.remove();
    $("peek").classList.remove("show"); // reply sent → she ducks away
    addMsg(d.reply, "gf", `Priya • ${d.mood.label} ${d.mood.emoji}`);
    setMood(d.mood);
  } catch (e) {
    typing.remove();
    $("peek").classList.remove("show");
    addMsg("⚠️ Couldn't reach backend. Is uvicorn running on :8000?", "gf");
  }
}

$("composer").addEventListener("submit", (e) => {
  e.preventDefault();
  const t = inputEl.value.trim();
  if (t) send(t);
});
document.querySelectorAll(".quick button").forEach((b) =>
  b.addEventListener("click", () => send(b.dataset.q))
);
$("resetBtn").addEventListener("click", async () => {
  if (!confirm("Wipe Priya's memory and restart the relationship? 💔")) return;
  await fetch(API + "/api/reset", { method: "POST" });
  refreshState();
  setMemories([]);
});

refreshState();
