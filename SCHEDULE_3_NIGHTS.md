# Schedule — All Three Nights Clear

Aug 11–14, 2026. Times EDT. Astronomical dark ~9:56 PM – 3:45 AM, shifting ~2 min earlier per
night (Aug 14 dark ≈ 9:51 PM).

Read [PRIORITIES.md](PRIORITIES.md) first. Core and meteors are the mission; everything else is
bonus.

---

## Every night is the same shape

> **Moose drive north → lake → core → back to the cabin for meteors.**

You're driving Route 3 at dusk every night to look for moose regardless, and the lake is where
that drive ends. So the core gets shot from the verified 204.4° site every clear night, and the
cabin's low southern horizon never has to be trusted.

| | Night 1 · Aug 11/12 | Night 2 · Aug 12/13 | Night 3 · Aug 13/14 |
|---|---|---|---|
| **Theme** | Shakedown | **Perseid peak + new moon** | **Creative session** |
| Lake, 8:30–11:45 PM | Core, wide + portrait | Core, wide + portrait | Core + **silhouettes & light painting** |
| Refractor, evening | **M8/M20** — only chance | porch, acclimating | porch, acclimating |
| Refractor, 1:00–3:45 | **Veil** | **Cocoon + B168** | **Dark Shark + vdB 152** |
| Palette | Teal + crimson | **Red + blue + dust** | Grey shapes + **blue knot** |
| Cabin, 12:30–3:45 AM | Meteors | **Meteors, peak hours** | Meteors |

**Integration:** M8/M20 ~2.3 h (night 1 only) · Veil ~3.5 h · Cocoon ~3 h · Dark Shark ~3 h.
At Bortle 2 that's comparable to 8–10 h per target from the pier. One palette per night —
see [TARGETS.md](TARGETS.md).

### The porch changes everything

**The scope can't be left outside** — theft worry, however unlikely. So there is no unattended
imaging block. On lake nights the refractor runs **1:00 to 3:45 AM**, just under three hours.

**The 3-season porch is what makes that work.** Unheated, so it tracks outdoor temperature. The
scope sits there fully assembled and powered from ~7 PM, camera cooling. By 12:15 the triplet is
**already at ambient** — no thermal defocus, no 45-minute settle — and the camera is at −10 °C.

- **Dew heaters OFF on the porch.** Under a roof the optics can't see open sky, so they can't
  radiatively cool below the dew point. No dew forms, and heaters would only fight the
  acclimation. On the moment it goes outside.
- **The whole tripod moves assembled**, so alt/az and the head registration survive. But the
  plate can shift and the ground settles — budget a **polar align check with a small
  adjustment**, not a from-scratch alignment.
- **At 4 AM it goes back on the porch, not into the warm cabin.** Cold optics carried into warm
  humid air fog instantly. The porch avoids it entirely.

**The casualty is M8/M20** — below 10° by 12:30, so the refractor only reaches it on night 1.

---

# NIGHT 1 · Tue Aug 11/12 — Build Night. **No moose drive, no lake.**

> ### Why night 1 is different
> The mount comes down and goes back up every night, and **polar alignment needs Polaris —
> not visible until ~8:45 PM.** You'd be departing for the moose drive at 7:15. Those can't both
> happen on a night when you're building from scratch.
>
> So night 1 stays at the cabin. You set up properly, align properly, and **mark the plate
> position** — which is what makes nights 2 and 3 work at all. Everything after tonight is
> repetition on marks.

The Canon shoots the core **from the cabin** tonight. The arrival survey will tell you whether
the low south works there; if it doesn't, the Canon does meteors and you've lost nothing
irreplaceable.

