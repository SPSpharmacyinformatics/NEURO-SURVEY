"""Metric definitions for local (on-device) longitudinal trends and the
shareable side-by-side comparison.

Nothing here is stored server-side: the results page hands the current
snapshot to the browser, which keeps the history in localStorage. The
compare code is a compact, lossy, non-identifying encoding of a handful of
scale percentages generated in the browser.

The order of METRICS is part of the wire format for comparison codes — always
append, never reorder.
"""

CLINICAL = [
    ("phq9", "Mood (PHQ-9)", 27),
    ("gad7", "Anxiety (GAD-7)", 21),
    ("asrs", "Attention (ASRS)", 6),
    ("aq10", "Autism traits (AQ-10)", 10),
    ("mdq", "Mood swings (MDQ)", 13),
    ("pcptsd5", "Trauma (PC-PTSD-5)", 5),
]

BIG5_DOMAINS = [
    "Extraversion", "Agreeableness", "Conscientiousness",
    "Negative Emotionality", "Openness to Experience",
]

PID5_DOMAINS = [
    "Negative Affect", "Detachment", "Antagonism",
    "Disinhibition", "Psychoticism",
]

METRICS = (
    [{"key": k, "label": lbl, "max": mx, "group": "Clinical"} for k, lbl, mx in CLINICAL]
    + [{"key": "big5_" + d, "label": d, "max": 50, "group": "Big Five"}
       for d in BIG5_DOMAINS]
    + [{"key": "pid5_" + d, "label": d, "max": 15, "group": "DSM-5-TR traits"}
       for d in PID5_DOMAINS]
)


def snapshot(pairs):
    """pairs: [(section, result), ...] -> {metric_key: raw_value}."""
    out = {}
    for section, result in pairs:
        sid = section["id"]
        if sid == "big5":
            for dom, val in (result.get("domains") or {}).items():
                out["big5_" + dom] = val
        elif sid == "pid5":
            for dom, val in (result.get("domains") or {}).items():
                out["pid5_" + dom] = val
        else:
            out[sid] = result.get("score")
    return {k: v for k, v in out.items() if v is not None}
