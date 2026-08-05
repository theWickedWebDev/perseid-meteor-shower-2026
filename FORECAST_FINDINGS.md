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
| Is 45% cloud good? | No. Median for these dates here is **72%** | 30 years, solid |
| Odds at least one night works? | **83%**, against a **67%** base rate | Good, with caveats below |
| Does waiting help? | Yes to ~day 5. Past that, **nothing measurable** | 7 nights — differences under 6 pts invisible |
| Which model to believe? | **AIFS** past 5 days, **ECMWF** inside 3 | Weak — partly ranking pessimism (r −0.42) |
| Can we see cloud at night? | Yes — satellite, not the webcam | Verified |

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

climatological joint     67%
its independence bound   68%      <- one point apart
```

Real years sit at their own independence bound too. Three days at 45°N in August is long
enough for a system to pass through. So the comparison of 83% against the 67% base rate is
like-for-like — both computed the same way, both near-independent.

The correlation figure is printed on the page beside the joint so the assumption stays
visible. **If the nights were perfectly locked together the answer would be 47%, not 83%** —
that floor is also shown.

---

## 3. Climatology: what "good" means here

Thirty years of ERA5 (1996–2025) for exactly Aug 11, 12, 13, core window:

| | |
|---|---|
| Median cloud in the core window | **72%** |
| Individual nights beating 30% | **31%** |
| Years with ≥1 usable night | **67%** ← the base rate |

**Two nights in three are historically unusable at this site on these dates.** Three
UNRESOLVED cards read as alarming until you know that. The current forecast is drawn better
than a normal year, and every night individually beats its own historical odds.

This also settles the September question: the astronomy is worse (no Perseids, core window
roughly halved) and the weather gamble is about the same. Trading a known better-than-average
draw for an unknown one with worse astronomy is a poor swap.

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
| Always say climatology (72%) | 33.7 |
| Persistence (tonight = last night) | 38.7 |

Inside three days the models beat a constant "overcast" guess by only a few points. **At
seven days they are worse than it.** That is a property of a week that was cloudy on five
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
fixed-grid inverse projection and lands within 0.13 km; a reading is refused outright if the
nearest pixel is more than 5 km off.

### The webcam's numbers are only trusted in good light

Low sun reddens the whole sky and the red/blue cloud test reads that as overcast. Caught
live at 19:41 on 4 Aug: **camera 40%, satellite 0%, all eight models 0%**. Frames with the
sun below 15° are now excluded from scoring, from the calibration column, and from the
caption under each photo. The number under each webcam frame is the **satellite**, not the
camera.

### What the satellite still can't do

Infrared struggles with **low cloud and fog at night**, when cloud-top temperature is close
to ground temperature. That is the same gap the fog forecast covers, so the two are
complements rather than duplicates. Neither alone is airtight on the failure mode most
likely to cost you the back half of a night.

---

## 6. Where the cloud is, not just how much

A whole-dome percentage cannot say whether *your* sky is open. The southern programme lives
in azimuth **177°–232°** at roughly 7–22° altitude — a narrow slot.

Observed on 4 Aug at 00:56: **dome 54% cloud, north 0%, south 78%.** Fine for Andromeda and
the Perseid radiant; useless for the core. One number cannot express that.

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

## 7. The core window is not two clean hours

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

## 8. Things that are still weak

- **Correlated sources counted as independent votes.** NWS≈GFS, AIFS≈ECMWF. "Six sources
  agree" overstates it. The median limits the damage but does not remove it.
- **Even member counts.** The median averages the middle two, which can produce a value no
  model forecast — mildly contradicting the reason for choosing median over mean.
- **Fog is reported from one hour, and only one.** The badge quotes the worst single hour
  by dewpoint spread and wind together, named on the card. It used to quote `min(spread)`
  beside `min(wind)` across the whole night — a pair that often came from different hours
  and therefore described a condition that never occurred. `fog_hours` was always the
  honest number; the parenthetical was not.
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

## 9. Smoke — measured, and currently a live concern

August in northern New Hampshire sits downwind of Quebec, and **cloud cover reads 0%
straight through smoke**. A perfect-looking forecast can deliver a milky, low-contrast sky
that ruins exactly the faint red and blue the core is shot for.

Aerosol optical depth above **0.30** is a visibly degraded sky. As of 4 Aug the lead-up
nights already read:

```
Aug 05   0.16      Aug 07   0.44   <- well over
Aug 06   0.30      Aug 08   0.17
```

**The trip nights cannot be checked yet.** The aerosol forecast runs about five days, so
11–13 Aug come into range around the 7th. Until then the cards say "haze — not forecast
this far out" rather than showing nothing, because a blank badge beside a fog badge read as
a clean bill of health.

This is worth watching independently of cloud. A night that the page calls a GO can still be
a poor night for colour if the smoke arrives, and nothing else on the page would tell you.

---

## 10. How it runs

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

History older than 12 entries is compacted — the hourly detail is dropped after its consensus
is cached, cutting projected trip-end size from 2.7 MB to about 0.8 MB. No displayed value
changes.

If `venv/` is missing the satellite step is skipped with a message and the page falls back to
webcam-only ground truth. If the APIs are down entirely, the pages rebuild from stored
history so a fresh webcam frame still renders.
