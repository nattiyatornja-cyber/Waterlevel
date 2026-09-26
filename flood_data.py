from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import requests

THAIWATER = "https://api-v3.thaiwater.net/api/v1/thaiwater30/public/"
OSRM = "https://router.project-osrm.org/route/v1/driving/"
OPEN_METEO = "https://api.open-meteo.com/v1/forecast"
TZ_OFFSET = timedelta(hours=7)
BANGKOK_PROVINCE_CODE = "10"

LOCATIONS = {
    "Hotel": {"name": "Millennium Hilton Bangkok", "lat": 13.7284021, "lon": 100.5095113, "url": "https://maps.app.goo.gl/NUAdd5LuKyWJSEwJ9"},
    "Airport": {"name": "Suvarnabhumi Airport", "lat": 13.6818969, "lon": 100.7468694, "url": "https://maps.app.goo.gl/FgQiut3Rh18V6uNEA"},
    "WD PRB": {"name": "Western Digital Prachinburi", "lat": 13.9127824, "lon": 101.5705908, "url": "https://maps.app.goo.gl/Pkx61V9qPMF1NwHLA"},
    "WD BPI": {"name": "Western Digital Bang Pa-in (B3)", "lat": 14.2044253, "lon": 100.586419, "url": "https://maps.app.goo.gl/xsZRQ7k6DDJzg6cKA"},
}

# "via" points are (lon, lat); bearings pin the travel direction at each point (OSRM format, one entry per coordinate).
ROUTES = {
    "airport_expressway": {
        "from": "Airport", "to": "Hotel", "group": "airport", "via": [], "bearings": None,
        "name": {"en": "Airport → Hotel (Expressway)", "th": "สนามบิน → โรงแรม (ทางด่วน)"},
    },
    "airport_motorway": {
        "from": "Airport", "to": "Hotel", "group": "airport", "via": [(100.649963, 13.739837)], "bearings": ";270,45;",
        "name": {"en": "Airport → Hotel (Motorway 7)", "th": "สนามบิน → โรงแรม (มอเตอร์เวย์ 7)"},
    },
    "airport_local": {
        "from": "Airport", "to": "Hotel", "group": "airport",
        "via": [(100.6050, 13.6690), (100.5920, 13.7150), (100.5600, 13.7210), (100.5440, 13.7265), (100.5140, 13.7185)],
        "bearings": None,
        "name": {"en": "Airport → Hotel (Local roads, no toll)", "th": "สนามบิน → โรงแรม (ถนนปกติ ไม่เสียค่าผ่านทาง)"},
    },
    "wd_prb": {
        "from": "WD PRB", "to": "Hotel", "group": "wd", "via": [], "bearings": None,
        "name": {"en": "WD PRB → Hotel", "th": "WD PRB → โรงแรม"},
    },
    "wd_bpi": {
        "from": "WD BPI", "to": "Hotel", "group": "wd", "via": [], "bearings": None,
        "name": {"en": "WD BPI → Hotel", "th": "WD BPI → โรงแรม"},
    },
}

ROAD_NAMES_EN = {
    "ทางพิเศษบูรพาวิถี": "Burapha Withi Expressway",
    "ทางพิเศษสายบางนา-อาจณรงค์": "Bang Na–At Narong Expressway",
    "ทางพิเศษเฉลิมมหานคร": "Chaloem Maha Nakhon Expressway",
    "ทางพิเศษศรีรัช": "Si Rat Expressway",
    "ทางพิเศษอุดรรัถยา": "Udon Ratthaya Expressway",
    "ทางยกระดับอุตราภิมุข": "Don Muang Tollway (Uttaraphimuk)",
    "ถนนกรุงเทพฯ-ชลบุรี": "Motorway 7 (Bangkok–Chon Buri)",
    "ถนนกาญจนาภิเษก": "Kanchanaphisek Rd (Outer Ring Rd)",
    "ถนนสุวรรณภูมิ 3": "Suvarnabhumi Rd 3",
    "ถนนเทพรัตน": "Thepparat Rd (Bang Na–Trat)",
    "ถนนสุขุมวิท": "Sukhumvit Rd",
    "ถนนพระรามที่ 4": "Rama IV Rd",
    "ถนนสาทรใต้": "South Sathon Rd",
    "ถนนสาทรเหนือ": "North Sathon Rd",
    "ถนนสีลม": "Silom Rd",
    "ถนนกรุงธนบุรี": "Krung Thon Buri Rd",
    "ถนนเจริญนคร": "Charoen Nakhon Rd",
    "ถนนพหลโยธิน": "Phahonyothin Rd",
    "ถนนวิภาวดีรังสิต": "Vibhavadi Rangsit Rd",
    "ถนนสุวินทวงศ์": "Suwinthawong Rd",
    "ถนนรามอินทรา": "Ram Inthra Rd",
    "ถนนเลี่ยงเมืองฉะเชิงเทรา": "Chachoengsao Bypass Rd",
    "ถนนสิริโสธร": "Sirisothon Rd",
    "ถนนอุดมสรยุทธ์": "Udom Sorayut Rd",
    "ถนนสายเอเชีย": "Asian Highway (Rd 32)",
    "ถนนเชื้อเพลิง": "Chuea Phloeng Rd",
    "ถนนรัชดาภิเษก": "Ratchadaphisek Rd",
}

