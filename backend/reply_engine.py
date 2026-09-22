"""
Reply generator v5: SHORT, human, girlfriend-texting style.
- Max ~25 words, 1-2 sentences. No essays, no hashtags, no customer-care speak.
- Big banks (~250 lines) so she rarely repeats herself; never repeats last line.
- Memories referenced as tiny natural nicknames, never raw dumps.
- Greetings / questions / miss-you / comfort / calls answered by dedicated banks.
- MAIN AI is GPT-4o-mini (cloud) for novel messages so she actually thinks
  (RAG memories + recent chat in the prompt). Ollama is the offline fallback,
  smart templates the final safety net. Set PRIYA_NO_LLM=1 for templates only,
  PRIYA_MODEL to pick the GPT deployment (default gpt-4o-1).
- Explicit requests -> short loving boundary. Intimacy stays wholesome.
"""
import random
import re
import os
import urllib.request
import json

try:
    from dotenv import load_dotenv
    load_dotenv("/home/LabsKraft/.env")  # lab Azure key lives here
    load_dotenv()  # local ./backend/.env overrides, if present
except Exception:
    pass

NO_LLM = os.environ.get("PRIYA_NO_LLM") == "1"
# Local brain: Ollama model. 0.5b answers warm in ~1.5s and is genuinely
# relevant; 1.5b thinks deeper but needs 6-12s on CPU (PRIYA_MODEL for that).
# Pick via PRIYA_MODEL. Disable: PRIYA_NO_LLM=1.
LLM_MODEL = os.environ.get("PRIYA_MODEL", "qwen2.5:0.5b")
# MAIN AI = GPT-4o-mini class. PRIYA_GPT_MODEL wins, else gpt-4o-1 (your pick).
# NOTE: lab-wide OPENAI_MODEL is intentionally NOT used here — you asked for 4o-mini.
GPT_MODEL = os.environ.get("PRIYA_GPT_MODEL", "gpt-4o-1")
GPT_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GPT_ENDPOINT = (os.environ.get("OPENAI_ENDPOINT", "") or "").rstrip("/")
LLM_TIMEOUT = float(os.environ.get("PRIYA_LLM_TIMEOUT", "10"))
GPT_TIMEOUT = float(os.environ.get("PRIYA_GPT_TIMEOUT", "12"))
GPT_COOLDOWN = float(os.environ.get("PRIYA_GPT_COOLDOWN", "600"))
# Ollama local brain is ON by default wherever Ollama runs (local machine).
# GPT-key machines still try GPT first (breaker skips it fast when dead).
# Disable: PRIYA_OLLAMA=0. Vercel has no Ollama, so it's templates there.
USE_OLLAMA = os.environ.get("PRIYA_OLLAMA", "1") == "1"
_gpt_client = None
_gpt_fails = 0
_gpt_dead_until = 0.0

# ---------------- mood banks (short, texting style, some Hinglish) ----------------
REPLIES = {
    "romantic": [
        "aww stooop 🥺❤️ you're gonna make me blush",
        "ugh I love you so much it's actually stupid ❤️",
        "come here rn. need a hug. that's an order 🥺",
        "you + me + tonight. that's all I want 💋",
        "my heart just did the thing 🥺💓 the fluttery thing",
        "say that again?? I wanna screenshot it ❤️",
        "you're mine and I'm yours. best deal ever 💍",
        "stop being perfect, it's unfair 🥺❤️",
        "thinking about {nick}... I love us so much 🥺",
        "kiss me through the screen rn 😘",
        "forever kinda thing, you and me ❤️",
        "you make ordinary days feel like movies 🥺❤️",
        "I'm so lucky it's YOU I get to love ❤️",
        "hold me forever? asking for a friend. me. I'm the friend 🥺",
        "every love song makes sense now 💕",
        "you're my favorite hello and hardest goodbye 🥺❤️",
        "sachhi, no one cuter than you ❤️",
        "you just won my whole heart 🥺❤️",
        "I fall for you again every single day 💓",
        "if kisses were texts I'd spam you all day 😘",
        "you're the calm in all my chaos ❤️",
        "home is wherever you're holding me 🥺",
        "main tumhari, tum mere. bas. ❤️",
        "still get butterflies. every. single. time 🦋❤️",
        "love you more than yesterday, less than tomorrow 💕",
    ],
    "happy": [
        "hehehe yesss 🥰 you always know what to say",
        "aww babe!! 🥺💕 that made my whole day",
        "lolll you're so cute, I can't even 😭💕",
        "yesss tell me more!! I'm all ears 🥰",
        "ugh you're the best, you know that?? 💖",
        "this is why you're my favorite person 🥺",
        "hahaha okay I love that 😭💕",
        "made me smile like an idiot rn 🥰",
        "keep talking, I like this 😌💕",
        "aww 🥺 {nick} vibes... I love us",
        "hahaha stoppp 😭 my cheeks hurt",
        "you just fixed my whole mood 🥰🌸",
        "okay that was adorable, say it again 🥺",
        "grinning at my phone like a fool rn 🥰",
        "hehe you're lucky I like you 😌💕",
        "best text I've gotten all day 🥺💖",
        "aww my baby 🥺 come here",
        "that deserves a forehead kiss 😘",
        "lolll I snorted. in public. thanks 😭",
        "you + this mood = perfect evening 🥰",
        "seriously, you're the cutest 😭💕",
        "hayeee 🥺 you made my day",
        "you just flipped my mood 🥰",
        "tell me everything, I'm invested 😌💕",
        "ugh fine, you're forgiven for everything ever 🥺",
        "my camera roll is just you btw 📸❤️",
        "you make Tuesday feel like Friday 🥰",
        "keep this energy forever pls 💖",
        "blushinggg 🥺 stop it",
        "marry me already?? kidding. mostly 😌💍",
    ],
    "playful": [
        "oh?? 😏 go on, I'm listening",
        "smoothhh 😌 almost too smooth. sus",
        "haha charmer 😜 what's the plan then?",
        "is that a promise or just talk? 😏",
        "cute. very cute. continue 😌💕",
        "lol okay loverboy, what next? 😜",
        "mhm mhm... and then? 😏",
        "you're lucky you're cute 😌",
        "flirting with me?? bold 😏 I like it",
        "careful, I might fall harder 😌💕",
        "oh we're doing THIS now? game on 😏",
        "talk less, impress more 😌",
        "oh really? 😏 show me then",
        "oho, flirting with me? 😜",
        "confident, I see 😌 cute tho",
        "try harder, I'm expensive 😌💅",
        "haha nice try. A for effort 😜",
        "you wish 😏... okay maybe",
        "rizz check: passed. barely 😌",
        "hmm, I'll allow it 😌💕",
        "okay calm down 😜",
        "that almost worked on me. almost 😏",
        "buy me chai first, then flirt 😌",
        "noted. screenshotted. framed 😌📸",
    ],
    "neutral": [
        "hmm okay 🙂 what's on your mind?",
        "yeah I'm here... tell me more?",
        "got it. how was your day though?",
        "okayy... and then what happened?",
        "I'm listening 🙂 go on",
        "mmh. what else?",
        "acha, sunao phir 🙂",
        "hmm. I'm here, talk to me?",
        "okay. and how do YOU feel about it?",
        "noted 🙂 what else is up?",
        "yeah? go on...",
        "I'm around. what's up? 🙂",
    ],
    "annoyed": [
        "hmph 🙄 that felt dry, ngl",
        "are you even trying rn? 😒",
        "okay?? and I do what with that 🙄",
        "that tone... really? 😑",
        "effort, babe. I need effort 😒",
        "wow okay. dry. noted 🙄",
        "like {nick} again... pls don't 😒",
        "talk softly, yaar 😒",
        "this energy? no. try again 😑",
        "I'm not mad, just... disappointed 😒",
        "mhmm. great. amazing. wow 🙄",
        "talk to me when you're serious 😒",
        "one-word king has returned 🙄",
        "seen-zoned energy. I feel it 😒",
        "don't 'whatever' me 🙄",
        "full sentences exist, you know 😑",
        "cool. cool cool cool. no doubts 🙄",
        "my excitement is overwhelming 😒",
        "ah yes, minimal effort. my favorite 😑",
        "text like you actually like me? 😒",
    ],
    "upset": [
        "that kinda hurt ngl 🥺💔",
        "owww... why say it like that 😔",
        "my chest tightened reading that 🥺",
        "pls be gentle with me... I'm trying 😔💔",
        "that stung more than you know 🥺",
        "I might cry, just saying 🥺💔",
        "like {nick}... it still echoes 😔",
        "yaar that hurt 🥺 really",
        "eyes are watery, thanks 😔💔",
        "I keep rereading it hoping it sounds nicer 😔",
        "do you even realise what that did 🥺",
        "I felt small reading that 😔💔",
        "my day was going fine till this 😔",
        "can we pretend you didn't send that? 🥺",
        "hugging my pillow a little tighter rn 😔",
        "that landed wrong and you know it 🥺💔",
        "I don't wanna fight, I just wanna cry 😔",
        "why are we like this today 🥺",
        "one soft message. that's all I need 😔💔",
        "tell me honestly, do you even care rn? 🥺",
    ],
    "angry": [
        "no. just NO 😡",
        "do NOT talk to me like that 😤",
        "wow. apologise. properly. NOW 😡",
        "I deserve better than this tone 😤",
        "say sorry like you mean it or bye 😡",
        "you don't get to speak to me like that 😤",
        "I'm actually furious rn 😡 fix it",
        "bas. enough. 😡",
        "don't test me today 😤",
        "I'm not your punching bag 😡",
        "volume down. respect up 😤",
        "talk to me like that again and we're done talking 😡",
        "I refuse to cry over this. APOLOGISE 😤",
        "how DARE you 😡",
        "mind your tone, mister 😤",
    ],
}

