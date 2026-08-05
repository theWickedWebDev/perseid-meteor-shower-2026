#!/usr/bin/env python3
"""
Find point sources in the webcam's night frames, and check whether they move.

    venv/bin/python stars.py            # report on every night frame held
    venv/bin/python stars.py --track    # match sources between consecutive frames

Why this matters: the camera goes monochrome after dark (saturation drops to 0, R/B to
1.00), so the daytime red/blue cloud test is dead at night — confirmed on the first night
frame of 4 Aug. But if stars are visible, their COUNT is a cloud measure that needs no
colour at all, and it is the one the satellite cannot provide: infrared struggles with
exactly the low cloud and fog that would hide stars.

The confounder is that a hot pixel, a sensor artefact or a distant ground light also looks
like a dot. Two things separate them from stars:

  brightness must track darkness — a star is invisible at noon, faint at dusk, obvious at
  full dark. An artefact sits at the same offset in every frame.

  position must change — the sky turns about 15 degrees an hour. An artefact does not move
  at all, and a ground light does not either.

The first test passed on 4 Aug: two sources at (280, 77) and (493, 79) went from under
2 sigma in daylight to 92 and 59 sigma at 21:00. The second needs consecutive night frames.
"""

import glob
import json
import os
import sys
from datetime import datetime

SHOTS = "webcam"
SKY_FRAC = 0.30          # top of frame that is sky rather than treeline and water
MIN_SNR = 5.0
MAX_PX = 40              # bigger than this is a light or a reflection, not a point source
OUT = "stars_log.json"


def sources(path):
    """[(x, y, npix, peak, snr)] for point-like excesses in the sky region."""
    import numpy as np
    from PIL import Image
    from scipy import ndimage as nd

    im = np.asarray(Image.open(path).convert("L")).astype(float)
    H, W = im.shape
    sky = im[0:int(SKY_FRAC * H), :]
    bg = nd.median_filter(sky, size=25)
    res = sky - bg
    sigma = np.median(np.abs(res - np.median(res))) * 1.4826
    if sigma <= 0:
        return [], 0.0, float(im.mean())
    lab, n = nd.label(res > MIN_SNR * sigma)
    out = []
    for i in range(1, n + 1):
        m = lab == i
        npx = int(m.sum())
        if npx > MAX_PX:
            continue
        ys, xs = np.where(m)
        pk = float(res[m].max())
        out.append((float(xs.mean()), float(ys.mean()), npx, pk, pk / sigma))
    out.sort(key=lambda r: -r[4])
    return out, float(sigma), float(im.mean())


def is_night(path):
    import numpy as np
    from PIL import Image
    return np.asarray(Image.open(path).convert("L")).astype(float).mean() < 60


def track(a, b, tol=90):
    """Match sources between two frames by nearest neighbour, and report the shift.

    A star should move; the sky turns ~15 deg/hour, which at any plausible webcam focal
    length is tens of pixels. Anything matching at zero displacement is not on the sky.
    """
    pairs = []
    for x1, y1, _, pk1, s1 in a:
        best, bd = None, 1e9
        for x2, y2, _, pk2, s2 in b:
            d = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** .5
            if d < bd:
                best, bd = (x2, y2, pk2, s2), d
        if best and bd < tol:
            pairs.append(((x1, y1, pk1, s1), best, bd))
    return pairs


def main():
    frames = sorted(glob.glob(f"{SHOTS}/*.jpg"))
    night = [f for f in frames if is_night(f)]
    if not night:
        print("no night frames yet — the camera is still in daylight")
        return 0

    log = {}
    print(f"{len(night)} night frame(s) of {len(frames)}\n")
    for f in night:
        src, sigma, lum = sources(f)
        hh = os.path.basename(f)[11:13]
        log[os.path.basename(f)] = [
            {"x": round(s[0], 1), "y": round(s[1], 1), "px": s[2],
             "peak": round(s[3], 1), "snr": round(s[4], 1)} for s in src[:12]]
        strong = [s for s in src if s[4] >= 20]
        print(f"  {hh}:00  lum {lum:5.1f}  sigma {sigma:4.2f}  "
              f"{len(strong)} source(s) above 20 sigma")
        for x, y, npx, pk, snr in strong[:8]:
            print(f"        ({x:5.0f},{y:5.0f})  {npx:2d} px  peak {pk:6.1f}  {snr:5.1f} sigma")

    if "--track" in sys.argv and len(night) >= 2:
        print("\n  movement between consecutive night frames:")
        for f1, f2 in zip(night, night[1:]):
            a, _, _ = sources(f1)
            b, _, _ = sources(f2)
            a = [s for s in a if s[4] >= 20]
            b = [s for s in b if s[4] >= 20]
            pairs = track(a, b)
            h1, h2 = os.path.basename(f1)[11:13], os.path.basename(f2)[11:13]
            if not pairs:
                print(f"    {h1}:00 -> {h2}:00   no matches within tolerance")
                continue
            for (x1, y1, _, s1), (x2, y2, _, s2), d in pairs:
                verdict = ("FIXED — not on the sky" if d < 3 else
                           "moved — consistent with a star" if d < 90 else "large jump")
                print(f"    {h1}:00 -> {h2}:00   ({x1:5.0f},{y1:5.0f}) -> "
                      f"({x2:5.0f},{y2:5.0f})   {d:5.1f} px   {verdict}")
    elif "--track" in sys.argv:
        print("\n  need a second night frame before movement can be checked")

    json.dump(log, open(OUT, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