| Time | Action |
|---|---|
| **3:00 PM** | Arrive. Unload the truck. |
| **3:20** | **360° HORIZON SURVEY — [ARRIVAL_SURVEY.md](ARRIVAL_SURVEY.md).** Do it first, while the light's good and before you're committed to a spot. Dense every 5° across **170°–240°**. |
| **3:45** | **Pick positions.** EQ6 spot (clear north for Polaris, open south and west), 6SE spot far enough that walking to it doesn't shake the rig, Canon spot, and where the desktop lives. Find the AC outlet and measure the run. |
| **4:00** | **Desktop setup indoors** — tower, monitors, power. Then run the 50' ethernet out to where the Pi will sit. Do this after picking the mount spot, not before. |
| **4:45** | **Plywood plate down. Tripod on it, levelled to the bubble.** Note the leg extension against your tape marks. |
| **5:15** | Mount head on. Counterweights. OTA. **Balance RA and DEC.** |
| **6:00** | Cabling and power. **All USB connected before the Pi gets power** — hot-plug crashes the Pi 5. Boot, wait for the beep, Ekos connects, verify all five devices. |
| **6:30** | **Site coordinates in — `ssh astro`, edit `/etc/systemd/system/virtualgps.service` to 45.088279, −71.324767, `daemon-reload`, `restart virtualgps`, then `cat /tmp/vgps` to confirm.** Check the site in Ekos too. Cool to −10 °C. Rough daylight focus, EAF step 500. |
| **7:00** | **Daylight flats** with the panel, ~0.005 s at gain 100. |
| **7:30** | Eat. Assemble the SAM and the 6SE. Load the M8/M20 sequence, 120 s. |
| **7:58** | Sunset. |
| **8:30** | Civil twilight ends. **Set park position = home/Polaris.** Verify `ON_COORD_SET=TRACK`, never SYNC. |
| **8:45** | **POLAR ALIGN.** Polaris is up. Take your time — tonight's alignment is the one you're reproducing for the rest of the trip. |
| **9:10** | ⭐ **MARK THE PLATE.** Stake it, or outline it, or both. Mark which corner faces north. **Then do not touch the alt/az bolts again all trip.** |
| **9:15** | Plate-solve test, autofocus V-curve (step 30, 15 steps), start guiding. Target HFR ~1.2. |
| **9:30** | Polar align the SAM. Frame the Canon — core from the cabin if the survey allows, otherwise the Cassiopeia/M31 meteor field. |
| **9:56** | **Dark. Refractor → M8/M20.** Canon running. |
| **10:00–12:00** | 6SE on the southern showpieces — **M8, M17 Swan, M16 Eagle, M22, M11, M20.** Invisible from home and only up now. |
| **12:15 AM** | M8/M20 drops below 10°. **Slew to Veil** — just past its 12:17 transit, so west of the meridian, **no flip all night**. |
| **12:30** | Canon to the meteor field if it wasn't already. 20 s, f/1.8, ISO 3200, continuous. |
| **2:00–3:45** | Perseids. 6SE on NGC 7331 + Stephan's Quintet, M31, M33, Saturn. |
| **3:45** | Twilight. Stop capture. |
| **4:00** | **Teardown practice.** Move the **whole tripod assembled** — head, OTA, counterweights, alt/az untouched — onto the porch. That's where it lives for the rest of the trip, and moving it in one piece is what preserves the alignment. Time yourself; you repeat this twice. |

**What night 1 delivers:** a marked plate, a known-good alignment, a proven solve/focus/guide
chain, and a teardown you've done once in the dark. That's what buys you nights 2 and 3.

---

# NIGHT 2 · Wed Aug 12/13 — Perseid Peak, New Moon

Everything is set up. Same shape, but the back half of the night is the point.