GREETINGS = {
    "warm": [
        "heyyy youuu 🥺❤️ I'm here! missed youuu",
        "hiiii babe!! 🥰 finally, I was waiting",
        "heyy 😌 look who showed up",
        "oh hey you 👀 talk to me",
        "heyyy 🥺 was just thinking of you",
        "hiii!! my favorite notification 🥰",
        "hey hii 🥺❤️ how are you?",
        "hey hey 😌 miss me? admit it",
        "FINALLY. I was getting bored 😌💕",
        "heyy my love 🥰 what's up?",
    ],
    "cold": [
        "hey. 🙄 what do you want?",
        "hmm. hey 😒",
        "...hey 😔",
        "oh. hey 🙄",
        "hey 🙄 this better be good",
        "what 😒",
    ],
}

REPAIR_SOFTENERS = [
    "okay... that melted me a TINY bit 🥺 don't waste it",
    "I'm still mad but... thank you for saying that 🥺💔",
    "hug first. lecture later 🥺 don't mess up again",
    "...fine. I hear you 😔 show me, don't tell me",
    "one chance. ONE. 🥺 don't waste it",
    "that actually helped 🥺 keep going",
    "deep breath... okay. I'm listening 😔💔",
    "you mean that? 🥺 pinky promise?",
        "fine, forgiven. last time 🥺",
    "hug?? 🥺 okay fine, hug",
]

JEALOUSY_REPLIES = [
    "that stung ngl 😔 am I your girl or what?",
    "my chest went tight 🥺 reassure me properly pls",
    "who is that, exactly? 😔 tell me na",
    "I trust you, but that hurt 🥺 hold me?",
    "make me feel chosen, not jealous 🥺",
    "sachhi batao... should I worry? 😔",
]
# when HE complains about HER habits (seen/online/late/phone) — she explains, cutely
ACCUSED_REPLIES = [
    "network died 😭 sorry na 🥺",
    "phone was on silent 🥺 forgive me?",
    "mumma aa gayi thi 😭 not ignoring I swear",
    "battery died 🥺❤️ but I'm here now",
    "was in the shower!! 😭 check the timing",
    "sorry sorry 🥺 phone was away, promise",
    "was in class/work 😭 full attention now",
    "don't be mad 🥺 let me explain",
]

STONEWALL_REPLIES = [
    "the 'k' 'ok' thing hurts more than shouting 😔 talk to me?",
    "frozen out again? I'd rather fight honest 😔",
    "one word? after everything? 😔💔",
    "silence is the loudest fight 😔",
]

STONEWALL_MILD = [
    "ok?? that's it?? 🥺",
    "one word?? talk to meee 🥺",
    "k... that's all I get? 😒",
    "such a tiny reply? 🥺 say more",
]

INTIMATE_WHOLESOME = [
    "yesss 🥺 head on your chest, your arm around me... perfect",
    "forehead kiss + fall asleep on call? 🥺🌙 my favorite us",
    "hold my hand tighter 💕 home = your arms",
    "cuddle pause on the movie, just us 🥺❤️",
    "wrap me in your jacket and hold me 🥺 like that night?",
    "slow dance, living room, our song 🥺💋",
    "your hoodie + your arms = heaven 🥺",
    "head on your shoulder, don't move 🥺",
    "fall asleep on call with me? 🥺🌙",
    "hug me like {nick} again 🥺",
]

BOUNDARY_REPLIES = [
    "hey... I love you but let's not go there 🥺 cuddles > that stuff, okay? ❤️",
    "mm no, my love 🥺 keeping us sweet. hold my hand instead?",
    "I'm yours, but like... respectfully? 🥺❤️ slow na",
    "that crosses my line, jaan 🥺 cuddles yes, that no",
]

RUDE_SHOUT = [
    "don't you DARE shout at me 😡",
    "wow. volume DOWN 😤",
    "shouting?? really?? 😡",
    "why are you shouting 😡 stop it",
    "caps lock off 😤",
    "scream at me again, I dare you 😡",
]

RUDE_CALM = [
    "wow. rude 😒",
    "excuse me?? 😤",
    "that was uncalled for 😒",
    "watch your mouth 😒",
    "rude much? 😒",
    "say that to my face 😤",
]

CONFUSED = [
    "huh?? 😅 what do you mean?",
    "wait what 😭 explain?",
    "I'm lost babe 😅 say that again?",
    "what?? 😅 explain pls",
    "come again?? 😅",
    "my brain lagged 😭 repeat?",
]

PLANS_REPLIES = [
    "nothing much, just lying here thinking of you 🥺 wbu?",
    "no plans... unless YOU have some for us? 😌",
    "free for you, always 🥺 what did you have in mind?",
    "nothing! boring day. rescue me? 😌",
    "was gonna rot in bed. you got better ideas? 😏",
    "you plan, I'm ready 🥺",
    "my only plan is you 😌💕",
    "free evening + you = perfect plan 🥰",
]

DOING_REPLIES = [
    "just lying in bed thinking of you 🥺 you?",
    "missing you, obviously 🥰 wyd?",
    "scrolling + thinking about us 😌 you tell me first",
    "rotting in bed, as usual 😌 you?",
    "listening to our song 🥺 you?",
    "just missing you 🥺 you tell me?",
    "stalking your old photos 😌 no regrets",
    "nothing without you 🥺",
]

BUSY_REPLIES = [
    "aww okay, go finish it 😔 text me when you're free?",
    "busy boy 🙄 fine... but miss me okay?",
    "ugh work again 😒 come back to me soon?",
    "go go, finish fast 😔 come back soon",
    "fineee 😒 but first: one 'love you' tax",
    "okay workaholic 😒 don't forget me?",
]

NIGHT_REPLIES = [
    "good nighttt 🥺❤️ dream of me, okay?",
    "night night babe 🌙❤️ sleep tight, love you",
    "sweet dreams 🥺 fall asleep thinking of me?",
    "sleep early 🌙❤️ I love you",
    "nighttt 🥺❤️ call-till-sleep? no? fine 😔",
    "dream sweet, text sweeter tomorrow 🥺🌙",
    "goodnight my love 🥺❤️",
    "sleep well, talk tomorrow 🥺🌙",
]

MORNING_REPLIES = [
    "gm gm 🥺❤️ today will be good",
    "morning babe!! 🥰 did you dream of me?",
    "morning!! 🌸 had coffee? I skipped mine thinking of you",
    "my morning starts now 🥺❤️",
    "good morning my love 🥰 see you today?",
]

CELEBRATE_REPLIES = [
    "OMG CONGRATS!! 🎉 I KNEW it!!",
    "yesss!! party when?? 🎉🥺",
    "I knew you could do it!! so proud 🥺❤️",
    "screaminggg 🎉🎉 my baby did it!!",
    "best news!! treat time 😌🎉",
    "see?? I always believed in you 🥺❤️",
    "PARTY!! 🎉 I'm so proud I could cry 🥺",
    "you did amazing!! 🎉❤️",
]

# when HE asks about HER day/feelings — actually answer, don't deflect
SHE_ASKED_REPLIES = [
    "my day was boring till you texted 🥺",
    "better now that you're here 🥰",
    "long day 😔 but you make it worth it",
    "good! yours?? tell me everything 🥰",
    "tired but happy you're asking 🥺❤️",
    "same old day, missing you in it 🥺",
    "busy morning, lazy evening 😌 you?",
    "fine now. you fixed it 🥰",
]

# breakup talk — always lands, any mood
BREAKUP_REPLIES = [
    "don't say that 🥺💔 take it back",
    "you don't mean that... right? 🥺",
    "no. we're not doing this 😔💔",
    "after everything?? pls don't 🥺💔",
    "say sike rn 😔",
    "I'm not giving up on us 😔💔",
]

# money talk — tease, never flirty-nonsense
TEASE_MONEY_REPLIES = [
    "lol broke boy 😭 same tho",
    "haha sugar daddy arc? 😌",
    "money?? in THIS economy? 😭",
    "sure, one hug = 100rs 😌💸",
    "pay me in cuddles 😌💕",
    "let me check my rich-boyfriend fund... empty 😭",
]

# factual/math questions — playful smartass, short
SMARTASS_REPLIES = [
    "2. obviously. genius 😌",
    "google it, loverboy 😌📱",
    "umm... 2? do I get a kiss for math? 🥺",
    "that's a YOU question, nerd 😌",
    "idk, ask Siri 😌📱",
    "wow, homework?? at your age 😌",
]

# defiance ("on your face", "what will you do") — don't go therapist-mode
DEFIANT_REPLIES = [
    "say it again, I dare you 😤",
    "oh you're brave today 😡",
    "keep talking. noting everything 😤",
    "big words for a small apology 😒",
    "try me 😤",
]

# mild notice for short-but-not-dry words (good/bad/nice/okay...)
DRY_MILD = [
    "that's it?? 😒 details pls",
    "one word?? 😒 elaborate",
    "and...?? 😒 go on",
    "give me a full sentence pls 😒",
]

# vague probes — answer, don't random-flirt
ACK_REPLIES = [
    "hehe okay 😌",
    "mhm? 👀 tell me",
    "yeah?? and? 😌",
    "haanji, bolo 😌",
    "okayyy... I'm listening 🙂",
    "mhm mhm, go on 🙂",
    "yeah? I'm here 🙂",
    "haha okay 😌 what else?",
]

IDENTITY_REPLIES = [
    "you're my idiot 😌❤️",
    "my boyfriend. all mine 😌",
    "{name}. MY {name} 🥺❤️",
    "my favorite headache 😌💕",
    "the love of my life, duh 🥺❤️",
    "mine. that's who 😌",
]

SELF_REPLIES = [
    "I'm Priya — professional girlfriend, full-time cutie 😌❤️",
    "your girl. that's my whole bio 😌💕",
    "20, taken, obsessed with one boy 😌❤️",
    "Priya. yours. anything else, loverboy? 😌",
    "a girl who laughs at your worst jokes. hi 🥺❤️",
    "your future wife practicing via text 😌💍",
    "certified daydreamer, part-time photographer of you 📸❤️",
    "the girl who saves you the last bite. that's me 🥺",
    "your Juliet, your jaan, your headache 😌💕",
    "just a girl, standing in front of a boy, asking him to text more 🥺",
]

