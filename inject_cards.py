#!/usr/bin/env python3
"""
Keep three live weather cards at the top of index.html in step with the forecast.

    python3 inject_cards.py

index.html is hand-written — the trip plan, the schedules, the reasoning — and should stay
that way. Only the block between the FORECAST-CARDS markers is machine-owned; everything
around it is left untouched. If the markers are missing the file is not modified at all,
which is the safe failure for a document nobody wants a script rewriting.

Three cards, one per trip night, each carrying the two things you would actually check
before setting off: what the sky does after dark, and whether the daytime is wet.
"""

import json
import re
import sys
from datetime import datetime

import log_forecast as lf

PAGE = "index.html"
OPEN = "<!-- FORECAST-CARDS -->"
CLOSE = "<!-- /FORECAST-CARDS -->"

CSS = """
<style>
.fcards{display:grid;gap:.7rem;grid-template-columns:1fr;margin:1.1rem 0}
@media(min-width:38rem){.fcards{grid-template-columns:repeat(3,1fr)}}
.fc{background:var(--surface);border:1px solid var(--rule);border-radius:4px;padding:.8rem .9rem}
.fc .fch{font-family:var(--mono);font-size:.62rem;letter-spacing:.12em;text-transform:uppercase;
  color:var(--muted)}
.fc .fcn{font-family:var(--mono);font-size:1.9rem;line-height:1.1;margin:.25rem 0 .1rem;
  font-variant-numeric:tabular-nums}
.fc .fcv{font-family:var(--mono);font-size:.6rem;letter-spacing:.1em;text-transform:uppercase}
.fc .fcd{margin-top:.6rem;padding-top:.5rem;border-top:1px solid var(--rule);
  font-family:var(--mono);font-size:.72rem;color:var(--body)}
.fc .fcd .wx{font-size:1rem;margin-right:.2rem}
.fcgood{color:var(--good,#2E6B4F)} .fcwarn{color:var(--warn,#B5721A)}
.fcbad{color:var(--bad,#B03A2C)} .fcdim{color:var(--muted)}
.fcnote{font-size:.82rem;color:var(--muted);margin:.1rem 0 0}
</style>
"""


def build():
    hist = json.load(open(lf.HIST))
    e = hist[-1]
    day = e.get("daytime") or {}
    cond = e.get("cond") or {}
    trip = e.get("trip") or {}
    base = (lf._skill().get("climatology") or {}).get("p_trip_good")

    cards = []
    for label, date_ in lf.NIGHTS:
        nd = e["nights"].get(label) or {}
        c = lf.consensus(nd)
        d = datetime.strptime(date_, "%Y-%m-%d")
        # daytime keys are "Tue 11" style
        dk = next((k for k in day if k.endswith(f"{d.day:02d}") or k.endswith(f"{d.day}")), None)
        dv = day.get(dk) or {}

        if not c:
            val, cls, verd = "—", "fcdim", "no data"
        else:
            val = f"{c[0]}%"
            iqr = c[5] if len(c) > 5 else c[3]
            if iqr >= lf.NO_CONSENSUS:
                cls, verd = ("fcwarn" if c[0] <= 55 else "fcbad"), "unresolved"
            elif c[0] <= lf.GO:
                cls, verd = "fcgood", "go"
            elif c[0] <= 55:
                cls, verd = "fcwarn", "marginal"
            else:
                cls, verd = "fcbad", "poor"

        p = (trip.get("per") or {}).get(label)
        fog = (cond.get(label) or {}).get("fog_hours")
        wet = dv.get("wet_hours") or 0
        mm = dv.get("rain_mm") or 0
        icon = lf.wx_icon(_worst_code(dv), 18)
        dayline = (f'{icon} {dv.get("t_lo")}–{dv.get("t_hi")}°C · '
                   + ("dry" if wet == 0
                      else f"{wet} h drizzle" if mm < 1.0
                      else f"{wet} h rain")) if dv else "daytime not forecast yet"

        cards.append(
            f'<div class="fc"><div class="fch">{label} · {d:%a %d %b}</div>'
            f'<div class="fcn {cls}">{val}</div>'
            f'<div class="fcv {cls}">{verd}'
            + (f' <span class="fcdim">· {p}% usable</span>' if p is not None else '')
            + '</div>'
            + (f'<div class="fcd">{dayline}'
               + (f' <span class="fcbad">· fog {fog}h</span>' if fog else '')
               + '</div>')
            + '</div>')

    j = trip.get("joint")
    note = ""
    if j is not None and base is not None:
        d_ = j - base
        w = ("a better draw than these dates usually give" if d_ >= 10 else
             "about what these dates normally offer" if d_ >= -5 else
             "a worse draw than these dates usually give")
        note = (f'<p class="fcnote"><b>{j}%</b> chance at least one night gives you the core '
                f'— {w} ({base}% base rate). '
                f'<a href="forecast.html">Full forecast →</a></p>')

    stamp = datetime.fromisoformat(e["taken"])
    return (CSS + '<div class="fcards">' + "".join(cards) + '</div>' + note
            + f'<p class="fcnote" style="margin-top:.3rem">Cloud in the core window, '
              f'updated hourly · {stamp:%a %d %b %H:%M} EDT</p>')


def _worst_code(dv):
    """The most significant weather code of the day, for one icon."""
    hrs = dv.get("hours") or []
    if not hrs:
        return None
    codes = [h.get("code") for h in hrs if h.get("code") is not None]
    if not codes:
        return None
    precip = [c for c in codes if c in lf.PRECIP_CODES]
    return max(precip) if precip else max(codes)


def main():
    try:
        html = open(PAGE).read()
    except OSError as ex:
        print(f"  cannot read {PAGE}: {ex}")
        return 1
    if OPEN not in html or CLOSE not in html:
        print(f"  {PAGE} has no FORECAST-CARDS markers — not touching it")
        return 0
    block = build()
    new = re.sub(re.escape(OPEN) + r".*?" + re.escape(CLOSE),
                 OPEN + "\n" + block + "\n" + CLOSE, html, flags=re.S)
    if new != html:
        open(PAGE, "w").write(new)
        print(f"  updated the cards in {PAGE}")
    else:
        print(f"  {PAGE} cards already current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
