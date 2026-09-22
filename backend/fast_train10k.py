"""
10k expansion: multiplies fresh cores into ~50 phrasing variants each
(texting spellings, typos, emoji, openers/closers, punctuation),
then FAST-trains (no retrieval during training — mood + template only,
single save at end). Appends to existing RAG, trims to 10000 docs.

Run:  python3 fast_train10k.py
"""
import json
import os
import random
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mood_engine import MoodEngine
from rag_store import RAGStore, is_training_turn
from reply_engine import template_reply
from cores10k import CORES, FIGHT_CORES, SOFT_CORES, CHILL_CORES, FLIRTY_CORES, NAG_CORES

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
CONV_PATH = os.path.join(DATA, "conversations.json")
MOOD_PATH = os.path.join(DATA, "mood.json")
SEED_PATH = os.path.join(DATA, "seed_memories.json")

with open(SEED_PATH, encoding="utf-8") as f:
    SEED = json.load(f)

NAME = "Satya"
TARGET_NEW = 12000
PER_CORE = 75
rng = random.Random(42)

TEXTING = [(" you ", " u "), (" are ", " r "), (" your ", " ur "),
           ("please", "pls"), ("because", "cos"), ("love", "luv"),
           ("tonight", "tonite"), ("people", "ppl"), ("before", "b4"),
           ("great", "gr8"), ("night", "nite"), ("to you", "to u"),
           ("for you", "for u"), ("with you", "w u"), ("me too", "me 2")]
OPENERS = ["", "", "", "hey ", "babe ", "yaar ", "hey babe ", "baby ",
           "sun na ", "hey ", "arey ", "hello ", "yo "]
COLD_OPENERS = ["", "", "", "hey ", "listen ", "seriously ", "wow ", "so "]
CLOSERS = ["", "", "", " na", " please", " lol", " haha", "...", "!!",
           "?", " no?", " right?", " btw", " tho", " 🥺", " ❤️"]
COLD_CLOSERS = ["", "", ".", "?", "??", "!", " 🙄", " 😒", " lol", " wow"]
EMOJIS = ["❤️", "🥺", "😌", "😭", "🥰", "😏", "💕", "🌙", "✨", "😅", "💖", "🌧️"]
COLD_EMOJIS = ["🙄", "😒", "😑"]
SOFT_EMOJIS = ["🥺", "😔", "💔", "🌙", "🤗"]
SOFT_CLOSERS = ["", "", " 🥺", " please?", "...", " na", " 💔"]

COLD_KEYS = ("shut", "stupid", "idiot", "dumb", "hate", "ugly", "pathetic",
             "loser", "break", "leave", "done with", "go away", "hell",
             "jealous", "who were", "who was", "why is he", "why are",
             "lying", "lied", "lie", "liar", "ignoring", "late reply",
             "seen", "cheat", "threat", "divorce", "never listen",
             "always ", "chill out", "drama", "overreact", "shut up",
             "fight", "argue", "blame", "fault", "dump", "block you",
             "unfollow", "breakup", "break up", "end this", "forget me",
             "don't love", "dont love", "no time", "too busy", "busy with",
             "forgot", "dry", "sarcasm", "yawn", "asleep", "snor", "muted",
             "cancelled", "online", "boys", "callback", "on read",
             "caps", "attitude", "agreeing", "whatever", "haha", "ex ",
             "defend", "double standard", "texting first", "paragraphs",
             "one-word", "sus", "read at")


SOFT_KEYS = ("crying", "cry ", "tears", "sad", "lonely", "empty inside",
             "scared", "anxiety", "headache", "sick", "hospital", "failed",
             "failure", "rejected", "useless", "panic", "fear", "nervous",
             "depressed", "invisible", "overthinking", "disappear", "losses",
             "storm inside", "comfort", "hold me", "hug me", "stay with",
             "don't let go", "dont let go", "praying", "worried", "migraine",
             "broke down", "down bad", "not okay", "lowest")


def tone(core: str) -> str:
    t = core.lower()
    if any(k in t for k in COLD_KEYS):
        return "cold"
    if any(k in t for k in SOFT_KEYS):
        return "soft"
    return "warm"


