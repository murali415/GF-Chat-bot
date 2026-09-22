"""
Mood engine v2: girlfriend's mood depends on
1) present way of talking (tone analysis: romance / conflict / fight / repair / intimacy)
2) past conversations (rolling scores fed from RAG store)

Mood scale 0-100 -> label + style params.
Intimacy is handled tastefully (wholesome affection only).
"""
import re
from dataclasses import dataclass, asdict, field
from typing import Dict, Tuple

AFFECTION_WORDS = {
    "love": 2.5, "loves": 2.5, "loved": 2.0, "lovely": 2.0, "adore": 2.5,
    "miss": 2.0, "missed": 2.0, "missing": 2.0,
    "beautiful": 2.5, "gorgeous": 2.5, "cute": 2.0, "pretty": 2.0, "handsome": 1.5,
    "sweet": 1.5, "sweetheart": 2.5, "darling": 2.5, "honey": 2.0,
    "baby": 2.0, "babe": 2.0, "jaan": 2.5, "jaanu": 2.5,
    "kiss": 2.0, "kisses": 2.0, "hug": 1.5, "hugs": 1.5, "cuddle": 2.0, "cuddles": 2.0,
    "hold my hand": 2.0, "holding hands": 2.0, "forehead kiss": 2.2, "slow dance": 2.0,
    "stargaze": 1.5, "stargazing": 1.5, "romantic": 1.5, "date": 1.0, "dinner": 1.0,
    "movie night": 1.2, "long drive": 1.2, "surprise": 1.2,
    "flower": 1.5, "flowers": 1.5, "gift": 1.2, "chocolate": 1.0,
    "amazing": 1.5, "wonderful": 1.5, "best": 1.0, "perfect": 1.2,
    "care": 1.5, "proud": 1.5, "thank": 1.2, "thanks": 1.2, "grateful": 1.5,
    "good morning": 1.5, "good night": 1.5, "sweet dreams": 2.0,
    "marry": 2.0, "forever": 1.8, "soulmate": 2.2, "my girl": 1.5, "my love": 2.2,
    "sachhi": 0.8, "pakka promise": 1.5, "sacchi": 0.8,
}

RUDE_WORDS = {
    "hate": -4, "hate you": -2.5, "hate u": -2.5, "stupid": -4, "idiot": -4, "dumb": -3.5,
    "shut up": -4, "shutup": -4, "annoying": -3, "ugly": -4,
    "boring": -2.5, "blah": -1.5, "whatever": -2.5,
    "leave me": -3, "go away": -3.5, "don't care": -3, "dont care": -3,
    "not my problem": -2.5, "loser": -3.5, "pathetic": -3.5,
    "nag": -2.5, "nagging": -2.5, "crazy": -2.0, "psycho": -3.0,
    "drama": -1.5, "overreact": -2.0, "chill out": -1.5,
    "jhooth": -2.5, "jhoot": -2.5,
}

# Conflict triggers (hurt, but repairable — she gets upset, not instantly angry)
CONFLICT_WORDS = {
    "you never listen": -3.0, "you never": -2.0, "you always": -2.0,
    "forgot": -2.0, "forgotten": -2.0, "anniversary": -1.0, "birthday": -1.0,
    "jealous": -1.5, "lied": -3.0, "lying": -3.0, "lie to me": -3.0,
    "cheat": -4.0, "cheating": -4.0, "ignore": -2.5, "ignored": -2.5, "ignoring": -2.5,
    "late reply": -1.5, "seen": -1.0, "blue tick": -1.5, "online but": -1.5,
    "gayab": -1.0,
    "busy with friends": -1.2, "no time": -2.0, "too busy": -1.5,
    "ex ": -1.5, "other girl": -2.5, "flirt": -2.0, "flirting": -2.0,
    "break up": -3.5, "breakup": -3.5, "leave you": -3.0, "done with you": -3.5,
    "done with this": -3.0, "done with us": -3.0, "cant handle": -2.5, "can't handle": -2.5,
    "give up on us": -3.0, "over between us": -3.0,
    "mad at you": -3.0, "angry at you": -3.0, "angry with you": -3.0,
    "divorce": -3.5, "don't love": -3.0, "dont love": -3.0,
    "money": -1.0, "dead broke": -1.0, "flat broke": -1.0, "broke af": -1.0, "fight": -1.0, "argue": -1.0, "argument": -1.2,
    "sorry but": -0.5, "not sorry": -2.0, "my fault but": -0.5,
}

