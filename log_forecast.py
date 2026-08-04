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
DARK    = (21, 4)           # 21:56–03:45 EDT — full astronomical dark
GO      = 30                # go/no-go threshold, % cloud cover

# Second opinion: Open-Meteo exposes individual models rather than a blend. ECMWF is the
# most skillful global model and is genuinely independent of NWS's GFS/NAM-based product.
# The point isn't more data — it's that MODEL AGREEMENT IS A CONFIDENCE SIGNAL. A narrow
# spread means the atmosphere is predictable; a wide one means nobody knows yet.
OM_MODELS = [("ecmwf_ifs025", "ECMWF"), ("gfs_seamless", "GFS"),
             ("icon_seamless", "ICON"), ("gem_seamless", "GEM")]
# Open-Meteo publishes per-dataset run metadata. The slugs differ from the model
# parameter names used in the forecast call, and not every dataset stays current —
# anything older than 48 h is treated as unknown rather than printed as fact.
OM_META = [("ECMWF", "ecmwf_ifs025"), ("GFS", "ncep_gfs013"), ("ICON", "dwd_icon")]

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


def snapshot():
    p = get(f"https://api.weather.gov/points/{SITE[1]},{SITE[2]}")["properties"]
    grid = get(p["forecastGridData"])["properties"]
    sky, pop, dew = (expand(grid[k]) for k in
                     ("skyCover", "probabilityOfPrecipitation", "dewpoint"))
    om = open_meteo()
    runs = model_runs()

    stamp = datetime.now(EDT)
    entry = {"taken": stamp.isoformat(),
             "issued": grid.get("updateTime"),          # when NWS published this package
             "runs": runs,                              # model init + availability times
             "grid": f"{p['gridId']} {p['gridX']},{p['gridY']}",
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
            "hour_labels": (om.get(label) or {}).get("hours", []),
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
            out.append("| Hour (EDT) | Sky | PoP | Dewpoint |\n|---|---|---|---|\n")
            for r in n["rows"]:
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

    # go-zone band
    p.append(f'<rect class="band" x="{L}" y="{py(GO):.1f}" width="{pw}" '
             f'height="{T+ph-py(GO):.1f}"/>')
    p.append(f'<text class="bandlab" x="{L+6}" y="{T+ph-8:.1f}">under {GO}% — go</text>')

    # gridlines + y labels
    for v in (0, 25, 50, 75, 100):
        p.append(f'<line class="grid" x1="{L}" y1="{py(v):.1f}" x2="{L+pw}" y2="{py(v):.1f}"/>')
        p.append(f'<text class="ax" x="{L-8}" y="{py(v)+4:.1f}" text-anchor="end">{v}%</text>')

    # x labels
    for i, d in enumerate(xs):
        p.append(f'<text class="ax" x="{px(i):.1f}" y="{T+ph+18:.0f}" '
                 f'text-anchor="middle">{d:%d %b}</text>')
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
        pts = [(i, e["nights"][label]["core"]) for i, e in enumerate(hist)
               if e["nights"][label]["core"] is not None]
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


def mrange(nd):
    """(lo, hi, spread) across models for a night, or None."""
    m = nd.get("models") or {}
    if not m:
        return None
    lo, hi = min(m.values()), max(m.values())
    return lo, hi, hi - lo


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

    rowsH, W, PAD = 92, 720, 92
    nights = [(l, latest["nights"][l]) for l, _ in NIGHTS]
    H = rowsH * len(nights) + 26
    tw = W - PAD - 118
    def x(v): return PAD + tw * v / 100

    p = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Spread between forecast models '
         f'for each night" preserveAspectRatio="xMidYMid meet">']
    p.append(f'<rect class="band" x="{PAD}" y="14" width="{x(GO)-PAD:.1f}" height="{H-30}"/>')
    for v in (0, 25, 50, 75, 100):
        p.append(f'<line class="grid" x1="{x(v):.1f}" y1="14" x2="{x(v):.1f}" y2="{H-16}"/>')
        p.append(f'<text class="ax" x="{x(v):.1f}" y="{H-4}" text-anchor="middle">{v}%</text>')

    for i, (label, nd) in enumerate(nights):
        y = 46 + i * rowsH
        p.append(f'<text class="nlab" x="0" y="{y+4}">{label}</text>')
        mods = nd.get("models") or {}
        if not mods:
            p.append(f'<text class="ax" x="{PAD}" y="{y+4}">no model data</text>')
            continue
        lo, hi = min(mods.values()), max(mods.values())
        p.append(f'<line class="rng" x1="{x(lo):.1f}" y1="{y}" x2="{x(hi):.1f}" y2="{y}"/>')

        pts = sorted(mods.items(), key=lambda kv: kv[1])
        xs  = [x(v) for _, v in pts]
        lt  = tier(xs, 40)        # model names need ~40px
        vt  = tier(xs, 24)        # numbers need ~24px

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

        nws = nd.get("core")
        if nws is not None:
            p.append(f'<path class="nws" d="M{x(nws):.1f},{y-9} L{x(nws)+6:.1f},{y} '
                     f'L{x(nws):.1f},{y+9} L{x(nws)-6:.1f},{y} Z"/>')
        spread = hi - lo
        verd = "agree" if spread < 20 else "some spread" if spread < 40 else "no consensus"
        cls  = "good" if spread < 20 else "warn" if spread < 40 else "bad"
        p.append(f'<text class="spread {cls}" x="{W-112}" y="{y-2}">±{spread}</text>')
        p.append(f'<text class="spreadlab {cls}" x="{W-112}" y="{y+12}">{verd}</text>')
    p.append("</svg>")
    return "\n".join(p)


