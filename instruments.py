"""Validated clinical screening instruments with published cutoffs.

Sources (current standards):
- PHQ-9  (Kroenke/Spitzer 2001): 0-27; 5/10/15/20 band cutoffs
- GAD-7  (Spitzer 2006): 0-21; >=10 clinical; 5/10/15 bands
- ASRS v1.1 Part A (WHO/Harvard 2005): 6 items, 4+ shaded = screen positive
- AQ-10  (Allison 2012; cutoff review 2025): >=6 optimal (NICE's >=7 suboptimal)
- MDQ    (Hirschfeld 2000): 7+ + co-occurrence = bipolar spectrum screen positive
- PC-PTSD-5 (Prins 2016): >=3 = positive trauma screen
- IPIP-50 Big Five (Goldberg, public domain) + DSM-5-TR PID-5-BF trait-domain mapping
"""

import math

LIKERT4 = ["Not at all", "Several days", "More than half the days", "Nearly every day"]
FREQ5 = ["Never", "Rarely", "Sometimes", "Often", "Very Often"]
AQ_AGREE = ["Definitely agree", "Slightly agree", "Slightly disagree", "Definitely disagree"]
YN = ["Yes", "No"]

PHQ9 = {
    "id": "phq9", "title": "Mood & Depression", "instrument": "PHQ-9",
    "scale": LIKERT4, "max": 27, "cutoff": 10,
    "bands": [(0, 4, "Minimal", "ok"), (5, 9, "Mild", "info"),
              (10, 14, "Moderate", "flag"), (15, 19, "Moderately severe", "flag"),
              (20, 27, "Severe", "alarm")],
    "items": [
        "Little interest or pleasure in doing things",
        "Feeling down, depressed, or hopeless",
        "Trouble falling or staying asleep, or sleeping too much",
        "Feeling tired or having little energy",
        "Poor appetite or overeating",
        "Feeling bad about yourself — or that you are a failure or have let yourself or your family down",
        "Trouble concentrating on things, such as reading or watching television",
        "Moving or speaking so slowly that other people could have noticed — or being so fidgety or restless that you have been moving a lot more than usual",
        "Thoughts that you would be better off dead, or of hurting yourself in some way",
    ],
}

GAD7 = {
    "id": "gad7", "title": "Anxiety", "instrument": "GAD-7",
    "scale": LIKERT4, "max": 21, "cutoff": 10,
    "bands": [(0, 4, "Minimal", "ok"), (5, 9, "Mild", "info"),
              (10, 14, "Moderate", "flag"), (15, 21, "Severe", "alarm")],
    "items": [
        "Feeling nervous, anxious, or on edge",
        "Not being able to stop or control worrying",
        "Worrying too much about different things",
        "Trouble relaxing",
        "Being so restless that it's hard to sit still",
        "Becoming easily annoyed or irritable",
        "Feeling afraid, as if something awful might happen",
    ],
}

# ASRS v1.1 Part A: shaded-box scoring — items 0,1,3 score positive at 2+
# (Sometimes), items 2,4,5 at 3+ (Often). 4+ positives = screen positive.
ASRS = {
    "id": "asrs", "title": "Attention & Hyperactivity", "instrument": "ASRS v1.1 Part A",
    "scale": FREQ5, "max": 24, "cutoff": None,
    "items": [
        {"t": "How often do you have trouble wrapping up the final details of a project, once the challenging parts have been done?", "shade": 2},
        {"t": "How often do you have difficulty getting things in order when you have to do a task that requires organization?", "shade": 2},
        {"t": "How often do you have problems remembering appointments or obligations?", "shade": 3},
        {"t": "When you have a task that requires a lot of thought, how often do you avoid or delay getting started?", "shade": 2},
        {"t": "How often do you fidget or squirm with your hands or feet when you have to sit down for a long time?", "shade": 3},
        {"t": "How often do you feel overly active and compelled to do things, like you were driven by a motor?", "shade": 3},
    ],
}

