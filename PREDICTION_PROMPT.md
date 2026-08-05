# Prediction prompt — hand this to a fresh model

Self-contained and reusable. No run-date is baked in: the model works out today
from `date` and from the newest snapshot in `forecast_history.json`.

Paste everything below the line into a model with read access to this repository.

---

You are making an independent forecast, in a repository you have not seen before.

## Do not read these files

```
predictions/            <- the whole directory
```

Two other models have already written predictions and they live in `predictions/`, along
with a README that summarises where they disagree. Reading any of it destroys the point of the exercise, which is three independent forecasts scored
against each other. Do not open them, do not grep them, do not let their contents reach
your context by any route — including `git log -p`, `git show`, and any command that dumps
whole directories. If you see their contents by accident, say so plainly in your output
rather than pretending otherwise.

Everything else in `/home/stephen/pittsburg-trip` is fair game.

## The situation

A three-night astrophotography trip to Pittsburg, New Hampshire on **11, 12 and 13 August
2026** — Perseid maximum and new moon. The site is a lake shore at 45.2393, −71.1964. The
whole trip turns on roughly 80 minutes each night when the Milky Way core sits above a
treeline, so cloud in a narrow southern window matters far more than cloud in general.

**Work out today's date yourself** — run `date`, and check the newest `taken` timestamp in
`forecast_history.json`. Do not assume; this prompt is reused and the answer changes.

A forecast site logs model data hourly. It pools several deterministic models plus three
ensembles, keeps satellite ground truth from GOES-19, and counts stars in the actual target
region of sky via a webcam 16.6 km from the site.

## Your task

Predict **what this project's own data will say on Sunday 9 August 2026** — the date on
which Night 1 sits 2 days out, Night 2 three and Night 3 four. That is chosen because the
project's own measured skill curve flattens around there: `skill.json` shows error falling
sharply between 7 and 3 days out and then not improving, so the 9th is roughly the last day
new information arrives.

You are not forecasting the weather on the 9th. You are forecasting the *numbers* — what the
site will display about 11, 12 and 13 August when read on that date.

**If today is already on or past 9 August**, say so at the top of your file and instead
predict for the trip nights themselves as the nearest useful equivalent, stating clearly
what you changed. Do not silently predict a date that has passed.

## Where to look

| File | What it holds |
|---|---|
| `forecast_history.json` | Every snapshot. Per-night per-model values, the pooled consensus, spread, the ensemble trip probability and its ladder, fog and aerosol readings |
| `skill.json` | 30-year ERA5 climatology for these exact dates, and measured model error by forecast lead against satellite truth |
| `satellite_log.json` | GOES-19 clear-sky-mask readings, hourly, over both the site and the webcam |
| `nightwatch_log.json` | Star counts and flux in the core, Rho Ophiuchi and teapot regions |
| `FORECAST_FINDINGS.md` | How every number is computed, and a frank list of what is still weak |
| `log_forecast.py` | The rendering logic, including the thresholds that decide verdict wording |
| `SITE_DATA.md` | Site geometry, target altitudes, the core window |

`FORECAST_FINDINGS.md` is worth reading before predicting. It documents several things that
are easy to get wrong — why the base rate is the yardstick rather than zero, what the
measured error actually is at each lead, and which statistics are known to be fragile.

## What to produce

Write `predictions/<timestamp>.md`, where `<timestamp>` is the moment you write it in
`YYYY-MM-DDTHHMM` form, taken from `date` rather than assumed — e.g.
`predictions/2026-08-06T0915.md`. The timestamp alone is the identity: this prompt is run
several times a day, so what matters is when a prediction was made and therefore how much
data it had, not which model made it, taken from `date` rather than assumed. Write the file directly —
do **not** list the directory first, since the filenames alone would tell you when the
others were written and the README beside them would tell you what they said.

Include:

**1. Specific numbers with ranges.** At minimum: the pooled consensus for each of the three
nights, the model spread, the headline joint trip probability, and the exact verdict wording
the page will render. Check `log_forecast.py` for the thresholds rather than guessing — the
wording follows from the number by a rule, so predicting a number and an incompatible
wording is an internal contradiction.

**2. Your reasoning, briefly.** What you are weighting and why. If you are guessing, say so.

**3. Predictions about the machinery, not just the weather.** Which sources come into range,
how the sample sizes in `skill.json` change, what stays fixed. These score cleanly regardless
of what the sky does.

**4. What would show you wrong.** Stated in advance, concretely.

**5. A scoring table** with a blank "actual" column, so it can be filled in on Sunday.

## Ground rules

- Commit to numbers. An interval so wide it cannot be wrong is not a forecast.
- State the date and time you are writing, the snapshot count in `forecast_history.json`,
  and the lead time in days to each trip night. This prompt is run repeatedly as the trip
  approaches, so a prediction is only interpretable alongside how much data it had.
- Put a machine-readable block at the very end, exactly in this form, so predictions can be
  scored automatically:

```yaml
written: 2026-08-06T09:15
snapshots: 41
lead_days: [5, 6, 7]
night1: 33
night2: 40
night3: 57
spread1: 45
joint: 76
verdict: about what these dates normally offer
```
- Distinguish what you measured from what you assumed.
- If the data contradicts something in the documentation, say so — that is a finding.
- Do not hedge in prose what you have already stated as a number.

The repository is a git repo and `publish.sh` runs hourly from cron, so your file will be
committed automatically. That is intended: it timestamps the prediction before the fact.