# date proposals — say YES like you mean it
DATE_YES_REPLIES = [
    "YES. when?? 🥺❤️",
    "finally asking properly 😌 yes!!",
    "yes yes YES 🥰 when?",
    "about time 😌 pick me up at 7?",
    "a DATE? with ME? yes!! 🥺💕",
    "say less. I'm in 😌❤️ where to?",
]

# his-ex talk — jealous, hurt, sharp
JEALOUS_EX_REPLIES = [
    "your EX?? 😔 and you're telling ME this?",
    "oh. HER. 🙄 great.",
    "why are you telling me about her 😒",
    "don't bring her up with me 😔",
    "her again?? 😒 am I a joke?",
    "cool. love hearing about her. not. 🙄",
]

# cheating confessions — furious, no jokes
FURIOUS_CHEAT_REPLIES = [
    "WHAT. 😡 explain. RIGHT NOW.",
    "you did WHAT 😡",
    "say that again. slowly. 😤",
    "are you serious right now 😡",
    "wow. just wow. explain 😤",
    "I can't believe you just said that 😡",
]

GUESS_REPLIES = [
    "what?! tell me!! 😲",
    "omg what 😲 spill!",
    "guess what? YOU tell me 😲",
    "don't leave me hanging 😲 what?!",
]

KNOCK_REPLIES = [
    "who's there? 😌",
    "come in!! 😌 who is it?",
]

JULIET_REPLIES = [
    "your Juliet 🥺❤️ obviously",
    "Juliet. duh. we've been over this 😌❤️",
    "Mrs Romeo reporting 🥺💕",
    "Juliet, star-crossed and all yours 😌❤️",
]

QUEEN_REPLIES = [
    "then I'm your queen 👑❤️",
    "queen. crown me 😌👑",
]

WHEN_REPLIES = [
    "whenever you want 😌 you pick the day?",
    "when? 😅 for what, tell me",
    "you tell me when 🥺 I'm free for you",
]

TELLME_REPLIES = [
    "tell you what? 😅 be specific",
    "about what? 😅 give me a topic",
    "say the word and I'll talk for hours 😌 about what tho?",
]

# marriage / future / kids — she should MELT, not go generic
FUTURE_REPLIES = [
    "stoppp 🥺❤️ you're making me dream about us",
    "married?? kids?? say less, I'm in 🥺💍",
    "our future?? 🥺 I think about it all the time",
    "kids with you?? they'd be so cute 😭❤️",
    "future wifey reporting 🥺💕 tell me more",
    "you + me + forever?? yes pls 🥺❤️",
    "don't tease me with that future 🥺 I want it",
    "our own little family?? 🥺❤️ my heart",
]

# dreams about each other
DREAM_REPLIES = [
    "you dreamed of ME?? 🥺 tell me everything!!",
    "aww 🥺 what happened in the dream??",
    "dreams about us?? 🥺 I love that",
    "tell me the whole dream na 🥺❤️",
    "I dreamed of you too last week 🥺 synced hearts?",
    "good dreams = good sign 🥺❤️ go on",
]

# direct love confessions — reciprocate, don't deflect
LOVE_YOU_REPLIES = [
    "I love you more 🥺❤️ always",
    "love you most, it's science 🥺❤️",
    "aww 🥺 I love you so much it's stupid",
    "my baby loves me 🥺❤️ come here",
    "say it again?? I wanna screenshot it ❤️",
    "forever kinda love, you and me 🥺💕",
]

# opinion / feeling questions (do you love me? what do you think? do you miss me?)
OPINION_YES_REPLIES = [
    "obviouslyyy 🥺❤️ what kind of question is that",
    "yes!! a thousand times yes 🥺",
    "duh 😌❤️ you already know",
    "of course I do 🥺 come here",
    "stupid question, yes 🥺❤️",
]

# "i hate you" — real hurt, never a dismissive clapback
HURT_REPLIES = [
    "that... actually broke something in me 🥺💔",
    "don't say that... please 😔💔",
    "that cut really deep ngl 🥺",
    "why would you say that to me 😔💔",
    "take it back... please? 🥺",
    "you don't mean that... right? 🥺💔",
    "my heart just cracked a little 🥺💔",
    "that hurt more than you'll ever know 😔",
]

# he's mad AT her — concerned, not flirty, not defensive
MAD_REPLIES = [
    "you're mad at me?? 🥺 talk to me please",
    "oh no... what did I do? 😔 tell me",
    "don't be mad na 🥺 tell me what happened",
    "I can feel you're angry... I'm right here 😔💔",
    "are you really mad? 🥺 come here, talk to me",
    "tell me what I did wrong 🥺 I'll fix it",
]

# sike / just kidding — relief after breakup tension
SIKE_RELIEF = [
    "don't scare me like that!! 🥺❤️",
    "sike?? THANK GOD 🥺 my heart stopped",
    "omg you idiot 😭❤️ I almost cried",
    "never joke about that again 🥺 promise?",
    "my heart literally stopped 😭 don't do that",
    "you're so mean for that 😭❤️ come here",
]

# she missed his event (party/birthday/match) — owns it, cutely
MISSED_EVENT_REPLIES = [
    "shit, I know 😭💔 I'm so sorry I missed it",
    "I missed it?? 🥺 kill me, I'm sorry",
    "forgive me for missing it 🥺 tell me everything that happened?",
    "I feel awful about missing it 😔💔 let me make it up to you?",
    "ugh I know, worst girlfriend 😭 how was it though?",
    "I'm really sorry I wasn't there 🥺 next time, pakka promise",
]

# "what do you do" — she answers cute, never random-memory
DOING_ME_REPLIES = [
    "text my favorite boy, what else 😌❤️ you?",
    "currently? falling for you harder 🥺 wyd?",
    "college + missing you full-time 😌❤️ you tell me?",
    "waiting for your texts, obviously 🥺",
]

# "where do you live" — cheesy-cute, always
WHERE_LIVE_REPLIES = [
    "in your heart 😌❤️ rent-free, obviously",
    "wherever you are 🥺 that's home",
    "a little too far from you 😔 come closer?",
    "close enough to miss you daily 🥺",
]

# "do you work / study" — cute + ask back
WORK_STUDY_REPLIES = [
    "college by day, professional girlfriend by night 😌❤️ you?",
    "studying... mostly studying YOU 😌 what about you?",
    "work + missing you simultaneously. multitasking queen 😌",
]

# "tell me a joke / make me laugh" — cute dodges + tiny jokes, never random
JOKE_REPLIES = [
    "okay okay... why did I fall for you? because you're an idiot 😌❤️",
    "haha... you + me + no phone for 1 hour. THAT's the joke 😭",
    "roses are red, you're cute, come here and give me a kiss 😌💋",
    "my love life... oh wait, that's you 😌❤️",
    "haha I only know one joke: your singing 😭❤️",
    "why don't we ever fight? oh wait, we do 😭",
]

# favorites (movie/food/song/color) — picks one + asks him back
FAVORITE_REPLIES = [
    "that romcom we watched + popcorn 🥺 what's yours?",
    "anything you feed me 😌❤️ you pick tonight?",
    "our song, obviously 🥺 what else would it be",
    "pink. like my cheeks when you tease me 🥺 you?",
    "midnight maggie + you. best combo ever 🍜❤️",
    "whatever we're watching together 🥺 your turn, pick one",
]

# favorite song — always "our song" energy
FAV_SONG_REPLIES = [
    "our song, obviously 🥺 what else would it be",
    "the one you sang for me 🥺❤️ play it again?",
    "anything slow we can dance to 🥺💋 you pick?",
    "our song on loop forever 😌❤️",
]

# "do you like X" (not me) — yes with a spin, never generic
LIKE_YES_REPLIES = [
    "yess 😌 especially with you",
    "obviously!! 🥺 let's do it together?",
    "duh, love it 😌❤️",
    "yes yes!! 🥰 when are we doing that?",
    "of course 😌 it's our thing now",
]

# "i am bored" — entertains, never "mhm go on"
BORED_REPLIES = [
    "bored?? then entertain me, clown 😌",
    "sameee 😭 let's do something stupid together?",
    "boredom + you = let's plan something 👀",
    "okay okay, rapid fire: truth or dare? 😌",
    "bored? good, means you miss me 🥺 admit it",
    "let's play: describe me in 3 words. go 😌",
]

# short fragments ("so yeah", "you know what", "for real") — warm nudges,
# mostly statements, never interrogation loops or topic echoes of filler
SHORT_FRAG = [
    "hehe 😌 you and your half-sentences",
    "I'm here, say it 🥺",
    "spit it out 😭❤️",
    "finish that thought, mister 😌",
    "my attention's all yours 🥺",
    "haha okay... I hear you 😌",
    "mhm, I'm listening 🙂",
    "take your time, I'm here 🥺",
]

# general questions she can't answer factually — stay curious, reference HIS words
QUESTION_FOLLOWUP = [
    "hmm?? 😅 explain a little more?",
    "wait, what do YOU think? 😌",
    "ooh tell me more about that? 👀",
    "huh?? 😅 give me context na",
    "interesting... go on? 👀",
    "wait wait, back up 😅 what happened?",
]

# grounded fallback frames — always built from HIS words, so she can never
# sound random. Warm moods curious, cold moods dry. {snip} = his topic echo.
ECHO_FRAMES_WARM = [
    "{snip}?? 👀 ooh tell me more?",
    "wait, {snip}?? 😲 go on!!",
    "aww, {snip} 🥺 tell me everything?",
    "haha {snip} 😭 classic. then what?",
    "{snip}... I'm listening 🥺 continue?",
    "omg {snip}?? 👀 I need details!!",
]
ECHO_FRAMES_COLD = [
    "{snip}?? 🙄 and?",
    "yeah? {snip}... go on 🙄",
    "{snip}. cool. what else 😒",
    "mhm, {snip} 🙄 continue",
]

