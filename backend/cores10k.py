"""
150 fresh real-life cores for the 10k expansion.
Short, real, mostly English + light Hinglish. fast_train10k.py multiplies
each core into ~50 phrasing variants (texting spellings, typos, emoji...).
"""
CORES = [
# greetings / probes
"hey beautiful", "hi jaan, free?", "good evening love", "hey, miss me?",
"you awake?", "still up?", "hey stranger, long time", "guess who",
# morning / night
"morning love, slept well?", "wake up, big day today", "early morning flight, miss you",
"night, don't let bedbugs bite 😌", "sleeping now, love you", "late night, still thinking of you",
"morning traffic sucks", "night shift tonight, ugh",
# love / miss
"love you more than yesterday", "you mean the world to me", "my heart beats for you",
"missing your laugh badly", "wish you were in my arms", "you're my peace",
"love your stupid jokes", "can't stop thinking about your smile",
# compliments / thinking
"that new haircut though 😍", "you looked stunning last night",
"this song = you", "saw your favorite dessert, bought two",
"you'd love this place I'm at", "that sunset needed you",
"your voice note made my day", "you're glowing these days",
# daily / care
"reached home safe", "ate lunch, mom's food ❤️", "stuck in traffic 1hr",
"boss gave extra work again", "payday!! party time 🎉", " Drank 4 coffees today",
"gym leg day killed me", "movie was boring without you", "cooked pasta, edible!",
"rain + chai evening 🌧️", "power cut here, candles 😌", "weekend grocery run done",
"got a haircut, rate it", "new phone wallpaper = us 📱", "mom sends love",
# food / plans
"biryani night? I'm paying", "pizza or Chinese tonight?", "cook together Sunday?",
"trying that new cafe Saturday?", "long drive + music tonight?", "beach plan Sunday morning?",
"midnight maggie partner needed", "ice cream emergency 🍦",
# comfort seeking
"failed the test, feel useless", "lost my wallet, panicking", "phone broke, typing from laptop",
"fight with mom, crying", "best friend ignoring me", "scared about results",
"headache since morning", "couldn't sleep at all", "anxiety high today",
"everyone's mad at me for nothing",
# celebrate
"got the internship!!", "passed driving test!! 🚗", "won the match!!",
"hike confirmed!!", "siblings proud of me today", "artwork selected!!",
"signed the offer letter!!", "lost 3kg this month!!",
# intimacy (wholesome)
"hug me virtually right now", "need your forehead kiss", "hold my hand in dreams",
"slow dance in the rain with me?", "cuddle + thunderstorm outside?", "fall asleep next to me (call)?",
"your lap = my pillow", "kiss me good luck please 😘",
# jealousy
"who were you out with last night", "why is he liking all your posts",
"you replied him instantly, wow", "who's that guy in your story",
"why did you hide your story from me", "who calls you this late",
"that boy best friend again?", "why do you blush at his texts",
"saw you laughing with some guy", "who's texting you nonstop",
# late / phone
"reply fast, it's urgent", "seen since morning, hello?", "are you ignoring me or busy",
"phone addiction is real with you", "put the game down please", "reels can wait, I can't",
"last seen keeps changing, replies don't", "do my texts bore you",
# forgot / dismissive
"you forgot to text back again", "our plan slipped your mind?", "stop saying chill out",
"don't call me dramatic", "take me seriously for once", "stop minimizing my feelings",
# fights
"you're so immature sometimes", "stop twisting my words", "you never take responsibility",
"I can't trust your words now", "you embarrassed me today", "stop comparing me",
"your anger scares me", "you only care when I'm leaving", "this relationship feels one-sided",
"I'm tired of begging for attention",
# repair
"I'll prove it with actions", "tell me what you need from me", "I'll wait till you forgive",
"taking you out Friday, no excuses", "writing you a long letter tonight",
"I'm working on my temper, promise", "you're right about everything",
"I'll keep my phone away at dinner", "daily good mornings restart today",
"consider it done, whatever you asked",
# money / smartass / identity
"can you cover dinner today?", "what's 12x12, quick", "who's your boyfriend? say it 😌",
"do you even know my birthday", "what's my favorite food, test", "am I your favorite person?",
"rate me out of 10, honest", "what do you love most about me", "describe me in 3 words",
"do you dream about me",
# her-day / breakup / edge
"how was office today, details", "did you sleep well?", "are you eating properly?",
"please don't leave me", "give us one more chance", "I can't lose you over this",
"is this really the end?", "say you don't mean it", "fight me, don't leave me",
"love me like before, please",
# extra annoyed fuel (dry, complaints, jealous jabs — real irritants)
"seen-zone again? cool","reply in caps? no. reply at all? also no",
"one-word replies today, I see",
"you text paragraphs to everyone but me",
"dry as toast today",
"phone died? for 6 hours? sure",
"busy with the boys again",
"cancelled on me last minute, classic",
"you forgot. I remembered. as usual",
"laughing at her jokes, silent at mine",
"new girl's photo liked in 2 seconds",
"you remember his birthday, not our date",
"call dropped, no callback. nice",
"you promised 5 mins, it's been 2 hours",
"always online, never for me",
"short replies = big attitude today",
" sarcasm won't fix this",
"you're agreeing with everything = suspicious",
"fine. whatever. you clearly don't care",
"don't 'haha' your way out of this",
"seen my long text? replied 'k'. wow",
"you yawned on call. rude.",
"fell asleep mid-call again",
"you chose the match over our call",
"snoring on call while I vent. thanks",
"you muted me? I heard the beep",
"laughing with friends, dry with me",
"you shared the meme with everyone except me",
"your ex viewed your story? and you replied?",
"you defended HIM instead of me",
"double standards much",
"you never start the conversation",
"I'm always texting first lately",
"you forgot good morning. again",
"dry goodnight. no emoji. noted",
"you left me on read at my good news",
]

