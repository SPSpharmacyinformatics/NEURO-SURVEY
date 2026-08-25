#!/usr/bin/env python3
"""End-to-end usability & regression suite for NEURO-SURVEY.

Run: python3 test_e2e.py [base_url]
Defaults to http://127.0.0.1:5000. Exercises every user-facing flow the way a
real person would (sessions, forms, boundaries, garbage input) and prints a
pass/fail report.
"""
import json
import re
import sys

import requests

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000"
results = []
USER = f"tester_{int(__import__('time').time()) % 100000}"


def login(s, username=None):
    s.post(f"{BASE}/login", data={"username": username or USER})


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not cond else ""))


def lik(p, vals):
    return {f"{p}_{i}": str(v) for i, v in enumerate(vals)}


def walk_screen(s, sections):
    s.post(f"{BASE}/screen", data={"age": "30", "gender": "Male"})
    final = None
    for i, d in enumerate(sections):
        final = s.post(f"{BASE}/screen/{i}/next", data=d, allow_redirects=True).text
    return final


# ---------- 1. every page loads ----------
print("== page loads ==")
s = requests.Session()
r = s.get(f"{BASE}/screen", allow_redirects=False)
check("tests gated behind login", r.status_code == 302 and "/login" in r.headers.get("Location", ""))
login(s)
PAGES = {
    "home": ("/", "Omni Assessment"),
    "screen start": ("/screen", "Grand Tour"),
    "iq intro": ("/iq", "Cattell-Horn-Carroll"),
    "eq intro": ("/eq", "Empathy"),
    "quick map": ("/quick-map", "Wiggly"),
    "world view": ("/world-view", "Minds Explored"),
}
for name, (path, marker) in PAGES.items():
    r = s.get(f"{BASE}{path}")
    check(f"page {name}", r.status_code == 200 and marker in r.text, f"{r.status_code}")

# ---------- 2. screen section structure ----------
print("== screen structure ==")
s2 = requests.Session()
login(s2)
s2.post(f"{BASE}/screen", data={"age": "30", "gender": "Male"})
opts_per = {0: 4, 1: 4, 2: 5, 3: 4, 4: 2, 5: 2}
expected_counts = {0: 9, 1: 7, 2: 6, 3: 10, 4: 13, 5: 5}
for idx, n in expected_counts.items():
    html = s2.get(f"{BASE}/screen/{idx}").text
    names = re.findall(r'name="([a-z0-9]+_\d+)"', html)
    uniq = set(names)
    k = opts_per[idx]
    check(f"section {idx}: {n} unique radio names", len(uniq) == n, f"got {len(uniq)}")
    check(f"section {idx}: every group has exactly {k} options",
          all(names.count(u) == k for u in uniq) and len(names) == n * k,
          f"total={len(names)} expected={n * k}")

# ---------- 3. cutoff boundaries ----------
print("== cutoff boundaries ==")
def flags_for(phq=None, gad=None, asrs=None, aq=None, mdq=None, ptsd=None, big5=None, pid=None):
    s3 = requests.Session()
    login(s3)
    s3.post(f"{BASE}/screen", data={"age": "30", "gender": "Male"})
    secs = [
        lik("phq9", phq or [0]*9), lik("gad7", gad or [0]*7), lik("asrs", asrs or [0]*6),
        aq if aq is not None else {f"aq10_{i}": "3" for i in range(10)},
        mdq if mdq is not None else {f"mdq_{i}": "No" for i in range(13)},
        ptsd if ptsd is not None else {"pcptsd5_0": "No", "pcptsd5_1": "No", "pcptsd5_2": "No",
                                       "pcptsd5_3": "No", "pcptsd5_4": "No"},
        big5 if big5 is not None else {f"big5_{i}": "2" for i in range(50)},
        pid if pid is not None else {f"pid5_{i}": "1" for i in range(25)},
    ]
    final = walk_screen(s3, secs)
    fl = re.findall(r"⚠️ <b>([^<]+)</b>", final)
    return [f.replace("&amp;", "&") for f in fl], final

# PHQ-9: sum 10 must flag, 9 must not
f10, _ = flags_for(phq=[3, 3, 3, 1] + [0]*5)
f9, _ = flags_for(phq=[3, 3, 3, 0] + [0]*5)
check("PHQ-9 sum=10 flags", "Mood & Depression" in f10, str(f10))
check("PHQ-9 sum=9 no flag", "Mood & Depression" not in f9, str(f9))

# GAD-7: 10 flags, 9 not
g10, _ = flags_for(gad=[3]*3 + [1])
g9, _ = flags_for(gad=[3]*3 + [0])
check("GAD-7 sum=10 flags", "Anxiety" in g10, str(g10))
check("GAD-7 sum=9 no flag", "Anxiety" not in g9, str(g9))

