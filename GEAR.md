# Gear, Settings & Support

Four optical systems, two operators. Setup order every night: **refractor first, wide-field
camera second, visual last.** Systems 1 and 2 produce data you can't recreate; the 6SE is
entertainment and will absorb unlimited time if you let it start first.

---

## 1. EQ6-R Pro + Sharpstar 76EDPH + ASI2600MC Pro

| | |
|---|---|
| Focal length / ratio | 342 mm, f/4.5 |
| Sensor | 23.5 × 15.7 mm, 6248 × 4176, 3.76 µm |
| **Image scale** | **2.27 "/px** |
| **Field of view** | **3.94° × 2.63°** |
| Guiding | ASI120MM Mini on SVBONY SV106 (60 mm) → 1.93 "/px |
| Focuser | ZWO EAF Standard + external temp sensor |

**Capture settings** (from `remote-astro/CLAUDE.md`):

| Setting | Value |
|---|---|
| Gain | 100 (unity) |
| Offset | 50 — offset 1 causes banding |
| Cooling | −10 °C, always |
| Subs | **120 s for the low southern targets**, 300 s for everything high |
| Dithering | 3 px every frame, Guide tab |
| Format | Raw 16-bit FITS, RGGB |

**Why 120 s on M8/M20:** at 20° altitude the sky background fills the histogram far faster
than at home, and M8's Hourglass core clips easily. Shorter subs, more of them.

**Darks:** the 2600MC is cooled, so the existing library applies —
`calibration/Darks/master_dark_<exp>s_g100_o50.fit`. **Confirm the masters for both 120 s and
300 s are on the tower before leaving.**

**No pier.** Budget for it: polar align nightly, tripod settles on soft ground (stomp the
legs in, let it sit an hour), and set **park position = home/Polaris** first thing — the
auto-park watchdog is useless without it. In the Align module use "Slew to Target," never
"Sync." Never leave `ON_COORD_SET` on SYNC.

---

## 2. Star Adventurer Mini Pro Pack + Canon T8i + Sigma 18-35 f/1.8 Art

**The Sigma is a RENTAL.** See the pre-trip checklist.

| | |
|---|---|
| Body | Canon T8i / 850D, **astromodified FULL SPECTRUM** |
| Sensor | APS-C 22.3 × 14.9 mm, 6000 × 4000, 3.72 µm, 1.6× crop |
| Lens | Sigma 18-35mm f/1.8 DC HSM Art, **Canon EF mount**, 72 mm filter thread |
| 18 mm | 28.8 mm equiv → **63.5° × 45°** |
| 35 mm | 56 mm equiv → **35.3° × 24°** |
| SAM payload | 3 kg rated; this rig ≈ 1.6 kg. Comfortable. |

**NPF rule at 18 mm f/1.8 = 9.7 s → use 10 s.** The 500 rule would say 17 s and it's wrong
at pixel level.

| Job | Aperture | Exposure | ISO |
|---|---|---|---|
| Meteors, fixed tripod | **f/1.8** | 10 s | 3200 |
| Meteors, tracked on SAM | **f/1.8** | 20 s | 3200 |
| Core sky panel, tracked | f/2.5 | 60–120 s | 800 |
| Core sky panel, untracked | f/2.5 | 10 s ×20, stack | 3200 |
| Foreground (twilight) | f/2.8 | 60–120 s | 800 |

**Aperture principle: stop down when you can pay for it with time, open up when time is
capped.** Tracked, f/1.8→f/2.5 costs one stop and you buy it straight back by doubling the
exposure — with much better corner stars. On a fixed tripod NPF caps you at 10 s and no
amount of wanting changes that, so shoot wide open. For meteors specifically, aperture is
the *only* lever: a meteor is a half-second transient, so longer exposure does not make it
brighter.

**Coma:** the 18-35 Art smears corner stars at f/1.8. Fine for meteors. Stop to f/2.5 for
keepers. **Sample variation is real and this is a rental — run your own aperture sweep.**