| Time | Action |
|---|---|
| **5:00 PM** | **Assemble on the porch.** Head, counterweights, OTA, **balance RA and DEC**, cables dressed. Comfortable, lit, sitting down — this is where the "why won't it connect" half-hours normally happen. |
| **5:45** | Pi up, Ekos connects, all five devices verified. **Start the camera cooling** — the porch is at ambient, so −10 °C is an easy 22 °C delta. **Dew heaters OFF** — under a roof it can't dew, and heat fights the acclimation. |
| **6:15** | Confirm the tripod is still seated on the plate outside, bagged and level. Fix whatever broke last night. **Load the car — PACK THE 6SE**, its southern targets only exist while you're at the lake. |
| **7:15** | **Depart. Moose drive.** |
| **8:10** | **Earth's shadow + Belt of Venus** at azimuth 112°, off your right heading north — dark band with a pink edge rising out of the east. Gone by 8:35. Bright twilight: ~1/10 s, f/5.6, ISO 100, underexpose slightly. |
| **8:30** | Arrive the lake. Setup is quick now — you did it last night. |
| **8:45** | Foreground frames. |
| **9:00–9:30** | Polar align, frame to 204°, focus, lock. |
| **9:56** | **Dark. Core.** Landscape → portrait as before. Take more 35 mm frames — last night told you which worked. |
| **11:25** | Core at 10°. Pack. |
| **11:45** | Depart. |
| **12:10 AM** | Cabin. Card off to the desktop, verify two or three frames opened sharp. Fresh card in. |
| **12:15** | **Carry the scope out from the porch.** Already at ambient, camera already cold. **Polar align check** — plate may have shifted, expect a small adjustment. **Dew heaters ON now**, low setting. |
| **1:00** | **Refractor → Cocoon IC 5146 + B168.** Red core, blue rim, black dust river — the best colour target of the trip, transits at 87.8°, essentially zenith. |
| **1:00** | Canon onto the SAM, Cassiopeia/M31 field. 20 s, f/1.8, ISO 3200, continuous. |
| **1:19** | ⚠️ **Near-zenith meridian flip.** These are the awkward ones — azimuth swings fast, clearance gets tight. Supervise it. (Alternative: don't start until 1:25, just past transit, and track down the west side with no flip. Costs 55 min, buys certainty.) |
| **2:00** | **Peak window.** Radiant 47° → 61°. Rates roughly 3× the evening. |
| **2:00–3:45** | Both of you outside. Lawn chairs. Camera runs itself. **This is what the trip is for.** |
| **~2:55** | **Doorway frames — ten minutes, not a session.** **Draco's head** passes the NW door at 37° altitude, the only recognizable thing that does so during your cabin hours. Radiant is ~60° off, near-ideal for trail length. Grab a handful, then put the Canon back on the open-sky field. |
| **3:45** | Twilight. |
| **4:00** | Park, ramp cooling off, **carry the scope back to the porch — not into the warm cabin.** Cold optics in warm humid air fog instantly. Pull cards. |

---

# NIGHT 3 · Thu Aug 13/14 — Creative Session

Core and meteors are banked. Tonight the Canon does the fun stuff. See
[CREATIVE_SHOTS.md](CREATIVE_SHOTS.md).

| Time | Action |
|---|---|
| **3:00 PM** | **Assemble on the porch** — pull the whole rebuild into the afternoon. Head, counterweights, OTA, balance, cables, Pi, Ekos, devices verified. Camera cooling. **Heaters off.** |
| **5:00** | **Dinner at Buck Rub Pub** — 45.0658, −71.3437. 2.9 km SSW, ~5 min, opposite direction from the moose drive. Pull the forecast and the Kp index while you have a table. |
| **6:40** | Back. Final checks. **Load the car — PACK THE 6SE.** **Pack the creative kit** — second headlamp, amber gel, something to drop the tripod to ~0.5 m, a marker for the subject's spot. |
| **7:15** | **Depart. Moose drive.** |
| **8:10** | **Earth's shadow + Belt of Venus** at azimuth 112°, off your right heading north — dark band with a pink edge rising out of the east. Gone by 8:35. Bright twilight: ~1/10 s, f/5.6, ISO 100, underexpose slightly. |
| **8:30** | Arrive. Setup. |
| **8:45** | Foreground frames. |
| **9:00–9:30** | Polar align, frame to 204°, focus. |
| **9:56** | **Dark. Core, landscape.** Get the stacking frames done efficiently — you already have two nights of them, so twenty good subs is plenty. |
| **10:45** | **Portrait, vertical band.** Twenty frames, then stop. |
| **11:05** | **Drop the tripod to knee height. Creative session.** Subject 5–7 m out. 10 s, f/1.8, ISO 3200, untracked. Silhouettes, light-painted foreground, headlamp beam into the sky, reflections if the water's calm. **Twenty minutes, twenty-plus frames.** |
| **11:25** | Core at 10°. Done. Pack. |
| **11:45** | Depart. |
| **12:10 AM** | Cabin. Card off, verify. Fresh card in. |
| **12:15** | **Carry the scope out from the porch.** At ambient, camera cold. **Polar align check**, expect a small adjustment. **Dew heaters ON**, low. |
| **1:00** | **Refractor → Dark Shark + vdB 152.** Centre Dec +71° 47', long axis N–S. Canon → Cassiopeia/M31. |
| **1:30** | Supervise the flip. |
| **2:00–3:45** | Perseids. Rates are down from peak but still excellent. 6SE for whatever's left on the list. |
| **3:45** | Twilight. |
| **4:00** | Park, ramp cooling off, **scope back onto the porch**, pull cards. Sleep. Pack out in the morning. |

---

## Lake kit — load before 7:15 every night

**Four separate supplies, one per system — no single point of failure.**
Canon → **LP-E17 batteries** (swap at the 10:45 landscape→portrait break) ·
dew strap → **USB power bank** · 6SE → **lead-acid direct, 12 V** ·
SAM → **2×AA lithiums, bring a spare pair**. Power box and coupler ride in the truck as backup.
Fuse the alligator lead at the battery end.

**PACK THE 6SE** — fork, tripod, eyepieces, 32 mm Plössl. **Leave the EQ wedge home.** And set
the NexStar handset site to **45° 14' N / 71° 12' W** before you go, not your home coords.

Full list in [SCHEDULE_1_NIGHT.md](SCHEDULE_1_NIGHT.md#lake-kit).

---

## Standing notes

- **Flats:** daylight panel flats on night 1 cover all three nights provided you don't rotate the
  camera or change the optical train. If you do either, reshoot them.
- **Cards:** one per night. Swap, never format in the field.
- **The 6SE's southern showpieces** — M8, M17, M16, M22, M11 — only exist 9:56 PM to midnight,
  which is exactly when you're at the lake. If your friend wants them, **bring the 6SE along**;
  the fork travels fine and the lake has the horizon for it.
- **Every clear night, the same shape.** If a night clouds out, the next clear one just becomes
  whichever night you hadn't done yet.
