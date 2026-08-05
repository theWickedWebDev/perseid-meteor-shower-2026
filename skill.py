#!/usr/bin/env python3
"""
Two questions the hourly forecast cannot answer, computed once a day and cached.

    python3 skill.py            # refresh skill.json
    python3 skill.py --show     # print it, change nothing

1. IS THIS FORECAST GOOD? Every number on the page is absolute. 45% cloud means nothing
   without knowing that the median for these dates at this site is 72%. Thirty years of
   ERA5 reanalysis gives the base rate, so a forecast can be read as better or worse than
   a normal year rather than as a naked number.

2. DOES WAITING HELP? The trip hinges on deciding a few days out, and the honest answer
   turned out to be "only up to a point". Model error against satellite truth falls hard
   between 7 and 5 days out and is then flat — from 3 days to same-day it improves by
   about one point. That is worth knowing before agreeing a decision date with someone.

Both are slow — thirty archive calls and seven previous-run calls — and neither moves on
an hourly timescale, so they are cached to skill.json and the page just reads that.
Nothing here is on the critical path: if the file is missing the page omits the sections.
"""

import json
import os
import random
import statistics as st
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

SITE = (45.2393, -71.1964)
EDT = timezone(timedelta(hours=-4))
OUT = "skill.json"
UA = {"User-Agent": "perseid-meteor-shower-2026"}

CORE_HR = (22, 23)
GO = 30

# Climatology must weight the core window exactly as the ensemble does, or the base rate
# is not comparable with the forecast it is the yardstick for — unweighted it reads 67%,
# weighted 70%, and the page compares the two directly.
#
# Imported rather than restated. The weights derive from the core-set times in
# schedule_data.ASTRO, which is verified against the ephemeris at import; a second copy
# here would silently desynchronise the moment the treeline is re-measured on arrival.
def _core_weights(month_day):
    from log_forecast import core_weights
    return core_weights(f"2026-08-{month_day:02d}")
TRIP_NIGHTS = (11, 12, 13)          # August
CLIMO_YEARS = range(1996, 2026)     # thirty full Augusts

MODELS = [("ecmwf_ifs025", "ECMWF"), ("gfs_seamless", "GFS"), ("icon_seamless", "ICON"),
          ("gem_seamless", "GEM"), ("ecmwf_aifs025_single", "AIFS"), ("jma_gsm", "JMA"),
          ("ukmo_global_deterministic_10km", "UKMO")]


def get(url, timeout=90):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                            timeout=timeout))


