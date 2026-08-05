# Prediction — what the page will say on Sunday 9 Aug

**Written Tue 4 Aug 2026, ~22:00 EDT**, at snapshot 16 of `forecast_history.json`.

Made by the auditing model, independently. Built only from `forecast_history.json`,
`skill.json`, `satellite_log.json`, `nightwatch_log.json` and my own recomputation of the
ERA5 climatology. **`PREDICTION.md` was not read** — the whole point is that these two are
scored against each other, not merged.

Everything below is meant to be checkable on Sunday. Where I am guessing, it says so.

---

## The framing, before any number

Today's figures carry almost no information about Sunday, and the project's own
measurements are what say so:

```
model mean absolute error at 7 days     38.1
"just say overcast" every single night  22.7
```

At the trip nights' current lead the models are **worse than a constant guess**. It shows
in the raw values — Night 2 right now is ECMWF **0%** against GEM **92%**. That is not a
forecast, it is two different weeks.

So the anchor for a prediction is not today's 83%. It is the 30-year base rate, **70%**.

---

## Part 1 — Machinery. High confidence.

Sunday 9 Aug puts Nights 1 / 2 / 3 at leads **2 / 3 / 4 days**.

| | Today (4 Aug) | Predicted Sunday |
|---|---|---|
| Sources per night | 6 / 5 / 5 | **8 on all three** — NWS returns (its 7-day limit clears), ICON and UKMO come into range |
| HRRR | out of range | **Night 1 only, and only late Sunday.** 48 h reaches Aug 11 evening; Nights 2 and 3 still out |
| Model spread | ±78 / ±92 / ±62 | **±25 to ±45** |
| UNRESOLVED cards | 3 of 3 | **at most 1.** Nights 1 and 2 resolve to a verdict; Night 3 borderline against the ±40 gate |
| Haze badge, trip nights | "not forecast this far out" | **populated on all three** — aerosol runs ~5 days |
| Climatology block | 70 / 72 / 65 / 34 | **byte-identical.** These are 30-year statistics. If they move, something is broken |
| `forecast_history.json` | 380 KB | **0.5–0.7 MB**, held down by `compact()` |

### `skill.json`, with roughly 12 verification nights instead of 7

- **`diffs.7_3` stays significant.** It is +17 with a CI of +8 to +24; more data will tighten
  it, not kill it.
- **`diffs.3_0` stays NON-significant.** Going 7 → 12 episodes shrinks a bootstrap interval
  by about √(7/12) ≈ 0.76, so ±10 becomes roughly ±7.6. A +1 point effect still straddles
  zero. The "past about five days, waiting buys nothing measurable" conclusion survives.
- **`pessimism_r` weakens to |r| < 0.3.** It is −0.42 today only because five of seven
  verification nights were overcast. Aug 5 forecasts 31% and Aug 9 forecasts 24% — if either
  verifies clear, the sample stops being one-sided and the confound drops.
  **This is the single most testable call in this document.**
- **The model ranking shuffles.** AIFS's long-range lead is partly an artefact of sitting
  nearest a 77% truth mean. Expect ECMWF and GFS to gain at range if any clear nights enter.

---

## Part 2 — Weather. Low confidence, and stated as such.

### Headline joint

> **Central estimate 72%. Eighty-percent interval roughly 45–93%.**

Drifting **down** from today's 83%, for two reasons:

1. Regression toward the 70% base rate, from a figure computed at a lead where the models
   demonstrably have negative skill.
2. The surrounding pattern looks unsettled. Lead-up nights currently read Aug 6 **74%**,
   Aug 7 **90%**, Aug 10 **92%** — and Aug 10 is the night before Night 1.

**I predict the verdict wording changes** from *"a better draw than these dates usually
give"* to *"about what these dates normally offer."* The threshold is +10 over the base
rate, i.e. 80%, and my central estimate sits under it.

### Per-night — the interesting part

Today the three nights are indistinguishable: 47 / 43 / 44. **My prediction is that an
ordering appears**, and this is it:

