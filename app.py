import json
import os
import sqlite3

from flask import (Flask, render_template, request, redirect, url_for,
                   session)

from instruments import (SCREEN_SECTIONS, score_instrument, QUESTIONS,
                         classify_profile)
import iq_eq

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
        CREATE TABLE IF NOT EXISTS responses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            age INTEGER, gender TEXT, scores TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS screens(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            age INTEGER, gender TEXT, results TEXT NOT NULL,
            flags TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS iq_results(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            age INTEGER, standard_score INTEGER, domains TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS eq_results(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            age INTEGER, total INTEGER, subscales TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
    """)
    conn.commit()
    conn.close()


# ---------------- home ----------------
@app.route('/')
def index():
    return render_template('assess.html')


# ---------------- original quick map ----------------
@app.route('/quick-map')
def quick_map():
    return render_template('index.html')


@app.route('/survey', methods=['POST'])
def survey():
    return render_template('survey.html',
                           name=request.form.get('name', ''),
                           age=request.form.get('age', ''),
                           gender=request.form.get('gender', ''),
                           questions=QUESTIONS)


@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name', 'Anonymous')
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
    conn.execute("INSERT INTO responses(age, gender, scores) VALUES(?,?,?)",
                 (int(age) if str(age).isdigit() else None,
                  request.form.get('gender', ''), json.dumps(scores)))
    conn.commit()
    conn.close()
    return render_template('results.html', name=name, age=age,
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
    if 'screen_data' not in session:
        return redirect(url_for('screen_start'))
    if idx >= len(SCREEN_SECTIONS):
        return redirect(url_for('screen_finish'))
    return render_template('screen_section.html',
                           section=SCREEN_SECTIONS[idx], idx=idx,
                           total=len(SCREEN_SECTIONS))


@app.route('/screen/<int:idx>/next', methods=['POST'])
def screen_next(idx):
    if 'screen_data' not in session:
        return redirect(url_for('screen_start'))
    section = SCREEN_SECTIONS[idx]
    session['screen_data'][str(idx)] = score_instrument(section, request.form)
    session.modified = True
    if idx + 1 >= len(SCREEN_SECTIONS):
        return redirect(url_for('screen_finish'))
    return redirect(url_for('screen_section', idx=idx + 1))


@app.route('/screen/finish')
def screen_finish():
    data = session.get('screen_data')
    ident = session.get('screen_identity', {})
    if data is None:
        return redirect(url_for('screen_start'))
    results = [data.get(str(i)) for i in range(len(SCREEN_SECTIONS))]
    flags = [(SCREEN_SECTIONS[i]['title'], SCREEN_SECTIONS[i]['instrument'])
             for i, r in enumerate(results) if r and r.get('flag')]
    conn = get_db()
    age = ident.get('age', '')
    conn.execute("INSERT INTO screens(age, gender, results, flags) VALUES(?,?,?,?)",
                 (int(age) if str(age).isdigit() else None,
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
    return render_template('iq_intro.html', domains=iq_eq.IQ_DOMAINS,
                           minutes=12)


@app.route('/iq/test')
def iq_test():
    return render_template('iq_test.html', items=iq_eq.iq_domain_items(),
                           digit=iq_eq.DIGIT_SPAN,
                           symbols=iq_eq.SYMBOL_SEARCH_SECONDS)


@app.route('/iq/result', methods=['POST'])
def iq_result():
    data = request.get_json(force=True)
    correct = data.get('correct', {})
    digits = int(data.get('digits', 0))          # longest span reached
    symbols = int(data.get('symbols', 0))        # items found in 60s

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
    conn.execute("INSERT INTO iq_results(age, standard_score, domains) VALUES(?,?,?)",
                 (int(age) if str(age or '').isdigit() else None, iq,
                  json.dumps(domains_out)))
    conn.commit()
    conn.close()
    return render_template('iq_result.html', iq=iq, band=iq_eq.iq_band(iq),
                           domains=domains_out)


# ---------------- EQ ----------------
@app.route('/eq')
def eq_intro():
    return render_template('eq_intro.html')


@app.route('/eq/test')
def eq_test():
    return render_template('eq_test.html', items=iq_eq.EQ_ITEMS,
                           scale=iq_eq.EQ_SCALE)


@app.route('/eq/result', methods=['POST'])
def eq_result():
    total, subs, subsmax = iq_eq.score_eq(request.form)
    total_max = sum(subsmax.values())
    age = request.form.get('age', '')
    conn = get_db()
    conn.execute("INSERT INTO eq_results(age, total, subscales) VALUES(?,?,?)",
                 (int(age) if age.isdigit() else None, total, json.dumps(subs)))
    conn.commit()
    conn.close()
    return render_template('eq_result.html', total=total, total_max=total_max,
                           band=iq_eq.eq_band(total), subs=subs, subsmax=subsmax)


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)