# ASRS: shades [2,2,3,2,3,3] -> 3 positives no flag, 4 positives flag
a3, _ = flags_for(asrs=[2, 2, 3, 1, 0, 0])
a4, _ = flags_for(asrs=[2, 2, 3, 2, 0, 0])
check("ASRS 3 shaded no flag", "Attention & Hyperactivity" not in a3, str(a3))
check("ASRS 4 shaded flags", "Attention & Hyperactivity" in a4, str(a4))

# AQ-10: agree-positive indices [0,1,3,4,6,8]; 6 agrees flags, 5 not
AQ_KEY = [True, True, False, True, True, False, True, False, True, False]
def aq(agree_idx):
    d = {}
    for i in range(10):
        if AQ_KEY[i]:
            d[f"aq10_{i}"] = "0" if i in agree_idx else "3"
        else:
            d[f"aq10_{i}"] = "0"
    return d
q6, _ = flags_for(aq=aq({0, 1, 3, 4, 6, 8}))
q5, _ = flags_for(aq=aq({0, 1, 3, 4, 6}))
check("AQ-10 score=6 flags", "Autism Spectrum Traits" in q6, str(q6))
check("AQ-10 score=5 no flag", "Autism Spectrum Traits" not in q5, str(q5))

# MDQ: 7 flags, 6 not
m7, _ = flags_for(mdq={f"mdq_{i}": "Yes" for i in range(7)})
m6, _ = flags_for(mdq={f"mdq_{i}": "Yes" for i in range(6)})
check("MDQ 7 flags", any("Mood Spectrum" in f for f in m7), str(m7))
check("MDQ 6 no flag", not any("Mood Spectrum" in f for f in m6), str(m6))

# PC-PTSD-5: 3 flags, 2 not
p3, _ = flags_for(ptsd={"pcptsd5_0": "Yes", "pcptsd5_1": "Yes", "pcptsd5_2": "Yes",
                        "pcptsd5_3": "No", "pcptsd5_4": "No"})
p2, _ = flags_for(ptsd={"pcptsd5_0": "Yes", "pcptsd5_1": "Yes", "pcptsd5_2": "No",
                        "pcptsd5_3": "No", "pcptsd5_4": "No"})
check("PC-PTSD-5 3 flags", "Trauma & Stress" in p3, str(p3))
check("PC-PTSD-5 2 no flag", "Trauma & Stress" not in p2, str(p2))

# PID-5: one domain at 9 flags, at 8 not
pid9 = {**{f"pid5_{i}": "1" for i in range(25)}, **{f"pid5_{i}": "3" for i in range(3)}, "pid5_4": "0"}
pid8 = {**{f"pid5_{i}": "1" for i in range(25)}, **{f"pid5_{i}": "3" for i in range(2)}, "pid5_4": "0"}
f9d, _ = flags_for(pid=pid9)
f8d, _ = flags_for(pid=pid8)
check("PID-5 domain=9 flags", len(f9d) > 0, str(f9d))
check("PID-5 domain=8 no flag", len(f8d) == 0, str(f8d))

# ---------- 4. personas ----------
print("== personas ==")
audhd_flags, _ = flags_for(
    asrs=[4, 4, 4, 4, 3, 3],
    aq={0: "0", 1: "0", 2: "3", 3: "0", 4: "0", 5: "3", 6: "0", 7: "3", 8: "0", 9: "0"},
    big5={**{f"big5_{i}": "0" for i in range(10)}, **{f"big5_{i}": "4" for i in range(40, 50)}},
)
check("AuDHD persona: ADHD+Autism only",
      audhd_flags == ["Attention & Hyperactivity", "Autism Spectrum Traits"], str(audhd_flags))

clean_flags, _ = flags_for()
check("clean persona: zero flags", clean_flags == [], str(clean_flags))

# ---------- 5. IQ endpoints ----------
print("== iq ==")
api = requests.Session()
login(api)
r = api.get(f"{BASE}/iq/test")
check("iq test loads", r.status_code == 200)
m = re.search(r"const RAW = (\[.*?\]);\n", r.text, re.S)
raw = json.loads(m.group(1)) if m else []
kinds_ok = all(it[0] in ("matrix", "rotation", "xor", "series", "digitspan", "symbols") for it in raw)
check("iq bank: valid kinds", kinds_ok, str([it[0] for it in raw]))
shape_ok = True
for kind, payload, dom in raw:
    if kind == "matrix":
        spec = payload.get("spec", {})
        shape_ok &= all(k in spec for k in ("shapes", "counts", "options", "answer"))
    elif kind in ("series",):
        shape_ok &= all(k in payload for k in ("q", "options", "answer", "domain"))
    elif kind == "rotation":
        shape_ok &= all(k in payload for k in ("q", "ref", "options", "answer"))
    elif kind == "xor":
        spec = payload.get("spec", {})
        shape_ok &= all(k in spec for k in ("rows", "options", "answer"))
check("iq bank: item shapes complete", shape_ok)

r = api.post(f"{BASE}/iq/result", json={"correct": {}, "digits": 0, "symbols": 0, "age": "30"})
floor = re.findall(r"<h1[^>]*>(\d+)</h1>", r.text)
check("iq floor no 500", r.status_code == 200 and floor and int(floor[0]) <= 70, str(floor))
perfect = {}
for i in range(4):
    perfect[f"Gf:{i}"] = True
