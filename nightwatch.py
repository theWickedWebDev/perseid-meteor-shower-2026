#!/usr/bin/env python3
"""
Count stars in the webcam's view of YOUR targets, all night.

    venv/bin/python nightwatch.py --once      # one capture now
    venv/bin/python nightwatch.py --loop      # every 30 min until dawn

The camera at Lopstick looks at bearing 178.5 deg with a 94 deg field, and every target of
the trip falls inside it: the Milky Way core at 16 deg altitude, Rho Ophiuchi at 19, M8 and
M20 at 20-22. Same low southern sky the whole trip depends on, from 16.6 km away.

So this is not a generic cloud check. It asks the actual question — can the core be seen
right now — and it covers exactly the case the satellite is worst at, because infrared
struggles with the low cloud whose tops sit near ground temperature, and low cloud is
precisely what blocks a target at 16 degrees.

Method, in the order it matters:

  1080p, not 720p. Twice the pixels and twice the bitrate; faint stars live or die on it.
  30 seconds at 2 fps, then keep only the least-compressed frames. YouTube's predicted
    frames are mush — detection counts swing from 19 to 2 between consecutive frames — and
    median-stacking the clean ones roughly halves the noise.
  A sky mask built from daylight frames. Without it, reflections off the road and treetop
    edges get counted as stars.

Everything here was calibrated against the night of 4 Aug 2026, the only fully dark night
available before the trip.
"""

import glob
import json
import math
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone

STREAM = "https://www.youtube.com/watch?v=wNxk-XC8Z5s"
EDT = timezone(timedelta(hours=-4))
LOG = "nightwatch_log.json"
SHOTS = "nightwatch"     # stacked frames kept as evidence, one per capture
MASK = "skymask.npy"
SECONDS = 30
FPS = 2
KEEP_BEST = 30          # least-compressed frames to stack
SNR = 6.0

# From the plate solve of 4 Aug. Pixel positions are for 1920x1080.
SOLVE = {"bearing": 178.5, "pitch": -3.0, "fov": 94, "roll": -3.0}
WEBCAM = (45.10367, -71.28616)
W, H = 1920, 1080

# The regions worth counting separately, in the camera's own pixel space. A radius of
# 220 px is about 11 degrees at this plate scale — generous enough to hold the target
# and its surroundings, tight enough that cloud elsewhere does not dilute it.
TARGETS = [("core", "17h45m40s", "-29d00m28s"),
           ("rho", "16h25m35s", "-23d26m50s"),
           ("teapot", "18h24m10s", "-34d23m05s")]
RADIUS = 220


def grab(outdir):
    """30 s of 1080p as individual frames. Returns the file list."""
    yt = subprocess.Popen(["yt-dlp", "-q", "--no-warnings", "-f", "96/best", "-o", "-", STREAM],
                          stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", "pipe:0",
                        "-t", str(SECONDS), "-vf", f"fps={FPS}", "-q:v", "1",
                        f"{outdir}/f%03d.jpg"],
                       stdin=yt.stdout, check=True, timeout=SECONDS + 180)
    finally:
        yt.stdout.close()
        yt.terminate()
        try:
            yt.wait(timeout=10)
        except subprocess.TimeoutExpired:
            yt.kill()
    return sorted(glob.glob(f"{outdir}/*.jpg"))


MASK_HD = "skymask_hd.npy"     # built at 1920x1080 from format 96, the rendition we use


