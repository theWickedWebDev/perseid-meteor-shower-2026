# Forecast Findings — how the numbers on the site are made, and what they're worth

Everything on [forecast.html](forecast.html) comes from the methods below. This file exists
because several of the numbers look more confident than they are, a few of them mean
something other than the obvious thing, and two of them are corrections to advice given
earlier in this project. If a figure on the page ever looks surprising, the explanation is
probably here.

Measured at the lake site, 45.2393 / −71.1964, unless stated. All times EDT.

---

## The short version

| Question | Answer | Confidence |
|---|---|---|
| Is 45% cloud good? | No. Median for these dates here is **65%** | 30 years, solid |
| Odds at least one night works? | **83%**, against a **70%** base rate | Good, with caveats below |
| Does waiting help? | Yes to ~day 5. Past that, **nothing measurable** | 7 nights — differences under 6 pts invisible |
| Which model to believe? | **AIFS** past 5 days, **ECMWF** inside 3 | Weak — partly ranking pessimism (r −0.42) |
| Can we see cloud at night? | Yes — satellite, not the webcam | Verified |
| Anything else likely to spoil it? | **Night 3 fog** (7 h) and regional **smoke** | Both live as of 4 Aug |

---

## 1. Everything is an ensemble. Nothing is one model.

Every figure — headline percentage, verdict, best hour, trend chart, movement table — is
the **median across every source that reaches that night**, taken hour by hour and then
averaged over the window.

Median rather than mean, because with GEM at 92% and ECMWF at 38% for the same night, a
mean invents a number nobody forecast and lets one outlier drag the verdict.

Sources: NWS gridpoint, ECMWF, GFS, ICON, GEM, AIFS, JMA, UKMO, HRRR. They drop in and out
by range — the page marks each *in play* or *out of range* rather than hiding the ones that
can't see that far.

**NWS is not independent.** It is a forecaster-edited blend built largely on GFS and the
NBM, so when NWS and GFS agree you are partly hearing one model twice. Similarly AIFS is
trained on ERA5, which is ECMWF reanalysis. Of nine nominal sources there are perhaps six
genuinely independent opinions. The page does not currently correct for this.

### The verdict is gated on agreement

A median of 30% drawn from sources spanning 4–82% is not a GO. Where the spread is 40
points or more the card reads **UNRESOLVED** with the span instead of a verdict. The page
spent a while printing "GO" in 48pt over a 4–82% disagreement, which is exactly the
overconfidence the whole thing exists to prevent.

---

## 2. The trip probability, and the assumption inside it

**You do not need a particular night. You need one of three.** That is a joint probability,
and it's the number in the largest type on the page.

It is computed by pooling three ensembles — GEFS (31 members), ECMWF ENS (51), GEM ENS (21)
— and counting how many of the 103 members give *at least one* usable night. Each member is
one physically consistent scenario spanning all three nights, so correlation is measured
rather than assumed.

Pooling matters. Run separately:

| Ensemble | Per-night | Joint |
|---|---|---|
| GEFS | 45 / 55 / 68 | **90%** |
| ECMWF ENS | 51 / 35 / 31 | 82% |
| GEM ENS | 33 / 29 / 38 | 71% |
| **Pooled (103)** | 47 / 43 / 44 | **83%** |

The page used to show GEFS alone — the single most optimistic source, and the ensemble of
the model these notes elsewhere describe as run-to-run volatile.

### The near-independence question — worth understanding

The joint sits within a point or two of the **independence bound**: what you'd get by
multiplying the per-night probabilities as if the nights were unrelated. Measured
correlation between members is **−0.04**.

That looks wrong. Three consecutive nights in one weather pattern should move together, and
if they don't, the suspicion is that the ensemble has simply spread into noise at 7–9 days,
inflating the joint mechanically.

**It was checked against reality, and near-independence is correct here.** Thirty years of
ERA5 for Aug 11/12/13 at this site:

```
Aug 11 vs Aug 12   r = +0.293
Aug 11 vs Aug 13   r = −0.194
Aug 12 vs Aug 13   r = +0.007
mean r             = +0.035

climatological joint     70%
its independence bound   72%      <- two points apart
```

Both figures come from `skill.json` — `p_trip_good` and `p_trip_indep` — so they can be
regenerated rather than taken on trust. An earlier version of this document quoted 67 / 68
from prose alone, computed by hand and never stored.

