# Priya 💖 — Mood-Based Girlfriend Chatbot (RAG)

You are the **boyfriend**. Priya is your **girlfriend** who replies based on her **mood**.
Mood = **present tone** (how you talk now) + **past conversations** (RAG retrieval).

## Quick start (localhost)

```bash
cd /home/LabsKraft/gf-chatbot/backend
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

Then open 👉 http://localhost:8000

Or one-liner:
```bash
bash /home/LabsKraft/gf-chatbot/run.sh
```

## Deploy on Vercel (live link) 🚀

Push this folder to GitHub, then Vercel Dashboard → **Add New → Project** →
**Import** the repo. That's it — no build settings needed (`vercel.json`
routes everything to the FastAPI app, `requirements.txt` installs deps).

Notes:
- Cloud mode runs template replies over a bundled 10k
  episode sample (`data/conversations.sample.json`) — no Ollama on Vercel.
- For a thinking brain, add a free key — **Gemini** (aistudio.google.com →
  Get API key, free) or **Groq** (console.groq.com, free) — as `GEMINI_API_KEY`
  (model `PRIYA_GEMINI_MODEL`, default `gemini-2.0-flash`) or `OPENAI_API_KEY` +
  `OPENAI_ENDPOINT`, in Vercel → Project → Settings → Environment Variables
  (or exported locally). No code change needed — the brain chain is
  GPT-key → Gemini → local Ollama → templates, each with breakers + fallbacks.
- Serverless filesystem is ephemeral: chats persist per-instance only.

## How it works

```
You (boyfriend) ──message──▶ RAG retrieve (TF-IDF over past chats + seed memories)
                                │  top-3 memories + history_bias
                                ▼
                    MoodEngine: present tone analysis (sweet/rude/dry/sorry/caring/CAPS/emoji)
                                + past bias → mood score 0-100 → label
                                ▼
                    Reply: Ollama qwen2.5 (if running) else template bank, mood-conditioned
                                ▼
                    Save episode → data/conversations.json → shown in UI
```

**Moods:** 😍 romantic (85+) → 🥰 happy (70+) → 😉 playful (55+) → 🙂 neutral (40+) → 😒 annoyed (28+) → 😔 upset (15+) → 😡 angry (<15), plus 🔥 **spicy** — a sticky arousal state: desire lights it for ~3 turns (refused while she's hurt)

**Try this demo:**
1. `Good morning beautiful ❤️ I missed you` → she melts 🥰
2. `ok` → she notices the dry reply 😒
3. `whatever, not my problem` → upset/angry 😡
4. `I'm really sorry, forgive me please? 🥺` → she softens slowly (apologies heal more when she's hurt)

## Training (relationship memory) 🧠💘

Priya is trained on **229576 lived episodes + 30 long-term memories** across
**300+ real-life situation types incl. angry, playful, annoyed, jealous, sadness, convincing, emotional, goofy, stressed, funny, flirty (tasteful)** — written like actual chats (typos, slang,
lowercase, Hinglish mix), based on research into how real couples text:
specific over generic, short over paragraphs, presence over advice
("I'm just here" beats solutions), accountability + repair after fights.

| Category | Examples |
|---|---|
| Romance (12+5) | surprise dinner, love letters, long drives, good-morning texts |
| Wholesome intimacy (8+4) | cuddles, forehead kisses, hand-holding, slow dances, stargazing |
| Conflict (17) | late replies, phone addiction, jealousy, forgotten anniversary, dismissive "chill out", "you never listen" |
| Fights (8+5) | shouting, insults, stonewalling ("k"/"whatever"), breakup threats, lying |
| Repair (8+3) | sincere apologies, "I was wrong", promises, making-up dates |
| Desire (4) | explicit flirting → reciprocated heat (consensual adults, no lectures) |

```bash
cd /home/LabsKraft/gf-chatbot/backend
python3 fast_train10k.py      # full re-train (~108k episodes, ~30s)
python3 train_story.py        # story-time top-up (~14k episodes, ~20s, idempotent)
python3 train_spicy.py        # desire top-up (~11k [spicy] episodes, ~20s, idempotent)
python3 train_sensitive.py    # intimate top-up (~96k [intimate] episodes, ~2min, idempotent)
python3 -u stress_test.py     # hard test: 33 checks
```

**Last stress-test result: 33/33 passed** — mood direction, fight→repair arc
(72 → angry 2.0 after sustained cruelty → climbs back with sincere apologies),
RAG retrieval relevance, desire reciprocation, wholesome-intimacy warmth, live API.

**Repair realism:** one "sorry" doesn't fix a fight — mood climbs gradually
(2 → 11 → 20 → 28 → 38 → 45 → 58). Sarcastic "fine, SORRY" barely heals.
Sustained cruelty is remembered (`hurt_total` makes repeat offenses cut deeper).

## Files

```
gf-chatbot/
  backend/
    app.py           FastAPI: /api/chat /api/history /api/mood /api/memories /api/reset + serves frontend
    mood_engine.py   present-tone scoring + mood state 0-100
    rag_store.py     pure-Python TF-IDF RAG over past chats + long-term seed memories
    reply_engine.py  Ollama 0.5b (warmed, grounded replies win) → word-echo safety net;
    exact math solver, story-time tales, knowledge questions go to the brain first
    scenarios_story.py story-time cores (47 day/incident/memory archetypes)
    train_story.py   story-time top-up trainer (~14k [story] episodes)
    train_spicy.py   desire top-up trainer (~11k [spicy] episodes)
    train_sensitive.py intimate top-up trainer (~96k [intimate] episodes)
    requirements.txt
  frontend/
    index.html / style.css / app.js   cute chat UI + love meter + RAG memory panel
  data/
    seed_memories.json   long-term memories (editable!)
    conversations.json   auto-saved chat episodes
    mood.json            auto-saved mood state
  run.sh  README.md
```

## API

- `POST /api/chat` `{message, boyfriend_name}` → `{reply, mood, memories, source}`
- `GET /api/history?limit=50`, `GET /api/mood`, `GET /api/memories?q=...`, `POST /api/reset`

## Notes
- Works **fully offline** (template replies). If Ollama is running (`ollama serve`, model `qwen2.5:0.5b`), replies become more natural automatically.
- Edit `data/seed_memories.json` to give her more long-term memories of “you two”.
- Typing-peek character: **Codexa** chibi pet by gantrol via [OpenPets](https://openpets.dev) (unofficial fan content, sprite trimmed to idle+wave).