def build_mask_hd():
    """Build the sky mask at full resolution from the SAME stream rendition we analyse.

    The first mask was derived from webcam/*.jpg — already downscaled to 760 px by
    webcam.py, and grabbed from the 720p rendition — then NEAREST-upscaled to 1920x1080.
    That is about 2.5 px of slop along the treeline, and it assumes the two renditions are
    framed identically, which is likely but was never checked. Since the treeline is
    exactly where road reflections and treetop edges would leak back in as false stars,
    the mask should come from the frames it is applied to.

    Daylight only — the sky/land distinction needs the sky to be the bright part.
    """
    import numpy as np
    from PIL import Image
    from scipy import ndimage as nd
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        files = grab(td)
        if len(files) < 3:
            print("  not enough frames to build a mask")
            return None
        arr = np.stack([np.asarray(Image.open(f).convert("L")).astype(np.float32)
                        for f in files[:10]])
        med = np.median(arr, axis=0)
    if med.mean() < 70:
        print(f"  too dark to build a sky mask (mean {med.mean():.0f}) — daylight only")
        return None
    sd = nd.generic_filter(med, np.std, size=9)
    m = (med > np.percentile(med, 55)) & (sd < np.percentile(sd, 60))
    lab, _ = nd.label(m)
    top = set(lab[0, :][lab[0, :] > 0])
    if top:
        m = np.isin(lab, list(top))
    m = nd.binary_erosion(nd.binary_opening(nd.binary_closing(m, np.ones((15, 15))),
                                            np.ones((9, 9))), np.ones((11, 11)))
    np.save(MASK_HD, m)
    print(f"  built {MASK_HD} at {m.shape[1]}x{m.shape[0]}, sky = {100*m.mean():.1f}%")
    return m


def sky_mask(shape):
    """Sky-only mask at the analysis resolution.

    Prefers the full-resolution mask built from this rendition; falls back to the
    upscaled 760 px one, which is approximate along the treeline.
    """
    import numpy as np
    if os.path.exists(MASK_HD):
        m = np.load(MASK_HD)
        if m.shape == shape:
            return m
    import numpy as np
    from PIL import Image
    from scipy import ndimage as nd
    if os.path.exists(MASK):
        m = np.load(MASK)
    else:
        day = sorted(glob.glob("webcam/*T1[4-8].jpg"))[:5]
        if not day:
            return np.ones(shape, bool)
        med = np.median(np.stack([np.asarray(Image.open(f).convert("L")).astype(float)
                                  for f in day]), axis=0)
        bright = med > np.percentile(med, 55)
        smooth = nd.generic_filter(med, np.std, size=9) < np.percentile(
            nd.generic_filter(med, np.std, size=9), 60)
        m = bright & smooth
        lab, _ = nd.label(m)
        top = set(lab[0, :][lab[0, :] > 0])
        if top:
            m = np.isin(lab, list(top))
        m = nd.binary_erosion(nd.binary_opening(nd.binary_closing(m, np.ones((9, 9))),
                                                np.ones((5, 5))), np.ones((7, 7)))
        np.save(MASK, m)
    from PIL import Image as I
    return np.asarray(I.fromarray((m * 255).astype("uint8")).resize(
        (shape[1], shape[0]), I.NEAREST)) > 127


def project(alt, az):
    A0, h0, fov, roll = (SOLVE[k] for k in ("bearing", "pitch", "fov", "roll"))
    a, z, h = math.radians(alt), math.radians(az - A0), math.radians(h0)
    d = math.sin(h) * math.sin(a) + math.cos(h) * math.cos(a) * math.cos(z)
    if d <= 0.2:
        return None
    f = (W / 2) / math.tan(math.radians(fov) / 2)
    x = f * math.cos(a) * math.sin(z) / d
    y = f * (math.cos(h) * math.sin(a) - math.sin(h) * math.cos(a) * math.cos(z)) / d
    r = math.radians(roll)
    return W / 2 + x * math.cos(r) - y * math.sin(r), H / 2 - (x * math.sin(r) + y * math.cos(r))


