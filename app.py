import pandas as pd
import pydeck as pdk
import streamlit as st

import flood_data as fd

st.set_page_config(page_title="Flood route monitor", page_icon=":material/flood:", layout="wide")

T = {
    "th": {
        "settings": "ตั้งค่า", "language": "ภาษา / Language", "more": "ดูรายละเอียด",
        "buffer": "ระยะห่างจากเส้นทาง (กม.)",
        "heavy_1h": "ฝนหนัก 1 ชม. (มม.)", "heavy_1h_help": "ถึงค่านี้ = เสี่ยงน้ำท่วม, ครึ่งหนึ่ง = เฝ้าระวัง",
        "heavy_24h": "ฝนสะสม 24 ชม. เฝ้าระวัง (มม.)", "heavy_24h_help": ">= 90 มม. = เสี่ยงน้ำท่วม",
        "refresh": "รีเฟรชข้อมูล", "places": "จุดหมาย",
        "title": "มอนิเตอร์น้ำท่วมตามเส้นทาง", "loading": "กำลังโหลดข้อมูลล่าสุด...",
        "updated": "อัปเดตข้อมูลฝนล่าสุด: {t} น. · รีเฟรชอัตโนมัติทุก 10 นาที",
        "airport_section": "สนามบิน → โรงแรม: เปรียบเทียบเส้นทาง",
        "wd_section": "WD → โรงแรม",
        "recommend": "**แนะนำ: {name}** — ช่วงที่ผ่านลำบาก/ผ่านไม่ได้น้อยที่สุด และใช้เวลาน้อยที่สุดในบรรดาเส้นทางที่สภาพเท่ากัน",
        "all_risky": "ทุกเส้นทางจากสนามบินมีช่วงที่น่าจะผ่านลำบาก ควรเช็คสภาพจราจรจริงก่อนออกเดินทาง",
        "pass_legend": "สีเส้นทาง (ประเมินจากฝนและระดับน้ำ):",
        "km_breakdown": "ผ่านได้ {k0:.0f} กม. · ขับระวัง {k1:.0f} กม. · ผ่านลำบาก {k2:.0f} กม. · ผ่านไม่ได้ {k3:.0f} กม.",
        "problem_title": "ช่วงถนนที่ต้องระวัง (ผ่านลำบาก / ผ่านไม่ได้)",
        "no_problem": "ไม่พบช่วงที่ผ่านลำบากหรือผ่านไม่ได้บนเส้นทางนี้",
        "col_road": "ถนน", "col_km": "กม.ที่", "col_pass": "สภาพการผ่าน", "col_wl_level": "ระดับน้ำใกล้เคียง",
        "col_elevated": "ยกระดับ",
        "km_min": "{d:.0f} กม. · ~{m:.0f} นาที (ไม่รวมรถติด)",
        "toll": "ค่าผ่านทาง", "toll_yes": "มี", "toll_no": "ไม่มี",
        "rain1": "ฝน 1 ชม. สูงสุด", "rain24": "ฝน 24 ชม. สูงสุด", "fc": "พยากรณ์ 12 ชม.", "fc_unit": "มม./ชม.",
        "wl_high": "สถานีน้ำมาก/ล้นตลิ่ง", "mm": "มม.",
        "roads": "ถนนที่ใช้", "gmaps": "เปิดใน Google Maps (ดูรถติดสด)",
        "compare_note": "ช่วงทางด่วน/มอเตอร์เวย์ที่ยกระดับมักไม่ท่วม จุดที่ต้องระวังคือทางขึ้น-ลงและถนนระดับพื้น · "
                        "แอปนี้ไม่มีข้อมูลการจราจรสด ให้กดลิงก์ Google Maps เพื่อดูสภาพจราจร",
        "tab_map": "แผนที่", "tab_detail": "รายละเอียดเส้นทาง", "tab_bkk": "น้ำท่วมใน กทม.", "tab_sources": "แหล่งข้อมูล",
        "route": "เส้นทาง",
        "map_legend": "เส้น = เส้นทาง แบ่งเป็นช่วงละ ~1 กม. สีตามสภาพการผ่าน · วงกลมจาง = สถานีวัดฝน (ขนาดตามฝน 24 ชม.) · "
                      "วงกลมขอบดำ = สถานีระดับน้ำ · ชี้ที่เส้นเพื่อดูรายละเอียด",
        "rain_near": "สถานีวัดฝนใกล้เส้นทาง", "wl_near": "สถานีระดับน้ำใกล้เส้นทาง",
        "col_station": "สถานี", "col_amphoe": "อำเภอ/เขต", "col_province": "จังหวัด", "col_time": "เวลา",
        "col_rain1": "ฝน 1 ชม. (มม.)", "col_rain24": "ฝน 24 ชม. (มม.)", "col_dist": "ห่างเส้นทาง (กม.)",
        "col_risk": "ระดับ", "col_risk_help": "0 ปกติ · 1 เฝ้าระวัง · 2 เสี่ยง", "col_situation": "สถานการณ์",
        "col_bank": "% ความจุตลิ่ง", "col_diff": "ห่างตลิ่ง (ม.)", "col_status": "สถานะ", "col_stations": "จำนวนสถานี",
        "col_district": "เขต", "col_rain1_max": "ฝน 1 ชม. สูงสุด (มม.)", "col_rain24_max": "ฝน 24 ชม. สูงสุด (มม.)",
        "fc_title": "พยากรณ์ฝนรายชั่วโมงตามเส้นทาง (12 ชม.)", "fc_x": "เวลา", "fc_y": "ฝนสูงสุดตามเส้นทาง (มม./ชม.)",
        "bkk_stations": "สถานีวัดฝน กทม.", "bkk_risk": "เขตเสี่ยงน้ำท่วม", "bkk_watch": "เขตที่ต้องเฝ้าระวัง",
        "by_district": "สรุปรายเขต", "wl_prefix": "ระดับน้ำ", "bank_of": "% ของตลิ่ง",
        "sources_intro": "ข้อมูลทั้งหมดดึงจากแหล่งสาธารณะแบบ real-time ไม่ต้องใช้ API key",
        "src_col": ["ข้อมูล", "แหล่งที่มา", "ความถี่อัปเดต", "ลิงก์"],
        "sources": [
            ("ฝนรายชั่วโมง / สะสม 24 ชม. จากสถานีโทรมาตร (กรมชลประทาน, กทม., กรมอุตุนิยมวิทยา ฯลฯ)",
             "คลังข้อมูลน้ำแห่งชาติ (ThaiWater) โดย สสน.", "10–60 นาที", "https://www.thaiwater.net"),
            ("ระดับน้ำในแม่น้ำ/คลอง และ % ความจุตลิ่ง", "คลังข้อมูลน้ำแห่งชาติ (ThaiWater) โดย สสน.", "10–60 นาที",
             "https://www.thaiwater.net"),
            ("พยากรณ์ฝนรายชั่วโมง 12 ชม. ตามจุดบนเส้นทาง", "Open-Meteo (โมเดลพยากรณ์อากาศ ECMWF/GFS ฯลฯ)", "ทุกชั่วโมง",
             "https://open-meteo.com"),
            ("เส้นทางขับรถ ระยะทาง เวลาเดินทาง (ไม่รวมรถติด)", "OSRM บนข้อมูลแผนที่ OpenStreetMap", "คำนวณวันละครั้ง",
             "https://project-osrm.org"),
            ("พิกัดโรงแรม สนามบิน และโรงงาน WD", "Google Maps (ลิงก์ที่ผู้ใช้ให้มา)", "คงที่", "https://maps.google.com"),
            ("แผนที่พื้นหลัง", "CARTO / OpenStreetMap", "-", "https://carto.com"),
        ],
        "method_title": "วิธีประเมินสภาพการผ่าน",
        "method": "- แบ่งเส้นทางเป็นช่วงละ ~1 กม. แต่ละช่วงใช้สถานีที่อยู่ห่างไม่เกินระยะที่ตั้งไว้ (ค่าเริ่มต้น 3 กม.) และข้อมูลย้อนหลังไม่เกิน 24 ชม.\n"
                  "- :red-badge[ผ่านไม่ได้ / น้ำท่วมสูง] ฝน 1 ชม. ≥ เกณฑ์ฝนหนัก (ค่าเริ่มต้น 30 มม.) หรือฝน 1 ชม. ≥ ครึ่งเกณฑ์ร่วมกับฝน 24 ชม. ≥ 90 มม.\n"
                  "- :orange-badge[ผ่านลำบาก / น้ำขัง] ฝน 1 ชม. ≥ ครึ่งเกณฑ์ หรือฝน 24 ชม. ≥ 90 มม. หรือมีสถานีระดับน้ำล้นตลิ่ง\n"
                  "- :yellow-badge[ผ่านได้ ขับระวัง] ฝน 1 ชม. ≥ 5 มม. หรือฝน 24 ชม. ≥ เกณฑ์เฝ้าระวัง (ค่าเริ่มต้น 35 มม.) หรือระดับน้ำมาก (>70% ตลิ่ง)\n"
                  "- :green-badge[ผ่านได้ปกติ] ไม่เข้าเงื่อนไขข้างบน\n"
                  "- ช่วงทางด่วน/ทางยกระดับ (ชื่อถนนมีคำว่า ทางพิเศษ, ทางยกระดับ) ถือว่าไม่ท่วม จึงแสดงสูงสุดแค่ \"ขับระวัง\"\n"
                  "- สภาพของเส้นทาง = ช่วงที่แย่ที่สุด; ถ้าพยากรณ์ฝน 12 ชม. ≥ เกณฑ์ฝนหนัก จะขึ้นอย่างน้อย \"ขับระวัง\"\n"
                  "- **เป็นการประเมินจากข้อมูลฝนและระดับน้ำ ไม่ใช่การวัดน้ำบนถนนจริง** (เซนเซอร์น้ำท่วมถนนของ กทม. เข้าถึงจากเครือข่ายนี้ไม่ได้)",
    },
    "en": {
        "settings": "Settings", "language": "ภาษา / Language", "more": "More details",
        "buffer": "Distance from route (km)",
        "heavy_1h": "Heavy rain, 1 h (mm)", "heavy_1h_help": "At or above = flood risk, half = watch",
        "heavy_24h": "24 h rainfall watch level (mm)", "heavy_24h_help": ">= 90 mm = flood risk",
        "refresh": "Refresh data", "places": "Locations",
        "title": "Flood route monitor", "loading": "Loading latest data...",
        "updated": "Latest rainfall data: {t} · auto-refresh every 10 minutes",
        "airport_section": "Airport → Hotel: route comparison",
        "wd_section": "WD → Hotel",
        "recommend": "**Recommended: {name}** — fewest difficult/impassable stretches, and fastest among equally affected routes",
        "all_risky": "Every airport route has stretches that are likely difficult to pass. Check live traffic before departure.",
        "pass_legend": "Route colors (estimated from rainfall and water levels):",
        "km_breakdown": "Passable {k0:.0f} km · care {k1:.0f} km · difficult {k2:.0f} km · impassable {k3:.0f} km",
        "problem_title": "Stretches to watch (difficult / impassable)",
        "no_problem": "No difficult or impassable stretches found on this route.",
        "col_road": "Road", "col_km": "At km", "col_pass": "Passability", "col_wl_level": "Nearby water level",
        "col_elevated": "Elevated",
        "km_min": "{d:.0f} km · ~{m:.0f} min (without traffic)",
        "toll": "Toll", "toll_yes": "Yes", "toll_no": "No",
        "rain1": "Max 1 h rain", "rain24": "Max 24 h rain", "fc": "12 h forecast", "fc_unit": "mm/h",
        "wl_high": "High/overflow stations", "mm": "mm",
        "roads": "Roads used", "gmaps": "Open in Google Maps (live traffic)",
        "compare_note": "Elevated expressway/motorway sections rarely flood; watch the on/off ramps and ground-level roads. · "
                        "This app has no live traffic data; use the Google Maps link to check traffic.",
        "tab_map": "Map", "tab_detail": "Route details", "tab_bkk": "Bangkok flooding", "tab_sources": "Data sources",
        "route": "Route",
        "map_legend": "Lines = routes split into ~1 km stretches, colored by passability · faded circles = rain gauges (size by 24 h rain) · "
                      "black-outlined circles = water level stations · hover a line for details",
        "rain_near": "Rain gauges near route", "wl_near": "Water level stations near route",
        "col_station": "Station", "col_amphoe": "District", "col_province": "Province", "col_time": "Time",
        "col_rain1": "1 h rain (mm)", "col_rain24": "24 h rain (mm)", "col_dist": "Distance to route (km)",
        "col_risk": "Level", "col_risk_help": "0 normal · 1 watch · 2 risk", "col_situation": "Situation",
        "col_bank": "% of bank capacity", "col_diff": "To bank (m)", "col_status": "Status", "col_stations": "Stations",
        "col_district": "District", "col_rain1_max": "Max 1 h rain (mm)", "col_rain24_max": "Max 24 h rain (mm)",
        "fc_title": "Hourly rain forecast along route (12 h)", "fc_x": "Time", "fc_y": "Max rain along route (mm/h)",
        "bkk_stations": "Bangkok rain gauges", "bkk_risk": "Districts at flood risk", "bkk_watch": "Districts on watch",
        "by_district": "Summary by district", "wl_prefix": "Water level", "bank_of": "% of bank",
        "sources_intro": "All data is pulled in real time from public sources; no API key needed.",
        "src_col": ["Data", "Source", "Update frequency", "Link"],
        "sources": [
            ("Hourly / 24 h rainfall from telemetry gauges (RID, BMA, TMD, etc.)",
             "Thailand National Water Data Center (ThaiWater) by HII", "10–60 min", "https://www.thaiwater.net"),
            ("River/canal water level and % of bank capacity", "Thailand National Water Data Center (ThaiWater) by HII",
             "10–60 min", "https://www.thaiwater.net"),
            ("12 h hourly rain forecast at points along each route", "Open-Meteo (ECMWF/GFS and other weather models)",
             "Hourly", "https://open-meteo.com"),
            ("Driving routes, distance, travel time (without traffic)", "OSRM on OpenStreetMap data", "Computed daily",
             "https://project-osrm.org"),
            ("Hotel, airport and WD plant coordinates", "Google Maps (links provided by user)", "Static", "https://maps.google.com"),
            ("Base map", "CARTO / OpenStreetMap", "-", "https://carto.com"),
        ],
        "method_title": "How passability is assessed",
        "method": "- Each route is split into ~1 km stretches; each stretch uses stations within the configured distance (default 3 km) and data from the last 24 h.\n"
                  "- :red-badge[Impassable, deep flooding] 1 h rain ≥ heavy-rain threshold (default 30 mm), or 1 h rain ≥ half the threshold together with 24 h rain ≥ 90 mm.\n"
                  "- :orange-badge[Difficult, standing water] 1 h rain ≥ half the threshold, or 24 h rain ≥ 90 mm, or a water level station overflowing its bank.\n"
                  "- :yellow-badge[Passable, drive with care] 1 h rain ≥ 5 mm, or 24 h rain ≥ watch level (default 35 mm), or high water (>70% of bank).\n"
                  "- :green-badge[Passable] none of the above.\n"
                  "- Expressway/elevated stretches (road name contains ทางพิเศษ or ทางยกระดับ) are assumed not to flood, so they show at most \"drive with care\".\n"
                  "- Route status = its worst stretch; a 12 h forecast ≥ the heavy-rain threshold raises it to at least \"drive with care\".\n"
                  "- **This is an estimate from rainfall and water level data, not a measurement of water on the road** (BMA road flood sensors are not reachable from this network).",
    },
}