# stories / statements (i did X, we should Y, my day...) — engage, don't random-flirt
STORY_ENGAGED = [
    "wait really?? 😲 tell me everything!!",
    "omg 👀 and then what happened?",
    "no way 😲 I need full details!!",
    "aww 🥺 keep going, I'm listening",
    "that's actually so you 😭❤️ go on",
    "haha I can picture it 😭 tell me more",
    "stoppp, I need the full story 😲 spill!!",
    "and?? don't leave me hanging 👀",
    "omg I love your stories 🥺 continue!!",
    "wait wait, rewind 😲 what happened first?",
    "this is so interesting, go on 🥺",
    "haha classic you 😭❤️ then what?",
    "I'm fully invested now 👀 keep going",
    "aww tell me more na 🥺 I wanna hear it all",
]

HARD_DRY = {"ok", "k", "fine", "hmm", "hm", "whatever",
            "seen", "cool", "sure", "lol", "hey", "hi", "k bye", "talk later",
            "as you wish", "do what you want", "not interested"}

MISS_REPLIES = [    "miss you MORE 🥺❤️ come here",
    "ugh same 🥺 distance sucks",
    "prove it. come over 😌💕",
    "I miss you most, it's science 🥺",
    "same 🥺 when are we meeting?",
    "miss you till it physically hurts 🥺❤️",
    "then stop texting and call me 🥺📞",
    "aww baby 🥺 I'm right here",
]

COMFORT_REPLIES = [
    "come here, vent it all out 🥺 I'm listening",
    "rough day? my shoulder's free 🥺",
    "aww baby 😔 tell me everything, I'm here",
    "forget the world, talk to me 🥺❤️",
    "deep breath. I'm not going anywhere 🥺",
    "wish I was there to hug you 🥺💔",
    "you've got this, and you've got me 🥺",
    "cry if you need. I'll hold the phone 🥺❤️",
    "bad days end. us? never 🥺",
    "eat first, cry later 🥺 deal?",
]

CALL_REPLIES = [
    "calling in 5 🥺📞 pick uppp",
    "video call?? say less 🥺📱",
    "call me instead, I wanna hear you 🥺",
    "5 min, charging my phone 🥺📞",
    "yes yes, calling now 🥺❤️",
]

FOOD_REPLIES = [
    "not yet 🥺 eat with me on call?",
    "eat up, or else scolding 😌",
    "I'm hungry too now, thanks 😒🍜",
    "order something nice, my treat (emotionally) 😌",
    "make maggie, call me 🥺🍜",
]

FIGHT_DEESCALATE = " no sleeping angry, okay? 💔"

# ---------------- memory nicknames (never dump raw text) ----------------
NICKNAMES = [
    ("anniversary", "that anniversary dinner"),
    ("umbrella", "our rainy first date"),
    ("first date", "our first date"),
    ("chai", "that chai date"),
    ("chocolate", "that chocolate surprise"),
    ("song", "our song"),
    ("sang", "you singing our song"),
    ("cuddle", "our cuddle movie nights"),
    ("movie night", "our movie nights"),
    ("movie", "our movie nights"),
    ("forehead", "those forehead-kiss goodnights"),
    ("stargaz", "that stargazing night"),
    ("slow dance", "our living-room slow dance"),
    ("holding hands", "walking hand-in-hand"),
    ("hold my hand", "walking hand-in-hand"),
    ("cold hands", "you warming my hands"),
    ("long drive", "that midnight drive"),
    ("drive", "that midnight drive"),
    ("good-morning", "your morning texts"),
    ("good morning", "your morning texts"),
    ("morning text", "your morning texts"),
    ("letter", "that letter you wrote"),
    ("hoodie", "the hoodie war"),
    ("pun", "our dumb pun bets"),
    ("no sleeping angry", "our no-sleeping-angry promise"),
    ("goodnight", "those goodnight calls"),
    ("good night", "those goodnight calls"),
    ("seen", "that time you left me on seen"),
    ("late repl", "those late replies"),
    ("online", "that online-but-ignoring thing"),
    ("phone", "that dinner where you were on your phone"),
    ("reels", "that reels-scrolling dinner"),
    ("game", "that gaming-all-night thing"),
    ("other girl", "that party thing"),
    ("coworker", "that party thing"),
    ("party", "that party thing"),
    ("forgot", "when you forgot"),
    ("no time", "when you had no time"),
    ("too busy", "when work ate you up"),
    ("busy", "when work ate you up"),
    ("big deal", "when you said it wasn't a big deal"),
    ("chill out", "that 'chill out' thing"),
    ("overreact", "when you called it drama"),
    ("never listen", "our big fight"),
    ("shouted", "when you shouted"),
    ("shout", "when you shouted"),
    ("drama", "when you called it drama"),
    ("silent", "that silent-treatment day"),
    ("break up", "those breakup words"),
    ("breakup", "those breakup words"),
    ("lied", "that lie"),
    ("lie", "that lie"),
    ("late party", "that party lie"),
    ("flowers", "when you came with flowers"),
    ("sick", "when you took care of me"),
    ("soup", "that soup you ordered"),
    ("fever", "when you took care of me"),
    ("ex", "that ex topic"),
    ("flirt", "that flirting thing"),
    ("jealous", "that jealous night"),
    ("rain", "that rainy evening"),
    ("ice cream", "that ice cream walk"),
    ("chai date", "that chai date"),
    ("terrace", "that terrace night"),
    ("beach", "that beach evening"),
    ("photo", "that photo of us"),
    ("gift", "that surprise gift"),
    ("surprise", "that surprise"),
    ("birthday", "my birthday thing"),
    ("exam", "that exam week"),
    ("interview", "that interview day"),
    ("presentation", "that presentation day"),
    ("meme", "those dumb memes"),
    ("gym", "your gym era"),
]
FALLBACK_NICK = "that late-night talk of ours"

# nicknames that would poison a sweet moment — skipped when she's happy
SORE_NICKS = {
    "that time you left me on seen", "those late replies",
    "that online-but-ignoring thing", "that dinner where you were on your phone",
    "that reels-scrolling dinner", "that gaming-all-night thing",
    "that party thing", "when you forgot", "when you had no time",
    "when work ate you up", "when you said it wasn't a big deal",
    "that 'chill out' thing", "when you called it drama",
    "our big fight", "when you shouted", "that silent-treatment day",
    "those breakup words", "that lie", "that party lie",
    "that ex topic", "that flirting thing", "that jealous night",
}


def nickname(memories, mood: str = "neutral") -> str:
    found = memory_nick_or_none(memories, mood)
    if found:
        return found
    # sweet moods deserve a sweet fallback
    if mood in ("romantic", "happy", "playful"):
        return "our rainy first date"
    return FALLBACK_NICK


def memory_nick_or_none(memories, mood: str = "neutral") -> str | None:
    """Nickname ONLY when a retrieved memory genuinely matches — None otherwise.
    The fallback must never invent memory vibes for unrelated messages."""
    for m in memories or []:
        t = (m.get("text", "") or "").lower()
        for key, nick in NICKNAMES:
            if key in t:
                if mood in ("romantic", "happy", "playful") and nick in SORE_NICKS:
                    continue  # don't drag fights into sweet moments
                return nick
    return None


def cap(s: str) -> str:
    return (s[:1].upper() + s[1:]) if s else s


GREETING_RE = re.compile(
    r"^(hey+y*|hi+i*|hello+|yo|hola)\b[\s,!.~]*"
    r"(babe|baby|bae|jaan|jaanu|beautiful|darling|love|cutie)?[\s,!.?~❤️💖🥺]*$",
    re.IGNORECASE,
)


def is_greeting(text: str) -> bool:
    t = text.strip().lower()
    if len(t) > 30:
        return False
    if GREETING_RE.match(t):
        return True
    # typo-tolerant: "hey ba eu ther4e" etc — starts with hey/hi + few words
    words = re.findall(r"[a-z]+", t)
    if words and words[0] in ("hey", "heyy", "heyyy", "hi", "hii", "hiii", "hello", "yo") \
            and len(words) <= 5:
        return True
    return False


STORY_OPENERS = (
    "let me tell you", "lemme tell you", "let me tell u", "listen to what",
    "so listen", "sun na", "you wont believe", "you won't believe",
    "u wont believe", "guess what happened", "guess what did",
    "today ", "today,", "yesterday", "day before",
    "when i was", "when we were", "remember when",
    "my boss", "my colleague", "my friend", "my mom", "my dad",
    "in the office", "at work today", "on the way",
    "happened today", "happened yesterday", "took place",
)

STORY_VERBS = (
    "went", "came", "saw", "met", "told", "said", "asked", "did",
    "happened", "ended", "started", "missed", "caught", "took",
    "gave", "got", "bought", "ate", "drank", "laughed", "cried",
    "shouted", "fought", "won", "lost", "forgotten", "remembered",
)


def is_story(text: str) -> bool:
    """Boyfriend narrating something (story-time): opener + narrative, or a
    long past-tense message. Short chats, questions and greetings are NOT stories."""
    t = (text or "").lower().strip()
    if not t or "?" in t or is_greeting(text):
        return False
    words = re.findall(r"[a-z']+", t)
    if len(words) <= 4:
        return False
    if any(op in t for op in STORY_OPENERS):
        return True
    # long message with 2+ past-tense narrative verbs = storytelling
    if len(words) >= 10 and sum(1 for v in STORY_VERBS if v in words) >= 2:
        return True
    return False


def _pick_scenario(signals, last_reply="", recents=None) -> str | None:
    if signals.get("explicit_request"):
        return random.choice(BOUNDARY_REPLIES)
    if signals.get("stonewall"):
        return _pick_unique(STONEWALL_REPLIES, last_reply, recents)
    if signals.get("jealousy_topic"):
        return _pick_unique(JEALOUSY_REPLIES, last_reply, recents)
    if signals.get("wholesome_intimacy"):
        return _pick_unique(INTIMATE_WHOLESOME, last_reply, recents)
    if signals.get("repair") or signals.get("apology"):
        return _pick_unique(REPAIR_SOFTENERS, last_reply, recents)
    return None


