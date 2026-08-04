#!/usr/bin/env python3
"""
Render forecast_preview.html from FAKE data, to see what the real page will look
like after several days of logging. Touches nothing real — writes only
forecast_preview.html. Delete it whenever.

    python3 preview_forecast.py

The invented story is a realistic and instructive one: at long range everything
looks mediocre, then as the lead time shortens the nights separate — the pivot
night improves into a clear GO while night 3 deteriorates. That's the shape of
decision you'll actually be making on the 8th.
"""

from datetime import datetime, timedelta
import log_forecast as lf

# core-window cloud cover by snapshot day (Aug 4 → Aug 8). None = outside window.
STORY = {
    "Night 1": [57, 62, 48, 55, 41],
    "Night 2": [None, 66, 54, 47, 24],     # the pivot night converges GOOD
    "Night 3": [None, None, 61, 58, 72],   # deteriorates
    "Lead-up 05": [42, 38, None, None, None],
    "Lead-up 06": [54, 47, 31, None, None],
    "Lead-up 07": [65, 71, 58, 44, None],
    "Lead-up 08": [53, 60, 66, 51, 39],
    "Lead-up 09": [62, 55, 49, 58, 46],
    "Lead-up 10": [64, 58, 63, 49, 55],
}
DAYS = 5


def build():
    hist = []
    base = datetime(2026, 8, 4, 13, 40, tzinfo=lf.EDT)
    for i in range(DAYS):
        taken = base + timedelta(days=i)
        nights = {}
        for label, day in lf.ALL:
            d0 = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=lf.EDT)
            v = STORY.get(label, [None] * DAYS)[i]
            lead = (d0.date() - taken.date()).days
            nights[label] = {"date": day, "lead": lead, "core": v,
                             "dark": None if v is None else min(100, v + 4),
                             "pop": None if v is None else max(0, v - 25),
                             "flat": lead >= 6, "rows": []}
        hist.append({"taken": taken.isoformat(),
                     "grid": "GYX 28,125 (MOCK DATA)", "nights": nights})
    return hist


if __name__ == "__main__":
    lf.PAGE = "forecast_preview.html"
    hist = build()
    lf.write_page(hist)

    # stamp it clearly so it can't be mistaken for the real thing
    s = open(lf.PAGE).read()
    s = s.replace("<h1>Forecast trend</h1>",
        '<h1>Forecast trend</h1>\n'
        '<div style="margin:.6rem 0 0;padding:.7rem .9rem;border:1px solid var(--bad);'
        'border-left:3px solid var(--bad);border-radius:3px;background:var(--surface)">'
        '<b style="color:var(--bad)">MOCK DATA — none of this is a real forecast.</b> '
        '<span style="display:block;margin-top:.2rem;font-size:.9rem">Invented to preview what '
        'the page looks like after five days of logging. The real one is '
        '<a href="forecast.html">forecast.html</a>.</span></div>')
    s = s.replace("<title>Forecast trend", "<title>PREVIEW (mock) — Forecast trend")
    open(lf.PAGE, "w").write(s)
    print(f"wrote {lf.PAGE} — {DAYS} mock snapshots, real data untouched")