def target_pixels(when):
    import warnings
    warnings.filterwarnings("ignore")
    from astropy.coordinates import EarthLocation, AltAz, SkyCoord
    from astropy.time import Time
    import astropy.units as u
    loc = EarthLocation(lat=WEBCAM[0] * u.deg, lon=WEBCAM[1] * u.deg, height=500 * u.m)
    t = Time(when.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
    aa = AltAz(obstime=t, location=loc)
    out = {}
    for name, ra, dec in TARGETS:
        c = SkyCoord(ra=ra, dec=dec).transform_to(aa)
        p = project(c.alt.deg, c.az.deg)
        out[name] = {"alt": round(float(c.alt.deg), 1), "az": round(float(c.az.deg), 1),
                     "px": [round(p[0]), round(p[1])] if p else None,
                     "in_frame": bool(p and 0 < p[0] < W and 0 < p[1] < H)}
    return out


def analyse(files):
    """Median-stack the cleanest frames, mask to sky, return detected sources."""
    import numpy as np
    from PIL import Image
    from scipy import ndimage as nd
    if len(files) < 5:
        return None
    best = [f for _, f in sorted(((os.path.getsize(f), f) for f in files),
                                 reverse=True)[:KEEP_BEST]]
    arr = np.stack([np.asarray(Image.open(f).convert("L")).astype(np.float32) for f in best])
    stack = np.median(arr, axis=0)
    mask = sky_mask(stack.shape)
    res = stack - nd.uniform_filter(stack, size=41)
    res[~mask] = 0
    v = res[mask]
    sig = float(np.median(np.abs(v - np.median(v))) * 1.4826) or 1.0
    lab, n = nd.label(res > SNR * sig)
    src = []
    for i, sl in enumerate(nd.find_objects(lab), 1):
        m = lab[sl] == i
        npx = int(m.sum())
        if not (3 <= npx <= 200):
            continue
        sub = res[sl] * m
        ys, xs = np.nonzero(m)
        src.append({"x": float(xs.mean() + sl[1].start), "y": float(ys.mean() + sl[0].start),
                    "snr": float(sub.max() / sig), "px": npx})
    src.sort(key=lambda s: -s["snr"])
    return {"n_frames": len(files), "n_stacked": len(best), "sigma": round(sig, 2),
            "sky_lum": round(float(stack[mask].mean()), 1), "sources": src[:40],
            "_res": res, "_mask": mask, "_stack": stack}


def region_stats(res, mask, cx, cy, radius=RADIUS, **kwargs):
    """Continuous measures for a target region, not just a count above a threshold.

    A count is fragile: two captures two minutes apart gave 15 sources and then 5, purely
    because the stack noise moved from 0.78 to 0.88 and the 6-sigma cut moved with it.
    Flux and the brightest-source strength do not depend on where a threshold happens to
    land, so they can be compared across captures and across nights.
    """
    import numpy as np
    yy, xx = np.ogrid[:res.shape[0], :res.shape[1]]
    reg = ((xx - cx) ** 2 + (yy - cy) ** 2 <= radius ** 2) & mask
    if not reg.any():
        return None
    v = res[reg]
    bg = np.median(np.abs(v - np.median(v))) * 1.4826 or 1.0
    # NOT "px" — that key already holds the target's pixel coordinates, and overwriting
    # it with a pixel count silently broke the evidence image.
    # Raw flux is not comparable between readings, and this bit me. As the target sinks,
    # two things shrink it for reasons that are not weather:
    #   the aperture overlaps the masked treeline, so it holds fewer sky pixels — a third
    #     of them between 16 and 10 degrees on the night of 4/5 Aug
    #   the light travels through more atmosphere — 3.6 air masses at 16 deg, 5.6 at 10
    # `density` divides out the first. `airmass` records the second so readings can be
    # compared like with like, or corrected later. Neither is applied to `flux` itself,
    # which stays raw.
    import math
    area = int(reg.sum())
    alt = kwargs.get("alt")
    am = None
    if alt is not None and alt > 0:
        am = round(1.0 / max(math.sin(math.radians(alt)) + 0.0001, 0.02), 2)
    return {"flux": round(float(v[v > 3 * bg].sum()), 1),
            "peak": round(float(v.max() / bg), 1),
            "n3": int((v > 3 * bg).sum()),
            "area": area,
            "density": round(float(v[v > 3 * bg].sum()) / area * 1000, 3) if area else None,
            "airmass": am}


def run_once():
    now = datetime.now(EDT)
    with tempfile.TemporaryDirectory() as td:
        try:
            files = grab(td)
        except Exception as ex:
            print(f"  grab failed: {str(ex)[:80]}")
            return None
        a = analyse(files)
    if not a:
        print("  too few frames")
        return None
    res, mask = a.pop("_res"), a.pop("_mask")
    stack = a.pop("_stack")
    tp = target_pixels(now)
    for name, t in tp.items():
        if not t["px"]:
            t["stars"] = None
            continue
        cx, cy = t["px"]
        t["stars"] = sum(1 for s in a["sources"]
                         if (s["x"] - cx) ** 2 + (s["y"] - cy) ** 2 < RADIUS ** 2)
        t.update(region_stats(res, mask, cx, cy, alt=t.get("alt")) or {})
    # Keep the stacked frame as evidence, stretched so faint stars are actually visible,
    # with the target regions ringed. A number nobody can check is worth little.
    shot = None
    try:
        import numpy as np
        from PIL import Image, ImageDraw
        os.makedirs(SHOTS, exist_ok=True)
        lo, hi = np.percentile(stack, 20), np.percentile(stack, 99.9)
        im = Image.fromarray(np.clip((stack - lo) / max(hi - lo, 1) * 255, 0, 255)
                             .astype("uint8")).convert("RGB")
        d = ImageDraw.Draw(im)
        for nm, col in (("core", "#7dd3fc"), ("rho", "#ffd166"), ("teapot", "#9fb3c8")):
            t_ = tp.get(nm) or {}
            if not t_.get("px"):
                continue
            cx, cy = t_["px"]
            d.ellipse([cx - RADIUS, cy - RADIUS, cx + RADIUS, cy + RADIUS],
                      outline=col, width=3)
            d.text((cx - RADIUS + 8, cy - RADIUS + 6),
                   f"{nm}  {t_.get('stars', '-')} stars", fill=col)
        for sc in a["sources"][:30]:
            d.ellipse([sc["x"] - 12, sc["y"] - 12, sc["x"] + 12, sc["y"] + 12],
                      outline="#3ddc84", width=2)
        im = im.resize((960, 540))
        shot = f"{SHOTS}/{now:%Y-%m-%dT%H%M}.jpg"
        im.save(shot, quality=82)
        keep = sorted(glob.glob(f"{SHOTS}/*.jpg"))[-60:]
        for f in glob.glob(f"{SHOTS}/*.jpg"):
            if f not in keep:
                os.remove(f)
    except Exception as ex:
        print(f"  could not save stack: {str(ex)[:60]}")

    rec = {"time": now.isoformat(), "shot": shot, **a, "targets": tp}
    log = json.load(open(LOG)) if os.path.exists(LOG) else []
    log.append(rec)
    json.dump(log, open(LOG, "w"), indent=1)
    print(f"{now:%H:%M}  sky {a['sky_lum']:5.1f}  sig {a['sigma']:4.2f}  "
          f"{len(a['sources']):3d} src  |  "
          + "  ".join(f"{k}: {v.get('stars', '-')}★ flux {v.get('flux', 0):>7.0f} "
                      f"peak {v.get('peak', 0):>5.1f} @{v['alt']:.0f}°"
                      for k, v in tp.items()), flush=True)
    return rec


def main():
    if "--build-mask" in sys.argv:
        build_mask_hd()
        return 0
    if "--loop" in sys.argv:
        # tighter than hourly: there is exactly one fully dark night before the trip, so
        # the sampling has to be dense enough to see cloud move through
        gap = 900
        for i, a_ in enumerate(sys.argv):
            if a_ == "--every" and i + 1 < len(sys.argv):
                gap = int(sys.argv[i + 1]) * 60
        while True:
            h = datetime.now(EDT).hour
            if 5 <= h < 20:
                print("daylight — stopping")
                return 0
            run_once()
            time.sleep(gap)
    run_once()
    return 0


if __name__ == "__main__":
    sys.exit(main())
