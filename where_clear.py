#!/usr/bin/env python3
"""
Where in the northeast are the trip nights actually clear?

    python3 where_clear.py --lat 42.x --lon -71.x            # search, print a table
    python3 where_clear.py --lat 42.x --lon -71.x --html where.html

Grid-searches the region for the three trip nights and ranks by how clear the core window
looks, so a fixed plan can be checked against the alternative of driving somewhere else.

The premise: a Bortle 4 site under clear sky beats Bortle 2 under overcast, every time. Cloud
is the binding constraint and darkness is the one you optimise second — but only second, and
this tool cannot see darkness at all. It ranks weather and nothing else. Everything it
returns must be checked against a light-pollution map before it means anything.

Open-Meteo accepts comma-separated coordinates, so a whole grid costs one request per model.
Home coordinates are an argument and are used only to compute distances; nothing is written.
"""

import json
import math
import statistics as st
import sys
import time
from datetime import datetime

import log_forecast as lf

# The northeast, coarsely. Far enough west for the Adirondacks, north for the Eastern
# Townships, east for Maine — all inside a day's drive of southern New England.
LAT0, LAT1, LON0, LON1, STEP = 42.0, 47.5, -74.0, -67.0, 0.5
# --wide widens it to everything inside a long day's drive of southern New England:
# eastern NY and the Catskills, the Adirondacks, Vermont, the Berkshires, Long Island,
# the Jersey shore, and the Maine coast as far as Bar Harbour.
WIDE = (40.5, 46.5, -76.0, -67.0, 0.5)
MODELS = [("ecmwf_ifs025", "ECMWF"), ("gfs_seamless", "GFS"),
          ("icon_seamless", "ICON"), ("gem_seamless", "GEM")]
BATCH = 120          # coordinates per request
PAUSE = 6            # seconds between requests; the free tier rate-limits hard


def grid():
    global LAT0, LAT1, LON0, LON1
    if "--wide" in sys.argv:
        LAT0, LAT1, LON0, LON1, _ = WIDE
    pts, la = [], LAT0
    while la <= LAT1 + 1e-9:
        lo = LON0
        while lo <= LON1 + 1e-9:
            pts.append((round(la, 2), round(lo, 2)))
            lo += STEP
        la += STEP
    return pts


def km(a, b, c, d):
    """Great-circle. Road distance is worse; this is a floor, not an estimate."""
    p = math.pi / 180
    h = (0.5 - math.cos((c - a) * p) / 2
         + math.cos(a * p) * math.cos(c * p) * (1 - math.cos((d - b) * p)) / 2)
    return 12742 * math.asin(math.sqrt(h))


def fetch(pts):
    """{(lat,lon): {night: [per-model cloud]}} — one request per model per batch."""
    out = {}
    for key, name in MODELS:
        for i in range(0, len(pts), BATCH):
            chunk = pts[i:i + BATCH]
            url = ("https://api.open-meteo.com/v1/forecast?"
                   + "latitude=" + ",".join(str(a) for a, _ in chunk)
                   + "&longitude=" + ",".join(str(b) for _, b in chunk)
                   + f"&hourly=cloud_cover&models={key}&forecast_days=14"
                   + "&timezone=America%2FNew_York")
            res = None
            for attempt in range(5):
                try:
                    res = lf.get(url)
                    break
                except Exception as ex:
                    if attempt == 4:
                        print(f"  {name} batch {i//BATCH}: {str(ex)[:60]}", flush=True)
                    else:
                        # 429 is the usual one. Without this the batch silently drops a
                        # model, cells end up with fewer members, and the spread across
                        # two models gets read as agreement across four.
                        time.sleep(12 * (attempt + 1))
            if res is None:
                continue
            time.sleep(PAUSE)
            if isinstance(res, dict):
                res = [res]
            for pt, r in zip(chunk, res):
                h = r.get("hourly") or {}
                col = next((k for k in h if k.startswith("cloud_cover")), None)
                if not col:
                    continue
                idx = {t: j for j, t in enumerate(h["time"])}
                for label, day in lf.NIGHTS:
                    w = lf.core_weights(day)
                    vals, wts = [], []
                    for hh, wt in w.items():
                        j = idx.get(f"{day}T{hh:02d}:00")
                        if j is not None and h[col][j] is not None:
                            vals.append(h[col][j]); wts.append(wt)
                    mv = lf.wmean(vals, wts)
                    if mv is not None:
                        out.setdefault(pt, {}).setdefault(label, []).append(mv)
        print(f"  {name} done", flush=True)
    return out


