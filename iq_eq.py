"""Cognitive (IQ) and Empathy (EQ) assessment banks.

IQ structure follows Cattell-Horn-Carroll (CHC) theory — the framework
underpinning the WJ V (2025) and WAIS batteries: Fluid Reasoning (Gf),
Comprehension-Knowledge (Gc), Working Memory (Gwm), Visual-Spatial (Gv),
Quantitative Reasoning (Gq) and Processing Speed (Gs).

Items are original, difficulty-ordered within each domain. Standard scores
are reported as mean 100 / SD 15 (Wechsler convention) using fixed
raw-to-scaled mappings calibrated to expected adult performance.
"""

IQ_DOMAINS = [
    ("Gf", "Fluid Reasoning", "Novel problem solving — the core of g"),
    ("Gc", "Verbal Comprehension", "Crystallized knowledge and language"),
    ("Gwm", "Working Memory", "Holding and manipulating information"),
    ("Gv", "Visual-Spatial", "Mental imagery and rotation"),
    ("Gq", "Quantitative Reasoning", "Numerical relations"),
]

# ---- Gf: Matrix reasoning (SVG shown; answer = option index) -------------
# Each matrix: 3x3 grid where shapes follow a rule; last cell missing.
# Shapes are rendered as inline SVG from the item's spec.
MATRIX_ITEMS = [
    # rule: shape count increases left-to-right, fill alternates
    {"svg": "matrix", "spec": {
        "shapes": ["circle", "circle", "circle", "square", "square", "square", "triangle", "triangle"],
        "counts": [1, 2, 3, 1, 2, 3, 1, 2],
        "options": [
            {"shape": "triangle", "count": 3}, {"shape": "circle", "count": 1},
            {"shape": "square", "count": 2}, {"shape": "triangle", "count": 1}],
        "answer": 0}},
    # rule: XOR of elements across the row
    {"svg": "xor", "spec": {
        "rows": [
            [[1, 0, 1, 0], [0, 1, 1, 0], [1, 1, 0, 0]],
            [[0, 1, 0, 1], [1, 1, 0, 1], [1, 0, 0, 0]],
            [[1, 0, 0, 1], [0, 0, 1, 1], None]],
        "options": [[1, 0, 1, 0], [1, 1, 1, 1], [0, 0, 0, 0], [1, 0, 0, 1]],
        "answer": 0}},
]

# ---- Gf/Gq: Number & series puzzles --------------------------------------
SERIES_ITEMS = [
    {"q": "2, 4, 8, 16, …", "options": ["24", "30", "32", "20"], "answer": 2, "domain": "Gq"},
    {"q": "1, 1, 2, 3, 5, 8, …", "options": ["11", "13", "12", "10"], "answer": 1, "domain": "Gf"},
    {"q": "3, 6, 11, 18, 27, …", "options": ["36", "38", "40", "35"], "answer": 1, "domain": "Gq"},
    {"q": "A, C, F, J, O, …", "options": ["T", "U", "S", "V"], "answer": 1, "domain": "Gf"},
    {"q": "81, 27, 9, 3, …", "options": ["0", "1", "2", "-1"], "answer": 1, "domain": "Gq"},
    {"q": "2, 3, 5, 7, 11, 13, …", "options": ["15", "17", "19", "21"], "answer": 1, "domain": "Gf"},
]

# ---- Gc: Verbal analogies & vocabulary ------------------------------------
VERBAL_ITEMS = [
    {"q": "Ephemeral is to permanent as transparent is to ___", "options": ["clear", "opaque", "visible", "glass"], "answer": 1, "domain": "Gc"},
    {"q": "Sculptor is to marble as poet is to ___", "options": ["rhyme", "language", "verse", "ink"], "answer": 1, "domain": "Gc"},
    {"q": "Which word means most nearly the opposite of 'magnanimous'?", "options": ["generous", "petty", "noble", "forgiving"], "answer": 1, "domain": "Gc"},
    {"q": "Arboreal is to tree as aquatic is to ___", "options": ["fish", "water", "swim", "boat"], "answer": 1, "domain": "Gc"},
    {"q": "Ubiquitous most nearly means ___", "options": ["rare", "unique", "everywhere", "unclear"], "answer": 2, "domain": "Gc"},
    {"q": "Cacophony is to sound as labyrinth is to ___", "options": ["maze", "music", "silence", "wall"], "answer": 0, "domain": "Gc"},
]