# ── 1. climatology ───────────────────────────────────────────────────────
def climatology():
    """Base rate for the trip nights from ERA5, 1996-2025.

    ERA5 is reanalysis rather than observation — a model assimilating what was measured —
    and at ~25 km it can smooth away a local deck. Checked against the GOES readings it
    agreed within 10 points on 73% of hours but once read 23% against the satellite's 99%.
    Good enough for thirty-year statistics; not a substitute for looking at tonight.
    """
    by_year = {}
    for y in CLIMO_YEARS:
        url = (f"https://archive-api.open-meteo.com/v1/archive?latitude={SITE[0]}"
               f"&longitude={SITE[1]}&start_date={y}-08-{TRIP_NIGHTS[0]:02d}"
               f"&end_date={y}-08-{TRIP_NIGHTS[-1] + 1:02d}"
               f"&hourly=cloud_cover&timezone=America%2FNew_York")
        try:
            h = get(url)["hourly"]
        except Exception as ex:
            print(f"  {y}: {str(ex)[:60]}")
            continue
        idx = {t: i for i, t in enumerate(h["time"])}
        for d in TRIP_NIGHTS:
            w = _core_weights(d)
            vals, wts = [], []
            for x in CORE_HR:
                k = f"{y}-08-{d:02d}T{x:02d}:00"
                if k in idx and h["cloud_cover"][idx[k]] is not None and w.get(x):
                    vals.append(h["cloud_cover"][idx[k]]); wts.append(w[x])
            if vals:
                by_year.setdefault(y, {})[d] = sum(v * q for v, q in zip(vals, wts)) / sum(wts)
    if not by_year:
        return None
    allv = [v for nights in by_year.values() for v in nights.values()]
    # Per-calendar-date climatology is deliberately NOT computed. It looked meaningful —
    # Aug 11 median 73%, Aug 12 48%, Aug 13 68% — but adjacent calendar dates cannot differ
    # by 25 points for any physical reason, and resampling one pooled distribution produces
    # a gap that large 34% of the time. With n=30 and a standard deviation near 37 points
    # it is sampling noise wearing a table, and it would eventually be read as signal.
    trip_ok = sum(1 for n in by_year.values() if any(v < GO for v in n.values()))

    # The independence bound for the REAL years, so the near-independence claim in the
    # findings doc can be regenerated from the repo instead of living only in prose.
    ind = 1.0
    for d in TRIP_NIGHTS:
        vals = [n[d] for n in by_year.values() if d in n]
        if vals:
            ind *= (1 - sum(1 for v in vals if v < GO) / len(vals))
    return {"years": len(by_year), "median": round(st.median(allv)),
            "p_night_good": round(100 * sum(1 for v in allv if v < GO) / len(allv)),
            "p_trip_good": round(100 * trip_ok / len(by_year)),
            "p_trip_indep": round(100 * (1 - ind)),
            "weighted": True,
            "window": f"Aug {TRIP_NIGHTS[0]}-{TRIP_NIGHTS[-1]}"}


# ── 2. does waiting help ─────────────────────────────────────────────────
def truth_hours(satlog, region="dome"):
    """{hour_iso: observed cloud} from the satellite log, night hours only.

    `region="dome"` is the 34 km box overhead — what the models have always been scored
    against. `region="slot"` is the southern fan the trip's targets actually occupy, which
    satellite.py already banks at no extra cost.

    Scoring on the dome answers "was the sky cloudy". Scoring on the slot answers "was the
    shot possible", and those are different questions on any night with structure. If the
    two rankings agree the compass is decoration; if they disagree, every skill number on
    the page has been measuring the wrong quantity.
    """
    out = {}
    for e in satlog:
        if region == "slot":
            sl = e.get("slot") or {}
            v = [sl[k] for k in ("near", "mid") if sl.get(k) is not None]
            v = sum(v) / len(v) if v else None
        else:
            v = e.get("cloud")
        if v is None:
            continue
        t = datetime.fromisoformat(e["time"])
        if t.hour >= 21 or t.hour <= 4:
            out[e["time"][:13] + ":00"] = v
    return out


def _episodes(hours):
    """Group verified hours into contiguous nights.

    The unit of independent information is a night, not an hour. Cloud at 02:00 is nearly
    the same draw as cloud at 01:00, and seven models scoring the same hour are not seven
    observations either. Resampling by episode is what stops 357 correlated numbers being
    reported as though they were 357 independent ones.
    """
    ts = sorted(datetime.fromisoformat(h) for h in hours)
    if not ts:
        return []
    eps, cur = [], [ts[0]]
    for a_, b_ in zip(ts, ts[1:]):
        if (b_ - a_).total_seconds() > 4 * 3600:
            eps.append(cur); cur = [b_]
        else:
            cur.append(b_)
    eps.append(cur)
    return [[t.strftime("%Y-%m-%dT%H:00") for t in e] for e in eps]