TOLL = {"airport_expressway": True, "airport_motorway": True, "airport_local": False, "wd_prb": True, "wd_bpi": True}
PASS_ICON = {0: ":material/check_circle:", 1: ":material/warning:", 2: ":material/water:", 3: ":material/block:"}


@st.cache_data(ttl="1d", show_spinner=False)
def load_route(route_id):
    return fd.fetch_route(route_id)


@st.cache_data(ttl="10m", show_spinner=False)
def load_water_levels():
    return fd.fetch_water_levels()


@st.cache_data(ttl="10m", show_spinner=False)
def load_rainfall():
    return fd.fetch_rainfall()


@st.cache_data(ttl="30m", show_spinner=False)
def load_forecast(points):
    return fd.fetch_forecast(list(points))


is_phone = any(k in st.context.headers.get("User-Agent", "") for k in ("Mobile", "Android", "iPhone"))
with st.container(horizontal=True, horizontal_alignment="right"):
    lang_choice = st.segmented_control("ภาษา / Language", ["ไทย", "English"], default="ไทย", key="lang",
                                       bind="query-params", label_visibility="collapsed")
    view_choice = st.segmented_control("View", ["Desktop", "Mobile"], default="Mobile" if is_phone else "Desktop",
                                       format_func=lambda v: {"Desktop": ":material/computer: Desktop",
                                                              "Mobile": ":material/smartphone: Mobile"}[v],
                                       key="view", bind="query-params", label_visibility="collapsed")
