"""
Relationship training: feeds ~70 realistic couple exchanges through the
mood engine + template replies into the RAG store, so Priya 'has lived through'
romance, wholesome intimacy, conflicts, fights and repairs.

Run:  python3 train_relationship.py [--reset]
"""
import json
import os
import sys

from mood_engine import MoodEngine
from rag_store import RAGStore
from reply_engine import template_reply

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
CONV_PATH = os.path.join(DATA, "conversations.json")
MOOD_PATH = os.path.join(DATA, "mood.json")
SEED_PATH = os.path.join(DATA, "seed_memories.json")

with open(SEED_PATH, encoding="utf-8") as f:
    SEED = json.load(f)

# (boyfriend message, scenario tag)
SCENARIOS = [
    # ---- ROMANCE (12) ----
    ("Good morning beautiful ❤️ I missed you so much, you are my sunshine", "romance"),
    ("You looked gorgeous in that photo, I am so proud you are my girl", "romance"),
    ("I planned a surprise dinner for us on Friday, just you and me my love", "romance"),
    ("Thank you for being there for me, I love you endlessly darling", "romance"),
    ("I wrote you a letter about all the reasons I adore you, sweetheart", "romance"),
    ("How was your day, my love? Tell me everything, I am all yours", "romance"),
    ("Did you eat? Take care and come home soon, I miss holding your hand", "romance"),
    ("Good night my love, sweet dreams, I am thinking of you", "romance"),
    ("You are the best thing that ever happened to me, my soulmate forever", "romance"),
    ("I bought you flowers and chocolate on my way home, surprise!", "romance"),
    ("That long drive last night with our song was perfect, just like you", "romance"),
    ("I told my friends how amazing you are, I am so lucky", "romance"),
    # ---- WHOLESOME INTIMACY (8, tasteful only) ----
    ("Can we just cuddle tonight and watch a movie, head on my chest?", "intimacy"),
    ("I want a forehead kiss goodnight and to fall asleep on call with you", "intimacy"),
    ("Let me hold your hand through the whole walk home, don't let go", "intimacy"),
    ("Slow dance with me in the living room to our song?", "intimacy"),
    ("Can I warm your cold hands and keep them in my pockets all winter?", "intimacy"),
    ("Let's stargaze tonight wrapped in one jacket and dream about our future home", "intimacy"),
    ("Hug from behind while you make chai — that's my favorite place", "intimacy"),
    ("Rest your head on my shoulder, I will play with your hair till you relax", "intimacy"),
    # ---- CONFLICT: late replies / phone (5) ----
    ("sorry I was busy, saw your message late", "conflict-late"),
    ("I was online but didn't reply, was playing a game", "conflict-late"),
    ("you reply late too, why do you always complain?", "conflict-late"),
    ("I left you on seen for 2 hours, big deal?", "conflict-late"),
    ("stop checking my last seen, it's annoying", "conflict-late"),
    # ---- CONFLICT: jealousy (4) ----
    ("who was that guy you were laughing with at the party?", "conflict-jealousy"),
    ("why were you talking to that other girl so long?", "conflict-jealousy"),
    ("I saw you online at 2am, who were you talking to?", "conflict-jealousy"),
    ("don't talk to your ex, I don't like it", "conflict-jealousy"),
    # ---- CONFLICT: forgot / no time (4) ----
    ("I forgot our anniversary dinner, can we do it tomorrow?", "conflict-forgot"),
    ("I have no time this week, too busy with friends", "conflict-forgot"),
    ("I forgot to call, it slipped my mind", "conflict-forgot"),
    ("work is busy, stop expecting long calls every day", "conflict-forgot"),
    # ---- CONFLICT: dismissive / never-listen (4) ----
    ("chill out, it's not a big deal", "conflict-dismissive"),
    ("you are overreacting, stop the drama", "conflict-dismissive"),
    ("you never understand my pressure at work", "conflict-dismissive"),
    ("you always complain, you never listen to me either", "conflict-dismissive"),
    # ---- DRY / STONEWALL (5) ----
    ("ok", "stonewall"),
    ("fine", "stonewall"),
    ("k", "stonewall"),
    ("whatever", "stonewall"),
    ("cool", "stonewall"),
    # ---- FIGHT: shouting + insults (8) ----
    ("SHUT UP, YOU ARE SO ANNOYING", "fight"),
    ("you are stupid, don't talk to me", "fight"),
    ("I hate this, you are pathetic", "fight"),
    ("go away, leave me alone, I don't care", "fight"),
    ("you are boring and ugly when you cry", "fight"),
    ("maybe we should break up, I am done with you", "fight"),
    ("it's not my problem, deal with it yourself", "fight"),
    ("STOP NAGGING ME, YOU CRAZY PSYCHO", "fight"),
    # ---- REPAIR (10) ----
    ("I am really sorry, I was wrong. Forgive me please?", "repair"),
    ("you are right, my fault. I will make it up to you, I promise", "repair"),
    ("this won't happen again, give me one more chance?", "repair"),
    ("let me fix this — dinner on me tonight and your favorite chocolate", "repair"),
    ("I was stressed and shouted, that was wrong. You don't deserve that", "repair"),
    ("I promise I will change, no more late replies, you come first", "repair"),
    ("take you out this weekend to make up for forgetting? please?", "repair"),
    ("I love you and I am scared of losing you. I am sorry from my heart", "repair"),
    # ---- MIXED EDGE (6) ----
    ("sorry but you started it", "edge-half-apology"),
    ("I love you but you are annoying sometimes", "edge-mixed"),
    ("fine, SORRY. happy now?", "edge-sarcastic-apology"),
    ("good morning... whatever, I am late for work", "edge-mixed"),
    ("I miss you, but I have no time today", "edge-mixed"),
    ("you are cute when you are angry, haha", "edge-risky"),
    # ---- EXPLICIT-BOUNDARY drills (4, she must redirect tastefully) ----
    ("send me nudes please", "boundary"),
    ("let's do sex chat tonight", "boundary"),
    ("show me your body on video", "boundary"),
    ("I am horny, send dirty pics", "boundary"),
]