def _baselines(truth, climo_median=None):
    """What a forecaster with no skill would score. Context for the model numbers.

    A week that was overcast most nights makes 'always 100%' look good, so a model beating
    it by three points is barely doing anything. Without this the skill table flatters.
    """
    v = list(truth.values())
    if not v:
        return {}
    # Baseline against the CURRENT climatological median, not a literal. It was hardcoded
    # at 72, the unweighted median, which stopped being right the moment the window was
    # weighted — and the correct value makes the baseline worse, which strengthens rather
    # than weakens the point this table exists to make.
    med = climo_median if climo_median is not None else round(st.mean(v))
    out = {"always_overcast": round(st.mean([abs(100 - x) for x in v]), 1),
           "always_climatology": round(st.mean([abs(med - x) for x in v]), 1),
           "climatology_value": med,
           "truth_mean": round(st.mean(v))}
    nights = {}
    for k, x in truth.items():
        d = datetime.fromisoformat(k)
        key = (d if d.hour >= 21 else d - timedelta(days=1)).date()
        nights.setdefault(key, []).append(x)
    ks = sorted(nights)
    pe = [abs(st.mean(nights[a]) - x) for a, b in zip(ks, ks[1:]) for x in nights[b]]
    if pe:
        out["persistence"] = round(st.mean(pe), 1)
    return out


def lead_skill(satlog, climo_median=None, region="dome"):
    """Mean absolute error against the satellite, by how far ahead the forecast was made.

    Uses Open-Meteo's previous-runs archive: for each hour it exposes what the model said
    1..7 days earlier. Comparing those against what the satellite actually saw gives the
    honest shape of "does another day of waiting buy me anything".
    """
    truth = truth_hours(satlog, region)
    if len(truth) < 6:
        return None
    varlist = ",".join(["cloud_cover"] + [f"cloud_cover_previous_day{i}" for i in range(1, 8)])
    per_lead, per_model = {}, {}
    per_hour_lead, pred_by_model = {}, {}
    for key, name in MODELS:
        url = (f"https://previous-runs-api.open-meteo.com/v1/forecast?latitude={SITE[0]}"
               f"&longitude={SITE[1]}&hourly={varlist}&models={key}&forecast_days=2"
               f"&past_days=7&timezone=America%2FNew_York")
        try:
            h = get(url)["hourly"]
        except Exception:
            continue
        idx = {t: i for i, t in enumerate(h["time"])}
        for hour, actual in truth.items():
            i = idx.get(hour)
            if i is None:
                continue
            for lead in range(8):
                col = "cloud_cover" if lead == 0 else f"cloud_cover_previous_day{lead}"
                series = h.get(col) or []
                if i >= len(series) or series[i] is None:
                    continue
                err = abs(series[i] - actual)
                per_lead.setdefault(lead, []).append(err)
                per_model.setdefault(name, {}).setdefault(lead, []).append(err)
                per_hour_lead.setdefault((hour, lead), []).append(err)
                if lead <= 2:
                    pred_by_model.setdefault(name, []).append(series[i])
    if not per_lead:
        return None

    # Bootstrap over nights so the reported uncertainty reflects the real sample size.
    # Without it the curve invited conclusions it could not support: 1 day out appeared to
    # beat the night itself by 5 points, which is impossible and sets the noise floor.
    eps = _episodes(truth)
    rng = random.Random(20260804)
    by_ep = {}
    for (hour, lead), errs in per_hour_lead.items():
        by_ep.setdefault(lead, {}).setdefault(hour, []).extend(errs)

    def mean_for(lead, keys):
        v = [e for k in keys for e in by_ep.get(lead, {}).get(k, [])]
        return st.mean(v) if v else None

    ci, boots_by_lead = {}, {}
    for lead in sorted(per_lead):
        draws = []
        for _ in range(2000):
            pick = [eps[rng.randrange(len(eps))] for _ in range(len(eps))]
            m = mean_for(lead, [k for ks in pick for k in ks])
            if m is not None:
                draws.append(m)
        draws.sort()
        boots_by_lead[lead] = draws
        if draws:
            ci[lead] = (round(draws[int(.025 * len(draws))], 1),
                        round(draws[int(.975 * len(draws))], 1))

    # is a given improvement bigger than the noise?
    def diff_ci(a_, b_):
        draws = []
        for _ in range(2000):
            pick = [eps[rng.randrange(len(eps))] for _ in range(len(eps))]
            ks = [k for ks in pick for k in ks]
            ma, mb = mean_for(a_, ks), mean_for(b_, ks)
            if ma is not None and mb is not None:
                draws.append(ma - mb)
        if not draws:
            return None
        draws.sort()
        lo, hi = draws[int(.025 * len(draws))], draws[int(.975 * len(draws))]
        return {"delta": round(st.mean(draws), 1), "lo": round(lo, 1), "hi": round(hi, 1),
                "significant": bool(lo > 0 or hi < 0)}

    # pessimism confound: on an overcast week the gloomiest model wins on error alone
    mean_pred = {m: round(st.mean(v)) for m, v in pred_by_model.items() if v}
    def _bias():
        # No [0] default. Injecting a zero error for a model missing lead-0 data would
        # flatter exactly the model that lost its feed, and it would do so inside the one
        # statistic whose job is detecting bias.
        pairs = [(mean_pred[m], st.mean(e)) for m in mean_pred
                 if (e := per_model[m].get(0, []) + per_model[m].get(1, []))]
        if len(pairs) < 4:
            return None
        xs = [a_ for a_, _ in pairs]
        ys = [b_ for _, b_ in pairs]
        mx, my = st.mean(xs), st.mean(ys)
        den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** .5
        return round(sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den, 2) if den else None

    bias_r = _bias()

    return {
        "n_hours": len(truth),
        "n_episodes": len(eps),
        "by_lead": {str(k): {"mean": round(st.mean(v), 1),
                             "median": round(st.median(v), 1), "n": len(v),
                             "lo": ci.get(k, (None, None))[0],
                             "hi": ci.get(k, (None, None))[1]}
                    for k, v in sorted(per_lead.items())},
        "by_model": {m: {str(k): round(st.mean(v)) for k, v in sorted(d.items())}
                     for m, d in per_model.items()},
        "mean_forecast": mean_pred,
        "pessimism_r": bias_r,
        "baselines": _baselines(truth, climo_median),
        "diffs": {"7_3": diff_ci(7, 3), "3_0": diff_ci(3, 0), "1_0": diff_ci(1, 0)},
    }


