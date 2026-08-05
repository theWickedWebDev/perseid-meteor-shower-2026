# Perseid Meteor Shower 2026 — Pittsburg, NH

Planning for three nights of astrophotography in Pittsburg, New Hampshire,
**August 11–14, 2026** — Perseid maximum and new moon fall inside the window.

**[→ The trip plan](index.html)** · **[→ Forecast trend](forecast.html)**

---

## What this is

Two people, four optical systems, and a 90-minute window each night when the Milky Way core
sits above 10° over a lake. Everything here exists to make that 90 minutes work, and to decide
— on evidence rather than nerves — whether to drive up at all.

| | |
|---|---|
| **Dates** | Aug 11–14, 2026 · Perseid max Aug 12–13 · new moon Aug 12 |
| **Site** | Pittsburg NH · Bortle 2 · 45.09 N cabin, 45.24 N lake |
| **Gear** | EQ6-R + Sharpstar 76EDPH + ASI2600MC · Star Adventurer Mini + astromodified Canon T8i + Sigma 18-35 f/1.8 · NexStar 6SE visual · iPhone |
| **Mission** | Milky Way core, and Perseids. Everything else is bonus |

## The documents

| File | What's in it |
|---|---|
| [PRIORITIES.md](PRIORITIES.md) | What the trip is for, and what gets cut first |
| [OH_SHIT.md](OH_SHIT.md) | Clouded out and a hole just opened — hourly triage |
| [SITE_DATA.md](SITE_DATA.md) | Coordinates, horizons, every computed altitude and azimuth |
| [HORIZON_PHOTOS.md](HORIZON_PHOTOS.md) | How each site's horizon was measured, with the photos |
| [TARGETS.md](TARGETS.md) | Targets organised by colour palette, with windows and framing |
| [GEAR.md](GEAR.md) | The four systems, settings, power, dew, thermal |
| [CREATIVE_SHOTS.md](CREATIVE_SHOTS.md) | Silhouettes, light painting, portrait geometry |
| [ARRIVAL_SURVEY.md](ARRIVAL_SURVEY.md) | 3 PM day one — the 360° horizon survey |
| [SCHEDULE_3_NIGHTS.md](SCHEDULE_3_NIGHTS.md) | Full plan · [2 nights](SCHEDULE_2_NIGHTS.md) · [1 night](SCHEDULE_1_NIGHT.md) |
| [OPEN_ITEMS.md](OPEN_ITEMS.md) | Pre-trip checklist and unresolved questions |
| [predictions/](predictions/) | Independent forecasts of what the data will say on 9 Aug, one per model |
| [PREDICTION_PROMPT.md](PREDICTION_PROMPT.md) | Hand this to a fresh model to add another independent forecast |
| [FORECAST_FINDINGS.md](FORECAST_FINDINGS.md) | **How the forecast numbers are made, and what they're worth** · [rendered](findings.html) |
| [FORECAST_LOG.md](FORECAST_LOG.md) | Auto-generated forecast history |

## The interesting bits

**The site bearing was recovered from EXIF.** A 2023 iPhone photo taken at the lake still had
`GPSImgDirection` — 204.43° true. Cross-checking it against the moon's computed position at
that exact timestamp agreed to within **0.7°**, which validated both the phone's compass and
the ephemeris. Three other copies of nearby photos had been stripped by Google Photos and were
useless. See [HORIZON_PHOTOS.md](HORIZON_PHOTOS.md).

**The cabin's horizons were plate-solved from old snapshots.** Three February photos were
identified by their constellations — Orion, Pleiades + Aldebaran, Pleiades + Orion — and
combined with their EXIF timestamps that fixes altitude and azimuth exactly, which gives the
treeline height in each direction without ever standing there with a compass.

**The forecast tooling tracks model disagreement, not just the forecast.** `log_forecast.py`
pulls NWS gridpoint data plus ECMWF, GFS, ICON and GEM via Open-Meteo, and renders
[forecast.html](forecast.html). The useful output isn't the number — it's the *spread*. At nine
days out, GFS and ECMWF disagreed by 82 points about the same night. Watching that spread
narrow is the actual go/no-go signal.

**No number on the page comes from a single source.** Every figure — the headline percentage,
the verdict, the best hour, the trend chart, the movement table — is the median across every
source that reaches that night, taken hour by hour and then averaged over the window. NWS is one
member of the ensemble, not the answer; it stops at 7 days, so the trip nights are carried by the
models alone until the grid reaches them. Median rather than mean, because with GEM at 92 and
ECMWF at 38 for the same night a mean invents a number nobody forecast.

## Tooling

`publish.sh` runs hourly from cron and does the whole loop — grab a webcam frame, refresh the
forecast if there's a new package, rebuild the pages, commit, push. **The site updates itself.**

```bash
./publish.sh                # the hourly job; safe to run by hand
python3 webcam.py           # webcam frame + cloud estimate + model comparison
python3 log_forecast.py     # forecast snapshot, rebuild FORECAST_LOG.md + forecast.html
python3 make_calendar.py    # regenerate pittsburg-2026.ics (schedule with phone alarms)
python3 preview_forecast.py # forecast_preview.html from mock data, to preview the full UI
```

A forecast point is only recorded when NWS issues a new package *or* a model refreshes, so
each point on the chart is a genuinely separate forecast rather than a repeated reading.

## A note on what's here

The Pittsburg coordinates are deliberate — they're a public lake and a rental cabin, and the
whole method depends on showing the actual numbers. **Home coordinates, contact details and
service credentials have been kept out.** If you're reusing `log_forecast.py`, put your own
contact string in the `UA` constant; the NWS API asks for one.