lang = "en" if lang_choice == "English" else "th"
mobile = view_choice == "Mobile"
t = T[lang]
MAP_H = {"main": 420, "detail": 380, "bkk": 400} if mobile else {"main": 620, "detail": 450, "bkk": 500}

with st.sidebar:
    st.header(t["settings"])
    buffer_km = st.slider(t["buffer"], 1.0, 10.0, 3.0, 0.5)
    heavy_1h = st.number_input(t["heavy_1h"], 5, 100, 30, help=t["heavy_1h_help"])
    heavy_24h = st.number_input(t["heavy_24h"], 10, 200, 35, help=t["heavy_24h_help"])
    if st.button(t["refresh"], icon=":material/refresh:", width="stretch"):
        st.cache_data.clear()
    st.subheader(t["places"])
    for key, loc in fd.LOCATIONS.items():
        st.markdown(f"- **{key}** — [{loc['name']}]({loc['url']})")

st.title(t["title"])


def route_card(route_id, r, recommended=False):
    with st.container(border=True, width="stretch" if mobile else 340):
        st.markdown(f"**{fd.ROUTES[route_id]['name'][lang]}**" + (" :material/star:" if recommended else ""))
        st.badge(fd.PASS_LABEL[lang][r["level"]], color=fd.PASS_BADGE[r["level"]], icon=PASS_ICON[r["level"]])
        st.caption(t["km_min"].format(d=r["route"]["distance_km"], m=r["route"]["duration_min"])
                   + f" · {t['toll']}: {t['toll_yes'] if TOLL[route_id] else t['toll_no']}")
        st.caption(t["km_breakdown"].format(**{f"k{i}": r["km"][i] for i in range(4)}))
        with st.expander(t["more"]) if mobile else st.container():
            c1, c2 = st.columns(2)
            rain = r["rain"]
            c1.metric(t["rain1"], f"{rain['rain_1h'].max() if not rain.empty else 0:.1f} {t['mm']}")
            c2.metric(t["rain24"], f"{rain['rain_24h'].max() if not rain.empty else 0:.1f} {t['mm']}")
            c1.metric(t["fc"], f"{r['fc_max']:.1f} {t['fc_unit']}")
            c2.metric(t["wl_high"], int((r["wl"]["situation_level"] >= 4).sum()))
            st.caption(f"{t['roads']}: " + " › ".join(fd.road_label(n, lang) for n in r["route"]["roads"]))
        st.link_button(t["gmaps"], fd.gmaps_directions_url(route_id), icon=":material/traffic:", width="stretch")


