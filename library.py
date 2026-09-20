"""Extended instrument library — stand-alone screeners.

Every item below is reproduced verbatim from an authoritative, openly available
source and may be used without a paid licence. Instruments whose item text is
copyrighted and permission-restricted are listed in REFERENCE_ONLY rather than
reproduced, so nothing on this site is paraphrased into a fake scale.

Scoring conventions:
- ``scale`` is the default list of response labels; ``values`` maps the selected
  option (by position) to points.  Both default to ``range(len(scale))``.
- An item may override the default with a dict::

      {"t": "statement", "scale": ["...", "..."]}

- ``reverse`` lists item indices that are reverse-scored within the value range.
- Bands give a friendly name + level (``ok``/``info``/``flag``/``alarm``).
  ``flag``/``alarm`` bands set ``flag=True``.
"""

LIKERT4 = ["Not at all", "Several days", "More than half the days",
           "Nearly every day"]

WHO5 = {
    "id": "who5",
    "title": "Well-being",
    "instrument": "WHO-5 Well-Being Index",
    "group": "Well-being",
    "blurb": "Five positively worded items on how good life has felt over the "
             "past two weeks. Higher is better.",
    "intro": "Over the last two weeks, how much of the time has each of these "
             "been true for you?",
    "scale": ["All of the time", "Most of the time", "More than half of the time",
              "Less than half of the time", "Some of the time", "At no time"],
    "values": [5, 4, 3, 2, 1, 0],
    "max": 25,
    "cutoff": 13,
    "bands": [(0, 12, "Low well-being — screen positive", "flag"),
              (13, 19, "Moderate well-being", "info"),
              (20, 25, "Good well-being", "ok")],
    "items": [
        "I have felt cheerful and in good spirits",
        "I have felt calm and relaxed",
        "I have felt active and vigorous",
        "I woke up feeling fresh and rested",
        "My daily life has been filled with things that interest me",
    ],
    "citation": "World Health Organization (1998). Well-Being Index (WHO-5). "
                "WHO Regional Office for Europe.",
    "note": "Raw score 0–25; multiply by 4 for a 0–100 percentage. A score at or "
            "below 50% (raw ≤ 12) is the usual trigger for further depression "
            "screening.",
    "minutes": 1,
}

PHQ2 = {
    "id": "phq2",
    "title": "Mood — quick 2-item check",
    "instrument": "PHQ-2",
    "group": "Mood & anxiety",
    "blurb": "The two-item depression pre-screen. A positive result means take "
             "the full PHQ-9, not that anything is wrong.",
    "intro": "Over the last 2 weeks, how often have you been bothered by…",
    "scale": LIKERT4,
    "max": 6,
    "cutoff": 3,
    "items": [
        "Little interest or pleasure in doing things",
        "Feeling down, depressed, or hopeless",
    ],
    "citation": "Kroenke K, Spitzer RL, Williams JB (2003). The Patient Health "
                "Questionnaire-2. Med Care 41(11):1284–92.",
    "note": "A PHQ-2 score of 3 or more is the recommended trigger for the full "
            "PHQ-9. It is a screen, not a diagnosis.",
    "minutes": 1,
}

GAD2 = {
    "id": "gad2",
    "title": "Anxiety — quick 2-item check",
    "instrument": "GAD-2",
    "group": "Mood & anxiety",
    "blurb": "The two-item anxiety pre-screen, drawn from the GAD-7.",
    "intro": "Over the last 2 weeks, how often have you been bothered by…",
    "scale": LIKERT4,
    "max": 6,
    "cutoff": 3,
    "items": [
        "Feeling nervous, anxious, or on edge",
        "Not being able to stop or control worrying",
    ],
    "citation": "Kroenke K, Spitzer RL, Williams JB, Monahan PO, Löwe B (2007). "
                "Anxiety disorders in primary care: the GAD-2. Ann Intern Med "
                "146(5):317–25.",
    "note": "A GAD-2 score of 3 or more is the recommended trigger for the full "
            "GAD-7. It is a screen, not a diagnosis.",
    "minutes": 1,
}