**Why 20 s subs for the meteor run:** one continuous run does both jobs. Stack the lot for a
deep Cassiopeia–M31 wide-field, and pull out any frame that caught a meteor. Shorter subs
also give meteors better contrast — a meteor dumps its light in half a second while the sky
keeps accumulating for the whole exposure, so 20 s beats 60 s for meteor visibility even
though both catch the same number.

### FILTER — the one thing with no field workaround

The T8i is **full spectrum**, not Ha-modified. Without an IR cut you get bloated stars, a
visible/IR focus plane disagreement, and a magenta cast no white balance fixes.

**Buy a 72 mm screw-on UV/IR cut.** The Sigma DC is EF mount with a recessed rear element
(*not* EF-S), so a clip-in filter may physically fit — but you can't verify that on a rental
until it's in your hands, with nine days to go. The front filter is guaranteed.

Also set a **custom white balance** off a grey card in daylight so back-of-camera review is
usable. Shoot RAW regardless.

**Skip narrowband** (L-eXtreme etc.) on this lens. At f/1.8 the light cone is too steep and
the interference bandpass blue-shifts off Ha. At Bortle 2 you don't need it.

---

## 3. Celestron NexStar 6SE — visual

On the **stock alt-az fork** (confirmed working). The EQ6-R is committed to the 76EDPH all
three nights.

1500 mm, **1.25" only → maximum field stop 27 mm → max true field ≈ 1.0°.** That rules out
large nebulae and most of M31. Play to aperture and dark sky instead:

| Class | Targets |
|---|---|
| Southern showpieces (9:56 PM – midnight, lake-window only) | **M8 Lagoon, M17 Swan, M16 Eagle, M22, M11 Wild Duck, M20** |
| Planetary nebulae (ideal at 1500 mm) | NGC 6543 Cat's Eye, NGC 6826 Blinking, NGC 7009 Saturn Nebula, M57, M27 |
| Globulars | M13, M92 (west by late), M15, M2, M5, M4 (next to Antares) |
| Galaxies | **NGC 7331 + Stephan's Quintet** — the trophy. M33 shows spiral structure at Bortle 2. |
| Doubles | Albireo, Epsilon Lyrae (double-double splits cleanly), Antares |
| Planets | **Saturn** ~39° at 2 AM, rings near edge-on. **Jupiter unavailable** (solar conjunction). |

The Sagittarius showpieces are invisible from the home yard and only up during the early
window. **M8 and M17 in a six-inch under Bortle 2 are the "why did we drive here" moment,
and it happens then or not at all.**

Bring a **32 mm Plössl** if available — 47×, ~1° field, the widest true field the 6SE can give.

**Placement:** keep the 6SE far enough from the EQ6-R that walking up to it doesn't put
vibration into the subs. Not the same deck, not the same patch of soft ground.

---

## 4. iPhone

Two jobs it's genuinely good at, rather than competing with the real cameras:

- **Afocal moon** through the 6SE at dusk (needs a phone-to-eyepiece bracket). Aug 13–14
  gives a 1–2 day crescent setting right after sunset — thin, low, mostly an earthshine
  subject. Marginal; dusk is better spent finishing setup.
- **Wide Milky Way and aurora.** 30 s Night Mode on a mini tripod, ProRAW. A free second
  wide-field camera at the lake, and genuinely good at aurora.

**Don't attempt afocal DSOs.** It doesn't work and it burns the hour you should be observing.

**Always keep originals.** Google Photos and messaging apps strip GPS and GPSImgDirection —
that metadata is what solved the lake-site question. Export via Share → Options → "All
Photos Data," or AirDrop, or the Files app.

---

## Power

> **WARNING — the 4S24P Li-ion pack is 14.8 V nominal but reaches ~16.8 V fully charged. The
> EQ6-R Pro's rated input is 11–16 V DC. Connecting it directly to a freshly charged 4S pack
> exceeds the mount's specification and risks damaging its drive electronics. The ASI2600MC
> and its TEC cooler are 12 V devices with the same exposure.**
>
> Put a buck regulator or DC-DC converter in between, set to 12.0–13.8 V. The DIY 12 V
> distribution box may already do this — **verify with a meter, under load, before the trip.**