# AQ-10: items where "agree" scores 1, items where "disagree" scores 1.
AQ10 = {
    "id": "aq10", "title": "Autism Spectrum Traits", "instrument": "AQ-10",
    "scale": AQ_AGREE, "max": 10, "cutoff": 6,
    "agree_positive": [True, True, False, True, True, False, True, False, True, False],
    "items": [
        "I often notice small sounds when others do not",
        "I usually concentrate more on the whole picture, rather than the small details",
        "I find it easy to do more than one thing at once",
        "If there is an interruption, I can switch back to what I was doing very quickly",
        "I frequently get so strongly absorbed in one thing that I lose sight of other things",
        "I know how to tell if someone listening to me is getting bored",
        "When I'm reading a story I find it difficult to work out the characters' intentions",
        "I like to collect information about categories of things (e.g. types of car, types of bird, types of train, types of plant)",
        "I find it easy to work out what someone is thinking or feeling just by looking at their face",
        "I find it difficult to work out people's intentions",
    ],
}

MDQ = {
    "id": "mdq", "title": "Mood Spectrum (Bipolar Screen)", "instrument": "MDQ",
    "scale": YN, "max": 13, "cutoff": 7,
    "items": [
        "There was a period of time when you felt so good or so hyper that other people thought you were not your normal self, or you were so hyper that you got into trouble?",
        "You were so irritable that you shouted at people or started fights or arguments?",
        "You felt much more self-confident than usual?",
        "You got much less sleep than usual and found you didn't really miss it?",
        "You were much more talkative or spoke much faster than usual?",
        "Thoughts raced through your head or couldn't slow your mind down?",
        "You were so easily distracted by things around you that you had trouble concentrating or staying on track?",
        "You had much more energy than usual?",
        "You were much more active or did many more things than usual?",
        "You were much more social or outgoing than usual — for example, you telephoned friends in the middle of the night?",
        "You were much more interested in sex than usual?",
        "You did things that were unusual for you or that other people might have thought were excessive, foolish, or risky?",
        "Spending money got you or your family into trouble?",
    ],
}

PCPTSD5 = {
    "id": "pcptsd5", "title": "Trauma & Stress", "instrument": "PC-PTSD-5",
    "scale": YN, "max": 5, "cutoff": 3,
    "items": [
        "Have you ever had any experience that was so frightening, horrible, or upsetting that, in the past month, you: had nightmares about it or thought about it when you did not want to?",
        "…tried hard not to think about it or went out of your way to avoid situations that reminded you of it?",
        "…were constantly on guard, watchful, or easily startled?",
        "…felt numb or detached from people, activities, or your surroundings?",
        "…felt guilty or unable to stop blaming yourself or others about it?",
    ],
}

# IPIP-50 Big Five — 10 items per domain, +1 keyed / -1 reverse keyed.
BIG5 = {
    "id": "big5", "title": "Personality Profile", "instrument": "IPIP-50 (Big Five)",
    "scale": ["Strongly disagree", "Disagree", "Neutral", "Agree", "Strongly agree"],
    "domains": {
        "Extraversion": [
            ("I am the life of the party", 1), ("I don't mind being the center of attention", 1),
            ("I feel comfortable around people", 1), ("I start conversations", 1),
            ("I talk to a lot of different people at parties", 1),
            ("I don't talk a lot", -1), ("I think a lot before I speak or act", -1),
            ("I have little to say", -1), ("I keep in the background", -1),
            ("I am quiet around strangers", -1),
        ],
        "Agreeableness": [
            ("I am interested in people", 1), ("I sympathize with others' feelings", 1),
            ("I have a soft heart", 1), ("I take time out for others", 1),
            ("I feel others' emotions", 1), ("I make people feel at ease", 1),
            ("I am not really interested in others", -1), ("I insult people", -1),
            ("I am not interested in other people's problems", -1),
            ("I feel little concern for others", -1),
        ],
        "Conscientiousness": [
            ("I am always prepared", 1), ("I pay attention to details", 1),
            ("I get chores done right away", 1), ("I like order", 1),
            ("I follow a schedule", 1), ("I leave my belongings around", -1),
            ("I often forget to put things back in their proper place", -1),
            ("I shirk my duties", -1), ("I make a mess of things", -1),
            ("I often forget to return things", -1),
        ],
        "Negative Emotionality": [
            ("I am relaxed most of the time", -1), ("I seldom feel blue", -1),
            ("I get stressed out easily", 1), ("I worry about things", 1),
            ("I am easily disturbed", 1), ("I get upset easily", 1),
            ("I change my mood a lot", 1), ("I have frequent mood swings", 1),
            ("I get irritated easily", 1), ("I often feel blue", 1),
        ],
        "Openness to Experience": [
            ("I have a rich vocabulary", 1), ("I have a vivid imagination", 1),
            ("I have excellent ideas", 1), ("I am quick to understand things", 1),
            ("I use difficult words", 1), ("I spend time reflecting on things", 1),
            ("I am full of ideas", 1), ("I have difficulty understanding abstract ideas", -1),
            ("I am not interested in abstract ideas", -1),
            ("I do not have a good imagination", -1),
        ],
    },
}