Real years sit at their own independence bound too. Three days at 45°N in August is long
enough for a system to pass through.

**The comparison is like-for-like, but only since it was made so.** The ensemble weights
hour 23 by the minutes the core is actually up (0.35 / 0.28 / 0.22 — see section 8); the
climatology originally took a plain mean of hours 22 and 23. Unweighted the base rate reads
67%, weighted it reads **70%**, and the page compares the forecast against it
directly. `climatology()` now applies the same weights, so the two numbers are computed the
same way.

The correlation figure is printed on the page beside the joint so the assumption stays
visible. **If the nights were perfectly locked together the answer would be 47%, not 83%** —
that floor is also shown.

---

## 3. Climatology: what "good" means here

Thirty years of ERA5 (1996–2025) for exactly Aug 11, 12, 13, core window:

| | |
|---|---|
| Median cloud in the core window | **65%** |
| Individual nights beating 30% | **34%** |
| Years with ≥1 usable night | **70%** ← the base rate |

**Two nights in three are historically unusable at this site on these dates.** Three
UNRESOLVED cards read as alarming until you know that. The current forecast is drawn better
than a normal year, and every night individually beats its own historical odds.

This also settles the September question, and more decisively than previously written:

```
Aug 12   dark 21:54, core 14.9° → below 10° at 23:17    83 min
Sep 12   dark 20:43, core 12.4° → below 10° at 21:15    32 min
```

Not "roughly halved" — **cut to 39%**. September also has no Perseids, and the weather gamble
is the same draw from the same distribution. Trading a better-than-average August for an
unknown September with a third of the core window is a poor swap.

### The verdict is anchored to this, not to round numbers

The banner's wording is derived from the base rate rather than fixed thresholds. It used to
say "worth the drive" above 70% and "a real gamble" above 45% — which meant a
climatologically *average* trip read as a gamble, while the line directly beneath it argued
that absolute numbers are unreadable without the base rate. The page was contradicting
itself one card apart.

These dates are a gamble every year. The only question the data can answer is whether this
year is a better or worse draw than usual, so that is what the verdict now says.

**ERA5 caveat.** It is reanalysis — a model assimilating observations — at about 25 km.
Checked against the satellite it agreed within 10 points on 73% of hours, but once read 23%
against the satellite's 99%, having smoothed away a local deck. Fine for 30-year statistics,
not a substitute for looking at tonight.

---

## 4. Does waiting help? Mostly no.

Model error against satellite truth, by how far ahead the forecast was made. **Seven
nights**, 51 verified hours — the model-hour count is larger but not independent, since
seven models scoring one hour is a single observation and 02:00 is nearly the same draw as
01:00. Intervals below are bootstrapped by night:

```
lead      mean     95% CI
7 days    38.1   [29.9, 46.0]
6 days    23.2   [11.8, 33.1]
5 days    20.6   [ 8.6, 31.9]
4 days    17.9   [ 8.3, 28.8]
3 days    20.8   [10.7, 30.8]
2 days    18.0   [ 8.2, 29.3]
1 day     14.6   [ 7.7, 21.3]   <- below 0 d, which cannot be real
0 days    19.7   [13.0, 25.0]
```

### Is this better than no skill at all?

Barely, and worse than that at range. The verification week averaged **77% cloud**:

| Forecaster | Mean error |
|---|---|
| Always say "overcast" | **22.7** |
| Models, 0–3 days | 15–20 |
| Models, 7 days | 38.1 |
| Always say climatology (65%) | 37.1 |
| Persistence (tonight = last night) | 38.7 |

Inside three days the models beat a constant "overcast" guess by only a few points. **At
seven days they are worse than it** — and worse than every baseline here except persistence. That is a property of a week that was cloudy on five
nights out of seven — the measure will mean more once some genuinely clear nights are in
the sample.

**Waiting from 7 days to 3 gains 17 points of accuracy** — 95% CI +8 to +24, comfortably
clear of the noise. **From 3 days to the night itself, nothing measurable**: the point
estimate is +1 with an interval of −9 to +11, straddling zero.

The chart itself shows why the second number cannot be taken at face value — **1 day out
scores 5 points better than the night itself**, which is impossible, and sets the noise
floor at roughly ±6. An earlier version of this document stated the +1 as a finding. It is
not one; it is smaller than the error bar.