LEVEL_LABEL = {"th": {0: "ปกติ", 1: "เฝ้าระวัง", 2: "เสี่ยงน้ำท่วม"}, "en": {0: "Normal", 1: "Watch", 2: "Flood risk"}}
LEVEL_COLOR = {0: [0, 176, 80], 1: [255, 165, 0], 2: [220, 20, 20]}

ELEVATED_KEYWORDS = ("ทางพิเศษ", "ทางยกระดับ")
PASS_LABEL = {
    "th": {0: "ผ่านได้ปกติ", 1: "ผ่านได้ ขับระวัง", 2: "ผ่านลำบาก / น้ำขัง", 3: "ผ่านไม่ได้ / น้ำท่วมสูง"},
    "en": {0: "Passable", 1: "Passable, drive with care", 2: "Difficult, standing water", 3: "Impassable, deep flooding"},
}
PASS_COLOR = {0: [0, 176, 80], 1: [240, 200, 0], 2: [255, 120, 0], 3: [210, 0, 0]}
PASS_BADGE = {0: "green", 1: "yellow", 2: "orange", 3: "red"}
WL_SITUATION = {
    "th": {1: "น้ำน้อยวิกฤติ", 2: "น้ำน้อย", 3: "น้ำปกติ", 4: "น้ำมาก", 5: "น้ำล้นตลิ่ง"},
    "en": {1: "Critically low", 2: "Low", 3: "Normal", 4: "High", 5: "Overflowing"},
}

_session = requests.Session()
_session.headers["User-Agent"] = "Waterbkk-flood-monitor/1.0"


def now_bkk():
    return datetime.now(timezone.utc).replace(tzinfo=None) + TZ_OFFSET


def route_points(route_id):
    r = ROUTES[route_id]
    o, d = LOCATIONS[r["from"]], LOCATIONS[r["to"]]
    return [(o["lon"], o["lat"]), *r["via"], (d["lon"], d["lat"])]


def gmaps_directions_url(route_id):
    pts = [(lat, lon) for lon, lat in route_points(route_id)]
    url = f"https://www.google.com/maps/dir/?api=1&travelmode=driving&origin={pts[0][0]},{pts[0][1]}&destination={pts[-1][0]},{pts[-1][1]}"
    if len(pts) > 2:
        url += "&waypoints=" + "%7C".join(f"{la},{lo}" for la, lo in pts[1:-1])
    return url


def fetch_route(route_id):
    coords = ";".join(f"{lon},{lat}" for lon, lat in route_points(route_id))
    params = {"overview": "full", "geometries": "geojson", "steps": "true"}
    if ROUTES[route_id]["bearings"]:
        params["bearings"] = ROUTES[route_id]["bearings"]
    r = _session.get(OSRM + coords, params=params, timeout=30)
    r.raise_for_status()
    route = r.json()["routes"][0]
    roads, steps = [], []
    for leg in route["legs"]:
        for step in leg["steps"]:
            name = (step.get("name") or "").strip()
            if step["distance"] > 800 and name and not name.startswith("ทางบริการ") and name not in roads:
                roads.append(name)
            if len(step["geometry"]["coordinates"]) > 1:
                steps.append((name, step["geometry"]["coordinates"]))
    return {
        "coords": route["geometry"]["coordinates"],
        "distance_km": route["distance"] / 1000,
        "duration_min": route["duration"] / 60,
        "roads": roads,
        "segments": split_segments(steps),
    }