def score(raw, home):
    """Cells where a model dropped out are discarded, not scored.

    A batch request that fails for one model leaves that cell with fewer members, and the
    spread across two models is not comparable to the spread across four — a cell with a
    single model has a spread of ZERO and sorts to the top of any ranking by agreement.
    That is how a rate-limited batch turns into "the models agree completely here", which
    is the most dangerous possible failure for a tool whose whole job is to say when the
    forecast can be trusted. Require the full set or drop the cell.
    """
    want = len(MODELS)
    rows, thin = [], 0
    for (la, lo), nights in raw.items():
        if len(nights) < len(lf.NIGHTS):
            continue
        if any(len(nights[l]) < want for l, _ in lf.NIGHTS):
            thin += 1
            continue
        per = {}
        for label, _ in lf.NIGHTS:
            v = nights[label]
            per[label] = {"cloud": round(st.median(v)),
                          "spread": round(max(v) - min(v)), "n": len(v)}
        best = min(per.values(), key=lambda x: x["cloud"])
        rows.append({
            "lat": la, "lon": lo,
            "per": per,
            "best_night": min(per, key=lambda k: per[k]["cloud"]),
            "best_cloud": best["cloud"],
            "best_spread": best["spread"],
            # the whole trip, not one night: how many of the three are workable
            "workable": sum(1 for x in per.values() if x["cloud"] <= lf.GO),
            "mean_cloud": round(st.mean(x["cloud"] for x in per.values())),
            "km_home": round(km(home[0], home[1], la, lo)),
            "km_lake": round(km(lf.SITE[1], lf.SITE[2], la, lo)),
        })
    if thin:
        print(f"  dropped {thin} cells that did not get all {want} models")
    return rows