def add_typos(text: str) -> str:
    words = text.split()
    out = []
    for w in words:
        core = re.sub(r"[^a-zA-Z]", "", w)
        if len(core) >= 6 and rng.random() < 0.22:
            i = rng.randrange(len(core) - 1)
            chars = list(core)
            if rng.random() < 0.5:
                del chars[i]  # dropped letter: thinking -> thiking
            else:
                chars[i], chars[i + 1] = chars[i + 1], chars[i]  # swap
            w = w.replace(core, "".join(chars), 1)
        out.append(w)
    return " ".join(out)


def stretch(text: str) -> str:
    if rng.random() < 0.18:
        text = re.sub(r"(hey+|so+|please+|no+)\b",
                      lambda m: m.group(1) + m.group(1)[-1] * rng.randint(1, 2),
                      text, count=1)
    return text


def variant(core: str, ton: str) -> str:
    cold = ton == "cold"
    soft = ton == "soft"
    t = " " + core.strip() + " "
    for a, b in TEXTING:
        if a in t and rng.random() < (0.2 if (cold or soft) else 0.35):
            t = t.replace(a, b, 1)
    t = t.strip()
    t = add_typos(t)
    t = stretch(t)
    if cold:
        t = rng.choice(COLD_OPENERS) + t
        emo = rng.choice(COLD_EMOJIS) if rng.random() < 0.25 else ""
        clo = rng.choice(COLD_CLOSERS)
    elif soft:
        t = rng.choice(OPENERS) + t
        emo = rng.choice(SOFT_EMOJIS) if rng.random() < 0.5 else ""
        clo = rng.choice(SOFT_CLOSERS)
    else:
        t = rng.choice(OPENERS) + t
        emo = "".join(rng.sample(EMOJIS, k=rng.choice([0, 0, 1, 1, 2]))) if rng.random() < 0.55 else ""
        clo = rng.choice(CLOSERS)
    punct = rng.choice(["", "", ".", "!", "!!", "?", "??", "..."])
    t = (t + (" " + emo if emo else "") + clo).strip()
    if not re.search(r"[.!?…❤️🥺😌😭🥰😏💕🌙✨😅💖🌧️🙄😒😑]$", t):
        t += punct
    return re.sub(r"\s+", " ", t).strip()[:160]


def build_variants(triples) -> list:
    """triples = [(core, tone, per_core, group)]. Returns [(text, group)]."""
    seen, out = set(), []
    for core, ton, per_core, group in triples:
        made, tries = 0, 0
        while made < per_core and tries < per_core * 8:
            tries += 1
            v = variant(core, ton)
            key = v.lower()
            if len(v) >= 3 and key not in seen:
                seen.add(key)
                out.append((v, group))
                made += 1
        clean = core.strip()
        if clean.lower() not in seen:
            seen.add(clean.lower())
            out.append((clean, group))
    rng.shuffle(out)
    return out


TARGET_TOTAL = 101500
MOOD_TARGET = 15600  # equal share per mood
# top-up families if a bucket runs short (keeps labels truthful)
FILL_FAMILY = {
    "angry": ["angry", "upset"], "upset": ["upset", "annoyed", "angry"],
    "annoyed": ["annoyed", "upset"], "happy": ["happy", "playful"],
    "playful": ["playful", "happy"], "romantic": ["romantic", "happy"],
    "neutral": ["neutral", "playful"],
}
FILL_ORDER = ["playful", "happy", "annoyed", "neutral", "romantic", "upset", "angry"]


