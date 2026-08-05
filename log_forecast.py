#!/usr/bin/env python3
"""
Snapshot the NWS forecast for the trip nights, log it, and rebuild forecast.html.

Runs hourly from cron via publish.sh. Manual run:

    python3 log_forecast.py

Writes three things:
  forecast_history.json  — machine-readable history, one entry per run
  FORECAST_LOG.md        — human-readable log, newest first
  forecast.html          — trend chart of how each night's prediction has moved

Pulls raw gridpoint data (hourly sky cover, PoP, dewpoint) rather than the worded
forecast, because "40% chance of showers" says nothing about whether it's clear at
10 PM and sky cover says everything.
"""

import json, os, re, urllib.request
from datetime import datetime, timedelta, timezone

SITE    = ("Lake spot", 45.2393, -71.1964)
UA      = "perseid-meteor-shower-2026 (https://github.com/theWickedWebDev/perseid-meteor-shower-2026)"
EDT     = timezone(timedelta(hours=-4))
WEBCAM_SITE = (45.0958, -71.2600)   # First Connecticut Lake cam, not the shooting site
HIST    = "forecast_history.json"
LOG     = "FORECAST_LOG.md"
PAGE    = "forecast.html"

NIGHTS  = [("Night 1", "2026-08-11"), ("Night 2", "2026-08-12"), ("Night 3", "2026-08-13")]
# nights before the trip — they verify while you watch, so they calibrate how much a
# forecast actually moves in this pattern. Tracked and tabled, not charted.
LEADUP  = [(f"Lead-up {d[-2:]}", d) for d in
           ("2026-08-05","2026-08-06","2026-08-07","2026-08-08","2026-08-09","2026-08-10")]
ALL     = NIGHTS + LEADUP
CORE_HR = (22, 23)          # 21:56–23:30 EDT — Milky Way core, at the lake
LATE_HR = (1, 2, 3)         # 12:45–03:45 EDT — Perseid peak + refractor, at the cabin
DARK    = (18, 7)           # hourly strips run 6 PM–7 AM: the shooting window plus
                            # context either side, so a trend into or out of it is visible
DARK_HOURS = [f"{h:02d}" for h in list(range(18, 24)) + list(range(0, 8))]
GO      = 30                # go/no-go threshold, % cloud cover
SUCKER  = 40                # 30-40%: not a go, but breaks open — OH_SHIT.md territory
SCORE_MIN_N = 12            # scored webcam frames before the model ranking means anything
SCORE_MIN_SPREAD = 30       # ...and they must span this much cloud, or every model wins
NO_CONSENSUS = 40           # spread at or above this and no median is worth a verdict;
                            # matches the "no consensus" label on the agreement chart

# Second opinion: Open-Meteo exposes individual models rather than a blend. ECMWF is the
# most skillful global model and is genuinely independent of NWS's GFS/NAM-based product.
# The point isn't more data — it's that MODEL AGREEMENT IS A CONFIDENCE SIGNAL. A narrow
# spread means the atmosphere is predictable; a wide one means nobody knows yet.
# Reach varies a lot and changes daily, so models are not filtered by range here — a
# model simply contributes to the nights it can see. UKMO (~7 d) and HRRR (48 h) are
# useless for the trip today and become the best sources available in the final days.
OM_MODELS = [("ecmwf_ifs025", "ECMWF"), ("gfs_seamless", "GFS"),
             ("icon_seamless", "ICON"), ("gem_seamless", "GEM"),
             ("ecmwf_aifs025_single", "AIFS"), ("jma_gsm", "JMA"),
             ("ukmo_global_deterministic_10km", "UKMO"),
             ("ncep_hrrr_conus", "HRRR")]
# Open-Meteo publishes per-dataset run metadata. The slugs differ from the model
# parameter names used in the forecast call, and not every dataset stays current —
# anything older than 48 h is treated as unknown rather than printed as fact.
OM_META = [("ECMWF", "ecmwf_ifs025"), ("GFS", "ncep_gfs013"), ("ICON", "dwd_icon"),
           ("GEM", "cmc_gem_gdps"), ("AIFS", "ecmwf_aifs025_single"), ("JMA", "jma_gsm"),
           ("UKMO", "ukmo_global_deterministic_10km"), ("HRRR", "ncep_hrrr_conus")]

OM_URL = ("https://api.open-meteo.com/v1/forecast?latitude={la}&longitude={lo}"
          "&hourly=cloud_cover&models={m}&timezone=America%2FNew_York&forecast_days=14")

def hr12(h):
    """22 -> '10 PM'. Hours read faster than 24h codes on a card."""
    h = int(h)
    return f"{(h % 12) or 12} {'AM' if h < 12 else 'PM'}"


# validated categorical slots 1–3 (all-pairs, both modes) + dash as secondary encoding
SERIES = [("#2a78d6", "#3987e5", "none"),
          ("#eb6834", "#d95926", "7 4"),
          ("#1baf7a", "#199e70", "2 4")]


# ── fetch ────────────────────────────────────────────────────────────────
def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def expand(series):
    """NWS gives ISO intervals like 2026-08-04T06:00:00+00:00/PT6H. Flatten to hourly."""
    out = {}
    for v in series.get("values", []):
        t, dur = v["validTime"].split("/")
        start = datetime.fromisoformat(t)
        m = re.match(r"P(?:(\d+)D)?T?(?:(\d+)H)?", dur)
        hours = (int(m.group(1) or 0) * 24) + int(m.group(2) or 0) or 1
        for h in range(hours):
            out[(start + timedelta(hours=h)).astimezone(EDT).isoformat()] = v["value"]
    return out


def model_runs():
    """{name: (init_utc, avail_local)} for each model whose metadata is current."""
    out = {}
    for name, slug in OM_META:
        try:
            d = get(f"https://api.open-meteo.com/data/{slug}/static/meta.json")
            init = datetime.fromtimestamp(d["last_run_initialisation_time"], timezone.utc)
            avail = datetime.fromtimestamp(d["last_run_availability_time"], timezone.utc)
            if (datetime.now(timezone.utc) - avail).total_seconds() > 48 * 3600:
                continue                      # dataset has gone stale — don't claim a run time
            out[name] = (init.strftime("%HZ"), avail.astimezone(EDT).strftime("%d %b %H:%M"),
                         avail.timestamp())
        except Exception:
            pass
    return out