For the trip: Night 1 is Aug 11, so by **Aug 6 or 7** you have essentially the whole picture.
Deciding on the 8th is not premature.

> **This corrects earlier advice.** I previously said the forecast would sharpen closer in
> and suggested pushing the decision to Aug 9 to catch HRRR. The measurement says otherwise
> for the global models. HRRR is a different resolution class and may still add something,
> but do not expect the *forecast* to improve by waiting.

### Mean versus median — where the risk actually lives

At three days the mean error is 21 but the **median is 8**. Most nights are forecast well;
the mean is dragged up by occasional total misses. So the typical night is reliable and the
risk is entirely in the tail — which is why spread matters more than the number. When the
models agree they are usually right. When they split 0-vs-100, the tail is announcing itself.

### Scored against the slot, not just the dome

The models are scored against the satellite's 34 km box overhead. But the trip does not care
about the dome — it cares about the southern fan the targets sit in, which `satellite.py`
already banks at no extra cost. Scoring on the dome answers *"was the sky cloudy"*; scoring
on the slot answers *"was the shot possible"*, and on any night with structure those differ.

Both are now computed. Today they agree:

| Model | dome, 0–2 d | slot, 0–2 d |
|---|---|---|
| AIFS | 10 | 9 |
| ECMWF | 10 | 9 |
| UKMO | 13 | 9 |
| ICON | 14 | 11 |

The top three tie at 9 on the slot, so the reordering between the two lists is noise. That
is the expected result while the sky stays uniform — with no directional structure the slot
*is* the dome. The number worth watching is whether they diverge on a night that has
structure, because if they do, every skill figure computed on the dome has been answering
the wrong question.

### Which model, at which range

Mean absolute error against satellite, measured here:

| Model | 0–2 d | 5–7 d |
|---|---|---|
| AIFS | 10 | **19** |
| ECMWF | **11** | 31 |
| UKMO | 14 | 26 |
| ICON | 15 | 12 |
| JMA | 21 | 36 |
| GFS | 24 | 21 |
| GEM | 27 | 32 |

**ECMWF is the best short-range model here and among the worst long-range ones** — 9 points
of error inside a day, 47 at a week. **AIFS is the reverse**: unremarkable up close, the most
stable across the whole range, clearly best at distance. The AI model's smoothing hurts it
near and helps it far.

> **This also corrects earlier advice.** The site originally said to weight ECMWF throughout.
> It now says AIFS at range, ECMWF inside three days.

**Read this ranking with suspicion.** The correlation between "forecasts more cloud" and
"scores well" is **−0.42** on this sample, so it is partly ranking pessimism rather than
skill: on an overcast week the gloomiest model wins on error alone. AIFS, ECMWF and UKMO
happen to sit nearest the truth mean of 77%; JMA and GEM are the optimistic ones and score
worst. Directional at best until the sample contains clear nights.

---


### How often it is right, on a much larger sample

The measurements above score against the satellite, which is the honest reference and caps
the sample at the nights the satellite has watched. A second pass trades reference quality
for volume: 92 days of Open-Meteo previous runs, every model, core hours only,
scored against each model's own day-0 value for the same hour. Over a thousand readings per lead instead of a few dozen.

That reference is an analysis rather than an observation, so it measures how far a forecast
**moves** between issue and arrival, not how wrong it finally is. Bigger sample, weaker
truth. Both numbers are worth having and neither replaces the other.

"Right" means within **5 percentage points** of the outcome — not on the correct
side of any threshold. An earlier version scored the GO line instead, which counted a 5%
forecast against a 25% outcome as a hit, and folded a question about the trip into a
measurement of the models.

| Lead | Right (±5) | Half the time within | 9 in 10 within |
|---|---|---|---|
| 1 day | 44% | ±8 | ±66 |
| 2 days | 38% | ±11 | ±71 |
| 3 days | 33% | ±13 | ±80 |
| 4 days | 28% | ±19 | ±82 |
| 5 days | 26% | ±21 | ±82 |
| 6 days | 23% | ±24 | ±87 |
| 7 days | 19% | ±29 | ±86 |

**The baselines matter more than the headline.** Three predictors that know nothing:

| Predictor | Scores |
|---|---|
| Always say overcast | **28%** |
| Random guess 0–100 | 11% |
| Always say the 30-year average (53%) | 7% |