**Budget.** Rig alone: EQ6-R ~2 A, Pi ~1 A equivalent, 2600MC cooling 1–3 A, dew heaters
1–2 A each, plus EAF and guide camera ≈ 8–10 A at 12 V ≈ 120 W. Over ~6 h of dark ≈ 750 Wh.
The pack is ~770 Wh — no margin. And that's before the desktop tower's 300–500 W.

**Run everything off cabin AC.** Keep the battery for the lake and as backup.

**Canon power:** dummy battery all night. T8i takes a **DR-E18 DC coupler** (ACK-E18 kit
pairs it with the AC-E6N adapter). At the lake, the lead-acid's DSLR output **must be
regulated to 8 V** — a charged lead acid sits at 12.7 V resting and up to 14.4 V off the
charger. Confirm the regulator exists and the coupler is a genuine E18. Draw is trivial:
~8 W body + ~15 W lens heater ≈ 75 Wh for a three-hour session.

---

## Thermal: the porch

**The scope can't be left outside** (theft), so it lives on the **unheated 3-season porch**
between sessions — fully assembled, powered, camera cooling, from ~5 PM.

**Why it matters:** the 76EDPH is a **triplet APO**. Carried from a 22 °C cabin into 12 °C night
air it takes 45–90 minutes to stabilise, and focus drifts the whole time. On the porch it's at
ambient before you touch it. No thermal defocus, no settle, better stars.

Cooling on the porch is also *easier* on the camera — −10 °C from a 12 °C ambient is a 22 °C
delta, versus 32 °C from a warm room, which is near the TEC's limit.

**At the end of the night it goes back to the porch, not into the cabin.** Cold optics carried
into warm humid air fog instantly; that's the classic condensation failure and the porch avoids
it entirely.

---

## Dew

**Straps are covered — Stephen has plenty** (the "large + small" line in
`remote-astro/CLAUDE.md` is out of date). Four optics need one each:

1. 76EDPH objective
2. SV106 guide scope
3. **6SE corrector plate** — SCT correctors are the worst dew magnets in amateur astronomy.
   The dew shield helps; it does not solve it.
4. Sigma front element on the SAM

**Only remaining question: does the controller have four channels?** Straps without ports is
the same failure as no straps.

### When to run them

**OFF on the porch. ON the moment anything goes out under open sky.**

Dew forms by radiative cooling — a surface that can see the open sky radiates to space and
drops below the dew point. **Under a roof it can't**, so nothing on the porch will dew, and
heat there would only fight the acclimation you want.

### How hard to run them

Don't bother computing dew point. The thing to optimise is **heat, not power**: too little and
you dew, too much and you get tube currents and mushy, bloated stars. Target the optic sitting
**2–5 °C above ambient, no more.**

| Optic | Setting |
|---|---|
| **76EDPH** | **Err low.** Triplet — heating the objective puts gradients through three elements and degrades stars directly. Minimum that keeps it dry. |
| **6SE corrector** | More tolerant — thin plate. Which is lucky, since it's the worst dew magnet you own. |
| **Sigma on the SAM** | Doesn't much care. Small glass, short path. |

### Setting it by measurement — the IR thermometer gun

Stop guessing. Point it at the **objective**, then at an **unheated surface nearby** (the dew
shield, the tripod leg, the ground). The difference is your heater setting.

> **Target: objective 2–5 °C above the unheated reference. No more.**

Two things to know about IR guns:

- **Glass and painted surfaces read fine** (emissivity ~0.9, which is what the gun assumes).
  **Bare polished metal reads garbage** (emissivity ~0.05) — don't reference off a shiny tube ring.
- It measures **surfaces, not air.** So compare against another surface at ambient, not against
  a thermometer's air reading.

### Bonus: it's a cloud detector

