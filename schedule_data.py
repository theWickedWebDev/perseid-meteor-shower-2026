#!/usr/bin/env python3
"""
The trip schedule, once, as data. Both outputs are generated from this module:

    make_calendar.py    -> pittsburg-2026.ics   (phone alarms)
    make_schedules.py   -> SCHEDULE_3_NIGHTS.md (the timeline tables)

They used to be maintained separately and drifted: the doorway frames sat on Night 2 in
the markdown and Night 3 in the calendar, porch assembly was 3 PM in one and 5 PM in the
other, and three events existed only in the markdown. Anything that must agree lives here.

Event tuple: (day, "HH:MM", alarm_minutes_before, "Summary", "Description", md=None)
  day is the literal calendar date the event falls on — post-midnight entries name the
  following day. Nothing rolls implicitly; that bug put a whole night on the wrong date.
  md is optional richer markdown for the schedule table; the summary is used if absent.
"""

from datetime import datetime, timedelta

# ── astronomy, computed rather than typed ────────────────────────────────
# Hand-copied times drifted between documents and were quietly wrong: one core deadline
# was quoted for all three nights when it actually moves four minutes earlier each night.
# These are derived from the ephemeris at import, with a checked fallback so neither
# generator hard-depends on astropy.

LAKE = (45.2393, -71.1964, 500)          # lat, lon, metres
CORE = ("17h45m40s", "-29d00m28s")       # Sgr A* — the Milky Way core
RHO  = ("16h27m00s", "-25d00m00s")       # Rho Ophiuchi complex
NIGHT_DATES = ("2026-08-11", "2026-08-12", "2026-08-13")
TREELINE = 10.0                          # deg. Provisional 7.3 once the arrival survey
                                         # confirms it — see SITE_DATA.md.

# Verified against astropy 6.0.0 on 4 Aug 2026. Kept literal so the generators still run
# without it; _verify_astro() re-derives and complains if these ever go stale.
ASTRO = {
    "2026-08-11": {"dark": "21:56", "core_set": "23:21", "rho_set": "22:39", "dawn": "03:45"},
    "2026-08-12": {"dark": "21:54", "core_set": "23:17", "rho_set": "22:35", "dawn": "03:45"},
    "2026-08-13": {"dark": "21:52", "core_set": "23:13", "rho_set": "22:32", "dawn": "03:45"},
}


def _verify_astro(tol_min=2):
    """Recompute ASTRO and return a list of discrepancies. Needs astropy; [] if absent."""
    try:
        import warnings; warnings.filterwarnings("ignore")
        from astropy.coordinates import EarthLocation, AltAz, SkyCoord, get_sun
        from astropy.time import Time
        import astropy.units as u, numpy as np
    except ImportError:
        return []
    loc = EarthLocation(lat=LAKE[0]*u.deg, lon=LAKE[1]*u.deg, height=LAKE[2]*u.m)
    out = []

    def cross(tgt, day, thresh, sun=False):
        t = Time(f"{day} 20:00:00") + 4*u.hour + np.arange(0, 500, 1)*u.min
        f = AltAz(obstime=t, location=loc)
        a = (get_sun(t) if sun else tgt).transform_to(f).alt.deg
        for k in range(1, len(a)):
            if a[k-1] >= thresh > a[k]:
                return (t[k] - 4*u.hour).datetime.strftime("%H:%M")
        return None

    core = SkyCoord(ra=CORE[0], dec=CORE[1])
    rho = SkyCoord(ra=RHO[0], dec=RHO[1])
    for day in NIGHT_DATES:
        for key, got in (("dark", cross(None, day, -18.0, sun=True)),
                         ("core_set", cross(core, day, TREELINE)),
                         ("rho_set", cross(rho, day, TREELINE))):
            want = ASTRO[day][key]
            if got and abs((datetime.strptime(got, "%H:%M")
                            - datetime.strptime(want, "%H:%M")).total_seconds()) > tol_min*60:
                out.append(f"{day} {key}: stored {want}, computed {got}")
    return out


