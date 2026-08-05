#!/usr/bin/env python3
"""
Desktop notification when the headline trip probability moves.

    python3 notify_trip.py            # check and notify if it changed
    python3 notify_trip.py --test     # send one regardless, to prove it works
    python3 notify_trip.py --status   # print state, notify nothing

Called at the end of publish.sh, so it fires at most once an hour.

Not every wobble is worth a notification. The joint probability shifts a point or two
whenever an ensemble refreshes, and a popup for that is noise you would learn to ignore —
at which point it fails on the day it matters. So it fires on:

  a move of MIN_DELTA points or more, or
  crossing the climatological base rate in either direction, or
  crossing the "better draw" threshold that drives the verdict wording

Crossings are notified even when small, because those are the moments the page's own
conclusion changes.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

EDT = timezone(timedelta(hours=-4))
STATE = ".notify_trip.json"
HIST = "forecast_history.json"
SKILL = "skill.json"
MIN_DELTA = 5          # points; smaller moves are ensemble churn
BETTER_BY = 10         # the margin that makes the verdict say "a better draw"
URL = "https://thewickedwebdev.github.io/perseid-meteor-shower-2026/forecast.html"


def notify(title, body, urgency="normal"):
    """Desktop popup. Needs DISPLAY and DBUS when called from cron."""
    env = dict(os.environ)
    env.setdefault("DISPLAY", ":0")
    env.setdefault("DBUS_SESSION_BUS_ADDRESS", "unix:path=/run/user/1000/bus")
    try:
        subprocess.run(["notify-send", "-u", urgency, "-a", "Pittsburg trip",
                        "-i", "weather-clear-night", title, body],
                       env=env, check=True, timeout=20)
        return True
    except Exception as ex:
        print(f"  notify-send failed: {str(ex)[:70]}")
        return False


def current():
    try:
        h = json.load(open(HIST))
    except Exception:
        return None
    t = (h[-1] or {}).get("trip") if h else None
    if not t:
        return None
    base = None
    try:
        base = (json.load(open(SKILL)).get("climatology") or {}).get("p_trip_good")
    except Exception:
        pass
    return {"joint": t.get("joint"), "per": t.get("per"), "n": t.get("n"),
            "spread_floor": t.get("floor"), "base": base,
            "ladder": {str(e["thr"]): e["joint"] for e in (t.get("ladder") or [])}}


def verdict(j, base):
    if base is None:
        return "no base rate"
    d = j - base
    return ("better draw" if d >= BETTER_BY else
            "worse draw" if d <= -5 else "normal draw")


def main():
    cur = current()
    if not cur or cur["joint"] is None:
        print("  no trip figure yet")
        return 0
    prev = {}
    if os.path.exists(STATE):
        try:
            prev = json.load(open(STATE))
        except Exception:
            prev = {}

    j, base = cur["joint"], cur["base"]
    pj = prev.get("joint")

    if "--status" in sys.argv:
        print(f"  now {j}%  ·  last notified {pj}%  ·  base {base}%  "
              f"·  verdict {verdict(j, base)}")
        return 0

    if "--test" in sys.argv:
        notify(f"Trip odds {j}%", f"Test notification. Base rate {base}%.\n{URL}")
        print("  test sent")
        return 0

    if pj is None:
        json.dump({**cur, "at": datetime.now(EDT).isoformat()}, open(STATE, "w"), indent=1)
        print(f"  first run — baseline set at {j}%, nothing sent")
        return 0

    delta = j - pj
    crossed_base = base is not None and ((pj < base) != (j < base))
    crossed_verdict = verdict(j, base) != verdict(pj, base)
    if abs(delta) < MIN_DELTA and not crossed_base and not crossed_verdict:
        print(f"  {j}% (was {pj}%, {delta:+d}) — below the {MIN_DELTA}-point floor, quiet")
        return 0

    arrow = "▲" if delta > 0 else "▼" if delta < 0 else "→"
    why = []
    if crossed_verdict:
        why.append(f"now reads as a {verdict(j, base)}")
    elif crossed_base:
        why.append(f"crossed the {base}% base rate")
    lad = cur.get("ladder") or {}
    # per-night odds, with the move on each since the last notification
    pper = prev.get("per") or {}
    nights = []
    for k, v in (cur.get("per") or {}).items():
        was = pper.get(k)
        d = f" ({v - was:+d})" if isinstance(was, int) else ""
        nights.append(f"{k}: {v}%{d}")
    detail = []
    if nights:
        detail.append("   ".join(nights))
    if lad.get("10"):
        detail.append(f"genuinely good night: {lad['10']}%   "
                      f"pristine: {lad.get('5', '—')}%")
    body = (f"{pj}% → {j}%   ({delta:+d})\n"
            + (("  " + "; ".join(why) + "\n") if why else "")
            + ("  " + "\n  ".join(detail) + "\n" if detail else "")
            + URL)
    urgency = "critical" if crossed_verdict else "normal"
    notify(f"{arrow} Trip odds {j}%  (base {base}%)", body, urgency)
    print(f"  notified: {pj}% -> {j}% ({delta:+d})"
          + (f", {'; '.join(why)}" if why else ""))
    json.dump({**cur, "at": datetime.now(EDT).isoformat()}, open(STATE, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
