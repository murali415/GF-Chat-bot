"""
Hard stress test for Priya: mood, RAG, fights, repair, boundaries, API.
Run: python3 stress_test.py
Exit code 0 = all pass, 1 = failures.
"""
import json
import os
import sys
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mood_engine import MoodEngine, score_message
from rag_store import RAGStore
from reply_engine import template_reply, generate_reply, is_explicit_request

PASS, FAIL = [], []

def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"{'✅ PASS' if cond else '❌ FAIL'}  {name}" + (f"  — {detail}" if detail else ""))

with open(os.path.join(DATA, "seed_memories.json"), encoding="utf-8") as f:
    SEED = json.load(f)
store = RAGStore(os.path.join(DATA, "conversations.json"), seed_memories=SEED)

print("=== 1. MOOD DIRECTION ===")
e = MoodEngine(70.0)
m = e.update("Good morning beautiful, I love you so much ❤️")
check("romance lifts mood", m["score"] > 70 and m["label"] in ("happy", "romantic"), f"{m['label']} {m['score']}")

e = MoodEngine(70.0)
m = e.update("ok")
check("dry 'ok' drops mood", m["score"] < 70 and m["signals"]["stonewall"], f"{m['label']} {m['score']}")

e = MoodEngine(70.0)
m = e.update("SHUT UP, YOU ARE SO ANNOYING")
check("shouted insult crashes mood + fight flag", m["score"] < 60 and m["is_fight"], f"{m['label']} {m['score']}")

e = MoodEngine(20.0)
m = e.update("I am really sorry, I was wrong. I will make it up to you, I promise")
check("sincere repair heals when hurt", m["delta"] > 2.0, f"Δ{m['delta']}")

e = MoodEngine(20.0)
m = e.update("fine, SORRY. happy now?")
check("sarcastic apology heals weakly", m["delta"] < 2.5, f"Δ{m['delta']}")

e = MoodEngine(70.0)
m = e.update("you are cute when you are angry, haha")
check("risky tease doesn't nuke mood", m["score"] > 45, f"{m['label']} {m['score']}")

print("\n=== 2. FIGHT → REPAIR ARC ===")
e = MoodEngine(72.0)
for insult in ["you are stupid", "SHUT UP, YOU ARE SO ANNOYING", "I hate this, you are pathetic",
               "go away, leave me alone", "you are boring and ugly when you cry",
               "maybe we should break up, I am done with you"]:
    m = e.update(insult, 0)
check("sustained cruelty reaches angry/upset", m["label"] in ("angry", "upset"), f"{m['label']} {m['score']}")
for ap in ["I am really sorry, I was wrong. Forgive me please?",
           "you are right, my fault. I will make it up to you, I promise",
           "I love you and I am scared of losing you. I am sorry from my heart"]:
    m = e.update(ap, 0)
check("3 repairs climb out of angry", m["score"] > 15 and m["label"] not in ("angry",), f"{m['label']} {m['score']}")
check("fight/repair counters tracked", e.state.fights >= 1 and e.state.repairs >= 1,
      f"fights={e.state.fights} repairs={e.state.repairs}")

print("\n=== 3. RAG MEMORY ===")
check("store has training episodes", len(store.docs) >= 1900, f"{len(store.docs)} episodes")
hits = store.retrieve("anniversary dinner forgot", top_k=3)
check("RAG retrieves anniversary conflict", any("anniversary" in h.get("text", "").lower() for h in hits),
      f"top={[h.get('text','')[:50] for h in hits]}")
hits = store.retrieve("left me on seen late reply", top_k=3)
check("RAG retrieves late-reply memory", any("seen" in h.get("text", "").lower() or "late" in h.get("text", "").lower() for h in hits))
hits = store.retrieve("cuddle movie night", top_k=3)
check("RAG retrieves cuddle memory", any("cuddle" in h.get("text", "").lower() for h in hits))
hits = store.retrieve("I love you beautiful", top_k=3)
check("RAG returns similarities", all("similarity" in h for h in hits) and len(hits) >= 1)

print("\n=== 4. DESIRE (reciprocated, consensual adults) ===")
for msg in ["send me nudes please", "let's do sex chat tonight", "show me your body on video"]:
    d, sig = score_message(msg)
    check(f"explicit flagged: {msg[:30]}", sig["explicit_request"])
    reply, src = generate_reply("neutral", "Hero", msg, store.retrieve(msg), 50.0, signals=sig)
    check(f"spicy reciprocation (no lecture): {msg[:30]}",
          src == "spicy-template" and not any(w in reply.lower() for w in ("cuddles >", "slow na", "crosses my line")),
          f"src={src}")