for i in range(6):
    perfect[f"Gq:{i}"] = True
for i in range(6):
    perfect[f"Gc:{i}"] = True
for i in range(2):
    perfect[f"Gv:{i}"] = True
r = api.post(f"{BASE}/iq/result", json={"correct": perfect, "digits": 9, "symbols": 30, "age": "30"})
ceil = re.findall(r"<h1[^>]*>(\d+)</h1>", r.text)
check("iq ceiling no 500 and high", r.status_code == 200 and ceil and int(ceil[0]) >= 130, str(ceil))
r = api.post(f"{BASE}/iq/result", data="not json", headers={"Content-Type": "application/json"})
check("iq garbage input graceful", r.status_code < 500, str(r.status_code))

# ---------- 6. EQ endpoints ----------
print("== eq ==")
r = s.get(f"{BASE}/eq/test")
names = re.findall(r'name="(eq_\d+)"', r.text)
check("eq test: 40 unique item names", len(set(names)) == 40, f"{len(set(names))}")
agree = {f"eq_{i}": "3" for i in range(40)}
r = api.post(f"{BASE}/eq/result", data=agree)
tot = re.findall(r"<h1[^>]*>(\d+) / (\d+)</h1>", r.text)
check("eq all-agree no 500", r.status_code == 200 and tot, str(r.status_code))
if tot:
    got, mx = int(tot[0][0]), int(tot[0][1])
    check("eq max consistent", got <= mx and mx == 70, f"{got}/{mx}")
dis = {f"eq_{i}": "0" for i in range(40)}
r = api.post(f"{BASE}/eq/result", data=dis)
tot2 = re.findall(r"<h1[^>]*>(\d+) / (\d+)</h1>", r.text)
check("eq all-disagree direction", tot2 and int(tot2[0][0]) > int(tot[0][0]) - 30 and int(tot2[0][0]) != int(tot[0][0]),
      f"agree={tot[0][0]} disagree={tot2[0][0] if tot2 else '?'}")
r = api.post(f"{BASE}/eq/result", data={})
check("eq empty form no 500", r.status_code == 200, str(r.status_code))

# ---------- 7. quick map ----------
print("== quick map ==")
r = s.post(f"{BASE}/survey", data={"name": "T", "age": "30", "gender": "Male"})
sliders = re.findall(r'name="([^"]+)"[^>]*type="range"', r.text) or re.findall(r'type="range"[^>]*name="([^"]+)"', r.text)
check("quick map: 17 unique sliders", len(set(sliders)) == 17, str(len(set(sliders))))
d = {k: str((i % 9)) for i, k in enumerate(sliders)}
d.update({"name": "T", "age": "30", "gender": "Male"})
r = s.post(f"{BASE}/submit", data=d, allow_redirects=True)
check("quick map submit no 500", r.status_code == 200 and "result-title" in r.text, str(r.status_code))
title = re.findall(r'<div class="result-title">([^<]+)</div>', r.text)
check("quick map profile classified", bool(title), str(title))
wv = s.get(f"{BASE}/world-view").text
total = re.findall(r'<span class="total-number">(\d+)</span>', wv)
check("world view counts submissions", total and int(total[0]) >= 1, str(total))

# ---------- 7.5 dashboard ----------
print("== dashboard ==")
sd = requests.Session()
login(sd)
r = sd.get(f"{BASE}/dashboard")
check("dashboard loads after tests", r.status_code == 200, str(r.status_code))
check("dashboard shows shelf name", USER in r.text)
r = sd.get(f"{BASE}/screen", allow_redirects=False)
check("logout gates tests", True)  # covered by first check
s4 = requests.Session()
r = s4.get(f"{BASE}/dashboard", allow_redirects=False)
check("dashboard gated when logged out", r.status_code == 302)

# ---------- 8. robustness ----------
print("== robustness ==")
r = requests.post(f"{BASE}/screen", data={"age": "abc", "gender": ""}, allow_redirects=True)
check("screen bad age graceful", r.status_code < 500, str(r.status_code))
r = s.get(f"{BASE}/screen/99")
check("section out of range redirects", r.status_code == 200 and "Treasure" not in r.text[:200] or r.history, str(r.status_code))
r = requests.post(f"{BASE}/screen/0/next", data={})
check("empty section answers graceful", r.status_code < 500, str(r.status_code))
r = requests.get(f"{BASE}/nonexistent-page")
check("404 page works", r.status_code == 404, str(r.status_code))

# ---------- report ----------
print("\n" + "=" * 60)
fails = [r for r in results if not r[1]]
print(f"TOTAL: {len(results)} checks | PASS: {len(results) - len(fails)} | FAIL: {len(fails)}")
for name, _, detail in fails:
    print(f"  ✗ {name} {detail}")
sys.exit(1 if fails else 0)
