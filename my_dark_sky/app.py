from flask import Flask, render_template, request
import requests
import json
import time
import os
from datetime import date, datetime

app = Flask(__name__)

CACHE_DIR = "cache"
CACHE_PATH = os.path.join(CACHE_DIR, "data.json")
CACHE_TTL = 300

# Каждое значение — кортеж (описание, иконка), потому что parse_daily
# распаковывает его в две переменные: desc, icon = WMO_CODES.get(...)
WMO_CODES = {
    0: ("Clear Sky", "☀️"), 1: ("Mostly Clear", "🌤️"), 2: ("Partly Cloudy", "⛅"),
    3: ("Overcast", "☁️"), 45: ("Foggy", "🌫️"), 48: ("Icy Fog", "🌫️"),
    51: ("Light Drizzle", "🌦️"), 53: ("Drizzle", "🌦️"), 55: ("Heavy Drizzle", "🌧️"),
    61: ("Light Rain", "🌦️"), 63: ("Rain", "🌧️"), 65: ("Heavy Rain", "🌧️"),
    71: ("Light Snow", "🌨️"), 73: ("Snow", "❄️"), 75: ("Heavy Snow", "❄️"),
    80: ("Light Showers", "🌦️"), 81: ("Showers", "🌧️"), 82: ("Heavy Showers", "🌧️"),
    95: ("Thunderstorm", "⛈️"), 96: ("Thunderstorm + Hail", "⛈️"), 99: ("Severe Thunderstorm", "⛈️"),
}


def read_cache():
    os.makedirs(CACHE_DIR, exist_ok=True)
    try:
        with open(CACHE_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def write_cache(data):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CACHE_PATH, "w") as f:
        json.dump(data, f)


def fetch_with_cache(url, params):
    store = read_cache()
    key = url + json.dumps(params, sort_keys=True)
    now = time.time()
    entry = store.get(key)
    if entry and (now - entry["ts"]) < CACHE_TTL:
        return entry["payload"], True
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    result = resp.json()
    store[key] = {"ts": now, "payload": result}
    write_cache(store)
    return result, False


def find_location(city):
    data, cached = fetch_with_cache(
        "https://geocoding-api.open-meteo.com/v1/search",
        {"name": city, "count": 1, "language": "en", "format": "json"}
    )
    results = data.get("results", [])
    if not results:
        return None, cached
    r = results[0]
    return {"name": r.get("name", city), "country": r.get("country", ""),
            "lat": r["latitude"], "lon": r["longitude"]}, cached


def fetch_weather(lat, lon, target_date):
    today = date.today()
    dt = datetime.strptime(target_date, "%Y-%m-%d").date()
    daily_vars = ["weather_code", "temperature_2m_max", "temperature_2m_min",
                  "apparent_temperature_max", "apparent_temperature_min",
                  "precipitation_sum", "wind_speed_10m_max", "sunrise", "sunset", "uv_index_max"]
    if dt < today:
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {"latitude": lat, "longitude": lon, "start_date": target_date,
                  "end_date": target_date, "daily": ",".join(daily_vars), "timezone": "auto"}
        mode = "history"
    else:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {"latitude": lat, "longitude": lon,
                  "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,cloud_cover",
                  "daily": ",".join(daily_vars), "start_date": target_date,
                  "end_date": target_date, "timezone": "auto"}
        mode = "forecast"
    data, cached = fetch_with_cache(url, params)
    return data, cached, mode


def parse_daily(data):
    d = data.get("daily", {})
    if not d or not d.get("time"):
        return None
    code = (d.get("weather_code") or [0])[0]
    if code is None:
        code = 0
    desc, icon = WMO_CODES.get(code, ("Unknown", "🌡️"))
    return {
        "date": d["time"][0], "icon": icon, "description": desc,
        "temp_max": (d.get("temperature_2m_max") or [None])[0],
        "temp_min": (d.get("temperature_2m_min") or [None])[0],
        "feels_max": (d.get("apparent_temperature_max") or [None])[0],
        "feels_min": (d.get("apparent_temperature_min") or [None])[0],
        "rain": (d.get("precipitation_sum") or [0])[0],
        "wind": (d.get("wind_speed_10m_max") or [None])[0],
        "sunrise": (d.get("sunrise") or [""])[0],
        "sunset": (d.get("sunset") or [""])[0],
        "uv": (d.get("uv_index_max") or [None])[0],
    }


@app.route("/")
def index():
    city = request.args.get("city", "").strip()
    lat = request.args.get("lat", "").strip()
    lon = request.args.get("lon", "").strip()
    sel_date = request.args.get("date", date.today().isoformat())
    try:
        datetime.strptime(sel_date, "%Y-%m-%d")
    except ValueError:
        sel_date = date.today().isoformat()
    ctx = dict(city=city or "Baku", selected_date=sel_date,
               location=None, weather=None, current=None, mode=None, cached=False, error=None)
    if not (city or (lat and lon)):
        return render_template("index.html", **ctx)
    try:
        if lat and lon:
            location = {"name": "My Location", "country": "", "lat": float(lat), "lon": float(lon)}
            from_cache = False
        else:
            location, from_cache = find_location(city)
            if not location:
                ctx["error"] = f"City '{city}' not found."
                return render_template("index.html", **ctx)
        raw, weather_cached, mode = fetch_weather(location["lat"], location["lon"], sel_date)
        daily = parse_daily(raw)
        current = raw.get("current")
        if not daily:
            ctx["error"] = "No weather data for this date."
            return render_template("index.html", **ctx)
        ctx.update(location=location, weather=daily, current=current,
                   mode=mode, cached=(from_cache or weather_cached))
   except requests.RequestException as e:
        import traceback; traceback.print_exc()
        ctx["error"] = f"Could not reach weather service: {e}"
    except Exception as e:
        import traceback; traceback.print_exc()
        ctx["error"] = f"Unexpected error: {e}"
        
    return render_template("index.html", **ctx)


if __name__ == "__main__":
    app.run(debug=True)