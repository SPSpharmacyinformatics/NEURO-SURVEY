"""Procedural vector hero art shared by SVG rendering and the PDF dossier."""

import math
import random


def hsv(h, s, v):
    h = h % 360 / 60.0
    c = v * s
    x = c * (1 - abs(h % 2 - 1))
    m = v - c
    r, g, b = [(c, x, 0), (x, c, 0), (0, c, x),
               (0, x, c), (x, 0, c), (c, 0, x)][int(h)]
    return (round((r + m) * 255), round((g + m) * 255), round((b + m) * 255))


def _mix(c1, c2, t):
    return tuple(round(a + (b - a) * t) for a, b in zip(c1, c2))


DOMINANT_HUE = {
    "Openness": 268,
    "Conscientiousness": 205,
    "Extraversion": 32,
    "Agreeableness": 145,
    "Emotional Stability": 350,
}


def build(done, st, dominant, seed):
    rng = random.Random(seed)
    hue = DOMINANT_HUE.get(dominant or "Conscientiousness", 210)
    main = hsv(hue, 0.72, 0.85)
    dark = hsv(hue, 0.65, 0.22)
    mid = hsv(hue, 0.6, 0.5)
    accent = hsv(hue + 150, 0.85, 0.9)
    glow = _mix(main, (255, 255, 255), 0.45)

    S = []
    W, H = 420, 560

    def C(cx, cy, r, fill, stroke=None, sw=0, op=1.0):
        S.append({"op": "circle", "cx": cx, "cy": cy, "r": r, "fill": fill,
                  "stroke": stroke, "sw": sw, "a": op})

    def P(pts, fill=None, stroke=None, sw=0, a=1.0):
        S.append({"op": "poly", "pts": pts, "fill": fill,
                  "stroke": stroke, "sw": sw, "a": a})

    def L(x1, y1, x2, y2, stroke, sw):
        S.append({"op": "line", "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                  "stroke": stroke, "sw": sw, "a": 1.0})

    S.append({"op": "rect", "x": 0, "y": 0, "w": W, "h": H, "rx": 24,
              "fill": dark, "stroke": None, "sw": 0, "a": 1.0})

    cx, cy = 210, 240
    aura_r = [0, 120, 150, 175, 200][max(done, 0)] or 90
    rings = [0.05, 0.09, 0.14][: max(done, 1)]
    for i, a in enumerate(rings):
        C(cx, cy, aura_r - i * 28, main, None, 0, a)

    S.append({"op": "ellipse" , "cx": cx, "cy": 505, "rx": 130, "ry": 18,
              "fill": (0, 0, 0), "stroke": None, "sw": 0, "a": 0.35})

    intellect = st.get("Intellect", 30)
    empathy = st.get("Empathy", 30)
    resolve = st.get("Resolve", 40)
    serenity = st.get("Serenity", 40)
    radiance = st.get("Radiance", 40)

    if done == 0:
        C(cx, 250, 46, None, mid, 3, 0.7)
        P([(170, 330), (250, 330), (230, 430), (190, 430)], None, mid, 3, 0.55)
        for _ in range(7):
            px, py = rng.randint(80, 340), rng.randint(140, 420)
            C(px, py, rng.randint(2, 5), accent, None, 0, 0.5)
        return S

    cape_w = 95 + done * 12
    P([(cx, 165), (cx - cape_w, 300), (cx - cape_w + 25, 470), (cx, 430),
       (cx + cape_w - 25, 470), (cx + cape_w, 300)], mid, None, 0, 0.95)

    if done >= 3:
        wing = 70 + (done - 3) * 45
        for sgn in (-1, 1):
            pts = [(cx + sgn * 38, 235), (cx + sgn * (70 + wing), 150 - done * 8),
                   (cx + sgn * (60 + wing // 2), 245), (cx + sgn * (78 + wing), 320),
                   (cx + sgn * 40, 290)]
            P(pts, glow, accent, 2, 0.75)

    sh = 34 + resolve / 100 * 16
    torso = [(cx, 185), (cx + 62, 215), (cx + sh, 330), (cx + 20, 400),
             (cx - 20, 400), (cx - sh, 330), (cx - 62, 215)]
    P(torso, main, _mix(main, (0, 0, 0), 0.35), 3)

    if done >= 2:
        for sgn in (-1, 1):
            P([(cx + sgn * 52, 212), (cx + sgn * 92, 228), (cx + sgn * 84, 262),
               (cx + sgn * 48, 250)], _mix(main, (255, 255, 255), 0.2), dark, 2)

    core_r = 10 + empathy / 100 * 14
    C(cx, 275, core_r, accent, glow, 2, 0.95)
    C(cx, 275, core_r + 6, None, accent, 1, 0.5)

    hr = 42
    C(cx, 128, hr, _mix(main, (255, 235, 210), 0.65), dark, 3)
    visor_h = 8 + intellect / 100 * 8
    S.append({"op": "rect", "x": cx - 30, "y": 116, "w": 60, "h": visor_h, "rx": 4,
              "fill": (20, 24, 34), "stroke": glow, "sw": 1, "a": 1.0})
    L(cx - 22, 120 + visor_h / 2, cx + 22, 120 + visor_h / 2, accent, 2)
    P([(cx - 14, 150), (cx + 14, 150), (cx, 160)], _mix(main, (0, 0, 0), 0.4))

    if done >= 3:
        blade = 90 + intellect / 100 * 70
        L(cx + 96, 420, cx + 96, 420 - blade, glow, 5)
        L(cx + 96, 420, cx + 96, 420 - blade, (255, 255, 255), 2)
        P([(cx + 82, 424), (cx + 110, 424), (cx + 104, 436), (cx + 88, 436)], dark)
        C(cx + 96, 444, 7, accent)

    shield = 26 + serenity / 100 * 18
    sp = [(cx - 96, 420 - shield), (cx - 96 + shield * 0.8, 420 - shield),
          (cx - 96 + shield * 0.9, 420 + shield * 0.3),
          (cx - 96, 420 + shield), (cx - 96 - shield * 0.9, 420 + shield * 0.3),
          (cx - 96 - shield * 0.8, 420 - shield)]
    P(sp, _mix(mid, (0, 0, 0), 0.25), accent, 3)
    C(cx - 96, 420, shield * 0.32, glow, None, 0, 0.85)

    if done >= 4:
        P([(cx - 34, 92), (cx - 20, 64), (cx - 7, 88), (cx, 56), (cx + 7, 88),
           (cx + 20, 64), (cx + 34, 92)], hsv(48, 0.9, 0.95), dark, 2)
        for sgn in (-1, 1):
            P([(cx + sgn * 52, 218), (cx + sgn * 66, 196), (cx + sgn * 74, 232)],
              hsv(48, 0.9, 0.95), dark, 1.5)

    n_part = 8 + done * 4
    for _ in range(n_part):
        px, py = rng.randint(40, 380), rng.randint(90, 480)
        C(px, py, rng.randint(2, 5), rng.choice([accent, glow, main]), None, 0,
          rng.uniform(0.25, 0.7))
    return S


def _fmt(c):
    return "#%02x%02x%02x" % tuple(c)


def render_svg(shapes, title="hero"):
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 560" '
           'role="img" aria-label="%s">' % title]
    for s in shapes:
        a = s.get("a", 1.0)
        op = (' opacity="%s"' % round(a, 2)) if a < 1 else ""
        fill = s.get("fill")
        stroke = s.get("stroke")
        f = (' fill="%s"' % _fmt(fill)) if fill else ' fill="none"'
        st = (' stroke="%s" stroke-width="%s"' % (_fmt(stroke), s.get("sw", 1))) if stroke else ""
        if s["op"] == "circle":
            out.append('<circle cx="%s" cy="%s" r="%s"%s%s%s/>' %
                       (s["cx"], s["cy"], s["r"], f, st, op))
        elif s["op"] == "ellipse":
            out.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s"%s%s%s/>' %
                       (s["cx"], s["cy"], s["rx"], s["ry"], f, st, op))
        elif s["op"] == "rect":
            out.append('<rect x="%s" y="%s" width="%s" height="%s" rx="%s"%s%s%s/>' %
                       (s["x"], s["y"], s["w"], s["h"], s.get("rx", 0), f, st, op))
        elif s["op"] == "poly":
            pts = " ".join("%s,%s" % p for p in s["pts"])
            out.append('<polygon points="%s"%s%s%s/>' % (pts, f, st, op))
        elif s["op"] == "line":
            out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" '
                       'stroke-width="%s" stroke-linecap="round"%s/>' %
                       (s["x1"], s["y1"], s["x2"], s["y2"],
                        _fmt(s["stroke"]), s.get("sw", 1), op))
    out.append("</svg>")
    return "".join(out)


def pdf_ops(shapes, ox, oy, scale, paper=(255, 255, 255)):
    parts = []

    def emit_path(d, fill, stroke, sw):
        if fill:
            col(fill)
        if stroke:
            col(stroke, True)
            parts.append("%s w" % sw)
        parts.append(d + (" f" if fill and not stroke else
                          " S" if not fill else " B"))

    def blend(c, a):
        if c is None or a >= 0.999:
            return c
        return _mix(paper, c, a)

    def col(c, stroke=False):
        r, g, b = [v / 255.0 for v in c]
        parts.append("%.3f %.3f %.3f %s" % (r, g, b, "RG" if stroke else "rg"))

    def X(x):
        return ox + x * scale

    def Y(y):
        return oy - y * scale

    for s in shapes:
        a = s.get("a", 1.0)
        if a <= 0.01 and not s.get("stroke"):
            continue
        fill = blend(s.get("fill"), a)
        stroke = s.get("stroke")
        sw = max(0.4, s.get("sw", 1) * scale * 0.5)
        if s["op"] == "line":
            col(blend(s["stroke"], a), True)
            parts.append("%s w %s %s m %s %s l S" %
                         (sw, X(s["x1"]), Y(s["y1"]), X(s["x2"]), Y(s["y2"])))
            continue
        if s["op"] in ("circle", "ellipse"):
            cx = X(s["cx"])
            cy = Y(s["cy"])
            if s["op"] == "ellipse":
                rx = s["rx"] * scale
                ry = s["ry"] * scale
            else:
                rx = ry = s["r"] * scale
            k = 0.5523
            pts = [(cx + rx, cy), (cx + rx, cy + k * ry), (cx + k * rx, cy + ry),
                   (cx, cy + ry), (cx - k * rx, cy + ry), (cx - rx, cy + k * ry),
                   (cx - rx, cy), (cx - rx, cy - k * ry), (cx - k * rx, cy - ry),
                   (cx, cy - ry), (cx + k * rx, cy - ry), (cx + rx, cy - k * ry),
                   (cx + rx, cy)]
            d = "%s %s m " % (pts[0][0], pts[0][1])
            for i in range(1, len(pts), 3):
                d += "%s %s %s %s %s %s c " % (pts[i][0], pts[i][1],
                                               pts[i + 1][0], pts[i + 1][1],
                                               pts[i + 2][0], pts[i + 2][1])
            d += "h"
            emit_path(d, fill, stroke, sw)
        elif s["op"] == "poly":
            pts = s["pts"]
            d = "%s %s m " % (X(pts[0][0]), Y(pts[0][1]))
            for p in pts[1:]:
                d += "%s %s l " % (X(p[0]), Y(p[1]))
            d += "h"
            emit_path(d, fill, stroke, sw)
        elif s["op"] == "rect":
            x, wd = min(X(s["x"]), X(s["x"] + s["w"])), abs(s["w"]) * scale
            y, ht = min(Y(s["y"]), Y(s["y"] + s["h"])), abs(s["h"]) * scale
            d = "%s %s %s %s re" % (x, y, wd, ht)
            emit_path(d, fill, stroke, sw)

    return parts


def certificate_svg(token_id, token_hash, codename, username, minted_at, art_svg):
    short = token_hash[:16] + "\u2026" + token_hash[-10:]
    inner = art_svg.replace("<svg ", '<svg x="110" y="120" width="200" height="267" ', 1)
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 560">
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="#141a2e"/><stop offset="1" stop-color="#2a1440"/>
</linearGradient></defs>
<rect x="4" y="4" width="412" height="552" rx="20" fill="url(#bg)" stroke="#c9a227" stroke-width="4"/>
<rect x="16" y="16" width="388" height="528" rx="14" fill="none" stroke="#c9a227" stroke-width="1" opacity="0.6"/>
<text x="210" y="58" text-anchor="middle" font-family="Georgia,serif" font-size="21" fill="#f5d76e">NEURO-SURVEY COLLECTIBLE</text>
<text x="210" y="84" text-anchor="middle" font-family="Courier New,monospace" font-size="13" fill="#9fb3d9">TOKEN #""" + str(token_id) + """</text>
<g>""" + inner + """</g>
<text x="210" y="428" text-anchor="middle" font-family="Georgia,serif" font-size="17" fill="#ffffff" font-style="italic">""" + codename[:38] + """</text>
<text x="210" y="452" text-anchor="middle" font-family="Helvetica,Arial" font-size="12" fill="#9fb3d9">minted for nft name """ + username + """ on """ + str(minted_at) + """</text>
<rect x="40" y="472" width="340" height="34" rx="8" fill="#0b0f1c" stroke="#3d4a6b"/>
<text x="210" y="494" text-anchor="middle" font-family="Courier New,monospace" font-size="11" fill="#7fe3a0">""" + short + """</text>
<text x="210" y="530" text-anchor="middle" font-family="Helvetica,Arial" font-size="10" fill="#5d6f96">SHA-256 bound to answers + nft name - offline-verifiable collectible</text>
</svg>"""
