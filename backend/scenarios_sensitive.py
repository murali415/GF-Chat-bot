"""
Sensitive cores: consensual-adult intimacy across 5 moods. train_sensitive.py
multiplies each core into ~2200 texting variants => ~100,000 lived episodes
tagged [intimate].

Groups: passion (spicy), tender (romantic), tease (playful),
         jealous (annoyed), aching (upset, tasteful longing).
Hook first: variant() truncates to 160 chars, so heat must open early.
Validated: passion/tender/tease/aching carry no rude/conflict triggers;
jealous cores intentionally carry jealousy signals (truthful labels).
"""
# (core text, group)
SENSITIVE_CORES = [
# ---- PASSION: bedroom + sexting + raw desire (spicy) ----
("shower together tonight, hot water and your hands", "passion"),
("backseat of your car after the movie, just us", "passion"),
("kitchen counter, flour everywhere, then you", "passion"),
("strip slowly for me on video call tonight", "passion"),
("send me a voice note moaning my name", "passion"),
("office desk fantasy about you again today", "passion"),
("kiss me in the rain till we are breathless", "passion"),
("elevator ride alone with you, hands everywhere", "passion"),
("terrace night, stars above, you inside me", "passion"),
("massage oil ready, your back first then mine", "passion"),
# ---- TENDER: slow romance + devotion (romantic) ----
("slow dance with me to our song tonight", "tender"),
("write me a love letter like old times", "tender"),
("promise me we grow old teasing each other", "tender"),
("cook dinner with me and feed me first bite", "tender"),
("hold my face and kiss my forehead slowly", "tender"),
("plan our anniversary like a fairytale", "tender"),
("fall asleep in my arms every night forever", "tender"),
("tell me again how we first met, every detail", "tender"),
("buy matching rings and wear them always", "tender"),
# ---- TEASE: playful heat (playful) ----
("guess what color i am wearing underneath", "tease"),
("bite my neck softly next time you see me", "tease"),
("leave a hickey where only i can see", "tease"),
("feed me chocolate with your fingers", "tease"),
("tickle war, whoever laughs first removes one cloth", "tease"),
("strawberries and cream on my skin tonight", "tease"),
("roleplay tonight, you pick the story", "tease"),
("spank me lightly for being late today", "tease"),
("shower singing duet, clothes optional", "tease"),
# ---- JEALOUS: possessive heat (annoyed, truthful) ----
("who was that girl all over your story", "jealous"),
("why did you like her photo at midnight", "jealous"),
("you stared at that girl in the cafe", "jealous"),
("your ex texted you again, explain now", "jealous"),
("who is texting you so late at night", "jealous"),
("dont talk to her like that in front of me", "jealous"),
("delete her number right now please", "jealous"),
("who was that girl calling you baby", "jealous"),
# ---- ACHING: longing + missing touch (upset, tasteful) ----
("miss your touch so much tonight", "aching"),
("sleeping alone in this big bed feels empty", "aching"),
("wish you were here holding me tight", "aching"),
("lonely tonight without your arms around me", "aching"),
("need your warmth beside me to sleep", "aching"),
("your side of the bed is cold tonight", "aching"),
("hug me through the phone till i sleep", "aching"),
("miss your kisses when you are far", "aching"),
("nights without you feel endless baby", "aching"),
]
