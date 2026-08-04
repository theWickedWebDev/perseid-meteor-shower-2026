#!/usr/bin/env python3
"""
Generate pittsburg-2026.ics — the trip schedule as phone calendar events with alarms.

The schedule itself lives in schedule_data.py, shared with make_schedules.py so the
calendar and the markdown cannot drift apart. Edit it there, not here.

Import once on the phone and it handles every reminder natively: works offline, no
dependency on the Pi, the network, or a script staying alive. Re-run to regenerate.

    python3 make_calendar.py

All times are EDT (UTC-4) and are emitted as UTC so no VTIMEZONE block is needed.
"""

from datetime import datetime, timedelta

from schedule_data import PRETRIP, NIGHT1, NIGHT2, NIGHT3, _verify_astro

UTC_OFFSET = 4            # EDT
DUR_MIN    = 10           # default event length
OUT        = "pittsburg-2026.ics"


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
    """Local wall-clock on `datestr` to UTC. The date is taken literally.

    This deliberately does NOT roll small hours to the next day. It used to, which
    double-shifted every entry that already carried the correct post-midnight date and
    also pushed 11:00 daytime tasks a day late. Entries after midnight now name the day
    they actually fall on, which is the only representation with one meaning.
    """
    d = datetime.strptime(datestr, "%Y-%m-%d")
    h, m = map(int, hhmm.split(":"))
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