@st.fragment(run_every="10m")
def dashboard():
    with st.spinner(t["loading"]):
        wl = fd.localize(fd.fresh(load_water_levels(), 24), lang)
        rain = fd.localize(fd.fresh(load_rainfall(), 24), lang)
        wl = wl.assign(risk=wl.apply(fd.waterlevel_risk, axis=1))
        rain = rain.assign(risk=rain.apply(fd.rain_risk, axis=1, heavy_1h=heavy_1h, heavy_24h=heavy_24h))

        results = {}
        for route_id in fd.ROUTES:
            route = load_route(route_id)
            forecast = load_forecast(tuple(fd.sample_route(route["coords"])))
            near_wl = fd.near_route(wl, route["coords"], buffer_km)
            near_rain = fd.near_route(rain, route["coords"], buffer_km)
            fc_max = float(forecast["precipitation"].max())
            segments = fd.assess_segments(route["segments"], near_wl, near_rain, buffer_km, heavy_1h, heavy_24h)
            km = segments.groupby("pass_level")["length_km"].sum().reindex(range(4), fill_value=0.0).to_dict()
            level = max(int(segments["pass_level"].max()), 1 if fc_max >= heavy_1h else 0)
            results[route_id] = dict(route=route, wl=near_wl, rain=near_rain, forecast=forecast, fc_max=fc_max,
                                     segments=segments, km=km, level=level)

    st.caption(t["updated"].format(t=f"{rain['datetime'].max():%d/%m/%Y %H:%M}"))

    airport = [k for k, v in fd.ROUTES.items() if v["group"] == "airport"]
    best = min(airport, key=lambda k: (results[k]["level"], results[k]["km"][3], results[k]["km"][2],
                                       results[k]["route"]["duration_min"]))

    st.subheader(t["airport_section"])
    if results[best]["level"] >= 2:
        st.warning(t["all_risky"], icon=":material/warning:")
    st.success(t["recommend"].format(name=fd.ROUTES[best]["name"][lang]), icon=":material/route:")
    with st.container(horizontal=not mobile):
        for route_id in airport:
            route_card(route_id, results[route_id], recommended=route_id == best)
    st.caption(t["compare_note"])

    st.subheader(t["wd_section"])
    with st.container(horizontal=not mobile):
        for route_id in [k for k, v in fd.ROUTES.items() if v["group"] == "wd"]:
            route_card(route_id, results[route_id])

    map_tab, detail_tab, bkk_tab, src_tab = st.tabs([t["tab_map"], t["tab_detail"], t["tab_bkk"], t["tab_sources"]])

    with map_tab:
        render_map(results, wl, rain)
    with detail_tab:
        route_id = st.selectbox(t["route"], list(results), format_func=lambda k: fd.ROUTES[k]["name"][lang], key="detail_route")
        render_route_detail(route_id, results[route_id])
    with bkk_tab:
        render_bangkok(wl, rain)
    with src_tab:
        render_sources()