def main():
    t0 = time.time()
    store = RAGStore(CONV_PATH, seed_memories=SEED)
    # idempotent: drop previous [10k] batch before regenerating
    store.docs = [d for d in store.docs if not str(d.get("bf", "")).startswith("[10k]")]
    store._rebuild_cache()
    print(f"Existing RAG docs: {len(store.docs)}")
    # (core, tone, variants each, seed group)
    triples = (
        [(c, "cold", 430, "rage") for c in FIGHT_CORES]
        + [(c, "soft", 480, "soft") for c in SOFT_CORES]
        + [(c, "chill", 520, "chill") for c in CHILL_CORES]
        + [(c, "warm", 320, "warm") for c in FLIRTY_CORES]
        + [(c, "cold", 200, "cold") for c in NAG_CORES]
        + [(c, tone(c), 320 if tone(c) == "warm" else 200, tone(c)) for c in CORES]
    )
    variants = build_variants(triples)
    print(f"Generated {len(variants)} new situations")

    engine = MoodEngine(initial_score=72.0)
    buckets, last_reply = {}, ""
    warm_cycle, wi = [88.0, 74.0, 60.0], 0
    for n, (bf, grp) in enumerate(variants, 1):
        # seed mood so labels land truthfully (with jitter)
        if grp == "rage":
            engine.state.score = 10.0 + rng.uniform(-3, 3)    # -> angry
        elif grp == "cold":
            engine.state.score = 34.0 + rng.uniform(-4, 4)    # -> annoyed
        elif grp == "soft":
            engine.state.score = 20.0 + rng.uniform(-3, 3)    # -> upset
        elif grp == "chill":
            engine.state.score = 47.0 + rng.uniform(-4, 4)    # -> neutral
        else:
            engine.state.score = warm_cycle[wi % 3] + rng.uniform(-3, 3)  # romantic/happy/playful
            wi += 1
        mood = engine.update(bf, history_bias=0.0)  # no retrieval: fast path
        reply = template_reply(mood["label"], NAME, [{"text": bf}],
                               signals=mood["signals"], msg=bf,
                               last_reply=last_reply)
        last_reply = reply
        turn = {
            "id": 0,  # renumbered below
            "bf": f"[10k] {bf}", "gf": reply, "mood": mood["label"],
            "delta": mood["delta"], "training": True,
            "timestamp": store.docs[-1]["timestamp"] if store.docs else "2026-01-01T00:00:00",
        }
        buckets.setdefault(mood["label"], []).append(turn)
        if n % 2000 == 0:
            print(f"  ...{n}/{len(variants)}")

    # equal top-up: each mood totals MOOD_TARGET (14500) incl. existing docs
    from collections import Counter
    old_mix = Counter(d.get("mood", "neutral") for d in store.docs)
    picked = []
    for mood in ("romantic", "happy", "playful", "neutral", "annoyed", "upset", "angry"):
        need = max(0, MOOD_TARGET - old_mix.get(mood, 0))
        pool = buckets.get(mood, [])
        rng.shuffle(pool)
        picked.extend(pool[:need])
    # family fill if a bucket ran short (truthful labels only)
    used = {(t["bf"], t["gf"]) for t in picked}
    cur = Counter(t["mood"] for t in picked)
    for mood in FILL_ORDER:
        while old_mix.get(mood, 0) + cur.get(mood, 0) < MOOD_TARGET:
            added = False
            for fam in FILL_FAMILY[mood]:
                for t in buckets.get(fam, []):
                    if (t["bf"], t["gf"]) not in used:
                        used.add((t["bf"], t["gf"]))
                        picked.append(t)
                        cur[t["mood"]] = cur.get(t["mood"], 0) + 1
                        added = True
                        break
                if added:
                    break
            if not added:
                break
        if len(store.docs) + len(picked) >= TARGET_TOTAL:
            break
    # fill up to TARGET_TOTAL in priority order
    used = {(t["bf"], t["gf"]) for t in picked}
    if len(store.docs) + len(picked) < TARGET_TOTAL:
        for mood in FILL_ORDER:
            for t in buckets.get(mood, []):
                if len(store.docs) + len(picked) >= TARGET_TOTAL:
                    break
                if (t["bf"], t["gf"]) not in used:
                    used.add((t["bf"], t["gf"]))
                    picked.append(t)
            if len(store.docs) + len(picked) >= TARGET_TOTAL:
                break
    rng.shuffle(picked)
    base_id = max((d.get("id", 0) for d in store.docs), default=0)
    for i, t in enumerate(picked, 1):
        t["id"] = base_id + i
    store.docs = store.docs + picked
    # drop live test chats (non-training) so the user starts clean
    store.docs = [d for d in store.docs if d.get("training") or is_training_turn(d)]
    store._rebuild_cache()
    store._save()

    fresh = MoodEngine(initial_score=72.0)
    with open(MOOD_PATH, "w", encoding="utf-8") as f:
        json.dump(fresh.state.__dict__, f, ensure_ascii=False, indent=2)

    from collections import Counter
    print(f"\n--- TRAINING COMPLETE in {time.time()-t0:.0f}s ---")
    print(f"RAG docs: {len(store.docs)}")
    print(f"All-mood mix: {dict(Counter(d['mood'] for d in store.docs))}")


if __name__ == "__main__":
    main()