# DSM-5-TR PID-5-BF style trait domains (25 items, 5 per domain, 0-3 each).
PID5 = {
    "id": "pid5", "title": "Personality Trait Domains", "instrument": "DSM-5-TR trait model (PID-5-BF style)",
    "scale": ["Very false or often false", "Sometimes or somewhat false",
              "Sometimes or somewhat true", "Very true or often true"],
    "domains": {
        "Negative Affect": [
            "I get emotional easily, often for little reason",
            "Little things bother me more than they should",
            "I often feel tense, anxious, or on edge",
            "My mood shifts can be very strong",
            "I worry about bad things happening far in the future",
        ],
        "Detachment": [
            "I prefer to keep relationships shallow and distant",
            "I rarely feel strong emotions connected to other people",
            "Social gatherings drain me even when I enjoy the people",
            "I don't feel much interest in what's happening around me",
            "I avoid romantic or close relationships",
        ],
        "Antagonism": [
            "I use people to get what I want",
            "I feel little remorse when I hurt someone's feelings",
            "I believe most people would take advantage of you if you let them",
            "I like being the one who makes the rules",
            "I often dominate conversations",
        ],
        "Disinhibition": [
            "I act on impulse without planning",
            "I have trouble sticking to boring but necessary tasks",
            "I often do things for thrills even when they are risky",
            "Deadlines and rules feel restrictive to me",
            "I spend or commit without thinking of consequences",
        ],
        "Psychoticism": [
            "I have had experiences of things feeling unreal or dreamlike",
            "I notice connections between events that others find strange",
            "My thoughts sometimes race in unusual directions others don't follow",
            "I have unusual perceptual experiences (e.g. hearing things faintly)",
            "I speak in an odd or tangential way that confuses people",
        ],
    },
}

# Linear progression order — broad neurodevelopmental/mood first, then
# trauma, then deep personality profiling.
SCREEN_SECTIONS = [PHQ9, GAD7, ASRS, AQ10, MDQ, PCPTSD5, BIG5, PID5]