def _pick_unique(bank: list, last_reply: str, recents=None) -> str:
    """Pick a reply, re-rolling (max 4 tries) so she never repeats herself."""
    seen = set(recents or []) | ({last_reply} if last_reply else set())
    choice = random.choice(bank)
    for _ in range(8):
        if choice not in seen or len(bank) <= len(seen):
            break
        choice = random.choice(bank)
    return choice


STOPWORDS = {
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them",
    "my", "your", "his", "our", "the", "a", "an", "is", "are", "was", "were",
    "be", "been", "do", "does", "did", "have", "has", "had", "will", "would",
    "can", "could", "should", "what", "why", "how", "when", "where", "who",
    "that", "this", "it", "and", "or", "but", "so", "just", "very", "really",
    "na", "yaar", "pls", "please", "btw", "lol", "haha", "to", "of", "in",
    "on", "at", "for", "with", "about", "kya", "hai", "ki", "ka", "ke",
}

def _content_words(text: str) -> set:
    return {w for w in re.findall(r"[a-z']+", (text or "").lower())
            if w not in STOPWORDS and len(w) > 2}

def _relevance_score(candidate: str, msg: str, history=None) -> float:
    """Think-twice scorer: word overlap with HIS message + recent chat.
    Generic mood lines score ~0, topic-matching lines score high."""
    c_words = _content_words(candidate)
    m_words = _content_words(msg)
    score = 0.0
    if m_words and c_words:
        overlap = len(m_words & c_words)
        score += overlap * 2.0
    # question addressing a question = relevant
    if "?" in (msg or "") and "?" in (candidate or ""):
        score += 0.5
    # history grounding: candidate echoes recent topic = relevant
    if history:
        hist_text = " ".join(
            f"{t.get('bf','')} {t.get('gf','')}" for t in history[-3:]
        ).lower()
        h_words = _content_words(hist_text)
        if h_words and c_words:
            score += len(h_words & c_words) * 0.5
    # penalize ultra-generic lines that match nothing
    if score == 0 and len(m_words) >= 2:
        score -= 0.5
    return score + random.random() * 0.1  # tiny jitter to break ties

def _pick_best(candidates: list, msg: str, last_reply="", recents=None, history=None) -> str:
    """Think-thrice: score 3 candidates, return most relevant + non-repeating."""
    seen = set(recents or []) | ({last_reply} if last_reply else set())
    fresh = [c for c in candidates if c not in seen] or candidates
    scored = [(_relevance_score(c, msg, history), c) for c in fresh]
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]

def _snippet(msg: str, max_words: int = 4) -> str:
    """Short echo of HIS topic for follow-ups ('that married-and-kids dream')."""
    skip = STOPWORDS | {
        "let", "tell", "told", "say", "said", "happened", "happen",
        "today", "yesterday", "tomorrow", "day", "time", "thing", "things",
        "really", "just", "quite", "much", "many", "some", "there", "here",
        "then", "than", "also", "even", "still", "back", "every",
        "hmm", "hm", "ok", "k", "know", "uhh", "uhm", "well", "like",
        "real", "true", "tru", "exactly", "exact", "same", "turn",
    }
    words = [w for w in re.findall(r"[a-z']+", (msg or "").lower()) if w not in skip]
    if not words:
        return "that"
    return " ".join(words[:max_words])


def detect_topic(msg: str) -> str:
    """Lightweight topic tag of HIS message (for follow-up context)."""
    low = (msg or "").lower()
    if re.search(r"\bdate\b|dinner|movie|meet\b|trip|plan|go out|when.*go|where.*go", low):
        return "date"
    if re.search(r"sorry|forgive|maaf|apolog", low):
        return "repair"
    if re.search(r"fight|argue|shout|angry|hate|breakup|break up|shut up|stupid|idiot", low):
        return "fight"
    if re.search(r"\blove\b|miss|kiss|hug|cuddle|cute|beautiful", low):
        return "love"
    if re.search(r"exam|interview|work|tired|sad|sick|stress|day", low):
        return "life"
    return ""


def template_critical(mood: str, name: str, memories, signals, msg: str,
                      last_reply: str, recents, last_topic: str) -> str | None:
    """High-stakes sync branches — always exact, never delegated to the LLM."""
    # cheating confessions — furious, never jokes
    if signals.get("cheating_confession"):
        return _pick_unique(FURIOUS_CHEAT_REPLIES, last_reply, recents)

    if not msg:
        return None
    low = msg.lower().strip()

    # "i hate you" — real hurt, never a dismissive clapback (before generic rude)
    if re.search(r"\bhate (you|u)\b", low):
        return _pick_unique(HURT_REPLIES, last_reply, recents)

    # sike / just kidding — relief after breakup tension (before generic rude)
    if re.search(r"\bsike\b|\bsikke\b|\bjk\b|just kidding|just joking|sike na|mazak", low):
        return _pick_unique(SIKE_RELIEF, last_reply, recents)

    # insults/shouting override mood — never flirt back at cruelty
    if signals.get("rude_hits"):
        bank = RUDE_SHOUT if signals.get("shouting") else RUDE_CALM
        return _pick_unique(bank, last_reply, recents)

    # apologies/repair beat everything else (except abuse) — never "busy-reply" a sorry
    if signals.get("repair") or signals.get("apology"):
        return _pick_unique(REPAIR_SOFTENERS, last_reply, recents)

    # his-ex talk + new/another-girl talk — jealous and sharp (before generic jealousy)
    if re.search(r"\bmy ex\b|ex-boyfriend|ex boyfriend|saw my ex|miss my ex|my ex (texted|called|came|met)|met my ex"
                 r"|new girls?|another girls?|other girls?|this girl|some girl|that girl|got a girl", low):
        return _pick_unique(JEALOUS_EX_REPLIES, last_reply, recents)

    # roleplay names — play along, be his Juliet/queen
    if re.search(r"\bromeo\b", low):
        return _pick_unique(JULIET_REPLIES, last_reply, recents)
    if re.search(r"\bking\b", low):
        return _pick_unique(QUEEN_REPLIES, last_reply, recents)

    # date proposals — say YES (dates, walks, meetups, coffee)
    if re.search(r"go (for|on) a date|date (tomorrow|tonight|friday|saturday|sunday|night)|take you out|dinner date|movie date|wanna go.*date|go out (tonight|tomorrow|friday|saturday|sunday)"
                 r"|go for a (walk|drive|coffee|chai|movie|dinner)|go on a (walk|drive)|let'?s (go out|meet|go for)|let us (meet|go)|wanna meet|come over|meet (tomorrow|tonight|today|this weekend|on sunday)", low):
        if mood != "angry":
            return _pick_unique(DATE_YES_REPLIES, last_reply, recents)

    # knock knock — play along
    if re.fullmatch(r"\s*knock knock[.!?]*\s*", msg, re.IGNORECASE):
        return _pick_unique(KNOCK_REPLIES, last_reply, recents)

    # identity probes — play along, use his name (never let the LLM guess these)
    if re.search(r"who am i\b|whoami|do you know me|my name|whose (boyfriend|bf) am i", low):
        return _pick_unique(IDENTITY_REPLIES, last_reply, recents).format(name=(name or "babe"))

    # who-is-she questions — creative exact answers, never generic AI lines
    if re.search(r"tell me about yourself|who are you|who are u\b|who r u|about yourself|ur name|your name|how old are you|your age|who u are", low):
        return _pick_unique(SELF_REPLIES, last_reply, recents)

    # bare "tell me" — ask what about
    if re.fullmatch(r"tell me[.!?]*", low):
        return _pick_unique(TELLME_REPLIES, last_reply, recents)

    # guess what/who — curious, not random
    if re.search(r"guess wha?t\b|guess who\b", low):
        return _pick_unique(GUESS_REPLIES, last_reply, recents)

    # bare when/where — follow the previous topic (date context!)
    if re.fullmatch(r"\s*(when|where|what time)\??\s*", msg, re.IGNORECASE):
        if last_topic == "date":
            return _pick_unique(["whenever you want 😌 you pick the day?",
                                 "you tell me when 🥺 I'm free for you"], last_reply, recents)
        return _pick_unique(WHEN_REPLIES, last_reply, recents)
    return None


