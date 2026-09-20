"""The "What now?" engine — plain-language context, support routing, clinician guide.

Path A (hybrid): everything here runs server-side on already-anonymized scores
(age/gender/scores only). Names and raw answers never persist anywhere. Nothing
here sends data to a third party; resources are displayed as text, not tracked.
"""

import datetime

# --------------------------------------------------------------------------
# Verified crisis & support resources (checked against official sources, 2026).
# Sections with the crisis tier surface the emergency + UAE + international
# blocks; the support tier surfaces UAE + international non-urgent lines.
# --------------------------------------------------------------------------

RESOURCES = {
    "emergency": ("If you or someone else is in immediate danger, call your local "
                  "emergency number (UAE: 998 medical / 999 police) or go to the "
                  "nearest emergency department. You do not need to have it all "
                  "figured out to ask for help."),
    "uae": [
        ("800-SAKINA (800-725462)",
         "24/7 mental health hotline — Abu Dhabi Department of Health + SEHA/Sakina, Arabic & English"),
        ("800-4673 (800-HOPE)",
         "UAE Mental Support Line — national psychological support, Arabic & English"),
        ("Al Amal Psychiatric Hospital (Dubai): 04 519 2500",
         "24-hour psychiatric emergency support"),
    ],
    "intl": [
        ("988 Suicide & Crisis Lifeline",
         "US/Canada — call or text 988, free, 24/7"),
        ("Crisis Text Line — text HOME to 741741",
         "US/Canada — free text support, 24/7"),
        ("Samaritans — 116 123",
         "UK & Ireland — free, 24/7 (or email jo@samaritans.org)"),
        ("Befrienders Worldwide",
         "find.befrienders.org — directory of local helplines by country"),
    ],
}

# --------------------------------------------------------------------------
# Plain-language context per clinical instrument.
#
#   what     — one sentence everyone understands
#   impact   — what an elevated result tends to look like in daily life,
#              written with zero shame (only shown when elevated)
#   points   — talking points the user can hand a practitioner
# --------------------------------------------------------------------------

PLAIN = {
    "phq9": {
        "what": "A 9-item screen for low mood and depression over the last 2 weeks.",
        "impact": "When this runs high, everyday things — showering, answering "
                  "messages, making a decision — can feel like they take three "
                  "times the energy. That is not laziness; it is the motor "
                  "running on fumes. It also drains concentration, which makes "
                  "executive-function work (planning, starting, finishing) "
                  "noticeably harder.",
        "points": [
            "I've been low more days than not, and sleep / energy / focus are the parts I notice most.",
            "Even small daily routines have started to feel heavy.",
        ],
    },
    "gad7": {
        "what": "A 7-item screen for anxiety and worry over the last 2 weeks.",
        "impact": "When this runs high, the brain keeps scanning for what could "
                  "go wrong — which hijacks the same executive resources you "
                  "need to focus, decide and sleep. Restlessness, irritability "
                  "and physical tension usually ride along.",
        "points": [
            "I worry most days and find it hard to switch the thoughts off at night.",
            "It's affecting my sleep, my patience, and how much I avoid things.",
        ],
    },
    "asrs": {
        "what": "ASRS v1.1 Part A — the adult ADHD screen (6 items for attention and hyperactivity).",
        "impact": "When this flags, it usually shows up as the classic executive "
                  "struggle: starting tasks that feel boring, keeping track of "
                  "appointments, finishing the last 10% of a project. Rejection "
                  "sensitivity and emotional over-reaction to criticism often "
                  "travel with it — the 'small comment, big reaction' effect.",
        "points": [
            "Organising and finishing tasks takes me far longer than it should.",
            "I avoid starting things I find dull, and I lose or forget commitments constantly.",
        ],
    },
    "aq10": {
        "what": "AQ-10 — a 10-item screen for autism-spectrum traits.",
        "impact": "When this flags, sensory overload and cognitive fatigue are "
                  "usually the loudest daily symptoms: loud rooms drain you in "
                  "minutes, small talk costs more energy than it should, and you "
                  "may hyper-focus hard on preferred interests while struggling "
                  "to switch tasks. None of that is a flaw — it's a different "
                  "operating system.",
        "points": [
            "Noisy or crowded settings drain me fast, and I hyper-focus on a few interests to the point of losing track of time.",
            "Social small talk exhausts me more than it should.",
        ],
    },
    "mdq": {
        "what": "MDQ — a screen for past episodes of unusually high mood (bipolar spectrum).",
        "impact": "When this flags, it suggests periods of very high energy — "
                  "less sleep needed, racing thoughts, big plans — followed by "
                  "crashes. Noticing the pattern early is genuinely useful: "
                  "mood tracking and sleep routines are the levers that help most.",
        "points": [
            "I have had periods where my mood swings very high, with much less sleep needed, followed by a crash.",
            "During those high periods I tend to take on far more than I can finish.",
        ],
    },
    "pcptsd5": {
        "what": "PC-PTSD-5 — a screen for trauma-related symptoms in the past month.",
        "impact": "When this flags, the past is intruding on the present: "
                  "unwanted memories, hypervigilance, difficulty feeling safe, "
                  "avoiding reminders. This is a well-understood condition with "
                  "effective treatments — and speaking to a professional about "
                  "it is a strength, not a weakness.",
        "points": [
            "Some events from the past keep coming back uninvited, and I avoid things that remind me.",
            "I find it hard to feel fully safe or to relax, even in calm settings.",
        ],
    },
    "big5": {
        "what": "IPIP-50 Big Five — a 50-item profile of broad personality traits (openness, conscientiousness, extraversion, agreeableness, neuroticism).",
        "impact": "Traits are dimensions, not disorders. What matters is the fit: "
                  "a very introverted, highly sensitive profile in a loud, "
                  "fast-paced environment explains a lot of fatigue. Your scores "
                  "give a useful language for describing yourself to others "
                  "(and to yourself).",
        "points": [
            "My personality profile: high on some traits, low on others — I'd like help seeing how it interacts with the clinical screens.",
            "I want help understanding the fit between who I am and the environment I live/work in.",
        ],
    },
    "pid5": {
        "what": "DSM-5-TR trait domains (PID-5-BF style) — maladaptive trait patterns across five domains.",
        "impact": "Elevated domains describe persistent patterns (e.g. negative "
                  "affectivity, detachment, disinhibition) that colour how you "
                  "react under stress. Like Big Five, these are continuums — "
                  "and they are very discussable with a clinician.",
        "points": [
            "Certain trait domains (negative affectivity / detachment / disinhibition) came back elevated and I'd like to understand how they play out.",
            "I want help spotting the pattern before it becomes a spiral.",
        ],
    },
}

