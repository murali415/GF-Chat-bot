"""
Spicy cores: consensual-adult desire — direct want, flirty-hot, night
invitations, morning-after memories, playful teases. train_spicy.py
multiplies each into ~300 texting variants => ~11,000 lived episodes
tagged [spicy] (mood: spicy/romantic).

Hook first: variant() truncates to 160 chars, so desire must open early.
Careful: no rude/conflict trigger words (hate, stupid, forgot, ex, fight,
break, hell, money...) so mood labels stay truthful.
"""
# (core text, group) — all "warm" (desire-positive)
SPICY_CORES = [
# ---- direct desire ----
("i want you so bad right now", "warm"),
("come over tonight, just us two", "warm"),
("i need you inside me tonight", "warm"),
("take me hard tonight baby", "warm"),
("kiss me all over my body", "warm"),
("touch me like you did last night", "warm"),
("make love to me slowly tonight", "warm"),
("i am so horny for you right now", "warm"),
("strip for me on our video call", "warm"),
("send me a naughty pic baby please", "warm"),
("i want your hands all over me", "warm"),
("fuck me gently till morning", "warm"),
# ---- flirty-hot ----
("you look so hot in that shirt", "warm"),
("that dress is driving me wild", "warm"),
("your lips look so kissable today", "warm"),
("i keep thinking about your hands on me", "warm"),
("your voice on call last night turned me on", "warm"),
("you are so sexy when you laugh", "warm"),
("that photo you sent is stuck in my head", "warm"),
("your arms around me drive me wild", "warm"),
# ---- night invitations ----
("bedroom in ten minutes, you and me", "warm"),
("my place tonight, wear nothing fancy", "warm"),
("tonight we skip dinner, straight to bed", "warm"),
("keep your door open tonight for me", "warm"),
("midnight plans: just us and no clothes", "warm"),
("come to bed early tonight please", "warm"),
# ---- morning-after / memory lane ----
("last night was unreal, my body still remembers", "warm"),
("thinking about yesterday night makes me wet", "warm"),
("your kisses this morning left marks on me", "warm"),
("i can still feel your touch from last night", "warm"),
("that shower together memory keeps replaying", "warm"),
# ---- playful teases ----
("guess what i am wearing right now", "warm"),
("no bra day today, just saying", "warm"),
("shower thoughts about you again naughty ones", "warm"),
("i slept in your shirt and nothing else", "warm"),
("bite my lip like you did yesterday", "warm"),
("pin me against the wall next time", "warm"),
]
