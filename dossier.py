"""PDF dossier builder: hero cover + full assessment analyses."""

import datetime

import charart
import iq_eq
import pdfdoc
import personality

INK = (28, 30, 40)
MUTED = (110, 116, 130)
GOLD = (201, 162, 39)
LINE = (222, 226, 234)

SANITIZE = {"—": "-", "–": "-", "’": "'", "‘": "'", "“": '"', "”": '"', "…": "..."}


def _t(s):
    for k, v in SANITIZE.items():
        s = str(s).replace(k, v)
    return s


def _header(pdf, title, sub=None):
    pdf.rect(0, 0, pdf.w, 64, fill=(20, 24, 38))
    pdf.text(36, 30, 16, _t(title), bold=True, color=(245, 215, 110))
    if sub:
        pdf.text(36, 48, 9, _t(sub), color=(159, 179, 217))
    pdf.line(36, 78, pdf.w - 36, 78, LINE, 1)


def _footer(pdf, n, username):
    pdf.text(36, pdf.h - 30, 8, _t("NEURO-SURVEY Omni Assessment - screening only, not a diagnosis"),
             color=MUTED)
    pdf.text(pdf.w - 90, pdf.h - 30, 8, _t("@%s - p.%d" % (username, n)), color=MUTED)


def build_dossier(username, state):
    prof = state["profile"]
    pdf = pdfdoc.PDF()

    p = pdf.add_page()
    pdf.rect(0, 0, pdf.w, pdf.h, fill=(16, 19, 32))
    art = charart.build(state["done"], state["stats"], state["dominant"],
                        hash(state["fingerprint"]) % 10**9)
    pdf.art(art, ox=48, oy_top=560, scale=0.62, paper=(16, 19, 32))
    pdf.text(330, 120, 11, "OFFICIAL HERO DOSSIER", bold=True, color=GOLD)
    words = state["codename"].split(", ")
    pdf.text(330, 150, 17, _t(words[0]), bold=True, color=(255, 255, 255))
    if len(words) > 1:
        pdf.text(330, 176, 11, _t(", ".join(words[1:])), color=(159, 179, 217))
    pdf.text(330, 210, 10, "@%s" % username, color=GOLD)
    y = 250
    for label, val in (("Stage", state["stage"]), ("Power Level", str(state["power"])),
                       ("Sections", "%d / %d" % (state["done"], state["total_sections"]))):
        pdf.text(330, y, 9, label.upper(), color=MUTED)
        pdf.text(330, y + 14, 12, _t(val), bold=True, color=(255, 255, 255))
        y += 44
    sy = 420
    for k, v in state["stats"].items():
        pdf.text(330, sy, 9, _t("%s  %d" % (k, v)), color=(230, 232, 240))
        w = 180 * min(v, 100) / 100.0
        pdf.rect(330, sy + 6, 180, 4, fill=(45, 52, 74))
        pdf.rect(330, sy + 6, max(2, w), 4, fill=(127, 227, 160))
        sy += 24
    tok = state.get("minted")
    if tok:
        pdf.text(60, 662, 8, "TOKEN #%s  SHA-256 %s..." %
                 (_tokid(tok, state), tok["token_hash"][:24]), color=(127, 227, 160))
    pdf.text(60, pdf.h - 34, 8,
             _t("Generated %s - NEURO-SURVEY on pm3" % datetime.date.today().isoformat()),
             color=MUTED)

    p = pdf.add_page()
    _header(pdf, "Intellect & Empathy", "CHC-style IQ and EQ profile")
    iq = prof.get("iq")
    y = 110
    if iq:
        pdf.text(36, y, 13, "Full-scale standard score: %d (%s)" %
                 (iq["standard_score"], iq_eq.iq_band(iq["standard_score"])),
                 bold=True); y += 26
        pdf.line(36, y, pdf.w - 36, y, LINE); y += 14
        for dom, d in iq["domains"].items():
            pdf.text(36, y, 10, dom, bold=True)
            pdf.text(140, y, 10, "standard %d" % d["standard"])
            pdf.bar(260, y - 2, 200, 10, (d["standard"] - 55) / 90.0)
            pdf.text(475, y, 9, d["band"], color=MUTED)
            y += 24
    else:
        pdf.text(36, y, 10, "Not taken yet.", color=MUTED); y += 24
    y += 18
    eq = prof.get("eq")
    if eq:
        pdf.text(36, y, 13, "Empathy Quotient: %d / 80 (%s)" %
                 (eq["total"], iq_eq.eq_band(eq["total"])), bold=True); y += 26
        mx = {"Cognitive Empathy": 40, "Emotional Reactivity": 25, "Social Skills": 15}
        for sub, v in eq["subscales"].items():
            pdf.text(36, y, 10, sub)
            pdf.text(220, y, 10, "%d / %s" % (v, mx.get(sub, "?")))
            pdf.bar(320, y - 2, 140, 10, v / max(mx.get(sub, 1), 1))
            y += 24
    else:
        pdf.text(36, y, 10, "EQ not taken yet.", color=MUTED)
    _footer(pdf, 2, username)

    p = pdf.add_page()
    _header(pdf, "Personality Forge", "IPIP Big-Five, rescaled 20-100")
    b5 = prof.get("big5", {}).get("domains")
    y = 110
    if b5:
        for dom in personality.DOMAINS:
            d = b5[dom]
            pdf.text(36, y, 11, dom, bold=True)
            pdf.text(200, y, 11, "%d  (%s)" % (d["score"], personality.band(d["score"])))
            pdf.bar(330, y - 2, 130, 12, (d["score"] - 20) / 80.0)
            y += 26
            interp = personality.INTERPRETATION[dom][personality.band(d["score"])]
            for chunk in [interp[i:i + 95] for i in range(0, len(interp), 95)]:
                pdf.text(48, y, 8.5, _t(chunk), color=MUTED)
                y += 14
            y += 8
    else:
        pdf.text(36, y, 10, "Big Five not taken yet.", color=MUTED)
    _footer(pdf, 3, username)

    p = pdf.add_page()
    _header(pdf, "Mind Trials", "Clinical screeners - bands, not diagnoses")
    scr = prof.get("screen")
    y = 110
    if scr:
        from instruments import SCREEN_SECTIONS
        for sec, r in zip(SCREEN_SECTIONS, scr["results"]):
            if not r:
                continue
            pdf.text(36, y, 10, _t(sec["title"]))
            pdf.text(280, y, 10, "score %s / %s" % (r.get("score"), r.get("max")))
            band = r.get("band", "")
            color = (200, 70, 70) if "positive" in band.lower() or "Elevated" in band else MUTED
            pdf.text(400, y, 9, _t(band), color=color)
            y += 22
        flags = scr.get("flags") or []
        if flags:
            y += 10
            pdf.text(36, y, 10, "Flagged instruments:", bold=True); y += 18
            for f in flags:
                name = f[0] if isinstance(f, (list, tuple)) else f
                pdf.text(48, y, 9, "- %s" % name, color=(200, 70, 70)); y += 15
    else:
        pdf.text(36, y, 10, "Screen not taken yet.", color=MUTED)
    y += 24
    tok = state.get("minted")
    if tok:
        pdf.rect(36, y, pdf.w - 72, 64, fill=(245, 245, 238), stroke=GOLD, sw=1.5)
        pdf.text(50, y + 20, 10, "MINTED COLLECTIBLE  TOKEN #%s" % _tokid(tok, state),
                 bold=True, color=GOLD)
        pdf.text(50, y + 38, 8, _t("codename: %s" % state["codename"]))
        pdf.text(50, y + 52, 8, "SHA-256 %s" % tok["token_hash"])
    _footer(pdf, 4, username)
    return pdf.out()