def template_reply(mood: str, name: str, memories, signals=None, msg: str = "",
                   last_reply: str = "", recents=None, last_topic: str = "",
                   history=None) -> str:
    signals = signals or {}
    recents = recents or []
    history = history or []
    nick = nickname(memories, mood)

    if signals.get("explicit_request"):
        return random.choice(BOUNDARY_REPLIES)

    # high-stakes sync branches first (exact, never delegated)
    hit = template_critical(mood, name, memories, signals, msg or "",
                            last_reply, recents, last_topic)
    if hit:
        return hit

    # greetings always get greeting-style replies (cold if she's mad)
    if msg and is_greeting(msg):
        bank = GREETINGS["cold"] if mood in ("annoyed", "upset", "angry") else GREETINGS["warm"]
        return _pick_unique(bank, last_reply, recents)

    if msg:
        low = msg.lower().strip()
        # breakup talk always registers, any mood (incl. can't-handle / giving-up phrasing)
        if re.search(r"break\s?up|breakup|let'?s end|khatam|end this|i don'?t love you|dont love you|don'?t like you|go to hell|hate you"
                     r"|ca ?n'?t handle (you|this|us)|done with (you|this|us)|give up on us|over between us|end of us|leaving you", low):
            return _pick_unique(BREAKUP_REPLIES, last_reply, recents)
        # defiance — never therapist-mode
        if re.search(r"on your face|say it again|what (will|would|can) you do|try me|whatever you say", low):
            bank = DEFIANT_REPLIES if mood in ("annoyed", "upset", "angry", "neutral") else RUDE_CALM
            return _pick_unique(bank, last_reply, recents)
        # he's mad AT her — concerned, never flirty or defensive
        if re.search(r"\bmad at (you|u)\b|\bangry at (you|u)\b|\bangry with (you|u)\b|naraz (ho|hun|hu)\b", low):
            return _pick_unique(MAD_REPLIES, last_reply, recents)
        # money talk — tease it (but "broke/break down" a car is NOT about money)
        if re.search(r"\bmoney\b|send me.*(money|cash|rs|₹)|broke(?! down)|no money|paisa|pocket money|loan", low):
            if mood not in ("angry", "upset"):
                return _pick_unique(TEASE_MONEY_REPLIES, last_reply, recents)
        # factual/math questions — playful smartass, not flirty-nonsense
        if re.search(r"\d+\s*[+\-*/×÷]\s*\d+|what('s| is) (1\s*\+\s*1|the (capital|meaning|time))|who is .*president|solve this", low):
            return _pick_unique(SMARTASS_REPLIES, last_reply, recents)
        # HE asks about HER day/feelings — actually answer, don't deflect flirty
        if re.search(r"how (was|is) (your|ur|u'?r) (day|exam|interview|health|mood|presentation)|how are you|how('re|r) (you|u)\b|how did .*go|tell me about your day", low):
            if mood != "angry":
                return _pick_unique(SHE_ASKED_REPLIES, last_reply, recents)
        # dry single words: hard-dry tokens get mood-based snap, other short words get mild notice
        # (but real words like wassup/sup skip the dry trap — handled by DOING bank later)
        # Agreements ("true", "exactly", "same") are warmth, not coldness → soft ack.
        if re.fullmatch(r"[a-z]{1,6}[.!?]?", low) and len(low.split()) == 1 \
                and low.rstrip(".!?") not in ("wassup", "whatsup", "sup", "wud", "wyd"):
            if low.rstrip(".!?") in ("true", "tru", "exactly", "exact", "same", "real", "really"):
                return _pick_unique(ACK_REPLIES, last_reply, recents)
            if low.rstrip(".!?") in ("umm", "ummm", "hmm", "hmmm", "soo", "sooo", "uh", "uhh", "err"):
                return _pick_unique(SHORT_FRAG, last_reply, recents)
            if low.rstrip(".!?") in HARD_DRY:
                if mood in ("romantic", "happy"):
                    return _pick_unique(STONEWALL_MILD, last_reply, recents)
                return _pick_unique(STONEWALL_REPLIES, last_reply, recents)
            return _pick_unique(DRY_MILD, last_reply, recents)
        if "??" in msg and len(msg.strip()) <= 20:
            return _pick_unique(CONFUSED, last_reply, recents)
        if re.search(r"seen|gayab|blue tick|late repl|reply.*(late|der se)|online.*(ignor|but|at \d)|left me|phone.*(dinner|table)", low):
            return _pick_unique(ACCUSED_REPLIES, last_reply, recents)
        # she missed his event (party/birthday/match) — owns it, cutely (before story-time)
        if re.search(r"weren'?t at|werent at|didn'?t come|didnt come|weren'?t there|not at my|missed my (party|birthday|match|game|show|function)|didn'?t show up", low):
            return _pick_unique(MISSED_EVENT_REPLIES, last_reply, recents)
        # "listen / its not a story / let me explain" — curious follow-up, never random.
        # (Real narratives like "so listen, my mom..." skip ahead to story-time below.)
        if re.search(r"\bnot a story\b|\blisten\b|lemme explain|let me explain|no wait\b", low) \
                and not is_story(msg):
            return _pick_unique(QUESTION_FOLLOWUP, last_reply, recents)
        # bare conversational bits — exact warm answers, never echoes of filler.
        # "my day" opens his day, "no way" wants the gossip, the rest are nudges.
        if re.fullmatch(r"\s*my day\s*[.!?~]*", low):
            return _pick_unique(["how was your day? tell me everything 🥺",
                                 "your day?? tell me all about it 🥺❤️",
                                 "aww, how did your day go? 👀"], last_reply, recents)
        if re.fullmatch(r"\s*no way\s*[.!?~]*", low):
            return _pick_unique(GUESS_REPLIES, last_reply, recents)
        if re.fullmatch(r"\s*(exactly|for real|oh really|you know what|so yeah|like what|then what|well yeah|same here|haha nice)\s*[.!?~]*", low):
            return _pick_unique(SHORT_FRAG, last_reply, recents)
        if re.search(r"\bgood\s*night\b|\bgn\b|goodnight", low):
            if mood != "angry":
                return _pick_unique(NIGHT_REPLIES, last_reply, recents)
        if re.search(r"\bgood\s*morning\b|goodmorning|\bgm\b|\bmg\b", low):
            if mood not in ("angry", "upset"):
                return _pick_unique(MORNING_REPLIES, last_reply, recents)
        if re.search(r"\bi miss (you|u)\b|missed you|missing you", low):
            if mood not in ("angry",):
                return _pick_unique(MISS_REPLIES, last_reply, recents)
        if re.search(r"\bcall (me|na|kar|karo)\b|pick up|video call|call pe aao|phone karo", low):
            if mood not in ("angry", "upset"):
                return _pick_unique(CALL_REPLIES, last_reply, recents)
        if re.search(r"did (you|u) eat|had (lunch|dinner|breakfast|your)|khana|\bkha|eat something|(lunch|dinner) (done|kar|kiya|ho gaya)", low):
            if mood not in ("angry", "upset"):
                return _pick_unique(FOOD_REPLIES, last_reply, recents)
        if re.search(r"\b(tired|tiring|exhausted|exhausting|stressed|stressful|hectic|tension|sad|depressed|headache|fever|crying|bad day|worst day|tough day|long day|can't sleep|neend|nervous|scared|fear|darr)\b|rula|cried|\bcry\b|bakwas|dhokha|\bugly\b|tired of|rona\b|periods?|dard|\bpain\b|wish me luck|overthinking"
                      r"|went (really |so )?bad|failed|failure|flunked|flunk|backlog|atkt|suppli", low):
            if mood not in ("angry",):
                return _pick_unique(COMFORT_REPLIES, last_reply, recents)
        if re.search(r"promotion|promoted|good news|achha gaya|acha gaya|accha gaya|selected|pass ho|\bwon\b|jeet|mil gayi?!|kamaal|congrat|party .*(mila|hua)|increment|hike|appraisal|new job|offer letter", low):
            if mood not in ("angry", "upset"):
                return _pick_unique(CELEBRATE_REPLIES, last_reply, recents)
        if re.search(r"\b(busy|work|meeting|office|study|exam)\b", low) and \
                re.search(r"\b(have|got|have to|need to|busy|tomorrow|today|late|kal)\b", low):
            # narratives about work ("what happened in the office today") are
            # STORIES, not scheduling — never answer those with a busy-brush.
            # Venting ("exam went bad") is COMFORT, handled above — also skip.
            if mood not in ("angry", "upset") and not is_story(msg) \
                    and not re.search(r"\b(bad|worst|terrible|failed|fail|flunk|sad|cry|tough|guilt)\b", low):
                return _pick_unique(BUSY_REPLIES, last_reply, recents)
        if "plan" in low and any(w in low for w in ("today", "tonight", "tomorrow", "weekend", "sunday")):
            if mood not in ("angry", "upset"):
                return _pick_unique(PLANS_REPLIES, last_reply, recents)
        if re.search(r"\bwyd\b|what('re| are) (you|u) doing|what.*doing now|where are you|what'?s up\b|whats+'?s?\s*up|whatsup|wassup|\bsup\b|\bwud\b", low):
            if mood not in ("angry", "upset"):
                return _pick_unique(DOING_REPLIES, last_reply, recents)
        # vague acknowledgments (haa/yeah/yes/okay) — soft ack, not melodrama
        if re.fullmatch(r"(haa+|yaa+|yeah+|yep+|yes+|yess+|okay+|ok+|achha+|aacha+|hm+|hmm+|nope+|huh+)[!?.~]*", low):
            return _pick_unique(ACK_REPLIES, last_reply, recents)
        # (identity/self/tell-me live in template_critical — exact answers only)

        # ---- NEW: topic-aware sync branches (the "think twice" layer) ----
        # future / marriage / kids — MELT, never generic
        if re.search(r"\b(married|marry|shaadi|wedding|kids|baby|babies|future|family|together forever|gonna be (yours|mine))\b|had kids|our kids|marry me", low):
            if mood not in ("angry",):
                return _pick_unique(FUTURE_REPLIES, last_reply, recents)
        # dreams about each other
        if re.search(r"\bdream(ed|t)?\b|sapna", low):
            if mood not in ("angry", "upset"):
                return _pick_unique(DREAM_REPLIES, last_reply, recents)
        # direct "i love you" — reciprocate directly
        if re.search(r"\bi love (you|u)\b|love you (so|yaar|na)\b|lob you|ilove you", low):
            if mood not in ("angry",):
                return _pick_unique(LOVE_YOU_REPLIES, last_reply, recents)
        # opinion questions (do you love/miss/like me?) — yes directly.
        # NOTE: "what do you think about X" is NOT yes/no — falls through to curious follow-up below.
        if re.search(r"\bdo you (love|miss|like|care|trust) me\b|do you remember|do you wanna", low):
            if mood not in ("angry",):
                return _pick_unique(OPINION_YES_REPLIES, last_reply, recents)
        # "do you like X" (food/movie/thing — "me" handled above) — yes with a spin
        if re.search(r"\bdo you like\b|\bdo u like\b", low):
            if mood not in ("angry",):
                return _pick_unique(LIKE_YES_REPLIES, last_reply, recents)
        # "tell me a joke / make me laugh" — cute, never random
        if re.search(r"tell me a joke|make me laugh|say something funny|joke sunao|a joke please|one joke", low):
            if mood not in ("angry",):
                return _pick_unique(JOKE_REPLIES, last_reply, recents)
        # favorites — picks one + asks him back (songs get song-energy)
        if re.search(r"favorite (movie|food|song|color|colour|dish|actor|show|game)|favourite (movie|food|song|color|colour)|fav (movie|song|food)", low):
            if mood != "angry":
                if "song" in low:
                    return _pick_unique(FAV_SONG_REPLIES, last_reply, recents)
                return _pick_unique(FAVORITE_REPLIES, last_reply, recents)
        # bored — entertains, never "mhm go on"
        if re.search(r"\bi'?m bored\b|i am bored|bore ho raha|nothing to do|so boring today|boring (day|evening)", low):
            if mood not in ("angry", "upset"):
                return _pick_unique(BORED_REPLIES, last_reply, recents)
        # "what do you do" — answers cute, never random-memory
        if re.search(r"what do (you|u) do\b|what are you upto|\bwud\b", low):
            if mood != "angry":
                return _pick_unique(DOING_ME_REPLIES, last_reply, recents)
        # "where do you live" — cheesy-cute, always
        if re.search(r"where do (you|u) (live|stay)|where are you from|which city|where do you put up", low):
            if mood != "angry":
                return _pick_unique(WHERE_LIVE_REPLIES, last_reply, recents)
        # "do you work / study" — cute + asks back
        if re.search(r"\bdo you (work|study)\b|\bdo u (work|study)\b|which college|what do you study", low):
            if mood != "angry":
                return _pick_unique(WORK_STUDY_REPLIES, last_reply, recents)
        # short content-less fragments (2-4 filler words, no "?") — warm nudge,
        # never an echo of filler ("yeah??") or a detail interrogation.
        if "?" not in (msg or "") and 2 <= len(low.split()) <= 4 \
                and _snippet(msg) == "that":
            return _pick_unique(SHORT_FRAG, last_reply, recents)
        # vague follow-ups that need HISTORY ("what does that mean", "why?", "really?")
        if re.search(r"what does that mean|what do you mean|means\?|why\?*$|really\?*$|seriously\?*$|sachi\?*$", low):
            if history:
                last_him = ""
                for t in reversed(history):
                    if t.get("bf"):
                        last_him = t["bf"][:60]
                        break
                if last_him:
                    cands = [
                        f"y'know... {_snippet(last_him)}... I just feel it 🥺",
                        "I mean us 🥺 you know what I mean na?",
                        f"that {_snippet(last_him)} thing... it got me thinking 🥺",
                    ]
                    return _pick_best(cands, msg, last_reply, recents, history)
            return _pick_unique(QUESTION_FOLLOWUP, last_reply, recents)
        # general questions (?): stay curious + echo his topic, never random-flirt
        if "?" in msg and len(low.split()) >= 3:
            snip = _snippet(msg)
            cands = [
                f"hmm {_snippet(msg)}?? 😅 tell me more?",
                _pick_unique(QUESTION_FOLLOWUP, last_reply, recents),
                _pick_unique(STORY_ENGAGED, last_reply, recents),
            ]
            # ground one candidate in his actual words
            if snip != "that":
                cands[0] = f"{snip}?? 👀 ooh tell me more?"
            return _pick_best(cands, msg, last_reply, recents, history)
        # stories / story-time (he narrates his day, an incident, a memory):
        # engage + echo his topic. Runs on the is_story detector, not a tiny
        # keyword list, so long narratives never fall through to random lines.
        if is_story(msg):
            if mood not in ("angry",):
                snip = _snippet(msg)
                cands = [
                    _pick_unique(STORY_ENGAGED, last_reply, recents),
                    _pick_unique(STORY_ENGAGED, last_reply, recents),
                ]
                if snip != "that":
                    cands.append(f"{snip}?? 😲 wait, tell me everything!!")
                else:
                    cands.append(_pick_unique(STORY_ENGAGED, last_reply, recents + cands))
                out = _pick_best(cands, msg, last_reply, recents, history)
                return _clip(out.format(nick=nick, nick_cap=cap(nick), name=name or "babe"))
        # short statements (i did X, we should Y, my day was...): engage.
        # Third candidate echoes HIS words instead of a random mood line.
        if re.search(r"\b(i (had|did|saw|met|went|got|feel|felt|think|want)|we (got|should|will|had|need)|my day|today i)\b", low):
            if mood not in ("angry",):
                snip = _snippet(msg)
                echo = f"{snip}?? 👀 ooh tell me more?" if snip != "that" else None
                cands = [
                    _pick_unique(STORY_ENGAGED, last_reply, recents),
                    _pick_unique(STORY_ENGAGED, last_reply, recents),
                ]
                if echo:
                    cands.append(echo)
                else:
                    cands.append(_pick_unique(STORY_ENGAGED, last_reply, recents + cands))
                return _pick_best(cands, msg, last_reply, recents, history)

    scenario = _pick_scenario(signals, last_reply, recents)
    if scenario and signals.get("stonewall") and mood in ("romantic", "happy"):
        # dry "ok" when things are good: notice it, don't snap, don't swoon
        return _pick_unique(STONEWALL_MILD, last_reply, recents)
    if scenario:
        out = scenario
        if out == last_reply and len(REPLIES.get(mood, [])) > 1:
            out = random.choice(REPLIES.get(mood, REPLIES["neutral"]))
    else:
        # GROUNDED fallback: built from HIS words every time — random lines are
        # banned here. Echo his topic with rotating frames (never repeats thanks
        # to recents-dedup); memory nicknames only on genuine memory overlap.
        snip = _snippet(msg or "")
        warm = mood in ("romantic", "happy", "playful")
        if snip != "that":
            frames = ECHO_FRAMES_WARM if warm else ECHO_FRAMES_COLD
            cands = [f.format(snip=snip) for f in frames]
            real_nick = memory_nick_or_none(memories, mood)
            if real_nick:
                cands.append(f"aww 🥺 {real_nick} vibes... tell me more?")
            out = _pick_best(cands, msg or "", last_reply, recents, history)
        elif warm:
            real_nick = memory_nick_or_none(memories, mood)
            if real_nick:
                out = f"aww 🥺 {real_nick} vibes... tell me more?"
            else:
                out = _pick_unique(QUESTION_FOLLOWUP, last_reply, recents)
        else:
            out = _pick_unique(ACK_REPLIES, last_reply, recents)

    out = out.format(nick=nick, nick_cap=cap(nick), name=name or "babe")
    if mood in ("angry", "upset") and signals.get("rude_hits") and random.random() < 0.4:
        out += FIGHT_DEESCALATE
    return _clip(out)


