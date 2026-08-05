#!/usr/bin/env python3
"""
Grab a frame from the First Connecticut Lake webcam, estimate cloud cover, and record it
alongside what each model predicted for that same hour.

    python3 webcam.py

The screenshot is nice. The point is the verification: after a few days you get a
mean absolute error per model, which tells you which one to believe for the trip
nights — rather than guessing that "ECMWF is usually best."

Cloud detection is the standard red/blue ratio used by whole-sky imagers: clear sky
scatters blue so R/B is low (~0.75); cloud is spectrally flat so R/B approaches 1.
The threshold is calibrated by eye against this specific camera — see CAL below.

Only works in daylight. At night the frame is too dark to say anything, which is
unfortunate given the trip happens at night, but daytime verification still
calibrates the models.
"""

import json, os, subprocess, urllib.request
from datetime import datetime, timedelta, timezone

STREAM  = "https://www.youtube.com/watch?v=wNxk-XC8Z5s"
SITE    = ("Lopstick, First Connecticut Lake", 45.10367, -71.28616)  # the camera itself
EDT     = timezone(timedelta(hours=-4))
LOG     = "webcam_log.json"
SHOTS   = "webcam"
KEEP    = 48                       # archived frames to retain

# Calibration for this camera. Fractions of frame size, NOT pixels — yt-dlp may hand us
# 720p or 1080p depending on what's available, and an absolute box would sample a
# different part of the scene at each resolution.
# Box excludes the pole at far left, the conifers at right, and the bottom band where
# horizon haze reads as false cloud.
CAL = {"y0": 0.019, "y1": 0.241, "x0": 0.078, "x1": 0.677, "rb": 0.85, "dark": 40}

MODELS = [("ecmwf_ifs025", "ECMWF"), ("gfs_seamless", "GFS"),
          ("icon_seamless", "ICON"), ("gem_seamless", "GEM")]


def grab(path):
    """Pipe the stream through yt-dlp rather than handing ffmpeg the manifest URL.

    YouTube throttles segment requests that lack a correctly deciphered `n` parameter,
    and ffmpeg can't do that deciphering — so fetching the manifest directly works
    only intermittently. yt-dlp handles it, so let it do the fetching and give ffmpeg
    a pipe. ffmpeg exits after one frame and SIGPIPEs yt-dlp, which is fine.
    """
    yt = subprocess.Popen(
        ["yt-dlp", "-q", "--no-warnings", "-f", "best[height<=720]/best", "-o", "-", STREAM],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", "pipe:0",
                        "-frames:v", "1", "-q:v", "3", path],
                       stdin=yt.stdout, check=True, timeout=120)
    finally:
        yt.stdout.close()
        yt.terminate()
        try:
            yt.wait(timeout=10)
        except subprocess.TimeoutExpired:
            yt.kill()
    if not os.path.exists(path) or os.path.getsize(path) < 5000:
        raise RuntimeError("frame came out empty")


def estimate(path):
    """(cloud_pct, is_night, stats). Cloud is None at night — but record the raw
    statistics anyway so a night method can be calibrated once real night frames exist.

    The likely night signal is the inverse of the daytime one: ground light bounces off
    cloud base and comes back down, so an overcast sky reads BRIGHTER than a clear one.
    Texture matters too — clear sky is smooth, broken cloud has structure. And if the
    camera switches to IR at night the image goes monochrome, which kills R/B entirely;
    `sat` detects that.
    """
    import numpy as np
    from PIL import Image
    im = np.asarray(Image.open(path).convert("RGB")).astype(float)
    H, W = im.shape[:2]
    sky = im[int(CAL["y0"] * H):int(CAL["y1"] * H),
             int(CAL["x0"] * W):int(CAL["x1"] * W)]
    lum = sky.mean(axis=2)
    mx, mn = sky.max(axis=2), sky.min(axis=2)
    stats = {
        "lum": round(float(lum.mean()), 1),        # overall sky brightness
        "lum_sd": round(float(lum.std()), 1),      # texture — smooth vs structured
        "lum_p90": round(float(np.percentile(lum, 90)), 1),
        "sat": round(float((mx - mn).mean()), 1),  # ~0 means monochrome, i.e. IR mode
        "rb": round(float((sky[:, :, 0] / np.maximum(sky[:, :, 2], 1)).mean()), 3),
    }
    if lum.mean() < CAL["dark"]:
        return None, True, stats
    rb = sky[:, :, 0] / np.maximum(sky[:, :, 2], 1)
    return round(float((rb > CAL["rb"]).mean() * 100)), False, stats


def forecast_now(hour_iso):
    """What each model said the cloud cover would be for this hour, at the webcam site."""
    m = ",".join(k for k, _ in MODELS)
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={SITE[1]}&longitude={SITE[2]}"
           f"&hourly=cloud_cover&models={m}&timezone=America%2FNew_York&forecast_days=2")
    req = urllib.request.Request(url, headers={"User-Agent": "perseid-meteor-shower-2026"})
    with urllib.request.urlopen(req, timeout=30) as r:
        h = json.load(r)["hourly"]
    try:
        i = h["time"].index(hour_iso)
    except ValueError:
        return {}
    out = {}
    for key, name in MODELS:
        col = h.get(f"cloud_cover_{key}") or []
        if i < len(col) and col[i] is not None:
            out[name] = col[i]
    return out


def main():
    os.makedirs(SHOTS, exist_ok=True)
    now = datetime.now(EDT).replace(minute=0, second=0, microsecond=0)
    stamp = now.strftime("%Y-%m-%dT%H")
    raw = f"{SHOTS}/{stamp}.jpg"

    try:
        grab(raw)
    except Exception as ex:
        print(f"grab failed: {ex}")
        return

    cloud, night, stats = estimate(raw)

    # shrink for the repo — full frames are ~300 KB each and we keep dozens
    try:
        from PIL import Image
        im = Image.open(raw); im.thumbnail((760, 760)); im.save(raw, quality=78)
    except Exception:
        pass

    entry = {"time": now.isoformat(), "cloud": cloud, "night": night, "stats": stats,
             "shot": raw, "models": forecast_now(now.strftime("%Y-%m-%dT%H:00"))}

    log = json.load(open(LOG)) if os.path.exists(LOG) else []
    log = [e for e in log if e["time"] != entry["time"]]
    log.append(entry)
    log.sort(key=lambda e: e["time"])

    # Prune old frames. Only ever touch .jpg files we could have written, and never let a
    # stray file or a subdirectory kill the run — webcam.py goes first in publish.sh, so an
    # exception here costs the forecast refresh too.
    log = log[-KEEP * 3:]
    keep = {e["shot"] for e in log[-KEEP:]}
    for f in sorted(os.listdir(SHOTS)):
        path = f"{SHOTS}/{f}"
        if path in keep or not f.lower().endswith(".jpg"):
            continue
        try:
            if os.path.isfile(path):
                os.remove(path)
        except OSError as ex:
            print(f"  could not prune {path}: {ex}")
    json.dump(log, open(LOG, "w"), indent=1)

    if night:
        ms = entry["models"]
        exp = (f"  models said {min(ms.values())}–{max(ms.values())}%" if ms else "")
        print(f"{stamp}  NIGHT  lum {stats['lum']} sd {stats['lum_sd']} "
              f"sat {stats['sat']}{exp}")
    else:
        ms = entry["models"]
        err = (f"  models {min(ms.values())}–{max(ms.values())}%" if ms else "")
        print(f"{stamp}  observed {cloud}% cloud{err}")


if __name__ == "__main__":
    main()