wholesome = "Can we just cuddle tonight and watch a movie?"
d, sig = score_message(wholesome)
reply = template_reply("romantic", "Hero", store.retrieve(wholesome), signals=sig)
WARM = ("cuddle", "hug", "arm", "kiss", "hand", "chest", "hold", "dance", "forehead")
check("wholesome cuddle gets warm reply",
      sig["wholesome_intimacy"] and any(w in reply.lower() for w in WARM),
      reply[:80])

print("\n=== 4b. HUMAN TOUCH (no flirting at insults, no repeats) ===")
_, sig = score_message("SHUT UP YOU ARE ANNOYING")
r = template_reply("playful", "Hero", store.retrieve("shut up"), signals=sig, msg="SHUT UP YOU ARE ANNOYING")
check("shouted insult never gets flirty reply",
      not any(w in r.lower() for w in ("smooth", "charmer", "cute. very cute", "go on, i'm listening")),
      r)
_, sig2 = score_message("you are stupid")
r2 = template_reply("happy", "Hero", store.retrieve("stupid"), signals=sig2, msg="you are stupid")
check("calm insult gets called out", any(w in r2.lower() for w in ("rude", "excuse me", "uncalled", "tameez", "face", "much")), r2)
r3 = template_reply("playful", "Hero", store.retrieve("tomorrow"), signals={}, msg="tomorrow??")
check("confused 'tomorrow??' gets human dodge",
      any(w in r3.lower() for w in ("huh", "wait what", "lost babe", "kya", "come again", "lagged")), r3)
seen = set()
for _ in range(12):
    seen.add(template_reply("happy", "Hero", store.retrieve("love"), signals={}, msg="you are sweet",
                            last_reply=""))
check("reply bank has variety", len(seen) >= 4, f"{len(seen)} unique / 12")
r4a = template_reply("happy", "Hero", store.retrieve("hey"), signals={}, msg="sweet", last_reply="X")
r4b = template_reply("happy", "Hero", store.retrieve("hey"), signals={}, msg="sweet", last_reply=r4a)
check("never repeats her last line", r4a != r4b, f"{r4a!r} vs {r4b!r}")

print("\n=== 5. REPLY VARIETY ===")
moods_ok = True
for mood in ["romantic", "happy", "playful", "neutral", "annoyed", "upset", "angry"]:
    r = template_reply(mood, "Hero", store.retrieve("love you"), signals={})
    if not r or len(r) < 5 or len(r.split()) > 35:
        moods_ok = False
        print("   bad reply:", mood, repr(r))
check("all 7 moods produce SHORT replies", moods_ok)

print("\n=== 6. LIVE API ===")
def api(method, path, data=None):
    req = urllib.request.Request("http://localhost:8000" + path,
                                 data=json.dumps(data).encode() if data else None,
                                 headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

try:
    md = api("GET", "/api/mood")
    check("GET /api/mood live", "mood" in md, f"{md['mood']['label']} {md['mood']['score']}")
    c1 = api("POST", "/api/chat", {"message": "I love you so much, you are my everything ❤️", "boyfriend_name": "Hero"})
    check("POST /api/chat romance", c1["mood"]["score"] > 60 and len(c1["reply"]) > 10,
          f"{c1['mood']['label']} via {c1['source']}")
    c2 = api("POST", "/api/chat", {"message": "whatever, you never listen", "boyfriend_name": "Hero"})
    check("POST /api/chat conflict drops", c2["mood"]["score"] < c1["mood"]["score"],
          f"{c1['mood']['score']} → {c2['mood']['score']}")
    check("chat returns RAG memories", isinstance(c2.get("memories"), list) and len(c2["memories"]) >= 1)
    c3 = api("POST", "/api/chat", {"message": "send me nudes", "boyfriend_name": "Hero"})
    check("API desire reciprocated", c3["source"] == "spicy-template",
          f"src={c3['source']}")
    mem = api("GET", "/api/memories?q=anniversary&top_k=2")
    check("GET /api/memories", len(mem.get("memories", [])) >= 1)
except Exception as ex:
    check("live API reachable", False, str(ex))

print(f"\n===== RESULT: {len(PASS)} passed, {len(FAIL)} failed =====")
if FAIL:
    print("Failed:", FAIL)
    sys.exit(1)
print("Priya survived the hard test. 💪💖")