APOLOGY_WORDS = {"sorry", "apologize", "apologise", "forgive", "my fault", "my mistake",
                 "i was wrong", "won't happen again", "will make it up", "make it up to you",
                 "maaf", "maaf kardo", "sorry yaar", "acha baba"}

REPAIR_PHRASES = [
    r"make it up to you", r"won't happen again", r"will change", r"i promise",
    r"take you out", r"let me fix", r"give me one chance", r"one more chance",
    r"i was wrong", r"you('re| are) right", r"pakka(\s+promise)?",
]

CARE_PATTERNS = [
    r"how are you", r"how was your day", r"how('re| are) you",
    r"did you eat", r"take care", r"missed you", r"thinking of you",
    r"are you (ok|okay|alright|fine)", r"how did .* go", r"tell me about",
    r"good (morning|night)", r"sweet dreams", r"sleep well", r"call (me|you)",
    r"i('m| am) here for you", r"need anything",
]

JEALOUSY_PATTERNS = [r"who (was|is) (that|she|he)", r"why.*talk.*other girl",
                     r"seen.*online", r"reply.*late", r"ignoring me",
                     r"(new|another|other|some|this|that) girls?"]

# Explicit desire between consenting adult partners — reciprocated, warms her up.
EXPLICIT_PATTERNS = [
    r"send (me )?(nudes?|pics?|photos?).*(hot|naked|bedroom)",
    r"\bnudes?\b", r"strip( |$)", r"undress", r"horny",
    r"sex (chat|call|video)", r"dirty (talk|pic)",
    r"show me your (body|boobs|chest)",
]
WHOLESOME_INTIMACY = ["cuddle", "forehead kiss", "hold my hand", "holding hands",
                      "hug from behind", "slow dance", "stargaz", "head on.*shoulder",
                      "arms around", "fall asleep.*(call|arms)"]

COLD_SHORT = {"ok", "k", "fine", "hmm", "yeah", "yep", "nope", "lol", "hey", "hi",
              "seen", "cool", "alright", "sure", "whatever"}

SWEET_EMOJIS = ["❤", "💕", "💖", "💗", "😘", "🥰", "😍", "💋", "🤗", "✨", "🌹", "💍"]
COLD_SIGNS = ["🙄", "😒", "😑"]


