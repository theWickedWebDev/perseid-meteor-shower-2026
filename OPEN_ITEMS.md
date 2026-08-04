# Open Items & Pre-Trip Checklist

**Departure: Aug 11, 2026.** Ordering window is short — anything that needs shipping should go
in the cart today.

---

## BUILD BEFORE YOU GO — the plywood pier plate

**The rig comes in every night** — theft worry — and lives on the unheated 3-season porch.
Polar alignment needs Polaris (~8:45 PM) and you leave for the moose drive at 7:15, so nights 2
and 3 depend entirely on reproducing night 1's tripod position.

- [ ] **Cut a triangular 3/4" plywood plate** with three shallow recesses for the tripod leg tips
      (Forstner bit, ~1/2" wide, 1/4" deep — the tips seat, they don't go through).

> ⚠️ **Set the tripod up at home first, at the exact leg extension you'll use, and measure the
> triangle before drilling.** Drill blind and the holes won't match. Also **tape-mark the leg
> extension** so it reproduces, and **mark which corner faces north** so the plate goes back the
> same way round.

**The other half of the trick: move the whole tripod assembled** — head, OTA, counterweights,
alt/az bolts untouched — out to the porch and back. Keeping it in one piece is what preserves
the alignment.

That still isn't perfect: the plate can shift and the ground settles. So budget a **polar align
check with a small adjustment** at 12:15, not a from-scratch alignment. Ten minutes rather than
twenty-five.

- [ ] **Bring the bubble level and use it every night.** If the tripod tilts differently, the
      alt/az setting doesn't reproduce and the marks are worthless. Level to the same bubble
      or the plate buys you nothing.

Plywood on soft ground still settles — but it settles as a unit, which preserves the relative
geometry. That's the part that matters.

---

## DON'T LEAVE WITHOUT

- [ ] **Desktop computer** — tower, monitor(s), keyboard, mouse, all cables. The entire
      Ekos/PHD2/Siril/GraXpert stack lives on it.
- [ ] **Heavy-gauge outdoor extension cord** + weatherproof power strip
- [ ] **50' ethernet cable**
- [ ] **Plywood pier plate** (above)
- [ ] **Three pavers** (~12×12) — seat them into the ground at the leg points with the plywood
      spanning on top. Pavers stop the assembly sinking, plywood holds the geometry. Seat them
      roughly **coplanar** or the plywood rocks. If the ground turns out packed or gravelled,
      leave them in the truck.
- [ ] **Bubble level**
- [ ] **Multimeter** — verify the alligator lead's polarity before it touches the power box,
      confirm 12 V regulation under load, and diagnose anything electrical at 1 AM.
- [ ] **IR thermometer gun** — the way to actually set heater level. Point at the objective,
      point at an unheated surface nearby, subtract. Target 2–5 °C above ambient. Also doubles
      as a cloud detector, see [GEAR.md](GEAR.md).

- [ ] Spare SD cards, one per night
- [ ] Two headlamps — one red for working, one warm-white for light painting

> **Don't set up on a wooden deck**, however flat it looks. Every footstep goes into the subs
> and you'll be walking to the 6SE all night. Grass or dirt wins.

---

## MUST DO — trip degrades or fails without these

- [x] ~~Order the 72 mm UV/IR cut filter~~ — **ICE UV/IR Cut arrived Aug 3.** Passband 400–700 nm
      at 99.4%, IR cut above 750 nm, so **Ha at 656 nm gets through** — the one spec that mattered.
  - [x] ~~Confirm it blocks IR~~ — **tested Aug 3 at dusk. Strongly magenta without, normal
        with.** That's the signature: IR leaks near-equally through all three Bayer filters, so
        it desaturates toward magenta, and it vanishes the moment something blocks it.
  - [ ] **Star test once the Sigma lands** (~Aug 8) — bright star at f/1.8, with and without, at
        100%. Looking for halos from the coatings. A **58→72 step-up ring** (~$6) lets you screw
        it onto the kit lens properly rather than hand-holding through a long exposure.

- [ ] **Update `virtualgps` coordinates** — ⚠️ **this is a CABIN job, night 1 at ~6:30 PM.**
      The Pi is packed, so it can't be done before leaving. Scheduled in
      [SCHEDULE_3_NIGHTS.md](SCHEDULE_3_NIGHTS.md).

      Hardcoded to the home site (redacted) in
      `/etc/systemd/system/virtualgps.service` on the Pi. Flagged as an open TODO in
      `remote-astro/CLAUDE.md:29`. **Wrong coords → wrong LST → wrong meridian-flip timing and
      wrong altitude limits**, and nothing looks broken until Ekos flips at the wrong moment.

      ```bash
      ssh astro
      sudo nano /etc/systemd/system/virtualgps.service
      #   set 45.088279, -71.324767  + elevation
      sudo systemctl daemon-reload
      sudo systemctl restart virtualgps
      cat /tmp/vgps          # confirm the new numbers came through
      ```

      Then confirm the site in **Ekos** (Geographic Location). It should pick up from GPSD via
      `indi_gpsd`, but check rather than assume.

- [x] ~~Two more dew heater straps~~ — **Stephen has plenty.** (`remote-astro/CLAUDE.md` listing
      "large + small" is out of date.) Four optics still need covering: 76EDPH objective, SV106
      guide scope, **6SE corrector** (worst offender — a dew shield does not solve it), and the
      Sigma front element. **Confirm the controller has enough channels to run all four at once.**

- [ ] **Verify 12 V regulation.** ⚠️ The 4S24P pack reaches ~16.8 V fully charged; the EQ6-R Pro
      is rated 11–16 V. Two measurements, in order:

      **Test A — unloaded, pack fully charged** (worst case, and the gate):
      1. Charge the pack fully. Meter across its terminals — expect ~16.8 V, confirming it's full.
      2. Meter each output of the distribution box with nothing connected.

      | Reading | Meaning |
      |---|---|
      | **12.0–13.8 V** | Regulating. Proceed to Test B. |
      | **~16.8 V, tracking the pack** | Passthrough, not a regulator. **Do not connect the mount.** |

      **Test B — under load.** A regulator can look fine unloaded and sag once current flows.
      Connect the mount (safe now that A passed) or a **12 V automotive bulb** as a dumb load —
      21 W brake bulb ≈ 1.75 A, 55 W headlight ≈ 4.5 A. **Measure during a slew**, not at idle:
      that's the current peak and where sag shows. Want 12.0–13.8 V, not dipping toward 11 V.

      **If it fails:** low stakes. Cabin AC is the plan and the 4S pack was only ever backup —
      just don't pair that pack with the mount. The lead-acid at 12.6 V is already in spec.

- [x] ~~Confirm the cabin has AC~~ — **confirmed.** Still bring the heavy-gauge outdoor
      extension cord and a weatherproof strip: the run from the porch outlet to wherever the
      tripod ends up is the bit that has to reach. The battery does not cover a full night with
      the rig, and the tower adds 300–500 W on top.

- [ ] **Rental lens in hand by ~Aug 8.** Then:
  - [ ] Confirm it's **Canon EF mount** (Sigma also makes Nikon F and Sigma SA)
  - [ ] **Decentering test** — shoot a star field, compare all four corners at 100%. One corner
        clearly worse than the diagonally opposite one means a knocked copy. Swap it, don't work
        around it.
  - [ ] **Aperture sweep** at 35 mm: f/1.8, 2.0, 2.2, 2.5. Find where *your* copy cleans up.
  - [ ] Confirm the rental window covers shipping both ways — home by the 15th at the earliest.

- [ ] **Confirm the DR-E18 coupler and the lead-acid's 8 V regulation.** A charged lead acid sits
      at 12.7 V resting, 14.4 V off the charger. That goes nowhere near a DR-E18 unregulated.

---

## SHOULD DO

- [ ] **Cabin elevation** — needed for `virtualgps` and Stellarium. Carrying ~455 m as a
      placeholder. Pull the real number off a topo map.
- [ ] **Subscribe to the ntfy topic on your phone** — topic name is in `remote-astro/FIELD_OPS.md`, deliberately not in this public repo (ntfy topics are open pub/sub). Free, works
      over cell, and it means you learn from the lake if the rig has lost guiding rather than
      discovering it at 12:10 AM. Highest value-per-minute item on this list.
- [ ] **Install Tailscale** on the tower and the phone if you want the actual dashboard from the
      lake. It binds to the LAN only, so cabin WiFi alone doesn't reach you 20 km up Route 3.
      Free, no port forwarding, and it gives you `ssh astro` from anywhere too. ~30 min.
- [ ] **mDNS fallback.** `ssh astro` resolves via mDNS; some rental routers
      don't pass multicast between wired and wireless. Know how to find the Pi's IP from the
      router admin page. Test the whole chain before leaving.
- [ ] **Spare SD cards** — one per night minimum. Swap, never format in the field.
- [ ] **Master darks on the tower** for both **120 s** and **300 s** at gain 100 / offset 50.
      Confirm they exist before you drive.
- [ ] **Stellarium** — switch off the pier landscape (rotation −56, vertical +15°). Use a generic
      or ocean horizon, or it will lie to you about exactly the low southern targets that matter.
- [ ] **Phone-to-eyepiece bracket** for afocal moon shots through the 6SE.
- [ ] **32 mm Plössl** if you don't have one — 47×, ~1° field, the widest the 6SE can give.
- [ ] **Red film for the tower's monitors**, or run them at minimum brightness. A desktop display
      through a cabin window wrecks dark adaptation.
- [ ] **Location services ON for the iPhone camera.** The 15 Pro Max records `GPSImgDirection`
      when enabled — the February reference shots simply had it off, which is why three of them
      couldn't be solved directly.
- [ ] If tethering the Canon: test `killall gvfs-gphoto2-volume-monitor gvfsd-gphoto2` on the
      desktop. `gvfs` grabs the camera as MTP and gphoto2 then can't claim it.

---

## DONE

- [x] **`weather.sh` curl timeout.** `--max-time 8` added to
      `/media/stephen/hdd/astrophotography/ekos_scripts/weather.sh:22`. It had no timeout and runs
      inside the **blocking** Ekos post-capture hook — flaky or absent cabin internet would have
      stalled the capture sequence on every frame. (`remote-astro/tools/weather.sh` does not
      exist; only the live copy needed it.)
- [x] **6SE stock alt-az fork confirmed working.** The EQ6-R is committed to the 76EDPH all three
      nights, so the fork was the only option — and it's in prime condition.
- [x] **Lake site bearing confirmed: 204.4° True**, from EXIF, cross-validated against the moon.
- [x] **Cabin horizons measured** from three plate-solved reference photos. See
      [HORIZON_PHOTOS.md](HORIZON_PHOTOS.md).
- [x] **Dark Shark confirmed viable** — never below 52.7°, clears the ~17° NW treeline.
- [x] **Desktop tower coming** — full Ekos/PHD2/Siril/GraXpert/Cosmic Clarity stack available.
- [x] **Camera power solved** — dummy battery on AC at the cabin, lead-acid at the lake.
- [x] **Networking solved** — 50' ethernet to the Pi, tower on WiFi. No travel router needed.

---

## STILL UNRESOLVED

### 1. Which lake is the shooting spot?

EXIF puts it at **45.239267, −71.196433**. Stephen believes it's Third Connecticut, which sits
nearer 45.30 N — these coordinates are closer to the Second Connecticut stretch. The 666 m
elevation matches Third better than Second, but the horizontal fix (±4.6 m) is far more reliable
than phone GPS altitude. **Drop the coordinates on a map and settle it.**

### 2. Is IMG_6099 the same site?

The twilight lake photo has no GPS. Its ridgeline profile (2–4° in the SW rising to ~10° in the
W) is excellent, but it isn't proven to be the same spot as the 204.4° view. Re-shoot from the
exact tripod position with location services on.

### 3. Does the friend operate the rig?

Determines whether the refractor can be actively run while Stephen is at the lake, or whether it
has to go out on a Scheduler job and be left blind. Current plans assume **Scheduler + unattended**.

### 4. Is there a northeast-facing opening at the cabin?

For the doorway shot. The February composition (M31 centred in a NW doorway) doesn't reproduce
in August — M31 only reaches azimuth 309° in daylight then. But at **11:00 PM on Aug 12 M31 sits
at azimuth 65°, altitude 36°**, with the radiant 29° away. A **northeast**-facing window, porch
post, or roof edge framing 30–45° up gives M31 in the aperture with meteors crossing it.

### 5. Cabin's exact tripod placement

Needs a clear north for Polaris (both mounts), open SSW for M8/M20, and enough separation
between the EQ6 and the 6SE that walking to the eyepiece doesn't put vibration into the subs.

---

## In-field survey to run on arrival

Now that we know the phone records compass bearing when location services are on:

1. From each tripod position, shoot a **level 24 mm landscape frame** at roughly **180°, 210°,
   240°, 270°, and 000°**, horizon visible in each.
2. Keep the **originals** — AirDrop, or Share → Options → "All Photos Data".
3. With bearing plus a visible horizon, ridge altitude can be computed at every azimuth and
   turned into a proper **Stellarium landscape file** for the site — replacing the flat
   mathematical horizon.
