# Site Data & Computed Astronomy

All times EDT. All azimuths true north. Computed for Aug 12, 2026 unless noted;
times shift **~2 minutes earlier per night** (Aug 14 astronomical dark ≈ 9:51 PM).

---

## 1. Locations

### Cabin

```
Decimal:  45.088278684047886, -71.324767296
DMS:      45° 5' 17.80" N,  71° 19' 29.16" W
Elevation: UNKNOWN — carrying ~455 m as a placeholder. Needs a topo lookup.
```

### Lake shooting spot

Derived from EXIF of `IMG_8460.jpeg` (iPhone 13 Pro, 2023-11-18 18:15:22 −05:00).

```
Decimal:  45.239267, -71.196433
DMS:      45° 14' 21.36" N,  71° 11' 47.16" W
Elevation: 666 m / 2,185 ft  (phone GPS — routinely ±50 m; horizontal fix was ±4.6 m)
```

**~20 km NNE of the cabin, 20–25 min up Route 3.**

> **Unresolved:** Stephen believes this is Third Connecticut Lake. Third Connecticut sits
> nearer 45.30 N; these coordinates are closer to the Second Connecticut stretch. The
> elevation matches Third better than Second, but the horizontal fix is far more reliable
> than the altitude. **Drop the coordinates on a map and confirm which lake.**

### Home observatory (reference)

`[home site — redacted]` — 2.2° south of the trip site, so the core sits about
2° *higher* at home than in Pittsburg. Traded away for Bortle 2.

---

## 2. The bearing measurement — how the lake site got confirmed

`IMG_8460.jpeg` retained full EXIF (the Google-processed copies had it stripped):

| Tag | Value |
|---|---|
| **GPSImgDirection** | **204.43° True North** |
| GPSDestBearing | 204.43° |
| GPS position | 45°14'21.36" N, 71°11'47.16" W (±4.6 m) |
| GPSAltitude | 666.05 m |
| DateTimeOriginal | 2023:11:18 18:15:22, offset −05:00 |
| Camera | iPhone 13 Pro, main camera, 5.7 mm (26 mm equiv), f/1.5 |
| Orientation | Rotate 90 CW → portrait frame |
| Composite FOV | 69.4° along the long axis |

**Independent cross-check:** the moon's computed position at that exact timestamp and
location was **azimuth 203.7°, altitude 16.8°** (topocentric apparent — includes the ~0.95°
lunar parallax and refraction). The phone's compass reported the camera at 204.4°, and the
moon sits just right of frame center. **Agreement within 0.7°** — the phone compass and the
ephemeris validate each other to well under a degree.

> Corrected 4 Aug 2026. This previously read 209.1° / 19.5°, computed geocentrically and
> wrong in azimuth besides. Recomputed with astropy. The conclusion was right and is now
> much better supported; the treeline recipe below inherited the altitude error.

**Frame coverage.** Portrait at 26 mm equiv = 69.4° tall × 54.9° wide. Centered on 204.4°,
that spans **azimuth 177° to 232°** — which contains the entire southern program.

**Lesson for the rest of the trip:** always work from camera originals. Google Photos and
most messaging apps strip GPS and GPSImgDirection. That one file settled a question three
stripped copies could not.

---

## 3. Horizons

### Lake spot — SOLVED

- **View bearing 204.4° (SSW)** — dead center of the target arc
- **Treeline ≈ 7.3°, PROVISIONAL** — was 10°, but that came off the moon fiducial when it
  carried a +2.7° altitude error. Correcting the anchor drops the treeline by the same amount.
  Direction is favourable: it buys about **29 more minutes on the core each night**. Treat as
  provisional until the 360° horizon survey on arrival measures it directly — that task is
  already first on the Night 1 schedule.
- Water in the foreground, gravel/flat launch area, no artificial light

Verification method if it needs tightening: the moon in IMG_8460 is a calibrated fiducial at
**16.8°** altitude. Frame is 4032 px over 69.4° → **58.1 px per degree**.

