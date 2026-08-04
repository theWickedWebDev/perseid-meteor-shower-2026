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

<!-- GENERATED FROM schedule_data.py — edit there, then run make_schedules.py -->

| Time | Action |
|---|---|
| **3:00 PM** | **ARRIVE - unload the truck** Move fast. Every minute before dark is load-bearing today. |
| **3:20** | **360 HORIZON SURVEY - do this first** Phone app, mark the treeline from the exact spot the tripod will stand. Dense every 5 deg across 170-240. That band is where M8/M20, the core and the Trifid all live. |
| **3:45** | **Pick positions** EQ6 spot (clear north for Polaris - watch for eaves and the north wall, not trees). 6SE spot far enough that walking to it doesn't shake the rig. Canon spot. Desktop. Find the AC outlet and measure the run. |
| **4:00** | **Desktop setup indoors, then run the ethernet** Tower, monitors, power. Run the 50ft ethernet out to where the Pi will sit. Do this after picking the mount spot, not before. |
| **4:45** | **Plate down, tripod on it, level to the bubble** Pavers underneath if the ground is soft - seat them roughly coplanar or the plywood rocks. Note the leg extension against your tape marks. |
| **5:15** | **Head on, counterweights, OTA, balance** Balance RA on the counterweight shaft and DEC in the dovetail. |
| **6:00** | **Cabling and power - USB FIRST** All USB connected before the Pi gets power. Hot-plug crashes the Pi 5. Boot, wait for the beep, Ekos connects, verify all five devices. |
| **6:30** | **Site coords in - virtualgps on the Pi** ssh astro / sudo nano /etc/systemd/system/virtualgps.service / set 45.088279, -71.324767 + elevation / sudo systemctl daemon-reload / sudo systemctl restart virtualgps / cat /tmp/vgps to confirm. Then check the site in Ekos. Wrong coords means wrong LST and wrong meridian-flip timing. Cool to -10C. Daylight focus, EAF step 500. |
| **7:00** | **Daylight flats** ~0.005s at gain 100 with the panel. These cover all three nights unless you rotate the camera or change the optical train. |
| **7:30** | **Eat. Assemble the SAM and the 6SE** Load the M8/M20 sequence, 120s. Sunset 19:58 - the SAM's latitude wedge goes to 45 now, in the light, rather than later by headlamp. |
| **8:30** | **Set park position = home/Polaris** Verify ON_COORD_SET=TRACK, never SYNC. |
| **8:45** | **POLAR ALIGN** Polaris is up. Take your time - tonight's alignment is the one you reproduce for the rest of the trip. |
| **9:10** | ***** MARK THE PLATE ***** Stake it, outline it, both. Mark which corner faces north. Then DO NOT TOUCH THE ALT/AZ BOLTS again all trip. This is what makes nights 2 and 3 possible. |
| **9:15** | **Plate-solve test, autofocus V-curve, start guiding** Step 30, 15 steps. Target HFR ~1.2. |
| **9:30** | **Polar align the SAM, frame the Canon** Core from the cabin if the arrival survey allows it, otherwise the Cassiopeia/M31 meteor field. Decide from the survey, not from hope. |
| **9:56** | **ASTRONOMICAL DARK - scope to M8/M20** 120s subs, gain 100, offset 50, dither 3px. THE ONLY NIGHT the refractor can reach this pair - on lake nights it's below 10 deg before you get back. |
| **10:00** | **6SE - the southern showpieces** M8, M17 Swan, M16 Eagle, M22, M11, M20. Invisible from home and only up now. This is the why-did-we-drive-here moment. |
| **12:15 AM** | **Scope to the Veil / Cygnus Loop** Just past its 12:17 transit so it's west of the meridian - no flip all night. Teal OIII and crimson Ha filaments. |
| **12:30** | **Canon to the meteor field** 20s, f/1.8, ISO 3200, continuous. |
| **2:00** | **Perseids building** 6SE on NGC 7331 + Stephan's Quintet while it's high. Then M31, M33, Saturn. |
| **3:45** | **Twilight - stop capture** Then TEARDOWN PRACTICE: pull the OTA and counterweights, lift the head off without touching alt/az, and move it TO THE PORCH - that's where it lives for the rest of the trip. Time yourself, you repeat this twice. |