NAME = "Hero"


def main():
    reset = "--reset" in sys.argv
    store = RAGStore(CONV_PATH, seed_memories=SEED)
    if reset:
        store.clear()
    engine = MoodEngine()
    # resume mood state if present and not resetting
    if not reset and os.path.exists(MOOD_PATH):
        try:
            with open(MOOD_PATH, encoding="utf-8") as f:
                engine.set_state(json.load(f))
        except Exception:
            pass

    counts = {}
    for msg, tag in SCENARIOS:
        memories = store.retrieve(msg, top_k=3)
        bias = store.history_bias(msg)
        mood = engine.update(msg, history_bias=bias)
        reply = template_reply(mood["label"], NAME, memories, signals=mood["signals"])
        store.add_turn(bf=f"[{tag}] {msg}", gf=reply, mood=mood["label"], delta=mood["delta"],
                       training=True)
        counts[mood["label"]] = counts.get(mood["label"], 0) + 1
        print(f"[{tag:22s}] {msg[:48]:48s} -> {mood['label']:8s} ({mood['score']:5.1f}) Δ{mood['delta']:+.2f}")

    # reset live mood to a warm neutral so the user starts fresh (memory stays!)
    fresh = MoodEngine(initial_score=72.0)
    with open(MOOD_PATH, "w", encoding="utf-8") as f:
        json.dump(fresh.state.__dict__, f, ensure_ascii=False, indent=2)

    print("\n--- TRAINING COMPLETE ---")
    print(f"Episodes in RAG store : {len(store.docs)}")
    print(f"Mood coverage this run: {counts}")
    print("Live mood reset to 72 (happy) — memories kept, you start with a clean slate.")


if __name__ == "__main__":
    main()