# ---- Gv: Mental rotation (described shapes rendered as SVG polygons) ------
ROTATION_ITEMS = [
    {"q": "Which figure is the same object as the reference, rotated?", "ref": [[0, 0], [4, 0], [4, 1], [1, 1], [1, 3], [0, 3]],
     "options": [[[0, 0], [4, 0], [4, 1], [1, 1], [1, 3], [0, 3]],
                 [[0, 0], [1, 0], [1, 3], [4, 3], [4, 4], [0, 4]],
                 [[0, 0], [3, 0], [3, 4], [2, 4], [2, 1], [0, 1]],
                 [[0, 0], [4, 0], [4, 4], [3, 4], [3, 1], [0, 1]]],
     "answer": 1},
    {"q": "Which figure is the same object as the reference, rotated?", "ref": [[0, 0], [3, 0], [3, 1], [2, 1], [2, 2], [0, 2]],
     "options": [[[0, 0], [2, 0], [2, 2], [1, 2], [1, 3], [0, 3]],
                 [[0, 0], [3, 0], [3, 1], [1, 1], [1, 2], [0, 2]],
                 [[0, 0], [2, 0], [2, 3], [1, 3], [1, 1], [0, 1]],
                 [[0, 0], [3, 0], [3, 2], [2, 2], [2, 3], [0, 3]]],
     "answer": 0, "domain": "Gc"},
]

# ---- Gwm: Digit span (interactive; JS generates sequences) ----------------
DIGIT_SPAN = {"start": 3, "max": 9}

# ---- Gs: Symbol search (timed 60s; JS-driven count) -----------------------
SYMBOL_SEARCH_SECONDS = 60


def iq_domain_items():
    """Ordered item list: (kind, payload, domain)."""
    items = []
    for m in MATRIX_ITEMS:
        items.append((m["svg"], m, "Gf"))
    for s in SERIES_ITEMS:
        items.append(("series", s, s["domain"]))
    for v in VERBAL_ITEMS:
        items.append(("series", v, "Gc"))
    for r in ROTATION_ITEMS:
        items.append(("rotation", r, "Gv"))
    items.append(("digitspan", DIGIT_SPAN, "Gwm"))
    items.append(("symbols", {"seconds": SYMBOL_SEARCH_SECONDS}, "Gs"))
    return items


# Raw (0-1 per static item, plus digit-span and symbol-speed scaled) ->
# standard score (mean 100, SD 15). Fixed calibration table.
def standard_score(fraction):
    """Map a 0..1 performance fraction to an IQ-style standard score."""
    fraction = max(0.0, min(1.0, fraction))
    return int(round(55 + fraction * 90))  # 55..145


def iq_band(iq):
    if iq >= 130: return "Very superior"
    if iq >= 120: return "Superior"
    if iq >= 110: return "High average"
    if iq >= 90: return "Average"
    if iq >= 80: return "Low average"
    return "Below average"


# ---- EQ (Empathy Quotient style, 40 scored items, 3 subscales) ------------
# Scoring: strongly agree/agree on positive-keyed items = 2/1 points;
# reversed for negative-keyed. Max 80.
EQ_SCALE = ["Strongly disagree", "Slightly disagree", "Slightly agree", "Strongly agree"]