# --------------------------------------------------------------------------
# Tier logic: mood + trauma instruments only (per design spec). ASRS/AQ-10 flags
# are "further assessment" territory, not crisis routing.
# --------------------------------------------------------------------------


def card_context(section, result):
    """Per-card plain-language block for the results page (or None)."""
    if not result:
        return None
    info = PLAIN.get(section["id"])
    if not info:
        return None
    elevated = bool(result.get("flag")) or result.get("level") in ("flag", "alarm")
    return {
        "what": info["what"],
        "elevated": elevated,
        "impact": info.get("impact") if elevated else None,
        "points": info.get("points") if elevated else [],
    }


def support_tier(pairs):
    """pairs: list of (section, result). Returns {tier, reasons, resources}."""
    crisis, support = [], []
    for s, r in pairs:
        if not r:
            continue
        sid, band, flag = s["id"], r.get("band"), bool(r.get("flag"))
        item9 = r.get("item9") or 0
        if sid == "phq9" and item9 >= 1:
            crisis.append("You marked that you've had thoughts that you'd be better "
                          "off dead, or of hurting yourself. That is a heavy thing "
                          "to carry — please reach someone today, not 'later'.")
        if sid == "pcptsd5" and flag:
            crisis.append("The trauma screen (PC-PTSD-5) came back positive for the "
                          "past month. Trauma support is effective, and now is a "
                          "good time to reach for it.")
        if sid == "mdq" and flag:
            support.append("MDQ flagged possible bipolar-spectrum symptoms — high "
                           "periods followed by crashes. Worth a conversation, and "
                           "worth keeping a simple mood log this week.")
        if sid == "phq9" and band in ("Severe", "Moderately severe"):
            support.append("PHQ-9 in the %s range — this is past 'just having a "
                           "rough patch' territory, and that's OK to say out loud." % band)
        elif sid == "phq9" and flag:
            support.append("PHQ-9 above the clinical threshold (moderate range).")
        if sid == "gad7" and band == "Severe":
            support.append("GAD-7 in the Severe range — chronic, heavy worry that "
                           "deserves real support, not willpower.")
        elif sid == "gad7" and flag:
            support.append("GAD-7 above the clinical threshold.")
    if crisis:
        return {"tier": "crisis", "reasons": crisis, "support": support,
                "resources": RESOURCES}
    if support:
        return {"tier": "support", "reasons": support, "support": support,
                "resources": RESOURCES}
    return {"tier": "ok", "reasons": [], "support": [], "resources": RESOURCES}


