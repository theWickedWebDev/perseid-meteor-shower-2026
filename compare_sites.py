#!/usr/bin/env python3
"""
Drive north, or stay home? The same forecast, run at two places.

    python3 compare_sites.py --lat 42.x --lon -71.x
    python3 compare_sites.py --lat 42.x --lon -71.x --json out.json

Home coordinates are arguments, never a constant — this repository publishes to the open
web. Nothing here writes them anywhere.

The comparison is deliberately NOT symmetric, and the output says so. A clear night at a
suburban site is not a substitute for a clear night under Bortle 2: the Milky Way core needs
dark as much as it needs transparency, and no amount of clear sky buys back a washed-out
background. What the home column is for is the case where the lake is hopeless — if
Pittsburg is 90% cloud and home is 20%, shooting something ordinary from the garden beats
driving five hours to sit in a car.

So this answers one question only: is the lake clear enough to be worth going to, and if it
is not, would home have been usable that night. It does not tell you home is "better".
"""

import json
import statistics as st
import sys
from datetime import datetime

import log_forecast as lf

MODELS = [("ecmwf_ifs025", "ECMWF"), ("gfs_seamless", "GFS"), ("icon_seamless", "ICON"),
          ("gem_seamless", "GEM"), ("jma_seamless", "JMA"), ("gem_hrdps_continental", "HRDPS"),
          ("ukmo_seamless", "UKMO")]
ENS = [("gfs025", "GEFS"), ("ecmwf_ifs025", "ECMWF ENS"), ("gem_global", "GEM ENS")]


def deterministic(lat, lon):
    """{night: {model: core-window cloud}} at one location."""
    out = {}
    for key, name in MODELS:
        url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
               f"&hourly=cloud_cover&models={key}&forecast_days=14"
               f"&timezone=America%2FNew_York")
        try:
            h = lf.get(url)["hourly"]
        except Exception:
            continue
        col = next((k for k in h if k.startswith("cloud_cover")), None)
        if not col:
            continue
        idx = {t: i for i, t in enumerate(h["time"])}
        for label, day in lf.NIGHTS:
            w = lf.core_weights(day)
            vals, wts = [], []
            for hh, wt in w.items():
                i = idx.get(f"{day}T{hh:02d}:00")
                if i is not None and h[col][i] is not None:
                    vals.append(h[col][i]); wts.append(wt)
            mv = lf.wmean(vals, wts)
            if mv is not None:
                out.setdefault(label, {})[name] = round(mv)
    return out


def ensemble(lat, lon):
    """P(core window under GO) per night, from pooled members."""
    rows = []
    for key, _ in ENS:
        try:
            h = lf.get(lf.ENS_URL.format(la=lat, lo=lon, m=key))["hourly"]
        except Exception:
            continue
        idx = {t: i for i, t in enumerate(h["time"])}
        for m in [k for k in h if k.startswith("cloud_cover")]:
            night = {}
            for label, day in lf.NIGHTS:
                w = lf.core_weights(day)
                vals, wts = [], []
                for hh, wt in w.items():
                    i = idx.get(f"{day}T{hh:02d}:00")
                    if i is not None and h[m][i] is not None:
                        vals.append(h[m][i]); wts.append(wt)
                mv = lf.wmean(vals, wts)
                if mv is not None:
                    night[label] = mv
            if len(night) == len(lf.NIGHTS):
                rows.append(night)
    if not rows:
        return None, 0
    per = {l: round(100 * sum(1 for r in rows if r[l] < lf.GO) / len(rows))
           for l, _ in lf.NIGHTS}
    anyn = round(100 * sum(1 for r in rows
                           if any(r[l] < lf.GO for l, _ in lf.NIGHTS)) / len(rows))
    return {"per": per, "any": anyn}, len(rows)


def climo(path, month=8, days=(11, 12, 13)):
    """The 30-year usable-night rate for these dates, if best_nights has been run."""
    try:
        rows = json.load(open(path))["rows"]
    except (OSError, ValueError, KeyError):
        return None
    v = [r["good_s"] for r in rows if r["month"] == month and r["day"] in days]
    return round(st.mean(v)) if v else None


def main():
    if "--lat" not in sys.argv or "--lon" not in sys.argv:
        print(__doc__.strip().split("\n\n")[1])
        return 1
    lat = float(sys.argv[sys.argv.index("--lat") + 1])
    lon = float(sys.argv[sys.argv.index("--lon") + 1])

    print("  fetching both sites...", flush=True)
    lake_d = deterministic(lf.SITE[1], lf.SITE[2])
    home_d = deterministic(lat, lon)
    lake_e, ln = ensemble(lf.SITE[1], lf.SITE[2])
    home_e, hn = ensemble(lat, lon)

    print(f"\n  THE SAME THREE NIGHTS, TWO PLACES\n")
    print(f"  {'night':<9}{'lake':>18}{'home':>18}")
    print("  " + "-"*45)
    verdicts = []
    for label, day in lf.NIGHTS:
        row = {"night": label, "date": day}
        cells = []
        for tag, d in (("lake", lake_d), ("home", home_d)):
            ms = d.get(label) or {}
            if not ms:
                cells.append("—"); row[tag] = None; continue
            med = round(st.median(ms.values()))
            spread = max(ms.values()) - min(ms.values())
            ab = lf.agree_band(spread)
            row[tag] = {"cloud": med, "spread": spread,
                        "trust": ab[0] if ab else None, "models": ms}
            cells.append(f"{med}% ±{spread}" + (f" ({ab[0]}%)" if ab else ""))
        print(f"  {label:<9}{cells[0]:>18}{cells[1]:>18}")
        verdicts.append(row)

    print(f"\n  {'':<9}{'lake':>18}{'home':>18}")
    print("  " + "-"*45)
    for label, _ in lf.NIGHTS:
        a = (lake_e or {}).get("per", {}).get(label)
        b = (home_e or {}).get("per", {}).get(label)
        print(f"  {label:<9}{(str(a)+'% clear') if a is not None else '—':>18}"
              f"{(str(b)+'% clear') if b is not None else '—':>18}")
    if lake_e and home_e:
        print(f"  {'any night':<9}{str(lake_e['any'])+'%':>18}{str(home_e['any'])+'%':>18}")
    print(f"  {'members':<9}{ln:>18}{hn:>18}")

    cl, ch = climo("best_nights.json"), climo("home_nights.json")
    if cl and ch:
        print(f"\n  30-year rate for these dates:  lake {cl}%   home {ch}%")

    print(f"""
  READ IT THIS WAY

  The lake is Bortle 2 and home is not, so these columns are not interchangeable.
  A clear night at home does not replace a clear night at the lake for the core —
  it replaces it for everything that does not need a dark background.

  Home is only the answer when the lake is hopeless. If the lake is workable, go:
  you cannot buy a dark sky with clear weather.
""")
    if "--json" in sys.argv:
        path = sys.argv[sys.argv.index("--json") + 1]
        json.dump({"taken": datetime.now().isoformat(), "nights": verdicts,
                   "lake_ens": lake_e, "home_ens": home_e,
                   "climo": {"lake": cl, "home": ch}}, open(path, "w"), indent=1)
        print(f"  wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
