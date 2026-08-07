# Backup plan — cancel Pittsburg, or go?

Written 7 Aug 2026. The decision gets made **Sunday 9 August**, and Sunday is a bad day to
start thinking about it.

## It is a binary

There is no mid-trip detour. Driving south from the cabin for one night is 2–3 hours each
way, arrives after the core has set, and costs the following night to exhaustion. So:

**A — Go to Pittsburg.** Three nights, Bortle 2, the full rig, the plan as written.

**B — Cancel, and do one night from home.** Wednesday 12 August, the Perseid peak, at a
summit about 1½–2 hours away. Canon + SAM-Mini in a pack, eyes and an iPhone for visual.

Nothing in between.

## Why A wins unless it is hopeless

Cancelling trades **three nights under Bortle 2 for one night under Bortle 4.** The bar for
that has to be high, and right now it is nowhere near being met:

| | chance of a usable core window |
|---|---|
| **A — at least one of three nights at the lake** | **68%** |
| B — Wednesday at Mt Shaw | 52% |
| B — Wednesday at Mt Major | 51% |

A is ahead on probability *and* on sky quality *and* has two extra nights of upside. Three
draws is worth a great deal: even writing off one night entirely only costs the joint figure
about ten points.

## The rule

Run this on Sunday morning:

```bash
python3 log_forecast.py                                    # the lake
python3 compare_sites.py --lat <home> --lon <home> --html compare.html
```

Then read the **joint** figure on the forecast page — the chance at least one night works —
against Wednesday's ensemble number at the summits:

| Sunday | Do |
|---|---|
| **Lake joint ≥ 55%** | **Go.** Comfortably ahead of one night anywhere else. |
| **Lake joint 40–55%** | **Go**, unless a summit is above 65% for Wednesday. Two extra nights and a darker sky are worth a modest deficit. |
| **Lake joint < 40%, and a summit is ≤ 20% with a span ≤ 30** | **Cancel and hike.** This is the case the backup exists for. |
| **Lake joint < 40% and no summit clears that bar** | **Cancel and stay home.** Do not hike into a sucker hole. |
| **Everything unresolved** (spans > 60 everywhere) | **Go.** Unresolved dark beats unresolved bright. |

You cannot buy a dark sky with clear weather, and Bortle 2 is the one thing Pittsburg has
that nothing else in range does. That is why the thresholds favour going.

**But the dark-sky argument does not apply to Wednesday itself.** The Perseid radiant climbs
to 47–61° and bright meteors punch through Bortle 4 perfectly well — you lose the faint tail,
not the show. So if the trip is cancelled, Wednesday at a summit is a genuinely good night
rather than a consolation prize. Which is exactly why the rule above keys on the *joint*
figure and not on Wednesday at the lake.

## Option B has a higher bar than the trip, not a lower one

At the lake the cabin is booked and you are there regardless. Waiting out a marginal night
costs nothing, so the trip's threshold is the ordinary one: **30% is shootable**.

The summit is the opposite. A drive, a climb, a carry, and no shelter — all committed hours
before you can see the sky. There is no waiting it out and no salvaging it. So the bar is
**not** the trip's threshold, and specifically it is not the sucker-hole band (30–40%),
which is exactly the range that looks acceptable on a forecast and delivers twenty minutes
of sky between cloud.

**Only make the hike if both hold:**

| | |
|---|---|
| **cloud ≤ 20%** | not 30, and certainly not the 30–40 band |
| **span ≤ 30 points** | the models must actually agree — that band is right 77% of the time, against 26% for a split forecast |

Both, not either. A 15% median drawn from sources spanning 80 points is one model winning a
vote, and it is precisely the reading that puts you on a summit at midnight under overcast.

**If neither the lake nor a summit clears its bar, do nothing.** That is a legitimate
outcome, not a failure of the plan. The Perseids run for weeks either side of the peak at
reduced rates, the core is up until October, and Sep 5–14 is the best fortnight of the whole
year at both sites — 33% usable against these dates' 30%, measured over thirty years. A
wasted Wednesday costs nothing except a Wednesday.

## Option B, if it happens

**Mt Major** — 43.51330, −71.28830. 536 m, about 1.5 miles and 1,100 ft of climb, roughly
1½ hours from home. Southern terrain **−0.6°**: nothing within 25 km rises to eye level.

**Mt Shaw** — 43.74650, −71.27467. 847 m, 4–5 miles, roughly 2 hours from home. Southern
terrain **−1.2°**, the best measured anywhere, and 300 m higher — which puts you above more
of the boundary-layer aerosol that scatters city light.

They are near-identical on cloud and on terrain. A crude sky-glow model over the core's arc
puts them within 5% of each other: I had assumed Shaw was clearly darker and the arithmetic
did not support it, because Laconia sits inside Shaw's south-west arc at 29 km and cancels
most of its distance advantage. **Mt Major is the sensible default**; Shaw only if the extra
elevation is worth the walk.

**Kit — one pack each.**

Comes: Canon T8i + Sigma 18–35 f/1.8 on the SAM-Mini, tripod, spare batteries, power bank,
dew strip, red headlamp, cards, iPhone, warm layers. It drops to single figures °C at 2,000
ft in August and you are standing still from 21:00 to 03:00.

Stays: the EQ6-R, the pier plate, the pavers, the desktop, the 6SE, anything on mains.

**Not the camping chairs.** They are right for a drive-up and the worst item in the bag for a
carry-in — bulky, 6–10 lb each. Closed-cell foam pads weigh a pound, pack flat, and let you
lie flat, which is the better posture for a radiant at 47–61° anyway.

**Timing on 12 Aug:** astronomical dark 21:54, core sets 23:17, Perseid peak 02:00–03:45,
dawn 03:45. Be on the summit by 21:00, which means leaving home around 18:30 for Major.

## Rejected, and why

**A Wednesday detour from the cabin.** Kanc east is 2.1 h each way, Mt Shaw 2.6 h, Mt Major
3.0 h. Even the nearest gets you there after the core has set, and costs Thursday night to
exhaustion. If the trip happens, it happens at the lake.

**Kanc, Lincoln end** (−71.49 to −71.59). The core goes behind a ridge by 22:30 — terrain
11–17°. Fine for meteors, useless for the core.

**Echo Lake / Lafayette Place.** Southern terrain 7.9° against a core at 10° by 23:30. Two
degrees of margin, which trees eat. Also inside a state park with posted hours.

## What none of this knows

- **Trees.** Every terrain figure is bare-earth from a 90 m DEM. White Mountain forest adds
  15–25 m, which is several degrees at close range and is usually what actually blocks you.
  Both summits are believed to have open ledges; neither has been verified.
- **Access.** Whether you can legally be on either at 1 AM.
- **Light pollution.** Nothing here measures it. The 5% figure above is a
  distance-and-population model, not an observation.
- **Precision.** Correcting Mt Shaw's coordinates by 3.4 km moved its cloud mean by 6 points.
  No number here is worth more than its nearest 10.
- **Stability.** On the morning of 7 Aug the southern sites read 22% mean against the lake's
  57%; by that afternoon it was 36% against 46%. At this lead the whole picture can invert
  inside a day. Nothing before Sunday means anything.
