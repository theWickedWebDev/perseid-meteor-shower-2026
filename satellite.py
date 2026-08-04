#!/usr/bin/env python3
"""
Cloud cover over the lake from the GOES-19 satellite — including at night.

    venv/bin/python satellite.py

Why this exists: webcam.py can only score cloud in daylight, so the model scoreboard was
being calibrated on afternoon cumulus and then trusted for 2 AM stratus. Different regime,
different physics. The satellite sees cloud by temperature rather than reflected light, so
it works in the dark, which is when the whole trip happens.

Product is ABI-L2-ACMC — the Clear Sky Mask over CONUS, 2 km pixels, a new granule every
5 minutes, about 4.8 MB. It is a multi-band algorithm rather than a raw infrared threshold,
and it ships a continuous Cloud_Probabilities field alongside the binary mask.

Known weakness, stated plainly: infrared cloud detection is least reliable for low cloud
and fog at night, when cloud-top temperature is close to ground temperature. That is the
same blind spot the fog forecast in log_forecast.py covers, so the two are complements
rather than a redundant pair. Neither alone is enough.

Needs h5py, which is not in system Python — hence venv/. publish.sh calls this with the
venv interpreter and carries on without it if that is missing.
"""

import io
import json
import math
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

BUCKET = "noaa-goes19"
PRODUCT = "ABI-L2-ACMC"
S3 = "{http://s3.amazonaws.com/doc/2006-03-01/}"
EDT = timezone(timedelta(hours=-4))
LOG = "satellite_log.json"
KEEP = 400                      # readings retained, about a fortnight at hourly

SITE = (45.2393, -71.1964)      # the shooting site itself, not the webcam
BOX_KM = 34                     # square sampled around the site, roughly the visible dome


def _list_latest(dt_utc):
    """Newest granule key in the hour containing dt_utc, or None."""
    pref = f"{PRODUCT}/{dt_utc.year}/{dt_utc.timetuple().tm_yday:03d}/{dt_utc.hour:02d}/"
    url = f"https://{BUCKET}.s3.amazonaws.com/?list-type=2&prefix={pref}"
    with urllib.request.urlopen(url, timeout=45) as r:
        x = ET.fromstring(r.read())
    keys = [c.findtext(S3 + "Key") for c in x.findall(S3 + "Contents")]
    return sorted(keys)[-1] if keys else None


def _attr(obj, name, default=None):
    import numpy as np
    if name not in obj.attrs:
        return default
    return float(np.asarray(obj.attrs[name]).ravel()[0])


def _scaled(var):
    """NetCDF stores the grids as scaled integers; undo that."""
    return var[:].astype("float64") * _attr(var, "scale_factor", 1.0) + \
        _attr(var, "add_offset", 0.0)


def latlon_to_scan(lat, lon, lon0, a, b, H):
    """Geodetic to ABI fixed-grid scan angles. GOES-R product guide, vol 3 s5.1.2.8."""
    lat, lon = math.radians(lat), math.radians(lon)
    e2 = 1 - (b * b) / (a * a)
    lat_c = math.atan((b * b) / (a * a) * math.tan(lat))
    rc = b / math.sqrt(1 - e2 * math.cos(lat_c) ** 2)
    dl = lon - math.radians(lon0)
    sx = H - rc * math.cos(lat_c) * math.cos(dl)
    sy = -rc * math.cos(lat_c) * math.sin(dl)
    sz = rc * math.sin(lat_c)
    return (math.asin(-sy / math.hypot(math.hypot(sx, sy), sz)),
            math.atan(sz / sx))


