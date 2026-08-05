# Future

Noted 5 Aug 2026, during the trip build. Nothing here is scheduled; it is the shape of the
thing if it gets picked up after 14 August.

Two directions, and they are separable. The first keeps the astronomy and drops the
location. The second drops the astronomy entirely and keeps the one thing this project
does that nothing else does.

---

# Direction one — any site, any target

## The idea

Right now this answers one question about one place on three specific nights: *will the
Milky Way core be shootable from the lake on 11–13 August.* The machinery underneath is
more general than that. Point it at an arbitrary location and an arbitrary target and it
would answer *can I shoot this, from here, on that night* — starting with the back yard.

## What already generalises

These take a latitude and longitude and nothing else. They work anywhere on earth today.

- the multi-model ensemble and its hour-by-hour median consensus
- the pooled GEFS / ECMWF-ENS / GEM-ENS members behind the joint probability
- the 30-year ERA5 climatology base rate (`archive-api.open-meteo.com`)
- lead-time skill measurement against the previous-runs API
- the IQR agreement gate, the bootstrap CIs resampled by night episode
- `nightwatch.py` — it takes frames and returns flux, star counts and sky brightness. It
  does not care where the frames came from.

## What is specific to Pittsburg, and what replaces it

| Tied to this trip | At another site |
|---|---|
| the Lopstick webcam, its plate solve, its sky mask | your own subs — same `nightwatch.py`, better data, because it measures the exact patch of sky you are shooting through |
| HRRR (CONUS only), NWS/GYX text package (US only) | drop them, or swap the regional model for whatever covers the location |
| GOES-19 | unchanged over the Americas; Meteosat or Himawari elsewhere |
| `SITE`, `WEBCAM_SITE`, `NIGHTS`, the `ASTRO` dict | configuration |
| `CORE_HR` / `LATE_HR`, tuned to the core's August transit | derived from the target's own transit |

The webcam is the only real loss, and only because it was a workaround for the site being
five hours away. At home you are standing there.

## Three pieces that do not exist yet

1. **Target resolution.** Name to coordinates to an altitude curve for the site and date.
   Astropy is already in the stack; this wants astroquery for the SIMBAD lookup. Small.

2. **The Moon.** Ignored throughout, because this trip was deliberately planned on a new
   moon. Generalised it is often the binding constraint — phase, altitude, and angular
   separation from the target. A 60% moon 30° away ruins a night the cloud forecast calls
   perfect. Small, also astropy.

3. **A real horizon profile.** `CORE_UP_MIN = 10.0` is a hardcoded stand-in for the
   treeline at one lake. From a back yard the horizon is trees, a roofline, a neighbour's
   garage, and it differs at every azimuth. Take a phone panorama, extract horizon altitude
   per azimuth, store the profile. Then "is my target up" means *up above what is actually
   in front of me*, which is the question being asked. This is the piece that would make it
   specific to a place rather than generically correct.

## The honest limitation, which is also the point

Measured on this project's own data: forecasts at day 7 carry **37.2 points of mean error**
against **27.0** for simply saying "overcast every night." At a week out the cloud forecast
is worse than a constant guess. So the truthful answer to *can I shoot in seven days* is
almost always:

> climatology says roughly X% for this date, the forecast adds nothing yet, ask again on
> day 4.

That is the product. Not *will it be clear on the 12th* — every planning tool answers that
one confidently and wrongly — but **is it worth deciding yet, and when will it be.** The
machinery for the second question already exists here, because the skill curve was measured
rather than assumed. And it is measured per site, so a back yard would earn its own.

## Why the home version would end up better than this one

The skill curve here rests on **8 night episodes**, because that is how many nights this
site has been observed, and it never gets more — there is one trip. A fixed site logs every
clear night indefinitely: hundreds of episodes, per-model error bars that actually converge,
a climatology checked against its own record instead of ERA5 alone, and a horizon profile
that stops being a guess.

It loses a webcam and gains the one thing this project keeps apologising for: enough n.

## Rough shape of the work

- a day to lift the hardcoded site and dates out into configuration
- a day for target resolution and the moon
- a day for the horizon profile
- the skill curve starts uncalibrated and needs a few weeks of logging before it means
  anything, so it should say so on the page rather than imply confidence it has not earned

---

# Direction two — a general weather forecast

Not astronomy at all. Possibly the stronger idea, and it needs less work than direction one.

## Don't build a weather app

Weather apps exist, they are fine, and a hand-rolled one would be worse at all the ordinary
parts. The value here is a thin layer sitting *on top* of an ordinary forecast, doing three
things no consumer app does. Keep the surface small.

## The three things

**1. Show the disagreement instead of hiding it.**

Every consumer app collapses six models into one confident number. This one already renders
`Models 0–98%` and refuses to call a night when the IQR crosses 40. That single behaviour —
*the models do not agree, so I am not going to pretend* — is the whole differentiator, and
it is already built and already shipping.

**2. Publish a measured skill horizon, per variable.**

This is the piece worth building. Cloud, temperature and rain have completely different
forecastability, and no app distinguishes them: a day-9 rain percentage is rendered in the
same typeface as tomorrow's. The skill machinery here already scores forecasts against the
previous-runs API. Run it per variable and the page can state, measured rather than assumed:

```
temperature   trustworthy to day 7
cloud         to day 4
rain amount   to day 2
rain timing   don't
```

Measured at the location in question, not quoted from a paper. Most of the frustration with
forecasts is not that they are wrong, it is that they never say which of their own numbers
to believe.

**3. Fall back to the base rate, out loud.**

When the forecast adds nothing over climatology — which at this site is anywhere past day 6
for cloud — say so and give the 30-year number instead. Already implemented for the trip
nights; generalises directly.

## What would need changing

The data layer is largely done. `inject_schedule.py` already pulls temperature,
precipitation, probability, wind and WMO codes hourly, and the daytime section already
renders them with icons. Most of the work is re-pointing existing plumbing.

The verdicts are what is astronomy-specific. `GO <= 30%` cloud means nothing to a person
deciding about a walk. Replace it with a small set of ordinary questions, each with its own
threshold on its own variable — will the walk stay dry, do I need a coat, is it worth
hanging washing out. That is configuration, not architecture.

## Why this one might be better than direction one

It benefits from the same fixed-site advantage — every day logged, error bars that converge
— but it does not have to wait for clear nights to learn anything. Every day is a data
point, including the overcast ones. The skill curve would calibrate several times faster
than an astronomy version of the same thing.
