#!/usr/bin/env python3
"""
When is the best time of year to shoot from Pittsburg, on weather alone?

    python3 best_nights.py            # fetch (slow, ~30 requests) and write best_nights.json
    python3 best_nights.py --show     # report from the cache

Thirty years of ERA5 at the lake site, every night of the year, asking what fraction of
years had a shootable core window on that date. Nothing here knows or cares what is in the
sky — no Milky Way season, no moon, no meteor showers. Purely: how often is it clear, and
when it is clear, is it also pleasant to stand in.

Four things are scored, because "best night" is not only cloud:

  clear    mean cloud below GO across the night window. The dominant term.
  dew      temperature within DEW_SPREAD of the dew point with little wind — the failure
           mode that ruins optics on a night the cloud forecast called perfect.
  wind     enough to shake a mount.
  cold     how hard the night is to stand in, which decides whether you last until 3 AM.

A night is "good" when it is clear and not dewing. The rest is reported alongside rather
than folded in, because trading a clear night against a cold one is a judgement, not a
calculation.

ERA5 is reanalysis at ~25 km, so it smooths local decks and valley fog — the two things
this site is worst for. Read the shape of the year from this, not the absolute numbers.
"""

import json
import os
import statistics as st
import sys
import time
import urllib.request
from datetime import date, datetime, timedelta

SITE = (45.2393, -71.1964)          # the lake — override with --lat/--lon
YEARS = range(1996, 2026)           # 30 full years
NIGHT_HOURS = (22, 23, 0, 1, 2)     # attributed to the evening's date
GO = 30                             # % cloud, shootable
DEW_SPREAD = 2.0                    # °C between air and dew point
DEW_WIND = 5.0                      # km/h below which dew settles
WINDY = 20.0                        # km/h, shakes a mount
SMOOTH = 7                          # ± days, to see season rather than noise
OUT = "best_nights.json"
TRIP = True          # show the 11-13 Aug block; off for other sites
UA = {"User-Agent": "perseid-meteor-shower-2026"}


def get(url, tries=3):
    for a in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r:
                return json.load(r)
        except Exception:
            if a == tries - 1:
                raise
            time.sleep(4 * (a + 1))


def fetch():
    """One request per year. Returns {(month, day): [per-year night summaries]}."""
    nights = {}
    for y in YEARS:
        url = (f"https://archive-api.open-meteo.com/v1/archive?latitude={SITE[0]}"
               f"&longitude={SITE[1]}&start_date={y}-01-01&end_date={y}-12-31"
               f"&hourly=cloud_cover,temperature_2m,dew_point_2m,wind_speed_10m"
               f"&timezone=America%2FNew_York")
        try:
            h = get(url)["hourly"]
        except Exception as ex:
            print(f"  {y}: {str(ex)[:70]}", flush=True)
            continue
        acc = {}
        for i, t in enumerate(h["time"]):
            hh = int(t[11:13])
            if hh not in NIGHT_HOURS:
                continue
            d = datetime.strptime(t[:10], "%Y-%m-%d").date()
            # 00:00-02:00 belong to the previous evening
            if hh < 12:
                d -= timedelta(days=1)
            c = h["cloud_cover"][i]
            tm, dp = h["temperature_2m"][i], h["dew_point_2m"][i]
            wd = h["wind_speed_10m"][i]
            if None in (c, tm, dp, wd):
                continue
            a = acc.setdefault(d, {"c": [], "t": [], "s": [], "w": []})
            a["c"].append(c)
            a["t"].append(tm)
            a["s"].append(tm - dp)
            a["w"].append(wd)
        for d, a in acc.items():
            if len(a["c"]) < len(NIGHT_HOURS) - 1:
                continue
            cloud = st.mean(a["c"])
            dewy = sum(1 for s_, w_ in zip(a["s"], a["w"])
                       if s_ <= DEW_SPREAD and w_ <= DEW_WIND)
            nights.setdefault((d.month, d.day), []).append({
                "cloud": cloud,
                "clear": cloud < GO,
                "dew_h": dewy,
                "wind": st.mean(a["w"]),
                "temp": st.mean(a["t"]),
            })
        print(f"  {y} ok", flush=True)
    return nights


def summarise(nights):
    rows = []
    for (m, d), ns in sorted(nights.items()):
        if (m, d) == (2, 29) or len(ns) < 10:
            continue
        n = len(ns)
        clear = sum(1 for x in ns if x["clear"]) / n * 100
        # dew is only a problem on a night you would otherwise have used
        usable = [x for x in ns if x["clear"]]
        dewy = (sum(1 for x in usable if x["dew_h"] >= 2) / len(usable) * 100) if usable else 0
        rows.append({
            "month": m, "day": d, "n": n,
            "clear": round(clear, 1),
            "good": round(clear * (1 - dewy / 100), 1),
            "dew_pct": round(dewy),
            "median_cloud": round(st.median(x["cloud"] for x in ns)),
            "windy_pct": round(sum(1 for x in ns if x["wind"] >= WINDY) / n * 100),
            "temp": round(st.median(x["temp"] for x in ns), 1),
        })
    # a single date is 30 samples and jumps around; the season is the real signal
    for i, r in enumerate(rows):
        win = [rows[(i + k) % len(rows)] for k in range(-SMOOTH, SMOOTH + 1)]
        r["clear_s"] = round(st.mean(x["clear"] for x in win), 1)
        r["good_s"] = round(st.mean(x["good"] for x in win), 1)
        r["temp_s"] = round(st.mean(x["temp"] for x in win), 1)
    return rows


MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def report(rows):
    by_month = {}
    for r in rows:
        by_month.setdefault(r["month"], []).append(r)
    print(f"\n  BY MONTH — {rows[0]['n']} years per date, night window "
          f"{NIGHT_HOURS[0]}:00–{NIGHT_HOURS[-1]:02d}:00\n")
    print(f"  {'':<6}{'clear':>7}{'usable':>8}{'dew':>6}{'windy':>7}{'temp':>7}   {'':<22}")
    print("  " + "-"*58)
    order = sorted(by_month, key=lambda m: -st.mean(x["good"] for x in by_month[m]))
    for m in range(1, 13):
        v = by_month[m]
        good = st.mean(x["good"] for x in v)
        bar = "#" * int(good / 1.4)
        rank = order.index(m) + 1
        print(f"  {MONTHS[m]:<6}{st.mean(x['clear'] for x in v):>6.0f}%{good:>7.0f}%"
              f"{st.mean(x['dew_pct'] for x in v):>5.0f}%"
              f"{st.mean(x['windy_pct'] for x in v):>6.0f}%"
              f"{st.mean(x['temp'] for x in v):>6.0f}°   {bar} {'←' if rank == 1 else ''}")

    print(f"\n  BEST DATES — smoothed ±{SMOOTH} days, so these are seasons not lucky days\n")
    top = sorted(rows, key=lambda r: -r["good_s"])[:15]
    print(f"  {'date':<9}{'usable':>8}{'clear':>7}{'temp':>7}")
    print("  " + "-"*33)
    for r in top:
        print(f"  {MONTHS[r['month']]} {r['day']:<5}{r['good_s']:>7.0f}%"
              f"{r['clear_s']:>6.0f}%{r['temp_s']:>6.0f}°")

    print(f"\n  WORST\n")
    for r in sorted(rows, key=lambda r: r["good_s"])[:5]:
        print(f"  {MONTHS[r['month']]} {r['day']:<5}{r['good_s']:>7.0f}%"
              f"{r['clear_s']:>6.0f}%{r['temp_s']:>6.0f}°")

    trip = [r for r in rows if r["month"] == 8 and 11 <= r["day"] <= 13] if TRIP else []
    if trip:
        rank = sorted(rows, key=lambda r: -r["good_s"])
        pos = rank.index(max(trip, key=lambda r: r["good_s"])) + 1
        print(f"\n  YOUR TRIP — 11–13 Aug\n")
        for r in trip:
            print(f"  {MONTHS[r['month']]} {r['day']:<5}{r['good_s']:>7.0f}% usable"
                  f"{r['clear_s']:>6.0f}% clear{r['temp_s']:>6.0f}°  "
                  f"dew on {r['dew_pct']}% of clear nights")
        print(f"\n  best of the three ranks {pos} of {len(rows)} nights in the year "
              f"({100*pos/len(rows):.0f}th percentile).")


def _args():
    """--lat/--lon/--out, so this can be pointed anywhere.

    Deliberately arguments rather than a config entry: the interesting comparison is a home
    site, and home coordinates do not belong in a repository that publishes to the open web.
    Passed on the command line they stay in the shell, and --out keeps the result out of the
    tree unless someone chooses otherwise.
    """
    global SITE, OUT
    for flag, cast in (("--lat", float), ("--lon", float), ("--out", str)):
        if flag in sys.argv:
            v = cast(sys.argv[sys.argv.index(flag) + 1])
            if flag == "--lat":
                SITE = (v, SITE[1])
            elif flag == "--lon":
                SITE = (SITE[0], v)
            else:
                OUT = v
    if "--lat" in sys.argv or "--lon" in sys.argv:
        globals()["TRIP"] = False


def main():
    _args()
    if "--show" in sys.argv:
        if not os.path.exists(OUT):
            print(f"  {OUT} not written yet — run without --show first")
            return 1
        report(json.load(open(OUT))["rows"])
        return 0
    print(f"  fetching {len(list(YEARS))} years of ERA5 at {SITE}...", flush=True)
    nights = fetch()
    if not nights:
        print("  nothing fetched")
        return 1
    rows = summarise(nights)
    json.dump({"computed": datetime.now().isoformat(), "years": [YEARS[0], YEARS[-1]],
               "night_hours": list(NIGHT_HOURS), "go": GO, "rows": rows},
              open(OUT, "w"), indent=1)
    print(f"\n  wrote {OUT} — {len(rows)} dates")
    report(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