def open_meteo():
    """Per-model core-window cloud cover for each night. {night: {model: value}}"""
    url = OM_URL.format(la=SITE[1], lo=SITE[2], m=",".join(m for m, _ in OM_MODELS))
    try:
        h = get(url)["hourly"]
    except Exception as ex:
        print(f"  open-meteo unavailable: {ex}")
        return {}
    times = h["time"]
    out = {}
    for label, day in ALL:
        nxt = (datetime.strptime(day, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        ic = [i for i, t in enumerate(times)
              if any(t.startswith(f"{day}T{hh:02d}") for hh in CORE_HR)]
        il = [i for i, t in enumerate(times)
              if any(t.startswith(f"{nxt}T{hh:02d}") for hh in LATE_HR)]
        # full night hour-by-hour, so structure is visible instead of averaged away
        hrs = [(day, hh) for hh in range(DARK[0], 24)] + [(nxt, hh) for hh in range(0, DARK[1] + 1)]
        per, perl, hourly = {}, {}, {}
        for key, name in OM_MODELS:
            col = h.get(f"cloud_cover_{key}") or []
            vc = [col[i] for i in ic if i < len(col) and col[i] is not None]
            vl = [col[i] for i in il if i < len(col) and col[i] is not None]
            if vc:
                per[name] = round(sum(vc) / len(vc))
            if vl:
                perl[name] = round(sum(vl) / len(vl))
            row = []
            for dd, hh in hrs:
                try:
                    j = times.index(f"{dd}T{hh:02d}:00")
                    row.append(col[j] if j < len(col) else None)
                except ValueError:
                    row.append(None)
            if any(v is not None for v in row):
                hourly[name] = row
        if per or perl or hourly:
            out[label] = {"core": per, "late": perl, "hourly": hourly,
                          "hours": [f"{hh:02d}" for _, hh in hrs]}
    return out


KEEP_FULL = 12      # entries retaining full hourly detail; older ones keep only what the
                    # page actually reads back — the consensus, the per-model window values


def compact(hist):
    """Drop hourly detail from old entries, preserving every rendered number.

    Only the newest entry is drawn hour-by-hour; older ones contribute a single point to
    the trend chart and a row to the movement table. Keeping their full hourly arrays cost
    about 19 KB each and would have reached ~2.7 MB by the end of the trip, rewritten and
    committed hourly. The consensus is computed and stored before the source is removed,
    so no displayed value changes.
    """
    for e in hist[:-KEEP_FULL]:
        for nd in e.get("nights", {}).values():
            if "cons" in nd or not nd.get("models_hourly"):
                continue
            for key, late in (("cons", False), ("cons_late", True)):
                c = consensus(nd, late)
                if c:
                    nd[key] = list(c)
            for k in ("rows", "models_hourly", "hour_labels"):
                nd.pop(k, None)
    return hist


# ── the decision layer ───────────────────────────────────────────────────
# The page answers "how much cloud on the 12th". The actual question is "should we drive
# four hours on the 8th", and you do not need the 12th — you need ONE of three nights to
# give you ninety minutes. That is a joint probability, and guessing at how correlated
# consecutive nights are would be the same overconfidence this page keeps fixing. Each
# GEFS member is one physically consistent scenario across all three nights, so counting
# members measures the correlation instead of assuming it.
# Three ensembles, pooled. GEFS alone was the single most optimistic source on the page —
# 90% joint against ECMWF's 82% and GEM's 71% — and it is GFS's ensemble, the one family
# these notes elsewhere describe as run-to-run volatile. Pooling is 103 members instead of
# 31 and stops the headline resting on one centre.
ENS_MODELS = (("gfs025", "GEFS"), ("ecmwf_ifs025", "ECMWF ENS"), ("gem_global", "GEM ENS"))
ENS_URL = ("https://ensemble-api.open-meteo.com/v1/ensemble?latitude={la}&longitude={lo}"
           "&hourly=cloud_cover&models={m}&forecast_days=14"
           "&timezone=America%2FNew_York")

# Fog. Radiative cooling needs a clear sky, so the nights that fog are the nights that
# forecast best — anti-correlated with the very number the page optimises. Saturated and
# calm under clear sky is the signature; wind mixes the layer out and prevents it.
FOG_SPREAD = 2.0     # deg C between temperature and dewpoint
FOG_WIND   = 5.0     # km/h at 10 m
FOG_CLOUD  = 40      # % — above this there is no radiative cooling to drive it

# Transparency. Cloud cover reads 0% straight through wildfire smoke, and northern NH sits
# downwind of Quebec in August. AOD above this is a visibly milky sky.
AOD_HAZY = 0.30


def core_weights(day):
    """Hour weights for the core window on `day` — how much of each hour the core is up.

    CORE_HR treated 22 and 23 equally, but the Milky Way core drops below the treeline at
    about 23:17 (and four minutes earlier each night), so most of hour 23 is already gone.
    Weighting by the minutes actually available stops a cloudy 23:40 counting as heavily as
    a cloudy 22:15.
    """
    end = {"2026-08-11": 23 + 21 / 60, "2026-08-12": 23 + 17 / 60,
           "2026-08-13": 23 + 13 / 60}.get(day, 23 + 17 / 60)
    out = {}
    for h in CORE_HR:
        frac = max(0.0, min(1.0, end - h))
        if frac > 0:
            out[h] = frac
    return out or {CORE_HR[0]: 1.0}


def wmean(vals, weights):
    tot = sum(weights)
    return sum(v * w for v, w in zip(vals, weights)) / tot if tot else None


def ensemble_trip():
    """Per-night and joint probability of a usable core window, pooled across ensembles.

    Also reports the independence bound and the measured member correlation, because the
    joint is only meaningful alongside them. At 7-9 days the members carry almost no
    night-to-night correlation — but neither do the real years: thirty Augusts of ERA5 give
    a mean r of +0.035 and a joint that sits one point off its own independence bound. So
    near-independence here is the behaviour of these dates, not an artefact. Both numbers
    are published so the assumption stays visible rather than buried.
    """
    rows, per_model = [], {}
    for key, label in ENS_MODELS:
        try:
            h = get(ENS_URL.format(la=SITE[1], lo=SITE[2], m=key))["hourly"]
        except Exception as ex:
            print(f"  {label} unavailable: {str(ex)[:60]}")
            continue
        idx = {t: i for i, t in enumerate(h["time"])}
        got = 0
        for m in [k for k in h if k.startswith("cloud_cover")]:
            night = {}
            for lab, day in NIGHTS:
                w = core_weights(day)
                vals, wts = [], []
                for hh, wt in w.items():
                    i = idx.get(f"{day}T{hh:02d}:00")
                    if i is not None and h[m][i] is not None:
                        vals.append(h[m][i]); wts.append(wt)
                mv = wmean(vals, wts)
                if mv is not None:
                    night[lab] = mv
            if len(night) == len(NIGHTS):
                rows.append(night); got += 1
        if got:
            per_model[label] = got
    if not rows:
        return None

    per = {lab: sum(1 for r in rows if r[lab] < GO) / len(rows) for lab, _ in NIGHTS}
    joint = sum(1 for r in rows if any(r[lab] < GO for lab, _ in NIGHTS)) / len(rows)
    ind = 1.0
    for v in per.values():
        ind *= (1 - v)
    ind = 1 - ind

    # mean pairwise correlation between nights, so the reader can judge the joint
    import statistics as _st
    labs = [l for l, _ in NIGHTS]
    rs = []
    for i in range(len(labs)):
        for j in range(i + 1, len(labs)):
            xs = [r[labs[i]] for r in rows]; ys = [r[labs[j]] for r in rows]
            mx, my = _st.mean(xs), _st.mean(ys)
            num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
            den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** .5
            if den:
                rs.append(num / den)
    return {"per": {l: round(100 * v) for l, v in per.items()},
            "joint": round(100 * joint), "n": len(rows),
            "indep": round(100 * ind),
            "floor": round(100 * max(per.values())),
            "corr": round(_st.mean(rs), 3) if rs else None,
            "sources": per_model}


def conditions():
    """Fog risk and aerosol per night. {night: {fog_hours, spread, wind, aod, pm25}}."""
    out = {}
    try:
        h = get(f"https://api.open-meteo.com/v1/forecast?latitude={SITE[1]}&longitude={SITE[2]}"
                f"&hourly=temperature_2m,dew_point_2m,wind_speed_10m,cloud_cover"
                f"&forecast_days=14&timezone=America%2FNew_York")["hourly"]
    except Exception as ex:
        print(f"  fog inputs unavailable: {ex}")
        h = None
    aq = None
    try:
        aq = get(f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={SITE[1]}"
                 f"&longitude={SITE[2]}&hourly=aerosol_optical_depth,pm2_5"
                 f"&forecast_days=7&timezone=America%2FNew_York")["hourly"]
    except Exception as ex:
        print(f"  air quality unavailable: {ex}")

    for label, day in ALL:
        nxt = (datetime.strptime(day, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        keys = [f"{day}T{x:02d}:00" for x in range(DARK[0], 24)] + \
               [f"{nxt}T{x:02d}:00" for x in range(0, DARK[1] + 1)]
        rec = {}
        if h:
            idx = {t: i for i, t in enumerate(h["time"])}
            risk, spreads, winds = 0, [], []
            for k in keys:
                i = idx.get(k)
                if i is None:
                    continue
                t, td = h["temperature_2m"][i], h["dew_point_2m"][i]
                w, c = h["wind_speed_10m"][i], h["cloud_cover"][i]
                if None in (t, td, w, c):
                    continue
                sp = t - td
                spreads.append(sp)
                winds.append(w)
                if sp < FOG_SPREAD and w < FOG_WIND and c < FOG_CLOUD:
                    risk += 1
            if spreads:
                rec.update(fog_hours=risk, spread=round(min(spreads), 1),
                           wind=round(min(winds), 1), hours=len(spreads))
        if aq:
            idx = {t: i for i, t in enumerate(aq["time"])}
            a = [aq["aerosol_optical_depth"][idx[k]] for k in keys
                 if idx.get(k) is not None and aq["aerosol_optical_depth"][idx[k]] is not None]
            pm = [aq["pm2_5"][idx[k]] for k in keys
                  if idx.get(k) is not None and aq["pm2_5"][idx[k]] is not None]
            if a:
                rec.update(aod=round(max(a), 2), pm25=round(max(pm), 1) if pm else None)
        if rec:
            out[label] = rec
    return out


def snapshot():
    p = get(f"https://api.weather.gov/points/{SITE[1]},{SITE[2]}")["properties"]
    grid = get(p["forecastGridData"])["properties"]
    sky, pop, dew = (expand(grid[k]) for k in
                     ("skyCover", "probabilityOfPrecipitation", "dewpoint"))
    om = open_meteo()
    runs = model_runs()
    trip = ensemble_trip()
    cond = conditions()

    stamp = datetime.now(EDT)
    entry = {"taken": stamp.isoformat(),
             "issued": grid.get("updateTime"),          # when NWS published this package
             "runs": runs,                              # model init + availability times
             "grid": f"{p['gridId']} {p['gridX']},{p['gridY']}",
             "trip": trip,                              # joint probability from GEFS members
             "cond": cond,                              # fog risk and aerosol per night
             "nights": {}}

    for label, day in ALL:
        d0 = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=EDT)
        hrs = [d0.replace(hour=h) for h in range(DARK[0], 24)] + \
              [(d0 + timedelta(days=1)).replace(hour=h) for h in range(0, DARK[1] + 1)]
        rows = [{"h": h.strftime("%H:%M"),
                 "sky": sky.get(h.isoformat()),
                 "pop": pop.get(h.isoformat()),
                 "dew": dew.get(h.isoformat())} for h in hrs]
        have = [r["sky"] for r in rows if r["sky"] is not None]
        # keep the hour with each value so "best hour" can say WHICH hour
        core_p = [(r["sky"], int(r["h"][:2])) for r in rows
                  if r["sky"] is not None and int(r["h"][:2]) in CORE_HR]
        late_p = [(r["sky"], int(r["h"][:2])) for r in rows
                  if r["sky"] is not None and int(r["h"][:2]) in LATE_HR]
        core = [v for v, _ in core_p]
        late = [v for v, _ in late_p]
        entry["nights"][label] = {
            "date": day,
            "lead": (d0.date() - stamp.date()).days,
            "core": round(sum(core) / len(core)) if core else None,
            "core_best": min(core_p)[0] if core_p else None,   # clearest single hour — "is there
            "core_best_hr": min(core_p)[1] if core_p else None,
            "late": round(sum(late) / len(late)) if late else None,   # a shootable moment?"
            "late_best": min(late_p)[0] if late_p else None,
            "late_best_hr": min(late_p)[1] if late_p else None,
            "dark": round(sum(have) / len(have)) if have else None,
            "pop":  max([r["pop"] for r in rows if r["pop"] is not None], default=None),
            "flat": len(set(have)) == 1 if have else None,
            "models": (om.get(label) or {}).get("core", {}),
            "models_late": (om.get(label) or {}).get("late", {}),
            "models_hourly": (om.get(label) or {}).get("hourly", {}),
            # Derived from DARK, not from the Open-Meteo payload. It used to come from
            # the payload, so an Open-Meteo outage silently took out the hourly strips,
            # the ensemble profile and the best-hour figure — while NWS hourly sky cover
            # sat unused in "rows" the whole time.
            "hour_labels": DARK_HOURS,
            "rows": rows,
        }
    return entry


# ── markdown log ─────────────────────────────────────────────────────────
def write_log(hist):
    head = ("# Forecast Log — Pittsburg NH, Aug 11–14 2026\n\n"
            f"Chart of how these have moved: **[forecast.html](forecast.html)**\n\n"
            "Updated hourly by cron. Newest entry first.\n\n"
            "**Watch how a given night moves as lead time shortens.** A night that holds steady "
            "across several days is a real signal; one that swings 40 points between runs is "
            "telling you the model doesn't know yet.\n\n"
            "Sky cover is the number that matters — **PoP is not a cloud forecast.** An overcast "
            "rainless night reads 0% precipitation and is a total loss.\n\n"
            "**Decision point: Aug 8.** Pivot night is **Aug 12/13** — Perseid maximum and new "
            f"moon. Go if the core window looks under ~{GO}% cloud.\n\n---\n\n")

    out = [head]
    for e in reversed(hist):
        t = datetime.fromisoformat(e["taken"])
        out.append(f"## {t:%a %d %b %Y, %H:%M} EDT\n\n"
                   f"`api.weather.gov` gridpoint **{e['grid']}** · {SITE[0]}\n\n")
        for label, _ in NIGHTS:
            n = e["nights"][label]
            d = datetime.strptime(n["date"], "%Y-%m-%d")
            out.append(f"### {label} · {d:%a %d %b} — lead {n['lead']} day"
                       f"{'s' if n['lead'] != 1 else ''}\n\n")
            if n["core"] is None and n["dark"] is None:
                out.append("_Outside the forecast window — no data yet._\n\n")
                continue
            out.append(f"**Core window mean sky cover: {n['core']}%** · full-dark "
                       f"{n['dark']}% · max PoP {n['pop']}%\n\n")
            if n["flat"]:
                out.append("> ⚠️ Every hour reads the same value — the model isn't resolving "
                           "hours at this lead time. One coarse long-range number stretched "
                           "across the night, not an hourly forecast. Pattern context only.\n\n")
            rows = n.get("rows")
            if not rows:
                # compact() drops the hourly detail from old entries once only their
                # headline numbers are still rendered; the log has to tolerate that
                out.append("_Hourly detail compacted — headline figures above._\n\n")
                continue
            out.append("| Hour (EDT) | Sky | PoP | Dewpoint |\n|---|---|---|---|\n")
            for r in rows:
                if r["sky"] is None and r["pop"] is None:
                    continue
                dp = f"{r['dew']*9/5+32:.0f}°F" if r["dew"] is not None else "—"
                out.append(f"| {r['h']} | {r['sky'] if r['sky'] is not None else '—'}% | "
                           f"{r['pop'] if r['pop'] is not None else '—'}% | {dp} |\n")
            out.append("\n")
        out.append("---\n\n")
    open(LOG, "w").write("".join(out))


# ── chart page ───────────────────────────────────────────────────────────
def svg_chart(hist):
    W, H = 720, 320
    L, R, T, B = 46, 108, 18, 42
    pw, ph = W - L - R, H - T - B

    xs = [datetime.fromisoformat(e["taken"]) for e in hist]
    n = len(xs)
    def px(i): return L + (pw / 2 if n == 1 else pw * i / (n - 1))
    def py(v): return T + ph * (1 - v / 100)

    p = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Predicted core-window sky cover '
         f'for each trip night, by forecast date" preserveAspectRatio="xMidYMid meet">']

    # Two bands. Under 30% is a go. 30-40% is not, but it is the range where the deck
    # breaks often enough to be worth sitting outside for — the OH_SHIT.md case.
    p.append(f'<rect class="sband" x="{L}" y="{py(SUCKER):.1f}" width="{pw}" '
             f'height="{py(GO)-py(SUCKER):.1f}"/>')
    p.append(f'<text class="sbandlab" x="{L+6}" y="{py(GO)-4:.1f}">'
             f'{GO}-{SUCKER}% — sucker holes</text>')
    p.append(f'<rect class="band" x="{L}" y="{py(GO):.1f}" width="{pw}" '
             f'height="{T+ph-py(GO):.1f}"/>')
    p.append(f'<text class="bandlab" x="{L+6}" y="{T+ph-8:.1f}">under {GO}% — go</text>')

    # gridlines + y labels
    for v in (0, 25, 50, 75, 100):
        p.append(f'<line class="grid" x1="{L}" y1="{py(v):.1f}" x2="{L+pw}" y2="{py(v):.1f}"/>')
        p.append(f'<text class="ax" x="{L-8}" y="{py(v)+4:.1f}" text-anchor="end">{v}%</text>')

    # X labels, thinned. A two-line stamp needs ~34 px and the plot is only `pw` wide, so
    # past roughly 16 snapshots every label would be drawn on top of its neighbour. Keep
    # every nth, always including the newest, and show the date only when the day changes.
    step = max(1, -(-n * 34 // max(int(pw), 1)))
    keep = sorted({0, n - 1} | set(range(n - 1, -1, -step)))
    prev_day = None
    for i in sorted(keep):
        d = xs[i]
        if d.strftime("%d %b") != prev_day:
            p.append(f'<text class="ax" x="{px(i):.1f}" y="{T+ph+18:.0f}" '
                     f'text-anchor="middle">{d:%d %b}</text>')
            prev_day = d.strftime("%d %b")
        p.append(f'<text class="ax dim" x="{px(i):.1f}" y="{T+ph+32:.0f}" '
                 f'text-anchor="middle">{d:%H:%M}</text>')

    # model spread as vertical range bars — uncertainty at each forecast run
    for si, (label, _) in enumerate(NIGHTS):
        for i, e in enumerate(hist):
            r = mrange(e["nights"][label])
            if not r:
                continue
            lo, hi, _ = r
            off = (si - 1) * 4          # nudge so the three don't overlap exactly
            p.append(f'<line class="rng{si}" x1="{px(i)+off:.1f}" y1="{py(lo):.1f}" '
                     f'x2="{px(i)+off:.1f}" y2="{py(hi):.1f}"/>')

    # series
    for si, (label, _) in enumerate(NIGHTS):
        pts = [(i, consensus(e["nights"][label])[0]) for i, e in enumerate(hist)
               if consensus(e["nights"][label])]
        if not pts:
            continue
        dash = SERIES[si][2]
        da = '' if dash == "none" else f' stroke-dasharray="{dash}"'
        if len(pts) > 1:
            d = " ".join(f"{'M' if k == 0 else 'L'}{px(i):.1f},{py(v):.1f}"
                         for k, (i, v) in enumerate(pts))
            p.append(f'<path class="s{si}" d="{d}" fill="none"{da}/>')
        for i, v in pts:
            p.append(f'<circle class="s{si} dot" cx="{px(i):.1f}" cy="{py(v):.1f}" r="4.5"/>')
        li, lv = pts[-1]
        p.append(f'<text class="s{si} lab" x="{px(li)+12:.1f}" y="{py(lv)+4:.1f}">'
                 f'{label} · {lv}%</text>')

    p.append(f'<line class="axis" x1="{L}" y1="{T+ph}" x2="{L+pw}" y2="{T+ph}"/>')
    p.append("</svg>")
    return "\n".join(p)


def members(nd, late=False):
    """{source: cloud%} for the window — every model plus NWS, as equal members.

    NWS is one opinion among several, not the answer. It is the only member that
    stops at 7 days, so for the trip nights it is simply absent early on and the
    ensemble carries on without it.
    """
    m = dict(nd.get("models_late" if late else "models") or {})
    n = nd.get("late" if late else "core")
    if n is not None:
        m["NWS"] = n
    return m


def consensus(nd, late=False):
    """(value, lo, hi, spread, n) — the ensemble's view of a window, or None.

    Median rather than mean: with GEM at 92 and ECMWF at 38 for the same night, a
    mean invents a number no model actually forecasts and lets one outlier drag the
    verdict. The median is the middle opinion, and it survives one model going rogue.

    The median is taken hour by hour and then averaged across the window, rather
    than the other way round, so that the best-hour figure is drawn from the same
    series — otherwise "best hour" can come out worse than the window containing it.
    lo/hi stay per-source window means, so the spread compares whole forecasts.
    """
    # Compacted history entries carry the already-computed answer, because the hourly
    # series it was derived from has been dropped. Without this, compaction would quietly
    # change every historical point on the trend chart.
    cached = nd.get("cons_late" if late else "cons")
    if cached:
        return tuple(cached)
    m = members(nd, late)
    if not m:
        return None
    v = sorted(m.values())
    k = len(v)
    mid = v[k // 2] if k % 2 else (v[k // 2 - 1] + v[k // 2]) / 2
    eh = ens_hourly(nd)
    hv = [eh[f"{h:02d}"] for h in (LATE_HR if late else CORE_HR) if f"{h:02d}" in eh]
    val = int(round(sum(hv) / len(hv))) if hv else int(round(mid))
    return val, v[0], v[-1], v[-1] - v[0], k


def ens_hourly(nd):
    """{hour: median across all members} — the ensemble's own hourly profile."""
    hrs = nd.get("hour_labels") or []
    mh = nd.get("models_hourly") or {}
    nws = {r["h"][:2]: r["sky"] for r in (nd.get("rows") or [])}
    out = {}
    for i, h in enumerate(hrs):
        vals = [row[i] for row in mh.values() if i < len(row) and row[i] is not None]
        if nws.get(h) is not None:
            vals.append(nws[h])
        if vals:
            s = sorted(vals)
            k = len(s)
            out[h] = int(round(s[k // 2] if k % 2 else (s[k // 2 - 1] + s[k // 2]) / 2))
    return out


def best_hour(nd, hours):
    """(cloud%, hour) of the clearest hour in the window by ensemble median, or (None, None)."""
    eh = ens_hourly(nd)
    p = [(eh[f"{h:02d}"], h) for h in hours if f"{h:02d}" in eh]
    return min(p) if p else (None, None)


def mrange(nd, late=False):
    """(lo, hi, spread) across all members — kept for the spread columns."""
    c = consensus(nd, late)
    return None if c is None else (c[1], c[2], c[3])


def agreement_svg(latest):
    """Small multiples: where each model sits for each night, and how wide the spread is.

    Models are samples of a distribution, not categorical identities — so one hue plus
    direct labels, not four competing colours. The range bar is the actual message.

    Labels are placed in tiers: when two models land close together their names would
    collide, so each is pushed to the next free row with a leader line back to its dot.
    """
    def tier(xs, minsep):
        """Greedy row assignment — lowest row where this x clears the last one placed."""
        rows, out = [], []
        for x in xs:
            for t, last in enumerate(rows):
                if x - last >= minsep:
                    rows[t] = x; out.append(t); break
            else:
                rows.append(x); out.append(len(rows) - 1)
        return out

    W, PAD = 720, 92
    nights = [(l, latest["nights"][l]) for l, _ in NIGHTS]
    tw = W - PAD - 118
    def x(v): return PAD + tw * v / 100

    # Pre-pass: the number of sources varies (models drop in and out by range), and with
    # eight of them the name and value labels tier several deep. Measure the deepest
    # stack first and size the rows to it, rather than trusting a fixed height that was
    # only ever right for four models.
    prep, up, dn = [], 1, 1
    for label, nd in nights:
        mods = members(nd)
        if not mods:
            prep.append((label, None))
            continue
        pts = sorted(mods.items(), key=lambda kv: kv[1])
        xs = [x(v) for _, v in pts]
        lt, vt = tier(xs, 40), tier(xs, 24)     # names need ~40px, numbers ~24px
        up, dn = max(up, max(lt) + 1), max(dn, max(vt) + 1)
        prep.append((label, (nd, mods, pts, xs, lt, vt)))
    rowsH = max(92, 24 + up * 12 + 22 + dn * 12)
    H = rowsH * len(nights) + 26

    p = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Spread between forecast models '
         f'for each night" preserveAspectRatio="xMidYMid meet">']
    p.append(f'<rect class="sband" x="{x(GO):.1f}" y="14" '
             f'width="{x(SUCKER)-x(GO):.1f}" height="{H-30}"/>')
    p.append(f'<rect class="band" x="{PAD}" y="14" width="{x(GO)-PAD:.1f}" height="{H-30}"/>')
    for v in (0, 25, 50, 75, 100):
        p.append(f'<line class="grid" x1="{x(v):.1f}" y1="14" x2="{x(v):.1f}" y2="{H-16}"/>')
        p.append(f'<text class="ax" x="{x(v):.1f}" y="{H-4}" text-anchor="middle">{v}%</text>')

    for i, (label, got) in enumerate(prep):
        y = 20 + up * 12 + i * rowsH
        p.append(f'<text class="nlab" x="0" y="{y+4}">{label}</text>')
        if not got:
            p.append(f'<text class="ax" x="{PAD}" y="{y+4}">no model data</text>')
            continue
        nd, mods, pts, xs, lt, vt = got
        lo, hi = min(mods.values()), max(mods.values())
        p.append(f'<line class="rng" x1="{x(lo):.1f}" y1="{y}" x2="{x(hi):.1f}" y2="{y}"/>')

        for (name, v), px_, tl, tv in zip(pts, xs, lt, vt):
            ly = y - 13 - tl * 12
            vy = y + 19 + tv * 12
            if tl:   # leader line so a bumped label still reads as belonging to its dot
                p.append(f'<line class="lead" x1="{px_:.1f}" y1="{y-7}" x2="{px_:.1f}" y2="{ly+3}"/>')
            if tv:
                p.append(f'<line class="lead" x1="{px_:.1f}" y1="{y+7}" x2="{px_:.1f}" y2="{vy-8}"/>')
            p.append(f'<circle class="mdot" cx="{px_:.1f}" cy="{y}" r="5"/>')
            p.append(f'<text class="mlab" x="{px_:.1f}" y="{ly}" text-anchor="middle">{name}</text>')
            p.append(f'<text class="mval" x="{px_:.1f}" y="{vy}" text-anchor="middle">{v}</text>')

        c = consensus(nd)
        if c is not None:
            cx = c[0]
            p.append(f'<path class="nws" d="M{x(cx):.1f},{y-9} L{x(cx)+6:.1f},{y} '
                     f'L{x(cx):.1f},{y+9} L{x(cx)-6:.1f},{y} Z"/>')
        spread = hi - lo
        verd = ("agree" if spread < 20 else
                "some spread" if spread < NO_CONSENSUS else "no consensus")
        cls = "good" if spread < 20 else "warn" if spread < NO_CONSENSUS else "bad"
        p.append(f'<text class="spread {cls}" x="{W-112}" y="{y-2}">±{spread}</text>')
        p.append(f'<text class="spreadlab {cls}" x="{W-112}" y="{y+12}">{verd}</text>')
    p.append("</svg>")
    return "\n".join(p)


def sat_strip(sat):
    """Last 24 h of satellite cloud over the site, hour by hour, night included.

    The webcam filmstrip below this stops at dusk. This does not — which is the entire
    reason it exists, because the trip happens after dusk.
    """
    if not sat:
        return ('<p class="note">No satellite readings yet. '
                '<span class="mono">satellite.py</span> fills this hourly.</p>')
    rows = sat[-24:]
    cell, gap, lab = 26, 2, 46
    W = len(rows) * (cell + gap) + lab + 14
    H = 74
    p = [f'<svg viewBox="0 0 {W} {H}" role="img" '
         f'aria-label="Satellite cloud over the site, last {len(rows)} hours">']
    p.append(f'<text class="srclab" x="{lab-6}" y="27" text-anchor="end">GOES</text>')
    p.append(f'<text class="srclab" x="{lab-6}" y="46" text-anchor="end">night</text>')
    for i, e in enumerate(rows):
        t = datetime.fromisoformat(e["time"])
        x = lab + i * (cell + gap)
        v = e.get("cloud")
        if v is None:
            p.append(f'<rect class="nodata" x="{x}" y="14" width="{cell}" height="14" rx="2"/>')
        else:
            p.append(f'<rect class="cloud" x="{x}" y="14" width="{cell}" height="14" rx="2" '
                     f'style="opacity:{max(v,0)/100:.2f}"><title>{t:%a %H:%M} — {v}% cloud'
                     f'</title></rect>')
            p.append(f'<rect class="cellb" x="{x}" y="14" width="{cell}" height="14" rx="2"/>')
        dark = sun_alt(t, *SITE[1:3]) < -18
        p.append(f'<rect class="{"nightbar" if dark else "daybar"}" x="{x}" y="33" '
                 f'width="{cell}" height="5" rx="2"/>')
        if i % 3 == 0:
            p.append(f'<text class="hlab" x="{x + cell/2:.0f}" y="52" '
                     f'text-anchor="middle">{t:%H}</text>')
    p.append(f'<text class="hlab" x="{lab}" y="68">'
             f'{datetime.fromisoformat(rows[0]["time"]):%a %d %b} → '
             f'{datetime.fromisoformat(rows[-1]["time"]):%a %d %b}, '
             f'darker = more cloud · bar under each hour marks astronomical dark</text>')
    p.append("</svg>")
    return "".join(p)


def sky_now(sat):
    """Where the cloud actually is right now, not just how much of it there is.

    The southern slot is the only part of the sky the core programme uses, so a dome
    percentage can be badly misleading in both directions — 54% overall has already meant
    a clear north and a socked-in south on this site. The upwind figure is what the flow
    is carrying toward you, and it has led the overhead reading by about an hour.
    """
    if not sat:
        return ""
    e = sat[-1]
    slot, oct_ = e.get("slot") or {}, e.get("octants") or {}
    if not slot and not oct_:
        return ""
    t = datetime.fromisoformat(e["scan"])

    def band(v):
        return "dim" if v is None else "good" if v <= GO else "warn" if v <= 55 else "bad"

    near, mid, far = slot.get("near"), slot.get("mid"), slot.get("far")
    verdict = ""
    if near is not None:
        if near <= GO and (far or 0) > 55:
            verdict = "clear overhead, cloud approaching from range"
        elif near > 55 and (far is not None and far <= GO):
            verdict = "blocked now, clearer air further out"
        elif near <= GO:
            verdict = "the southern slot is open"
        else:
            verdict = "the southern slot is blocked"

    ring = "".join(
        f'<div class="rk"><span class="rkl">{n}</span>'
        f'<span class="rkv {band(v)}">{"—" if v is None else str(v) + "%"}</span></div>'
        for n, v in (("0–9 km", near), ("9–25 km", mid), ("25–60 km", far)))

    # compass, north at top, drawn as a 3x3 with the site in the middle
    order = [("NW", 0), ("N", 1), ("NE", 2), ("W", 3), (None, 4), ("E", 5),
             ("SW", 6), ("S", 7), ("SE", 8)]
    cells = []
    for name, _ in order:
        if name is None:
            dv = e.get("cloud")
            df = 0 if dv is None else max(0, min(100, dv)) / 100
            cells.append(f'<div class="oc mid" style="--f:{df:.2f}">'
                         f'<span class="ocv {band(dv)}">{dv}%</span>'
                         f'<span class="ocl">dome</span></div>')
            continue
        v = oct_.get(name)
        hot = " slot" if name in ("S", "SW") else ""
        f = 0 if v is None else max(0, min(100, v)) / 100
        cells.append(f'<div class="oc{hot}" style="--f:{f:.2f}">'
                     f'<span class="ocv {band(v)}">'
                     f'{"—" if v is None else v}</span><span class="ocl">{name}</span></div>')

    up = e.get("upwind")
    wb = e.get("wind_from")
    upline = ("" if up is None else
              f'<p class="note"><b class="{band(up)}">{up}% cloud upwind</b> — 30–90 km out '
              f'on the {int(wb)}° flow, which is roughly what arrives overhead in the next '
              f'hour.</p>')
    return (f'<div class="card" style="margin-bottom:.8rem">'
            f'<span class="eyebrow">Where the cloud is · {t:%a %H:%M}</span>'
            f'<p class="lede" style="margin-top:.3rem">Your whole southern programme lives '
            f'between azimuth 177° and 232°. <b>{verdict}</b></p>'
            f'<div class="rings">{ring}</div>'
            f'<div class="compass">{"".join(cells)}</div>'
            f'{upline}'
            f'<p class="note">Left: cloud in the southern slot by distance — near cloud '
            f'blocks low altitudes, far cloud blocks the cirrus band. Right: cloud by '
            f'compass octant, south-west highlighted because that is where the core sits.</p>'
            f'</div>')


def compass_film(sat):
    """The compass again, but as a timeline you can scrub — 12 h behind, 12 h ahead.

    The static panel above answers "is the slot open now". This answers "is it opening or
    closing", which is the question at 9 PM with the car still packed. Past frames are
    satellite observation; future frames are HRRR, which at 3 km is the only model here
    that can resolve a 14 km offset — the coarser globals return eight nearly identical
    octants, a blur rather than a direction.
    """
    past = [e for e in (sat or []) if e.get("octants")][-12:]
    if FCST_OVERRIDE is not None:
        future = FCST_OVERRIDE
    else:
        try:
            import satellite as satmod
            future = satmod.octant_forecast(12)
        except Exception:
            future = []
    frames = [{"time": e["time"], "octants": e["octants"], "cloud": e.get("cloud"),
               "kind": "observed"} for e in past] + future
    if len(frames) < 2:
        return ""
    now_i = max(0, len(past) - 1)
    payload = json.dumps(frames).replace("</", "<\\/")
    cells = "".join(
        f'<div class="oc{" slot" if n in ("S", "SW") else ""}" data-oct="{n}">'
        f'<span class="ocv">—</span><span class="ocl">{n}</span></div>'
        if n else '<div class="oc mid" data-oct="dome"><span class="ocv">—</span>'
                  '<span class="ocl">dome</span></div>'
        for n in ("NW", "N", "NE", "W", None, "E", "SW", "S", "SE"))
    return (f'<div class="card" style="margin-bottom:.8rem">'
            f'<span class="eyebrow">Is it opening or closing?</span>'
            f'<div class="filmhead"><b id="cfTime">—</b>'
            f'<span id="cfKind" class="cfkind">—</span></div>'
            f'<div class="compass" id="cfGrid">{cells}</div>'
            f'<div class="cfctl">'
            f'<button class="btn" id="cfPlay" aria-label="Play or pause">▶ Play</button>'
            f'<input type="range" id="cfSlide" min="0" max="{len(frames)-1}" '
            f'value="{now_i}" aria-label="Time">'
            f'</div>'
            f'<div class="cftrack" id="cfTrack"></div>'
            f'<p class="note">Left of the marker is what the satellite saw; right of it is '
            f'HRRR. Watch south-west — that is the core. Cloud arriving there before it '
            f'arrives overhead is your warning.</p>'
            f'<script id="cfData" type="application/json">{payload}</script>'
            f'</div>')


def _skill():
    """Cached climatology and lead-time skill, or {}. Written by skill.py, daily."""
    try:
        return json.load(open("skill.json"))
    except Exception:
        return {}


def base_rate_line(sk, latest):
    """One sentence putting the trip odds against thirty years of the same dates.

    Every other number on this page is absolute, which makes 84% unreadable — good or bad
    depends entirely on what a normal year looks like here, and a normal year is 72% cloud
    with two nights in three unusable.
    """
    c = (sk or {}).get("climatology")
    t = (latest or {}).get("trip")
    if not c:
        return ""
    base = c["p_trip_good"]
    if not t:
        return (f'<p class="note">For reference, {c["window"]} at this site over '
                f'{c["years"]} years: median <b>{c["median"]}%</b> cloud in the core window, '
                f'and <b>{base}%</b> of years gave at least one usable night.</p>')
    j = t["joint"]
    d = j - base
    cls = "good" if d >= 8 else "bad" if d <= -8 else "warn"
    word = ("better than a normal year" if d >= 8 else
            "worse than a normal year" if d <= -8 else "about a normal year")
    return (f'<p class="baserate"><b class="{cls}">{word}</b> — {j}% against a '
            f'<b>{base}%</b> base rate for {c["window"]} here, measured over {c["years"]} '
            f'years. A typical year at this site is <b>{c["median"]}%</b> cloud in the core '
            f'window, and only <b>{c["p_night_good"]}%</b> of individual nights beat '
            f'{GO}%.</p>')


def waiting_section(sk):
    """Does another day of waiting actually buy a better forecast? Measured, not assumed."""
    ls = (sk or {}).get("lead_skill")
    if not ls or not ls.get("by_lead"):
        return ""
    bl = ls["by_lead"]
    leads = sorted(bl, key=int)
    mx = max(bl[k]["mean"] for k in leads) or 1
    bars = []
    for k in leads:
        m = bl[k]["mean"]
        w = 100 * m / mx
        cls = "bad" if m >= 30 else "warn" if m >= 22 else "good"
        bars.append(f'<div class="lk"><span class="lkl">{k} d</span>'
                    f'<span class="lkbar"><i class="{cls}" style="width:{w:.0f}%"></i></span>'
                    f'<span class="lkv">{m:.0f}</span></div>')
    e7 = bl.get("7", {}).get("mean")
    e3 = bl.get("3", {}).get("mean")
    e0 = bl.get("0", {}).get("mean")
    verdict = ""
    if None not in (e7, e3, e0):
        verdict = (f'<p>Waiting from seven days out to three gains '
                   f'<b>{e7 - e3:.0f} points</b> of accuracy. Waiting from three days to '
                   f'the night itself gains <b>{e3 - e0:.0f}</b>. The information arrives '
                   f'early and then stops — there is no eleventh-hour clarity to hold out '
                   f'for.</p>')

    bm = ls.get("by_model") or {}
    rows = []
    for name in sorted(bm, key=lambda n: bm[n].get("0", 99)):
        d = bm[name]
        near = [d[k] for k in ("0", "1", "2") if k in d]
        far = [d[k] for k in ("5", "6", "7") if k in d]
        n_, f_ = (sum(near) / len(near) if near else None), (sum(far) / len(far) if far else None)
        rows.append(f'<tr class="mrow"><td><b>{name}</b></td>'
                    f'<td class="n">{"—" if n_ is None else f"{n_:.0f}"}</td>'
                    f'<td class="n">{"—" if f_ is None else f"{f_:.0f}"}</td></tr>')
    table = ('<table class="mtable"><thead><tr><th>Model</th>'
             '<th>Error 0–2 d</th><th>Error 5–7 d</th></tr></thead><tbody>'
             + "".join(rows) + '</tbody></table>')
    return (f'<h2>Does waiting help?</h2>\n<div class="card">'
            f'<p class="lede">Mean error against the satellite, by how far ahead the '
            f'forecast was made. {ls["n_hours"]} verified night hours.</p>'
            f'<div class="lks">{bars and "".join(bars)}</div>'
            f'{verdict}'
            f'<p class="note">Typical error is far lower than the mean — the median at '
            f'three days is {bl.get("3", {}).get("median", "—")} points. The mean is pulled '
            f'up by occasional total misses, which is where the risk lives: when the models '
            f'agree they are usually right, and when they split the tail is announcing '
            f'itself.</p>'
            f'<h3 class="sub">Which model, at which range</h3>'
            f'<div class="scroll">{table}</div>'
            f'<p class="note">Lower is better. Measured at this site against satellite '
            f'observation, so it reflects this terrain rather than a global scorecard.</p>'
            f'</div>')


def webcam_section(log=None):
    """Live view, an hourly filmstrip with the forecast above each frame, and a scoreboard.

    The filmstrip is the point: scroll it and you can see what a given forecast number
    actually looked like out of the window.
    """
    if log is None:
        if not os.path.exists("webcam_log.json"):
            return ""
        log = json.load(open("webcam_log.json"))
    satby = {e["time"][:13]: e.get("cloud") for e in _satlog()}

    # Bright enough to score is not the same as trustworthy. Near sunrise and sunset the
    # whole sky reddens and the R/B test reads clear air as overcast — caught live at
    # 19:41 on 4 Aug, when the camera said 40% while the satellite and every model said 0.
    # Same SUN_MIN gate the calibration column already applies.
    day = [e for e in log if not e["night"] and e["cloud"] is not None
           and sun_alt(datetime.fromisoformat(e["time"]), *WEBCAM_SITE) >= SUN_MIN]
    if not day:
        return ""

    # scoreboard: mean absolute error per model
    # Score against the satellite where possible: it covers the night, which is the whole
    # point. Daylight webcam frames still count, but they were never the hours that matter.
    scored = [e for e in _satlog() if e.get("cloud") is not None and e.get("models")] + \
             [e for e in day if e.get("models")]
    errs = {}
    for e in scored:
        for m, v in (e.get("models") or {}).items():
            errs.setdefault(m, []).append(abs(v - e["cloud"]))
    # A ranking needs enough checks AND enough variety to mean anything. Three consecutive
    # clear frames give every model a near-perfect score and rank pure noise, so the table
    # shows n from the start but only claims a winner once there is something to separate.
    n_obs = len(scored)
    spread_obs = ((max(e["cloud"] for e in scored) - min(e["cloud"] for e in scored))
                  if scored else 0)
    trustworthy = n_obs >= SCORE_MIN_N and spread_obs >= SCORE_MIN_SPREAD
    score = ""
    if any(len(v) >= 2 for v in errs.values()):
        rows = "".join(
            f"<tr><td>{m}</td><td class='n'>{len(v)}</td>"
            f"<td class='n {'good' if sum(v)/len(v) < 12 else 'warn' if sum(v)/len(v) < 25 else 'bad'}'>"
            f"{sum(v)/len(v):.0f} pts</td></tr>"
            for m, v in sorted(errs.items(), key=lambda kv: sum(kv[1]) / len(kv[1])))
        verdict = ('<p class="note">Lowest = believe that one.</p>' if trustworthy else
                   f'<p class="note"><b>Not yet a ranking.</b> {n_obs} scored frame'
                   f'{"s" if n_obs != 1 else ""} spanning {spread_obs} points of cloud — '
                   f'a winner needs at least {SCORE_MIN_N} frames across '
                   f'{SCORE_MIN_SPREAD} points. Under a steady clear sky every model looks '
                   f'perfect and the order is noise.</p>')
        score = ('<div class="scroll" style="margin-top:1rem"><table><thead><tr>'
                 '<th>Model</th><th>Checks</th><th>Mean error vs camera</th></tr></thead><tbody>'
                 + rows + '</tbody></table></div>' + verdict)

    cells = []
    for e in reversed(log[-30:]):
        t = datetime.fromisoformat(e["time"])
        ms = e.get("models") or {}
        fc = (f'<span class="fc{" dim" if e["night"] else ""}">'
              f'{min(ms.values())}–{max(ms.values())}%</span>'
              if ms else '<span class="fc dim">—</span>')

        # The number under the photo is the SATELLITE, not the camera. The camera's red/blue
        # estimate is unusable at night and unreliable in low sun — it read 40% at 19:41 on
        # 4 Aug while the satellite and all eight models read 0 — so quoting it under every
        # frame was publishing a figure we had already decided not to trust. The satellite
        # has a verified number for every hour, dark included.
        sv = satby.get(e["time"][:13])
        if sv is None:
            obs = '<span class="obs dim">—</span>'
        else:
            if ms:
                d = abs(sv - sum(ms.values()) / len(ms))
                cl = "good" if d < 15 else "warn" if d < 30 else "bad"
            else:
                cl = ""
            obs = f'<span class="obs {cl}">{sv}%</span>'

        # the camera's own reading is kept as a second opinion, but only when the sun is
        # high enough for it to mean anything
        cam = ""
        if (e.get("cloud") is not None and not e["night"]
                and sun_alt(t, *WEBCAM_SITE) >= SUN_MIN):
            cam = f'<span class="cam">cam {e["cloud"]}%</span>'
        img = (f'<img src="{e["shot"]}" alt="webcam {t:%d %b %H:%M}" loading="lazy">'
               if os.path.exists(e["shot"]) else '<div class="noimg"></div>')
        cells.append(f'<figure class="shot"><span class="hr">{t:%a %H:%M}</span>'
                     f'{fc}{img}{obs}{cam}</figure>')

    return f'''
  <h2>Ground truth — satellite and webcam</h2>
  {sky_now(_satlog())}
  {compass_film(_satlog())}
  <div class="card" style="margin-bottom:.8rem">
    <p class="lede">What was actually overhead, hour by hour — <b>including after dark</b>,
    which the camera cannot see. This is what the models get marked against.</p>
    <div class="scroll" style="margin-top:.8rem">{sat_strip(_satlog())}</div>
  </div>
  <div class="card">
    <p class="lede">First Connecticut Lake, 16.7 km SSW of the site. Hourly frame, cloud estimated,
    compared against what each model said for that hour.</p>
    <div class="live"><iframe src="https://www.youtube.com/embed/wNxk-XC8Z5s"
      title="First Connecticut Lake live webcam" loading="lazy" allowfullscreen
      referrerpolicy="strict-origin-when-cross-origin"></iframe></div>
    <p class="note">Live — needs a connection. Frames below are archived.</p>
    {score}
    <h3 style="margin-top:1.4rem">Hour by hour, forecast above the photo</h3>
    <div class="film scroll">{"".join(cells)}</div>
    <p class="note">Above each photo, what the models forecast for that hour. Below it,
    what the <b>satellite</b> saw — <b class="good">within 15</b> /
    <b class="warn">30</b> / <b class="bad">beyond</b>. The camera's own estimate appears
    only where the sun was high enough for it to be trustworthy; at dusk a reddened sky
    reads as cloud, so those numbers are withheld rather than shown and disbelieved.</p>
  </div>
'''


def hourly_strips(latest):
    """Hour-by-hour cloud cover per night, per source. Structure, not averages.

    Opacity of the ink colour encodes cloud — transparent is clear sky, solid is
    overcast — so it reads identically in light, dark and night modes.
    """
    out = []
    for label, _ in NIGHTS:
        nd = latest["nights"][label]
        hrs = nd.get("hour_labels") or []
        mh = nd.get("models_hourly") or {}
        nws = {r["h"][:2]: r["sky"] for r in (nd.get("rows") or [])}
        if not hrs:
            out.append(f'<div class="striprow"><b>{label}</b>'
                       f'<span class="dim">no hourly data</span></div>')
            continue
        d = datetime.strptime(nd["date"], "%Y-%m-%d")
        cell, gap, lab = 24, 2, 54          # cell width, gap, left label column
        rowh, ch = 19, 14                   # row pitch, cell height
        W = len(hrs) * (cell + gap) + lab + 20
        rows = [("NWS", [nws.get(h) for h in hrs])] + \
               [(k, v) for k, v in sorted(mh.items())]
        H = len(rows) * rowh + 28
        p = [f'<svg viewBox="0 0 {W} {H}" role="img" '
             f'aria-label="Hour by hour cloud cover for {label}">']
        # Both shooting windows, bracketed. They are separate because the targets are
        # separate: the Milky Way core is below the 10 degree treeline by 11:25 PM, so
        # the late hours are Perseids and the refractor, not the core.
        for hrset, name, cls in ((CORE_HR, "MW CORE", "corebox"),
                                 (LATE_HR, "PERSEIDS", "latebox")):
            ci = [i for i, h in enumerate(hrs) if int(h) in hrset]
            if not ci:
                continue
            x0 = lab + ci[0] * (cell + gap) - 1
            x1 = lab + (ci[-1] + 1) * (cell + gap) - gap + 1
            p.append(f'<rect class="{cls}" x="{x0}" y="10" width="{x1-x0}" '
                     f'height="{H-26}" rx="2"/>')
            p.append(f'<text class="corelab {cls}lab" x="{(x0+x1)/2:.0f}" y="7" '
                     f'text-anchor="middle">{name}</text>')
        for i, h in enumerate(hrs):
            p.append(f'<text class="hlab" x="{lab + i*(cell+gap) + cell/2:.0f}" y="{H-5}" '
                     f'text-anchor="middle">{h}</text>')
        for r, (name, vals) in enumerate(rows):
            y = 15 + r * rowh
            p.append(f'<text class="srclab" x="{lab-6}" y="{y+ch-3}" '
                     f'text-anchor="end">{name}</text>')
            for i, v in enumerate(vals):
                x = lab + i * (cell + gap)
                if v is None:
                    p.append(f'<rect class="nodata" x="{x}" y="{y}" width="{cell}" '
                             f'height="{ch}" rx="2"/>')
                    continue
                p.append(f'<rect class="cloud" x="{x}" y="{y}" width="{cell}" height="{ch}" '
                         f'rx="2" style="opacity:{max(v,0)/100:.2f}"/>')
                p.append(f'<rect class="cellb" x="{x}" y="{y}" width="{cell}" '
                         f'height="{ch}" rx="2"/>')
                p.append(f'<text class="cellv" x="{x+cell/2:.0f}" y="{y+ch-3}" '
                         f'text-anchor="middle">{v}</text>')
        p.append("</svg>")
        out.append(f'<div class="striprow"><div class="striphead"><b>{label}</b>'
                   f'<span class="dim">{d:%a %d %b}</span></div>{"".join(p)}</div>')
    return "".join(out)


def delta_table(hist):
    if len(hist) < 2:
        return ('<p class="note">Only one snapshot so far. The movement column fills in once a '
                'second forecast package lands — see the next-check time at the top.</p>')
    rows = []
    for label, _ in NIGHTS:
        vals = [(datetime.fromisoformat(e["taken"]), consensus(e["nights"][label])[0])
                for e in hist if consensus(e["nights"][label])]
        if not vals:
            rows.append(f"<tr><td>{label}</td><td colspan='4' class='dim'>no data yet</td></tr>")
            continue
        first, last = vals[0][1], vals[-1][1]
        d = last - first
        swing = max(v for _, v in vals) - min(v for _, v in vals)
        arrow = "→" if d == 0 else ("↑" if d > 0 else "↓")
        cls = "worse" if d > 5 else ("better" if d < -5 else "")
        seq = [consensus(e["nights"][label])[0] for e in hist
               if consensus(e["nights"].get(label, {}))]
        trail = "".join(
            f'<span class="{"bad" if b > a else "good" if b < a else "dim"}">'
            f'{"↑" if b > a else "↓" if b < a else "→"}</span>'
            for a, b in zip(seq, seq[1:])) or '<span class="dim">—</span>'
        sp0 = next((mrange(e["nights"][label]) for e in hist
                    if mrange(e["nights"][label])), None)
        spN = next((mrange(e["nights"][label]) for e in reversed(hist)
                    if mrange(e["nights"][label])), None)
        if spN:
            tight = "" if not sp0 else ("good" if spN[2] < sp0[2] - 5 else
                                        "bad" if spN[2] > sp0[2] + 5 else "")
            spcell = (f"<td class='n {tight}'>±{sp0[2]} → ±{spN[2]}</td>" if sp0
                      else f"<td class='n'>±{spN[2]}</td>")
        else:
            spcell = "<td class='n dim'>—</td>"
        rows.append(f"<tr><td>{label}</td><td class='n'>{first}%</td><td class='n'>{last}%</td>"
                    f"<td class='n {cls}'>{arrow} {abs(d)}</td>"
                    f"<td class='trail'>{trail}</td>"
                    f"<td class='n'>{swing}</td>{spcell}</tr>")
    return ("<table><thead><tr><th>Night</th><th>First</th><th>Latest</th>"
            "<th>Change</th><th>Each step</th><th>Range</th><th>Model spread</th>"
            "</tr></thead><tbody>"
            + "".join(rows) + "</tbody></table>")


OBS_WIN = (16, 10)   # hours searched for usable webcam frames bracketing a night
SUN_MIN = 15.0   # deg. Below this the R/B cloud test is not trustworthy — a low sun
                 # reddens the whole sky, so clear evening air reads as cloud.


def sun_alt(dt, lat, lon):
    """Solar elevation in degrees. NOAA low-precision algorithm, good to ~0.1 deg.

    Validated at WEBCAM_SITE (45.0958, -71.2600), which is where observed() uses it:
    computes sunset 20:03 and sunrise 05:39 EDT for 4 Aug 2026, against published values
    of about 20:05 and 05:30. Other coordinates give other times — the numbers above are
    not a general claim about the function.
    """
    import math
    u = dt.astimezone(timezone.utc)
    n = (u - datetime(2000, 1, 1, 12, tzinfo=timezone.utc)).total_seconds() / 86400.0
    L = (280.460 + 0.9856474 * n) % 360
    g = math.radians((357.528 + 0.9856003 * n) % 360)
    lam = math.radians(L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g))
    eps = math.radians(23.439 - 0.0000004 * n)
    ra = math.atan2(math.cos(eps) * math.sin(lam), math.cos(lam))
    dec = math.asin(math.sin(eps) * math.sin(lam))
    gmst = (18.697374558 + 24.06570982441908 * n) % 24
    H = math.radians((gmst * 15 + lon) % 360) - ra
    la = math.radians(lat)
    return math.degrees(math.asin(math.sin(la) * math.sin(dec) +
                                  math.cos(la) * math.cos(dec) * math.cos(H)))


def observed(day, wlog, sat=None):
    """What was actually overhead across the dark window for `day`.

    Satellite first. It measures the window itself — every hour of it, in the dark — so
    when it is available the webcam bracket is not used at all. The webcam path below
    remains for the hours before the satellite log existed.

    Returns (mean, n_hours, unusable, source).
    """
    if sat:
        nxt = (datetime.strptime(day, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        want = {f"{day}T{h:02d}" for h in range(DARK[0], 24)} | \
               {f"{nxt}T{h:02d}" for h in range(0, DARK[1] + 1)}
        v = [e["cloud"] for e in sat
             if e["time"][:13] in want and e.get("cloud") is not None]
        if v:
            return round(sum(v) / len(v)), len(v), 0, "satellite"
    return _observed_webcam(day, wlog)


def _observed_webcam(day, wlog):
    """Fallback: what the webcam saw either side of the dark window for `day`.

    Returns (mean, n_hours, night_hours) or None. The window is the same 6 PM-7 AM span
    the strips use, spilling into the following morning.

    Only daylight frames carry a cloud number today, so in practice this averages the
    dusk and dawn frames bracketing the night rather than the night itself — reported
    honestly as such. Nothing here needs changing if night detection is calibrated
    later; those hours simply start contributing.
    """
    if not wlog:
        return None
    nxt = (datetime.strptime(day, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    # Deliberately wider than DARK. Inside the dark window almost nothing clears the sun
    # test, so this reaches back into the afternoon and forward into the morning to catch
    # the last trustworthy look before dark and the first after dawn.
    want = {f"{day}T{h:02d}" for h in range(OBS_WIN[0], 24)} | \
           {f"{nxt}T{h:02d}" for h in range(0, OBS_WIN[1] + 1)}
    vals, unusable = [], 0
    for e in wlog:
        if e["time"][:13] not in want:
            continue
        if e.get("cloud") is None:
            unusable += 1
            continue
        # A frame can be bright enough to score and still be worthless: near sunrise and
        # sunset the sky itself is red, which drives R/B past the cloud threshold on
        # perfectly clear air. Drop those rather than believe them.
        if sun_alt(datetime.fromisoformat(e["time"]), *WEBCAM_SITE) < SUN_MIN:
            unusable += 1
            continue
        vals.append(e["cloud"])
    if not vals:
        return None
    return round(sum(vals) / len(vals)), len(vals), unusable, "webcam bracket"


def calibration(hist, wlog=None, sat=None):
    """How much has a night's forecast moved as its lead time shrank — and was it right?"""
    if len(hist) < 2:
        return ('<p class="note">Fills in over the next day or two, once these nights have been '
                'forecast more than once — then it shows how far a forecast actually travels '
                'between day 5 and day 1.</p>')
    rows, moves, misses = [], [], []
    for label, day in LEADUP:
        vals = [(e["nights"][label]["lead"], consensus(e["nights"][label])[0])
                for e in hist if consensus(e["nights"].get(label, {}))]
        if len(vals) < 2:
            continue
        d = datetime.strptime(day, "%Y-%m-%d")
        lo, hi = min(v for _, v in vals), max(v for _, v in vals)
        first, last = vals[0][1], vals[-1][1]
        moves.append(hi - lo)
        ob = observed(day, wlog, sat)
        if ob:
            om, n, dk, src = ob
            miss = last - om
            mcls = "good" if abs(miss) <= 10 else "warn" if abs(miss) <= 25 else "bad"
            obs_td = (f"<td class='n' title='{n} readings from {src}"
                      f"{f', {dk} unusable' if dk else ''}'>{om}%"
                      f"{'' if src == 'satellite' else '*'}</td>")
            miss_td = (f"<td class='n {mcls}'>{'+' if miss > 0 else ''}{miss}</td>")
            misses.append(abs(miss))
        else:
            obs_td = "<td class='n dim'>—</td>"
            miss_td = "<td class='n dim'>—</td>"
        rows.append(f"<tr><td>{d:%a %d %b}</td><td class='n'>{vals[0][0]}d → {vals[-1][0]}d</td>"
                    f"<td class='n'>{first}%</td><td class='n'>{last}%</td>"
                    f"<td class='n'>{hi-lo}</td>{obs_td}{miss_td}</tr>")
    if not rows:
        return ('<p class="note">Not enough readings yet for the lead-up nights to show '
                'movement — check back tomorrow.</p>')
    avg, mx = sum(moves) / len(moves), max(moves)
    return (f'<p style="margin-bottom:.8rem"><b style="color:var(--ink)">Worst swing so far: '
            f'{mx} points</b> (typical {avg:.0f}). You are asking how <em>wrong</em> a forecast '
            f'could be — a tail question — so the worst case is the honest number and the mean '
            f'understates it. A night reading 45% four days out could plausibly land anywhere '
            f'within ±{mx} of that.</p>'
            + (f'<p style="margin-bottom:.8rem">Against the webcam, the final forecast has '
               f'missed by <b style="color:var(--ink)">{sum(misses)/len(misses):.0f} points '
               f'on average</b>, worst {max(misses)}. Positive means it forecast more cloud '
               f'than showed up.</p>' if misses else
               '<p class="note" style="margin-bottom:.8rem">The observed column fills in the '
               'morning after each lead-up night, once the webcam has frames spanning it.</p>')
            + '<div class="scroll"><table><thead><tr><th>Night</th><th>Lead</th><th>First</th>'
            '<th>Latest</th><th>Swing</th><th>Observed</th><th>Miss</th></tr></thead><tbody>'
            + "".join(rows) + '</tbody></table></div>'
            + '<p class="note" style="margin-top:.8rem"><b>Observed</b> is the webcam at '
            'First Connecticut Lake, 16.7 km SSW of the shooting site. Cloud can only '
            'be scored while the sun is more than 15° up, so this is the last trustworthy look '
            'before dark and the first after dawn — a bracket around the night, not a '
            'measurement of it. '
            'Frames nearer sunset and sunrise are discarded: a low sun reddens the whole '
            'sky, and the red/blue test then reads clear air as overcast. Hover a value '
            'for the usable frame count.</p>')


WEBCAM_OVERRIDE = None      # preview_forecast.py sets this to render mock frames
SAT_OVERRIDE = None         # ...and this, for the satellite panels
FCST_OVERRIDE = None        # ...and this, for the forward half of the compass film


def _satlog():
    """Hourly satellite cloud over the site. Empty list if it has not run yet."""
    if SAT_OVERRIDE is not None:
        return SAT_OVERRIDE
    try:
        return json.load(open("satellite_log.json"))
    except Exception:
        return []


def _wlog():
    """The webcam log, or an empty list if it has not been written yet."""
    try:
        return json.load(open("webcam_log.json"))
    except Exception:
        return []



# Who runs each model, what it is good for, and where it lets you down. Ordered by how
# much weight it deserves for THIS question — night cloud over a valley in northern NH.
MODEL_NOTES = [
 ("ECMWF", "ECMWF · Europe", "9 km",
  "Highest medium-range skill of any global model in general, and measured here it is the "
  "best of the set inside two days. Its long-range advantage does not survive verification "
  "at this site — see \"Does waiting help?\" — so weight it near, not far.",
  "Too coarse to resolve a valley; known to overdo low stratus in moist northwest flow."),
 ("HRRR", "NOAA · US", "3 km",
  "Convection-allowing and terrain-resolving — the only model here that can see your "
  "valley instead of averaging it away. Once it reaches your night, believe it over "
  "everything else.",
  "48 h ceiling. It will not cover 11 Aug until about 9 Aug — after your 8 Aug decision."),
 ("UKMO", "Met Office · UK", "10 km",
  "Usually second only to ECMWF on verification scores.",
  "About 7 days on the free tier, so it arrives late in the argument."),
 ("GEM", "Environment Canada", "15 km",
  "Your weather arrives from Quebec, and this is the model whose home turf sits upstream "
  "of you.",
  "Open-Meteo's run metadata for it has been unmaintained for months, so its vintage "
  "reads as unknown even though the forecast is current."),
 ("ICON", "DWD · Germany", "13 km",
  "Skill comparable to GFS or better at short range.",
  "180 h ceiling — silent on the trip nights until roughly 7 Aug."),
 ("AIFS", "ECMWF · Europe", "31 km",
  "Machine-learning model trained on ERA5 reanalysis. It fails differently from the "
  "physics models, which is the entire reason it earns a vote — and measured against "
  "satellite at this site it is the most accurate source beyond five days, ahead of "
  "ECMWF.",
  "Smooths extremes — a genuinely clear or genuinely socked-in night gets pulled toward "
  "the middle."),
 ("GFS", "NOAA · US", "13 km",
  "Updates four times a day out to 16 days, so it is the first to show a pattern change.",
  "Run-to-run volatility is real. One GFS swing is not news; three in a row is."),
 ("JMA", "Japan Met Agency", "20 km",
  "A genuinely independent forecast system, which is worth something in an ensemble.",
  "Least tuned for North America. A tiebreaker, not a lead."),
 ("NWS", "US forecaster-edited blend", "2.5 km grid",
  "A human has adjusted a model blend for local effects — worth real weight inside 3 days.",
  "Built largely on GFS and the NBM, so it is not independent of GFS. Stops at 7 days."),
]


def model_notes(latest):
    """Reference table for the sources, marked with who is actually contributing today."""
    live = set()
    for label, _ in NIGHTS:
        live |= set(members(latest["nights"][label]))
    rows = []
    for name, who, grid, good, bad in MODEL_NOTES:
        inplay = name in live
        tag = ('<span class="pill on">in play</span>' if inplay
               else '<span class="pill off">out of range</span>')
        # Two rows per source: the identity line, then the prose spanning the full width.
        # Prose in its own column forces a horizontal scrollbar on a phone.
        rows.append(
            f'<tr class="mrow"><td><b>{name}</b> '
            f'<span class="dim">{who}</span></td>'
            f'<td class="n">{grid}</td><td class="r">{tag}</td></tr>'
            f'<tr class="mdesc"><td colspan="3">{good}'
            f'<div class="wf">Watch for: {bad}</div></td></tr>')
    return ('<table class="mtable"><tbody>' + "".join(rows) + '</tbody></table>')

def trip_banner(latest):
    """The decision, not the forecast: odds that at least one night gives you the core."""
    t = latest.get("trip")
    if not t:
        return ('<div class="card"><p class="note">Trip odds unavailable — the GEFS '
                'ensemble did not answer on the last run.</p></div>')
    j = t["joint"]
    cls = "good" if j >= 70 else "warn" if j >= 45 else "bad"
    verdict = ("worth the drive" if j >= 70 else
               "a real gamble" if j >= 45 else "probably not worth it")
    src = t.get("sources") or {}
    srctxt = ", ".join(f"{k} {v}" for k, v in sorted(src.items())) or f'{t["n"]} members'
    corr, ind, floor = t.get("corr"), t.get("indep"), t.get("floor")
    diag = (f'<p class="note">Counted across <b>{t["n"]}</b> ensemble members '
            f'({srctxt}). Each member is one physically consistent scenario spanning all '
            f'three nights. You do not need a particular night — you need one of them.</p>')
    if corr is not None and ind is not None:
        near = abs(j - ind) <= 4
        diag += (f'<p class="note"><b>How much do the nights move together?</b> Measured '
                 f'correlation between members is <b>{corr:+.2f}</b>, so the nights are '
                 f'behaving almost independently and this figure sits '
                 f'{"right on" if near else "away from"} the independence bound of '
                 f'{ind}%. That is worth stating because it could be an artefact of the '
                 f'ensemble spreading out at long range — except thirty years of real '
                 f'Augusts here give a correlation of +0.04 and a joint one point off '
                 f'their own independence bound. These dates genuinely are near-independent; '
                 f'three days is long enough for a system to pass. If the nights were '
                 f'locked together the answer would be <b>{floor}%</b> instead.</p>')
    bars = []
    for label, _ in NIGHTS:
        v = t["per"].get(label, 0)
        c = "good" if v >= 50 else "warn" if v >= 25 else "bad"
        bars.append(f'<div class="pk"><span class="pkl">{label}</span>'
                    f'<span class="pkbar"><i class="{c}" style="width:{v}%"></i></span>'
                    f'<span class="pkv {c}">{v}%</span></div>')
    return (f'<div class="card trip">'
            f'<span class="eyebrow">The actual question</span>'
            f'<div class="tripbig {cls}">{j}%</div>'
            f'<p class="tripsub"><b>chance at least one of the three nights has a usable '
            f'core window</b> — {verdict}.</p>'
            f'<div class="pks">{"".join(bars)}</div>'
            f'{diag}'
            f'</div>')


def write_page(hist):
    latest = hist[-1]
    t = datetime.fromisoformat(latest["taken"])
    issued = (datetime.fromisoformat(latest["issued"]).astimezone(EDT).strftime("%a %d %b %H:%M")
              if latest.get("issued") else "unknown")
    rr = latest.get("runs") or {}

    # what lands next, and when. The hourly check is certain; model refreshes are
    # projected from the last publish time — these models run on a 6-hourly cycle.
    now = datetime.now(EDT)
    nxt_check = (now.replace(minute=5, second=0, microsecond=0)
                 + timedelta(hours=1 if now.minute >= 5 else 0))
    mins = int((nxt_check - now).total_seconds() // 60)
    upcoming = []
    for n, v in sorted(rr.items()):
        if len(v) < 3:
            continue
        nt = datetime.fromtimestamp(v[2], timezone.utc).astimezone(EDT)
        while nt <= now:
            nt += timedelta(hours=6)
        upcoming.append((nt, n))
    upcoming.sort()
    nextmodels = " · ".join(f"{u:%H:%M} {n}" for u, n in upcoming[:3])
    # The countdown must be computed in the browser — baked into the HTML it starts
    # decaying the moment the page is built. data-cron-min is the cron minute (:05).
    nextline = (f'<div class="next" data-cron-min="5">'
                f'<span id="nextcheck"><b>Next check {nxt_check:%H:%M}</b> '
                f'<span class="dim">— in {mins} min, then hourly</span></span>'
                + (f'<span class="dim"> · next model data: {nextmodels}</span>'
                   if nextmodels else "") + '</div>')
    vint = [("Page built", f"{t:%a %d %b %Y, %H:%M} EDT"),
            ("NWS package", f"issued {issued} EDT")]
    for n, (i, a, *_) in sorted(rr.items()):
        vint.append((n, f"{i} run · published {a}"))
    # Any model whose metadata feed is stale or missing — GEM's has been unmaintained for
    # months — still forecasts fine; only its run time is unknown. Say so rather than
    # omitting it, so a source never silently disappears from the vintage list.
    if rr:
        for _, n in OM_MODELS:
            if n not in rr:
                vint.append((n, "run time unknown"))
    runline = "".join(f'<div class="vk">{k}</div><div class="vv">{v}</div>' for k, v in vint)

    # Which sources actually reach the trip nights. A model that is merely short-range
    # would otherwise look like a broken feed — ICON only runs 180 h, so it cannot see
    # 11 Aug until roughly 7 Aug, and NWS gridpoint stops at 7 days.
    inm, allm = set(), {n for _, n in OM_MODELS} | {"NWS"}
    for label, _ in NIGHTS:
        inm |= set(members(latest["nights"][label]))
    missing = sorted(allm - inm)
    srcnote = (f'Median of <b>{", ".join(sorted(inm))}</b>, weighted equally. '
               f'The number under each night is the middle opinion, not an average — '
               f'one model going rogue moves the range, not the verdict.')
    if missing:
        srcnote += (f' <b>{", ".join(missing)}</b> '
                    f'{"do" if len(missing) > 1 else "does"} not forecast this far out yet '
                    f'and will join nearer the date.')

    cards = []
    for si, (label, _) in enumerate(NIGHTS):
        nd = latest["nights"][label]
        d = datetime.strptime(nd["date"], "%Y-%m-%d")
        cons = consensus(nd)
        v = cons[0] if cons else None
        # The verdict is gated on agreement, not just the median. A 30% median drawn from
        # sources spanning 4-82% is not a GO - it is one model's opinion winning a vote,
        # and calling it GO is exactly the overconfidence this page exists to prevent.
        spread = cons[3] if cons else None
        if v is None:
            verdict, vc = "no data", "dim"
        elif spread is not None and spread >= NO_CONSENSUS:
            verdict = f"UNRESOLVED · sources span {cons[1]}–{cons[2]}%"
            vc = "warn" if v <= 55 else "bad"
        else:
            verdict = "GO" if v <= GO else "marginal" if v <= 55 else "poor"
            vc = "good" if v <= GO else "warn" if v <= 55 else "bad"
        prev = next((consensus(h["nights"][label])[0] for h in reversed(hist[:-1])
                     if consensus(h["nights"].get(label, {}))), None)
        if v is not None and prev is not None and v != prev:
            dv = v - prev
            step = (f'<span class="step {"bad" if dv > 0 else "good"}">'
                    f'{"↑" if dv > 0 else "↓"}{abs(dv)} since last</span>')
        elif v is not None and prev == v:
            step = '<span class="step dim">→ no change</span>'
        else:
            step = ''
        cb, cbh = best_hour(nd, CORE_HR)
        lb, lbh = best_hour(nd, LATE_HR)
        lcons = consensus(nd, late=True)
        lt = lcons[0] if lcons else None
        ltxt = ("—" if lt is None else f"{lt}%")
        lrange = (f" · sources {lcons[1]}–{lcons[2]}%" if lcons else "")
        if cons:
            _, lo, hi, sp, k = cons
            scls = "good" if sp < 20 else "warn" if sp < 40 else "bad"
            src = ", ".join(sorted(members(nd)))
            mline = (f'<span class="mrange" title="{src}">{k} sources <b>{lo}–{hi}%</b> '
                     f'<span class="{scls}">±{sp}</span></span>')
        else:
            mline = '<span class="mrange dim">no data</span>'
        cd = (latest.get("cond") or {}).get(label) or {}
        warn = []
        if cd.get("fog_hours"):
            warn.append(f'<span class="bad">fog risk {cd["fog_hours"]}h</span> '
                        f'<span class="dim">({cd["spread"]}°C spread, {cd["wind"]} km/h)</span>')
        elif cd.get("spread") is not None:
            warn.append(f'<span class="good">no fog signal</span> '
                        f'<span class="dim">({cd["spread"]}°C, {cd["wind"]} km/h)</span>')
        if cd.get("aod") is not None:
            ac = "bad" if cd["aod"] >= AOD_HAZY else "good"
            warn.append(f'<span class="{ac}">haze {cd["aod"]}</span>')
        fogline = (f'<span class="mrange">{" · ".join(warn)}</span>' if warn else
                   '<span class="mrange dim">fog and haze: no data this far out</span>')
        cards.append(
            f'<div class="ncard"><span class="swatch s{si}"></span>'
            f'<b>{label}</b><span class="dim">{d:%a %d %b} · lead {nd["lead"]}d</span>'
            f'<span class="big {vc}">{"—" if v is None else str(v)+"%"}</span>'
            f'<span class="verdict {vc}">{cons[4] if cons else 0}-source median · '
            f'{verdict}{step}</span>'
            f'<span class="mrange">best hour '
            f'<b>{"—" if cb is None else hr12(cbh) + " · " + str(cb) + "%"}</b>'
            f'{"" if cb is None else " · " + ("shootable" if cb <= GO else "no clear hour")}</span>'
            f'{mline}'
            f'<span class="mrange">1–4 AM <b>{ltxt}</b>'
            f'{"" if lb is None else f" · best {hr12(lbh)} {lb}%"}{lrange}</span>'
            f'{fogline}</div>')

    def band(v):
        return "good" if v <= GO else "warn" if v <= 55 else "bad"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Forecast trend · Pittsburg Aug 11–14</title>
<meta name="color-scheme" content="dark light">
<style>
:root{{
  --ground:#F1F3F7; --surface:#FFFFFF; --ink:#171C26; --body:#3B4453; --muted:#6C7789;
  --rule:#D3D9E4; --accent:#B5721A; --good:#2E6B4F; --warn:#B5721A; --bad:#B03A2C;
  --band:rgba(46,107,79,.09); --sband:rgba(181,114,26,.10);
  --s0:#2a78d6; --s1:#eb6834; --s2:#1baf7a;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --mono:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,monospace;
  --serif:ui-serif,"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
}}
@media (prefers-color-scheme:dark){{:root{{
  --ground:#0A0D14; --surface:#121722; --ink:#E7ECF5; --body:#BAC4D4; --muted:#7A8698;
  --rule:#232B39; --accent:#E3A445; --good:#6FBF95; --warn:#E3A445; --bad:#E8705C;
  --band:rgba(111,191,149,.10); --sband:rgba(181,114,26,.10);
  --s0:#3987e5; --s1:#d95926; --s2:#199e70;
}}}}
:root[data-theme="light"]{{
  --ground:#F1F3F7; --surface:#FFFFFF; --ink:#171C26; --body:#3B4453; --muted:#6C7789;
  --rule:#D3D9E4; --accent:#B5721A; --good:#2E6B4F; --warn:#B5721A; --bad:#B03A2C;
  --band:rgba(46,107,79,.09); --sband:rgba(181,114,26,.10); --s0:#2a78d6; --s1:#eb6834; --s2:#1baf7a;
}}
:root[data-theme="dark"]{{
  --ground:#0A0D14; --surface:#121722; --ink:#E7ECF5; --body:#BAC4D4; --muted:#7A8698;
  --rule:#232B39; --accent:#E3A445; --good:#6FBF95; --warn:#E3A445; --bad:#E8705C;
  --band:rgba(111,191,149,.10); --sband:rgba(181,114,26,.10); --s0:#3987e5; --s1:#d95926; --s2:#199e70;
}}
:root[data-night="on"]{{
  --ground:#000; --surface:#0A0000; --ink:#FF4A22; --body:#C8351A; --muted:#7E2210;
  --rule:#3A0F06; --accent:#FF6A34; --good:#FF6A34; --warn:#C8351A; --bad:#7E2210;
  --band:rgba(255,106,52,.10); --sband:rgba(181,114,26,.10);
  --s0:#FF6A34; --s1:#FF6A34; --s2:#FF6A34;
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--ground);color:var(--body);font-family:var(--sans);
  line-height:1.6;padding-bottom:3rem}}
.wrap{{max-width:50rem;margin:0 auto;padding:0 clamp(1rem,3.5vw,1.6rem)}}
h1{{font-family:var(--serif);color:var(--ink);font-size:clamp(1.5rem,5vw,2rem);
  margin:2rem 0 .3rem;line-height:1.15}}
h2{{font-family:var(--serif);color:var(--ink);font-size:1.15rem;margin:2.2rem 0 .8rem}}
.bar{{position:sticky;top:0;z-index:9;background:var(--ground);border-bottom:1px solid var(--rule)}}
.bar-in{{max-width:50rem;margin:0 auto;padding:.5rem clamp(1rem,3.5vw,1.6rem);
  display:flex;gap:.5rem;align-items:center}}
.bar a{{font-family:var(--mono);font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted);text-decoration:none;margin-right:auto}}
.bar a:hover{{color:var(--accent)}}
.btn{{font-family:var(--mono);font-size:.66rem;letter-spacing:.1em;text-transform:uppercase;
  background:transparent;color:var(--body);border:1px solid var(--rule);padding:.4rem .65rem;
  border-radius:3px;cursor:pointer}}
.btn:hover{{border-color:var(--accent);color:var(--accent)}}
.eyebrow{{font-family:var(--mono);font-size:.68rem;letter-spacing:.16em;text-transform:uppercase;
  color:var(--muted)}}
.card{{background:var(--surface);border:1px solid var(--rule);border-radius:4px;padding:1.1rem}}
.cards{{display:grid;gap:.7rem;grid-template-columns:1fr;margin:1rem 0}}
@media(min-width:36rem){{.cards{{grid-template-columns:repeat(3,1fr)}}}}
.ncard{{background:var(--surface);border:1px solid var(--rule);border-radius:4px;padding:.8rem;
  display:flex;flex-direction:column;gap:.15rem}}
.ncard b{{color:var(--ink)}}
.swatch{{width:26px;height:3px;border-radius:2px;display:block;margin-bottom:.35rem}}
.swatch.s0{{background:var(--s0)}} .swatch.s1{{background:var(--s1)}} .swatch.s2{{background:var(--s2)}}
.big{{font-family:var(--mono);font-size:1.7rem;line-height:1.1;margin-top:.3rem;
  font-variant-numeric:tabular-nums}}
.verdict{{font-family:var(--mono);font-size:.66rem;letter-spacing:.12em;text-transform:uppercase}}
h3.sub{{font-family:var(--serif);color:var(--ink);font-size:1rem;margin:1.8rem 0 .5rem}}
.trip{{margin:1.2rem 0 .6rem}}
.tripbig{{font-family:var(--mono);font-size:clamp(2.6rem,11vw,3.6rem);line-height:1;
  font-variant-numeric:tabular-nums;margin:.2rem 0 .1rem}}
.tripsub{{margin:.1rem 0 .9rem;color:var(--body)}}
.pks{{display:flex;flex-direction:column;gap:.3rem;margin-bottom:.7rem}}
.pk{{display:grid;grid-template-columns:5.2rem 1fr 2.6rem;align-items:center;gap:.5rem;
  font-family:var(--mono);font-size:.72rem}}
.pkl{{color:var(--muted)}}
.pkbar{{background:var(--rule);border-radius:2px;height:6px;overflow:hidden}}
.pkbar i{{display:block;height:100%;border-radius:2px}}
.pkbar i.good{{background:var(--good)}} .pkbar i.warn{{background:var(--warn)}}
.pkbar i.bad{{background:var(--bad)}}
.pkv{{text-align:right;font-variant-numeric:tabular-nums}}
.mtable{{width:100%;table-layout:auto}}
.mtable td{{vertical-align:baseline;border:0;padding:.35rem .5rem .1rem 0;white-space:normal;overflow-wrap:anywhere}}
.mtable tr.mrow td{{padding-top:.9rem;border-top:1px solid var(--rule)}}
.mtable tr.mrow:first-child td{{border-top:0;padding-top:.2rem}}
.mtable tr.mdesc td{{padding:0 0 .5rem;color:var(--body)}}
.mtable td.r{{text-align:right}}
.mtable td.r .pill{{white-space:nowrap}}
.wf{{color:var(--muted);margin-top:.2rem}}
.baserate{{margin:.1rem 0 1rem;padding:.6rem .8rem;border-left:2px solid var(--rule);
  color:var(--body)}}
.lks{{display:flex;flex-direction:column;gap:.25rem;margin:.9rem 0}}
.lk{{display:grid;grid-template-columns:3rem 1fr 2rem;align-items:center;gap:.5rem;
  font-family:var(--mono);font-size:.72rem}}
.lkl{{color:var(--muted)}}
.lkbar{{background:var(--rule);border-radius:2px;height:8px;overflow:hidden}}
.lkbar i{{display:block;height:100%;border-radius:2px}}
.lkbar i.good{{background:var(--good)}} .lkbar i.warn{{background:var(--warn)}}
.lkbar i.bad{{background:var(--bad)}}
.lkv{{text-align:right;font-variant-numeric:tabular-nums}}
.filmhead{{display:flex;align-items:baseline;gap:.6rem;margin:.5rem 0 .2rem;
  font-family:var(--mono);font-size:.8rem}}
.filmhead b{{color:var(--ink);font-variant-numeric:tabular-nums}}
.cfkind{{font-size:.62rem;letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted);border:1px solid var(--rule);border-radius:3px;padding:.05rem .35rem}}
.cfkind.fc{{color:var(--accent);border-color:var(--accent)}}
.cfctl{{display:flex;align-items:center;gap:.6rem;margin:.5rem 0 .3rem;max-width:22rem}}
.cfctl input[type=range]{{flex:1;accent-color:var(--accent)}}
.cftrack{{display:flex;gap:1px;max-width:22rem;height:5px;margin-bottom:.5rem}}
.cftrack i{{flex:1;border-radius:1px;background:var(--rule)}}
.cftrack i.fc{{background:var(--accent);opacity:.35}}
.cftrack i.on{{outline:1px solid var(--ink)}}
.rings{{display:flex;gap:.5rem;margin:.8rem 0 .6rem;flex-wrap:wrap}}
.rk{{flex:1 1 5rem;border:1px solid var(--rule);border-radius:3px;padding:.4rem .5rem}}
.rkl{{display:block;font-family:var(--mono);font-size:.62rem;letter-spacing:.08em;
  text-transform:uppercase;color:var(--muted)}}
.rkv{{font-family:var(--mono);font-size:1.15rem;font-variant-numeric:tabular-nums}}
.compass{{display:grid;grid-template-columns:repeat(3,1fr);gap:2px;max-width:15rem;
  margin:.6rem 0}}
.oc{{background:var(--ground);border-radius:3px;padding:.35rem .2rem;text-align:center;
  position:relative;isolation:isolate}}
/* Density readout in two parts, because a wash behind text can only go so far. The tint
   tops out at .08: the amber "warn" colour is barely 3.5:1 on plain background, and at .30
   it fell to 1.8:1 — unreadable. The edge bar carries the rest of the signal, where there
   is no text to fight, so a full cell still reads as full at a glance. */
.oc::before{{content:"";position:absolute;inset:0;border-radius:3px;background:var(--ink);
  opacity:calc(var(--f,0) * .08);z-index:-1}}
.oc::after{{content:"";position:absolute;left:0;bottom:0;height:3px;border-radius:0 0 3px 3px;
  width:calc(var(--f,0) * 100%);background:var(--ink);opacity:.55;z-index:-1}}
.oc > *{{position:relative}}
.oc.slot{{outline:1px solid var(--accent);outline-offset:-1px}}
.oc.mid{{background:transparent;border:1px dashed var(--rule)}}
.ocv{{display:block;font-family:var(--mono);font-size:.95rem;
  font-variant-numeric:tabular-nums}}
.ocl{{display:block;font-family:var(--mono);font-size:.58rem;letter-spacing:.08em;
  color:var(--muted)}}
.cam{{display:block;font-family:var(--mono);font-size:.58rem;color:var(--muted);
  text-align:center;letter-spacing:.04em}}
.nightbar{{fill:var(--accent);opacity:.75}}
.daybar{{fill:var(--rule)}}
.pill{{font-family:var(--mono);font-size:.62rem;letter-spacing:.08em;text-transform:uppercase;padding:.15rem .4rem;border-radius:3px;white-space:nowrap;border:1px solid}}
.pill.on{{color:var(--good);border-color:var(--good)}}
.pill.off{{color:var(--muted);border-color:var(--rule)}}
.mrange{{font-family:var(--mono);font-size:.72rem;margin-top:.45rem;padding-top:.4rem;
  border-top:1px solid var(--rule);color:var(--muted)}}
.mrange b{{color:var(--body)}}
.good{{color:var(--good)}} .warn{{color:var(--warn)}} .bad{{color:var(--bad)}} .dim{{color:var(--muted)}}
svg{{width:100%;height:auto;display:block}}
.band{{fill:var(--band)}}
.sband{{fill:var(--sband)}}
.sbandlab{{fill:var(--warn);font-family:var(--mono);font-size:9px;letter-spacing:.08em;
  text-transform:uppercase;opacity:.8}}
.bandlab{{fill:var(--good);font-family:var(--mono);font-size:9px;letter-spacing:.08em;
  text-transform:uppercase;opacity:.85}}
.grid{{stroke:var(--rule);stroke-width:1}}
.axis{{stroke:var(--rule);stroke-width:1}}
.ax{{fill:var(--muted);font-family:var(--mono);font-size:10px}}
.ax.dim{{opacity:.6;font-size:9px}}
.live{{position:relative;padding-top:56.25%;margin-top:1rem;border-radius:4px;overflow:hidden;
  background:var(--sunken)}}
.live iframe{{position:absolute;inset:0;width:100%;height:100%;border:0}}
.film{{display:flex;gap:.5rem;padding-bottom:.5rem;margin-top:.6rem}}
.shot{{margin:0;flex:0 0 152px;display:flex;flex-direction:column;gap:.15rem;
  background:var(--surface);border:1px solid var(--rule);border-radius:4px;padding:.4rem}}
.shot img{{width:100%;height:86px;object-fit:cover;border-radius:2px;display:block;
  background:var(--sunken)}}
.shot .noimg{{width:100%;height:86px;border-radius:2px;background:var(--sunken)}}
.shot .hr{{font-family:var(--mono);font-size:.62rem;letter-spacing:.06em;color:var(--muted)}}
.shot .fc{{font-family:var(--mono);font-size:.72rem;color:var(--accent);font-weight:600}}
.shot .obs{{font-family:var(--mono);font-size:.8rem;font-weight:700;margin-top:.15rem}}
.striprow{{margin-bottom:1rem}}
.striphead{{display:flex;gap:.6rem;align-items:baseline;margin-bottom:.3rem}}
.striphead b{{color:var(--ink)}}
.striprow svg{{max-width:560px}}
.cloud{{fill:var(--ink)}}
.cellb{{fill:none;stroke:var(--rule);stroke-width:1}}
.nodata{{fill:none;stroke:var(--rule);stroke-width:1;stroke-dasharray:2 2}}
.cellv{{fill:var(--muted);font-family:var(--mono);font-size:7.5px;
  paint-order:stroke;stroke:var(--surface);stroke-width:2.5px}}
.hlab{{fill:var(--muted);font-family:var(--mono);font-size:8px}}
.srclab{{fill:var(--body);font-family:var(--mono);font-size:8.5px}}
.corebox{{fill:none;stroke:var(--accent);stroke-width:1.5;opacity:.8}}
.corelab{{fill:var(--accent);font-family:var(--mono);font-size:7px;letter-spacing:.12em}}
.latebox{{fill:none;stroke:var(--s2);stroke-width:1.5;opacity:.75;stroke-dasharray:3 2}}
.lateboxlab{{fill:var(--s2)}}
.rng0{{stroke:var(--s0);stroke-width:5;opacity:.22;stroke-linecap:round}}
.rng1{{stroke:var(--s1);stroke-width:5;opacity:.22;stroke-linecap:round}}
.rng2{{stroke:var(--s2);stroke-width:5;opacity:.22;stroke-linecap:round}}
path.s0{{stroke:var(--s0);stroke-width:2;stroke-linejoin:round;stroke-linecap:round}}
path.s1{{stroke:var(--s1);stroke-width:2;stroke-linejoin:round;stroke-linecap:round}}
path.s2{{stroke:var(--s2);stroke-width:2;stroke-linejoin:round;stroke-linecap:round}}
circle.s0{{fill:var(--s0)}} circle.s1{{fill:var(--s1)}} circle.s2{{fill:var(--s2)}}
circle.dot{{stroke:var(--surface);stroke-width:2}}
text.lab{{font-family:var(--mono);font-size:10px;font-weight:600}}
text.s0{{fill:var(--s0)}} text.s1{{fill:var(--s1)}} text.s2{{fill:var(--s2)}}
table{{border-collapse:collapse;width:100%;font-size:.9rem}}
th,td{{text-align:left;padding:.45rem .6rem;border-bottom:1px solid var(--rule);white-space:nowrap}}
th{{font-family:var(--mono);font-size:.64rem;letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted);font-weight:400}}
td.n{{font-family:var(--mono);font-variant-numeric:tabular-nums}}
td.better{{color:var(--good);font-weight:600}} td.worse{{color:var(--bad);font-weight:600}}
.val{{font-weight:600}}
.rng{{stroke:var(--muted);stroke-width:3;stroke-linecap:round;opacity:.45}}
.mdot{{fill:var(--accent);stroke:var(--surface);stroke-width:2}}
.lead{{stroke:var(--rule);stroke-width:1}}
.nws{{fill:none;stroke:var(--ink);stroke-width:2}}
.nlab{{fill:var(--ink);font-family:var(--mono);font-size:11px;font-weight:600}}
.mlab{{fill:var(--muted);font-family:var(--mono);font-size:9px;letter-spacing:.04em}}
.mval{{fill:var(--body);font-family:var(--mono);font-size:10px;font-variant-numeric:tabular-nums}}
.spread{{font-family:var(--mono);font-size:15px;font-weight:700;font-variant-numeric:tabular-nums}}
.spreadlab{{font-family:var(--mono);font-size:8.5px;letter-spacing:.1em;text-transform:uppercase}}
text.good{{fill:var(--good)}} text.warn{{fill:var(--warn)}} text.bad{{fill:var(--bad)}}
.delta{{display:inline-block;margin-left:.4rem;font-size:.76rem;font-weight:600;
  letter-spacing:.02em}}
.step{{display:inline-block;margin-left:.45rem;font-weight:700}}
td.trail{{font-family:var(--mono);font-size:1rem;letter-spacing:.12em}}
.note{{color:var(--muted);font-size:.85rem;margin:.6rem 0 0}}
.lede{{color:var(--body);font-size:.94rem;max-width:64ch;margin:0 0 .2rem}}
.next{{margin:.5rem 0 .9rem;padding:.5rem .75rem;background:var(--surface);
  border:1px solid var(--rule);border-left:3px solid var(--accent);border-radius:3px;
  font-family:var(--mono);font-size:.78rem}}
.next b{{color:var(--accent)}}
.vint{{display:grid;grid-template-columns:max-content 1fr;gap:.15rem .9rem;margin-top:.7rem;
  font-family:var(--mono);font-size:.76rem}}
.vk{{color:var(--ink);white-space:nowrap}}
.vv{{color:var(--muted)}}
.scroll{{overflow-x:auto}}
@media (prefers-reduced-motion:reduce){{*{{transition:none!important}}}}
</style>
</head>
<body>
<div class="bar"><div class="bar-in">
  <a href="index.html">← Trip plan</a>
  <button class="btn" id="theme" type="button">Theme</button>
  <button class="btn" id="night" type="button" aria-pressed="false">Night</button>
</div></div>

<div class="wrap">
  <div class="eyebrow" style="margin-top:2rem">Fetched {t:%a %d %b, %H:%M} EDT · forecast issued
    {issued} · gridpoint {latest['grid']}</div>
  <h1>Forecast trend</h1>
  {nextline}
  <p class="lede">Cloud cover. <b>Core window 10–11:30 PM</b> decides go/no-go; <b>1–4 AM</b> is
  Perseids and the scope. Each point is one forecast run.</p>

  {trip_banner(latest)}
  {base_rate_line(_skill(), latest)}
  <div class="cards">{"".join(cards)}</div>
  <p class="note">{srcnote}</p>

  <div class="card">
    {svg_chart(hist)}
    <p class="note">Lower is better. Dot &amp; line = consensus · pale bar = source spread.
    <b style="color:var(--ink)">Bars getting shorter = consensus forming.</b></p>
  </div>

  <h2>How much each night has moved</h2>
  <div class="card"><div class="scroll">{delta_table(hist)}</div></div>

  {webcam_section(WEBCAM_OVERRIDE)}

  <h2>Hour by hour</h2>
  <div class="card">
    <p class="lede">Darker = more cloud. Rows are sources.</p>
    <div style="margin-top:1.2rem" class="scroll">{hourly_strips(latest)}</div>
    <p class="note">EDT, 6 PM–7 AM. Amber box = core window. Dashed = no data.</p>
  </div>

  <h2>Do the models agree?</h2>
  <div class="card">
    <div>{agreement_svg(latest)}</div>
    <p class="note">Dots = each source · bar = range · ◇ = consensus median · shaded = under {GO}%</p>
  </div>

  <h2>Calibration — the nights before the trip</h2>
  <div class="card">
    <p class="lede">Nights before the trip, which verify while you watch — so this measures how far a forecast actually travels in this pattern.</p>
    {calibration(hist, WEBCAM_OVERRIDE or _wlog(), _satlog())}
  </div>

  <h2>What the percentage means</h2>
  <div class="card">
    <p class="lede"><b>Percent of sky covered by cloud</b> — not a probability. PoP is a different quantity and doesn't matter here.</p>
    <div class="scroll" style="margin-top:.9rem"><table>
      <thead><tr><th>Sky cover</th><th>NWS wording</th><th>For you</th></tr></thead>
      <tbody>
        <tr><td class="n">0–12%</td><td>Clear</td><td class="good">Everything works</td></tr>
        <tr><td class="n">13–37%</td><td>Mostly clear</td><td class="good">Shootable — might lose a few frames</td></tr>
        <tr><td class="n">38–62%</td><td>Partly cloudy</td><td class="warn">Broken. You'd get gaps — OH_SHIT territory</td></tr>
        <tr><td class="n">63–87%</td><td>Mostly cloudy</td><td class="bad">Occasional sucker holes</td></tr>
        <tr><td class="n">88–100%</td><td>Overcast</td><td class="bad">Nothing</td></tr>
      </tbody></table></div>
    <p class="note" style="margin-top:.9rem">Threshold {GO}% sits inside "mostly clear" (13–37%), deliberately short of its top.
    Caveat: it's a whole-dome average and can't say <em>where</em> the cloud is.</p>
  </div>

  {waiting_section(_skill())}

  <h2>The sources</h2>
  <div class="card">
    <p class="lede">Every number on this page is the median across these. None of them is
    the answer on its own.</p>
    <div style="margin-top:1rem">{model_notes(latest)}</div>

    <h3 class="sub">Should you weight one over another?</h3>
    <p>Yes, and it changes as the trip approaches.</p>
    <table class="mtable"><tbody>
      <tr class="mrow"><td class="n">Now — 7+ days</td>
        <td class="r"><b>AIFS, and the spread</b></td></tr>
      <tr class="mdesc"><td colspan="2">Measured at this site, AIFS is the most accurate
        model beyond five days and ECMWF one of the worst — the reverse of their short-range
        order. Mostly though, read the spread rather than the number: a ±60 split means the
        atmosphere has not committed and any single model quoting you 23% is guessing.
        <b>Waiting past about five days out is where the forecast stops improving</b> — see
        "Does waiting help?" above.</td></tr>
      <tr class="mrow"><td class="n">8 Aug — decision day</td>
        <td class="r"><b>ECMWF, then UKMO</b></td></tr>
      <tr class="mdesc"><td colspan="2">Inside three days ECMWF is the strongest here, UKMO
        and ICON are both in range by then, and NWS has a human in the loop. HRRR still
        cannot see 11 Aug. Note this is already past the point where extra waiting buys
        accuracy — by the 6th or 7th you have essentially the whole picture.</td></tr>
      <tr class="mrow"><td class="n">9–10 Aug</td><td class="r"><b>HRRR</b></td></tr>
      <tr class="mdesc"><td colspan="2">3 km resolves the valley and the lakes instead of
        averaging them into a 13 km box. For terrain cloud nothing else here is close.</td></tr>
      <tr class="mrow"><td class="n">On site</td>
        <td class="r"><b>The webcam and your eyes</b></td></tr>
      <tr class="mdesc"><td colspan="2">See the scoreboard above — it measures which model has
        actually been right at this location, which beats any model's general
        reputation.</td></tr>
    </tbody></table>

    <p class="note" style="margin-top:1rem"><b>The honest caveat:</b> night-time low cloud
    and valley fog are the weakest thing every global model does. They parameterise
    boundary-layer cloud across a 13–25 km box over terrain that changes on a 1 km scale.
    A clear synoptic pattern can still deliver a fogged-in lake at 3 AM, and none of these
    will have told you. That is what the webcam is for.</p>
  </div>

  <div style="margin-top:2.5rem;padding-top:1.2rem;border-top:1px solid var(--rule);
              color:var(--muted);font-size:.84rem">
    <a href="index.html" style="color:var(--accent)">← Trip plan</a>
    <div class="vint">{runline}</div>
    <p style="margin-top:.7rem;opacity:.8">Rebuilt hourly from
    <span style="font-family:var(--mono)">api.weather.gov</span>, Open-Meteo and the lake webcam.</p>
    <p style="margin-top:.35rem;opacity:.8">Each model is a snapshot of a different run — so a
    little of any apparent disagreement is just run age, not genuine divergence.</p>
  </div>
</div>

<script>
(function(){{
  // live countdown to the next cron run, ticking — a build-time value goes stale immediately
  var box=document.querySelector('.next'), el=document.getElementById('nextcheck');
  if(box&&el){{
    var m=parseInt(box.getAttribute('data-cron-min'),10)||0;
    var tick=function(){{
      var now=new Date(), nx=new Date(now);
      nx.setSeconds(0,0); nx.setMinutes(m);
      if(nx<=now) nx.setHours(nx.getHours()+1);
      var mins=Math.round((nx-now)/60000);
      var hh=String(nx.getHours()).padStart(2,'0')+':'+String(nx.getMinutes()).padStart(2,'0');
      el.innerHTML='<b>Next check '+hh+'</b> <span class="dim">— '+
        (mins<=1?'any moment now':'in '+mins+' min')+', then hourly</span>';
    }};
    tick(); setInterval(tick,20000);
  }}
  // compass film: scrub 12 h of satellite observation into 12 h of HRRR forecast
  var cfEl=document.getElementById('cfData');
  if(cfEl){{
    var F=JSON.parse(cfEl.textContent), grid=document.getElementById('cfGrid'),
        slide=document.getElementById('cfSlide'), play=document.getElementById('cfPlay'),
        lab=document.getElementById('cfTime'), kind=document.getElementById('cfKind'),
        track=document.getElementById('cfTrack'), timer=null, i=+slide.value;
    F.forEach(function(f,k){{
      var b=document.createElement('i');
      if(f.kind==='forecast') b.className='fc';
      track.appendChild(b);
    }});
    var band=function(v){{
      if(v===null||v===undefined) return 'dim';
      return v<={GO}?'good':(v<=55?'warn':'bad');
    }};
    var draw=function(){{
      var f=F[i]; if(!f) return;
      grid.querySelectorAll('[data-oct]').forEach(function(c){{
        var k=c.getAttribute('data-oct'),
            v=(k==='dome')?f.cloud:(f.octants?f.octants[k]:null),
            s=c.querySelector('.ocv');
        s.textContent=(v===null||v===undefined)?'—':(k==='dome'?v+'%':v);
        s.className='ocv '+band(v);
        c.style.setProperty('--f',(v===null||v===undefined)?0:Math.max(0,Math.min(100,v))/100);
      }});
      var d=new Date(f.time);
      lab.textContent=d.toLocaleDateString([], {{weekday:'short'}})+' '+
        String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0');
      kind.textContent=f.kind==='forecast'?'HRRR forecast':'satellite';
      kind.className='cfkind'+(f.kind==='forecast'?' fc':'');
      Array.prototype.forEach.call(track.children,function(b,k){{
        b.classList.toggle('on',k===i);
      }});
      slide.value=i;
    }};
    slide.addEventListener('input',function(){{ i=+slide.value; draw(); }});
    play.addEventListener('click',function(){{
      if(timer){{ clearInterval(timer); timer=null; play.textContent='▶ Play'; return; }}
      play.textContent='❚❚ Pause';
      timer=setInterval(function(){{ i=(i+1)%F.length; draw(); }},550);
    }});
    draw();
  }}

  var r=document.documentElement,t=document.getElementById('theme'),n=document.getElementById('night');
  t.addEventListener('click',function(){{
    var c=r.getAttribute('data-theme')||(window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
    r.setAttribute('data-theme',c==='dark'?'light':'dark');
  }});
  n.addEventListener('click',function(){{
    var on=r.getAttribute('data-night')==='on';
    if(on){{r.removeAttribute('data-night');n.setAttribute('aria-pressed','false');}}
    else{{r.setAttribute('data-night','on');n.setAttribute('aria-pressed','true');}}
  }});
}})();
</script>
</body>
</html>
"""
    open(PAGE, "w").write(html)


def main():
    hist = json.load(open(HIST)) if os.path.exists(HIST) else []
    new = snapshot()
    # one entry per FORECAST ISSUANCE, not per run. GYX publishes ~twice a day, so
    # running the script again before a new package lands would otherwise log the
    # same numbers twice and fake a stability that isn't there.
    # Skip only if BOTH the NWS package and every model reading are unchanged. The models
    # refresh more often than the NWS issuance, so keying on issuance alone would silently
    # discard fresh ECMWF/GFS/GEM data.
    def fingerprint(e):
        return (e.get("issued"),
                tuple(sorted((l, tuple(sorted((e["nights"][l].get("models") or {}).items())))
                             for l, _ in ALL if l in e["nights"])))
    if hist and fingerprint(hist[-1]) == fingerprint(new):
        print("no new NWS package and no model changes")
        # The deterministic forecast has not moved, but the ensemble and the fog/haze
        # readings have their own cadence and belong to "now" rather than to a package.
        # Refresh them on the existing entry instead of banking a duplicate snapshot.
        if new.get("trip"):
            hist[-1]["trip"] = new["trip"]
        # Merge conditions per night and per field. A partial outage — one endpoint timing
        # out while the other answers — returns a dict that is truthy but missing whole
        # nights, and replacing wholesale threw away good readings. Seen in the wild.
        if new.get("cond"):
            cur = hist[-1].setdefault("cond", {})
            for lab, rec in new["cond"].items():
                cur.setdefault(lab, {}).update({k: v for k, v in rec.items() if v is not None})
        json.dump(hist, open(HIST, "w"), indent=1)
        write_page(hist)          # webcam data still moves hourly, so rebuild anyway
        write_log(hist)
        return
    hist.append(new)
    hist.sort(key=lambda e: e["taken"])
    compact(hist)
    json.dump(hist, open(HIST, "w"), indent=1)
    write_log(hist)
    write_page(hist)
    print(f"snapshot {len(hist)} → {HIST}, {LOG}, {PAGE}")


if __name__ == "__main__":
    main()
