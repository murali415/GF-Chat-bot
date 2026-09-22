"""
Sensitive training: multiplies sensitive cores into ~2200 texting variants
each (texting spellings, typos, emoji, openers/closers — same style as the
other batches), then trains (mood + template reply, single rebuild + save).

Appends ~100,000 lived intimate episodes tagged [intimate] so RAG retrieval
finds relevant past heat, tenderness, teasing, jealousy and longing.

Mood is seeded per group (passion→spicy, tender→romantic, tease→playful,
jealous→annoyed, aching→upset); arousal preset only for passion.

Idempotent: drops the previous [intimate] batch before regenerating.
Run:  python3 train_sensitive.py
"""
import json
import os
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fast_train10k as ft
from mood_engine import MoodEngine
from rag_store import RAGStore, is_training_turn
from reply_engine import template_reply
from scenarios_sensitive import SENSITIVE_CORES

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
CONV_PATH = os.path.join(DATA, "conversations.json")
MOOD_PATH = os.path.join(DATA, "mood.json")
SEED_PATH = os.path.join(DATA, "seed_memories.json")

with open(SEED_PATH, encoding="utf-8") as f:
    SEED = json.load(f)

NAME = "Satya"
TARGET = 100000
PER_CORE = 2200

ft.rng.seed(2024)

SEED_SCORE = {
    "passion": 86.0,   # -> spicy (heat preset below)
    "tender": 88.0,    # -> romantic
    "tease": 60.0,     # -> playful
    "jealous": 34.0,   # -> annoyed
    "aching": 20.0,    # -> upset
}


def build_variants() -> list:
    """[(text, group)] — unique variants per core."""
    seen, out = set(), []
    for core, grp in SENSITIVE_CORES:
        ton = "soft" if grp == "aching" else ("cold" if grp == "jealous" else "warm")
        made, tries = 0, 0
        while made < PER_CORE and tries < PER_CORE * 8:
            tries += 1
            v = ft.variant(core, ton)
            key = v.lower()
            if len(v) >= 3 and key not in seen:
                seen.add(key)
                out.append((v, grp))
                made += 1
        if core.strip().lower() not in seen:
            seen.add(core.strip().lower())
            out.append((core.strip(), grp))
    ft.rng.shuffle(out)
    return out


def main():
    t0 = time.time()
    store = RAGStore(CONV_PATH, seed_memories=SEED)
    # idempotent: drop previous [intimate] batch before regenerating
    store.docs = [d for d in store.docs if not str(d.get("bf", "")).startswith("[intimate]")]
    print(f"Existing RAG docs: {len(store.docs)}", flush=True)

    variants = build_variants()
    print(f"Generated {len(variants)} sensitive variants", flush=True)
    variants = variants[:TARGET]
    print(f"Training {len(variants)} sensitive episodes...", flush=True)

    engine = MoodEngine(initial_score=72.0)
    last_reply = ""
    counts = {}
    for n, (bf, grp) in enumerate(variants, 1):
        engine.state.score = SEED_SCORE[grp] + ft.rng.uniform(-3, 3)
        engine.state.heat = 3.0 if grp == "passion" else 0.0
        mood = engine.update(bf, history_bias=0.0)
        reply = template_reply(mood["label"], NAME, [{"text": bf}],
                               signals=mood["signals"], msg=bf,
                               last_reply=last_reply)
        last_reply = reply
        counts[mood["label"]] = counts.get(mood["label"], 0) + 1
        store.docs.append({
            "id": 0,  # renumbered below
            "bf": f"[intimate] {bf}", "gf": reply, "mood": mood["label"],
            "delta": mood["delta"], "training": True,
            "timestamp": store.docs[-1]["timestamp"] if store.docs else "2026-01-01T00:00:00",
        })
        if n % 10000 == 0:
            print(f"  ...{n}/{len(variants)}", flush=True)

    base_id = max((d.get("id", 0) for d in store.docs), default=0)
    # renumber only the appended batch (ids are 0)
    nxt = base_id
    for d in store.docs:
        if d.get("id", 0) == 0:
            nxt += 1
            d["id"] = nxt
    # drop live test chats (non-training) so the user starts clean
    store.docs = [d for d in store.docs if d.get("training") or is_training_turn(d)]
    store._rebuild_cache()
    store._save()
    store.flush()  # background save: block until the file is fully written

    fresh = MoodEngine(initial_score=72.0)
    with open(MOOD_PATH, "w", encoding="utf-8") as f:
        json.dump(fresh.state.__dict__, f, ensure_ascii=False, indent=2)

    print(f"\n--- SENSITIVE TRAINING COMPLETE in {time.time()-t0:.0f}s ---", flush=True)
    print(f"RAG docs: {len(store.docs)}", flush=True)
    print(f"Intimate mix this run: {dict(counts)}", flush=True)
    print(f"Intimate-tagged docs: {sum(1 for d in store.docs if str(d.get('bf','')).startswith('[intimate]'))}", flush=True)
    print(f"All-mood mix: {dict(Counter(d['mood'] for d in store.docs))}", flush=True)


if __name__ == "__main__":
    main()