```
treeline altitude = 16.8° − (pixels from moon center down to treeline) / 58.1
```

### Cabin — MEASURED FROM PHOTOS

Full working in [HORIZON_PHOTOS.md](HORIZON_PHOTOS.md). Three frames were plate-solved off
identified constellations plus their exact EXIF timestamps.

| View | Azimuth | Horizon | Solved by |
|---|---|---|---|
| SSW | 195°–227° | **below 15.5°** | Orion |
| SW | 188°–262° | open; ~22° in one corner | Pleiades + Orion |
| W | 232°–290° | below 5° centre, ~25° at WNW edge | Pleiades + Aldebaran |
| NW (doorway) | centred ~309° | **~17°** | M31 framing |

**The trees live in the northwest and top out around 17°.** The southern and western skies —
where the entire refractor program runs — are clear.

- Perseid meteor field (NE, 47–61° altitude) explicitly fine
- Stephen wants the refractor pointed **SE → S → SW → WNW**

> **RESOLVED: Dark Shark is viable.** It never drops below 52.7° altitude, well clear of a ~17°
> northwest treeline. It stays in the plan.

### The 10-degree threshold

With a 10° horizon at the lake:

| Ridge height | Consequence |
|---|---|
| **Under 10°** | Everything works — Rho Oph, core, Trifid, full windows |
| 10–13° | Lose Rho Oph after ~10:15 and the core after ~11:00 |
| 13–16° | Rho Oph marginal at best; core only in the first half hour |
| Over 16° | Southern program in real trouble — need a different site |

---

## 4. Twilight & darkness — Aug 12, 2026

Solar noon **12:50 PM**. Sun declination +15.1°.

| Event | Time |
|---|---|
| Sunset | 7:58 PM |
| Civil twilight ends (−6°) | 8:30 PM |
| Polaris visible | ~8:45–9:00 PM |
| Nautical twilight ends (−12°) | 9:11 PM |
| **First usable sky frames (−15°)** | **9:30 PM** |
| **Astronomical dark (−18°)** | **9:56 / 9:54 / 9:52 PM** (nights 1 / 2 / 3) |
| Astronomical twilight begins | 3:43 AM |
| Sunrise | 5:41 AM |

**Usable dark ≈ 5 h 53 m per night**, lengthening by about 2 minutes a night.

Note: waiting for full dark costs almost nothing. The core transits at 9:06 PM and altitude
changes slowly near transit — only 0.5° is lost between 9:30 and 9:54. **The hard deadline
is setup, not darkness. Be aligned and framed by 9:15.**

---

## 5. Milky Way core — Sgr A*, RA 17h 45m 40s, Dec −29° 00'

**Transit 9:06 PM at 15.74° — 48 minutes before astronomical dark.** Already sinking west
by the time the sky is usable.

Recomputed with astropy 4 Aug 2026 for **Night 2 (12 Aug)**. The earlier table ran up to 0.4°
high and quoted one deadline for all three nights; the core actually sets about four minutes
earlier each night.

| Time | Altitude | Azimuth |
|---|---|---|
| 9:06 PM | 15.74° | 179° |
| 9:30 PM | 15.54° | 185° |
| **9:54 PM** | **14.94°** | **191°** |
| 10:30 PM | 13.32° | 199° |
| 11:00 PM | 11.33° | 205° |
| **11:17 PM** | **9.97°** | **209°** |
| 11:30 PM | 8.82° | 211° |
| 11:46 PM | 7.29° | 215° |
| Midnight | 5.84° | 217° |

**Usable window with a 10° ridge: 9:54 – 11:17 PM. Eighty-three minutes.**

Per-night deadline at 10°: **11:21 PM / 11:17 PM / 11:13 PM** for nights 1 / 2 / 3.