def station_layers(wl, rain):
    rain = rain.assign(
        color=rain["risk"].map(fd.LEVEL_COLOR),
        radius=150 + rain["rain_24h"].fillna(0).clip(upper=200) * 8,
        tip=rain["station"].fillna("") + " (" + rain["amphoe"].fillna("") + ")<br/>" + t["col_rain1"] + ": "
        + rain["rain_1h"].astype(str) + "<br/>" + t["col_rain24"] + ": " + rain["rain_24h"].astype(str)
        + "<br/>" + rain["datetime"].dt.strftime("%d/%m %H:%M"),
    )
    wl = wl.assign(
        color=wl["risk"].map({0: [30, 120, 255], 1: [255, 165, 0], 2: [220, 20, 20]}),
        tip=t["wl_prefix"] + ": " + wl["station"].fillna("") + "<br/>" + wl["situation"].fillna("-") + " ("
        + wl["bank_percent"].round(0).astype(str) + t["bank_of"] + ")<br/>" + wl["datetime"].dt.strftime("%d/%m %H:%M"),
    )
    return [
        pdk.Layer("ScatterplotLayer", rain, get_position=["lon", "lat"], get_fill_color="color", get_radius="radius",
                  opacity=0.35, pickable=True, stroked=False),
        pdk.Layer("ScatterplotLayer", wl, get_position=["lon", "lat"], get_fill_color="color", get_radius=400,
                  get_line_color=[0, 0, 0], line_width_min_pixels=1, stroked=True, pickable=True),
    ]


