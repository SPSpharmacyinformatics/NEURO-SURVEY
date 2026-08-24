import json
import math
import os
import sqlite3

from flask import Flask, render_template, request

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'neuro_survey.db')

QUESTIONS = {
    "Executive Function": {
        "q": "How hard is it to plan, start, and finish multi-step tasks?",
        "low": "Tasks flow naturally with minimal friction",
        "mid": "Occasional stalls that you can push through",
        "high": "Starting and sequencing tasks feels like pushing a boulder",
    },
    "Sensory Sensitivity": {
        "q": "How strongly do sounds, lights, textures, or crowds affect you?",
        "low": "Background noise rarely registers",
        "mid": "Certain environments become draining or irritating",
        "high": "Everyday sensations can be overwhelming or painful",
    },
    "Social Energy": {
        "q": "How much energy does socializing cost you?",
        "low": "Socializing recharges you",
        "mid": "Enjoyable but needs recovery time afterwards",
        "high": "Even short interactions feel exhausting",
    },
    "Hyperfocus": {
        "q": "How deeply can you lock into something that interests you?",
        "low": "Attention stays flexible and easily redirected",
        "mid": "Strong focus in bursts, on your own terms",
        "high": "Hours vanish; interrupting feels physically jarring",
    },
    "Task Switching": {
        "q": "How easy is it to jump between different activities?",
        "low": "Switching contexts is smooth and cheap",
        "mid": "A brief transition ritual is needed",
        "high": "Switching tasks mid-flow feels genuinely distressing",
    },
    "Verbal Communication": {
        "q": "How natural does spoken conversation feel?",
        "low": "Words arrive easily in most settings",
        "mid": "Fluent in comfort zones, harder elsewhere",
        "high": "Finding words often takes deliberate effort",
    },
    "Reading Between the Lines": {
        "q": "How easily do you read unspoken cues — tone, body language, subtext?",
        "low": "Unspoken cues are usually clear",
        "mid": "You catch most cues but miss subtle ones",
        "high": "Implicit meanings often need explicit translation",
    },
    "Routine Dependence": {
        "q": "How much do familiar routines and predictability matter?",
        "low": "Spontaneity feels easy and fun",
        "mid": "Prefer plans but adapt when needed",
        "high": "Unexpected changes can derail the whole day",
    },
    "Special Interests": {
        "q": "How intense and absorbing are your personal interests?",
        "low": "Hobbies stay casual and varied",
        "mid": "Deep dives that come and go in phases",
        "high": "Core interests are a central, defining part of life",
    },
    "Pattern Recognition": {
        "q": "How naturally do you spot systems, patterns, and details others miss?",
        "low": "Big picture over details",
        "mid": "Notice structures in familiar domains",
        "high": "Details and patterns jump out automatically, everywhere",
    },
    "Emotional Regulation": {
        "q": "How manageable are your emotional reactions in the moment?",
        "low": "Feelings rise and settle smoothly",
        "mid": "Occasional waves that need conscious handling",
        "high": "Emotions can hit hard and linger or overflow",
    },
    "Rejection Sensitivity": {
        "q": "How strongly does criticism or perceived rejection land?",
        "low": "Feedback rolls off easily",
        "mid": "Stings, but recovers within the day",
        "high": "Even small perceived slights can feel devastating",
    },
    "Self-Regulation Movements": {
        "q": "How much do repetitive movements or sounds (stimming) help you regulate?",
        "low": "Rarely needed or noticed",
        "mid": "Helpful in stressful moments",
        "high": "An essential, constant part of self-regulation",
    },
    "Sleep Rhythm": {
        "q": "How stable are your sleep and energy cycles?",
        "low": "Predictable schedule and steady energy",
        "mid": "Drifts with routine and stress",
        "high": "Sleep is erratic, reversed, or hard to initiate",
    },
    "Masking Effort": {
        "q": "How much energy goes into appearing 'typical' around others?",
        "low": "You are essentially the same everywhere",
        "mid": "Some conscious adjustment in certain company",
        "high": "Constant performance that leaves you drained",
    },
    "Time Perception": {
        "q": "How reliable is your internal sense of time?",
        "low": "You run on an accurate internal clock",
        "mid": "Time blurs occasionally",
        "high": "Time is either 'now' or 'not now' — estimation fails often",
    },
    "Sensory Seeking": {
        "q": "How much do you crave intense input — movement, pressure, sound, spice, speed?",
        "low": "Calm and low-stimulation feels best",
        "mid": "Enjoy intensity in chosen doses",
        "high": "Actively seek strong sensations to feel regulated",
    },
}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS responses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            age INTEGER,
            gender TEXT,
            scores TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def classify_profile(scores):
    avg = sum(scores) / len(scores)
    variance = sum((s - avg) ** 2 for s in scores) / len(scores)
    sd = math.sqrt(variance)
    if sd >= 2.0:
        return ("The Spiky Profile",
                "Your scores vary dramatically across parameters. You have "
                "pronounced peaks — areas of extraordinary intensity — alongside "
                "deep valleys. This uneven 'spikiness' is a hallmark of "
                "neurodivergent wiring, bringing both remarkable strengths and "
                "real friction points.")
    if avg >= 5.5:
        return ("The High-Intensity Mind",
                "Nearly every parameter runs hot. You experience the world at "
                "high gain — intensely, vividly, and sometimes overwhelmingly. "
                "Structure, recovery time, and self-advocacy are your key tools.")
    if avg <= 2.5 and sd < 1.2:
        return ("The Steady Baseline",
                "Your responses cluster close to the standard baseline. Your "
                "wiring is relatively typical for the current population average "
                "— which, like every profile, is simply one variation of human.")
    return ("The Balanced Explorer",
            "Your profile shows moderate variation with no extreme peaks. You "
            "move between worlds comfortably, though certain parameters still "
            "cost you more energy than others.")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/survey', methods=['POST'])
def survey():
    name = request.form.get('name', '')
    age = request.form.get('age', '')
    gender = request.form.get('gender', '')
    return render_template('survey.html', name=name, age=age,
                           gender=gender, questions=QUESTIONS)


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
    profile_title, profile_desc = classify_profile(ordered)

    # Privacy: per UAE Law No. 45/2021 the name is never stored.
    conn = get_db()
    conn.execute("INSERT INTO responses(age, gender, scores) VALUES(?,?,?)",
                 (int(age) if age.isdigit() else None,
                  request.form.get('gender', ''), json.dumps(scores)))
    conn.commit()
    conn.close()

    return render_template('results.html', name=name, age=age,
                           profile_title=profile_title,
                           profile_desc=profile_desc,
                           labels=list(QUESTIONS.keys()), scores=ordered)


@app.route('/world-view')
def world_view():
    conn = get_db()
    rows = conn.execute("SELECT scores FROM responses").fetchall()
    conn.close()
    total = len(rows)
    if total == 0:
        avg_scores = [2] * len(QUESTIONS)
    else:
        sums = [0] * len(QUESTIONS)
        for r in rows:
            data = json.loads(r['scores'])
            for i, key in enumerate(QUESTIONS):
                sums[i] += data.get(key, 2)
        avg_scores = [round(s / total, 2) for s in sums]
    return render_template('world_view.html', total=total,
                           labels=list(QUESTIONS.keys()), avg_scores=avg_scores)


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)