def verification(days=92):
    """How wrong the forecast typically is at each lead, and what a bad forecast is worth.

    `lead_skill` above scores against the satellite, which is the right reference but limits
    the sample to however many hours the satellite log covers — currently a handful of night
    episodes, which is why its error bars are wide. This function trades reference quality
    for sample size: it scores each model's day-N forecast against that model's own day-0
    value for the same hour, across three months. That is verification against an analysis
    rather than an observation, so it measures how much a forecast MOVES between issue and
    arrival rather than how wrong it finally is. Those are not the same quantity and the page
    must say so.

    Two outputs:

      by_lead  - percentiles of absolute error, so the page can say "half the time within
                 X points, nine times in ten within Y" instead of quoting a mean that a
                 skewed distribution makes meaningless.

      given    - the conditional question, which is the one actually asked while staring at a
                 bad number: when the forecast said this at six or seven days out, how often
                 did the night turn out fine anyway?
    """
    var = ",".join(["cloud_cover"] + [f"cloud_cover_previous_day{i}" for i in range(1, 8)])
    pairs = {}          # lead -> [(forecast, reference), ...]
    for key, name in MODELS:
        url = (f"https://previous-runs-api.open-meteo.com/v1/forecast?latitude={SITE[0]}"
               f"&longitude={SITE[1]}&hourly={var}&models={key}&past_days={days}"
               f"&forecast_days=1&timezone=America%2FNew_York")
        try:
            h = get(url)["hourly"]
        except Exception:
            continue
        ref = h.get("cloud_cover") or []
        for lead in range(1, 8):
            series = h.get(f"cloud_cover_previous_day{lead}") or []
            for i, t in enumerate(h["time"]):
                if int(t[11:13]) not in CORE_HR:
                    continue
                if i >= len(series) or series[i] is None or ref[i] is None:
                    continue
                pairs.setdefault(lead, []).append((series[i], ref[i]))
    if not pairs:
        return None

    def pct(v, q):
        v = sorted(v)
        return round(v[min(len(v) - 1, int(q * len(v)))])

    by_lead = {}
    for lead, ps in sorted(pairs.items()):
        errs = [abs(f - a) for f, a in ps]
        by_lead[str(lead)] = {"n": len(errs), "p50": pct(errs, .50),
                              "p80": pct(errs, .80), "p90": pct(errs, .90),
                              "mean": round(st.mean(errs), 1)}

    # The conditional table. Pooled over leads 6 and 7 — that is the range where the number
    # looks alarming and the honest answer is a base rate rather than a forecast.
    far = [p for lead in (6, 7) for p in pairs.get(lead, [])]
    given = None
    if len(far) >= 40:
        bad = [a for f, a in far if f >= 80]
        good = [a for f, a in far if f <= 20]
        given = {"leads": "6-7", "n": len(far)}
        if bad:
            given["said_bad"] = {
                "n": len(bad), "median_actual": round(st.median(bad)),
                "recovered_go": round(sum(1 for a in bad if a <= GO) / len(bad) * 100),
                "recovered_55": round(sum(1 for a in bad if a <= 55) / len(bad) * 100)}
        if good:
            given["said_good"] = {
                "n": len(good), "median_actual": round(st.median(good)),
                "collapsed_55": round(sum(1 for a in good if a > 55) / len(good) * 100)}
    # The percentile table says how far off the forecast was. It never says how often it was
    # RIGHT, which is the question anyone actually has. A cloud percentage only ever drives
    # one decision — go or do not go — so score that decision directly.
    calls, base = {}, {}
    for lead, ps in sorted(pairs.items()):
        ok = sum(1 for f, a in ps if (f <= GO) == (a <= GO))
        calls[str(lead)] = {"right": round(ok / len(ps) * 100), "n": len(ps)}
    allp = [p for ps in pairs.values() for p in ps]
    if allp:
        acts = [a for _, a in allp]
        # Two baselines, and the second matters more. Most nights here are not GO, so a
        # predictor that always says "cloudy" scores well above a coin flip while knowing
        # nothing. Quoting only the coin flip would flatter the forecast.
        base["coin"] = 50
        base["always_no_go"] = round(sum(1 for a in acts if a > GO) / len(acts) * 100)
        base["climatology_median"] = round(st.median(acts))

    return {"by_lead": by_lead, "given": given, "days": days, "calls": calls,
            "baselines": base, "go": GO,
            "reference": "each model's own day-0 value for the same hour"}


