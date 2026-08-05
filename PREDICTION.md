# Prediction — written 4 Aug 2026, 22:20 EDT

**How the forecast for 11–13 August will have changed by Sunday 9 August.**

A forecast of the forecast. Written before the fact so it can be scored afterwards rather
than reinterpreted, and because a claim nobody wrote down is a claim nobody can be wrong
about.

**What is being predicted:** what the site will *say about the trip nights* when read on
**Sunday 9 August**. Nothing here concerns the weather on Sunday itself — every figure is
the forecast for 11, 12 and 13 August as it will stand two days out.

Sunday is chosen because it sits 2 days before Night 1, 3 before Night 2 and 4 before Night
3 — inside the range where the measured skill curve says the models have stopped improving.
Sunday's numbers should therefore be close to what you actually get.

---

## The state being predicted from

Snapshot `2026-08-04T21:58:06 EDT`, 103 ensemble members, 6 deterministic sources.

| Night | Consensus | Spread | ECMWF | GFS | GEM | AIFS | JMA | NWS |
|---|---|---|---|---|---|---|---|---|
| **1** · 11 Aug | **24%** | ±78 | 4 | 6 | **82** | 34 | 16 | 51 |
| **2** · 12 Aug | **32%** | ±92 | 0 | 8 | **92** | 62 | 32 | — |
| **3** · 13 Aug | **58%** | ±60 | 80 | 20 | 58 | 59 | 24 | — |

Trip joint **83%** · independence bound 83% · correlated floor 47%
Ladder: 40% → 90 · **30% → 83** · 20% → 74 · 10% → 57 · 5% → 47
Climatology: median **65%** cloud · base rate **70%**
Fog: Night 3 has **7 risk hours**, worst 02:00 · Nights 1 and 2 clear
Aerosol: trip nights out of range; Aug 7 already reads **0.44**, above the 0.30 haze threshold

---

## The reasoning

Two forces, pulling opposite ways.

**Toward optimism.** ECMWF says 4% and 0% for Nights 1 and 2, and it is the best short-range
model measured at this site (error 11 points at 0–2 days). GFS agrees at 6% and 8%. Two
independent centres calling it nearly clear is not a fluke reading.

**Toward pessimism, and I weight this more heavily.** Nights 1 and 2 are being forecast **41
and 33 points better than the climatological median** for these dates. The measured error of
these models at 7 days out is **38 points** — the anomaly is the same size as the error bar.
When a forecast claims an anomaly as large as its own uncertainty, the anomaly usually
shrinks. Not because weather deteriorates, but because extreme long-range values tend not to
verify. GEM has also held 82% and 92% all day without moving a single point.

**This is a prediction about the estimate, not about the sky.** The weather on 11 August is
already whatever it is going to be. What I am forecasting is how the number moves as the
models stop guessing.

---

## Predictions

All rows read: *the forecast for that trip night, as displayed on Sunday.*

| Forecast for | Reads today | **Will read Sunday** | Range I would accept |
|---|---|---|---|
| Night 1 — 11 Aug | 24% | **38%** | 20–58 |
| Night 2 — 12 Aug | 32% | **42%** | 22–62 |
| Night 3 — 13 Aug | 58% | **55%** | 38–72 |
| Spread, Night 1 | ±78 | **±45** | ±25–65 |
| Trip joint | 83% | **74%** | 62–84 |
| Verdict wording | better draw | **still "better draw"**, narrowly | |

### Specific calls

- **GEM capitulates — 70% confidence.** One model against five, and it has the worst measured
  error of the set at this site. I expect it into the 50s rather than all the way down.
- **Night 3 stays the worst of the three.** Pinned at 58% for twelve straight hours with no
  movement in any direction, which usually means agreement on a pattern rather than
  uncertainty.
- **Spread narrows but does not close.** Full consensus, under ±20: only **25%** likely.
- **Nightwatch:** core region reading flux above 1,000 with 2–4 stars on clear nights, and at
  least one night before Sunday where the star count and the satellite disagree. That
  disagreement is the interesting case, not a failure.
- **Overall confidence in the direction: about 60/40.** A lean, not a conviction.

---

## What would make me wrong

**If ECMWF holds at 0–4% through Sunday**, I am too pessimistic and the nights come in near
20%. ECMWF is the model I would least like to bet against inside three days, so this is the
most likely way I lose.

**Smoke instead of cloud.** AOD already reads 0.44 on 7 Aug and the aerosol forecast cannot
see the trip nights yet. A clear-but-milky night would make my cloud numbers right and the
trip disappointing anyway — the one outcome where being correct is worth nothing.

**Fog on Night 3.** Seven risk hours already, worst at 02:00, and it grew from two hours
during the course of today. That is the middle of the Perseid window, and it is anti-
correlated with a good cloud forecast: the ridge that clears the sky is the ridge that goes
calm and saturated overnight.

---

## What this does not change

Even the pessimistic case — 38 / 42 / 55 — leaves a **74% chance at least one night
delivers, against a 70% base rate.** Still a better-than-average draw. Being right about the
softening does not flip the go/no-go; it means the margin is thinner than tonight's chart
suggests.

The outcome that *would* change the decision is Night 2 climbing back above 55% with GEM
vindicated rather than capitulating. That is the minority case, and it is the one to watch
for.

---

## Scoring

Compare against `forecast_history.json` for the snapshot nearest 9 Aug 21:00 EDT.
Cloud figures are the pooled consensus per night; joint is the 30% rung of the ladder.

Every claim is about the forecast **for the trip nights**, read on 9 Aug.

| Claim | Predicted | Actual | Hit? |
|---|---|---|---|
| Forecast for 11 Aug | 38% (20–58) | | |
| Forecast for 12 Aug | 42% (22–62) | | |
| Forecast for 13 Aug | 55% (38–72) | | |
| Trip joint | 74% (62–84) | | |
| Spread N1 | ±45 (±25–65) | | |
| GEM below 70 on Night 1 | yes, 70% conf | | |
| Night 3 worst of three | yes | | |
| Verdict still "better draw" | yes | | |
| Direction: Sunday worse than today | yes, 60% conf | | |
