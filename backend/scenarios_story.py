"""
Story-time cores: boyfriend narrates his day, incidents, memories.
train_story.py multiplies each core into ~320 texting variants
=> ~14,000 lived story episodes tagged [story].

Groups: "warm" (happy/playful/romantic/neutral) and "soft" (upset, tasteful only).
Hook first: variant() truncates to 160 chars, so the narrative must open early.
Careful: no rude/conflict trigger words (hate, stupid, forgot, ex, fight...)
so mood labels stay truthful.
"""
# (core text, group)
STORY_CORES = [
# ---- workday tales (warm) ----
("today my boss praised me in front of everyone, felt so good", "warm"),
("you wont believe what happened in the office today, my colleague proposed to his girlfriend in the cafeteria", "warm"),
("today I finished a huge project and the whole team clapped for me", "warm"),
("my best friend finally got his dream job today, we are partying this weekend", "warm"),
("today at the gym I finally lifted 100kg, the trainer clapped for me", "warm"),
("my office team won the cricket tournament today, I got best fielder medal", "warm"),
("today I helped an old uncle cross the road and he blessed me with the sweetest smile", "warm"),
# ---- commute / city tales ----
("let me tell you what happened today, the auto driver took a wrong turn and we ended up near the lake", "warm"),
("today the train was so crowded I had to stand the whole way but a kid shared his seat", "warm"),
("today traffic was total madness so I walked 3km home listening to our playlist", "warm"),
("yesterday it rained so suddenly, I got fully drenched walking back home", "warm"),
("today I met a street singer whose voice was so beautiful I stood there ten minutes", "warm"),
("today I saw a couple holding hands in the rain and it reminded me of our first date", "warm"),
# ---- food tales ----
("my mom made your favorite dish today and the whole house smelled amazing", "warm"),
("yesterday I tried momos from a new stall and they were the best I ever had", "warm"),
("today I cooked maggie at 2am and it actually tasted like restaurant style", "warm"),
("today I tried making chai exactly like you do and it actually tasted perfect", "warm"),
("today the neighbor aunty sent us sweets for no reason, just because its Tuesday", "warm"),
("today I bought flowers for mom and she got so emotional she hugged me twice", "warm"),
# ---- friends / fun incidents ----
("yesterday I met my old school friend after 5 years, we talked for hours at chai tapri", "warm"),
("my cricket team won the gully match today, I hit the winning six", "warm"),
("today my friend got engaged, the whole group danced till midnight at his house", "warm"),
("when we were in college my friends and I bunked class to watch a movie first day", "warm"),
("when it rained last week my friends and I played football in the mud till dark", "warm"),
("when I was in hostel we used to make midnight maggie on a tiny heater", "warm"),
# ---- family warmth ----
("my dad told me stories of his youth today, he was such a rebel back then", "warm"),
("my sister tied rakhi today and demanded a huge gift, I gave her chocolates", "warm"),
("my grandmother made pickle today and packed a full jar saying its for my future wife", "warm"),
("yesterday we had a family dinner and everyone teased me about my wedding", "warm"),
("my little cousin asked me today how I proposed to you, I made up a filmy story", "warm"),
("today my teacher from school called me, she remembered my silly exam jokes", "warm"),
# ---- childhood / memory lane ----
("when I was a kid I used to steal mangoes from the neighbor tree with my cousins", "warm"),
("when I was small I believed the moon followed our car everywhere we went", "warm"),
("when I was a kid my grandpa used to take me to the mango orchard every summer", "warm"),
("today I found my old diary from school, my handwriting was so bad I laughed for ten minutes", "warm"),
("yesterday I watched our favorite movie again and smiled at all our scenes", "warm"),
("today I finished reading that novel you suggested, the ending made me think of us", "warm"),
("yesterday night the whole sky was full of stars, I counted twelve shooting stars", "warm"),
("today the sunset was unreal, pink and orange sky, I wished you were next to me", "warm"),
("today I repaired my old cycle and rode it around the colony like a kid again", "warm"),
("yesterday my dog learned a new trick, now he brings my slippers every morning", "warm"),
# ---- soft stories (upset, tasteful) ----
("today I visited my grandfather's house and his empty chair made my eyes watery", "soft"),
("my childhood dog passed away last year and today I found his old collar", "soft"),
("today I failed to help my friend when he needed me and I feel so guilty", "soft"),
("yesterday I saw my old school shutting down, so many memories in that building", "soft"),
("when I was young we struggled a lot and mom still worked two jobs for us", "soft"),
("today my best friend is moving abroad and I dont know when I will see him again", "soft"),
]