def main():
    if "--show" in sys.argv:
        print(json.dumps(json.load(open(OUT)), indent=1) if os.path.exists(OUT)
              else f"{OUT} not written yet")
        return 0
    try:
        satlog = json.load(open("satellite_log.json"))
    except Exception:
        satlog = []
    out = {"computed": datetime.now(EDT).isoformat()}
    print("climatology...")
    out["climatology"] = climatology()
    print("lead-time skill...")
    med = (out.get("climatology") or {}).get("median")
    out["lead_skill"] = lead_skill(satlog, med)
    # The same measurement against the southern slot rather than the whole dome. If the
    # model ranking differs between them, the dome numbers are answering the wrong question.
    out["lead_skill_slot"] = lead_skill(satlog, med, region="slot")
    print("verification (92 days of previous runs)...")
    out["verification"] = verification()
    json.dump(out, open(OUT, "w"), indent=1)

    c, s = out["climatology"], out["lead_skill"]
    if c:
        print(f"  climatology: {c['years']} yrs, median {c['median']}%, "
              f"trip base rate {c['p_trip_good']}%")
    if s:
        b = s["by_lead"]
        print(f"  skill: {s['n_hours']} verified hours, "
              f"7d {b.get('7', {}).get('mean')} -> 3d {b.get('3', {}).get('mean')} "
              f"-> 0d {b.get('0', {}).get('mean')} mean error")
    return 0


if __name__ == "__main__":
    sys.exit(main())
