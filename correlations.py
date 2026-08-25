"""Cross-metric correlation engine.

Combines results from every instrument into interpretive insights, based on
relationships documented in the research literature:

- Camouflaging/masking: autistic traits with high EQ / strong social skills
  (CAT-Q literature; Hull et al. 2017); masking is associated with anxiety,
  depression and burnout in neurodivergent adults.
- Twice-exceptionality: high cognitive ability often delays/masks ADHD and
  autism recognition (e.g. Brown et al. on high-IQ ADHD).
- AuDHD: ADHD and autism co-occur far above chance (50%+ overlap estimates).
- ADHD cognition: working-memory / processing-speed deficits relative to
  fluid reasoning are the classic adult ADHD cognitive signature.
- Rejection sensitivity dysphoria: associated with ADHD and with high
  negative emotionality.
"""

def _latest(rows):
    return rows[0] if rows else None


def combined_insights(iq, eq, screen, maps):
    """All inputs are the user's latest result dicts (or None).

      iq:     {"standard_score": int, "domains": {code: {"standard": int}}}
      eq:     {"total": int, "max": int, "subscales": {name: val}}
      screen: {"flags": [names], "domains": [(title, band, score, max)]}
      maps:   {"scores": {param: 0-8}} latest quick map
    Returns list of {"title", "text", "tone"} — tone in ok|info|flag.
    """
    out = []

    iq_score = iq.get("standard_score") if iq else None
    eq_total = eq.get("total") if eq else None
    eq_subs = eq.get("subscales", {}) if eq else {}
    flags = [f.lower() for f in (screen.get("flags") or [])] if screen else []
    dom = {}
    for title, band, score, mx in (screen.get("domains") or []):
        dom[title.lower()] = (band, score, mx)

    has_adhd = any("attention" in f for f in flags)
    has_asd = any("autism" in f for f in flags)
    phq = dom.get("mood & depression", ("", 0, 27))
    gad = dom.get("anxiety", ("", 0, 21))
    mood_flag = any("mood" in f for f in flags)
    anx_flag = any("anxiety" in f for f in flags)

    ne = None
    if screen:
        for title, band, score, mx in screen.get("domains") or []:
            if "negative emotionality" in title.lower() and mx == 50:
                ne = score

    map_scores = maps.get("scores", {}) if maps else {}
    masking_self = map_scores.get("Masking Effort", 0)

    # 1. AuDHD co-occurrence
    if has_adhd and has_asd:
        out.append({
            "title": "AuDHD pattern 🧩⚡",
            "tone": "info",
            "text": "Both your ADHD and autism screens are positive. ADHD and "
                    "autism co-occur far more often than chance — a majority of "
                    "autistic adults also meet ADHD criteria. The combination "
                    "often produces push-pull experiences: craving novelty AND "
                    "routine at once.",
        })

    # 2. Masking signature: autistic traits + high empathy/social skill
    if has_asd and eq_total is not None and eq_total >= 47:
        out.append({
            "title": "High-masking signature 🎭",
            "tone": "flag",
            "text": "Elevated autistic traits TOGETHER with a high Empathy "
                    "Quotient is a known camouflaging profile: you may be "
                    "consciously translating yourself in real time. Research "
                    "(CAT-Q; Hull et al.) links this masking style to exhaustion, "
                    "identity confusion and delayed recognition.",
        })
    if has_asd and eq_subs.get("Social Skills", 0) >= 8:
        out.append({
            "title": "Learned social fluency 🎭",
            "tone": "info",
            "text": "Strong social-skills scores alongside autistic traits "
                    "suggest learned/compensated social fluency rather than "
                    "absent intuition — effortful, not effortless.",
        })

    # 3. Masking correlates with mood
    if (has_asd or has_adhd) and (mood_flag or anx_flag):
        out.append({
            "title": "Masking → mood pathway 🎭→🌧️",
            "tone": "flag",
            "text": "Neurodivergent screens are positive AND mood/anxiety "
                    "crossed clinical thresholds. Research consistently links "
                    "camouflaging to anxiety and depression — the mood signals "
                    "may be downstream of sustained self-suppression, not "
                    "separate conditions.",
        })

    # 4. Twice-exceptional / compensation
    if iq_score and iq_score >= 120 and (has_adhd or has_asd):
        out.append({
            "title": "Twice-exceptional pattern 🎓⚡",
            "tone": "info",
            "text": f"High cognitive ability (IQ {iq_score}) alongside "
                    "neurodevelopmental flags. High IQ frequently masks ADHD/"
                    "autism — struggles get attributed to 'not trying' because "
                    "results look fine. Recognition often comes late.",
        })
    if iq_score and iq_score >= 120 and not flags and eq_total is not None:
        out.append({
            "title": "Compensation watch 🎓",
            "tone": "info",
            "text": "Strong cognition with no current flags. If day-to-day "
                    "still feels harder than it looks on paper, achievement-"
                    "based compensation may be hiding effort — worth an honest "
                    "self-audit.",
        })

    # 5. ADHD cognitive signature: Gs/Gwm a full band below Gf
    if iq and iq.get("domains"):
        d = iq["domains"]
        gf = d.get("Gf", {}).get("standard")
        gwm = d.get("Gwm", {}).get("standard")
        gs = d.get("Gs", {}).get("standard")
        if gf and gwm and gs and gf - min(gwm, gs) >= 15:
            out.append({
                "title": "Cognitive speed gap 🐢⚡",
                "tone": "info",
                "text": "Your fluid reasoning outpaces your working memory / "
                        "processing speed by 15+ points — the classic adult "
                        "ADHD cognitive signature, and a common reason smart "
                        "people feel 'secretly slow'.",
            })

    # 6. Rejection sensitivity
    if has_adhd and ne is not None and ne >= 30:
        out.append({
            "title": "Rejection sensitivity 💔",
            "tone": "info",
            "text": "ADHD traits plus high negative emotionality is where "
                    "rejection-sensitive dysphoria usually lives — criticism "
                    "lands disproportionately hard. Worth naming explicitly "
                    "in any clinical conversation.",
        })

    # 7. Burnout risk
    if (has_asd or has_adhd or masking_self >= 6) and ne is not None and ne >= 30 \
            and map_scores.get("Sleep Rhythm", 0) >= 5:
        out.append({
            "title": "Burnout risk 🔥",
            "tone": "flag",
            "text": "Masking effort, high emotional load and unstable sleep "
                    "together are the classic neurodivergent burnout triad. "
                    "Recovery usually requires reducing masking load, not "
                    "pushing harder.",
        })

    # 8. Self-reported masking corroborates
    if masking_self >= 6 and not any("mask" in o["title"].lower() for o in out):
        out.append({
            "title": "Heavy self-reported masking 🎭",
            "tone": "info",
            "text": "You report strong masking effort on the Quick Map. "
                    "Camouflaging this intense is itself worth discussing — "
                    "it consumes significant daily energy.",
        })

    # 9. EQ low + no flags: informational
    if eq_total is not None and eq_total < 20 and not flags:
        out.append({
            "title": "Low empathy score, clean screens ℹ️",
            "tone": "info",
            "text": "A low EQ with no clinical flags sometimes reflects "
                    "alexithymia rather than reduced empathy — difficulty "
                    "identifying feelings, not lacking care.",
        })

    return out