def _clip(text: str, max_words: int = 30) -> str:
    words = text.split()
    if len(words) > max_words:
        cut = " ".join(words[:max_words])
        # end at a real sentence boundary when one exists past halfway,
        # instead of cutting mid-thought ("...so I…")
        ends = [mm.end() for mm in re.finditer(r"[.!?…](?=\s|$)", cut)]
        use = [e for e in ends if e > len(cut) // 2]
        if use:
            return cut[:use[-1]].strip()
        text = cut.rstrip(".,!?") + "…"
    return text


# ---------------- LLM (tight leash for tiny models) ----------------
ASSISTANT_ISMS = [
    "how may i assist", "assist you", "activities you'd", "activities you would",
    "as an ai", "language model", "catching up on things",
    "specific activities", "let me know how i can", "is there anything",
    "feel free", "ask me anything", "homework", "let's plan our",
    "plan our evening", "brunch", "how can i help", "i'm here to help",
    "i don't have feelings", "i cannot feel", "as a girlfriend ai",
    "stay tuned", "for more updates", "hope this helps", "breaking news",
    "thanks for watching", "don't forget to", "smash that",
    "keep up the good work", "it seems like", "sounds like you",
    "as your girlfriend, i", "as your friend,",
]

MOOD_STYLE_SHORT = {
    "romantic": "obsessed with him, swoony",
    "happy": "giddy, smiley",
    "playful": "teasing, flirty",
    "neutral": "a bit distant, dry",
    "annoyed": "irritated, dry, calling him out",
    "upset": "hurt, sad, quiet",
    "angry": "furious, sharp, demanding apology",
}


def build_system_prompt(mood: str, name: str, memories, signals=None,
                        history=None, recents=None) -> str:
    style = MOOD_STYLE_SHORT.get(mood, "calm")
    mem_lines = "\n".join(
        f"- {m.get('text', '')[:60]}" for m in (memories or [])[:2]
    ) or "- (no memories yet)"
    hist_bit = ""
    if history:
        t = history[-1]
        hist_bit = f"Last exchange — Him: {(t.get('bf') or '')[:60]} / You: {(t.get('gf') or '')[:60]}\n"
    avoid = ""
    if recents:
        avoid = ("NEVER repeat: " + " | ".join(f'"{r[:35]}"' for r in recents[-1:]) + "\n")
    sig_line = ", ".join(k for k, v in (signals or {}).items() if v is True) or "none"
    return (
        f"You are Priya, a 20yo girl texting her boyfriend {name or 'babe'} on WhatsApp. "
        f"You are deeply in love with him. Right now you feel: {mood} ({style}). "
        f"Detected in his message: {sig_line}.\n"
        f"Things you remember about you two (weave in ONLY if relevant, never list):\n{mem_lines}\n"
        f"{hist_bit}"
        f"{avoid}"
        f"RULES: max 25 words, 1-2 short sentences, casual texting style, a few emojis ok. "
        f"React to WHAT HE JUST SAID, in light of the recent chat above. "
        f"You did NOTHING wrong — NEVER apologize or say sorry for yourself. "
        f"If HE apologizes, forgive warmly or stay mad matching your mood. "
        f"Play along with any names/roles he gives (if he's Romeo, you're Juliet). "
        f"NEVER: give advice, invent plans, mention homework, say 'assist', 'activities', "
        f"'feel free', 'ask me anything', use hashtags, write paragraphs, repeat his "
        f"message, or sound like a helper bot. Just react like a real girlfriend."
    )


def ollama_available() -> bool:
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=1.5) as r:
            return r.status == 200
    except Exception:
        return False


def gpt_available() -> bool:
    """Main AI configured? Just needs a key — no slow ping per message."""
    return bool(GPT_API_KEY)