Point it at the **zenith**. On a genuinely clear night the sky reads absurdly cold — typically
−30 °C or below, because you're measuring space through a transparent atmosphere. Under cloud
it reads close to ambient, because you're measuring the cloud base.

**That's a two-second, unambiguous answer to "is that hole real or thin cirrus?"** — worth
knowing for [OH_SHIT.md](OH_SHIT.md). Thin high cloud that looks like clear sky to your eye
shows up immediately as a 20-degree jump.

Also check the objective with a red light every hour. Dewing → up. Stars soft and bloated with
no focus change → down.

**Under cloud, outdoors, run them.** Humidity under overcast is brutal and soaked optics when a
break comes cost you the break.

---

## Network & control

**Desktop tower is coming**, so the whole stack works as at home: KStars/Ekos, PHD2, Siril,
GraXpert, Cosmic Clarity on the RTX 5060 Ti.

- `ssh astro` resolves by **mDNS** — survives any subnet
- Dashboard binds `0.0.0.0:8092`; PHD2 is localhost; INDI web manager on 8624
- ntfy topic (name kept out of this public repo — see `remote-astro/FIELD_OPS.md`) for push alerts
- **Plan:** 50' ethernet from the cabin router to the Pi, tower on WiFi or a short cable

**mDNS risk:** some rental routers don't pass multicast between wired and wireless. Know how
to find the Pi's IP from the router admin page as a fallback, and test it before leaving. No
travel router needed given the ethernet run.

**Cabin has WiFi, and there's patchy cell around the area.** That changes the unattended
question — the rig doesn't have to run blind while you're at the lake.

**What works over cell for free: ntfy push alerts.** The dashboard already pushes to topic
its topic on star-lost, meridian-flip-imminent, and low-disk. ntfy is a public
service, so the Pi pushes out and your phone receives wherever it has signal. **Subscribe on
your phone before you leave** and you'll know from the lake if the rig has died — instead of
finding out at 12:10 AM.

**The dashboard itself won't reach you** without a tunnel — it binds `0.0.0.0:8092` on the
LAN. If you want the full page from the lake, **install Tailscale** on the tower and the phone
before the trip. Free, no port forwarding, works over cell. Half an hour of setup, and it also
gives you `ssh astro` from anywhere.

Either way the **auto-park watchdog** (15 min of lost guiding → park + alert) remains the
safety net.

**Start the dashboard with the venv python** — it needs `ephem`:

```bash
/home/stephen/remote-astro/venv/bin/python ~/Applications/astro_dashboard.py
```

### Tethering the Canon (optional, undecided)

`gvfs` grabs the Canon as an MTP volume the instant it's plugged in and gphoto2 then can't
claim it — this is why `~/kill-camera.sh` exists on the Pi. Desktop equivalent:

```bash
killall gvfs-gphoto2-volume-monitor gvfsd-gphoto2
```

Constraints: USB 2.0 tops out ~5 m; a 30 MB CR3 over gphoto2 takes several seconds, eating
duty cycle; and a tether that drops at 2 AM loses the rest of the night silently.

**Recommendation: keep writing to card and use the camera's internal interval timer for the
meteor run.** If you want the tether, use `--capture-image` not `--capture-image-and-download`
so the card stays the record and USB is just a window. Tethering earns its keep at the
**lake**, if you bring a laptop — checking corner stars on a 15" screen on a rental lens you've
never used, on the one night that matters.

`indi_canon_ccd` is in the `indi-full` install (removed from the "My Astro Gear" profile in
March). Running the Canon as an Ekos sequence would be elegant, but it's a stack to rebuild
and test with nine days left. File under next trip.

---

## Cards

Lake session (~100–150 frames) plus 585 meteor frames ≈ 800 shots ≈ 24 GB in CR3.

**Swap cards, don't format.** One card per night, offload to the tower, leave the original
untouched until home. Formatting in the field at half past midnight, tired, is how people
lose a night. The copy on the desktop is a copy, not a backup, until there are two.