def main():
    if "--lat" not in sys.argv or "--lon" not in sys.argv:
        print("  need --lat and --lon (home, for distances)")
        return 1
    home = (float(sys.argv[sys.argv.index("--lat") + 1]),
            float(sys.argv[sys.argv.index("--lon") + 1]))
    pts = grid()
    print(f"  {len(pts)} grid points, {LAT0}–{LAT1}N {LON0}–{LON1}W at {STEP}°", flush=True)
    raw = fetch(pts)
    rows = score(raw, home)
    if not rows:
        print("  nothing returned")
        return 1

    lake = min(rows, key=lambda r: r["km_lake"])
    print(f"\n  the lake for reference: {lake['mean_cloud']}% mean, "
          f"{lake['workable']}/3 nights workable\n")

    # Ranked by how much of the trip survives, then by how clear the best night is
    # --night N ranks on one night only; --within KM drops anything further from home.
    if "--within" in sys.argv:
        lim = float(sys.argv[sys.argv.index("--within") + 1])
        before = len(rows)
        rows = [r for r in rows if r["km_home"] <= lim]
        print(f"  {len(rows)} of {before} inside {lim:.0f} km straight-line of home\n")
    if "--night" in sys.argv:
        n = int(sys.argv[sys.argv.index("--night") + 1])
        label = lf.NIGHTS[n - 1][0]
        rows = [r for r in rows if label in r["per"]]
        rows.sort(key=lambda r: (r["per"][label]["cloud"], r["per"][label]["spread"]))
        print(f"  RANKED ON {label} ONLY — {lf.NIGHTS[n-1][1]}\n")
        print(f"  {'lat':>6}{'lon':>8}{'cloud':>8}{'span':>7}{'trust':>7}{'home':>7}")
        print("  " + "-"*45)
        for r in rows[:20]:
            c = r["per"][label]
            ab = lf.agree_band(c["spread"])
            print(f"  {r['lat']:>6}{r['lon']:>8}{c['cloud']:>7}%{c['spread']:>7}"
                  f"{(str(ab[0])+'%') if ab else '—':>7}{r['km_home']:>6}k")
        print(f"\n  Cells over open water are not filtered — the distance test knows "
              f"nothing about land.")
        return 0
    rows.sort(key=lambda r: (-r["workable"], r["mean_cloud"]))
    print(f"  BEST OF {len(rows)} LOCATIONS\n")
    print(f"  {'lat':>6}{'lon':>8}{'mean':>7}{'ok':>4}"
          + "".join(f"{l.replace('Night ','N'):>7}" for l, _ in lf.NIGHTS)
          + f"{'home':>7}{'lake':>7}")
    print("  " + "-"*60)
    for r in rows[:18]:
        cells = "".join(f"{r['per'][l]['cloud']:>6}%" for l, _ in lf.NIGHTS)
        print(f"  {r['lat']:>6}{r['lon']:>8}{r['mean_cloud']:>6}%{r['workable']:>4}"
              f"{cells}{r['km_home']:>6}k{r['km_lake']:>6}k")

    print(f"\n  WORST\n")
    for r in rows[-5:]:
        print(f"  {r['lat']:>6}{r['lon']:>8}{r['mean_cloud']:>6}%{r['workable']:>4}")

    print(f"""
  CAVEATS THAT MATTER MORE THAN THE RANKING

  This ranks weather and cannot see darkness. Several of the clearest cells will be
  over cities, water, or somewhere with no legal place to stand at 1 AM. Check every
  candidate against a light-pollution map and a road atlas before it means anything.

  Distances are great-circle. Real driving is worse, often much worse in this terrain.

  At {lf.NIGHTS[0][1]} the lead is still long enough that these fields will reshuffle. A cell
  that looks clear today is a cell whose models happened to agree today.
""")
    if "--html" in sys.argv:
        i = sys.argv.index("--html")
        path = (sys.argv[i + 1] if i + 1 < len(sys.argv)
                and not sys.argv[i + 1].startswith("--") else "where.html")
        open(path, "w").write(page(rows, lake))
        print(f"  wrote {path}")
    return 0


