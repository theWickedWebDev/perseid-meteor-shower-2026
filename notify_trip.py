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
# The ntfy topic is a shared secret — anyone holding it can read these alerts and publish
# to them — so it lives in a gitignored file, never in the repo. Absent means ntfy is
# simply skipped; the desktop popup still works.
TOPIC_FILE = ".ntfy_topic"


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


def ntfy(title, body, priority="default", tags="milky_way"):
    """Phone push. Silently skipped if no topic file is present."""
    try:
        topic = open(TOPIC_FILE).read().strip()
    except Exception:
        return False
    if not topic:
        return False
    import urllib.request
    # HTTP headers are latin-1 only. The title carries an arrow glyph for the desktop
    # popup, and passing it here raised UnicodeEncodeError and dropped the push entirely —
    # the desktop notification succeeded, so the failure was invisible without testing the
    # real trigger path. Strip to ASCII for the header; the body is UTF-8 and unaffected.
    safe = title.encode("ascii", "replace").decode("ascii").replace("?", "")
    req = urllib.request.Request(
        f"https://ntfy.sh/{topic}", data=body.encode("utf-8"),
        headers={"Title": safe.strip(), "Priority": priority, "Tags": tags,
                 "Click": URL, "User-Agent": "perseid-meteor-shower-2026"})
    try:
        with urllib.request.urlopen(req, timeout=20):
            return True
    except Exception as ex:
        print(f"  ntfy failed: {str(ex)[:70]}")
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
        msg = f"Test notification. Base rate {base}%."
        d = notify(f"Trip odds {j}%", f"{msg}\n{URL}")
        n = ntfy(f"Trip odds {j}%", msg)
        print(f"  test sent — desktop {'ok' if d else 'failed'}, "
              f"ntfy {'ok' if n else 'skipped/failed'}")
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
    title = f"{arrow} Trip odds {j}%  (base {base}%)"
    notify(title, body, urgency)
    # phone gets the same thing; a verdict change is worth a high-priority push
    # arrow direction moves into the tags, which ntfy renders as an icon
    ntfy(title, body.replace(URL, "").strip(),
         priority="high" if crossed_verdict else "default",
         tags=("chart_with_downwards_trend" if delta < 0
               else "chart_with_upwards_trend") + ",milky_way")
    print(f"  notified: {pj}% -> {j}% ({delta:+d})"
          + (f", {'; '.join(why)}" if why else ""))
    json.dump({**cur, "at": datetime.now(EDT).isoformat()}, open(STATE, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