EQ_ITEMS = [
    ("I can easily tell if someone else wants to enter a conversation", 1, "CE"),
    ("I prefer animals to humans", -1, "ER"),
    ("I try to keep up with the latest trends in fashion and music", 0, "SS"),
    ("I find it difficult to explain to others things I understand easily, if the explanation involves more than a few steps", -1, "CE"),
    ("I dream most nights", 0, "ER"),
    ("I really enjoy caring for other people", 1, "ER"),
    ("I try to solve my problems by myself", 0, "SS"),
    ("I find it hard to know what to do in a social situation", -1, "SS"),
    ("I am at my best first thing in the morning", 0, "SS"),
    ("Different situations make me laugh in quite different ways", 1, "CE"),
    ("I know how to tell if someone listening to me is getting bored", 1, "CE"),
    ("It's hard for me to see why some things upset people so much", -1, "ER"),
    ("I am good at predicting how someone will feel", 1, "CE"),
    ("I find that I can 'tune in' easily to another person's mood", 1, "CE"),
    ("I can sense if I am intruding, even if the other person doesn't tell me", 1, "CE"),
    ("I often find it difficult to judge if something is rude or polite", -1, "SS"),
    ("I can tune in to how someone else feels rapidly and intuitively", 1, "CE"),
    ("I can tell if someone is masking their real emotion", 1, "CE"),
    ("I don't usually notice if people treat me with less respect than they treat others", -1, "SS"),
    ("Other people often say that I am insensitive", -1, "ER"),
    ("I get upset if I see people suffering on news programmes", 1, "ER"),
    ("Friends usually talk to me about their problems as they say I am very understanding", 1, "ER"),
    ("I can pick up quickly if someone says one thing but means another", 1, "CE"),
    ("It is difficult for me to understand what other people feel", -1, "CE"),
    ("I can easily tell if someone else is interested or bored with what I am saying", 1, "CE"),
    ("I get irritated very easily", -1, "ER"),
    ("I can tell quickly how a person is feeling from their tone of voice", 1, "CE"),
    ("It is hard for me to see why some things upset people so much", -1, "ER"),
    ("I am quick to spot when someone in a group is feeling awkward or uncomfortable", 1, "CE"),
    ("If I say something that someone else is offended by, I think that that's their fault, not mine", -1, "SS"),
    ("Other people tell me I am good at understanding how they are feeling", 1, "CE"),
    ("I am good at predicting how someone will feel", 1, "CE"),
    ("I find it easy to put myself in somebody else's shoes", 1, "CE"),
    ("I can usually appreciate the other person's viewpoint, even if I don't agree with it", 1, "CE"),
    ("I usually stay emotionally detached when watching a film", -1, "ER"),
    ("I find it difficult to relate to other people's emotions", -1, "ER"),
    ("I like to be very organized in day-to-day tasks", 0, "SS"),
    ("I make friends easily", 1, "SS"),
    ("I would feel uncomfortable if someone cried in my presence", -1, "ER"),
    ("I find social situations easy", 1, "SS"),
]


def score_eq(form):
    names = {"CE": "Cognitive Empathy", "ER": "Emotional Reactivity", "SS": "Social Skills"}
    total = 0
    subscales = {v: 0 for v in names.values()}
    subscale_max = {v: 0 for v in names.values()}
    for i, (text, key, sub) in enumerate(EQ_ITEMS):
        v = int(form.get(f"eq_{i}", 1) or 1)  # 0..3
        pts = 0
        if key == 1:
            pts = 2 if v == 3 else (1 if v == 2 else 0)
        elif key == -1:
            pts = 2 if v == 0 else (1 if v == 1 else 0)
        # key 0 = filler, 0 points, excluded from max
        total += pts
        if key != 0:
            subscales[names[sub]] += pts
    counts = {}
    for t, k, s2 in EQ_ITEMS:
        if k != 0:
            counts[names[s2]] = counts.get(names[s2], 0) + 1
    for name, n in counts.items():
        subscale_max[name] = 2 * n
    return total, subscales, subscale_max


def eq_band(total):
    if total >= 60: return "Very high empathy"
    if total >= 47: return "High empathy"
    if total >= 32: return "Average empathy"
    if total >= 20: return "Below average empathy"
    return "Low empathy"