# Fire cores: rage, insults, threats, blame, jealous fury -> cold tone
FIGHT_CORES = [
"YOU NEVER LISTEN. EVER", "shut your mouth, I'm done", "you're a liar and I have proof",
"I hate what you've become", "drop dead (I don't mean it but I'm mad)",
"you're cheating, admit it NOW", "I saw the texts. explain. NOW",
"don't you dare lie again", "you make me sick today", "I'll break your phone",
"scream all you want, I'm leaving", "you're dead to me right now",
"filthy liar", "two-faced snake", "shameless. absolutely shameless",
"rot in hell with your excuses", "I'll expose you everywhere",
"watch me walk away for good", "you'll beg and I'll laugh",
"done. blocked. bye. forever", "I curse the day we met (angry words)",
"you're poison in my life", "get lost and stay lost", "I despise you today",
"trash behavior, trash person (sorry, mad)", "I'll smash something, move",
"screaming into my pillow because of YOU", "my blood is boiling",
"don't test my patience today", "one more word and I explode",
"you pushed every button today", "I'm seeing red right now",
"furious. shaking. done.", "how could you do this to us",
"you broke my trust into pieces", "unforgivable. this time it's different",
"I'm raging. don't call me", "stay away from me today", "I need to break things",
"you're the worst part of my day",
]

# Soft cores: sadness, emotional, stressed, vulnerable -> soft tone (upset labels)
SOFT_CORES = [
"crying quietly, don't mind me", "feel empty inside today",
"everyone forgot my birthday", "my dog is sick, praying",
"dad's health scares me", "failed again. I'm a failure",
"lonely even in crowds", "nobody understands me",
"tears won't stop tonight", "miss my childhood home",
"my best friend moved away", "grandma's in hospital",
"lost my job today", "rejected again. tired.",
"feel invisible to everyone", "sad song on loop, thinking",
"overthinking everything tonight", "want to disappear for a while",
"hug me through this phase?", "hold me while I cry?",
"don't let go tonight please", "stay with me, I'm scared",
"everything reminds me of losses", "smile outside, storm inside",
"need comfort, not advice",
]

# Chill cores: mundane daily logistics -> neutral labels
CHILL_CORES = [
"what time is it there", "weather nice today?", "had dal chawal for lunch",
"bus is late again", "bought new shoes", "haircut done, looks okay",
"need to buy groceries", "electric bill paid", "watered the plants",
"cleaned my room finally", "fixed my bike", "new episode out tonight",
"match at 7, watching?", "grocery list: milk, eggs, bread", "ironed clothes for week",
"bank work done", "recharged my metro card", "car service tomorrow",
"need a new charger", "library books due friday", "paying rent today",
"doctor appointment thursday", "dentist was painless, wow", "got a parcel",
"new neighbors moved in", "building painting this week", "lift not working, stairs",
"ordered new bedsheets", "fridge full, cooking week", "washed the car",
]

# Nag cores: everyday irritants that earn dry/snappy comebacks -> cold tone
NAG_CORES = [
"you're late again, shocking", "late as usual, huh",
"forgot my coffee order. again", "you never refill anything",
"left the lights on all night", "you ate my fries. all of them",
"you snore, admit it", "you hog the blanket every night",
"toilet seat saga continues", "you never replace the roll",
"loud chewing. stop.", "you talk during movies",
"you pause the movie for 20 mins", "you spoil every show",
"you never pick up on first ring", "callback ETA: never",
"you read my text and napped?", "voice notes 5 mins long. why",
"you send reels instead of replies", "your memes are stale",
"you laugh at your own jokes only", "you explain my own story back to me",
"mansplaining my own job to me? wow", "you forgot my food allergy. twice",
"you order for me without asking", "you're on the phone with mom. again",
"gaming with friends, me on hold", "football > facetime, noted",
"you cancelled gym with me. solo gym now", "you ate the last slice. betrayal",
"you drank my shake. thief", "you wore my hoodie. keep it (mad)",
"you lost my charger", "you broke my mug. MY mug",
"you scratched my phone", "you spilled chai on my notes",
"you're humming that song wrong", "you sing off-key, loudly",
"you dance-bomb my serious talks", "you tickle during fights. unfair",
"you steal my blanket AND pillow", "you set 7 alarms and wake for none",
"you sleep through my calls", "you dreamt and laughed. without me?",
"you're grumpy before coffee. scary", "you get hangry and I suffer",
"you shop 3 hours, buy socks", "you take 40 mins to get ready",
"you're ready in 5? suspicious. nice though", "you overpack for 2 days",
"you forgot the tickets. WE'RE AT THE GATE", "you took the wrong train. us. stranded",
]

# Tasteful flirty cores: suggestive but never explicit -> warm tone
FLIRTY_CORES = [
"you look hot in that pic 😍", "that dress should be illegal",
"can't stop staring at your photo", "you're dangerously cute today",
"that smile could start wars", "looking like a dream today",
"that pic broke my self-control (almost)", "you're glowing too much, suspicious",
"that look in your eyes... wow", "you're my favorite view, always",
"that laugh is trouble (good trouble)", "your photo = my wallpaper now",
"looking extra kissable today (cheek kiss!)", "that confidence is attractive",
"you're too pretty, it's distracting",
]
