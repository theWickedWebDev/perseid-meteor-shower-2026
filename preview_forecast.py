#!/usr/bin/env python3
"""
Render forecast_preview.html from FAKE data, so the full UI is visible before the real
data exists. Touches nothing real — writes only forecast_preview.html.

    python3 preview_forecast.py

Run automatically by publish.sh so it never drifts from the real page.

The invented story is the realistic and instructive one: at long range everything looks
mediocre and the models disagree wildly; as lead time shortens they converge and the
nights separate — the pivot night into a clear GO, night 3 into a washout. That's the
shape of decision you'll actually be making.
"""

import random
from datetime import datetime, timedelta
import log_forecast as lf

DAYS = 5
BASE = datetime(2026, 8, 4, 13, 40, tzinfo=lf.EDT)

# core-window cloud cover by snapshot day. None = outside the NWS window.
STORY = {
    "Night 1":    [57, 62, 48, 55, 41],
    "Night 2":    [None, 66, 54, 47, 24],    # the pivot converges GOOD
    "Night 3":    [None, None, 61, 58, 72],  # deteriorates
    "Lead-up 05": [42, 38, None, None, None],
    "Lead-up 06": [54, 47, 31, None, None],
    "Lead-up 07": [65, 71, 58, 44, None],
    "Lead-up 08": [53, 60, 66, 51, 39],
    "Lead-up 09": [62, 55, 49, 58, 46],
    "Lead-up 10": [64, 58, 63, 49, 55],
}
# model spread narrows as the forecast gets closer — the whole point of the display
SPREAD_BY_LEAD = {9: 82, 8: 60, 7: 52, 6: 44, 5: 36, 4: 28, 3: 18, 2: 12, 1: 8, 0: 6}
MODELS = ["ECMWF", "GFS", "GEM", "ICON"]


def clamp(v):
    return max(0, min(100, int(round(v))))


def curve(rng, mean, hours=8):
    """A plausible hourly cloud profile with roughly the given mean."""
    trend = rng.uniform(-2.2, 2.2)
    wobble = rng.uniform(3, 12)
    vals = [mean + trend * (i - hours / 2) + rng.uniform(-wobble, wobble) for i in range(hours)]
    off = mean - sum(vals) / len(vals)
    return [clamp(v + off) for v in vals]


