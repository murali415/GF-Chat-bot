"""
Story-time training: multiplies story cores into ~320 texting variants each
(texting spellings, typos, emoji, openers/closers — same style as the 10k batch),
then trains (mood + template reply, single rebuild + save at end).

Appends ~14,000 lived story episodes tagged [story] so RAG retrieval finds
relevant past episodes when he narrates his day (story-time mood:
happy/playful/romantic/neutral for warm tales, upset for soft ones).

Idempotent: drops the previous [story] batch before regenerating.
Run:  python3 train_story.py
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
from scenarios_story import STORY_CORES

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
CONV_PATH = os.path.join(DATA, "conversations.json")
MOOD_PATH = os.path.join(DATA, "mood.json")
SEED_PATH = os.path.join(DATA, "seed_memories.json")

with open(SEED_PATH, encoding="utf-8") as f:
    SEED = json.load(f)

NAME = "Satya"
TARGET = 14000
PER_CORE = 320

ft.rng.seed(1234)


def build_variants() -> list:
    """[(text, group)] — unique variants per core, hook-first cores survive 160-char cap."""
    seen, out = set(), []
    for core, grp in STORY_CORES:
        ton = "soft" if grp == "soft" else "warm"
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
    # idempotent: drop previous [story] batch before regenerating
    store.docs = [d for d in store.docs if not str(d.get("bf", "")).startswith("[story]")]
    print(f"Existing RAG docs: {len(store.docs)}")

    variants = build_variants()
    print(f"Generated {len(variants)} story variants")
    variants = variants[:TARGET]
    print(f"Training {len(variants)} story episodes...")

    engine = MoodEngine(initial_score=72.0)
    warm_cycle, wi = [88.0, 74.0, 60.0], 0
    last_reply = ""
    counts = {}
    for n, (bf, grp) in enumerate(variants, 1):
        if grp == "soft":
            engine.state.score = 20.0 + ft.rng.uniform(-3, 3)   # -> upset
        else:
            engine.state.score = warm_cycle[wi % 3] + ft.rng.uniform(-3, 3)
            wi += 1
        mood = engine.update(bf, history_bias=0.0)
        reply = template_reply(mood["label"], NAME, [{"text": bf}],
                               signals=mood["signals"], msg=bf,
                               last_reply=last_reply)
        last_reply = reply
        counts[mood["label"]] = counts.get(mood["label"], 0) + 1
        store.docs.append({
            "id": 0,  # renumbered below
            "bf": f"[story] {bf}", "gf": reply, "mood": mood["label"],
            "delta": mood["delta"], "training": True,
            "timestamp": store.docs[-1]["timestamp"] if store.docs else "2026-01-01T00:00:00",
        })
        if n % 2000 == 0:
            print(f"  ...{n}/{len(variants)}")

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

    print(f"\n--- STORY TRAINING COMPLETE in {time.time()-t0:.0f}s ---")
    print(f"RAG docs: {len(store.docs)}")
    print(f"Story mix this run: {dict(counts)}")
    print(f"Story-tagged docs: {sum(1 for d in store.docs if str(d.get('bf','')).startswith('[story]'))}")
    print(f"All-mood mix: {dict(Counter(d['mood'] for d in store.docs))}")


if __name__ == "__main__":
    main()