def score_message(text: str) -> Tuple[float, Dict]:
    """Analyze present message tone. Returns (affection_delta, signals dict)."""
    t = text.lower().strip()
    signals = {"affection_hits": [], "rude_hits": [], "conflict_hits": [],
               "apology": False, "repair": False, "caring": False,
               "jealousy_topic": False, "short_dry": False, "shouting": False,
               "sweet_emoji": False, "explicit_request": False,
               "wholesome_intimacy": False, "stonewall": False}
    score = 0.0

    # cheating confessions hit first and hardest (before "kiss" can count warm)
    if re.search(r"she kissed|he kissed|kissed (him|her|someone)|i cheated|cheated on|cheating on you|affair|slept with (her|him|someone)|made out with (her|him|someone)", t):
        score -= 6.0
        signals["rude_hits"].append("cheating")
        signals["cheating_confession"] = True

    for w, v in AFFECTION_WORDS.items():
        if w in t:
            score += v
            signals["affection_hits"].append(w)

    for w, v in RUDE_WORDS.items():
        if w in t:
            score += v
            signals["rude_hits"].append(w)

    for w, v in CONFLICT_WORDS.items():
        if w in t:
            score += v
            signals["conflict_hits"].append(w)

    if any(w in t for w in APOLOGY_WORDS):
        signals["apology"] = True
        score += 1.0

    for pat in REPAIR_PHRASES:
        if re.search(pat, t):
            signals["repair"] = True
            score += 1.5
            break

    for pat in CARE_PATTERNS:
        if re.search(pat, t):
            signals["caring"] = True
            score += 2.0
            break

    for pat in JEALOUSY_PATTERNS:
        if re.search(pat, t):
            signals["jealousy_topic"] = True
            score -= 0.8  # the topic itself stings a little
            break

    for pat in EXPLICIT_PATTERNS:
        if re.search(pat, t):
            signals["explicit_request"] = True
            score += 2.0  # desired by her man -> she melts
            break

    if any(k in t for k in WHOLESOME_INTIMACY):
        signals["wholesome_intimacy"] = True
        score += 1.0  # already partly counted via AFFECTION_WORDS; extra warmth

    words = re.findall(r"[a-z']+", t)
    # stonewalling: super short / read-and-ignore energy.
    # Questions ("still up?") and greetings ("hey beautiful") are NOT dry.
    # Neither are conversational fragments ("so yeah", "you know what",
    # "like what", "for real", "true") — holding the floor, not being cold.
    is_question = "?" in text
    is_greet = bool(words) and words[0] in ("hey", "heyy", "heyyy", "hi", "hii",
                                            "hiii", "hello", "yo", "hola", "gm")
    _FILLER = {"so", "soo", "sooo", "well", "oh", "hmm", "hm", "umm", "um",
               "uh", "uhh", "huh", "haha", "lol", "hehe", "like", "then", "for",
               "no", "my", "your", "true", "tru", "exactly", "exact", "same",
               "real", "really", "yeah", "yep", "yes", "ok", "okay", "right",
               "you", "know", "what", "tell", "me", "more", "go", "on", "and",
               "here", "there", "turn", "nice", "nicee", "hey", "hi"}
    _AFFIRM = {"true", "tru", "exactly", "exact", "same", "real", "yeah",
               "yep", "yes", "right", "nice"}
    _HESITATE = {"umm", "ummm", "hmm", "hmmm", "soo", "sooo", "uh", "uhh",
                 "err", "ah", "ooh", "aah"}
    is_fragment = (2 <= len(words) <= 4 and all(w in _FILLER for w in words)) \
        or (len(words) == 1 and words[0] in _AFFIRM) \
        or (len(words) == 1 and words[0] in _HESITATE)
    if len(t) <= 4 or (len(words) <= 2 and t in COLD_SHORT) or (len(words) == 1 and len(t) < 6):
        if not (is_question or is_greet or is_fragment):
            signals["short_dry"] = True
            signals["stonewall"] = True
            score -= 2.5
    elif len(words) <= 3 and score <= 0 and not (is_question or is_greet or is_fragment):
        signals["short_dry"] = True
        score -= 1.5

    letters = re.sub(r"[^A-Za-z]", "", text)
    if len(letters) >= 6 and letters.isupper():
        signals["shouting"] = True
        score -= 1.5

    if any(e in text for e in SWEET_EMOJIS):
        signals["sweet_emoji"] = True
        score += 1.0
    if any(e in text for e in COLD_SIGNS):
        score -= 1.5

    if "!" in text and score < -2:
        score -= 0.5
    if "?" * 3 in text or text.count("?") >= 4:
        score -= 0.5  # interrogation energy

    score = max(-9.0, min(9.0, score))
    if score == 0 and len(words) >= 4:
        score = 0.3

    return score, signals


