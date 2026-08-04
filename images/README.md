# Reference Images

Copied with `cp -p` — **EXIF is intact**, including the GPS and compass data on IMG_8460.
Full analysis in [../HORIZON_PHOTOS.md](../HORIZON_PHOTOS.md).

| File | Date | Direction | How determined |
|---|---|---|---|
| `lake_ssw_204deg_IMG_8460.jpeg` | 2023-11-18 18:15 | **az 204.4°** (SSW) | **EXIF GPSImgDirection** + moon cross-check |
| `lake_wnw_twilight_IMG_6099.jpeg` | 2026-02-21 18:21 | ~az 260° (W) | Twilight glow position |
| `lake_daylight_IMG_6182.jpg` | 2024-06-29 12:37 | unknown | Google-stripped; overcast, no shadows |
| `cabin_ssw_orion_IMG_6113.jpeg` | 2026-02-21 20:47 | ~az 211° (SSW) | **Orion** — Betelgeuse, Belt, M42 |
| `cabin_sw_pleiades_orion_IMG_6117.jpeg` | 2026-02-21 20:53 | ~az 225° (SW) | **Pleiades + Orion**, separation verified |
| `cabin_w_taurus_IMG_6116.jpeg` | 2026-02-21 20:51 | ~az 261° (W) | **Pleiades + Aldebaran** |
| `cabin_nw_doorway_IMG_6119.jpeg` | 2026-02-21 21:12 | ~az 309° (NW) | M31 framing (Stephen's pre-plan) |
| `nov2023_moon_silhouette_STRIPPED.jpg` | 2023-11-18 | unknown | All EXIF stripped |
| `nov2023_interior_STRIPPED.jpg` | 2023-11-18 | unknown | All EXIF stripped |

## Not Stephen's

| File | What it is |
|---|---|
| `REFERENCE_thirdconn_core_web_NOT_MINE.jpeg` | Someone else's Third Connecticut Milky Way shot, screenshotted from a web gallery. **Composition reference only** — no EXIF, no date, no bearing, possibly cropped or from a different vantage. Discussed in [../CREATIVE_SHOTS.md](../CREATIVE_SHOTS.md). |

## Quick EXIF check

```bash
exiftool -s -GPSImgDirection -GPSPosition -GPSAltitude -DateTimeOriginal \
         -FocalLengthIn35mmFormat -FOV -Orientation *.jpeg
```

## The lesson

Only `IMG_8460` kept its GPS and compass bearing. Everything routed through Google Photos or a
messaging app lost both. **Always work from camera originals** — AirDrop, or Share → Options →
"All Photos Data", or the Files app.