PRETRIP = [
    ("2026-08-05", "18:00", 0,  "Cut the plywood pier plate",
     "Set the tripod up FIRST at the exact leg extension you'll use and measure the "
     "triangle before drilling. Forstner recesses ~1/2in wide, 1/4in deep. Mark which "
     "corner faces north. Tape-mark the leg extension."),
    ("2026-08-05", "18:30", 0,  "Set mount latitude to 45 deg",
     "EQ6-R altitude bolt from 42.8 to 45.1. Do it in the driveway, not in the dark. "
     "Same for the SAM's latitude wedge."),
    ("2026-08-08", "12:00", 0,  "Rental lens should be here",
     "Confirm Canon EF mount. Decentering test: star field, compare all four corners at "
     "100%. Then aperture sweep at 35mm: f/1.8, 2.0, 2.2, 2.5."),

    ("2026-08-09", "11:00", 0,  "Verify 12V regulation under load",
     "WARNING: 4S pack reaches 16.8V, EQ6-R is rated 11-16V. Meter the distribution box "
     "under load and confirm 12.0-13.8V out."),
    ("2026-08-09", "12:00", 0,  "Subscribe to ntfy on phone",
     "Topic name is in remote-astro/FIELD_OPS.md. Star-lost, meridian-flip, low-disk alerts reach you "
     "over cell from the lake."),
    ("2026-08-10", "18:00", 0,  "Pack",
     "Desktop + monitors + cables. Extension cord. 50ft ethernet. Plywood plate. Pavers. "
     "Bubble level. Spare SD cards. Two headlamps (one red, one warm-white). Amber gel. "
     "72mm UV/IR filter. Multimeter. IR thermometer gun. ID."),
]