# ---- Quick Map (original 17-parameter self-assessment) --------------------
QUESTIONS = {
    "Executive Function": {
        "q": "How hard is it to plan, start, and finish multi-step tasks?",
        "low": "Tasks flow naturally with minimal friction",
        "mid": "Occasional stalls that you can push through",
        "high": "Starting and sequencing tasks feels like pushing a boulder",
    },
    "Sensory Sensitivity": {
        "q": "How strongly do sounds, lights, textures, or crowds affect you?",
        "low": "Background noise rarely registers",
        "mid": "Certain environments become draining or irritating",
        "high": "Everyday sensations can be overwhelming or painful",
    },
    "Social Energy": {
        "q": "How much energy does socializing cost you?",
        "low": "Socializing recharges you",
        "mid": "Enjoyable but needs recovery time afterwards",
        "high": "Even short interactions feel exhausting",
    },
    "Hyperfocus": {
        "q": "How deeply can you lock into something that interests you?",
        "low": "Attention stays flexible and easily redirected",
        "mid": "Strong focus in bursts, on your own terms",
        "high": "Hours vanish; interrupting feels physically jarring",
    },
    "Task Switching": {
        "q": "How easy is it to jump between different activities?",
        "low": "Switching contexts is smooth and cheap",
        "mid": "A brief transition ritual is needed",
        "high": "Switching tasks mid-flow feels genuinely distressing",
    },
    "Verbal Communication": {
        "q": "How natural does spoken conversation feel?",
        "low": "Words arrive easily in most settings",
        "mid": "Fluent in comfort zones, harder elsewhere",
        "high": "Finding words often takes deliberate effort",
    },
    "Reading Between the Lines": {
        "q": "How easily do you read unspoken cues — tone, body language, subtext?",
        "low": "Unspoken cues are usually clear",
        "mid": "You catch most cues but miss subtle ones",
        "high": "Implicit meanings often need explicit translation",
    },
    "Routine Dependence": {
        "q": "How much do familiar routines and predictability matter?",
        "low": "Spontaneity feels easy and fun",
        "mid": "Prefer plans but adapt when needed",
        "high": "Unexpected changes can derail the whole day",
    },
    "Special Interests": {
        "q": "How intense and absorbing are your personal interests?",
        "low": "Hobbies stay casual and varied",
        "mid": "Deep dives that come and go in phases",
        "high": "Core interests are a central, defining part of life",
    },
    "Pattern Recognition": {
        "q": "How naturally do you spot systems, patterns, and details others miss?",
        "low": "Big picture over details",
        "mid": "Notice structures in familiar domains",
        "high": "Details and patterns jump out automatically, everywhere",
    },
    "Emotional Regulation": {
        "q": "How manageable are your emotional reactions in the moment?",
        "low": "Feelings rise and settle smoothly",
        "mid": "Occasional waves that need conscious handling",
        "high": "Emotions can hit hard and linger or overflow",
    },
    "Rejection Sensitivity": {
        "q": "How strongly does criticism or perceived rejection land?",
        "low": "Feedback rolls off easily",
        "mid": "Stings, but recovers within the day",
        "high": "Even small perceived slights can feel devastating",
    },
    "Self-Regulation Movements": {
        "q": "How much do repetitive movements or sounds (stimming) help you regulate?",
        "low": "Rarely needed or noticed",
        "mid": "Helpful in stressful moments",
        "high": "An essential, constant part of self-regulation",
    },
    "Sleep Rhythm": {
        "q": "How stable are your sleep and energy cycles?",
        "low": "Predictable schedule and steady energy",
        "mid": "Drifts with routine and stress",
        "high": "Sleep is erratic, reversed, or hard to initiate",
    },
    "Masking Effort": {
        "q": "How much energy goes into appearing 'typical' around others?",
        "low": "You are essentially the same everywhere",
        "mid": "Some conscious adjustment in certain company",
        "high": "Constant performance that leaves you drained",
    },
    "Time Perception": {
        "q": "How reliable is your internal sense of time?",
        "low": "You run on an accurate internal clock",
        "mid": "Time blurs occasionally",
        "high": "Time is either 'now' or 'not now' — estimation fails often",
    },
    "Sensory Seeking": {
        "q": "How much do you crave intense input — movement, pressure, sound, spice, speed?",
        "low": "Calm and low-stimulation feels best",
        "mid": "Enjoy intensity in chosen doses",
        "high": "Actively seek strong sensations to feel regulated",
    },
}


def classify_profile(scores):
    avg = sum(scores) / len(scores)
    variance = sum((s - avg) ** 2 for s in scores) / len(scores)
    sd = math.sqrt(variance)
    if sd >= 2.0:
        return ("The Spiky Profile",
                "Your scores vary dramatically across parameters. You have "
                "pronounced peaks — areas of extraordinary intensity — alongside "
                "deep valleys. This uneven 'spikiness' is a hallmark of "
                "neurodivergent wiring, bringing both remarkable strengths and "
                "real friction points.")
    if avg >= 5.5:
        return ("The High-Intensity Mind",
                "Nearly every parameter runs hot. You experience the world at "
                "high gain — intensely, vividly, and sometimes overwhelmingly. "
                "Structure, recovery time, and self-advocacy are your key tools.")
    if avg <= 2.5 and sd < 1.2:
        return ("The Steady Baseline",
                "Your responses cluster close to the standard baseline. Your "
                "wiring is relatively typical for the current population average "
                "— which, like every profile, is simply one variation of human.")
    return ("The Balanced Explorer",
            "Your profile shows moderate variation with no extreme peaks. You "
            "move between worlds comfortably, though certain parameters still "
            "cost you more energy than others.")