ISI = {
    "id": "isi",
    "title": "Sleep — insomnia severity",
    "instrument": "Insomnia Severity Index (ISI)",
    "group": "Sleep",
    "blurb": "Seven questions about how badly sleep problems are biting, over "
             "the last two weeks.",
    "intro": "Rate the current severity of your insomnia over the LAST TWO WEEKS.",
    "scale": ["None", "Mild", "Moderate", "Severe", "Very severe"],
    "max": 28,
    "cutoff": 15,
    "bands": [(0, 7, "No clinically significant insomnia", "ok"),
              (8, 14, "Subthreshold insomnia", "info"),
              (15, 21, "Clinical insomnia (moderate)", "flag"),
              (22, 28, "Clinical insomnia (severe)", "alarm")],
    "items": [
        "Difficulty falling asleep",
        "Difficulty staying asleep",
        "Problems waking up too early",
        {"t": "How satisfied/dissatisfied are you with your current sleep pattern?",
         "scale": ["Very satisfied", "Satisfied", "Moderately satisfied",
                   "Dissatisfied", "Very dissatisfied"]},
        {"t": "How noticeable to others do you think your sleep problem is in "
              "terms of impairing the quality of your life?",
         "scale": ["Not at all noticeable", "A little", "Somewhat", "Much",
                   "Very much noticeable"]},
        {"t": "How worried/distressed are you about your current sleep problem?",
         "scale": ["Not at all worried", "A little", "Somewhat", "Much",
                   "Very much worried"]},
        {"t": "To what extent do you consider your sleep problem to interfere "
              "with your daily functioning (e.g. daytime fatigue, mood, ability "
              "to function at work/daily chores, concentration, memory)?",
         "scale": ["Not at all interfering", "A little", "Somewhat", "Much",
                   "Very much interfering"]},
    ],
    "citation": "Morin CM (1993, 1996, 2000, 2006). Insomnia Severity Index. "
                "Freely available for clinical and research use.",
    "note": "Total 0–28. Scores of 15 or more indicate clinical insomnia and are "
            "worth discussing with a clinician; 8–14 is subthreshold.",
    "minutes": 2,
}

PSS4 = {
    "id": "pss4",
    "title": "Stress — perceived stress",
    "instrument": "Perceived Stress Scale-4 (PSS-4)",
    "group": "Stress & coping",
    "blurb": "Four items on how unpredictable and overwhelming life has felt "
             "in the last month.",
    "intro": "In the last month, how often have you…",
    "scale": ["Never", "Almost never", "Sometimes", "Fairly often", "Very often"],
    "max": 16,
    "reverse": [1, 2],
    "bands": [(0, 5, "Low perceived stress", "ok"),
              (6, 9, "Moderate perceived stress", "info"),
              (10, 16, "High perceived stress", "info")],
    "items": [
        "felt that you were unable to control the important things in your life?",
        "felt confident about your ability to handle your personal problems?",
        "felt that things were going your way?",
        "felt difficulties were piling up so high that you could not overcome them?",
    ],
    "citation": "Cohen S, Kamarck T, Mermelstein R (1983). A global measure of "
                "perceived stress. J Health Soc Behav 24(4):385–96. "
                "PSS-4 normative data: Warttig et al. (2013).",
    "note": "Items 2 and 3 are reverse-scored. The PSS-4 has no validated "
            "clinical cutoff — the bands above are descriptive only.",
    "minutes": 1,
}

AUDITC = {
    "id": "auditc",
    "title": "Alcohol use",
    "instrument": "AUDIT-C",
    "group": "Substance use",
    "blurb": "The three-item alcohol screen from the WHO AUDIT. Honest answers "
             "make it useful.",
    "intro": "These questions are about the past year. One drink = a can/bottle "
             "of beer, a glass of wine, or one shot of spirits.",
    "scale": ["Never", "Monthly or less", "2–4 times a month",
              "2–3 times a week", "4 or more times a week"],
    "max": 12,
    "cutoff": 4,
    "bands": [(0, 3, "Lower-risk range", "ok"),
              (4, 12, "Positive screen — further assessment advised", "flag")],
    "items": [
        "How often did you have a drink containing alcohol in the past year?",
        {"t": "How many drinks did you have on a typical day when you were "
              "drinking in the past year?",
         "scale": ["None, I do not drink", "1 or 2", "3 or 4", "5 or 6",
                   "7 to 9", "10 or more"],
         "values": [0, 0, 1, 2, 3, 4]},
        "How often did you have six or more drinks on one occasion in the "
        "past year?",
    ],
    "citation": "Babor TF et al. (2001). AUDIT: The Alcohol Use Disorders "
                "Identification Test. WHO. AUDIT-C: Bush K et al. (1998), "
                "Arch Intern Med 158(16):1789–95.",
    "note": "Total 0–12. A score of 4 or more in men, or 3 or more in women, is "
            "considered a positive screen. This is a screen, not a diagnosis.",
    "minutes": 1,
}

