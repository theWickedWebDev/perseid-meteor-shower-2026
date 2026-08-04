# Arrival Day — Horizon Survey

**Tue Aug 11, ~3:00 PM. Before you build anything.**

Everything in the plan rests on horizon estimates derived from old photos. Twenty minutes with
the phone replaces all of it with measurements.

---

## Do this first

**Use the 360° horizon-marking app** — the one you used to build the Stellarium pier landscape.
Walk to each position, drop points along the treeline, export.

### Positions to survey

1. **EQ6 tripod spot** — the important one
2. **SAM / Canon spot** at the cabin, if it's meaningfully different
3. **The lake launch**, when you get there that evening — same routine, same export

Survey from the **exact spot the tripod will stand.** With trees this close, moving five metres
changes the answer.

### Coverage

| Azimuth range | Spacing | Why |
|---|---|---|
| **170° – 240°** | **every 5°** | M8/M20, the core, the Trifid all live here. Highest-value data on the trip. |
| 240° – 300° | every 10° | Veil's tail, and the doorway |
| 300° – 030° | every 10° | Dark Shark, Polaris, the meteor field |
| 030° – 170° | every 15° | Completeness; nothing critical |

If you're short on time, **do 170°–240° and nothing else.** That band is where every deadline
target lives.

---

## What to send me

Plain az/alt pairs, one per line, degrees:

```
170 8.5
175 9.0
180 11.2
...
```

If the app exports a **Stellarium polygonal horizon file** directly, even better — send that and
I'll build the `landscape.ini` around it. The format Stellarium wants is:

```ini
[landscape]
name = Pittsburg Cabin
type = polygonal
polygonal_horizon_list = horizon.txt
polygonal_angle_rotatez = 0
```

with `horizon.txt` holding the same `azimuth altitude` lines.

Then you get a Stellarium view with your **real** ridgeline instead of the flat mathematical
horizon that's currently lying to you about exactly the low southern targets that matter.

---

## What the numbers will change

### The one that matters most: azimuth 186° – 222°

That's M8/M20's track, and it's the **unattended Scheduler job every single night**.

| Treeline there | Consequence |
|---|---|
| **Under 10°** | Full 2 h 35 m run, 9:56 PM – 12:30 AM. As planned. |
| 13° | Run ends ~12:05 AM. Lose 25 min. |
| **15°** | Run ends ~11:40 PM. **Lose 50 minutes every night** — 2.5 hours across the trip. |
| Over 18° | M8/M20 barely works from the cabin; rethink the unattended block |

If it's 15° or worse, tell me and I'll swap the Scheduler job to something higher and move
M8/M20 to the lake where you know the horizon is ~10°.

### Azimuth 300° – 030° — Dark Shark

Currently estimated at ~17° from the doorway photo. Dark Shark never drops below **52.7°**, so
anything under 40° is a non-issue. Only worth flagging if the trees turn out to be very tall.

### Azimuth 240° – 300° — the Veil's tail

Veil finishes at **azimuth 269°, altitude 47°** at 3:45 AM. Estimated treeline ~25° at the WNW
edge. Again, only a problem if it's much higher than expected.

### Due north — Polaris at 45.1°

Both mounts need to see it to polar align. **This is a hard blocker, not a nice-to-have.** If
Polaris is behind trees from the EQ6 spot, move the spot before you build anything.

---

## Also on the 3 PM walk

- [ ] **Confirm Polaris is visible** from the EQ6 position — see above
- [ ] **Pick the 6SE spot** far enough away that walking to the eyepiece doesn't put vibration
      into the subs. Not the same deck, not the same patch of soft ground.
- [ ] **Find the exterior AC outlet.** Measure the run to where the rig will stand.
- [ ] **Check the cabin router** — can the Pi reach it on the 50' ethernet? Note the subnet and
      how to see the client list, in case mDNS doesn't pass.
- [ ] **Cabin elevation** if you can get it — goes into `virtualgps` and Stellarium.
- [ ] **Ground condition** where the tripod goes. Soft ground settles overnight and drifts your
      polar alignment; stomp the legs in and let it sit an hour before fine alignment.

---

## At the lake, the same evening

While there's still light, before setting up:

- [ ] **Same 360° survey** from the exact tripod position
- [ ] **Compass to 204°** — confirm the water and the far ridge are where IMG_8460 says
- [ ] **Look for a foreground element** — a branch, a rock, a snag. The reference shots both have
      one and it's what gives the frame depth.
- [ ] **Check the wind.** Calm water doubles the composition with a reflection; chop kills it.
- [ ] **Take a level 24 mm landscape frame with location services ON**, so it records
      `GPSImgDirection`. That plus a visible horizon lets me compute ridge altitude at every
      azimuth independently of the app.

---

## Send it and I'll turn it around

Numbers, and I'll re-run every altitude table in [SITE_DATA.md](SITE_DATA.md) against the real
horizon, flag anything that no longer works, and build the Stellarium landscape file.