If the arrival survey confirms the treeline is nearer 7.3° than 10°, those become
**11:50 / 11:46 / 11:42 PM** — about 29 extra minutes a night, which is a third more core
time than the plan currently assumes.

The frame bearing of 204.4° means the core **enters on the left, crosses frame center at
about 11:00 PM, and exits right**. The composition improves for the first hour and then
decays — if you only get one set, shoot around 10:45–11:00.

**Band orientation changes through the window:**
- 9:56 – 10:45 → band runs diagonally → **landscape orientation**
- 11:00 onward → band stands vertical out of the SW → **portrait orientation**

---

## 6. Rho Ophiuchi / Antares — the tightest constraint of the trip

Rho Oph: RA 16h 25m 35s, Dec −23° 26' 50". Antares: RA 16h 29m 24s, Dec −26° 25' 55".
Complex center for framing ≈ **16h 27m, −25°**.

| Time | Altitude | Azimuth |
|---|---|---|
| 9:56 PM | 13.2° | 208° |
| 10:15 PM | 11.6° | 212° |
| **10:30 PM** | **10.1°** | 215° |
| 11:00 PM | 6.9° | 220° |
| 11:30 PM | 3.3° | 226° |

**Window with a 10° ridge: 9:56 – 10:30 PM. Thirty-five minutes.**

It transits at 7:52 PM — essentially at sunset — so by full dark it's already two hours past
the meridian. This is fundamentally a June target from 45°N, and an Arizona/Chile object in
general. **It is the first thing lost if anything slips.**

**Decision made: Rho Oph comes off the refractor's list.** 35 minutes at 10–13° altitude on
faint reflection nebulosity at 342 mm produces nothing. The Canon at 35 mm has it in frame
alongside the core and Trifid from the moment it's dark.

---

## 7. M8 + M20 (Lagoon + Trifid) — M20 at RA 18h 02m, Dec −23° 02'

**Transit 9:28 PM at 21.9°** — only 28 minutes before dark, so it's caught essentially at
its highest.

| Time | Altitude | Azimuth |
|---|---|---|
| 9:56 PM | 21.4° | 186° |
| 11:00 PM | 18.6° | 202° |
| Midnight | 13.4° | 216° |
| ~12:30 AM | 10° | ~222° |

**Window with a 10° ridge: 9:56 PM – 12:30 AM. Two hours thirty-five.**

The pair sits 1.5° apart and the 76EDPH field is 3.94° × 2.63° — **both fit in one frame**
with M21 and surrounding nebulosity. Neither is in the capture history. Magnitude ~6, so
bright enough that low altitude is survivable.

---

## 8. Perseid radiant — RA 3h 13m, Dec +58°

Circumpolar at 45°N. Never sets; minimum altitude 13°.

| Time | Altitude | Azimuth |
|---|---|---|
| 10:00 PM | 21° | 26° (NNE) |
| Midnight | 32° | 38° (NE) |
| 2:00 AM | 47° | 47° (NE) |
| 3:45 AM | **61°** | 48° (NE) |

**Rates scale with sin(altitude) — 2:00 AM to twilight is worth roughly 3× the evening.**

**Trail length also scales as sin(θ)**, θ being angular distance from the radiant: zero at
the radiant, maximum at 90°, back toward zero at 180°. The usual 40–60° recommendation is a
practical compromise that keeps the frame high in dark sky.

**Earth-grazers:** when the radiant is low (21° at 10 PM, 26° at 10:30) meteors enter at a
shallow angle and skim enormous distances — slow, long, often colored, and appearing far
from the radiant. **The lake window is Earth-grazer time.** Low count, but any single one is
the most photogenic meteor of the shower.

**Direction is predictable.** Every Perseid travels directly away from Perseus, so with the
radiant off the lower-left corner, every meteor in frame runs lower-left to upper-right on
the same diagonal. Compose for it.

**Sorting afterwards:** extend a streak backwards. Points at Perseus → Perseid. Doesn't →
sporadic, or Kappa Cygnid (radiant near zenith) or Delta Aquariid (radiant in the south).