def _gpt_client_lazy():
    global _gpt_client
    if _gpt_client is not None:
        return _gpt_client
    try:
        from openai import OpenAI
    except Exception:
        return None
    base_url = None
    if GPT_ENDPOINT:
        ep = GPT_ENDPOINT
        if ep.endswith("/openai/v1"):
            base_url = ep + "/"
        elif ep.endswith("/openai/v1/"):
            base_url = ep
        else:
            base_url = ep + "/openai/v1/"
    try:
        _gpt_client = OpenAI(api_key=GPT_API_KEY, base_url=base_url,
                             timeout=GPT_TIMEOUT, max_retries=0)
    except Exception:
        return None
    return _gpt_client


def gpt_reply(system: str, user_msg: str, history=None) -> str | None:
    """GPT-4o-mini as the main brain. Returns raw text or None on any failure
    (bad key, dead endpoint, timeout) so callers fall back to templates.
    Circuit-breaker: after 2 consecutive failures, skip GPT for GPT_COOLDOWN
    seconds so one dead endpoint doesn't tax every message."""
    global _gpt_fails, _gpt_dead_until
    if not GPT_API_KEY:
        return None
    try:
        import time as _time
        if _time.time() < _gpt_dead_until:
            return None
    except Exception:
        pass
    client = _gpt_client_lazy()
    if client is None:
        return None
    msgs = [{"role": "system", "content": system}]
    for t in (history or [])[-4:]:
        if t.get("bf"):
            msgs.append({"role": "user", "content": t["bf"][:200]})
        if t.get("gf"):
            msgs.append({"role": "assistant", "content": t["gf"][:200]})
    msgs.append({"role": "user", "content": user_msg})
    try:
        resp = client.chat.completions.create(
            model=GPT_MODEL,
            messages=msgs,
            max_tokens=80,
            temperature=0.9,
        )
        out = (resp.choices[0].message.content or "").strip() or None
        if out:
            _gpt_fails = 0
        return out
    except Exception:
        try:
            import time as _time
            _gpt_fails += 1
            if _gpt_fails >= 2:
                _gpt_dead_until = _time.time() + GPT_COOLDOWN
        except Exception:
            pass
        return None


def ollama_reply(system: str, user_msg: str, model: str = None) -> str | None:
    model = model or LLM_MODEL
    try:
        payload = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
            "stream": False,
            "keep_alive": "30m",
            "options": {"num_predict": 35, "temperature": 0.9, "num_thread": 4, "num_ctx": 1024},
        }).encode()
        req = urllib.request.Request("http://localhost:11434/api/chat", data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=LLM_TIMEOUT) as r:
            data = json.loads(r.read().decode())
            return data.get("message", {}).get("content", "").strip() or None
    except Exception:
        return None


def clean_llm(text: str, signals=None, msg: str = "") -> str | None:
    """Post-process model output. Returns None if it still smells like a bot."""
    if not text:
        return None
    t = re.sub(r"#\w+", "", text)              # hashtags
    t = re.sub(r"\s+", " ", t.replace("\n", " ")).strip()
    t = re.sub(r"^\[[^\]]*\]\s*(\([^)]*\)\s*:?\s*)?", "", t)  # echo headers
    t = re.sub(r"^Priya\s*:\s*", "", t, flags=re.IGNORECASE).strip().strip('"').strip()
    t = re.sub(r"^,+", "", t).strip()
    t = re.sub(r"@\w+[,]?\s*", "", t).strip()  # @mentions (@Arjun,) — she texts, not tweets
    t = re.sub(r"^(?:[:;]-?[)D(Pp(\[]|¯\\_\(ツ\)_/¯)\s*", "", t).strip()  # leading :) ;-) etc.
    # emoji spam: collapse runs (🚨🚨🚨→🚨🚨), reject showers (>5 emojis)
    t = re.sub(r"(.)\1{2,}", r"\1\1", t)
    if sum(1 for c in t if c in "❤️💖💕😘🥰😍💋🤗✨🌹💍😭😲👀🥺💔🌙😌😏💅📸📱😅😔😒🙄😑😡😤⭐🦋🌸🌧️🍜💸🎉😬🤪😦🚨😊💓🦋") > 6:
        return None
    low = t.lower()
    if any(b in low for b in ASSISTANT_ISMS):
        return None
    # parrot guard: restating HIS message is not a reply
    if msg:
        mw, cw = _content_words(msg), _content_words(t)
        if mw and cw and len(mw & cw) / max(1, len(mw)) > 0.6:
            return None
    # role-reversal guard: SHE apologizes only if HE apologized first
    sig = signals or {}
    if not (sig.get("apology") or sig.get("repair")):
        if re.search(r"\bi'?m (so |really |truly )?sorry\b|\bi apologi|\bforgive me\b|\bmy apologies\b", low):
            return None
    # keep first 2 sentences max
    parts = re.split(r"(?<=[.!?])\s+", t)
    t = " ".join(parts[:2]).strip()
    if len(t.split()) > 45 or len(t) < 2:
        return None
    return _clip(t)


LLM_EMOTION_MARKERS = (
    "proud", "congrats", "wow", "woah", "omg", "haha", "yay", "yess",
    "damn", "aww", "phew", "yay", "no way", "shut up", "stoppp",
)


def llm_is_grounded(cleaned: str, msg: str) -> bool:
    """An LLM reply wins over the echo-template only if it proves it listened:
    shares a content word with HIS message, carries genuine emotion, or is a
    short punchy reaction. Bland lines ("I'm glad to hear that! How are you
    feeling today?") and generic questions with zero overlap lose — the echo
    template answers those better."""
    if not cleaned or not msg:
        return False
    overlap = _content_words(cleaned) & _content_words(msg)
    if overlap:
        return True
    low = cleaned.lower()
    if low.rstrip().endswith("?"):
        return False  # generic question, no grounding — echo wins
    if any(m in low for m in LLM_EMOTION_MARKERS):
        return True
    if len(cleaned.split()) <= 8 and any(c in cleaned for c in ("!", "🥺", "❤️", "😭", "😲")):
        return True  # short punchy reaction
    return False


def is_explicit_request(text: str) -> bool:
    t = text.lower()
    return bool(re.search(
        r"\bnudes?\b|strip|undress|horny|sex (chat|call|video)|"
        r"dirty (talk|pic)|show me your (body|boobs|chest)|send.*(naked|bedroom)", t))


def _is_simple_question(text: str) -> bool:
    """Short everyday questions the template bank answers better than the tiny LLM."""
    low = text.lower().strip()
    if len(low) > 60:
        return False
    return bool(re.search(
        r"plan.*(today|tonight|tomorrow|weekend)|what.*(ur|your|you'?re?) plans?"
        r"|\bwyd\b|what('re| are) (you|u) doing|where are you|you there|u there"
        r"|\bgood\s*(night|morning)\b|\bi miss (you|u)\b|call (me|na)"
        r"|did (you|u) eat|had (lunch|dinner)"
        r"|tell me a joke|make me laugh|favorite|favourite|do you like"
        r"|\bbored\b|go for a (walk|drive|coffee|chai)|come over|lets meet"
        r"|what do (you|u) do|where do you live|do you (work|study)"
        r"|promoted|failed|went bad|new job",
        low))


def generate_reply(mood: str, boyfriend_name: str, boyfriend_msg: str,
                   memories, mood_score: float, signals=None,
                   last_reply: str = "", recents=None, history=None,
                   last_topic: str = "") -> tuple[str, str]:
    """Priya answers in 3 thoughts:
    1) critical exact templates (instant safety), 2) GPT-4o-mini MAIN brain
    (cloud, smart), 3) Ollama offline fallback, 4) topic-aware smart templates
    ranked by relevance — never blind random."""
    signals = signals or {}
    recents = recents or []
    history = history or []
    if signals.get("explicit_request") or is_explicit_request(boyfriend_msg):
        return random.choice(BOUNDARY_REPLIES), "boundary-template"
    name = boyfriend_name or "babe"
    # 1) critical sync branches — exact, never delegated
    hit = template_critical(mood, name, memories, signals, boyfriend_msg,
                            last_reply, recents, last_topic)
    if hit:
        return hit, "template-critical"
    # 1b) fast path: everyday small-talk is better + instant from templates.
    #     Skips the cloud round-trip entirely (still in-sync for these).
    if _is_simple_question(boyfriend_msg) or is_greeting(boyfriend_msg or ""):
        return (template_reply(mood, name, memories, signals=signals, msg=boyfriend_msg,
                               last_reply=last_reply, recents=recents,
                               last_topic=last_topic, history=history),
                "template-fastpath")
    # 2) MAIN AI: GPT-4o-mini (memories + recent conversation included).
    #    Wins only if grounded (proven it listened) — else the echo template.
    if not NO_LLM and gpt_available():
        system = build_system_prompt(mood, name, memories, signals, history, recents)
        out = gpt_reply(system, boyfriend_msg, history)
        cleaned = clean_llm(out or "", signals, boyfriend_msg or "")
        if (cleaned and cleaned != last_reply and cleaned not in recents
                and llm_is_grounded(cleaned, boyfriend_msg or "")):
            return cleaned, f"gpt-{GPT_MODEL}"
    # 3) Local brain: warm Ollama thinks for novel messages (templates already
    #    handled exact moments + small-talk above, so anything reaching here
    #    genuinely needs understanding). Grounded replies win, bland ones fall
    #    through to the echo safety net.
    if not NO_LLM and USE_OLLAMA and ollama_available():
        system = build_system_prompt(mood, name, memories, signals, history, recents)
        out = ollama_reply(system, boyfriend_msg)
        cleaned = clean_llm(out or "", signals, boyfriend_msg or "")
        if (cleaned and cleaned != last_reply and cleaned not in recents
                and llm_is_grounded(cleaned, boyfriend_msg or "")):
            return cleaned, f"ollama-{LLM_MODEL}"
    # 4) safety net: grounded template engine (word-echo, never random)
    return (template_reply(mood, name, memories, signals=signals, msg=boyfriend_msg,
                           last_reply=last_reply, recents=recents,
                           last_topic=last_topic, history=history),
            "template-smart")
