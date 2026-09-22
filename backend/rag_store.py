"""
RAG store: pure-Python TF-IDF retrieval over past conversations + seed memories.
No external deps. Persists to JSON.
"""
import atexit
import json
import math
import os
import re
import threading
from datetime import datetime
from typing import List, Dict

TOKEN_RE = re.compile(r"[a-z']+")
TRAINING_TAG_RE = re.compile(r"^\[[a-z][a-z\-]*\] ")


def tokenize(text: str) -> List[str]:
    return TOKEN_RE.findall(text.lower())


def is_training_turn(doc: Dict) -> bool:
    """Training episodes (RAG memory) vs real user chats."""
    if doc.get("training"):
        return True
    return bool(TRAINING_TAG_RE.match(doc.get("bf", "")))


class RAGStore:
    def __init__(self, path: str, seed_memories: List[Dict] = None):
        self.path = path
        self.docs: List[Dict] = []  # {id, text, bf, gf, mood, delta, timestamp}
        self.seed = seed_memories or []
        self._tokcache: Dict[str, List[str]] = {}  # key -> tokens (speed at 10k scale)
        self._save_lock = threading.Lock()
        self._save_threads = []
        # Background saves die with the process — flush on exit so training
        # scripts never lose their final write (cost: ~1s at exit).
        try:
            atexit.register(self.flush)
        except Exception:
            pass
        self._load()

    # ---------- persistence ----------
    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.docs = data.get("docs", [])
            except Exception:
                self.docs = []
        self._rebuild_cache()

    def _rebuild_cache(self):
        self._tokcache = {}
        for d in self.docs:
            epi = (f"Boyfriend said: {d['bf']} Girlfriend ({d['mood']}) replied: {d['gf']}")
            self._tokcache[f"e{d.get('id', 0)}"] = tokenize(epi)
        for i, m in enumerate(self.seed):
            self._tokcache[f"s{i}"] = tokenize(m["text"])
        self._build_index()

    def _build_index(self):
        """Inverted index + cached TF counters + doc frequencies (fast at 100k)."""
        self._tf = []
        self._df = {}
        self._inv = {}
        texts = [m["text"] for m in self.seed] + [
            f"Boyfriend said: {d['bf']} Girlfriend ({d['mood']}) replied: {d['gf']}"
            for d in self.docs
        ]
        for i, text in enumerate(texts):
            toks = tokenize(text)
            tf = {}
            for t in toks:
                tf[t] = tf.get(t, 0) + 1
            n = len(toks) or 1
            tf = {t: c / n for t, c in tf.items()}
            self._tf.append(tf)
            for t in tf:
                self._df[t] = self._df.get(t, 0) + 1
                self._inv.setdefault(t, []).append(i)
        self._N = len(texts) or 1

    def _index_one_episode(self, d):
        text = f"Boyfriend said: {d['bf']} Girlfriend ({d['mood']}) replied: {d['gf']}"
        toks = tokenize(text)
        tf = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        n = len(toks) or 1
        tf = {t: c / n for t, c in tf.items()}
        i = len(self._tf)
        self._tf.append(tf)
        for t in tf:
            self._df[t] = self._df.get(t, 0) + 1
            self._inv.setdefault(t, []).append(i)
        self._N += 1
        self._tokcache[f"e{d.get('id', 0)}"] = toks

    def _meta(self, i):
        ns = len(self.seed)
        if i < ns:
            m = self.seed[i]
            return {"id": f"seed-{i}", "text": m["text"], "kind": "long-term",
                    "timestamp": m.get("timestamp", "long ago"),
                    "mood": m.get("mood", "happy")}
        d = self.docs[i - ns]
        return {"id": f"chat-{d['id']}",
                "text": f"Boyfriend said: {d['bf']} Girlfriend ({d['mood']}) replied: {d['gf']}",
                "kind": "episode", "timestamp": d["timestamp"], "mood": d["mood"],
                "delta": d.get("delta", 0)}

    def _save(self):
        # Non-blocking save: the response returns instantly while the disk
        # write happens in a background thread. The lock is held for the
        # ENTIRE snapshot + write + replace, so overlapping saves can never
        # interleave bytes into the same tmp file (that corrupts the store).
        # Each thread snapshots under the lock, so the last writer always
        # persists the newest state. Cap 500k docs (~110MB) — headroom above
        # the ~230k trained base so growth never silently drops old memory.
        try:
            path = self.path
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            if not hasattr(self, "_save_lock"):
                self._save_lock = threading.Lock()
                self._save_threads = []

            def _write():
                try:
                    with self._save_lock:
                        snapshot = {"docs": self.docs[-500000:]}
                        tmp = path + ".tmp"
                        with open(tmp, "w", encoding="utf-8") as f:
                            json.dump(snapshot, f, ensure_ascii=False,
                                      separators=(",", ":"))
                        os.replace(tmp, path)
                except Exception:
                    pass

            with self._save_lock:
                # prune finished workers so the list can't grow forever
                self._save_threads = [t for t in self._save_threads if t.is_alive()]
                t = threading.Thread(target=_write, daemon=True)
                self._save_threads.append(t)
            t.start()
        except Exception:
            pass

    def flush(self):
        """Block until ALL background saves finish (shutdown / reset / training)."""
        for t in list(getattr(self, "_save_threads", [])):
            try:
                t.join(timeout=30)
            except Exception:
                pass

    # ---------- indexing ----------
    def _corpus(self) -> List[Dict]:
        # seed memories act as long-term memory docs
        seed_docs = [
            {"id": f"seed-{i}", "_k": f"s{i}", "text": m["text"], "kind": "long-term",
             "timestamp": m.get("timestamp", "long ago"), "mood": m.get("mood", "happy")}
            for i, m in enumerate(self.seed)
        ]
        epi = [
            {"id": f"chat-{d['id']}", "_k": f"e{d['id']}",
             "text": f"Boyfriend said: {d['bf']} Girlfriend ({d['mood']}) replied: {d['gf']}",
             "kind": "episode", "timestamp": d["timestamp"], "mood": d["mood"], "delta": d.get("delta", 0)}
            for d in self.docs
        ]
        return seed_docs + epi

    def _idf(self, corpus_tokens: List[List[str]]) -> Dict[str, float]:
        df = {}
        n = len(corpus_tokens)
        for toks in corpus_tokens:
            for tok in set(toks):
                df[tok] = df.get(tok, 0) + 1
        return {t: math.log((n + 1) / (c + 1)) + 1.0 for t, c in df.items()}

    @staticmethod
    def _tf_vec(toks: List[str]) -> Dict[str, float]:
        tf = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        n = len(toks) or 1
        return {t: c / n for t, c in tf.items()}

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        q_toks = tokenize(query)
        if not q_toks or not self._tf:
            return [self._meta(0) | {"similarity": 0.0}] if self.seed else []
        q_tf = self._tf_vec(q_toks)
        idf = {t: math.log((self._N + 1) / (self._df.get(t, 0) + 1)) + 1.0 for t in q_tf}
        q_vec = {t: q_tf[t] * idf[t] for t in q_tf}
        q_norm = math.sqrt(sum(v * v for v in q_vec.values())) or 1.0
        # candidates: only docs sharing a query term (inverted index)
        cands = set()
        for t in q_tf:
            cands.update(self._inv.get(t, ()))
        if not cands:
            return [{**self._meta(0), "similarity": 0.0}] if self.seed else []
        scored = []
        for i in cands:
            tf = self._tf[i]
            dot = 0.0
            for t, qv in q_vec.items():
                c = tf.get(t)
                if c:
                    dot += qv * c * idf[t]
            if dot <= 0:
                continue
            norm = math.sqrt(sum((c * idf.get(t, 1.0)) ** 2 for t, c in tf.items())) or 1.0
            scored.append((dot / (q_norm * norm), i))
        scored.sort(key=lambda x: x[0], reverse=True)
        out = []
        for sim, i in scored[:top_k]:
            m = self._meta(i)
            if sim <= 0 and m["kind"] == "episode":
                continue
            out.append({**m, "similarity": round(float(sim), 3)})
        if not out:
            return [{**self._meta(0), "similarity": 0.0}] if self.seed else []
        return out

    def history_bias(self, query: str) -> float:
        """Past-conversation nudge: avg delta of similar past episodes, -2..+2."""
        hits = self.retrieve(query, top_k=5)
        epis = [h for h in hits if h["kind"] == "episode"]
        if not epis:
            return 0.0
        avg = sum(h.get("delta", 0) for h in epis) / len(epis)
        return max(-2.0, min(2.0, avg))

    def add_turn(self, bf: str, gf: str, mood: str, delta: float,
                 training: bool = False, save: bool = True) -> Dict:
        # fast max-id: track cached counter instead of scanning 100k docs
        if not hasattr(self, "_max_id"):
            self._max_id = max((d.get("id", 0) for d in self.docs), default=0)
        self._max_id += 1
        turn = {
            "id": self._max_id,
            "bf": bf, "gf": gf, "mood": mood, "delta": delta,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
        if training:
            turn["training"] = True
        self.docs.append(turn)
        self._index_one_episode(turn)
        if save:
            self._save()
        return turn

    def history(self, limit: int = 50, include_training: bool = False) -> List[Dict]:
        if include_training:
            return self.docs[-limit:]
        # fast path: scan from the end, stop once we have `limit` live chats.
        # Old code filtered all 100k+ docs every request (~1s). This is ~0.001s.
        out = []
        for d in reversed(self.docs):
            if not is_training_turn(d):
                out.append(d)
                if len(out) >= limit:
                    break
        return out[::-1]

    def clear_live(self):
        """Wipe real user chats but KEEP training episodes (her memory)."""
        self.docs = [d for d in self.docs if is_training_turn(d)]
        self._rebuild_cache()
        self._save()

    def clear(self):
        self.docs = []
        self._tokcache = {}
        self._save()