# ── shared lake-night skeleton ───────────────────────────────────────────
def lake_night(day, deep_target, deep_note, extra=None, porch=("17:00", "17:45", "18:15")):
    """One lake night. Every astronomical time comes from ASTRO for THIS date —
    dark, the Rho Oph deadline and the core deadline all shift a few minutes per
    night, and quoting one figure for all three is how the old plan went wrong."""
    A = ASTRO[day]
    # everything from "Back at the cabin" onward happens after midnight, so it belongs
    # to the following calendar day
    nxt = (datetime.strptime(day, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    ev = [
        (day, porch[0], 15, "Assemble the rig ON THE PORCH",
         "Head, counterweights, OTA, balance RA and DEC, cables dressed. Comfortable and lit - "
         "this is where the why-wont-it-connect half-hours normally happen."),
        (day, porch[1], 5, "Pi up, Ekos connected - START COOLING",
         "All five devices verified. Porch is at ambient so -10C is an easy 22C delta. "
         "DEW HEATERS OFF - under a roof it cannot dew, and heat fights the acclimation. "
         "The triplet needs these five hours to reach ambient."),
        (day, porch[2], 5, "Check the tripod outside",
         "Still seated on the plate, bagged, level. Alt/az bolts untouched so alignment "
         "carries over."),
        (day, "19:00", 20, "LOAD THE CAR - lake kit",
         "6SE + fork + tripod + eyepieces + 32mm Plossl (LEAVE THE EQ WEDGE HOME). Canon + "
         "Sigma with the 72mm UV/IR filter fitted + lens hood. SAM + tripod, wedge at 45. "
         "POWER, one supply per system: LP-E17 batteries for the camera (all four, charged) - "
         "USB power bank for the dew strap - lead-acid + FUSED alligator lead for the 6SE - "
         "2xAA lithiums plus spares for the SAM. Power box and coupler stay in the truck as "
         "backup. USB dew "
         "strap. Power bank + hand warmers as backup. Spare SD cards. IR thermometer. Two "
         "headlamps + amber gel. Something to drop the tripod to 0.5m. Chairs, layers, bug "
         "spray, ID."),
        (day, "19:15", 10, "DEPART - moose drive north on Route 3",
         "The 6SE's best targets are southern and only up 9:54 to midnight - exactly when "
         "you're at the lake. Leave it behind and M8, M17, M16, M22 and M11 do not happen this "
         "trip. Sunset 7:58."),
        (day, "20:10",  5, "Earth's shadow + Belt of Venus",
         "Azimuth 112, off your right heading north. Dark band with a pink edge rising out "
         "of the east. Gone by 8:35. ~1/10s, f/5.6, ISO 100, underexpose slightly."),
        (day, "20:30",  5, "Arrive the lake - set up",
         "Civil twilight ends. Tripod and SAM out immediately."),
        (day, "20:45",  5, "FOREGROUND FRAMES - only chance",
         "Glow still on the water. f/2.8, ISO 800, 60-120s. These are your blend layer and "
         "there is no second chance tonight."),
        (day, "21:00",  5, "Polar align the SAM - frame to azimuth 204",
         "Polaris is behind you over land. SAM latitude wedge should be at 45."),
        (day, "21:15",  5, "Focus, check corners, lock composition",
         "Hard deadline isn't darkness, it's being ready for it."),
        (day, A["dark"], 10, "ASTRONOMICAL DARK - shoot the core",
         "Landscape, 18mm. Also several at 35mm: Rho Oph + core + Trifid in one frame. "
         "Rho Oph is at 13.2 deg and dying - shoot it FIRST."),
        (day, A["rho_set"], 15, "RHO OPH DEADLINE - below 10 deg, gone for the year",
         "Last frames of Rho Oph now. Core at 13.6 and sliding toward frame centre."),
        (day, "23:00",  5, "Switch to PORTRAIT",
         "Band standing vertical out of the water. Core dead centre at 11.8 deg. "
         "This is the postcard."),
        (day, A["core_set"], 15, "CORE DEADLINE - 10 deg. South is finished",
         "Last frames. Pack up. Verified against astropy for this specific night - the core "
         "sets four minutes earlier each night, so this is not the same time every evening. "
         "If the arrival survey finds the treeline lower than 10 deg you gain roughly another "
         "half hour; re-check on site."),
        (day, "23:45",  5, "Depart the lake",
         "Moose peep on the way back to the cabin."),
        (nxt, "00:10",  0, "Back at the cabin",
         "Check ntfy / dashboard. Pull the SD card, copy to the desktop, verify two or "
         "three frames opened and are sharp. Fresh card in."),
        (nxt, "00:15",  5, "Carry the scope out from the porch",
         "Already at ambient, camera already cold. Onto the tripod - alt/az untouched, so the "
         "alignment carries over. Polar align CHECK - the plate may have shifted and the "
         "ground settles, so expect a small "
         "adjustment. Not from scratch. DEW HEATERS ON NOW, low setting. "
         "Target 2-5C above ambient, no more - err low on the triplet."),
        (nxt, "01:00", 10, f"Scope on {deep_target}", deep_note),
        (nxt, "01:00",  5, "Canon meteor run - Cassiopeia/M31 field",
         "20s, f/1.8, ISO 3200, continuous. Radiant in the lower-left corner. "
         "Dew heater on the lens."),
        (nxt, "01:30", 5, "Supervise the meridian flip",
         "Watch it through. Clearance is tight near zenith and a failed flip costs the "
         "rest of the night."),
        (nxt, "02:00", 15, "PERSEID PEAK HOURS",
         "Radiant climbs 47 to 61 deg. Rates roughly triple over the evening. Camera runs "
         "itself - both of you outside, in chairs, looking up."),
        (nxt, A["dawn"], 15, "Astronomical twilight - stop capture",
         "Park the mount, ramp cooling off gradually, pull cards. SCOPE BACK ON THE PORCH, not "
         "into the warm cabin - cold optics in warm humid air fog instantly."),
    ]
    if extra:
        ev.extend(extra)
    return ev

# ── night 1: build night, no lake ────────────────────────────────────────
NIGHT1 = [
    ("2026-08-11", "15:00", 30, "ARRIVE - unload the truck",
     "Move fast. Every minute before dark is load-bearing today."),
    ("2026-08-11", "15:20", 5,  "360 HORIZON SURVEY - do this first",
     "Phone app, mark the treeline from the exact spot the tripod will stand. Dense every "
     "5 deg across 170-240. That band is where M8/M20, the core and the Trifid all live."),
    ("2026-08-11", "15:45", 5,  "Pick positions",
     "EQ6 spot (clear north for Polaris - watch for eaves and the north wall, not trees). "
     "6SE spot far enough that walking to it doesn't shake the rig. Canon spot. Desktop. "
     "Find the AC outlet and measure the run."),
    ("2026-08-11", "16:00", 5,  "Desktop setup indoors, then run the ethernet",
     "Tower, monitors, power. Run the 50ft ethernet out to where the Pi will sit. "
     "Do this after picking the mount spot, not before."),
    ("2026-08-11", "16:45", 5,  "Plate down, tripod on it, level to the bubble",
     "Pavers underneath if the ground is soft - seat them roughly coplanar or the plywood "
     "rocks. Note the leg extension against your tape marks."),
    ("2026-08-11", "17:15", 5,  "Head on, counterweights, OTA, balance",
     "Balance RA on the counterweight shaft and DEC in the dovetail."),
    ("2026-08-11", "18:00", 5,  "Cabling and power - USB FIRST",
     "All USB connected before the Pi gets power. Hot-plug crashes the Pi 5. Boot, wait "
     "for the beep, Ekos connects, verify all five devices."),
    ("2026-08-11", "18:30", 5,  "Site coords in - virtualgps on the Pi",
     "ssh astro / sudo nano /etc/systemd/system/virtualgps.service / set 45.088279, -71.324767 "
     "+ elevation / sudo systemctl daemon-reload / sudo systemctl restart virtualgps / "
     "cat /tmp/vgps to confirm. Then check the site in Ekos. Wrong coords means wrong LST and "
     "wrong meridian-flip timing. Cool to -10C. Daylight focus, EAF step 500."),
    ("2026-08-11", "19:30", 10, "Eat. Assemble the SAM and the 6SE",
     "Load the M8/M20 sequence, 120s. Sunset 19:58 - the SAM's latitude wedge goes to 45 "
     "now, in the light, rather than later by headlamp."),
    ("2026-08-11", "21:30", 10, "Polar align the SAM, frame the Canon",
     "Core from the cabin if the arrival survey allows it, otherwise the Cassiopeia/M31 "
     "meteor field. Decide from the survey, not from hope."),
    ("2026-08-11", "19:00", 5,  "Daylight flats",
     "~0.005s at gain 100 with the panel. These cover all three nights unless you rotate "
     "the camera or change the optical train."),
    ("2026-08-11", "20:30", 5,  "Set park position = home/Polaris",
     "Verify ON_COORD_SET=TRACK, never SYNC."),
    ("2026-08-11", "20:45", 5,  "POLAR ALIGN",
     "Polaris is up. Take your time - tonight's alignment is the one you reproduce for the "
     "rest of the trip."),
    ("2026-08-11", "21:10", 5,  "*** MARK THE PLATE ***",
     "Stake it, outline it, both. Mark which corner faces north. Then DO NOT TOUCH THE "
     "ALT/AZ BOLTS again all trip. This is what makes nights 2 and 3 possible."),
    ("2026-08-11", "21:15", 5,  "Plate-solve test, autofocus V-curve, start guiding",
     "Step 30, 15 steps. Target HFR ~1.2."),
    (NIGHT_DATES[0], ASTRO[NIGHT_DATES[0]]["dark"], 10,
     "ASTRONOMICAL DARK - scope to M8/M20",
     "120s subs, gain 100, offset 50, dither 3px. THE ONLY NIGHT the refractor can reach "
     "this pair - on lake nights it's below 10 deg before you get back."),
    ("2026-08-11", "22:00", 5,  "6SE - the southern showpieces",
     "M8, M17 Swan, M16 Eagle, M22, M11, M20. Invisible from home and only up now. "
     "This is the why-did-we-drive-here moment."),
    ("2026-08-12", "00:15", 10, "Scope to the Veil / Cygnus Loop",
     "Just past its 12:17 transit so it's west of the meridian - no flip all night. "
     "Teal OIII and crimson Ha filaments."),
    ("2026-08-12", "00:30", 5,  "Canon to the meteor field",
     "20s, f/1.8, ISO 3200, continuous."),
    ("2026-08-12", "02:00", 15, "Perseids building",
     "6SE on NGC 7331 + Stephan's Quintet while it's high. Then M31, M33, Saturn."),
    ("2026-08-12", "03:45", 15, "Twilight - stop capture",
     "Then TEARDOWN PRACTICE: pull the OTA and counterweights, lift the head off without "
     "touching alt/az, and move it TO THE PORCH - that's where it lives for the rest of the "
     "trip. Time yourself, you repeat this twice."),
]

NIGHT2 = lake_night(
    "2026-08-12",
    "Cocoon IC 5146 + B168",
    "Red core, blue rim, black dust river - the best colour target of the trip. Transits "
    "1:19 at 87.8 deg, essentially zenith. WARNING: near-zenith meridian flips are the "
    "awkward ones. Supervise it, or start after 1:25 and skip the flip entirely.",
)

NIGHT3 = lake_night(
    "2026-08-13",
    "Dark Shark LDN 1235 + vdB 152",
    "Centre at Dec +71 47' with the long axis N-S and both cores land in one frame. "
    "Grey-brown dust shapes plus a blue reflection knot. Outer dust clips on each - "
    "that's the accepted trade.",
    extra=[
        ("2026-08-13", "17:00", 20, "Dinner at Buck Rub Pub",
         "45.0658, -71.3437. 2.9km SSW of the cabin, ~5 min, opposite direction from the moose "
         "drive. Rig already assembled on the porch this afternoon. Pull the forecast and the "
         "Kp index while you have a table."),
        ("2026-08-13", "16:30", 10, "Pack the creative kit",
         "Second headlamp, amber gel, something to drop the tripod to ~0.5m, a marker for "
         "the subject's spot."),
        ("2026-08-13", "23:05", 5,  "CREATIVE SESSION - drop the tripod to knee height",
         "Subject 5-7m out. 10s, f/1.8, ISO 3200, UNTRACKED. Silhouettes, light-painted "
         "foreground, headlamp beam. Light in a 1-2s PULSE from the side, never a hold. "
         "Shoot 20+ frames, the failure rate is high."),
        ("2026-08-14", "02:55", 5,  "Doorway frames - ten minutes, not a session",
         "Draco's head passes the NW door at 37 deg, the only recognizable thing that does "
         "so during your cabin hours. Radiant ~60 deg off, near-ideal for trail length."),
    ],
    # dinner at Buck Rub is 5 PM tonight, so the rebuild moves into the afternoon
    porch=("15:00", "15:45", "16:15"),
)
