#!/usr/bin/env python3
"""
Score every prediction in predictions/ against what actually happened.

    python3 score_predictions.py            # score against the newest snapshot
    python3 score_predictions.py --at 2026-08-09T21:00
    python3 score_predictions.py --table    # markdown, for pasting into the README

Reads the machine-readable block each prediction ends with — a fenced yaml block holding
the numbers it committed to — and compares them against `forecast_history.json`.

The point is not to crown a winner. The prompt is run several times a day as the trip
approaches, so the useful question is whether error shrinks with lead time. If the 9 Aug
predictions are no better than the 4 Aug ones, the models are not learning from the data
arriving, and that is worth knowing about the exercise itself.

A prediction without the yaml block is listed as unscoreable rather than skipped silently.
"""

import glob
import json
import os
import re
import statistics as st
import sys
from datetime import datetime, timedelta, timezone

import log_forecast as lf

DIR = "predictions"
EDT = timezone(timedelta(hours=-4))
FIELDS = ["night1", "night2", "night3", "spread1", "joint"]


def parse(path):
    """Pull the trailing yaml block out of a prediction. Returns {} if absent."""
    txt = open(path).read()
    blocks = re.findall(r"```ya?ml\s*\n(.*?)```", txt, re.S)
    if not blocks:
        return {}
    out = {}
    for line in blocks[-1].strip().split("\n"):
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip()
        if v.startswith("["):
            out[k] = [int(x) for x in re.findall(r"-?\d+", v)]
        elif re.fullmatch(r"-?\d+", v):
            out[k] = int(v)
        else:
            out[k] = v
    return out


def actual(at=None):
    """What the site really said, at `at` or at the newest snapshot."""
    hist = json.load(open(lf.HIST))
    if at:
        want = datetime.fromisoformat(at) if "T" in at else datetime.fromisoformat(at + "T21:00")
        hist = [e for e in hist
                if datetime.fromisoformat(e["taken"]).replace(tzinfo=None) <= want.replace(tzinfo=None)]
        if not hist:
            return None
    e = hist[-1]
    con = [lf.consensus(e["nights"][l]) for l, _ in lf.NIGHTS]
    t = e.get("trip") or {}
    base = (lf._skill().get("climatology") or {}).get("p_trip_good")
    j = t.get("joint")
    verdict = None
    if j is not None and base is not None:
        d = j - base
        verdict = ("a better draw than these dates usually give" if d >= 10 else
                   "about what these dates normally offer" if d >= -5 else
                   "a worse draw than these dates usually give")
    return {"taken": e["taken"], "night1": con[0][0], "night2": con[1][0],
            "night3": con[2][0], "spread1": con[0][3], "joint": j, "verdict": verdict}


def main():
    at = None
    if "--at" in sys.argv:
        at = sys.argv[sys.argv.index("--at") + 1]
    act = actual(at)
    if not act:
        print("no snapshot at or before that time")
        return 1

    files = sorted(glob.glob(f"{DIR}/2*.md"))
    rows, unscoreable = [], []
    for f in files:
        p = parse(f)
        if not all(k in p for k in FIELDS):
            unscoreable.append((f, sorted(p) or "no yaml block"))
            continue
        errs = {k: abs(p[k] - act[k]) for k in FIELDS if act.get(k) is not None}
        v_ok = None
        if p.get("verdict") and act.get("verdict"):
            v_ok = p["verdict"].strip().lower() in act["verdict"].lower()
        rows.append({"file": os.path.basename(f), "when": p.get("written", "?"),
                     "snaps": p.get("snapshots"), "lead": p.get("lead_days"),
                     "pred": p, "errs": errs,
                     "mae": st.mean(errs.values()) if errs else None, "verdict_ok": v_ok})

    # Predictions are FOR 9 Aug. Scoring them against today's snapshot compares a forecast
    # to a date it was not about, and the resulting error looks authoritative while meaning
    # nothing. Say so rather than printing a confident wrong number.
    TARGET = "2026-08-09"
    taken = act["taken"][:10]
    if taken < TARGET:
        days = (datetime.fromisoformat(TARGET) - datetime.fromisoformat(taken)).days
        print(f"  ⚠  PROVISIONAL — these predictions are for {TARGET}, and the newest")
        print(f"     snapshot is {taken}, {days} day{'s' if days != 1 else ''} early.")
        print(f"     The errors below are 'distance from today', not accuracy.\n")

    print(f"  actual, at snapshot {act['taken'][:16]}")
    print(f"    night1 {act['night1']}%  night2 {act['night2']}%  night3 {act['night3']}%  "
          f"spread1 ±{act['spread1']}  joint {act['joint']}%")
    print(f"    verdict: {act['verdict']}\n")

    if not rows:
        print("  nothing scoreable yet")
    else:
        md = "--table" in sys.argv
        hdr = f"  {'prediction':<22}{'lead':>6}{'N1':>10}{'N2':>10}{'N3':>10}{'joint':>10}{'MAE':>7}{'verdict':>9}"
        print(hdr if not md else
              "| prediction | lead | N1 | N2 | N3 | joint | MAE | verdict |\n|---|---|---|---|---|---|---|---|")
        for r in sorted(rows, key=lambda r: r["when"]):
            def cell(k):
                return f"{r['pred'][k]:>4} ({r['errs'].get(k, 0):+3.0f})"
            lead = r["lead"][0] if isinstance(r["lead"], list) and r["lead"] else "?"
            v = "ok" if r["verdict_ok"] else ("miss" if r["verdict_ok"] is False else "—")
            if md:
                print(f"| {r['file']} | {lead}d | {cell('night1')} | {cell('night2')} | "
                      f"{cell('night3')} | {cell('joint')} | {r['mae']:.1f} | {v} |")
            else:
                print(f"  {r['file']:<22}{str(lead)+'d':>6}{cell('night1'):>10}{cell('night2'):>10}"
                      f"{cell('night3'):>10}{cell('joint'):>10}{r['mae']:>7.1f}{v:>9}")

        # the actual question: does error fall as lead shortens?
        withlead = [(r["lead"][0], r["mae"]) for r in rows
                    if isinstance(r["lead"], list) and r["lead"] and r["mae"] is not None]
        if len(withlead) >= 4:
            xs = [a for a, _ in withlead]
            ys = [b for _, b in withlead]
            mx, my = st.mean(xs), st.mean(ys)
            den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** .5
            if den:
                r_ = sum((x - mx) * (y - my) for x, y in withlead) / den
                print(f"\n  error vs lead time: r = {r_:+.2f}")
                print("  positive means later predictions were more accurate — the models were")
                print("  using the data arriving. Near zero means they were not.")

    # The gaps different models independently identify — repetition ranks them
    gaps = [(os.path.basename(f), parse(f).get("missing"))
            for f in files if parse(f).get("missing")]
    if gaps:
        print(f"\n  what each model said was missing ({len(gaps)} of {len(files)}):")
        for f, g in gaps:
            print(f"    {f[:16]}  {g}")
        words = {}
        for _, g in gaps:
            for w in re.findall(r"[a-z]{5,}", g.lower()):
                words[w] = words.get(w, 0) + 1
        rep = sorted(((c, w) for w, c in words.items() if c > 1), reverse=True)[:6]
        if rep:
            print("    recurring: " + ", ".join(f"{w} ({c})" for c, w in rep))
            print("    a gap several models name independently is worth building")

    if unscoreable:
        print(f"\n  unscoreable ({len(unscoreable)}) — no complete yaml block:")
        for f, keys in unscoreable:
            print(f"    {os.path.basename(f)}  had: {keys}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
