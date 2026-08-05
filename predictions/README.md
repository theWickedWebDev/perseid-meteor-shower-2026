# Predictions

Independent forecasts of **what this project's own data will say on Sunday 9 August 2026**,
when the trip nights sit at leads of 2, 3 and 4 days.

Not forecasts of the weather on Sunday. Forecasts of the *numbers* — what the site will
display about 11, 12 and 13 August when read on the 9th.

Each is written by a different model, in isolation, without reading the others. Filenames
carry the time the prediction was made, so the record cannot be quietly reshaped afterwards:
git holds the commit, the filename holds the claim.

| File | Model | Written |
|---|---|---|
| [2026-08-04T2220-claude1.md](2026-08-04T2220-claude1.md) | the building model | 4 Aug, 22:20 EDT |
| [2026-08-04T2236-claude2.md](2026-08-04T2236-claude2.md) | the auditing model | 4 Aug, 22:36 EDT |

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

On Sunday 9 August, fill in the "actual" column in each file from the snapshot nearest
21:00 EDT in `forecast_history.json`. Nothing else changes.