def location_layer():
    locs = pd.DataFrame([{**v, "key": k, "tip": f"{k}<br/>{v['name']}"} for k, v in fd.LOCATIONS.items()])
    return [
        pdk.Layer("ScatterplotLayer", locs, get_position=["lon", "lat"], get_fill_color=[20, 20, 20], get_radius=700,
                  pickable=True),
        pdk.Layer("TextLayer", locs, get_position=["lon", "lat"], get_text="key", get_size=14, get_color=[0, 0, 0],
                  get_pixel_offset=[0, -18]),
    ]


def segment_tips(route_id, seg):
    return (fd.ROUTES[route_id]["name"][lang] + "<br/><b>" + seg["pass_level"].map(fd.PASS_LABEL[lang]) + "</b><br/>"
            + seg["road"].map(lambda n: fd.road_label(n, lang) or "-") + " · " + t["col_km"] + " "
            + seg["start_km"].round(0).astype(int).astype(str) + "<br/>" + t["col_rain1"] + ": " + seg["rain_1h"].round(1).astype(str)
            + " · " + t["col_rain24"] + ": " + seg["rain_24h"].round(1).astype(str))


def path_layer(results):
    paths = pd.concat([
        r["segments"].assign(color=r["segments"]["pass_level"].map(fd.PASS_COLOR), tip=segment_tips(k, r["segments"]))
        for k, r in results.items()
    ])[["path", "color", "tip"]]
    return [pdk.Layer("PathLayer", paths, get_path="path", get_color="color", width_min_pixels=6, pickable=True,
                      cap_rounded=True, joint_rounded=True)]