IQ_DOMAINS = [
    ("Gf", "Fluid Reasoning", "Novel problem solving — the core of g"),
    ("Gc", "Verbal Comprehension", "Crystallized knowledge and language"),
    ("Gwm", "Working Memory", "Holding and manipulating information"),
    ("Gv", "Visual-Spatial", "Mental imagery and rotation"),
    ("Gq", "Quantitative Reasoning", "Numerical relations"),
]


def score_instrument(section, form):
    """Returns dict with score, band, flag for a completed section."""
    sid = section["id"]
    if sid == "asrs":
        positives = 0
        for i, item in enumerate(section["items"]):
            v = int(form.get(f"{sid}_{i}", 0) or 0)
            if v >= item["shade"]:
                positives += 1
        flag = positives >= 4
        return {"score": positives, "max": 6,
                "band": "Screen positive" if flag else "Screen negative",
                "flag": flag,
                "note": "4+ items in the shaded range indicate symptoms highly "
                        "consistent with adult ADHD; further assessment is warranted."}
    if sid == "aq10":
        score = 0
        for i, item in enumerate(section["items"]):
            v = int(form.get(f"{sid}_{i}", 1) or 1)
            agrees = v <= 1
            if agrees == section["agree_positive"][i]:
                score += 1
        flag = score >= section["cutoff"]
        return {"score": score, "max": 10,
                "band": "Screen positive" if flag else "Screen negative",
                "flag": flag,
                "note": "Scores of 6+ on the AQ-10 (optimal cutoff, 2025 review) "
                        "suggest further autism assessment may be useful."}
    if sid in ("mdq", "pcptsd5"):
        score = sum(1 for i in range(len(section["items"]))
                    if form.get(f"{sid}_{i}") == "Yes")
        flag = score >= section["cutoff"]
        return {"score": score, "max": section["max"],
                "band": "Screen positive" if flag else "Screen negative",
                "flag": flag,
                "note": ("7+ lifetime episodes with co-occurrence suggests a "
                         "bipolar spectrum review." if sid == "mdq" else
                         "3+ symptoms in the past month suggest a trauma-related review.")}
    if sid == "big5":
        result = {}
        idx = 0
        for dom, items in section["domains"].items():
            total = 0
            for text, key in items:
                v = int(form.get(f"big5_{idx}", 2) or 2)
                total += (v + 1) * key
                idx += 1
            result[dom] = total  # 10..50
        return {"domains": result, "score": sum(result.values()) // 5,
                "max": 50, "band": "Profile", "flag": False,
                "note": "Higher scores mean more of the trait; Big Five traits "
                        "are dimensions, not disorders."}
    if sid == "pid5":
        result = {}
        idx = 0
        for dom, items in section["domains"].items():
            total = 0
            for text in items:
                total += int(form.get(f"pid5_{idx}", 0) or 0)
                idx += 1
            result[dom] = total  # 0..15
        flagged = [d for d, v in result.items() if v >= 9]
        return {"domains": result, "score": sum(result.values()),
                "max": 75, "band": "Elevated: " + ", ".join(flagged) if flagged else "Within range",
                "flag": bool(flagged),
                "note": "Domains averaging 2+/item (9+ here) may indicate a "
                        "clinically significant personality trait domain."}
    # PHQ9 / GAD7 style
    score = sum(int(form.get(f"{sid}_{i}", 0) or 0)
                for i in range(len(section["items"])))
    band, level = "Minimal", "ok"
    for lo, hi, name, lv in section["bands"]:
        if lo <= score <= hi:
            band, level = name, lv
    result = {"score": score, "max": section["max"], "band": band,
              "flag": score >= section["cutoff"], "level": level,
              "note": f"Clinical threshold is {section['cutoff']}+ on the "
                      f"{section['instrument']}."}
    if sid == "phq9":
        # Item 9 (index 8) is the self-harm/thoughts-of-death item — kept for
        # compassionate support routing, never stored long-term.
        result["item9"] = int(form.get("phq9_8", 0) or 0)
    return result