def webcam_section(log=None):
    """Live view, an hourly filmstrip with the forecast above each frame, and a scoreboard.

    The filmstrip is the point: scroll it and you can see what a given forecast number
    actually looked like out of the window.
    """
    if log is None:
        if not os.path.exists("webcam_log.json"):
            return ""
        log = json.load(open("webcam_log.json"))
    day = [e for e in log if not e["night"] and e["cloud"] is not None]
    if not day:
        return ""

    # scoreboard: mean absolute error per model
    errs = {}
    for e in day:
        for m, v in (e.get("models") or {}).items():
            errs.setdefault(m, []).append(abs(v - e["cloud"]))
    score = ""
    if any(len(v) >= 2 for v in errs.values()):
        rows = "".join(
            f"<tr><td>{m}</td><td class='n'>{len(v)}</td>"
            f"<td class='n {'good' if sum(v)/len(v) < 12 else 'warn' if sum(v)/len(v) < 25 else 'bad'}'>"
            f"{sum(v)/len(v):.0f} pts</td></tr>"
            for m, v in sorted(errs.items(), key=lambda kv: sum(kv[1]) / len(kv[1])))
        score = ('<div class="scroll" style="margin-top:1rem"><table><thead><tr>'
                 '<th>Model</th><th>Checks</th><th>Mean error vs camera</th></tr></thead><tbody>'
                 + rows + '</tbody></table></div>'
                 '<p class="note">Lowest = believe that one.</p>')

    cells = []
    for e in reversed(log[-30:]):
        t = datetime.fromisoformat(e["time"])
        ms = e.get("models") or {}
        if e["night"]:
            fc = f'<span class="fc dim">{min(ms.values())}–{max(ms.values())}%</span>' if ms else \
                 '<span class="fc dim">—</span>'
            obs = '<span class="obs dim">night</span>'
        else:
            fc = (f'<span class="fc">{min(ms.values())}–{max(ms.values())}%</span>'
                  if ms else '<span class="fc dim">—</span>')
            if ms:
                d = abs(e["cloud"] - sum(ms.values()) / len(ms))
                cl = "good" if d < 15 else "warn" if d < 30 else "bad"
            else:
                cl = ""
            obs = f'<span class="obs {cl}">{e["cloud"]}%</span>'
        img = (f'<img src="{e["shot"]}" alt="webcam {t:%d %b %H:%M}" loading="lazy">'
               if os.path.exists(e["shot"]) else '<div class="noimg"></div>')
        cells.append(f'<figure class="shot"><span class="hr">{t:%a %H:%M}</span>{fc}{img}{obs}</figure>')

    return f'''
  <h2>Ground truth — the webcam</h2>
  <div class="card">
    <p class="lede">First Connecticut Lake, ~15 km from the site. Hourly frame, cloud estimated,
    compared against what each model said for that hour.</p>
    <div class="live"><iframe src="https://www.youtube.com/embed/wNxk-XC8Z5s"
      title="First Connecticut Lake live webcam" loading="lazy" allowfullscreen
      referrerpolicy="strict-origin-when-cross-origin"></iframe></div>
    <p class="note">Live — needs a connection. Frames below are archived.</p>
    {score}
    <h3 style="margin-top:1.4rem">Hour by hour, forecast above the photo</h3>
    <div class="film scroll">{"".join(cells)}</div>
    <p class="note">Above = forecast range · below = observed ·
    <b class="good">within 15</b> / <b class="warn">30</b> / <b class="bad">beyond</b>.
    Daylight only.</p>
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
        cw, cell, gap = 34, 34, 2
        W = len(hrs) * (cell + gap) + 74
        rows = [("NWS", [nws.get(h) for h in hrs])] + \
               [(k, v) for k, v in sorted(mh.items())]
        H = len(rows) * 26 + 34
        p = [f'<svg viewBox="0 0 {W} {H}" role="img" '
             f'aria-label="Hour by hour cloud cover for {label}">']
        # core-window bracket
        ci = [i for i, h in enumerate(hrs) if int(h) in CORE_HR]
        if ci:
            x0 = 70 + ci[0] * (cell + gap) - 1
            x1 = 70 + (ci[-1] + 1) * (cell + gap) - gap + 1
            p.append(f'<rect class="corebox" x="{x0}" y="12" width="{x1-x0}" '
                     f'height="{H-30}" rx="3"/>')
            p.append(f'<text class="corelab" x="{(x0+x1)/2:.0f}" y="8" '
                     f'text-anchor="middle">CORE</text>')
        for i, h in enumerate(hrs):
            p.append(f'<text class="hlab" x="{70 + i*(cell+gap) + cell/2:.0f}" y="{H-6}" '
                     f'text-anchor="middle">{h}</text>')
        for r, (name, vals) in enumerate(rows):
            y = 18 + r * 26
            p.append(f'<text class="srclab" x="64" y="{y+14}" text-anchor="end">{name}</text>')
            for i, v in enumerate(vals):
                x = 70 + i * (cell + gap)
                if v is None:
                    p.append(f'<rect class="nodata" x="{x}" y="{y}" width="{cell}" '
                             f'height="20" rx="2"/>')
                    continue
                p.append(f'<rect class="cloud" x="{x}" y="{y}" width="{cell}" height="20" '
                         f'rx="2" style="opacity:{max(v,0)/100:.2f}"/>')
                p.append(f'<rect class="cellb" x="{x}" y="{y}" width="{cell}" height="20" rx="2"/>')
                p.append(f'<text class="cellv" x="{x+cell/2:.0f}" y="{y+14}" '
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
        vals = [(datetime.fromisoformat(e["taken"]), e["nights"][label]["core"])
                for e in hist if e["nights"][label]["core"] is not None]
        if not vals:
            rows.append(f"<tr><td>{label}</td><td colspan='4' class='dim'>no data yet</td></tr>")
            continue
        first, last = vals[0][1], vals[-1][1]
        d = last - first
        swing = max(v for _, v in vals) - min(v for _, v in vals)
        arrow = "→" if d == 0 else ("↑" if d > 0 else "↓")
        cls = "worse" if d > 5 else ("better" if d < -5 else "")
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
                    f"<td class='n {cls}'>{arrow} {abs(d)}</td><td class='n'>{swing}</td>"
                    f"{spcell}</tr>")
    return ("<table><thead><tr><th>Night</th><th>First</th><th>Latest</th>"
            "<th>Change</th><th>Range</th><th>Model spread</th></tr></thead><tbody>"
            + "".join(rows) + "</tbody></table>")


def calibration(hist):
    """How much has a night's forecast actually moved as its lead time shrank?"""
    if len(hist) < 2:
        return ('<p class="note">Fills in over the next day or two, once these nights have been '
                'forecast more than once — then it shows how far a forecast actually travels '
                'between day 5 and day 1.</p>')
    rows, moves = [], []
    for label, day in LEADUP:
        vals = [(e["nights"][label]["lead"], e["nights"][label]["core"])
                for e in hist if e["nights"].get(label, {}).get("core") is not None]
        if len(vals) < 2:
            continue
        d = datetime.strptime(day, "%Y-%m-%d")
        lo, hi = min(v for _, v in vals), max(v for _, v in vals)
        first, last = vals[0][1], vals[-1][1]
        moves.append(hi - lo)
        rows.append(f"<tr><td>{d:%a %d %b}</td><td class='n'>{vals[0][0]}d → {vals[-1][0]}d</td>"
                    f"<td class='n'>{first}%</td><td class='n'>{last}%</td>"
                    f"<td class='n'>{hi-lo}</td></tr>")
    if not rows:
        return ('<p class="note">Not enough readings yet for the lead-up nights to show '
                'movement — check back tomorrow.</p>')
    avg, mx = sum(moves) / len(moves), max(moves)
    return (f'<p style="margin-bottom:.8rem"><b style="color:var(--ink)">Worst swing so far: '
            f'{mx} points</b> (typical {avg:.0f}). You are asking how <em>wrong</em> a forecast '
            f'could be — a tail question — so the worst case is the honest number and the mean '
            f'understates it. A night reading 45% four days out could plausibly land anywhere '
            f'within ±{mx} of that.</p>'
            '<div class="scroll"><table><thead><tr><th>Night</th><th>Lead</th><th>First</th>'
            '<th>Latest</th><th>Swing</th></tr></thead><tbody>' + "".join(rows) +
            '</tbody></table></div>')


WEBCAM_OVERRIDE = None      # preview_forecast.py sets this to render mock frames


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
        t = datetime.fromtimestamp(v[2], timezone.utc).astimezone(EDT)
        while t <= now:
            t += timedelta(hours=6)
        upcoming.append((t, n))
    upcoming.sort()
    nextmodels = " · ".join(f"{n} ~{t:%H:%M}" for t, n in upcoming[:3])
    nextline = (f'<div class="next"><b>Next check {nxt_check:%H:%M}</b> '
                f'<span class="dim">— in {mins} min, then hourly</span>'
                + (f'<span class="dim"> · next model data: {nextmodels}</span>'
                   if nextmodels else "") + '</div>')
    runline = ("".join(f' · <b>{n}</b> <span style="font-family:var(--mono)">{i}</span> run, '
                       f'published <span style="font-family:var(--mono)">{a}</span>'
                       for n, (i, a, *_) in sorted(rr.items()))
               + (" · <b>GEM</b> run time unknown" if "GEM" not in rr else "")) if rr else ""
    cards = []
    for si, (label, _) in enumerate(NIGHTS):
        nd = latest["nights"][label]
        d = datetime.strptime(nd["date"], "%Y-%m-%d")
        v = nd["core"]
        verdict = ("no data" if v is None else
                   "GO" if v <= GO else "marginal" if v <= 55 else "poor")
        vc = "dim" if v is None else ("good" if v <= GO else "warn" if v <= 55 else "bad")
        cb, cbh = nd.get("core_best"), nd.get("core_best_hr")
        lb, lbh = nd.get("late_best"), nd.get("late_best_hr")
        lt = nd.get("late")
        ml = nd.get("models_late") or {}
        ltxt = ("—" if lt is None else f"{lt}%")
        lrange = (f" · models {min(ml.values())}–{max(ml.values())}%" if ml else "")
        r = mrange(nd)
        if r:
            lo, hi, sp = r
            scls = "good" if sp < 20 else "warn" if sp < 40 else "bad"
            mline = (f'<span class="mrange">models <b>{lo}–{hi}%</b> '
                     f'<span class="{scls}">±{sp}</span></span>')
        else:
            mline = '<span class="mrange dim">no model data</span>'
        cards.append(
            f'<div class="ncard"><span class="swatch s{si}"></span>'
            f'<b>{label}</b><span class="dim">{d:%a %d %b} · lead {nd["lead"]}d</span>'
            f'<span class="big {vc}">{"—" if v is None else str(v)+"%"}</span>'
            f'<span class="verdict {vc}">NWS mean · {verdict}</span>'
            f'<span class="mrange">best hour '
            f'<b>{"—" if cb is None else hr12(cbh) + " · " + str(cb) + "%"}</b>'
            f'{"" if cb is None else " · " + ("shootable" if cb <= GO else "no clear hour")}</span>'
            f'{mline}'
            f'<span class="mrange">1–4 AM <b>{ltxt}</b>'
            f'{"" if lb is None else f" · best {hr12(lbh)} {lb}%"}{lrange}</span></div>')

    def band(v):
        return "good" if v <= GO else "warn" if v <= 55 else "bad"

    built = []
    for i, e in enumerate(hist):                      # chronological, so deltas look backwards
        et = datetime.fromisoformat(e["taken"])
        cells = []
        for l, _ in NIGHTS:
            v = e["nights"][l]["core"]
            if v is None:
                cells.append('<td class="n dim">—</td>')
                continue
            prev = next((hist[j]["nights"][l]["core"] for j in range(i - 1, -1, -1)
                         if hist[j]["nights"][l]["core"] is not None), None)
            if prev is None:
                delta = '<span class="delta dim">new</span>'
            elif v == prev:
                delta = '<span class="delta dim">→ 0</span>'
            else:
                d = v - prev
                # less cloud is better, so a fall is good
                delta = (f'<span class="delta {"bad" if d > 0 else "good"}">'
                         f'{"↑" if d > 0 else "↓"} {abs(d)}</span>')
            cells.append(f'<td class="n"><span class="val {band(v)}">{v}%</span>{delta}</td>')
        built.append(f"<tr><td>{et:%d %b %H:%M}</td>{''.join(cells)}</tr>")
    rowsrc = list(reversed(built))                    # newest first for display

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
  --band:rgba(46,107,79,.09);
  --s0:#2a78d6; --s1:#eb6834; --s2:#1baf7a;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --mono:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,monospace;
  --serif:ui-serif,"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
}}
@media (prefers-color-scheme:dark){{:root{{
  --ground:#0A0D14; --surface:#121722; --ink:#E7ECF5; --body:#BAC4D4; --muted:#7A8698;
  --rule:#232B39; --accent:#E3A445; --good:#6FBF95; --warn:#E3A445; --bad:#E8705C;
  --band:rgba(111,191,149,.10);
  --s0:#3987e5; --s1:#d95926; --s2:#199e70;
}}}}
:root[data-theme="light"]{{
  --ground:#F1F3F7; --surface:#FFFFFF; --ink:#171C26; --body:#3B4453; --muted:#6C7789;
  --rule:#D3D9E4; --accent:#B5721A; --good:#2E6B4F; --warn:#B5721A; --bad:#B03A2C;
  --band:rgba(46,107,79,.09); --s0:#2a78d6; --s1:#eb6834; --s2:#1baf7a;
}}
:root[data-theme="dark"]{{
  --ground:#0A0D14; --surface:#121722; --ink:#E7ECF5; --body:#BAC4D4; --muted:#7A8698;
  --rule:#232B39; --accent:#E3A445; --good:#6FBF95; --warn:#E3A445; --bad:#E8705C;
  --band:rgba(111,191,149,.10); --s0:#3987e5; --s1:#d95926; --s2:#199e70;
}}
:root[data-night="on"]{{
  --ground:#000; --surface:#0A0000; --ink:#FF4A22; --body:#C8351A; --muted:#7E2210;
  --rule:#3A0F06; --accent:#FF6A34; --good:#FF6A34; --warn:#C8351A; --bad:#7E2210;
  --band:rgba(255,106,52,.10);
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
.mrange{{font-family:var(--mono);font-size:.72rem;margin-top:.45rem;padding-top:.4rem;
  border-top:1px solid var(--rule);color:var(--muted)}}
.mrange b{{color:var(--body)}}
.good{{color:var(--good)}} .warn{{color:var(--warn)}} .bad{{color:var(--bad)}} .dim{{color:var(--muted)}}
svg{{width:100%;height:auto;display:block}}
.band{{fill:var(--band)}}
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
.striprow{{margin-bottom:1.4rem}}
.striphead{{display:flex;gap:.6rem;align-items:baseline;margin-bottom:.3rem}}
.striphead b{{color:var(--ink)}}
.cloud{{fill:var(--ink)}}
.cellb{{fill:none;stroke:var(--rule);stroke-width:1}}
.nodata{{fill:none;stroke:var(--rule);stroke-width:1;stroke-dasharray:2 2}}
.cellv{{fill:var(--muted);font-family:var(--mono);font-size:9px;
  paint-order:stroke;stroke:var(--surface);stroke-width:2.5px}}
.hlab{{fill:var(--muted);font-family:var(--mono);font-size:9px}}
.srclab{{fill:var(--body);font-family:var(--mono);font-size:10px}}
.corebox{{fill:none;stroke:var(--accent);stroke-width:1.5;opacity:.8}}
.corelab{{fill:var(--accent);font-family:var(--mono);font-size:8px;letter-spacing:.14em}}
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
.note{{color:var(--muted);font-size:.85rem;margin:.6rem 0 0}}
.lede{{color:var(--body);font-size:.94rem;max-width:64ch;margin:0 0 .2rem}}
.next{{margin:.5rem 0 .9rem;padding:.5rem .75rem;background:var(--surface);
  border:1px solid var(--rule);border-left:3px solid var(--accent);border-radius:3px;
  font-family:var(--mono);font-size:.78rem}}
.next b{{color:var(--accent)}}
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
  Perseids and the scope. Each point is one forecast run.<br>
  <b style="color:var(--accent)">Decide Aug 8 on Night 2</b> — Perseid max and new moon.
  Go if its core window is under {GO}%.</p>

  <div class="cards">{"".join(cards)}</div>

  <div class="card">
    {svg_chart(hist)}
    <p class="note">Lower is better. Dot &amp; line = NWS · pale bar = model spread.
    <b style="color:var(--ink)">Bars getting shorter = consensus forming.</b></p>
  </div>

  <h2>How much each night has moved</h2>
  <div class="card"><div class="scroll">{delta_table(hist)}</div></div>

  {webcam_section(WEBCAM_OVERRIDE)}

  <h2>Hour by hour</h2>
  <div class="card">
    <p class="lede">Darker = more cloud. Rows are sources.</p>
    <div style="margin-top:1.2rem" class="scroll">{hourly_strips(latest)}</div>
    <p class="note">EDT, 9 PM–4 AM. Amber box = core window. Dashed = no data.</p>
  </div>

  <h2>Do the models agree?</h2>
  <div class="card">
    <div>{agreement_svg(latest)}</div>
    <p class="note">Dots = models · bar = range · ◇ = NWS · shaded = under {GO}%</p>
  </div>

  <h2>Calibration — the nights before the trip</h2>
  <div class="card">
    <p class="lede">Nights before the trip, which verify while you watch — so this measures how far a forecast actually travels in this pattern.</p>
    {calibration(hist)}
  </div>

  <h2>Every reading</h2>
  <div class="card"><div class="scroll"><table>
    <thead><tr><th>Forecast run</th><th>Night 1</th><th>Night 2</th><th>Night 3</th></tr></thead>
    <tbody>{"".join(rowsrc)}</tbody></table></div>
    <p class="note">Core-window mean cloud cover. <b class="good">Green ≤30%</b> ·
    <b class="warn">amber ≤55%</b> · <b class="bad">red above</b>. The arrow is the change since
    that night's previous reading — <b class="good">↓ green is improving</b> (less cloud),
    <b class="bad">↑ red is deteriorating</b>. Full hourly detail in
    <span style="font-family:var(--mono)">FORECAST_LOG.md</span>.</p>
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
    <p class="note" style="margin-top:.9rem">Threshold {GO}% = top of "mostly clear."
    Caveat: it's a whole-dome average and can't say <em>where</em> the cloud is.</p>
  </div>

  <div style="margin-top:2.5rem;padding-top:1.2rem;border-top:1px solid var(--rule);
              color:var(--muted);font-size:.84rem">
    <a href="index.html" style="color:var(--accent)">← Trip plan</a>
    <br><span style="font-family:var(--mono)">Page built {t:%a %d %b %Y, %H:%M} EDT</span>
    · rebuilt hourly from <span style="font-family:var(--mono)">api.weather.gov</span>,
    Open-Meteo and the lake webcam.
    <br><b>Data vintages</b> — NWS package issued <span style="font-family:var(--mono)">{issued}</span>
    EDT{runline}
    <br><span style="opacity:.75">Each model is a snapshot of a different run, so a little of any
    apparent disagreement is just run age rather than genuine divergence.</span>
  </div>
</div>

<script>
(function(){{
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
        write_page(hist)          # webcam data still moves hourly, so rebuild anyway
        return
    hist.append(new)
    hist.sort(key=lambda e: e["taken"])
    json.dump(hist, open(HIST, "w"), indent=1)
    write_log(hist)
    write_page(hist)
    print(f"snapshot {len(hist)} → {HIST}, {LOG}, {PAGE}")


if __name__ == "__main__":
    main()
