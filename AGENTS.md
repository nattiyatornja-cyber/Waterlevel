# Waterbkk – flood route monitor

- Run: `python -m streamlit run app.py --server.port 8501`
- Headless check: `python -c "from streamlit.testing.v1 import AppTest; at=AppTest.from_file('app.py',default_timeout=180).run(); print(at.exception)"` (set `PYTHONIOENCODING=utf-8` on Windows)
- `flood_data.py`: locations/routes + data fetchers (ThaiWater API, Open-Meteo, OSRM). `app.py`: Streamlit UI.
- ThaiWater API has no CORS, so it must be fetched server-side.
- BMA road-flood sensor sites (weather.bangkok.go.th, dxg-api.dds.bangkok.go.th) reset connections from this network; passability is estimated per ~1 km segment in `flood_data.assess_segments`.
- Deploy target: Streamlit Community Cloud (private GitHub repo, entry `app.py`, Python 3.13). Keep `requirements.txt` pinned to the tested versions. Git is not installed locally; files are uploaded via the GitHub web UI.
- Public OSRM demo does not support `exclude=toll/motorway`; route variants are pinned with `via` waypoints + `bearings` in `ROUTES`.
