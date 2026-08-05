# Predictions

Independent forecasts of **what this project's own data will say on Sunday 9 August 2026**,
when the trip nights sit at leads of 2, 3 and 4 days.

Not forecasts of the weather on Sunday. Forecasts of the *numbers* — what the site will
display about 11, 12 and 13 August when read on the 9th.

The prompt is run several times a day as the trip approaches, so this is less a contest
than a convergence study: each prediction is blind to every other, and the interesting
question is whether they tighten toward the truth as lead time shortens or simply wander.
Filenames are timestamps because *when* a prediction was made — and therefore how much data
it had — is the thing that makes it interpretable. Filenames
carry the time the prediction was made, so the record cannot be quietly reshaped afterwards:
git holds the commit, the filename holds the claim.

| File | Model | Written |
|---|---|---|
| [2026-08-04T2220.md](2026-08-04T2220.md) | the building model | 4 Aug, 22:20 EDT |
| [2026-08-04T2236.md](2026-08-04T2236.md) | the auditing model | 4 Aug, 22:36 EDT |

## Why bother

A forecast nobody wrote down is a forecast nobody can be wrong about. These commit to
numbers in advance so Sunday settles them rather than reinterprets them.

They also disagree in a way that is worth watching. The sharpest split is **Night 1**:

- one model expects the current anomaly to soften, because Nights 1 and 2 are forecast
  41 and 33 points better than the 30-year median for these dates while the measured model
  error at 7 days out is 38 points — an anomaly the size of its own error bar
- the other expects ECMWF and GFS to be vindicated, since ECMWF is the most accurate
  short-range model measured at this site and it is calling Night 1 emphatically clear

That is a direct test of *"regress the anomaly toward climatology"* against *"trust the best
model inside three days"*, and one of them will be visibly wrong.

## Adding another

Hand [`PREDICTION_PROMPT.md`](../PREDICTION_PROMPT.md) to a fresh model with read
access to the repo. It is self-contained, bakes in no run-date, and tells the model
not to read this directory.

## Rules

- Predictions are written **before** the target date and never edited afterwards. Any
  correction made between writing and Sunday is recorded inside the file, with its reason.
- Each model reads the data — `forecast_history.json`, `skill.json`, `satellite_log.json`,
  `nightwatch_log.json`, the code — but **not** the other predictions.
- Both weather claims and machinery claims count. The machinery ones (which sources come
  into range, what happens to the sample sizes in `skill.json`, what stays byte-identical)
  score cleanly regardless of what the sky does, and a surprise there is a bug rather than
  a forecast miss.

## Scoring

```
python3 score_predictions.py                        # against the newest snapshot
python3 score_predictions.py --at 2026-08-09T21:00  # against the target date
python3 score_predictions.py --table                # markdown for pasting here
```

It reads the yaml block each prediction ends with, compares against
`forecast_history.json`, and reports per-field error plus a mean. It also correlates error
against lead time, which is the question that actually matters once there are a dozen of
these: **do later predictions get better?** If they do not, the models are not using the
data arriving, and that is a finding about the exercise rather than about the weather.

A prediction with no yaml block is reported as unscoreable rather than skipped quietly.

## Scoring by hand

On Sunday 9 August, fill in the "actual" column in each file from the snapshot nearest
21:00 EDT in `forecast_history.json`. Nothing else changes.