def read(dt_utc=None):
    """Cloud over the site from the most recent granule. Returns a dict or None."""
    import numpy as np
    import h5py

    dt_utc = dt_utc or datetime.now(timezone.utc)
    key = _list_latest(dt_utc) or _list_latest(dt_utc - timedelta(hours=1))
    if not key:
        print("  no granule published yet for this hour")
        return None
    with urllib.request.urlopen(f"https://{BUCKET}.s3.amazonaws.com/{key}", timeout=180) as r:
        blob = r.read()
    f = h5py.File(io.BytesIO(blob), "r")

    gip = f["goes_imager_projection"]
    lon0 = _attr(gip, "longitude_of_projection_origin")
    a, b = _attr(gip, "semi_major_axis"), _attr(gip, "semi_minor_axis")
    H = _attr(gip, "perspective_point_height") + a

    xs, ys = _scaled(f["x"]), _scaled(f["y"])
    X, Y = latlon_to_scan(SITE[0], SITE[1], lon0, a, b, H)
    ix, iy = int(np.argmin(np.abs(xs - X))), int(np.argmin(np.abs(ys - Y)))
    # sanity: the nearest pixel must actually be near, or the projection is wrong
    off_km = math.hypot((xs[ix] - X) * H, (ys[iy] - Y) * H) / 1000.0
    if off_km > 5:
        print(f"  refusing the reading: nearest pixel is {off_km:.1f} km from the site")
        return None

    half = max(1, int(BOX_KM / 2 / 2))            # 2 km pixels
    bcm = f["BCM"]
    box = bcm[iy - half:iy + half + 1, ix - half:ix + half + 1].astype("float64")
    box[box > 1] = np.nan                          # 255 is fill
    cp = f["Cloud_Probabilities"]
    prob = cp[iy, ix] * _attr(cp, "scale_factor", 1.0) + _attr(cp, "add_offset", 0.0)

    stamp = key.split("_s")[1][:11]                # YYYYDDDHHMM
    scan = (datetime(int(stamp[:4]), 1, 1, tzinfo=timezone.utc)
            + timedelta(days=int(stamp[4:7]) - 1, hours=int(stamp[7:9]),
                        minutes=int(stamp[9:11])))
    pixel = bcm[iy, ix]
    return {
        "time": scan.astimezone(EDT).replace(minute=0, second=0,
                                             microsecond=0).isoformat(),
        "scan": scan.astimezone(EDT).isoformat(),
        "cloud": None if np.isnan(np.nanmean(box)) else round(100 * float(np.nanmean(box))),
        "pixel": None if pixel > 1 else int(pixel),
        "prob": None if not (0 <= prob <= 1) else round(float(prob), 2),
        "off_km": round(off_km, 2),
        "granule": key.split("/")[-1],
    }


MODELS = [("ecmwf_ifs025", "ECMWF"), ("gfs_seamless", "GFS"),
          ("icon_seamless", "ICON"), ("gem_seamless", "GEM"),
          ("ecmwf_aifs025_single", "AIFS"), ("jma_gsm", "JMA")]


def forecast_now(hour_iso):
    """What each model said for this hour at the site, so the reading can score them.

    This is the point of the whole exercise: the same comparison webcam.py does, but at
    the hours that matter. A model that nails afternoon cumulus and misses 2 AM stratus
    used to look perfect.
    """
    m = ",".join(k for k, _ in MODELS)
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={SITE[0]}&longitude={SITE[1]}"
           f"&hourly=cloud_cover&models={m}&timezone=America%2FNew_York&forecast_days=2")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "perseid-meteor-shower-2026"})
        with urllib.request.urlopen(req, timeout=45) as r:
            h = json.load(r)["hourly"]
        i = h["time"].index(hour_iso)
    except Exception:
        return {}
    out = {}
    for key, name in MODELS:
        col = h.get(f"cloud_cover_{key}") or []
        if i < len(col) and col[i] is not None:
            out[name] = col[i]
    return out


def main():
    rec = read()
    if not rec:
        return 1
    rec["models"] = forecast_now(datetime.fromisoformat(rec["time"]).strftime("%Y-%m-%dT%H:00"))
    log = []
    if os.path.exists(LOG):
        try:
            log = json.load(open(LOG))
        except (ValueError, OSError):
            log = []
    log = [e for e in log if e.get("time") != rec["time"]] + [rec]
    log.sort(key=lambda e: e["time"])
    json.dump(log[-KEEP:], open(LOG, "w"), indent=1)

    t = datetime.fromisoformat(rec["scan"])
    print(f"{t:%Y-%m-%dT%H:%M}  satellite {rec['cloud']}% cloud over the site "
          f"(pixel {rec['pixel']}, prob {rec['prob']}, {rec['off_km']} km off-centre)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