def _seg_len_km(a, b):
    kx = 111.32 * np.cos(np.radians((a[1] + b[1]) / 2))
    return float(np.hypot((b[0] - a[0]) * kx, (b[1] - a[1]) * 110.57))


def split_segments(steps, max_km=1.0):
    """Cut the route (list of (road name, coords) per OSRM step) into pieces of at most ~max_km."""
    segments, pos = [], 0.0
    for name, coords in steps:
        cur, cur_len = [coords[0]], 0.0
        for a, b in zip(coords, coords[1:]):
            cur.append(b)
            cur_len += _seg_len_km(a, b)
            if cur_len >= max_km:
                segments.append({"road": name, "path": cur, "start_km": pos, "length_km": cur_len})
                pos += cur_len
                cur, cur_len = [b], 0.0
        if len(cur) > 1:
            segments.append({"road": name, "path": cur, "start_km": pos, "length_km": cur_len})
            pos += cur_len
    for s in segments:
        s["elevated"] = any(k in s["road"] for k in ELEVATED_KEYWORDS)
    # Unnamed links between two elevated roads are interchange ramps, e.g. Burapha Withi -> Bang Na-At Narong.
    named = [i for i, s in enumerate(segments) if s["road"]]
    for i, s in enumerate(segments):
        if not s["road"]:
            prev = next((segments[j] for j in reversed(named) if j < i), None)
            nxt = next((segments[j] for j in named if j > i), None)
            s["elevated"] = bool(prev and nxt and prev["elevated"] and nxt["elevated"])
    return segments


def passability(rain_1h, rain_24h, wl_level, elevated, heavy_1h, heavy_24h):
    """0 passable · 1 caution · 2 difficult (standing water likely) · 3 impassable (deep flooding likely)."""
    if rain_1h >= heavy_1h or (rain_1h >= heavy_1h / 2 and rain_24h >= 90):
        level = 3
    elif rain_1h >= heavy_1h / 2 or rain_24h >= 90 or wl_level >= 5:
        level = 2
    elif rain_1h >= 5 or rain_24h >= heavy_24h or wl_level >= 4:
        level = 1
    else:
        level = 0
    return min(level, 1) if elevated else level


def assess_segments(segments, wl_near, rain_near, radius_km, heavy_1h, heavy_24h):
    rows = []
    for s in segments:
        r = rain_near[distance_to_route_km(rain_near["lat"].values, rain_near["lon"].values, s["path"]) <= radius_km] \
            if not rain_near.empty else rain_near
        w = wl_near[distance_to_route_km(wl_near["lat"].values, wl_near["lon"].values, s["path"]) <= radius_km] \
            if not wl_near.empty else wl_near
        rain_1h = float(r["rain_1h"].max()) if not r.empty and r["rain_1h"].notna().any() else 0.0
        rain_24h = float(r["rain_24h"].max()) if not r.empty and r["rain_24h"].notna().any() else 0.0
        wl_level = int(w["situation_level"].max()) if not w.empty and w["situation_level"].notna().any() else 0
        rows.append({**s, "rain_1h": rain_1h, "rain_24h": rain_24h, "wl_level": wl_level, "stations": len(r) + len(w),
                     "pass_level": passability(rain_1h, rain_24h, wl_level, s["elevated"], heavy_1h, heavy_24h)})
    return pd.DataFrame(rows)


def road_label(name, lang):
    return ROAD_NAMES_EN.get(name, name) if lang == "en" else name


def _geo(geo, field, lang):
    return (geo.get(field) or {}).get(lang)


def _base_row(x):
    st, geo = x.get("station") or {}, x.get("geocode") or {}
    name = st.get("tele_station_name") or {}
    return {
        "station_th": name.get("th") or name.get("en"),
        "station_en": name.get("en") or name.get("th"),
        "lat": float(st["tele_station_lat"]),
        "lon": float(st["tele_station_long"]),
        "province_code": geo.get("province_code"),
        "province_th": _geo(geo, "province_name", "th"),
        "province_en": _geo(geo, "province_name", "en"),
        "amphoe_th": _geo(geo, "amphoe_name", "th"),
        "amphoe_en": _geo(geo, "amphoe_name", "en") or _geo(geo, "amphoe_name", "th"),
    }


def _has_location(x):
    return (x.get("station") or {}).get("tele_station_lat") is not None


