"""
Bulk relationship training: ~68 core + ~490 real-life situations ≈ 558 episodes.
Interleaves categories round-robin so mood moves in realistic arcs
(romance -> small conflict -> repair -> daily life -> fight -> makeup ...)
instead of flat blocks.

Run:  python3 bulk_train.py
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mood_engine import MoodEngine
from rag_store import RAGStore
from reply_engine import template_reply
from train_relationship import SCENARIOS as CORE
from scenarios_bulk import BULK
from scenarios_bulk2 import BULK2
from scenarios_bulk3 import BULK3

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
CONV_PATH = os.path.join(DATA, "conversations.json")
MOOD_PATH = os.path.join(DATA, "mood.json")
SEED_PATH = os.path.join(DATA, "seed_memories.json")

with open(SEED_PATH, encoding="utf-8") as f:
    SEED = json.load(f)

NAME = "Satya"
random.seed(7)


def interleave(groups):
    """Round-robin across archetype groups with a little shuffle."""
    # groups = [(tag, [msgs]), ...]
    pools = [(tag, list(msgs)) for tag, msgs in groups]
    for _, msgs in pools:
        random.shuffle(msgs)
    out, i = [], 0
    while any(msgs for _, msgs in pools):
        tag, msgs = pools[i % len(pools)]
        if msgs:
            out.append((msgs.pop(), tag))
        i += 1
    return out


def main():
    store = RAGStore(CONV_PATH, seed_memories=SEED)
    store.clear()
    engine = MoodEngine()

    # core 68 first (foundation), then ~2200 interleaved real-life situations
    run = list(CORE) + interleave(BULK + BULK2 + BULK3)
    print(f"Training {len(run)} episodes...")

    counts, last_reply = {}, ""
    for n, (bf_msg, tag) in enumerate(run, 1):
        raw = bf_msg if not bf_msg.startswith("[") else bf_msg
        clean = raw
        memories = store.retrieve(clean, top_k=3)
        bias = store.history_bias(clean)
        mood = engine.update(clean, history_bias=bias)
        reply = template_reply(mood["label"], NAME, memories,
                               signals=mood["signals"], msg=clean,
                               last_reply=last_reply)
        last_reply = reply
        store.add_turn(bf=f"[{tag}] {raw}", gf=reply, mood=mood["label"],
                       delta=mood["delta"], training=True)
        counts[mood["label"]] = counts.get(mood["label"], 0) + 1
        if n % 100 == 0:
            print(f"  ...{n}/{len(run)}  mood now {mood['label']} ({mood['score']})")

    fresh = MoodEngine(initial_score=72.0)
    with open(MOOD_PATH, "w", encoding="utf-8") as f:
        json.dump(fresh.state.__dict__, f, ensure_ascii=False, indent=2)

    print("\n--- BULK TRAINING COMPLETE ---")
    print(f"Episodes in RAG store : {len(store.docs)}")
    print(f"Mood coverage         : {counts}")
    print("Live mood reset to 72 (happy) — memories kept.")


if __name__ == "__main__":
    main()
