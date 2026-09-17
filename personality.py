"""Big Five (Five-Factor Model) personality instrument for NEURO-SURVEY.

Items: Goldberg's IPIP Big-Five 50-item public-domain markers
(International Personality Item Pool, ipip.ori.org; Goldberg, 1992,
"An alternative 'description of personality': The Big-Five factor
structure", Journal of Personality and Social Psychology, 59, 1216-1229).
Response scale: IPIP standard 5-point accuracy Likert.
Scoring: reverse-keyed items inverted (6 - x); domain score = mean of its
10 items rescaled to 20-100. Bands are descriptive (approx. +/-0.5 SD
around the normative midpoint 50) as commonly reported for IPIP scales.

This module adds no dependencies and mirrors iq_eq.py conventions.
"""

SCALE = ["Very Inaccurate", "Moderately Inaccurate",
         "Neither Accurate nor Inaccurate", "Moderately Accurate", "Very Accurate"]

DOMAINS = ["Openness", "Conscientiousness", "Extraversion",
           "Agreeableness", "Emotional Stability"]

CITATION = ("IPIP Big-Five 50-item markers — Goldberg (1992), International "
            "Personality Item Pool (public domain, ipip.ori.org)")

# (item_text, domain, reversed?)  R = negatively keyed on its domain.
ITEMS = [
    # Openness (10)
    ("I have a rich vocabulary.", "Openness", False),
    ("I have a vivid imagination.", "Openness", False),
    ("I have excellent ideas.", "Openness", False),
    ("I am quick to understand things.", "Openness", False),
    ("I use difficult words.", "Openness", False),
    ("I spend time reflecting on things.", "Openness", False),
    ("I have difficulty understanding abstract ideas.", "Openness", True),
    ("I am not interested in abstract ideas.", "Openness", True),
    ("I do not have a good imagination.", "Openness", True),
    ("I avoid philosophical discussions.", "Openness", True),
    # Conscientiousness (10)
    ("I am always prepared.", "Conscientiousness", False),
    ("I pay attention to details.", "Conscientiousness", False),
    ("I get chores done right away.", "Conscientiousness", False),
    ("I like order.", "Conscientiousness", False),
    ("I follow a schedule.", "Conscientiousness", False),
    ("I leave my belongings around.", "Conscientiousness", True),
    ("I often forget to put things back in their proper place.", "Conscientiousness", True),
    ("I shirk my duties.", "Conscientiousness", True),
    ("I make a mess of things.", "Conscientiousness", True),
    ("I often forget to do things.", "Conscientiousness", True),
    # Extraversion (10)
    ("I am the life of the party.", "Extraversion", False),
    ("I feel comfortable around people.", "Extraversion", False),
    ("I start conversations.", "Extraversion", False),
    ("I talk to a lot of different people at parties.", "Extraversion", False),
    ("I don't mind being the center of attention.", "Extraversion", False),
    ("I don't talk a lot.", "Extraversion", True),
    ("I keep in the background.", "Extraversion", True),
    ("I have little to say.", "Extraversion", True),
    ("I don't like to draw attention to myself.", "Extraversion", True),
    ("I am quiet around strangers.", "Extraversion", True),
    # Agreeableness (10)
    ("I am interested in people.", "Agreeableness", False),
    ("I sympathize with others' feelings.", "Agreeableness", False),
    ("I have a soft heart.", "Agreeableness", False),
    ("I take time out for others.", "Agreeableness", False),
    ("I make people feel at ease.", "Agreeableness", False),
    ("I feel little concern for others.", "Agreeableness", True),
    ("I insult people.", "Agreeableness", True),
    ("I am not really interested in others.", "Agreeableness", True),
    ("I am not interested in other people's problems.", "Agreeableness", True),
    ("I am indifferent to the feelings of others.", "Agreeableness", True),
    # Neuroticism -> reported as Emotional Stability (10)
    ("I get stressed out easily.", "Emotional Stability", True),
    ("I worry about things.", "Emotional Stability", True),
    ("I am easily disturbed.", "Emotional Stability", True),
    ("I get upset easily.", "Emotional Stability", True),
    ("I change my mood a lot.", "Emotional Stability", True),
    ("I have frequent mood swings.", "Emotional Stability", True),
    ("I get irritated easily.", "Emotional Stability", True),
    ("I often feel blue.", "Emotional Stability", True),
    ("I am relaxed most of the time.", "Emotional Stability", False),
    ("I seldom feel blue.", "Emotional Stability", False),
]

INTERPRETATION = {
    "Openness": {
        "Low": ("Prefers routine and the familiar; practical and focused on "
                "concrete facts rather than abstraction."),
        "Average": ("Balances practicality with curiosity — open to new ideas "
                    "when they prove useful."),
        "High": ("Imaginative, curious, and drawn to art, ideas, novelty and "
                 "abstract thinking."),
    },
    "Conscientiousness": {
        "Low": ("More spontaneous and flexible; may struggle with organisation "
                "and follow-through."),
        "Average": ("Reliably dependable while retaining flexibility."),
        "High": ("Organised, disciplined and dependable; strong planners who "
                 "finish what they start."),
    },
    "Extraversion": {
        "Low": ("Introverted — energised by solitude; prefers small groups "
                "and quiet reflection."),
        "Average": ("Ambiverted — comfortable both socialising and alone."),
        "High": ("Outgoing, energetic and socially confident; seeks and enjoys "
                 "the company of others."),
    },
    "Agreeableness": {
        "Low": ("Direct, competitive and sceptical; prioritises candour over "
                "harmony."),
        "Average": ("Cooperative when it matters while able to hold a firm line."),
        "High": ("Warm, trusting and empathetic; values harmony and helps "
                 "readily."),
    },
    "Emotional Stability": {
        "Low": ("Emotionally reactive — more prone to stress, worry and mood "
                "swings."),
        "Average": ("Generally calm with normal emotional ups and downs."),
        "High": ("Calm, resilient and even-tempered under pressure."),
    },
}


def band(score):
    if score < 43:
        return "Low"
    if score <= 57:
        return "Average"
    return "High"


def score(answers):
    """answers: list of ints 1-5 aligned with ITEMS order.
    Returns {domain: {"score":20-100,"band":str}} plus raw neuroticism."""
    per = {d: [] for d in DOMAINS}
    for i, val in enumerate(answers):
        text, dom, rev = ITEMS[i]
        try:
            v = float(val)
        except (TypeError, ValueError):
            continue
        if v < 1 or v > 5:
            continue
        per[dom].append((6.0 - v) if rev else v)
    out = {}
    for d in DOMAINS:
        vals = per[d]
        mean = sum(vals) / len(vals) if vals else 3.0
        s = round(mean * 20.0)
        out[d] = {"score": max(20, min(100, s)), "band": band(s)}
    return out


def profile_label(scores):
    """Two-factor headline label, FFM-style shorthand."""
    hi = [d for d in DOMAINS if scores[d]["band"] == "High"]
    lo = [d for d in DOMAINS if scores[d]["band"] == "Low"]
    if len(hi) >= 3:
        return "Resilient & engaged profile"
    if "Conscientiousness" in hi and "Emotional Stability" in hi:
        return "Steady achiever profile"
    if "Extraversion" in hi and "Openness" in hi:
        return "Curious explorer profile"
    if "Extraversion" in lo and "Openness" in hi:
        return "Reflective thinker profile"
    if len(lo) >= 3:
        return "Currently strained profile"
    return "Balanced middle profile"


def validate_complete(answers):
    return len([a for a in answers if a]) == len(ITEMS)