def _tokid(tok, state):
    try:
        return str(tok["id"])
    except Exception:
        return "?"


def build_certificate_pdf(username, state, mint_row):
    pdf = pdfdoc.PDF()
    pdf.add_page()
    pdf.rect(0, 0, pdf.w, pdf.h, fill=(16, 19, 32))
    pdf.rect(24, 24, pdf.w - 48, pdf.h - 48, stroke=GOLD, sw=2.5)
    pdf.rect(32, 32, pdf.w - 64, pdf.h - 64, stroke=GOLD, sw=0.8)
    pdf.text(pdf.w / 2 - 170, 80, 20, "CERTIFICATE OF MINTING", bold=True, color=GOLD)
    art = charart.build(state["done"], state["stats"], state["dominant"],
                        hash(mint_row["token_hash"]) % 10**9)
    pdf.art(art, ox=(pdf.w - 210) / 2, oy_top=702, scale=0.5, paper=(16, 19, 32))
    words = state["codename"].split(", ")
    pdf.text(60, 450, 16, _t(words[0]), bold=True, color=(255, 255, 255))
    if len(words) > 1:
        pdf.text(60, 474, 10, _t(", ".join(words[1:])), color=(159, 179, 217))
    pdf.text(60, 494, 10, "minted to @%s on %s" % (username, mint_row["minted_at"]),
             color=MUTED)
    pdf.rect(60, 530, pdf.w - 120, 46, fill=(10, 13, 24), stroke=(61, 74, 107))
    pdf.text(76, 552, 8, "TOKEN #   %s" % mint_row["id"], bold=True, color=(127, 227, 160))
    pdf.text(76, 568, 8, "SHA-256 %s" % mint_row["token_hash"], color=(127, 227, 160))
    pdf.text(60, 614, 8, "This collectible is deterministically bound to the answers and",
             color=MUTED)
    pdf.text(60, 628, 8, "username at time of minting. Verify by re-hashing the dossier.",
             color=MUTED)
    return pdf.out()
