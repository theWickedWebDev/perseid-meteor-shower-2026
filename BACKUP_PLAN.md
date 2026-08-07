# Backup plan — if Pittsburg is clouded out

Written 7 Aug 2026, five days out, when nothing is decided yet. The point of writing it now
is that the decision has to be made on **Sunday 9 August** and Sunday is a bad day to start
thinking about it.

## The finding this rests on

A grid search of 180 points across the northeast found a sharp boundary at about **44°N**.
South of it the whole region is clear for the trip nights; north of it — including Pittsburg
— is not.

| | Tue 11 | Wed 12 | Thu 13 | mean |
|---|---|---|---|---|
| **Pittsburg (the lake)** | 62% | 20% | 88% | **57%** |
| Kanc, eastern half | 27% | 4% | 35% | 22% |
| Mt Shaw | 23% | 31% | 34% | 29% |
| 43.5 / −71.0 | 14% | 6% | 9% | 10% |

Two of the three nights are lost at the lake and workable 100–200 km south. Wednesday works
either way.

**The band is 43.0–44.0N, best around 43.5.** Below 43.0 the cloud comes back — 42.0 is as
bad as Pittsburg — so there is no reason to drive past it. Above 44.0 you are back under the
northern cloud.

Everything above is a 4–6 day forecast carrying **11% reliability**. The individual numbers
will move. What is more trustworthy is the *shape*: a boundary that appears across dozens of
grid cells and all three nights is a synoptic feature, not point noise.

## The decision, and when to make it

**Sunday 9 August.** That is when Night 1 reaches 2 days lead and Night 2 reaches 3 — the
range where the forecast first beats "always say overcast." Nothing before Sunday is worth
reacting to, and today is a good illustration: Wednesday looked excellent at the lake on
Thursday morning and had reshuffled completely by Friday.

Run both tools Sunday morning:

```bash
python3 log_forecast.py                    # the lake
python3 where_clear.py --lat <home> --lon <home> --html where.html
```

Then:

| Lake outlook Sunday | Do this |
|---|---|
| **Two or three nights ≤40%** | Go as planned. Nothing south is worth Bortle 2. |
| **One night ≤40%** | Go. Shoot that night hard, treat the others as visual and Perseids. |
| **No night ≤40% and the south is ≤30%** | Switch to Option C below. |
| **Everything unresolved (spreads >60)** | Go. An unresolved night at a dark site beats a confident night at a bright one, and the cabin is already paid for. |

The asymmetry is deliberate. **You cannot buy a dark sky with clear weather.** Bortle 2 is
the thing Pittsburg has that nowhere else within range does, and a marginal night there is
worth more than a good night at Bortle 4 *for the core specifically*. The south is only the
answer when the lake gives you nothing at all.

## Option C — the southern night

One night, hiked in, stripped down.

**Sites, in the order they currently rank.** All of these need eyes on them; the horizon
tool sees bare terrain and not the trees standing on it — which for Mt Shaw is the only open
question, since the terrain answer could not be better than it is.

| Site | Coordinates | Southern terrain | Notes |
|---|---|---|---|
| **Mt Shaw** | 43.74650, −71.27467 | **−1.2°** | Ossipee Range high point, 847 m by DEM. The southern skyline is *below the horizontal* across the whole arc — nothing within 25 km rises to eye level, so terrain is simply not a constraint. Best of every site measured, by a wide margin. A real hike, which suits the plan, and high enough to sit above valley fog — the failure mode that ruins clear nights in this region. |
| **Mt Major** | 43.51330, −71.28830 | **−0.6°** | Also unobstructed, 536 m, and a far shorter walk — roughly 1.5 miles against Mt Shaw's 4–5. Weaker on darkness though: at 43.51 the southern view looks straight down the Alton–Rochester–Portsmouth corridor, and the core sits at 10–17° in exactly that direction. Better choice for a Perseid-and-visual night than a core night. |
| **Kanc, eastern half** | −71.19 to −71.30 | 2–7° | Consistently open south. Roadside — the drive-up option, and the one to take if the chairs come. |
| **C.L. Graham Wangan** | ~44.021, −71.232 | 2.8° | Best terrain score measured. Coordinates are approximate — verify. |
| Kanc, Lincoln end | −71.49 to −71.59 | 11–17° | **Rejected.** Core behind a ridge by 22:30. |
| Echo Lake / Lafayette Place | 44.14 / 44.11, −71.68 | 7.9° | Marginal for the core — 2° of margin, which trees eat. Fine for Perseids. State park, check hours. |

**Kit — one backpack each.** This is a carry-in, not a drive-up, and the kit list is what
makes a summit viable at all.

Comes:
- Canon T8i + Sigma 18–35 f/1.8 on the Star Adventurer Mini, and a tripod
- Spare batteries, power bank, dew heater strip, red headlamp, spare cards
- iPhone — the only other "instrument"; visual is eyes
- Warm layers. 43.7N at ~2,800 ft in August still drops to single digits °C, and you are
  standing still from 21:00 to 03:00

Stays home:
- **EQ6-R, plywood pier plate, the three pavers** — the entire immovable rig
- **The 6SE.** 25 lb plus a fork mount does not go up a mountain in the dark
- The desktop and its power problem, and anything needing an extension cord

**Reconsider the chairs.** Two reclining camp chairs are on the main pack list for the
Perseid hours and they are right for a drive-up site. For a 4–5 mile carry they are the
single worst item in the bag — bulky, awkwardly shaped, 6–10 lb each. Closed-cell foam pads
weigh a pound, pack flat against the back panel, and let you lie flat, which is a better
posture for a radiant at 47–61° than any chair. Take the chairs if you drive to a pullout;
take pads if you walk up.

**Latitude:** aim for 43.3–44.1. There is no benefit below 43.0 — the cloud returns and the
light pollution rises as you approach the Massachusetts corridor. Core altitude gains only
1° per degree of latitude south, so this is a weather decision, not an astronomy one.

## What this plan does not know

- **Trees.** Every terrain figure here is bare-earth from a 90 m DEM. White Mountain forest
  adds 15–25 m, which at close range is several degrees, and is usually what actually blocks
  you.
- **Access.** Whether you can legally be at any of these at 1 AM.
- **Darkness.** Nothing here measures light pollution. Check every candidate against a
  light-pollution map before committing.
- **3 km of position moves the answer 6 points.** Mt Shaw's mean went from 23% to 29% when
  the coordinates were corrected by 3.4 km. Do not treat any single number as precise.
