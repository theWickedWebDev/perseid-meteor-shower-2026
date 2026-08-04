#!/usr/bin/env python3
"""
Generate pittsburg-2026.ics — the trip schedule as phone calendar events with alarms.

Import once on the phone and it handles every reminder natively: works offline, no
dependency on the Pi, the network, or a script staying alive. Edit the tables below and
re-run to regenerate.

    python3 make_calendar.py

All times are EDT (UTC-4) and are emitted as UTC so no VTIMEZONE block is needed.
"""

from datetime import datetime, timedelta

UTC_OFFSET = 4            # EDT
DUR_MIN    = 10           # default event length
OUT        = "pittsburg-2026.ics"

# (day, "HH:MM", alarm_minutes_before, "Summary", "Description")
#   day: 11/12/13 = that evening.  Times after midnight roll to the next date
#   automatically — anything before 12:00 is treated as the small hours.

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
def lake_night(day, deep_target, deep_note, extra=None):
    ev = [
        (day, "17:00", 15, "Assemble the rig ON THE PORCH",
         "Head, counterweights, OTA, balance RA and DEC, cables dressed. Comfortable and lit - "
         "this is where the why-wont-it-connect half-hours normally happen."),
        (day, "17:45", 5, "Pi up, Ekos connected - START COOLING",
         "All five devices verified. Porch is at ambient so -10C is an easy 22C delta. "
         "DEW HEATERS OFF - under a roof it cannot dew, and heat fights the acclimation. "
         "The triplet needs these five hours to reach ambient."),
        (day, "18:15", 5, "Check the tripod outside",
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
         "The 6SE's best targets are southern and only up 9:56 to midnight - exactly when "
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
        (day, "21:56", 10, "ASTRONOMICAL DARK - shoot the core",
         "Landscape, 18mm. Also several at 35mm: Rho Oph + core + Trifid in one frame. "
         "Rho Oph is at 13.2 deg and dying - shoot it FIRST."),
        (day, "22:30", 15, "RHO OPH DEADLINE - below 10 deg, gone for the year",
         "Last frames of Rho Oph now. Core at 13.6 and sliding toward frame centre."),
        (day, "23:00",  5, "Switch to PORTRAIT",
         "Band standing vertical out of the water. Core dead centre at 11.8 deg. "
         "This is the postcard."),
        (day, "23:25", 15, "CORE DEADLINE - 10 deg. South is finished",
         "Last frames. Pack up."),
        (day, "23:45",  5, "Depart the lake",
         "Moose peep on the way back to the cabin."),
        (day, "00:10",  0, "Back at the cabin",
         "Check ntfy / dashboard. Pull the SD card, copy to the desktop, verify two or "
         "three frames opened and are sharp. Fresh card in."),
        (day, "00:15",  5, "Carry the scope out from the porch",
         "Already at ambient, camera already cold. Onto the tripod - alt/az untouched, so this "
         "Polar align CHECK - the plate may have shifted and the ground settles, so expect a small "
         "adjustment. Not from scratch. DEW HEATERS ON NOW, low setting. "
         "Target 2-5C above ambient, no more - err low on the triplet."),
        (day, "01:00", 10, f"Scope on {deep_target}", deep_note),
        (day, "01:00",  5, "Canon meteor run - Cassiopeia/M31 field",
         "20s, f/1.8, ISO 3200, continuous. Radiant in the lower-left corner. "
         "Dew heater on the lens."),
        (day, "02:00", 15, "PERSEID PEAK HOURS",
         "Radiant climbs 47 to 61 deg. Rates roughly triple over the evening. Camera runs "
         "itself - both of you outside, in chairs, looking up."),
        (day, "03:45", 15, "Astronomical twilight - stop capture",
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
    ("2026-08-11", "21:56", 10, "ASTRONOMICAL DARK - scope to M8/M20",
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
)

# ── ics emitters ─────────────────────────────────────────────────────────
def esc(t):
    return (t.replace("\\", "\\\\").replace(";", r"\;")
             .replace(",", r"\,").replace("\n", r"\n"))

def fold(line):
    b = line.encode("utf-8")
    if len(b) <= 73:
        return line
    out, cur = [], b
    out.append(cur[:73].decode("utf-8", "ignore"))
    cur = cur[len(out[0].encode("utf-8")):]
    while cur:
        chunk = cur[:72].decode("utf-8", "ignore")
        out.append(" " + chunk)
        cur = cur[len(chunk.encode("utf-8")):]
    return "\r\n".join(out)

def to_utc(datestr, hhmm):
    d = datetime.strptime(datestr, "%Y-%m-%d")
    h, m = map(int, hhmm.split(":"))
    if h < 12:                      # small hours belong to the next calendar day
        d += timedelta(days=1)
    return d.replace(hour=h, minute=m) + timedelta(hours=UTC_OFFSET)

def event(idx, day, hhmm, alarm, summary, desc):
    s = to_utc(day, hhmm)
    e = s + timedelta(minutes=DUR_MIN)
    L = [
        "BEGIN:VEVENT",
        f"UID:pittsburg2026-{idx:03d}@stephen",
        "DTSTAMP:20260802T000000Z",
        f"DTSTART:{s:%Y%m%dT%H%M%S}Z",
        f"DTEND:{e:%Y%m%dT%H%M%S}Z",
        f"SUMMARY:{esc(summary)}",
        f"DESCRIPTION:{esc(desc)}",
        "BEGIN:VALARM",
        f"TRIGGER:-PT{alarm}M",
        "ACTION:DISPLAY",
        f"DESCRIPTION:{esc(summary)}",
        "END:VALARM",
        "END:VEVENT",
    ]
    return [fold(x) for x in L]

def main():
    out = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Pittsburg NH 2026//Trip Schedule//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Pittsburg NH - Aug 11-14 2026",
        "X-WR-TIMEZONE:America/New_York",
    ]
    i = 0
    for block in (PRETRIP, NIGHT1, NIGHT2, NIGHT3):
        for day, hhmm, alarm, summary, desc in block:
            out += event(i, day, hhmm, alarm, summary, desc)
            i += 1
    out.append("END:VCALENDAR")
    with open(OUT, "w", newline="") as f:
        f.write("\r\n".join(out) + "\r\n")
    print(f"wrote {OUT}: {i} events")

if __name__ == "__main__":
    main()