PCL5 = {
    "id": "pcl5",
    "title": "Trauma — PTSD check",
    "instrument": "PCL-5",
    "group": "Trauma",
    "blurb": "The 20-item DSM-5 PTSD symptom checklist. Keep your worst "
             "stressful experience in mind.",
    "intro": "Below is a list of problems people sometimes have after a very "
             "stressful experience. Keeping your worst event in mind, how much "
             "have you been bothered by each problem in the past month?",
    "scale": ["Not at all", "A little bit", "Moderately", "Quite a bit",
              "Extremely"],
    "max": 80,
    "cutoff": 31,
    "bands": [(0, 30, "Below screening threshold", "ok"),
              (31, 80, "Above screening threshold", "flag")],
    "items": [
        "Repeated, disturbing, and unwanted memories of the stressful experience?",
        "Repeated, disturbing dreams of the stressful experience?",
        "Suddenly feeling or acting as if the stressful experience were "
        "actually happening again (as if you were actually back there reliving it)?",
        "Feeling very upset when something reminded you of the stressful experience?",
        "Having strong physical reactions when something reminded you of the "
        "stressful experience (for example, heart pounding, trouble breathing, "
        "sweating)?",
        "Avoiding memories, thoughts, or feelings related to the stressful "
        "experience?",
        "Avoiding external reminders of the stressful experience (for example, "
        "people, places, conversations, activities, objects, or situations)?",
        "Trouble remembering important parts of the stressful experience?",
        "Having strong negative beliefs about yourself, other people, or the "
        "world (for example, having thoughts such as: I am bad, there is "
        "something seriously wrong with me, no one can be trusted, the world "
        "is completely dangerous)?",
        "Blaming yourself or someone else for the stressful experience or what "
        "happened after it?",
        "Having strong negative feelings such as fear, horror, anger, guilt, or shame?",
        "Loss of interest in activities that you used to enjoy?",
        "Feeling distant or cut off from other people?",
        "Trouble experiencing positive feelings (for example, being unable to "
        "feel happiness or have loving feelings for people close to you)?",
        "Irritable behavior, angry outbursts, or acting aggressively?",
        "Taking too many risks or doing things that could cause you harm?",
        "Being “superalert” or watchful or on guard?",
        "Feeling jumpy or easily startled?",
        "Having difficulty concentrating?",
        "Trouble falling or staying asleep?",
    ],
    "citation": "Weathers FW, Litz BT, Keane TM, Palmieri PA, Marx BP, "
                "Schnurr PP (2013). The PTSD Checklist for DSM-5 (PCL-5). "
                "U.S. Department of Veterans Affairs — public domain.",
    "note": "Total 0–80. A cutoff of 31–33 is commonly used for a probable "
            "screen; this is not a diagnosis and a clinician should interpret it.",
    "minutes": 5,
}

LIBRARY = [WHO5, PHQ2, GAD2, ISI, PSS4, AUDITC, PCL5]
BY_ID = {m["id"]: m for m in LIBRARY}

# Small metric list for cross-linking scores into the daily tracker.
LIB_METRICS = [{"id": m["id"], "label": m["title"], "max": m["max"]}
               for m in LIBRARY]

# Instruments we deliberately do NOT reproduce because the publisher requires
# a licence. Shown on the library page as reference-only cards.
REFERENCE_ONLY = [
    {"title": "Autism traits (RAADS-14)",
     "instrument": "RAADS-14 Screen",
     "why": "Item text is copyrighted by the rights holders; obtain the official "
            "form from the publisher or an authorised clinical source."},
    {"title": "Alexithymia (TAS-20)",
     "instrument": "Toronto Alexithymia Scale-20",
     "why": "Licensed for research/clinical use by the publisher; item text is "
            "not reproducible without permission."},
    {"title": "Emotion regulation (DERS-16)",
     "instrument": "Difficulties in Emotion Regulation Scale-16",
     "why": "Reproduction is permitted for personal use only; a public web "
            "version needs written permission from the copyright holders."},
    {"title": "Interoception (MAIA-2)",
     "instrument": "Multidimensional Assessment of Interoceptive Awareness-2",
     "why": "Requires a paid or written licence for use; not reproduced here."},
]


def item_text(item):
    return item["t"] if isinstance(item, dict) else item


def item_scale(module, item):
    if isinstance(item, dict) and "scale" in item:
        return item["scale"]
    return module["scale"]


def item_values(module, item):
    if isinstance(item, dict) and "values" in item:
        return item["values"]
    return module.get("values") or list(range(len(module["scale"])))


def missing_items(module, form):
    """Indices of items with no response — the scorer must not guess these.

    A guessed answer fails in one of two directions depending on the scale
    anchor (e.g. WHO-5 index 0 is the *best* response), so completeness is
    enforced before scoring.
    """
    sid = module["id"]
    return [i for i in range(len(module["items"]))
            if form.get(f"{sid}_{i}") in (None, "")]


def score_module(module, form):
    """Score a submitted module form. Raw answers are never stored."""
    sid = module["id"]
    reverse = set(module.get("reverse") or [])
    items = module["items"]
    total = 0
    for i, item in enumerate(items):
        values = item_values(module, item)
        try:
            idx = int(form.get(f"{sid}_{i}"))
        except (TypeError, ValueError):
            idx = 0
        idx = max(0, min(len(values) - 1, idx))
        val = values[idx]
        if i in reverse:
            val = max(values) - val
        total += val

    band, level = "Result", "info"
    for lo, hi, name, lv in module.get("bands") or []:
        if lo <= total <= hi:
            band, level = name, lv
            break
    if not module.get("bands"):
        cutoff = module.get("cutoff")
        if cutoff is not None:
            positive = total >= cutoff
            band = "Screen positive" if positive else "Screen negative"
            level = "flag" if positive else "ok"
    flag = level in ("flag", "alarm")
    return {"score": total, "max": module["max"], "band": band,
            "level": level, "flag": flag, "note": module.get("note", "")}
