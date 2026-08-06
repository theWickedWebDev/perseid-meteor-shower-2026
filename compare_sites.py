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


CSS = """
:root{--bg:#F1F3F7;--surface:#fff;--ink:#171C26;--body:#3B4453;--muted:#6C7789;
  --rule:#DDE2EA;--good:#2E6B4F;--warn:#B5721A;--bad:#B03A2C;--accent:#B5721A;
  --mono:ui-monospace,SFMono-Regular,Menlo,monospace}
@media(prefers-color-scheme:dark){:root{--bg:#0A0D14;--surface:#121722;--ink:#E7ECF5;
  --body:#BAC4D4;--muted:#7A8698;--rule:#242C3A}}
*{box-sizing:border-box}
body{margin:0;padding:2rem 1.2rem 4rem;background:var(--bg);color:var(--body);
  font:16px/1.6 ui-sans-serif,system-ui,sans-serif}
.wrap{max-width:46rem;margin:0 auto}
h1{color:var(--ink);font-size:1.6rem;margin:0 0 .2rem;letter-spacing:-.01em}
h2{color:var(--ink);font-size:1.05rem;margin:2rem 0 .6rem}
.eyebrow{font-family:var(--mono);font-size:.62rem;letter-spacing:.14em;
  text-transform:uppercase;color:var(--muted)}
.card{background:var(--surface);border:1px solid var(--rule);border-radius:5px;
  padding:1rem 1.1rem;margin:.8rem 0}
table{width:100%;border-collapse:collapse;font-size:.9rem}
th{font-family:var(--mono);font-size:.6rem;letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted);text-align:right;padding:.3rem .4rem;font-weight:400}
th:first-child,td:first-child{text-align:left}
td{padding:.5rem .4rem;border-top:1px solid var(--rule);text-align:right;
  font-family:var(--mono);font-variant-numeric:tabular-nums}
td b{color:var(--ink);font-size:1.05rem}
.sp{color:var(--muted);font-size:.8rem}
.pill{display:inline-block;font-family:var(--mono);font-size:.58rem;letter-spacing:.06em;
  text-transform:uppercase;padding:.1rem .34rem;border-radius:9px;border:1px solid}
.good{color:var(--good);border-color:var(--good)}
.warn{color:var(--warn);border-color:var(--warn)}
.bad{color:var(--bad);border-color:var(--bad)}
.note{color:var(--muted);font-size:.85rem;margin:.7rem 0 0}
.rule{border:0;border-top:1px solid var(--rule);margin:1.6rem 0}
.win{background:linear-gradient(transparent 62%,rgba(181,114,26,.22) 0)}
.rules li{margin:.35rem 0}
.rules b{color:var(--ink)}
"""


def page(verdicts, lake_e, home_e, ln, hn, cl, ch):
    """A local page. Never published — the point of it is a location that is not public."""
    def cell(x):
        if not x:
            return '<td>—</td>'
        t = x.get("trust")
        cls = "good" if (t or 0) >= 70 else "warn" if (t or 0) >= 25 else "bad"
        return (f'<td><b>{x["cloud"]}%</b><br><span class="sp">span {x["spread"]}</span> '
                f'<span class="pill {cls}">{t}%</span></td>')

    rows = ""
    for v in verdicts:
        d = datetime.strptime(v["date"], "%Y-%m-%d")
        rows += (f'<tr><td>{v["night"]}<br><span class="sp">{d:%a %d %b}</span></td>'
                 + cell(v.get("lake")) + cell(v.get("home")) + '</tr>')

    ens = ""
    if lake_e and home_e:
        for label in [v["night"] for v in verdicts]:
            a_, b_ = lake_e["per"].get(label), home_e["per"].get(label)
            w = ' class="win"' if (a_ or 0) >= (b_ or 0) else ''
            w2 = ' class="win"' if (b_ or 0) > (a_ or 0) else ''
            ens += (f'<tr><td>{label}</td><td><span{w}>{a_}%</span></td>'
                    f'<td><span{w2}>{b_}%</span></td></tr>')
        ens += (f'<tr><td><b>at least one</b></td><td><b>{lake_e["any"]}%</b></td>'
                f'<td><b>{home_e["any"]}%</b></td></tr>')

    climo = ""
    if cl and ch:
        climo = (f'<tr><td>30-year rate for these dates</td><td>{cl}%</td>'
                 f'<td>{ch}%</td></tr>')

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Drive north, or stay home?</title><style>{CSS}</style></head><body><div class="wrap">
<div class="eyebrow">local only · {datetime.now():%a %d %b %H:%M}</div>
<h1>Drive north, or stay home?</h1>
<p class="note">The same ensemble, the same core window, run at both places.</p>

<h2>What the models say</h2>
<div class="card"><table>
<thead><tr><th>night</th><th>the lake</th><th>home</th></tr></thead>
<tbody>{rows}</tbody></table>
<p class="note">Cloud in the core window, the spread between sources, and how often a
forecast with that much disagreement lands within 5 points. A wide span means the models
have not committed and the percentage in front of it is one model winning a vote.</p></div>

<h2>Chance of a clear core window</h2>
<div class="card"><table>
<thead><tr><th></th><th>the lake</th><th>home</th></tr></thead>
<tbody>{ens}{climo}</tbody></table>
<p class="note">Pooled ensemble members — {ln} at the lake, {hn} at home.</p></div>

<hr class="rule">
<h2>These columns are not interchangeable</h2>
<div class="card">
<p>The lake is Bortle 2 and home is not. A clear night at home does not replace a clear
night at the lake <em>for the core</em> — it replaces it for everything that does not need a
dark background. You cannot buy a dark sky with clear weather.</p>
<ul class="rules">
<li><b>Lake workable</b> — go. Home never wins that comparison.</li>
<li><b>Lake hopeless on all three</b> — stay. Home is then salvage, not substitute:
shoot what does not need dark.</li>
<li><b>Lake unresolved</b> — the spread is wide and the number in front of it means
little. Wait; it is not a decision yet.</li>
</ul>
</div>
</div></body></html>"""


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
    if "--html" in sys.argv:
        i = sys.argv.index("--html")
        path = (sys.argv[i + 1] if i + 1 < len(sys.argv)
                and not sys.argv[i + 1].startswith("--") else "compare.html")
        open(path, "w").write(page(verdicts, lake_e, home_e, ln, hn, cl, ch))
        print(f"  wrote {path} — open it with file://{__import__('os').path.abspath(path)}")

    if "--json" in sys.argv:
        path = sys.argv[sys.argv.index("--json") + 1]
        json.dump({"taken": datetime.now().isoformat(), "nights": verdicts,
                   "lake_ens": lake_e, "home_ens": home_e,
                   "climo": {"lake": cl, "home": ch}}, open(path, "w"), indent=1)
        print(f"  wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