def build():
    hist = []
    for i in range(DAYS):
        taken = BASE + timedelta(days=i)
        rng = random.Random(20260804 + i)          # deterministic, so reruns look the same
        nights = {}
        for label, day in lf.ALL:
            d0 = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=lf.EDT)
            lead = (d0.date() - taken.date()).days
            v = STORY.get(label, [None] * DAYS)[i]

            if lead < 0 or (v is None and lead > 7):
                nights[label] = {"date": day, "lead": lead, "core": None, "core_best": None,
                                 "late": None, "late_best": None, "pop": None, "dark": None,
                                 "core_best_hr": None, "late_best_hr": None,
                                 "flat": True, "models": {}, "models_late": {},
                                 "models_hourly": {}, "hour_labels": [], "rows": []}
                continue

            spread = SPREAD_BY_LEAD.get(max(lead, 0), 20)
            centre = v if v is not None else clamp(rng.uniform(30, 70))

            hours = [f"{h:02d}" for h in list(range(lf.DARK[0], 24))
                     + list(range(0, lf.DARK[1] + 1))]
            mh, mc, ml = {}, {}, {}
            for k, name in enumerate(MODELS):
                # spread the models symmetrically around the NWS value
                off = (k - (len(MODELS) - 1) / 2) * (spread / max(len(MODELS) - 1, 1))
                row = curve(rng, clamp(centre + off), hours=len(hours))
                mh[name] = row
                hi = {h: j for j, h in enumerate(hours)}
                mc[name] = clamp(sum(row[hi[f"{h:02d}"]] for h in lf.CORE_HR) / len(lf.CORE_HR))
                ml[name] = clamp(sum(row[hi[f"{h:02d}"]] for h in lf.LATE_HR) / len(lf.LATE_HR))

            nws_row = curve(rng, centre, hours=len(hours))
            rows = [{"h": f"{h}:00", "sky": nws_row[j],
                     "pop": clamp(nws_row[j] - 25), "dew": 14.0}
                    for j, h in enumerate(hours)]
            hi_ = {h: j for j, h in enumerate(hours)}
            core_p = [(nws_row[hi_[f"{h:02d}"]], h) for h in lf.CORE_HR]
            late_p = [(nws_row[hi_[f"{h:02d}"]], h) for h in lf.LATE_HR]
            core = [v for v, _ in core_p]
            late = [v for v, _ in late_p]

            nights[label] = {
                "date": day, "lead": lead,
                "core": clamp(sum(core) / 2),
                "core_best": min(core_p)[0], "core_best_hr": min(core_p)[1],
                "late": clamp(sum(late) / 3),
                "late_best": min(late_p)[0], "late_best_hr": min(late_p)[1],
                "dark": clamp(sum(nws_row) / len(nws_row)),
                "pop": clamp(centre - 25),
                "flat": False,
                "models": mc, "models_late": ml, "models_hourly": mh,
                "hour_labels": hours, "rows": rows,
            }

        # Trip odds tighten as the pivot night converges — the whole point of the display.
        # Night 1 fades, Night 2 firms up, Night 3 decays, and the joint number holds up
        # because you only need one of them.
        per = {"Night 1": [30, 28, 34, 26, 21][i],
               "Night 2": [38, 41, 48, 57, 72][i],
               "Night 3": [35, 33, 30, 26, 18][i]}
        joint = [62, 66, 71, 76, 81][i]
        # the ladder tightens as the pivot night firms up — the top of it barely moves,
        # the bottom of it moves a lot, which is the point of showing five standards
        ladder = [{"thr": t_, "word": w_,
                   "joint": max(0, min(100, joint - off + i * gain)),
                   "per": {l: max(0, min(100, per[l] - off // 2)) for l, _ in lf.NIGHTS}}
                  for t_, w_, off, gain in ((40, "sucker holes", -7, 0), (30, "shootable", 0, 0),
                                            (20, "genuinely good", 11, 1),
                                            (10, "excellent", 27, 2), (5, "pristine", 38, 3))]
        # fog: night 2 goes calm and saturated as the ridge builds — the classic trap where
        # the best-forecast night is the one that fogs
        cond = {}
        for lab, _ in lf.ALL:
            r = {"hours": 14}
            if lab == "Night 2":
                r.update(fog_hours=[0, 0, 1, 3, 4][i], spread=[4.1, 3.2, 1.8, 0.9, 0.4][i],
                         wind=[14.0, 11.0, 6.2, 3.1, 1.8][i], worst_hr="02:00",
                         worst_is_fog=bool([0, 0, 1, 3, 4][i]))
            elif lab == "Night 3":
                r.update(fog_hours=0, spread=5.4, wind=18.0, worst_hr="23:00",
                         worst_is_fog=False)
            else:
                r.update(fog_hours=[1, 1, 0, 0, 0][i], spread=2.6, wind=7.4,
                         worst_hr="03:00", worst_is_fog=bool([1, 1, 0, 0, 0][i]))
            if lab.startswith("Lead-up") or i >= 3:
                r["aod"] = [0.12, 0.18, 0.24, 0.36, 0.41][i]
                r["pm25"] = [4.0, 6.5, 9.0, 14.0, 17.5][i]
            cond[lab] = r

        hist.append({
            "taken": taken.isoformat(),
            "trip": {"per": per, "joint": joint, "n": 103, "ladder": ladder,
                     "indep": joint + 1, "floor": max(per.values()), "corr": -0.03,
                     "sources": {"GEFS": 31, "ECMWF ENS": 51, "GEM ENS": 21}},
            "cond": cond,
            "issued": (taken - timedelta(hours=5)).astimezone().isoformat(),
            "grid": "GYX 28,125 (MOCK)",
            "runs": {"ECMWF": ("06Z", f"{taken:%d %b} 09:06"),
                     "GFS":   ("12Z", f"{taken:%d %b} 13:52"),
                     "ICON":  ("12Z", f"{taken:%d %b} 11:53")},
            "nights": nights,
        })
    return hist


def mock_webcam():
    """Reuse whatever real frames exist, with invented numbers, so the filmstrip renders."""
    import glob, os
    shots = sorted(glob.glob("webcam/*.jpg"))
    if not shots:
        return None
    rng = random.Random(7)
    out, now = [], BASE + timedelta(days=DAYS - 1)
    for i in range(18):
        t = now - timedelta(hours=17 - i)
        night = t.hour >= 21 or t.hour <= 4
        obs = None if night else clamp(rng.uniform(0, 85))
        ms = {}
        for name in MODELS[:3]:
            base = obs if obs is not None else rng.uniform(20, 80)
            ms[name] = clamp(base + rng.uniform(-22, 22))
        out.append({"time": t.isoformat(), "cloud": obs, "night": night,
                    "shot": shots[i % len(shots)], "models": ms,
                    "stats": {"lum": 12.0 if night else 190.0, "lum_sd": 4.0,
                              "lum_p90": 20.0, "sat": 3.0 if night else 45.0, "rb": 0.98}})
    return out


def mock_satellite():
    """A night that clears from the north-west — the case the compass exists to show.

    Past 12 h is invented "observation": socked in at dusk, the north opening around 23:00
    while the core direction stays shut, then everything breaking through by 02:00. Forward
    12 h is invented HRRR with a second band arriving late.
    """
    from datetime import datetime as dt
    OCT = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
    # (hour offset from start, per-octant values in OCT order)
    story = [
        (100, 100, 100, 100, 100, 100, 100, 100),
        (100, 100, 100, 100,  95, 100, 100, 100),
        ( 89,  95, 100, 100,  95, 100,  95,  89),
        ( 67,  85,  95, 100,  95, 100,  89,  72),
        ( 45,  70,  90,  95,  95, 100,  78,  55),
        ( 22,  55,  80,  90,  90,  95,  60,  33),
        (  8,  35,  70,  85,  85,  92,  45,  15),
        (  0,  18,  55,  75,  80,  89,  30,   5),
        (  0,   8,  35,  60,  70,  75,  15,   0),
        (  0,   0,  20,  40,  50,  48,   5,   0),
        (  0,   0,   8,  20,  25,  18,   0,   0),
        (  0,   0,   0,   8,  10,   4,   0,   0),
    ]
    fcst = [
        (  0,   0,   0,   5,   8,   2,   0,   0),
        (  0,   0,   0,   0,   5,   0,   0,   0),
        (  0,   0,   0,   0,   0,   0,   0,   0),
        (  0,   0,   0,   0,   0,   0,   0,   0),
        (  0,   0,   0,   0,   0,   0,   5,   8),
        (  5,   0,   0,   0,   0,   8,  20,  25),
        ( 18,   8,   0,   0,   5,  25,  45,  50),
        ( 40,  22,   5,   0,  15,  48,  70,  72),
        ( 65,  45,  18,   8,  35,  70,  88,  90),
        ( 82,  68,  38,  20,  58,  85,  95,  95),
        ( 92,  85,  60,  40,  78,  95, 100, 100),
        ( 98,  95,  80,  62,  90, 100, 100, 100),
    ]
    start = BASE.replace(hour=17, minute=0) - timedelta(hours=len(story) - 1)
    past = []
    for k, row in enumerate(story):
        o = dict(zip(OCT, row))
        t = start + timedelta(hours=k)
        past.append({"time": t.isoformat(), "scan": t.isoformat(),
                     "cloud": round(sum(row) / len(row)), "octants": o,
                     "slot": {"near": o["S"], "mid": o["SW"], "far": o["W"]},
                     "upwind": o["NW"], "wind_from": 300, "pixel": 1,
                     "prob": round(sum(row) / len(row) / 100, 2), "off_km": 0.46,
                     "models": {"ECMWF": max(0, o["S"] - 12), "GFS": min(100, o["S"] + 18),
                                "GEM": max(0, o["S"] - 25), "ICON": o["S"],
                                "AIFS": min(100, o["S"] + 9), "JMA": max(0, o["S"] - 6)}})
    fut = []
    for k, row in enumerate(fcst):
        t = start + timedelta(hours=len(story) + k)
        fut.append({"time": t.isoformat(), "octants": dict(zip(OCT, row)),
                    "cloud": round(sum(row) / len(row)), "kind": "forecast",
                    "model": "ncep_hrrr_conus"})
    return past, fut


if __name__ == "__main__":
    lf.PAGE = "forecast_preview.html"
    lf.WEBCAM_OVERRIDE = mock_webcam()
    lf.SAT_OVERRIDE, lf.FCST_OVERRIDE = mock_satellite()
    # the skill cache is real (it is climatology plus verification, not a forecast), but
    # fall back to plausible numbers if it has never been computed on this machine
    import os, json as _j
    if not os.path.exists("skill.json"):
        lf._skill = lambda: {
            "climatology": {"years": 30, "median": 72, "p_night_good": 31,
                            "p_trip_good": 67, "window": "Aug 11-13", "per_night": {}},
            "lead_skill": {"n_hours": 51,
                           "by_lead": {str(k): {"mean": v, "median": max(4, v // 3), "n": 357}
                                       for k, v in enumerate([20, 15, 18, 21, 18, 21, 23, 38])},
                           "by_model": {"AIFS": {"0": 9, "1": 9, "2": 13, "5": 12, "6": 13, "7": 33},
                                        "ECMWF": {"0": 9, "1": 9, "2": 15, "5": 22, "6": 24, "7": 47}}}}
    lf.write_page(build())

    s = open(lf.PAGE).read()
    s = s.replace("<h1>Forecast trend</h1>",
        '<h1>Forecast trend</h1>\n'
        '<div style="margin:.6rem 0 0;padding:.7rem .9rem;border:1px solid var(--bad);'
        'border-left:3px solid var(--bad);border-radius:3px;background:var(--surface)">'
        '<b style="color:var(--bad)">MOCK DATA — none of this is a real forecast.</b> '
        '<span style="display:block;margin-top:.2rem;font-size:.9rem">Invented to preview the '
        'full UI after five days of logging. Webcam frames are real photos with fabricated '
        'numbers. The real page is <a href="forecast.html">forecast.html</a>.</span></div>')
    s = s.replace("<title>Forecast trend", "<title>PREVIEW (mock) — Forecast trend")
    open(lf.PAGE, "w").write(s)
    print(f"wrote {lf.PAGE} — {DAYS} mock snapshots, all sections populated")