<!-- END GENERATED -->

**What night 1 delivers:** a marked plate, a known-good alignment, a proven solve/focus/guide
chain, and a teardown you've done once in the dark. That's what buys you nights 2 and 3.

---

# NIGHT 2 · Wed Aug 12/13 — Perseid Peak, New Moon

Everything is set up. Same shape, but the back half of the night is the point.

<!-- GENERATED FROM schedule_data.py — edit there, then run make_schedules.py -->

| Time | Action |
|---|---|
| **5:00 PM** | **Assemble the rig ON THE PORCH** Head, counterweights, OTA, balance RA and DEC, cables dressed. Comfortable and lit - this is where the why-wont-it-connect half-hours normally happen. |
| **5:45** | **Pi up, Ekos connected - START COOLING** All five devices verified. Porch is at ambient so -10C is an easy 22C delta. DEW HEATERS OFF - under a roof it cannot dew, and heat fights the acclimation. The triplet needs these five hours to reach ambient. |
| **6:15** | **Check the tripod outside** Still seated on the plate, bagged, level. Alt/az bolts untouched so alignment carries over. |
| **7:00** | **LOAD THE CAR - lake kit** 6SE + fork + tripod + eyepieces + 32mm Plossl (LEAVE THE EQ WEDGE HOME). Canon + Sigma with the 72mm UV/IR filter fitted + lens hood. SAM + tripod, wedge at 45. POWER, one supply per system: LP-E17 batteries for the camera (all four, charged) - USB power bank for the dew strap - lead-acid + FUSED alligator lead for the 6SE - 2xAA lithiums plus spares for the SAM. Power box and coupler stay in the truck as backup. USB dew strap. Power bank + hand warmers as backup. Spare SD cards. IR thermometer. Two headlamps + amber gel. Something to drop the tripod to 0.5m. Chairs, layers, bug spray, ID. |
| **7:15** | **DEPART - moose drive north on Route 3** The 6SE's best targets are southern and only up 9:54 to midnight - exactly when you're at the lake. Leave it behind and M8, M17, M16, M22 and M11 do not happen this trip. Sunset 7:58. |
| **8:10** | **Earth's shadow + Belt of Venus** Azimuth 112, off your right heading north. Dark band with a pink edge rising out of the east. Gone by 8:35. ~1/10s, f/5.6, ISO 100, underexpose slightly. |
| **8:30** | **Arrive the lake - set up** Civil twilight ends. Tripod and SAM out immediately. |
| **8:45** | **FOREGROUND FRAMES - only chance** Glow still on the water. f/2.8, ISO 800, 60-120s. These are your blend layer and there is no second chance tonight. |
| **9:00** | **Polar align the SAM - frame to azimuth 204** Polaris is behind you over land. SAM latitude wedge should be at 45. |
| **9:15** | **Focus, check corners, lock composition** Hard deadline isn't darkness, it's being ready for it. |
| **9:54** | **ASTRONOMICAL DARK - shoot the core** Landscape, 18mm. Also several at 35mm: Rho Oph + core + Trifid in one frame. Rho Oph is at 13.2 deg and dying - shoot it FIRST. |
| **10:35** | **RHO OPH DEADLINE - below 10 deg, gone for the year** Last frames of Rho Oph now. Core at 13.6 and sliding toward frame centre. |
| **11:00** | **Switch to PORTRAIT** Band standing vertical out of the water. Core dead centre at 11.8 deg. This is the postcard. |
| **11:17** | **CORE DEADLINE - 10 deg. South is finished** Last frames. Pack up. Verified against astropy for this specific night - the core sets four minutes earlier each night, so this is not the same time every evening. If the arrival survey finds the treeline lower than 10 deg you gain roughly another half hour; re-check on site. |
| **11:45** | **Depart the lake** Moose peep on the way back to the cabin. |
| **12:10 AM** | **Back at the cabin** Check ntfy / dashboard. Pull the SD card, copy to the desktop, verify two or three frames opened and are sharp. Fresh card in. |
| **12:15** | **Carry the scope out from the porch** Already at ambient, camera already cold. Onto the tripod - alt/az untouched, so the alignment carries over. Polar align CHECK - the plate may have shifted and the ground settles, so expect a small adjustment. Not from scratch. DEW HEATERS ON NOW, low setting. Target 2-5C above ambient, no more - err low on the triplet. |
| **1:00** | **Scope on Cocoon IC 5146 + B168** Red core, blue rim, black dust river - the best colour target of the trip. Transits 1:19 at 87.8 deg, essentially zenith. WARNING: near-zenith meridian flips are the awkward ones. Supervise it, or start after 1:25 and skip the flip entirely. |
| **1:00** | **Canon meteor run - Cassiopeia/M31 field** 20s, f/1.8, ISO 3200, continuous. Radiant in the lower-left corner. Dew heater on the lens. |
| **1:30** | **Supervise the meridian flip** Watch it through. Clearance is tight near zenith and a failed flip costs the rest of the night. |
| **2:00** | **PERSEID PEAK HOURS** Radiant climbs 47 to 61 deg. Rates roughly triple over the evening. Camera runs itself - both of you outside, in chairs, looking up. |
| **3:45** | **Astronomical twilight - stop capture** Park the mount, ramp cooling off gradually, pull cards. SCOPE BACK ON THE PORCH, not into the warm cabin - cold optics in warm humid air fog instantly. |

