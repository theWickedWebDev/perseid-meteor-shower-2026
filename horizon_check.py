#!/usr/bin/env python3
"""
Does this spot actually see the core, or is there a mountain in the way?

    python3 horizon_check.py 44.1614 -71.6828 "Echo Lake"
    python3 horizon_check.py --file sites.txt

The Milky Way core sits low — around 10 degrees altitude due south from northern New
England in August — and low is where terrain lives. A site can be perfectly dark, perfectly
clear, and still show you nothing but a ridge.

For each candidate this samples ground elevation outward along the southern arc and works
out how high the skyline rises in each direction, then compares that to where the core
actually is. Terrain only: it cannot see the trees standing on top of the terrain, which in
the White Mountains add roughly 15-25 m and are frequently the thing that actually blocks
you. Treat a pass here as "worth driving to and checking", never as "verified".

Elevations come from Open-Meteo's elevation API, which serves the Copernicus 90 m DEM.
"""

import json
import math
import sys
import time
import urllib.request

import log_forecast as lf

RANGE_KM = 25            # how far out to look for a skyline
STEPS = 16               # samples along each ray
AZ = range(150, 226, 15)  # the southern arc that matters
BATCH = 100
PAUSE = 1.5              # between requests; the elevation API rate-limits quickly
UA = {"User-Agent": "perseid-meteor-shower-2026"}
EARTH_R = 6371000.0


def elev(points):
    """[(lat,lon)] -> [metres]. Open-Meteo takes 100 at a time."""
    out = []
    for i in range(0, len(points), BATCH):
        chunk = points[i:i + BATCH]
        url = ("https://api.open-meteo.com/v1/elevation?latitude="
               + ",".join(f"{a:.5f}" for a, _ in chunk)
               + "&longitude=" + ",".join(f"{b:.5f}" for _, b in chunk))
        for attempt in range(5):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                            timeout=60) as r:
                    out += json.load(r)["elevation"]
                break
            except Exception as ex:
                if attempt == 4:
                    raise
                # 429 is the usual one; the API forgives quickly but not instantly
                time.sleep(8 * (attempt + 1))
        time.sleep(PAUSE)
    return out


def offset(lat, lon, az_deg, dist_km):
    """Point dist_km away on bearing az_deg."""
    d = dist_km * 1000 / EARTH_R
    a, b, t = math.radians(lat), math.radians(lon), math.radians(az_deg)
    la = math.asin(math.sin(a) * math.cos(d) + math.cos(a) * math.sin(d) * math.cos(t))
    lo = b + math.atan2(math.sin(t) * math.sin(d) * math.cos(a),
                        math.cos(d) - math.sin(a) * math.sin(la))
    return math.degrees(la), math.degrees(lo)


def skyline(lat, lon):
    """Horizon altitude in degrees for each azimuth in AZ."""
    pts, meta = [(lat, lon)], []
    for az in AZ:
        for s in range(1, STEPS + 1):
            d = RANGE_KM * s / STEPS
            pts.append(offset(lat, lon, az, d))
            meta.append((az, d))
    e = elev(pts)
    here, rest = e[0], e[1:]
    out = {}
    for (az, d), h in zip(meta, rest):
        if h is None:
            continue
        # curvature and refraction drop the far ground away; ignoring it overstates
        # distant ridges enough to matter at 25 km
        drop = (d * 1000) ** 2 / (2 * EARTH_R) * 0.87
        ang = math.degrees(math.atan2(h - here - drop, d * 1000))
        out[az] = max(out.get(az, -90), ang)
    return here, out


def core_at(lat, lon, day="2026-08-12"):
    """Altitude and azimuth of the core through the evening, from schedule_data if possible."""
    try:
        from astropy.coordinates import SkyCoord, EarthLocation, AltAz
        from astropy.time import Time
        import astropy.units as u
        loc = EarthLocation(lat=lat * u.deg, lon=lon * u.deg, height=300 * u.m)
        core = SkyCoord(ra=266.4 * u.deg, dec=-29.0 * u.deg)   # Sgr A*, the core
        out = []
        for hh in (21, 22, 23):
            t = Time(f"{day} {hh:02d}:30:00") + 4 * u.hour       # EDT -> UTC
            a = core.transform_to(AltAz(obstime=t, location=loc))
            out.append((hh, float(a.alt.deg), float(a.az.deg)))
        return out
    except Exception:
        return None


def report(lat, lon, name):
    here, sky = skyline(lat, lon)
    core = core_at(lat, lon)
    print(f"\n  {name}   {lat:.4f}, {lon:.4f}   ground {here:.0f} m")
    print(f"  {'az':>5}{'skyline':>10}   ")
    worst = max(sky.values()) if sky else 0
    for az in AZ:
        a = sky.get(az)
        if a is None:
            continue
        bar = "#" * int(max(0, a) * 3)
        flag = ""
        if core:
            for hh, alt, caz in core:
                if abs(((caz - az + 180) % 360) - 180) <= 5:
                    flag = f"  <- core at {hh}:30 is {alt:.0f}°" + (
                        "  BLOCKED" if alt < a else "  clear")
        print(f"  {az:>4}°{a:>8.1f}°   {bar}{flag}")
    if core:
        print(f"\n  core on 12 Aug: " + ", ".join(f"{hh}:30 alt {alt:.0f}° az {caz:.0f}°"
                                                  for hh, alt, caz in core))
        blocked = []
        for hh, alt, caz in core:
            az = min(AZ, key=lambda a: abs(((caz - a + 180) % 360) - 180))
            if sky.get(az, 0) > alt:
                blocked.append(f"{hh}:30 (ridge {sky[az]:.0f}° vs core {alt:.0f}°)")
        print("  " + ("BLOCKED at " + ", ".join(blocked) if blocked
                      else "core clears the terrain at every hour checked"))
    print(f"  highest southern terrain: {worst:.1f}°")
    return {"name": name, "lat": lat, "lon": lon, "ground": here,
            "skyline": sky, "worst": worst}


def main():
    if "--file" in sys.argv:
        path = sys.argv[sys.argv.index("--file") + 1]
        sites = []
        for ln in open(path):
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            p = ln.split(None, 2)
            sites.append((float(p[0]), float(p[1]), p[2] if len(p) > 2 else "site"))
    elif len(sys.argv) >= 3:
        sites = [(float(sys.argv[1]), float(sys.argv[2]),
                  sys.argv[3] if len(sys.argv) > 3 else "site")]
    else:
        print(__doc__.strip().split("\n\n")[1])
        return 1

    print(f"  terrain only — trees add roughly 15-25 m and are not in the DEM")
    res = [report(a, b, n) for a, b, n in sites]
    if len(res) > 1:
        print(f"\n  RANKED by lowest southern skyline\n")
        for r in sorted(res, key=lambda r: r["worst"]):
            print(f"  {r['worst']:>5.1f}°   {r['name']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
