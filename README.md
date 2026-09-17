# NEURO-SURVEY

"Path of Self-Discovery" — a mobile-first Flask survey that maps a person
across 17 parameters of the neurodivergent spectrum (Executive Function,
Sensory Sensitivity, Masking Effort, …) and visualizes their "Spiky Profile"
against the standard baseline, plus an anonymized community World View.

## Live Demo / Public Instance

Try it now: **https://survey.sps.dpdns.org** — free, no registration required.
(Privacy note: your name is never stored; only anonymized age, gender, and
scores are persisted for the community World View.)

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

## Omni Assessment (v2)

The app now offers four modes from its home page:

| Mode | Instruments | Output |
|------|-------------|--------|
| **Full Clinical Screen** (linear, 8 sections) | PHQ-9, GAD-7, ASRS v1.1 Part A, AQ-10, MDQ, PC-PTSD-5, IPIP-50 Big Five, DSM-5-TR PID-5-BF trait domains | Per-domain scores vs published clinical cutoffs (PHQ-9 ≥10, GAD-7 ≥10, AQ-10 ≥6 per the 2025 cutoff review, ASRS 4+ shaded, MDQ 7+, PC-PTSD-5 ≥3, PID-5 domains ≥9/15) with a consolidated flag report |
| **IQ Assessment** | Original CHC-based battery: matrix reasoning, series, verbal analogies, mental rotation, interactive digit span, timed symbol search | Standard score (mean 100, SD 15) + per-domain profile (Gf/Gc/Gwm/Gv/Gq/Gs) |
| **EQ Assessment** | Empathy Quotient framework, 40 items | Total + Cognitive Empathy / Emotional Reactivity / Social Skills subscales |
| **Quick Map** | Original 17-parameter neurodiversity map | Spiky-profile radar + community World View |

### Standards used
- **CHC (Cattell-Horn-Carroll)** theory — the framework behind the WJ-V (2025) and WAIS — organizes the IQ battery
- **AQ-10 cutoff ≥6** (2025 psychometric review found NICE's ≥7 suboptimal)
- **ASRS v1.1** shaded-box Part A rule (WHO/Harvard)
- **PHQ-9 / GAD-7** standard 5/10/15/20 severity bands
- **PID-5-BF** style items mapped to the five DSM-5-TR personality trait domains
- **EQ** scored on the classic 2/1/0 agreement weighting with filler items

All results are screening-level and stored anonymized; every page carries a
not-a-diagnosis disclaimer.