def pass_legend():
    with st.container(horizontal=True, vertical_alignment="center"):
        st.caption(t["pass_legend"])
        for level in range(4):
            st.badge(fd.PASS_LABEL[lang][level], color=fd.PASS_BADGE[level], icon=PASS_ICON[level])


def render_map(results, wl, rain):
    pass_legend()
    view = pdk.ViewState(latitude=13.9, longitude=100.95, zoom=7.3 if mobile else 8.3)
    st.pydeck_chart(pdk.Deck(station_layers(wl, rain) + path_layer(results) + location_layer(), initial_view_state=view,
                             tooltip={"html": "{tip}"}), height=MAP_H["main"])
    st.caption(t["map_legend"])


def render_route_detail(route_id, r):
    coords = r["route"]["coords"]
    lons, lats = [c[0] for c in coords], [c[1] for c in coords]
    span = max(max(lons) - min(lons), max(lats) - min(lats))
    zoom = (11 if span < 0.3 else 10 if span < 0.6 else 9 if span < 1.2 else 8) - (1 if mobile else 0)
    pass_legend()
    st.pydeck_chart(pdk.Deck(station_layers(r["wl"], r["rain"]) + path_layer({route_id: r}) + location_layer(),
                             initial_view_state=pdk.ViewState(latitude=(min(lats) + max(lats)) / 2,
                                                              longitude=(min(lons) + max(lons)) / 2, zoom=zoom),
                             tooltip={"html": "{tip}"}), height=MAP_H["detail"])

    st.subheader(t["problem_title"])
    seg = r["segments"]
    bad = seg[seg["pass_level"] >= 2]
    if bad.empty:
        st.success(t["no_problem"], icon=":material/check_circle:")
    else:
        st.dataframe(
            bad.assign(road=bad["road"].map(lambda n: fd.road_label(n, lang) or "-"),
                       status=bad["pass_level"].map(fd.PASS_LABEL[lang]),
                       wl=bad["wl_level"].map(fd.WL_SITUATION[lang]))
            .sort_values(["pass_level", "start_km"], ascending=[False, True])
            [["start_km", "road", "status", "rain_1h", "rain_24h", "wl", "elevated"]],
            hide_index=True,
            column_config={
                "start_km": st.column_config.NumberColumn(t["col_km"], format="%.0f"),
                "road": t["col_road"], "status": t["col_pass"], "wl": t["col_wl_level"],
                "rain_1h": st.column_config.NumberColumn(t["col_rain1"], format="%.1f"),
                "rain_24h": st.column_config.NumberColumn(t["col_rain24"], format="%.1f"),
                "elevated": st.column_config.CheckboxColumn(t["col_elevated"]),
            },
        )

    left, right = (st.container(), st.container()) if mobile else st.columns(2)
    with left:
        st.subheader(t["rain_near"])
        st.dataframe(
            r["rain"].sort_values(["risk", "rain_1h", "rain_24h"], ascending=False)[
                ["station", "amphoe", "province", "rain_1h", "rain_24h", "dist_km", "datetime", "risk"]],
            hide_index=True,
            column_config={
                "station": t["col_station"], "amphoe": t["col_amphoe"], "province": t["col_province"],
                "rain_1h": st.column_config.NumberColumn(t["col_rain1"], format="%.1f"),
                "rain_24h": st.column_config.ProgressColumn(t["col_rain24"], min_value=0, max_value=150, format="%.1f"),
                "dist_km": st.column_config.NumberColumn(t["col_dist"], format="%.1f"),
                "datetime": st.column_config.DatetimeColumn(t["col_time"], format="DD/MM HH:mm"),
                "risk": st.column_config.NumberColumn(t["col_risk"], help=t["col_risk_help"]),
            },
        )
    with right:
        st.subheader(t["wl_near"])
        st.dataframe(
            r["wl"][["station", "amphoe", "province", "situation", "bank_percent", "diff_bank_m", "dist_km", "datetime"]],
            hide_index=True,
            column_config={
                "station": t["col_station"], "amphoe": t["col_amphoe"], "province": t["col_province"],
                "situation": t["col_situation"],
                "bank_percent": st.column_config.ProgressColumn(t["col_bank"], min_value=0, max_value=120, format="%.0f%%"),
                "diff_bank_m": st.column_config.NumberColumn(t["col_diff"], format="%.2f"),
                "dist_km": st.column_config.NumberColumn(t["col_dist"], format="%.1f"),
                "datetime": st.column_config.DatetimeColumn(t["col_time"], format="DD/MM HH:mm"),
            },
        )

    st.subheader(t["fc_title"])
    fc = r["forecast"].groupby("time", as_index=False).agg(precipitation=("precipitation", "max"))
    st.bar_chart(fc, x="time", y="precipitation", x_label=t["fc_x"], y_label=t["fc_y"], height=250)