def page(rows, lake):
    """Local map-ish page: the grid as a coloured field, plus the ranked table."""
    lats = sorted({r["lat"] for r in rows}, reverse=True)
    lons = sorted({r["lon"] for r in rows})
    by = {(r["lat"], r["lon"]): r for r in rows}

    def band(c):
        return ("g" if c <= 20 else "g2" if c <= lf.GO else
                "w" if c <= 55 else "b" if c <= 75 else "b2")

    grids = ""
    for label, day in lf.NIGHTS:
        cells = ""
        for la in lats:
            for lo in lons:
                r = by.get((la, lo))
                if not r:
                    cells += '<i class="x"></i>'; continue
                c = r["per"][label]["cloud"]
                mark = " me" if r is lake else ""
                cells += (f'<i class="{band(c)}{mark}" title="{la}, {lo} — {c}% cloud, '
                          f'spread {r["per"][label]["spread"]}"></i>')
        d = datetime.strptime(day, "%Y-%m-%d")
        grids += (f'<div class="gwrap"><h3>{label} · {d:%a %d %b}</h3>'
                  f'<div class="grid" style="grid-template-columns:repeat({len(lons)},1fr)">'
                  f'{cells}</div></div>')

    trs = ""
    for r in rows[:20]:
        trs += (f'<tr><td>{r["lat"]}, {r["lon"]}</td><td>{r["mean_cloud"]}%</td>'
                f'<td>{r["workable"]}/3</td>'
                + "".join(f'<td>{r["per"][l]["cloud"]}%</td>' for l, _ in lf.NIGHTS)
                + f'<td>{r["km_home"]} km</td><td>{r["km_lake"]} km</td></tr>')

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Where is it clear?</title><style>
:root{{--bg:#F1F3F7;--surface:#fff;--ink:#171C26;--body:#3B4453;--muted:#6C7789;
 --rule:#DDE2EA;--mono:ui-monospace,Menlo,monospace}}
@media(prefers-color-scheme:dark){{:root{{--bg:#0A0D14;--surface:#121722;--ink:#E7ECF5;
 --body:#BAC4D4;--muted:#7A8698;--rule:#242C3A}}}}
body{{margin:0;padding:2rem 1.2rem 4rem;background:var(--bg);color:var(--body);
 font:16px/1.6 ui-sans-serif,system-ui,sans-serif}}
.wrap{{max-width:52rem;margin:0 auto}}
h1{{color:var(--ink);font-size:1.6rem;margin:0 0 .2rem}}
h2{{color:var(--ink);font-size:1.05rem;margin:2rem 0 .6rem}}
h3{{color:var(--ink);font-size:.8rem;font-family:var(--mono);font-weight:600;
 letter-spacing:.06em;margin:0 0 .4rem}}
.eyebrow{{font-family:var(--mono);font-size:.62rem;letter-spacing:.14em;
 text-transform:uppercase;color:var(--muted)}}
.card{{background:var(--surface);border:1px solid var(--rule);border-radius:5px;
 padding:1rem 1.1rem;margin:.8rem 0}}
.maps{{display:flex;gap:1.1rem;flex-wrap:wrap}}
.gwrap{{flex:1 1 15rem}}
.grid{{display:grid;gap:1px}}
.grid i{{aspect-ratio:1;border-radius:1px;display:block}}
.g{{background:#1E7A4F}} .g2{{background:#6FBF8E}} .w{{background:#E0B15C}}
.b{{background:#C97A63}} .b2{{background:#8C3A2C}} .x{{background:var(--rule)}}
.me{{outline:2px solid var(--ink);outline-offset:-1px;z-index:2;position:relative}}
table{{width:100%;border-collapse:collapse;font-size:.82rem;font-family:var(--mono)}}
th{{font-size:.58rem;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);
 text-align:right;padding:.3rem;font-weight:400}}
th:first-child,td:first-child{{text-align:left}}
td{{padding:.34rem .3rem;border-top:1px solid var(--rule);text-align:right;
 font-variant-numeric:tabular-nums}}
.note{{color:var(--muted);font-size:.85rem}}
.key{{display:flex;gap:.8rem;flex-wrap:wrap;font-family:var(--mono);font-size:.62rem;
 color:var(--muted);margin-top:.7rem}}
.key span{{display:flex;align-items:center;gap:.3rem}}
.key i{{width:11px;height:11px;border-radius:2px;display:block}}
</style></head><body><div class="wrap">
<div class="eyebrow">local only · {datetime.now():%a %d %b %H:%M}</div>
<h1>Where is it clear?</h1>
<p class="note">Median of {len(MODELS)} models over the core window. North is up, west is
left; the outlined cell is the lake.</p>
<div class="card"><div class="maps">{grids}</div>
<div class="key"><span><i class="g"></i>0–20%</span><span><i class="g2"></i>21–30%</span>
<span><i class="w"></i>31–55%</span><span><i class="b"></i>56–75%</span>
<span><i class="b2"></i>76–100%</span></div></div>

<h2>Ranked</h2>
<div class="card"><table><thead><tr><th>location</th><th>mean</th><th>ok</th>
{''.join(f'<th>{l.replace("Night ","N")}</th>' for l, _ in lf.NIGHTS)}
<th>home</th><th>lake</th></tr></thead><tbody>{trs}</tbody></table></div>

<h2>Before this means anything</h2>
<div class="card"><p>This ranks <b>weather only</b>. It cannot see light pollution, roads,
water, or whether there is anywhere legal to stand at 1 AM. Check every candidate against a
light-pollution map and a road atlas.</p>
<p class="note">Distances are great-circle and real driving is worse. And at this lead the
field reshuffles daily — a cell that looks clear today is one whose models happened to agree
today.</p></div>
</div></body></html>"""


if __name__ == "__main__":
    sys.exit(main())