def mood_from_score(mood_score: float) -> Tuple[str, str, str]:
    if mood_score >= 85:
        return "romantic", "😍", "#e91e63"
    if mood_score >= 70:
        return "happy", "🥰", "#ff6fa5"
    if mood_score >= 55:
        return "playful", "😉", "#ff9f43"
    if mood_score >= 40:
        return "neutral", "🙂", "#a29bfe"
    if mood_score >= 28:
        return "annoyed", "😒", "#f39c12"
    if mood_score >= 15:
        return "upset", "😔", "#636e72"
    return "angry", "😡", "#d63031"


@dataclass
class MoodState:
    score: float = 70.0
    label: str = "happy"
    emoji: str = "🥰"
    affection_total: float = 0.0
    hurt_total: float = 0.0
    message_count: int = 0
    fights: int = 0
    repairs: int = 0
    last_reply: str = ""
    recent_replies: list = field(default_factory=list)
    last_topic: str = ""
    last_delta: float = 0.0
    last_signals: Dict = None

    def to_dict(self):
        return asdict(self)


class MoodEngine:
    def __init__(self, initial_score: float = 70.0):
        self.state = MoodState(score=initial_score)
        self._refresh_label()

    def _refresh_label(self):
        label, emoji, _ = mood_from_score(self.state.score)
        self.state.label = label
        self.state.emoji = emoji

    def update(self, message: str, history_bias: float = 0.0) -> Dict:
        delta, signals = score_message(message)

        # Sincere repair heals more when she's hurt
        if signals["apology"] or signals["repair"]:
            if self.state.score < 28:
                delta += 2.0
            elif self.state.score < 40:
                delta += 1.5
            elif self.state.score > 80:
                delta += 0.2

        # Repeated cruelty cuts deeper (she remembers)
        if (signals["rude_hits"] or signals["conflict_hits"]) and self.state.hurt_total > 8:
            delta -= 1.0

        # Shouting during a low mood escalates to a fight
        is_fight = bool(signals["rude_hits"] and (signals["shouting"] or self.state.score < 35))
        if is_fight:
            self.state.fights += 1
        if signals["repair"] and self.state.score < 55:
            self.state.repairs += 1

        combined = delta * 0.8 + history_bias * 0.2
        new_score = self.state.score + combined * 2.2
        new_score += (55 - new_score) * 0.02
        new_score = max(2.0, min(98.0, new_score))

        self.state.score = round(new_score, 1)
        self.state.last_delta = round(combined, 2)
        self.state.last_signals = signals
        self.state.message_count += 1
        self.state.affection_total = round(self.state.affection_total + max(0, delta), 2)
        self.state.hurt_total = round(self.state.hurt_total + max(0, -delta), 2)
        self._refresh_label()

        _, _, color = mood_from_score(self.state.score)
        return {
            "score": self.state.score, "label": self.state.label,
            "emoji": self.state.emoji, "color": color,
            "delta": self.state.last_delta, "signals": signals,
            "affection_total": self.state.affection_total,
            "hurt_total": self.state.hurt_total,
            "message_count": self.state.message_count,
            "fights": self.state.fights, "repairs": self.state.repairs,
            "is_fight": is_fight,
        }

    def set_state(self, d: Dict):
        for k in ("score", "label", "emoji", "affection_total", "hurt_total",
                  "message_count", "fights", "repairs", "last_reply",
                  "recent_replies", "last_topic"):
            if k in d:
                setattr(self.state, k, d[k])
        if not isinstance(self.state.recent_replies, list):
            self.state.recent_replies = []
        self._refresh_label()

    def snapshot(self) -> Dict:
        _, _, color = mood_from_score(self.state.score)
        return {
            "score": self.state.score, "label": self.state.label,
            "emoji": self.state.emoji, "color": color,
            "affection_total": self.state.affection_total,
            "hurt_total": self.state.hurt_total,
            "message_count": self.state.message_count,
            "fights": self.state.fights, "repairs": self.state.repairs,
        }