def render_bangkok(wl, rain):
    bkk_rain = rain[rain["province_code"] == fd.BANGKOK_PROVINCE_CODE]
    bkk_wl = wl[wl["province_code"] == fd.BANGKOK_PROVINCE_CODE]
    by_district = (bkk_rain.groupby("amphoe", as_index=False)
                   .agg(rain_1h=("rain_1h", "max"), rain_24h=("rain_24h", "max"), risk=("risk", "max"), stations=("station", "count"))
                   .sort_values(["risk", "rain_1h", "rain_24h"], ascending=False))
    by_district["status"] = by_district["risk"].map(fd.LEVEL_LABEL[lang])

    with st.container(horizontal=True):
        st.metric(t["bkk_stations"], len(bkk_rain), border=True)
        st.metric(t["bkk_risk"], int((by_district["risk"] == 2).sum()), border=True)
        st.metric(t["bkk_watch"], int((by_district["risk"] == 1).sum()), border=True)
        st.metric(t["rain1"], f"{bkk_rain['rain_1h'].max():.1f} {t['mm']}", border=True)
        st.metric(t["rain24"], f"{bkk_rain['rain_24h'].max():.1f} {t['mm']}", border=True)

    hotel = fd.LOCATIONS["Hotel"]
    st.pydeck_chart(pdk.Deck(station_layers(bkk_wl, bkk_rain) + location_layer(),
                             initial_view_state=pdk.ViewState(latitude=hotel["lat"], longitude=hotel["lon"] + 0.08,
                                                              zoom=9.5 if mobile else 10.3),
                             tooltip={"html": "{tip}"}), height=MAP_H["bkk"])

    st.subheader(t["by_district"])
    st.dataframe(
        by_district[["amphoe", "status", "rain_1h", "rain_24h", "stations"]],
        hide_index=True,
        column_config={
            "amphoe": t["col_district"], "status": t["col_status"], "stations": t["col_stations"],
            "rain_1h": st.column_config.NumberColumn(t["col_rain1_max"], format="%.1f"),
            "rain_24h": st.column_config.ProgressColumn(t["col_rain24_max"], min_value=0, max_value=150, format="%.1f"),
        },
    )


def render_sources():
    st.markdown(t["sources_intro"])
    st.dataframe(
        pd.DataFrame(t["sources"], columns=t["src_col"]),
        hide_index=True,
        column_config={t["src_col"][3]: st.column_config.LinkColumn(t["src_col"][3])},
    )
    st.subheader(t["method_title"])
    st.markdown(t["method"])


dashboard()
