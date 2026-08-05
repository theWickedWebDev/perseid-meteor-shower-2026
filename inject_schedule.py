#!/usr/bin/env python3
"""
Hang live weather off every time slot in the "same shape" schedule.

    python3 inject_schedule.py [file]        default: plan-weather.html

The schedule is written as one generic night — "every clear night, the same shape" — which
is the right way to plan and the wrong way to decide. This attaches, to each time, what the
forecast actually says for that hour on each of the three nights, so a row reads:

    7:15 PM   Load the car, depart, moose drive
              Tue 20° clear · Wed 18° cloud · Thu 15° rain

Then the generic plan tells you what to do and the badges tell you which night it will
work on.

Only the block between SCHEDULE-WX markers is touched; everything else in the file is left
alone. If the markers are absent the file is not modified.
"""

import json
import re
import sys
import urllib.request
from datetime import datetime, timedelta

import log_forecast as lf

DEFAULT = "plan-weather.html"
CACHE = "schedule_wx.json"
NIGHTS = [("Tue", "2026-08-11"), ("Wed", "2026-08-12"), ("Thu", "2026-08-13")]

# The schedule spans an evening into the small hours, so each night's window runs from
# 16:00 on the date to 06:00 the following morning.
SPAN_EVE = range(16, 24)
SPAN_AM = range(0, 7)