Always saying "overcast" is right 28% of the time because most nights
here are. That is the bar. The forecast clears it out to three days, ties at four, and
loses from five onward — the same conclusion the satellite-referenced curve reaches by a
completely different route.

Note the trap in choosing a baseline. Under the old GO-line scoring, "always say cloudy"
scored 62% and the forecast could not beat it at seven days. Under a 5-point test the
do-nothing predictors collapse and the forecast clears them at every lead. The stricter
definition produces a smaller headline number and a better-looking model, which is a good
reason to publish both the definition and the baseline rather than the number alone.

### Why no average error is quoted anywhere

The error distribution is bimodal, not bell-shaped. One day out:

| Off by | Share of nights |
|---|---|
| 0–2 points | 27% |
| 3–10 | 20% |
| 11–25 | 19% |
| 26–50 | 15% |
| 51+ | **18%** |

A fifth of nights are called dead on and nearly a fifth are wrong by more than fifty points
— the day before. Mean error is 22, median 8, and neither describes a night you would
actually experience. Percentiles are quoted throughout for this reason.

## 5. Ground truth: satellite, not the webcam

The webcam can only score cloud in daylight. The trip happens at night. So the model
scoreboard was being calibrated on afternoon cumulus and trusted for 2 AM stratus.

`satellite.py` reads **GOES-19 ABI-L2-ACMC**, the clear-sky mask, from the public S3 bucket:
2 km pixels, a new granule every 5 minutes, ~4.8 MB, no credentials. It detects cloud by
temperature rather than reflected light, so it works after dark.

Verified against a real night:

```
19:00  95%       03:00  10%   <- full dark, caught an overnight clearing
23:00  65%       11:00   0%
```

Where satellite and webcam overlap in daylight they agree. Geolocation uses the GOES-R
fixed-grid inverse projection and lands **0.46 km** from the site — under a quarter of a
2 km pixel, and nowhere near the 5 km refusal guard; a reading is refused outright if the
nearest pixel is more than 5 km off.

### The webcam's numbers are only trusted in good light

Low sun reddens the whole sky and the red/blue cloud test reads that as overcast. Caught
live at 19:41 on 4 Aug: **camera 40%, satellite 0%, all eight models 0%**. Frames with the
sun below 15° are now excluded from scoring, from the calibration column, and from the
caption under each photo. The number under each webcam frame is the **satellite**, not the
camera.

**A note on the sun angle.** `sun_alt()` returns the *geometric* altitude of the sun's
centre — no refraction, no semi-diameter. Conventional sunrise and sunset are the upper limb
at −0.833°, about five minutes later and earlier respectively. That distinction does not
matter for a quality gate on webcam frames, but it did make an earlier docstring compare a
zero crossing against almanac values using the other definition and call the near-miss
agreement. It was coincidence.

### What the satellite still can't do

Infrared struggles with **low cloud and fog at night**, when cloud-top temperature is close
to ground temperature. That is the same gap the fog forecast covers, so the two are
complements rather than duplicates. Neither alone is airtight on the failure mode most
likely to cost you the back half of a night.

---

## 6. Where the cloud is, not just how much

A whole-dome percentage cannot say whether *your* sky is open. The southern programme lives
in azimuth **177°–232°** at roughly 7–22° altitude — a narrow slot.

**This is currently unvalidated, and the honest version is less impressive than it first
appeared here.** An earlier draft cited a reading of "dome 54%, north 0%, south 78%" from
4 Aug 00:56. That was computed live while testing and is **not in `satellite_log.json`** —
octants were not being stored at that hour, so the example cannot be reproduced from the
record and should not have been quoted as though it could.

What the 63 logged readings that *do* carry octants actually show:

```
dome vs mean of S/SW/SE      0.8 points average, 12.3 max
readings differing by >=15   0 of 63
spread across the 8 octants  median 0, max 33
readings with a genuinely    3 of 63
  directional sky
```

So the compass has not yet demonstrated anything — because **55 of those 63 readings were
of an essentially uniform sky**, where by construction every direction agrees. The method is
untested rather than disproved: it has had three opportunities and the largest showed 33
points of directional variation, which is the kind of difference it exists to catch. It
earns or loses its place on a genuinely broken night, and there has not been one yet.

The satellite is sampled in a fan across that slot, in three rings, and the ring distances
are geometry rather than taste — blocking cloud sits at `height ÷ tan(altitude)`:

| Cloud | Height | Fills the slot from |
|---|---|---|
| Low stratus / fog | 1 km | 2–8 km out |
| Mid deck | 3 km | 7–23 km |
| Cirrus | 10 km | 25–78 km |

A far ring cloudier than the near ring means something is on its way. There is also an
**upwind** sample 30–90 km out along the 700 mb flow: on the night of 3/4 Aug it fell to 0%
an hour before the sky overhead cleared.

The scrubbable compass shows 12 hours of satellite observation running into 12 hours of HRRR
forecast. HRRR because at 3 km it can resolve a 14 km offset; ECMWF at 25 km returns eight
nearly identical octants, a blur rather than a direction.

---

## 7. Fog — the failure mode that likes good forecasts

Radiative cooling needs a clear sky. So the nights that fog are disproportionately the
nights that *forecast* best — anti-correlated with the very number the rest of the page
optimises. A card can read GO and still lose you the back half of the night.

Flagged when all three hold in the same hour, at the lake:

| | |
|---|---|
| Dewpoint spread | under **2 °C** |
| Wind at 10 m | under **5 km/h** |
| Cloud cover | under **40%** — above that there is no radiative cooling to drive it |

Wind is the term that saves most nights. Night 2 currently runs a spread of 1.4 °C — more
saturated than Night 1 — and flags nothing, because 5.5 km/h keeps the layer mixed.

**As of 4 Aug the live signal is on Night 3: 7 risk hours, worst at 2 AM with a 0.3 °C
spread and 1.8 km/h of wind.** That was 2 hours this afternoon. It is moving the wrong way,
and 2 AM is the middle of the Perseid window.

The badge names the single worst hour rather than summarising the night, because summarising
went wrong once already — see section 9.

---

## 8. The core window is not two clean hours

`CORE_HR` is hours 22 and 23, but the Milky Way core drops below a 10° treeline at about
**23:21 / 23:17 / 23:13** on the three nights — four minutes earlier each night. Most of hour
23 is already gone.

Hours are therefore weighted by the minutes actually available: hour 22 counts fully, hour 23
counts 0.35 / 0.28 / 0.22. Otherwise a cloudy 23:40 counts as heavily as a cloudy 22:15,
which flatters or damns a night for weather occurring after the target has set.

**The treeline itself is provisional.** It was derived from a moon fiducial in a 2023 photo
that carried a +2.7° altitude error. Correcting it suggests the treeline is nearer **7.3°
than 10°**, which would buy about **29 more minutes of core each night**. The 360° horizon
survey on arrival settles it — that task is first on the Night 1 schedule for a reason.

---

## 9. Things that are still weak

- **Spread is reported two ways, and only one of them gates the verdict.** The full range
  (max minus min) is the tail risk — how wrong this could be if the outlier is right. But as
  an agreement test across eight heterogeneous models a single dissenter sets it, so it
  exceeded the 40-point gate on **143 of 144** night-readings ever recorded, including
  nights one day out. A verdict that fires 99% of the time is not a verdict. The gate now
  uses the interquartile spread, which clears 40 about a third of the time and can therefore
  discriminate; the full range is still displayed beside it.
- **Correlated sources counted as independent votes.** NWS≈GFS, AIFS≈ECMWF. "Six sources
  agree" overstates it. The median limits the damage but does not remove it.
- **Even member counts.** The median averages the middle two, which can produce a value no
  model forecast — mildly contradicting the reason for choosing median over mean.
- **Fog is reported from one hour, and only one.** The badge quotes the worst single hour
  by dewpoint spread and wind together, named on the card. It used to quote `min(spread)`
  beside `min(wind)` across the whole night — a pair that often came from different hours
  and therefore described a condition that never occurred. `fog_hours` was always the
  honest number; the parenthetical was not.
- **Per-calendar-date climatology is deliberately absent.** Aug 11/12/13 medians came out
  73 / 48 / 68%, which looks like a real difference between nights and is not: adjacent
  calendar dates have no mechanism to differ by 25 points, the standard deviation is ~37 on
  n=30, and resampling one pooled distribution reproduces a gap that large 34% of the time.
  It was computed and never rendered; now it is not computed.