| Night | Predicted Sunday | Reasoning |
|---|---|---|
| **Night 1** · Tue 11 Aug | **Best. 20–35% cloud. Verdict "GO" or marginal** | ECMWF at 4% and GFS at 6% are both emphatically clear. ECMWF is the best short-range model in the project's own table (11 at 0–2 d). The lone 82% outlier is GEM, which ranks last in that same table (27) |
| **Night 2** · Wed 12 Aug | **Most uncertain. 35–55%** | ECMWF 0 against GEM 92 is the widest disagreement anywhere on the page. Genuine coin flip. Also the pivot night — Perseid max and new moon |
| **Night 3** · Thu 13 Aug | **Weakest. 55–75%. Verdict "poor" or marginal** | ECMWF is the *pessimist* here at 80%, which is unusual and worth respecting. Three of five models sit 58–80% |

If that ordering lands, it is awkward: **the best night is the build night**, with no lake
trip scheduled and the refractor tied up on M8/M20.

### Two more

- **Night 3 fog moves by more than 4 hours from today's 7.** Dewpoint spread and 10 m wind
  at nine days out are among the least skillful fields any model emits. If it still reads
  exactly 7 on Sunday, that is coincidence rather than confirmation.
- **~40% odds at least one trip night reads AOD over 0.30**, firing the smoke banner for a
  trip night rather than a lead-up one. The region already reads 0.44 on Aug 7.

---

## Part 3 — What Sunday actually means

The project's own skill curve says the information arrives between 7 and 3 days out and
then stops. Sunday puts the trip nights at leads 2–4.

> **Sunday is the day the curve flattens.** Whatever the page says on the 9th is — to within
> the measurement's own ability to detect a difference — what it will say on the 11th.

So read the **ladder**, not the headline. Today it is 83% shootable against 47% pristine. I
expect those to separate further by Sunday, and the gap between them is the real answer: it
is the difference between salvaging one night and getting a genuinely good one.

---

## Part 4 — What would show this prediction wrong

Stated in advance so it cannot be argued away afterwards.

- **Spread still above ±50 on Sunday.** Then the pattern is genuinely unpredictable at this
  range, the trip is a coin flip regardless of the number, and my per-night ranking is noise
  I mistook for signal.
- **Joint still sitting exactly on the independence bound with all three nights within 5
  points of each other.** That would mean the ensemble is not resolving even at leads 2–4 —
  a finding about the machinery rather than the weather, and it would make me suspect the
  three-ensemble pooling is averaging away signal rather than adding robustness.
- **`pessimism_r` unchanged at −0.42 with five more nights in the sample.** That would mean
  the verification week was not the cause, and the model ranking is measuring something I
  have not identified.

---

## Scoring table — fill in on Sunday

| # | Prediction | Predicted | Actual | Hit? |
|---|---|---|---|---|
| 1 | Sources per night | 8 | | |
| 2 | HRRR in play | Night 1 only | | |
| 3 | Max spread across the three nights | ±25 to ±45 | | |
| 4 | UNRESOLVED cards remaining | 0 or 1 | | |
| 5 | Haze badge on all three trip nights | yes | | |
| 6 | Climatology block unchanged | yes | | |
| 7 | `diffs.3_0` still non-significant | yes | | |
| 8 | `pessimism_r` | \|r\| < 0.3 | | |
| 9 | Joint trip odds | 72% (45–93) | | |
| 10 | Verdict wording | "about what these dates normally offer" | | |
| 11 | Night 1 core-window consensus | 20–35% | | |
| 12 | Night 2 | 35–55% | | |
| 13 | Night 3 | 55–75% | | |
| 14 | Night 1 is the best of the three | yes | | |
| 15 | Night 3 fog hours differ from 7 by >4 | yes | | |
| 16 | Any trip night AOD ≥ 0.30 | ~40% likely | | |

---

*Note: `publish.sh` runs `git add -A` hourly, so this file will be committed and pushed to
the public repo on the next run. That is presumably intended — it timestamps the prediction
before the fact, which is the only thing that makes it worth scoring.*
