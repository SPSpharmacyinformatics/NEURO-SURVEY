import io
import json
import os
import sqlite3

from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, Response, send_file)

from correlations import combined_insights
from instruments import (SCREEN_SECTIONS, score_instrument, QUESTIONS,
                         classify_profile)
import iq_eq
import personality
import character
import dossier

app = Flask(__name__)
app.secret_key = os.environ.get("NEURO_SECRET", "neuro-survey-local-key")

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'neuro_survey.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS responses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            age INTEGER, gender TEXT, scores TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS screens(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            age INTEGER, gender TEXT, results TEXT NOT NULL,
            flags TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS iq_results(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            age INTEGER, standard_score INTEGER, domains TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS eq_results(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            age INTEGER, total INTEGER, subscales TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS personality_results(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            age INTEGER, domains TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS heroes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            codename TEXT, token_hash TEXT,
            minted_at DATETIME DEFAULT CURRENT_TIMESTAMP);
    """)
    for table in ("responses", "screens", "iq_results", "eq_results", "personality_results"):
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()


def current_user():
    uid = session.get("uid")
    name = session.get("username")
    if not uid or not name:
        return None
    return {"id": uid, "username": name}


def require_login():
    if not current_user():
        return redirect(url_for("login", next=request.path))
    return None


# ---------------- auth ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    nxt = request.args.get('next') or request.form.get('next') or url_for('index')
    if not nxt.startswith('/'):
        nxt = url_for('index')
    if request.method == 'POST':
        username = (request.form.get('username') or "").strip()
        if not (3 <= len(username) <= 20) or not all(c.isalnum() or c == '_' for c in username):
            return render_template('login.html', error="Username must be 3-20 letters, digits or underscores.",
                                   next=nxt)
        conn = get_db()
        row = conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
        if row:
            uid = row["id"]
            flash_msg = f"Welcome back, {username}!"
        else:
            cur = conn.execute("INSERT INTO users(username) VALUES(?)", (username,))
            uid = cur.lastrowid
            flash_msg = f"Welcome aboard, {username}! Fresh journey started."
        conn.commit()
        conn.close()
        session["uid"] = uid
        session["username"] = username
        session["just_logged_in"] = flash_msg
        return redirect(nxt)
    return render_template('login.html', next=nxt)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# ---------------- home ----------------
@app.route('/')
def index():
    return render_template('assess.html', user=current_user(),
                           banner=session.pop("just_logged_in", None))


# ---------------- dashboard ----------------
@app.route('/dashboard')
def dashboard():
    gate = require_login()
    if gate:
        return gate
    user = current_user()
    conn = get_db()
    uid = user["id"]

    iq_rows = conn.execute("SELECT * FROM iq_results WHERE user_id=? ORDER BY id DESC LIMIT 10",
                           (uid,)).fetchall()
    eq_rows = conn.execute("SELECT * FROM eq_results WHERE user_id=? ORDER BY id DESC LIMIT 10",
                           (uid,)).fetchall()
    scr_rows = conn.execute("SELECT * FROM screens WHERE user_id=? ORDER BY id DESC LIMIT 10",
                            (uid,)).fetchall()
    p5_rows = conn.execute("SELECT * FROM personality_results WHERE user_id=? ORDER BY id DESC LIMIT 10",
                           (uid,)).fetchall()
    p5_latest = None
    if p5_rows:
        d = dict(p5_rows[0])
        d["domains"] = json.loads(d["domains"])
        p5_latest = d
    map_rows = conn.execute("SELECT * FROM responses WHERE user_id=? ORDER BY id DESC LIMIT 10",
                            (uid,)).fetchall()
    conn.close()

    iq_latest = None
    if iq_rows:
        d = dict(iq_rows[0])
        d["domains"] = json.loads(d["domains"])
        iq_latest = d
    eq_latest = None
    if eq_rows:
        d = dict(eq_rows[0])
        d["subscales"] = json.loads(d["subscales"])
        eq_latest = d
    scr_latest = None
    scr_flags = []
    scr_domains = []
    if scr_rows:
        d = dict(scr_rows[0])
        results = json.loads(d["results"])
        flags = json.loads(d["flags"])
        for f in flags:
            name = f[0] if isinstance(f, (list, tuple)) else f
            scr_flags.append(str(name).replace("&amp;", "&"))
        for section, r in zip(SCREEN_SECTIONS, results):
            if r:
                scr_domains.append((section["title"], r.get("band", ""),
                                    r.get("score", 0), r.get("max", 0)))
        scr_latest = d
    map_latest = None
    map_scores = {}
    if map_rows:
        d = dict(map_rows[0])
        map_scores = json.loads(d["scores"])
        map_latest = d

    insights = combined_insights(
        iq=iq_latest,
        eq={"total": eq_latest["total"], "max": 70, "subscales": eq_latest["subscales"]} if eq_latest else None,
        screen={"flags": scr_flags, "domains": scr_domains} if scr_rows else None,
        maps={"scores": map_scores} if map_rows else None,
    )

    return render_template('dashboard.html', user=user,
                           iq=iq_latest, iq_hist=iq_rows,
                           eq=eq_latest, eq_hist=eq_rows,
                           screen=scr_latest, screen_flags=scr_flags,
                           screen_domains=scr_domains, screen_hist=scr_rows,
                           map_latest=map_latest, map_hist=map_rows,
                           map_scores=map_scores,
                           big5=p5_latest, big5_hist=p5_rows,
                           insights=insights)


# ---------------- original quick map ----------------
@app.route('/quick-map')
def quick_map():
    gate = require_login()
    return gate or render_template('index.html')


@app.route('/survey', methods=['POST'])
def survey():
    gate = require_login()
    if gate:
        return gate
    return render_template('survey.html',
                           name=current_user()["username"],
                           age=request.form.get('age', ''),
                           gender=request.form.get('gender', ''),
                           questions=QUESTIONS)


@app.route('/submit', methods=['POST'])
def submit():
    gate = require_login()
    if gate:
        return gate
    age = request.form.get('age', '')
    scores = {}
    for key in QUESTIONS:
        try:
            scores[key] = max(0, min(8, int(request.form.get(key, 2))))
        except (TypeError, ValueError):
            scores[key] = 2
    ordered = [scores[k] for k in QUESTIONS]
    title, desc = classify_profile(ordered)
    conn = get_db()
    conn.execute("INSERT INTO responses(user_id, age, gender, scores) VALUES(?,?,?,?)",
                 (current_user()["id"],
                  int(age) if str(age).isdigit() else None,
                  request.form.get('gender', ''), json.dumps(scores)))
    conn.commit()
    conn.close()
    return render_template('results.html', name=current_user()["username"], age=age,
                           profile_title=title, profile_desc=desc,
                           labels=list(QUESTIONS.keys()), scores=ordered)


@app.route('/world-view')
def world_view():
    conn = get_db()
    rows = conn.execute("SELECT scores FROM responses").fetchall()
    conn.close()
    total = len(rows)
    if total == 0:
        avg = [2] * len(QUESTIONS)
    else:
        sums = [0] * len(QUESTIONS)
        for r in rows:
            data = json.loads(r['scores'])
            for i, key in enumerate(QUESTIONS):
                sums[i] += data.get(key, 2)
        avg = [round(s / total, 2) for s in sums]
    return render_template('world_view.html', total=total,
                           labels=list(QUESTIONS.keys()), avg_scores=avg)


# ---------------- linear clinical screen ----------------
@app.route('/screen', methods=['GET', 'POST'])
def screen_start():
    gate = require_login()
    if gate:
        return gate
    if request.method == 'POST':
        session['screen_identity'] = {
            'age': request.form.get('age', ''),
            'gender': request.form.get('gender', ''),
        }
        session['screen_data'] = {}
        return redirect(url_for('screen_section', idx=0))
    return render_template('screen_start.html', total=len(SCREEN_SECTIONS))


@app.route('/screen/<int:idx>', methods=['GET'])
def screen_section(idx):
    gate = require_login()
    if gate:
        return gate
    if 'screen_data' not in session:
        return redirect(url_for('screen_start'))
    if idx >= len(SCREEN_SECTIONS):
        return redirect(url_for('screen_finish'))
    return render_template('screen_section.html',
                           section=SCREEN_SECTIONS[idx], idx=idx,
                           total=len(SCREEN_SECTIONS))


@app.route('/screen/<int:idx>/next', methods=['POST'])
def screen_next(idx):
    gate = require_login()
    if gate:
        return gate
    section = SCREEN_SECTIONS[idx]
    session['screen_data'][str(idx)] = score_instrument(section, request.form)
    session.modified = True
    if idx + 1 >= len(SCREEN_SECTIONS):
        return redirect(url_for('screen_finish'))
    return redirect(url_for('screen_section', idx=idx + 1))


@app.route('/screen/finish')
def screen_finish():
    gate = require_login()
    if gate:
        return gate
    data = session.get('screen_data')
    ident = session.get('screen_identity', {})
    if data is None:
        return redirect(url_for('screen_start'))
    results = [data.get(str(i)) for i in range(len(SCREEN_SECTIONS))]
    flags = [(SCREEN_SECTIONS[i]['title'], SCREEN_SECTIONS[i]['instrument'])
             for i, r in enumerate(results) if r and r.get('flag')]
    conn = get_db()
    age = ident.get('age', '')
    conn.execute("INSERT INTO screens(user_id, age, gender, results, flags) VALUES(?,?,?,?,?)",
                 (current_user()["id"],
                  int(age) if str(age).isdigit() else None,
                  ident.get('gender', ''), json.dumps(results),
                  json.dumps(flags)))
    conn.commit()
    conn.close()
    session.pop('screen_data', None)
    session.pop('screen_identity', None)
    return render_template('screen_result.html', sections=SCREEN_SECTIONS,
                           results=results, flags=flags,
                           pairs=list(zip(SCREEN_SECTIONS, results)))


# ---------------- IQ (CHC) ----------------
@app.route('/iq')
def iq_intro():
    gate = require_login()
    return gate or render_template('iq_intro.html', domains=iq_eq.IQ_DOMAINS,
                                   minutes=12)


@app.route('/iq/test')
def iq_test():
    gate = require_login()
    return gate or render_template('iq_test.html', items=iq_eq.iq_domain_items(),
                                   digit=iq_eq.DIGIT_SPAN,
                                   symbols=iq_eq.SYMBOL_SEARCH_SECONDS)


@app.route('/iq/result', methods=['POST'])
def iq_result():
    gate = require_login()
    if gate:
        return gate
    data = request.get_json(force=True)
    correct = data.get('correct', {})
    digits = int(data.get('digits') or 0)
    symbols = int(data.get('symbols') or 0)

    domain_scores = {"Gf": [0, 0], "Gc": [0, 0], "Gv": [0, 0], "Gq": [0, 0]}
    for key, ok in correct.items():
        dom = key.split(':')[0]
        if dom in domain_scores:
            domain_scores[dom][1] += 1
            if ok:
                domain_scores[dom][0] += 1

    fracs = {}
    for dom, (got, tot) in domain_scores.items():
        fracs[dom] = (got / tot) if tot else 0
    fracs["Gwm"] = min(1.0, digits / 9.0)
    fracs["Gs"] = min(1.0, symbols / 30.0)

    weights = {"Gf": 0.3, "Gc": 0.2, "Gwm": 0.2, "Gv": 0.15, "Gq": 0.1, "Gs": 0.05}
    overall_frac = sum(fracs[d] * w for d, w in weights.items())
    iq = iq_eq.standard_score(overall_frac)

    domains_out = {d: {"standard": iq_eq.standard_score(f), "band": iq_eq.iq_band(iq_eq.standard_score(f))}
                   for d, f in fracs.items()}
    age = data.get('age')
    conn = get_db()
    conn.execute("INSERT INTO iq_results(user_id, age, standard_score, domains) VALUES(?,?,?,?)",
                 (current_user()["id"],
                  int(age) if str(age or '').isdigit() else None, iq,
                  json.dumps(domains_out)))
    conn.commit()
    conn.close()
    return render_template('iq_result.html', iq=iq, band=iq_eq.iq_band(iq),
                           domains=domains_out)


# ---------------- Personality (IPIP Big-Five) ----------------
@app.route('/personality')
def personality_intro():
    gate = require_login()
    return gate or render_template('personality_intro.html',
                                   citation=personality.CITATION,
                                   n_items=len(personality.ITEMS))


@app.route('/personality/test')
def personality_test():
    gate = require_login()
    return gate or render_template('personality_test.html',
                                   items=personality.ITEMS,
                                   scale=personality.SCALE)


@app.route('/personality/result', methods=['POST'])
def personality_result():
    gate = require_login()
    if gate:
        return gate
    answers = [request.form.get(f'big5_{i}') for i in range(len(personality.ITEMS))]
    if not personality.validate_complete(answers):
        return redirect(url_for('personality_test'))

    scores = personality.score(answers)
    label = personality.profile_label(scores)
    age = request.form.get('age')
    conn = get_db()
    conn.execute("INSERT INTO personality_results(user_id, age, domains) VALUES(?,?,?)",
                 (current_user()["id"],
                  int(age) if str(age or '').isdigit() else None,
                  json.dumps(scores)))
    conn.commit()
    conn.close()
    return render_template('personality_result.html',
                           scores=scores, domains=personality.DOMAINS,
                           interp=personality.INTERPRETATION, label=label,
                           citation=personality.CITATION)


# ---------------- EQ ----------------
@app.route('/eq')
def eq_intro():
    gate = require_login()
    return gate or render_template('eq_intro.html')


@app.route('/eq/test')
def eq_test():
    gate = require_login()
    return gate or render_template('eq_test.html', items=iq_eq.EQ_ITEMS,
                                   scale=iq_eq.EQ_SCALE)


@app.route('/eq/result', methods=['POST'])
def eq_result():
    gate = require_login()
    if gate:
        return gate
    total, subs, subsmax = iq_eq.score_eq(request.form)
    total_max = sum(subsmax.values())
    age = request.form.get('age', '')
    conn = get_db()
    conn.execute("INSERT INTO eq_results(user_id, age, total, subscales) VALUES(?,?,?,?)",
                 (current_user()["id"],
                  int(age) if age.isdigit() else None, total, json.dumps(subs)))
    conn.commit()
    conn.close()
    return render_template('eq_result.html', total=total, total_max=total_max,
                           band=iq_eq.eq_band(total), subs=subs, subsmax=subsmax)


# ---------------- hero (gamified character) ----------------
def _hero_context():
    user = current_user()
    conn = get_db()
    state = character.hero_state(conn, user["id"], user["username"])
    conn.close()
    return user, state


@app.route('/character')
def hero_page():
    gate = require_login()
    if gate:
        return gate
    user, state = _hero_context()
    return render_template('character.html', user=user,
                           sections=character.SECTIONS, **state)


@app.route('/character.svg')
def hero_svg():
    gate = require_login()
    if gate:
        return gate
    import charart
    user, state = _hero_context()
    shapes = charart.build(state["done"], state["stats"], state["dominant"],
                           int(state["fingerprint"][:12], 16) % 10**9)
    return Response(charart.render_svg(shapes), mimetype='image/svg+xml')


@app.route('/nft')
def nft_page():
    gate = require_login()
    if gate:
        return gate
    import charart
    user, state = _hero_context()
    cert_svg = None
    if state["minted"]:
        m = state["minted"]
        shapes = charart.build(state["done"], state["stats"], state["dominant"],
                               int(m["token_hash"][:12], 16) % 10**9)
        art_svg = charart.render_svg(shapes)
        cert_svg = charart.certificate_svg(m["id"], m["token_hash"],
                                           state["codename"], user["username"],
                                           m["minted_at"], art_svg)
    return render_template('nft.html', user=user, mint=state["minted"],
                           complete=state["complete"], cert_svg=cert_svg,
                           codename=state["codename"])


@app.route('/nft.svg')
def nft_svg():
    gate = require_login()
    if gate:
        return gate
    import charart
    user, state = _hero_context()
    m = state.get("minted")
    if not m:
        return redirect(url_for('nft_page'))
    shapes = charart.build(state["done"], state["stats"], state["dominant"],
                           int(m["token_hash"][:12], 16) % 10**9)
    art_svg = charart.render_svg(shapes)
    svg = charart.certificate_svg(m["id"], m["token_hash"], state["codename"],
                                  user["username"], m["minted_at"], art_svg)
    dl = request.args.get('dl')
    return Response(svg, mimetype='image/svg+xml',
                    headers={} if not dl else {
                        "Content-Disposition":
                        f'attachment; filename="neuro-token-{m["id"]}.svg"'})


@app.route('/nft/mint', methods=['POST'])
def nft_mint():
    gate = require_login()
    if gate:
        return gate
    user, state = _hero_context()
    if not state["complete"]:
        flash("Complete all four sections before minting your collectible.")
        return redirect(url_for('hero_page'))
    conn = get_db()
    row, fresh = character.mint(conn, user["id"], user["username"], state["profile"])
    conn.close()
    flash("Minted TOKEN #%d just for you!" % row["id"] if fresh
          else "Your collectible was already minted as TOKEN #%d." % row["id"])
    return redirect(url_for('nft_page'))


@app.route('/report.pdf')
def report_pdf():
    gate = require_login()
    if gate:
        return gate
    user, state = _hero_context()
    if not state["complete"]:
        flash("Finish all four sections to unlock your PDF dossier.")
        return redirect(url_for('hero_page'))
    data = dossier.build_dossier(user["username"], state)
    return send_file(io.BytesIO(data), mimetype='application/pdf',
                     as_attachment=True,
                     download_name=f"neuro_dossier_{user['username']}.pdf")


@app.route('/certificate.pdf')
def certificate_pdf():
    gate = require_login()
    if gate:
        return gate
    user, state = _hero_context()
    m = state.get("minted")
    if not m:
        return redirect(url_for('nft_page'))
    data = dossier.build_certificate_pdf(user["username"], state, m)
    return send_file(io.BytesIO(data), mimetype='application/pdf',
                     as_attachment=True,
                     download_name=f"neuro_token_{m['id']}_{user['username']}.pdf")


BASE_URL = "https://survey.sps.dpdns.org"

CRAWLABLE_ROUTES = ["/", "/quick-map", "/world-view",
                    "/screen", "/iq", "/eq", "/personality"]


@app.route('/robots.txt')
def robots():
    return Response(
        "User-agent: *\n"
        "Allow: /\n"
        f"Sitemap: {BASE_URL}/sitemap.xml\n",
        mimetype='text/plain')


@app.route('/sitemap.xml')
def sitemap():
    urls = "\n".join(
        f"  <url><loc>{BASE_URL}{path}</loc></url>" for path in CRAWLABLE_ROUTES)
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           f"{urls}\n"
           "</urlset>\n")
    return Response(xml, mimetype='application/xml')


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)