- **One ephemeris fact, one place.** The core-window weights derive from the core-set
  times in `schedule_data.ASTRO`, which is checked against astropy at import. They were
  briefly restated in three files; if the arrival survey confirms a 7.3° treeline, every
  core-set time moves ~29 minutes and all three weights change — that has to be one edit.
- **No test suite.** Everything is verified ad hoc. That is how the low-sun bug survived
  shipping twice, in two different places.
- **`EDT` is fixed at UTC−4** while Open-Meteo is queried with `America/New_York`. Identical
  in August, an hour apart after 1 Nov. Harmless for this trip, wrong on reuse.
- **Skill sample is 7 nights.** One week, late Jul to early Aug, overcast on five of them
  and bimodal — 41 readings at or above 50% cloud, 10 at or below 9%, nothing between. The
  satellite log also has one genuine gap (the night of 29 Jul, 4 hours). Differences smaller
  than about 6 points are not measurable at this size.
- **Aerosol data stops at about 5 days**, so smoke cannot be seen for the trip nights until
  around 7 Aug. This mattered more than expected: the cards showed a fog badge and no haze
  badge, which read as "checked, clear" when it actually meant "not checked". Absence now
  says so explicitly, for fog and haze alike.

---

## 10. Daytime, which the rest of this ignores

Every other number here concerns roughly eighty minutes of sky per night. The trip is four
days long, and a wet afternoon does not spoil it — it changes what you do with the day.

The daytime block restricts to **8 AM to 7 PM** rather than using the daily maximum most
forecasts publish. A 40% chance of rain driven by a shower at 3 AM says nothing useful about
a walk at noon, and the night is already covered in detail above.

It is coloured by **hours of rain, not probability**, because those diverge: a 30% chance
that resolves into one damp hour is a good day out, and the same 30% spread across eight
hours is not. Rain totals are shown but are the least useful figure — 6 mm in one afternoon
burst is a different day from 6 mm of drizzle.

---

## 11. Smoke — measured, and currently a live concern

August in northern New Hampshire sits downwind of Quebec, and **cloud cover reads 0%
straight through smoke**. A perfect-looking forecast can deliver a milky, low-contrast sky
that ruins exactly the faint red and blue the core is shot for.

Aerosol optical depth above **0.30** is a visibly degraded sky. As of 4 Aug the lead-up
nights already read:

```
Aug 05   0.16      Aug 07   0.44   <- well over
Aug 06   0.30      Aug 08   0.17
```

**The trip nights cannot be checked yet**, and they arrive later than previously written
here. The aerosol feed reaches about **four days** for a whole night, not five — a night's
window runs to 07:00 the following morning, and the feed stops before that on the last day
it covers. So Night 1 comes into range on **7 Aug**, Night 2 on the **8th**, Night 3 not
until the **9th**. On the 7th the page is still blind on two of the three nights, not
sighted on all three. Until then the cards say "haze — not forecast
this far out" rather than showing nothing, because a blank badge beside a fog badge read as
a clean bill of health.

This is worth watching independently of cloud. A night that the page calls a GO can still be
a poor night for colour if the smoke arrives, and nothing else on the page would tell you.

---

## 12. How it runs

```
publish.sh          hourly from cron at :05
  skill.py          climatology + lead-time skill, refreshed daily (37 API calls)
  webcam.py         frame, cloud estimate, model comparison
  satellite.py      GOES clear-sky mask, octants, upwind  [needs venv/ for h5py]
  log_forecast.py   snapshot, rebuild FORECAST_LOG.md and forecast.html
  preview_forecast.py   mock-data preview, gitignored
  → commit and push
```

A forecast point is recorded only when NWS issues a new package **or** a model refreshes, so
each point on the trend chart is a genuinely separate forecast rather than a repeated
reading. Ensemble and fog readings belong to *now* rather than to a package, so they refresh
in place without banking a duplicate snapshot.

`forecast_history.precompact.json` is written once, immediately before the first entry
ever loses its hourly detail — an uncompacted copy sitting next to the live file. It is
gitignored because git already holds every version, but recovering from git is archaeology
and this is not.

History older than 12 entries is compacted — the hourly detail is dropped after its consensus
is cached, cutting projected trip-end size from 2.7 MB to about 0.8 MB. No displayed value
changes.

If `venv/` is missing the satellite step is skipped with a message and the page falls back to
webcam-only ground truth. If the APIs are down entirely, the pages rebuild from stored
history so a fresh webcam frame still renders.
