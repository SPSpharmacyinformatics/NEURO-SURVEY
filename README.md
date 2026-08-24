# NEURO-SURVEY

"Path of Self-Discovery" — a mobile-first Flask survey that maps a person
across 17 parameters of the neurodivergent spectrum (Executive Function,
Sensory Sensitivity, Masking Effort, …) and visualizes their "Spiky Profile"
against the standard baseline, plus an anonymized community World View.

## Run

```sh
pip install -r requirements.txt
python app.py            # serves on 0.0.0.0:5000
```

## Flow

1. `/` — identity + consent (name, age, gender)
2. `/survey` — 17 sliders (0–8, default 2 = standard baseline) with live
   low/mid/high logic labels
3. `/submit` — radar chart of the user's map vs baseline, profile
   classification (Spiky / High-Intensity / Steady / Balanced)
4. `/world-view` — community average across all respondents

## Privacy

Per UAE Law No. 45/2021 the participant's name is **never stored** — it exists
only in the session long enough to render the personal results page. Only
age, gender, and scores are persisted for anonymized statistics.