def fetch():
    """Hourly conditions across each night's full span. {night: {hour_int: {...}}}"""
    out = {}
    try:
        h = lf.get(f"https://api.open-meteo.com/v1/forecast?latitude={lf.SITE[1]}"
                   f"&longitude={lf.SITE[2]}&hourly=temperature_2m,precipitation_probability,"
                   f"precipitation,cloud_cover,weather_code,wind_speed_10m,dew_point_2m"
                   f"&forecast_days=14&timezone=America%2FNew_York")["hourly"]
    except Exception as ex:
        print(f"  hourly forecast unavailable: {str(ex)[:70]}")
        return out
    idx = {t: i for i, t in enumerate(h["time"])}
    for name, day in NIGHTS:
        nxt = (datetime.strptime(day, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        got = {}
        for d, hours in ((day, SPAN_EVE), (nxt, SPAN_AM)):
            for hh in hours:
                i = idx.get(f"{d}T{hh:02d}:00")
                if i is None:
                    continue
                got[hh] = {"t": h["temperature_2m"][i],
                           "pop": h["precipitation_probability"][i],
                           "mm": h["precipitation"][i],
                           "cloud": h["cloud_cover"][i],
                           "code": h["weather_code"][i],
                           "wind": h["wind_speed_10m"][i],
                           "dew": h["dew_point_2m"][i]}
        if got:
            out[name] = got
    return out


def parse_hour(label):
    """'9:56' or '12:10 AM' or '2:00–3:45' to an hour of the day, 0-23, or None.

    The schedule is written the way a person reads a clock: a bare '9:56' means evening
    because that is when the night starts, and only the small hours carry AM. Anything
    before 5 is morning, anything from 5 to 11 is evening.
    """
    m = re.match(r"(\d{1,2}):(\d{2})", label.strip())
    if not m:
        return None
    hh = int(m.group(1))
    up = label.upper()
    if "AM" in up:
        return 0 if hh == 12 else hh
    if "PM" in up:
        return hh if hh == 12 else hh + 12
    # A bare 12 in a night schedule is midnight, never noon — the plan runs 5 PM to 4 AM
    # and never mentions the middle of the day. Reading it as 12:00 put the "12:15 carry
    # the scope out" row at lunchtime.
    if hh == 12:
        return 0
    return hh if hh <= 4 else (hh + 12 if hh < 12 else hh)


# Rows that always carry their weather, even when the hour has not turned over. These are
# the ones a person actually reads before deciding whether tonight is the night — full dark,
# the core deadline, and the Perseid window — and dropping them because a row twenty minutes
# earlier already claimed the hour is exactly backwards.
LANDMARK = re.compile(r"astronomical (?:dark|twilight)|full dark|core (?:hits|deadline|sets)"
                      r"|south is finished|perseid|meridian", re.I)


def badge(name, w):
    """One night, one chip. Deliberately tiny — three of these sit on a single line.

    Cloud percentage only. Temperature and wind live in the tooltip: this row already has
    a time, a heading and a paragraph of reasoning competing for attention, and a fourth
    number on every line turns a schedule into a spreadsheet.
    """
    if not w:
        return ""
    cloud = w.get("cloud")
    cc = "sgood" if (cloud or 0) <= 30 else "swarn" if (cloud or 0) <= 65 else "sbad"
    wet = (w.get("mm") or 0) >= 0.1
    tip = (f"{name}: {cloud}% cloud · {w.get('pop')}% rain chance · "
           f"{round(w['t']) if w.get('t') is not None else '—'}°C · "
           f"{w.get('wind') or 0:.0f} km/h wind")
    return (f'<span class="swx {cc}" title="{tip}">'
            f'{lf.wx_icon(w.get("code"), 13)}<b>{name}</b>'
            f'<span class="scl">{cloud}%</span>'
            + ('<span class="srn">·rain</span>' if wet else '')
            + '</span>')


CSS = """
<style>
/* One line, in the description column. The first attempt put these in the time column,
   which is narrow — they stacked three deep and overran the text beside them. */
.swxrow{display:flex;gap:.3rem;margin-top:.45rem;flex-wrap:wrap;align-items:center}
.swx{display:inline-flex;align-items:center;gap:.22rem;font-family:var(--mono);
  font-size:.6rem;line-height:1;padding:.16rem .34rem;border:1px solid var(--rule);
  border-radius:10px;background:var(--surface);white-space:nowrap}
.swx .wxe{font-size:.72rem}
.swx b{font-weight:600;letter-spacing:.02em}
.swx .scl{opacity:.65;font-variant-numeric:tabular-nums}
.swx .srn{color:var(--alert,#B03A2C);font-weight:600}
.swx.sgood{border-color:var(--good,#2E6B4F);color:var(--good,#2E6B4F)}
.swx.swarn{border-color:var(--warn,#B5721A);color:var(--warn,#B5721A)}
.swx.sbad{border-color:var(--bad,#B03A2C);color:var(--bad,#B03A2C)}
.swxnote{font-size:.8rem;color:var(--muted);margin:.2rem 0 1rem}
/* Three chips are ~10 px wider than a 390 px phone allows, which wrapped Thursday — the
   wettest night of the three — onto a line of its own. Tighten rather than let the
   comparison break across rows; the whole point is reading the nights side by side. */
@media(max-width:30rem){
  .swxrow{gap:.22rem}
  .swx{font-size:.55rem;padding:.15rem .26rem;gap:.16rem}
  .swx .wxe{font-size:.66rem}
  /* The rain icon and the red border already say "rain"; the word is what pushed the
     third chip onto its own line. Phones have no hover, so the icon carries it alone. */
  .swx .srn{display:none}
}
</style>
"""


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    try:
        html = open(path).read()
    except OSError as ex:
        print(f"  cannot read {path}: {ex}")
        return 1

    wx = fetch()
    if not wx:
        try:
            wx = json.load(open(CACHE))
            print("  using cached hourly")
        except Exception:
            print("  no hourly data and no cache — leaving the file alone")
            return 0
    else:
        json.dump(wx, open(CACHE, "w"), indent=1)

    def annotate(seg):
        """Append a chip row to each description cell.

        Description cells contain spans but never nested divs, so a time cell followed by
        its description can be matched as one unit and the chips inserted before the
        closing tag. An earlier attempt walked the string with a state variable and lost
        the pending hour the moment it saw the next opening tag.
        """
        pat = re.compile(
            r'(<div class="[^"]*tl-t">)([^<]*)(</div>\s*<div class="[^"]*tl-e">)((?:[^<]|<(?!/div>))*)(</div>)',
            re.S)

        seen = {"hh": None}

        def one(m):
            hh = parse_hour(m.group(2))
            if hh is None:
                return m.group(0)
            # The forecast is hourly and the schedule is finer than that, so four
            # consecutive rows inside 8 PM would carry four identical chip rows. Print
            # them once, when the hour turns over; repetition reads as wallpaper and the
            # eye stops seeing any of it.
            if hh == seen["hh"] and not LANDMARK.search(m.group(4)):
                return m.group(0)
            seen["hh"] = hh
            bits = [b for b in (badge(n, (wx.get(n) or {}).get(hh)) for n, _ in NIGHTS) if b]
            if not bits:
                return m.group(0)
            return (m.group(1) + m.group(2) + m.group(3) + m.group(4)
                    + f'<div class="swxrow">{"".join(bits)}</div>' + m.group(5))

        return pat.sub(one, seg)

    # Locate the schedule. The page is hand-written and carries no markers, so anchor on
    # the section id and stop at the next <section — narrower than a marker pair, and it
    # cannot silently swallow the rest of the document if the id is ever renamed.
    m = re.search(r'<section id="shape">', html)
    if not m:
        print(f'  {path} has no <section id="shape"> — leaving it alone')
        return 0
    start = m.start()
    nxt = html.find("<section", start + 10)
    end = nxt if nxt > -1 else len(html)
    head, seg, tail = html[:start], html[start:end], html[end:]

    # Idempotent: strip anything a previous run left before adding this run's.
    seg = re.sub(r'<div class="swxrow">.*?</div>\s*(?=</div>)', "", seg, flags=re.S)
    seg = re.sub(r'<style>\s*/\* One line.*?</style>\s*', "", seg, flags=re.S)
    seg = re.sub(r'<p class="swxnote">.*?</p>\s*', "", seg, flags=re.S)

    seg2 = annotate(seg)
    n = seg2.count('class="swxrow"')
    note = ('<p class="swxnote">Each time carries the forecast for that hour on all three '
            'nights — the plan is the same every night, the weather is not. Shown once an hour, '
            'when the forecast changes. Border colour is cloud cover; <b>rain</b> means '
            'precipitation is forecast. Hover for temperature and wind.</p>')
    # after the section heading, before the timeline itself
    hm = re.search(r'</div>', seg2[seg2.find("sec-head"):])
    if hm:
        k = seg2.find("sec-head") + hm.end()
        seg2 = seg2[:k] + CSS + note + seg2[k:]

    out = head + seg2 + tail
    if out != html:
        open(path, "w").write(out)
        print(f"  annotated {n} time slots in {path}")
    else:
        print(f"  {path} already current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