<!-- END GENERATED -->

---

# NIGHT 3 · Thu Aug 13/14 — Creative Session

Core and meteors are banked. Tonight the Canon does the fun stuff. See
[CREATIVE_SHOTS.md](CREATIVE_SHOTS.md).

<!-- GENERATED FROM schedule_data.py — edit there, then run make_schedules.py -->

| Time | Action |
|---|---|
| **3:00 PM** | **Assemble the rig ON THE PORCH** Head, counterweights, OTA, balance RA and DEC, cables dressed. Comfortable and lit - this is where the why-wont-it-connect half-hours normally happen. |
| **3:45** | **Pi up, Ekos connected - START COOLING** All five devices verified. Porch is at ambient so -10C is an easy 22C delta. DEW HEATERS OFF - under a roof it cannot dew, and heat fights the acclimation. The triplet needs these five hours to reach ambient. |
| **4:15** | **Check the tripod outside** Still seated on the plate, bagged, level. Alt/az bolts untouched so alignment carries over. |
| **4:30** | **Pack the creative kit** Second headlamp, amber gel, something to drop the tripod to ~0.5m, a marker for the subject's spot. |
| **5:00** | **Dinner at Buck Rub Pub** 45.0658, -71.3437. 2.9km SSW of the cabin, ~5 min, opposite direction from the moose drive. Rig already assembled on the porch this afternoon. Pull the forecast and the Kp index while you have a table. |
| **7:00** | **LOAD THE CAR - lake kit** 6SE + fork + tripod + eyepieces + 32mm Plossl (LEAVE THE EQ WEDGE HOME). Canon + Sigma with the 72mm UV/IR filter fitted + lens hood. SAM + tripod, wedge at 45. POWER, one supply per system: LP-E17 batteries for the camera (all four, charged) - USB power bank for the dew strap - lead-acid + FUSED alligator lead for the 6SE - 2xAA lithiums plus spares for the SAM. Power box and coupler stay in the truck as backup. USB dew strap. Power bank + hand warmers as backup. Spare SD cards. IR thermometer. Two headlamps + amber gel. Something to drop the tripod to 0.5m. Chairs, layers, bug spray, ID. |
| **7:15** | **DEPART - moose drive north on Route 3** The 6SE's best targets are southern and only up 9:54 to midnight - exactly when you're at the lake. Leave it behind and M8, M17, M16, M22 and M11 do not happen this trip. Sunset 7:58. |
| **8:10** | **Earth's shadow + Belt of Venus** Azimuth 112, off your right heading north. Dark band with a pink edge rising out of the east. Gone by 8:35. ~1/10s, f/5.6, ISO 100, underexpose slightly. |
| **8:30** | **Arrive the lake - set up** Civil twilight ends. Tripod and SAM out immediately. |
| **8:45** | **FOREGROUND FRAMES - only chance** Glow still on the water. f/2.8, ISO 800, 60-120s. These are your blend layer and there is no second chance tonight. |
| **9:00** | **Polar align the SAM - frame to azimuth 204** Polaris is behind you over land. SAM latitude wedge should be at 45. |
| **9:15** | **Focus, check corners, lock composition** Hard deadline isn't darkness, it's being ready for it. |
| **9:52** | **ASTRONOMICAL DARK - shoot the core** Landscape, 18mm. Also several at 35mm: Rho Oph + core + Trifid in one frame. Rho Oph is at 13.2 deg and dying - shoot it FIRST. |
| **10:32** | **RHO OPH DEADLINE - below 10 deg, gone for the year** Last frames of Rho Oph now. Core at 13.6 and sliding toward frame centre. |
| **11:00** | **Switch to PORTRAIT** Band standing vertical out of the water. Core dead centre at 11.8 deg. This is the postcard. |
| **11:05** | **CREATIVE SESSION - drop the tripod to knee height** Subject 5-7m out. 10s, f/1.8, ISO 3200, UNTRACKED. Silhouettes, light-painted foreground, headlamp beam. Light in a 1-2s PULSE from the side, never a hold. Shoot 20+ frames, the failure rate is high. |
| **11:13** | **CORE DEADLINE - 10 deg. South is finished** Last frames. Pack up. Verified against astropy for this specific night - the core sets four minutes earlier each night, so this is not the same time every evening. If the arrival survey finds the treeline lower than 10 deg you gain roughly another half hour; re-check on site. |
| **11:45** | **Depart the lake** Moose peep on the way back to the cabin. |
| **12:10 AM** | **Back at the cabin** Check ntfy / dashboard. Pull the SD card, copy to the desktop, verify two or three frames opened and are sharp. Fresh card in. |
| **12:15** | **Carry the scope out from the porch** Already at ambient, camera already cold. Onto the tripod - alt/az untouched, so the alignment carries over. Polar align CHECK - the plate may have shifted and the ground settles, so expect a small adjustment. Not from scratch. DEW HEATERS ON NOW, low setting. Target 2-5C above ambient, no more - err low on the triplet. |
| **1:00** | **Scope on Dark Shark LDN 1235 + vdB 152** Centre at Dec +71 47' with the long axis N-S and both cores land in one frame. Grey-brown dust shapes plus a blue reflection knot. Outer dust clips on each - that's the accepted trade. |
| **1:00** | **Canon meteor run - Cassiopeia/M31 field** 20s, f/1.8, ISO 3200, continuous. Radiant in the lower-left corner. Dew heater on the lens. |
| **1:30** | **Supervise the meridian flip** Watch it through. Clearance is tight near zenith and a failed flip costs the rest of the night. |
| **2:00** | **PERSEID PEAK HOURS** Radiant climbs 47 to 61 deg. Rates roughly triple over the evening. Camera runs itself - both of you outside, in chairs, looking up. |
| **2:55** | **Doorway frames - ten minutes, not a session** Draco's head passes the NW door at 37 deg, the only recognizable thing that does so during your cabin hours. Radiant ~60 deg off, near-ideal for trail length. |
| **3:45** | **Astronomical twilight - stop capture** Park the mount, ramp cooling off gradually, pull cards. SCOPE BACK ON THE PORCH, not into the warm cabin - cold optics in warm humid air fog instantly. |

<!-- END GENERATED -->

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
