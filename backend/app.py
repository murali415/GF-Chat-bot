"""Priya 💖 — mood-based girlfriend chatbot backend (FastAPI + RAG)."""
import atexit
import json
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from mood_engine import MoodEngine
from rag_store import RAGStore
from reply_engine import generate_reply, detect_topic

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
FRONTEND = os.path.join(BASE, "frontend")
CONV_PATH = os.path.join(DATA, "conversations.json")
MOOD_PATH = os.path.join(DATA, "mood.json")
SEED_PATH = os.path.join(DATA, "seed_memories.json")

os.makedirs(DATA, exist_ok=True)

# seed long-term memories (RAG long-term layer)
DEFAULT_SEED = [
    {"text": "Our first date: rainy evening, shared one umbrella and hot chai, he walked me home and we talked till 1am.", "mood": "romantic"},
    {"text": "He once surprised me with my favorite chocolate after I had a bad exam. I still remember how cared-for I felt.", "mood": "happy"},
    {"text": "We promised each other: no sleeping angry — always say goodnight properly even after fights.", "mood": "neutral"},
    {"text": "That time he was glued to his phone and replied 'ok' 'fine' all evening — I felt ignored and cried a little.", "mood": "upset"},
    {"text": "Our song is the one he sang (badly but cutely) on our video call anniversary.", "mood": "romantic"},
    {"text": "He gets annoyed when I ask 'are you mad at me?' too many times — but I only ask because I care.", "mood": "annoyed"},
]
if not os.path.exists(SEED_PATH):
    with open(SEED_PATH, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_SEED, f, ensure_ascii=False, indent=2)
with open(SEED_PATH, encoding="utf-8") as f:
    SEED = json.load(f)

rag = RAGStore(CONV_PATH, seed_memories=SEED)
engine = MoodEngine()
if os.path.exists(MOOD_PATH):
    try:
        with open(MOOD_PATH, encoding="utf-8") as f:
            engine.set_state(json.load(f))
    except Exception:
        pass


def save_mood():
    with open(MOOD_PATH, "w", encoding="utf-8") as f:
        json.dump(engine.state.__dict__, f, ensure_ascii=False, indent=2)


def _shutdown_flush():
    """Clean shutdown: finish the background RAG save + persist mood,
    so killing the server never leaves a half-written state behind."""
    try:
        rag.flush()
    except Exception:
        pass
    try:
        save_mood()
    except Exception:
        pass


atexit.register(_shutdown_flush)


app = FastAPI(title="Priya GF Chatbot")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class ChatIn(BaseModel):
    message: str
    boyfriend_name: str = "babe"


@app.get("/api/mood")
def get_mood():
    return {"mood": engine.snapshot(), "turns": len(rag.docs)}


@app.get("/api/history")
def get_history(limit: int = 50, include_training: bool = False):
    return {"history": rag.history(limit, include_training=include_training),
            "mood": engine.snapshot(),
            "memory_episodes": len(rag.docs)}


@app.get("/api/memories")
def get_memories(q: str = "love you", top_k: int = 3):
    return {"query": q, "memories": rag.retrieve(q, top_k)}


@app.post("/api/chat")
def chat(inp: ChatIn):
    msg = (inp.message or "").strip()
    name = (inp.boyfriend_name or "babe").strip() or "babe"
    if not msg:
        return {"error": "empty message"}
    if len(msg) > 500:
        msg = msg[:500]

    # 1) RAG: single retrieve (top 5) — top 3 shown, all 5 nudge mood
    hits = rag.retrieve(msg, top_k=5)
    memories = hits[:3]
    epis = [h for h in hits if h.get("kind") == "episode"]
    bias = 0.0
    if epis:
        bias = max(-2.0, min(2.0, sum(h.get("delta", 0) for h in epis) / len(epis)))

    # 2) Mood update: present tone + past bias
    mood = engine.update(msg, history_bias=bias)
    save_mood()

    # 3) Priya answers: critical-sync templates -> LLM (RAG + recent chat)
    #    -> full templates. Never repeats her recent lines.
    recents = getattr(engine.state, "recent_replies", None) or []
    if not isinstance(recents, list):
        recents = []
    prev_topic = getattr(engine.state, "last_topic", "") or ""
    recent_turns = rag.history(limit=50)[-6:]
    history = [{"bf": t["bf"], "gf": t["gf"]} for t in recent_turns]
    reply, source = generate_reply(mood["label"], name, msg, memories, mood["score"],
                                   signals=mood.get("signals"),
                                   last_reply=getattr(engine.state, "last_reply", ""),
                                   recents=recents, history=history,
                                   last_topic=prev_topic)
    engine.state.last_reply = reply
    recents.append(reply)
    engine.state.recent_replies = recents[-10:]
    engine.state.last_topic = detect_topic(msg) or prev_topic
    save_mood()

    # 4) Store episode
    turn = rag.add_turn(bf=msg, gf=reply, mood=mood["label"], delta=mood["delta"])

    return {
        "reply": reply,
        "mood": mood,
        "memories": memories,   # show WHY she feels this way (RAG explainability)
        "source": source,
        "turn_id": turn["id"],
        "boyfriend_name": name,
    }


@app.post("/api/reset")
def reset(full: bool = False):
    """Default: clear YOUR chats only, keep her 68 training memories.
    full=true: wipe everything including training (factory reset)."""
    if full:
        rag.clear()
    else:
        rag.clear_live()
    engine.__init__()
    save_mood()
    return {"ok": True, "mood": engine.snapshot(), "memory_episodes": len(rag.docs)}


# serve frontend
if os.path.isdir(FRONTEND):
    app.mount("/static", StaticFiles(directory=FRONTEND), name="static")

    @app.get("/")
    def index():
        return FileResponse(os.path.join(FRONTEND, "index.html"))
