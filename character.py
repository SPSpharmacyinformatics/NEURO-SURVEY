"""Gamification layer for NEURO-SURVEY: hero aggregation, stats, naming, minting."""

import hashlib
import json
import time

SECTIONS = [
    ("screen", "Mind Trials", "/screen"),
    ("iq", "Intellect Arena", "/iq"),
    ("eq", "Empathy Dojo", "/eq"),
    ("big5", "Personality Forge", "/personality"),
]

STAGES = ["Wisp of Potential", "Awakened Initiate", "Rune-Forged Adept",
          "Storm-Bound Champion", "Ascendant Legend"]

PREFIX = ["Vor", "Kael", "Nyx", "Auren", "Zeph", "Drav", "Sol", "Thal",
          "Orin", "Vex", "Kaz", "Rha", "Mor", "Elar"]
MID = ["a", "ar", "en", "ir", "un", "ys", "oth", "ael", "ion", "ra", "ith"]
SUF = ["rix", "dor", "wyn", "thas", "mir", "zar", "quel", "vane", "storm", "shade"]

TITLE_BY_DOMAIN = {
    "Openness": "the Visionary",
    "Conscientiousness": "the Unyielding",
    "Extraversion": "the Radiant",
    "Agreeableness": "the Kindblade",
    "Emotional Stability": "the Serene",
}

EPITHET_BY_IQ = [
    (130, "Archon of the Ninth Court"),
    (120, "Stormmind of the Quantum Spire"),
    (110, "Sage of the Crystal Hall"),
    (100, "Seeker of Hidden Patterns"),
    (0, "Apprentice of the Endless Ladder"),
]

TITLE_BY_EQ = [
    (60, "Heartflame Warden"),
    (47, "Echo of a Thousand Minds"),
    (32, "Listener at the Gate"),
    (20, "Wanderer of Feelings"),
    (0, "Novice of the Inner Path"),
]


def _clamp(v):
    return max(0, min(100, int(round(v))))


def load_profile(conn, uid):
    prof = {}
    row = conn.execute(
        "SELECT * FROM screens WHERE user_id=? ORDER BY id DESC LIMIT 1", (uid,)).fetchone()
    if row:
        d = dict(row)
        d["results"] = json.loads(d["results"])
        d["flags"] = json.loads(d["flags"])
        prof["screen"] = d
    row = conn.execute(
        "SELECT * FROM iq_results WHERE user_id=? ORDER BY id DESC LIMIT 1", (uid,)).fetchone()
    if row:
        d = dict(row)
        d["domains"] = json.loads(d["domains"])
        prof["iq"] = d
    row = conn.execute(
        "SELECT * FROM eq_results WHERE user_id=? ORDER BY id DESC LIMIT 1", (uid,)).fetchone()
    if row:
        d = dict(row)
        d["subscales"] = json.loads(d["subscales"])
        prof["eq"] = d
    row = conn.execute(
        "SELECT * FROM personality_results WHERE user_id=? ORDER BY id DESC LIMIT 1", (uid,)).fetchone()
    if row:
        d = dict(row)
        d["domains"] = json.loads(d["domains"])
        prof["big5"] = d
    return prof


def completion(prof):
    return sum(1 for key, _t, _u in SECTIONS if key in prof)


def stage_of(done):
    return STAGES[max(0, min(done, 4))]


def stats(prof):
    st = {}
    iq = prof.get("iq")
    if iq and iq.get("standard_score") is not None:
        st["Intellect"] = _clamp((iq["standard_score"] - 55) / 0.9)
    eq = prof.get("eq")
    if eq and eq.get("total") is not None:
        st["Empathy"] = _clamp(eq["total"] / 70.0 * 100)
    b5 = prof.get("big5", {}).get("domains")
    if b5:
        st["Resolve"] = _clamp(b5["Conscientiousness"]["score"])
        st["Serenity"] = _clamp(b5["Emotional Stability"]["score"])
        st["Chaos"] = _clamp(b5["Openness"]["score"])
        st["Heart"] = _clamp(b5["Agreeableness"]["score"])
        st["Radiance"] = _clamp(b5["Extraversion"]["score"])
    return st


def dominant_domain(prof):
    b5 = prof.get("big5", {}).get("domains")
    if not b5:
        return None
    return max(b5, key=lambda k: b5[k]["score"])


def power_level(done, st):
    base = done * 90
    mean_stat = (sum(st.values()) / len(st)) if st else 0
    return int(base + mean_stat * 2.2)


def codename(username, prof):
    h = hashlib.sha256(("hero:" + username).encode()).digest()
    name = PREFIX[h[0] % len(PREFIX)] + MID[h[1] % len(MID)] + SUF[h[2] % len(SUF)]
    dom = dominant_domain(prof)
    title = TITLE_BY_DOMAIN.get(dom) if dom else None
    if not title:
        eq = prof.get("eq", {}).get("total") or 0
        title = next(t for floor, t in TITLE_BY_EQ if eq >= floor)
    iq = prof.get("iq", {}).get("standard_score") or 0
    epithet = next(e for floor, e in EPITHET_BY_IQ if iq >= floor)
    marks = len(prof.get("screen", {}).get("flags") or [])
    suffix = f"; Bearer of {marks} Marks" if marks else ""
    return f"{name} {title}, {epithet}{suffix}"


def fingerprint(username, prof):
    canon = {"user": username.lower()}
    for key in ("screen", "iq", "eq", "big5"):
        if key in prof:
            canon[key] = prof[key].get("id")
    return hashlib.sha256(json.dumps(canon, sort_keys=True).encode()).hexdigest()


def ensure_table(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS heroes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            codename TEXT, token_hash TEXT,
            minted_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()


def get_mint(conn, uid):
    ensure_table(conn)
    row = conn.execute("SELECT * FROM heroes WHERE user_id=?", (uid,)).fetchone()
    return dict(row) if row else None


def mint(conn, uid, username, prof):
    existing = get_mint(conn, uid)
    if existing:
        return existing, False
    ensure_table(conn)
    nxt = conn.execute("SELECT COALESCE(MAX(id),0)+1 AS n FROM heroes").fetchone()["n"]
    tok = hashlib.sha256(
        f"{fingerprint(username, prof)}|{username}|{nxt}|{time.time()}".encode()
    ).hexdigest()
    conn.execute("INSERT INTO heroes(user_id, codename, token_hash) VALUES(?,?,?)",
                 (uid, codename(username, prof), tok))
    conn.commit()
    return get_mint(conn, uid), True


def hero_state(conn, uid, username):
    prof = load_profile(conn, uid)
    done = completion(prof)
    st = stats(prof)
    state = {
        "profile": prof,
        "done": done,
        "total_sections": len(SECTIONS),
        "complete": done >= len(SECTIONS),
        "stage": stage_of(done),
        "stats": st,
        "power": power_level(done, st),
        "codename": codename(username, prof),
        "dominant": dominant_domain(prof),
        "minted": get_mint(conn, uid),
        "fingerprint": fingerprint(username, prof),
    }
    return state