# --------------------------------------------------------------------------
# Support routing for the stand-alone instrument library. Only flags with a
# validated threshold appear here; descriptive-band modules (PSS-4) never
# reach this function because they do not set ``flag``.
# --------------------------------------------------------------------------

LIBRARY_TIER = {
    "phq2": ("support", "The 2-item mood screen came back positive — that's the "
              "signal to take the full PHQ-9, and more importantly to talk to "
              "someone equipped to help."),
    "gad2": ("support", "The 2-item anxiety screen came back positive. That's a "
              "sign to look closer, and worth a real conversation rather than "
              "more willpower."),
    "who5": ("support", "Your well-being score came back low. Acting on that "
              "early is a kindness to yourself, not an over-reaction."),
    "isi": ("support", "Your sleep score landed in the clinical insomnia range. "
             "Sleep is a lever that moves almost everything else — worth real "
             "support."),
    "pcl5": ("crisis", "The trauma screen (PCL-5) came back positive. Trauma "
             "support is effective, and now is a good time to reach for it."),
    "auditc": ("support", "The alcohol screen came back positive. That's a health "
               "signal, not a character flaw — worth an honest, non-judgemental "
               "conversation with a GP or clinician."),
}


def library_tier(module, result):
    """Support tier for a single stand-alone library result."""
    if not result or not result.get("flag"):
        return {"tier": "ok", "reasons": [], "resources": RESOURCES}
    entry = LIBRARY_TIER.get(module["id"])
    if not entry:
        return {"tier": "ok", "reasons": [], "resources": RESOURCES}
    return {"tier": entry[0], "reasons": [entry[1]], "resources": RESOURCES}


# --------------------------------------------------------------------------
# Discussion guide for a practitioner (plain-text).
# --------------------------------------------------------------------------


def _instrument_block(section, result, info):
    lines = []
    flag = bool(result.get("flag"))
    band = result.get("band", "")
    score = "%s" % result.get("score")
    if result.get("max"):
        score += "/%s" % result["max"]
    lines.append("[%s] %s — %s (%s)" %
                 (section["instrument"], section["title"], score, band))
    lines.append("  What this screen is about: %s" % info["what"])
    if flag:
        lines.append("  In daily life this can look like: %s" % info["impact"])
        lines.append("  Points you may want to raise:")
        for pt in info["points"]:
            lines.append("    - %s" % pt)
    return lines


def discussion_text(pairs, flags, ident, tier):
    """Plain-text 'Discussion Guide for my Doctor / Therapist'."""
    when = datetime.date.today().isoformat()
    out = []
    out.append("DISCUSSION GUIDE FOR MY DOCTOR / THERAPIST")
    out.append("=" * 46)
    out.append("Date: %s  ·  NEURO-SURVEY Omni Assessment (screening only)" % when)
    out.append("")
    out.append("How to read this: these are screening results, not a diagnosis. "
               "They help decide whether formal assessment is worth doing. "
               "Confidential by design — only age, gender and scores exist; "
               "your name and raw answers are never stored.")
    out.append("")
    flagged = [section for section, r in pairs if r and r.get("flag")]
    if flagged:
        out.append("Screens that crossed a clinical threshold:")
        for section in flagged:
            out.append("  - %s (%s)" % (section["title"], section["instrument"]))
        out.append("")
    out.append("--- Scores, explained ---")
    for section, r in pairs:
        if not r:
            continue
        info = PLAIN.get(section["id"])
        if not info:
            continue
        out.extend(_instrument_block(section, r, info))
        out.append("")
    if tier["tier"] != "ok":
        out.append("--- Support resources ---")
        out.append(RESOURCES["emergency"])
        out.append("UAE:")
        for name, desc in RESOURCES["uae"]:
            out.append("  - %s — %s" % (name, desc))
        out.append("International:")
        for name, desc in RESOURCES["intl"]:
            out.append("  - %s — %s" % (name, desc))
        out.append("")
    if flags:
        out.append("--- Flags raised this session ---")
        for title, instrument in flags:
            out.append("  # %s (%s)" % (title, instrument))
        out.append("")
    out.append("This document is screening-level information, not a medical "
               "diagnosis or treatment plan.")
    return "\n".join(out)