def fetch_water_levels():
    r = _session.get(THAIWATER + "waterlevel_load", timeout=60)
    r.raise_for_status()
    rows = [{
        **_base_row(x),
        "datetime": pd.to_datetime(x.get("waterlevel_datetime"), errors="coerce"),
        "waterlevel_msl": pd.to_numeric(x.get("waterlevel_msl"), errors="coerce"),
        "bank_percent": pd.to_numeric(x.get("storage_percent"), errors="coerce"),
        "situation_level": x.get("situation_level"),
        "diff_bank_m": pd.to_numeric(x.get("diff_wl_bank"), errors="coerce"),
    } for x in r.json()["waterlevel_data"]["data"] if _has_location(x)]
    return pd.DataFrame(rows)


def fetch_rainfall():
    r = _session.get(THAIWATER + "rain_24h", timeout=60)
    r.raise_for_status()
    rows = [{
        **_base_row(x),
        "datetime": pd.to_datetime(x.get("rainfall_datetime"), errors="coerce"),
        "rain_1h": pd.to_numeric(x.get("rain_1h"), errors="coerce"),
        "rain_24h": pd.to_numeric(x.get("rain_24h"), errors="coerce"),
    } for x in r.json()["data"] if _has_location(x)]
    return pd.DataFrame(rows)


def localize(df, lang):
    """Pick the language-specific station/district/province columns."""
    return df.assign(
        station=df[f"station_{lang}"], amphoe=df[f"amphoe_{lang}"], province=df[f"province_{lang}"],
        **({"situation": df["situation_level"].map(WL_SITUATION[lang])} if "situation_level" in df else {}),
    )


def fetch_forecast(points):
    """Hourly precipitation forecast (next 12h) for a list of (lat, lon) points."""
    r = _session.get(OPEN_METEO, params={
        "latitude": ",".join(f"{p[0]:.4f}" for p in points),
        "longitude": ",".join(f"{p[1]:.4f}" for p in points),
        "hourly": "precipitation,precipitation_probability",
        "forecast_hours": 12,
        "timezone": "Asia/Bangkok",
    }, timeout=30)
    r.raise_for_status()
    data = r.json()
    data = data if isinstance(data, list) else [data]
    df = pd.concat([pd.DataFrame(d["hourly"]).assign(point=i) for i, d in enumerate(data)])
    df["time"] = pd.to_datetime(df["time"])
    return df


def distance_to_route_km(lat, lon, coords):
    """Minimum distance (km) from each point to a polyline, using a local equirectangular projection."""
    line = np.asarray(coords, dtype=float)  # [lon, lat]
    lat0 = np.radians(line[:, 1].mean())
    kx, ky = 111.32 * np.cos(lat0), 110.57
    ax, ay = line[:-1, 0] * kx, line[:-1, 1] * ky
    bx, by = line[1:, 0] * kx, line[1:, 1] * ky
    px, py = np.asarray(lon)[:, None] * kx, np.asarray(lat)[:, None] * ky
    dx, dy = bx - ax, by - ay
    seg_len2 = np.where(dx**2 + dy**2 == 0, 1e-12, dx**2 + dy**2)
    t = np.clip(((px - ax) * dx + (py - ay) * dy) / seg_len2, 0, 1)
    return np.sqrt((px - (ax + t * dx)) ** 2 + (py - (ay + t * dy)) ** 2).min(axis=1)


def sample_route(coords, n=8):
    idx = np.linspace(0, len(coords) - 1, n).round().astype(int)
    return [(coords[i][1], coords[i][0]) for i in idx]


def waterlevel_risk(row):
    if row["situation_level"] == 5:
        return 2
    return 1 if row["situation_level"] == 4 else 0


def rain_risk(row, heavy_1h, heavy_24h):
    if row["rain_1h"] >= heavy_1h or row["rain_24h"] >= 90:
        return 2
    return 1 if row["rain_1h"] >= heavy_1h / 2 or row["rain_24h"] >= heavy_24h else 0


def fresh(df, hours):
    return df[df["datetime"] >= pd.Timestamp(now_bkk() - timedelta(hours=hours))]


def near_route(df, coords, buffer_km):
    if df.empty:
        return df.assign(dist_km=[])
    out = df.assign(dist_km=distance_to_route_km(df["lat"].values, df["lon"].values, coords))
    return out[out["dist_km"] <= buffer_km].sort_values("dist_km")