---

## 9. M31 & the meteor field

M31: RA 0h 42.7m, Dec +41° 16'. **29° from the radiant** (measured 27.5° in Stellarium —
the difference is projection stretch).

| Time | M31 altitude | Radiant altitude |
|---|---|---|
| Midnight | 46° | 32° |
| 2:00 AM | 66° (az 88°) | 47° |
| 3:45 AM | 84° | 61° |

M31 transits 4:08 AM. **2:00–3:45 AM is simultaneously the best meteor rate and the best
M31 altitude — no conflict.**

**Framing decision (verified in Stellarium):** radiant sits ~7° inside the left edge and 12°
above the bottom — effectively at the lower-left corner. Field contains the
Cassiopeia–Cepheus Milky Way, Wizard Nebula, Caroline's Rose, Salt-and-Pepper, M103,
M31/M32/M110, Double Cluster, Deer Lick Group (NGC 7331 + Stephan's Quintet), Blue Snowball,
NGC 752, Lacerta. M33 falls just outside the bottom edge — let it go.

Cassiopeia and the radiant are on the same side of the sky, so pushing the radiant fully out
of frame also pushes out most of the Milky Way. **Corner placement is the right compromise.**

Skip the Double Cluster as an anchor — it's only 7° from the radiant.

**Field test in the dark:** frame it so Perseus is just out of shot. If the Double Cluster
appears in a test frame, you're too close.

**Field rotation:** on a fixed tripod the whole pattern rotates out of frame over hours. Either
re-aim every ~45 min, or track on the SAM and lock the field.

---

## 10. Veil / Cygnus Loop — RA 20h 51m, Dec +30° 40'

**Transit 12:17 AM at 75.6° due south.** At 3:45 AM it's at 47.2°, azimuth 269° (due west).

Entirely inside the SE→WNW arc, never below 47°, and **starting it a few minutes after
transit puts it on the west side of the meridian — no flip for the rest of the night.**

3° object in a 3.94° field — Eastern Veil, Western Veil, and Pickering's Triangle all in one
frame. Capture history has only NGC 6974, a single segment.

---

## 11. LDN 1235 "Dark Shark" — RA 22h 14m, Dec +73° 20'

**Northern object.** Circumpolar, but confined to azimuth 345°–023° all night.

| | |
|---|---|
| Transit | 1:39 AM, altitude **61.8°, due north** |
| At 10 PM | 52.7°, az 023° (NNE) |
| At midnight | 59.6°, az 014° |
| At 3:30 AM | 59.1°, az 345° |
| Minimum altitude | 28.4° |

**Never enters the SE→WNW arc.** Status depends entirely on the cabin's north obstruction
height. Note: circumpolar does **not** avoid a meridian flip — a German equatorial still
flips at upper culmination. What Dec +73 gives you is generous tripod clearance, so a large
meridian limit can be set safely.

---

## 12. Other targets in the southern arc

| Target | RA / Dec | Transit | Alt at transit |
|---|---|---|---|
| Barnard's E (B142/143) | 19h 41m / +10° 54' | 11:07 PM | 55.8° S |
| Sadr / IC 1318 | 20h 22m / +40° 15' | 11:48 PM | 85.2° S |
| Cocoon IC 5146 + B168 | 21h 54m / +47° 16' | 1:19 AM | 87.8°, near zenith |
| IC 1396 Elephant Trunk | 21h 39m / +57° 30' | 1:05 AM | northern — az 49° at 10 PM |
| M33 | 1h 34m / +30° 40' | after dawn | 69.5° at 3:45 AM, az 128° |

Sadr and Cocoon pass essentially overhead — immune to any horizon problem in any direction.

**Planets:** Saturn ~39° at 2 AM, rings still nearly edge-on following the 2025 ring-plane
crossing. **Jupiter unavailable** — near solar conjunction. Confirm both in Stellarium.
