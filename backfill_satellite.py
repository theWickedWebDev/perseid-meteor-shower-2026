#!/usr/bin/env python3
"""
Fill holes in satellite_log.json from the GOES archive.

    python3 backfill_satellite.py            # show what is missing, change nothing
    python3 backfill_satellite.py --write    # fetch and fill
    python3 backfill_satellite.py --write --since 2026-08-06T00:00

The hourly cron writes one satellite reading per hour. When the machine loses its
connection the hour is simply absent, and those gaps land in the record that every model
on the site is scored against — so a night the models got wrong can quietly vanish from
their scorecard because nobody was listening.

Unlike the webcam, this is recoverable. GOES-19 ABI-L2-ACMC granules sit in a public S3
bucket for months, so an hour missed at 03:00 can be read at 09:00 and is byte-identical
to what would have been recorded live.

Two things are NOT backfilled, deliberately:

  models   satellite.py stores what each model said for that hour, fetched live. Asking
           now would return the model's *current* opinion of a past hour, which is an
           analysis rather than the forecast that was standing at the time. Writing that
           into the same field would silently corrupt every model score computed from it.
           Backfilled rows carry no models and are marked, so they contribute ground truth
           without contributing a false forecast.

  webcam   the stream has no history. Frames missed are gone.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone

import satellite

LOG = "satellite_log.json"
EDT = timezone(timedelta(hours=-4))
MAX_FILL = 48          # refuse to hammer S3 over a long outage without being asked twice


def load():
    try:
        return json.load(open(LOG))
    except (OSError, ValueError):
        return []


def missing(log, since=None):
    """Hours between the first and last entry that have no reading."""
    if not log:
        return []
    have = {e["time"][:13] for e in log}
    first = datetime.fromisoformat(log[0]["time"]).replace(minute=0, second=0, microsecond=0)
    last = datetime.fromisoformat(log[-1]["time"]).replace(minute=0, second=0, microsecond=0)
    if since:
        first = max(first, datetime.fromisoformat(since).replace(tzinfo=first.tzinfo))
    out, cur = [], first
    while cur <= last:
        if cur.strftime("%Y-%m-%dT%H") not in have:
            out.append(cur)
        cur += timedelta(hours=1)
    return out


def main():
    write = "--write" in sys.argv
    since = None
    if "--since" in sys.argv:
        since = sys.argv[sys.argv.index("--since") + 1]

    log = load()
    if not log:
        print(f"  {LOG} is empty or unreadable")
        return 1
    gaps = missing(log, since)
    print(f"  {len(log)} readings, {log[0]['time'][:16]} → {log[-1]['time'][:16]}")
    if not gaps:
        print("  no gaps")
        return 0

    print(f"  {len(gaps)} missing hour{'s' if len(gaps) != 1 else ''}:")
    for g in gaps[:12]:
        print(f"    {g:%a %d %b %H:00}")
    if len(gaps) > 12:
        print(f"    ... and {len(gaps) - 12} more")
    if not write:
        print("\n  dry run — pass --write to fetch these")
        return 0
    if len(gaps) > MAX_FILL:
        print(f"\n  refusing: {len(gaps)} hours is more than MAX_FILL={MAX_FILL}. "
              f"Narrow it with --since.")
        return 1

    got = 0
    for g in gaps:
        # satellite.read wants UTC; the log is EDT
        rec = satellite.read(g.astimezone(timezone.utc))
        if not rec:
            print(f"  {g:%d %b %H:00}  no granule")
            continue
        # The granule found may not be the hour asked for — read() falls back an hour when
        # the current one has not published. Keep only what actually lands in the hole,
        # otherwise a gap gets filled with a duplicate of the reading beside it.
        if rec["time"][:13] != g.strftime("%Y-%m-%dT%H"):
            print(f"  {g:%d %b %H:00}  archive returned {rec['time'][11:16]} — skipped")
            continue
        rec["backfilled"] = True
        rec["models"] = {}
        log = [e for e in log if e.get("time") != rec["time"]] + [rec]
        got += 1
        print(f"  {g:%d %b %H:00}  cloud {rec['cloud']}%  "
              f"webcam {rec.get('cloud_webcam')}%  ({rec['granule'][:28]})")

    if got:
        log.sort(key=lambda e: e["time"])
        json.dump(log, open(LOG, "w"), indent=1)
        print(f"\n  wrote {got} reading{'s' if got != 1 else ''} to {LOG}")
    else:
        print("\n  nothing recovered")
    return 0


if __name__ == "__main__":
    sys.exit(main())
