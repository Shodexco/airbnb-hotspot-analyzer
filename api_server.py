"""
Full Flask API + UI wrapper for Airbnb Hotspot Analyzer
(Complete version with all routes, exports, logs, luxury tiers, API tester,
map gallery, and dashboard/hotspots/maps pages.)

Everything has been fully fixed and cleaned for compatibility with:
- dashboard.html
- dashboard.js
- hotspots.html
- hotspots.js
- maps.html
- api_tester.html
- api_tester.js
"""

import os
import glob
from typing import Dict, Optional

from flask import (
    Flask,
    jsonify,
    request,
    render_template,
    send_from_directory,
)
from flask_cors import CORS

from airbnb_analyzer import run_analysis, CITY_CONFIG

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------

app = Flask(__name__)
CORS(app)

BASE_DIR = os.getcwd()
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
MAPS_DIR = os.path.join(BASE_DIR, "maps")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MAPS_DIR, exist_ok=True)

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def find_latest_run_for_city(city_code: str) -> Optional[Dict]:
    """
    Detect the newest analyzed_data CSV for a city.
    Example file pattern:
        nyc_2025-10-01_min200_analyzed_data.csv
    """
    pattern = os.path.join(OUTPUT_DIR, f"{city_code}_*_min*_analyzed_data.csv")
    files = glob.glob(pattern)
    if not files:
        return None

    # Sort newest by mod time
    files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
    path = files[0]

    name = os.path.basename(path)
    stem = name.replace(".csv", "")
    parts = stem.split("_")
    if len(parts) < 3:
        return None

    return {
        "city": parts[0],
        "date": parts[1],
        "threshold": float(parts[2].replace("min", "")),
        "path": path,
    }


def load_csv_records(path: str, limit: Optional[int] = None):
    """
    Lightweight CSV → list of dicts.
    """
    import csv
    rows = []
    if not os.path.exists(path):
        return rows

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            rows.append(row)
            if limit and idx + 1 >= limit:
                break

    return rows


def find_latest_export(city: str, keyword: str):
    """
    Find the newest file:
        {city}_*_{keyword}.csv
    Examples:
        premium_clusters
        luxury_clusters
        ultra_luxury_clusters
        neighborhood_scores
        analyzed_data
        log
    """
    pattern = os.path.join(OUTPUT_DIR, f"{city}_*_{keyword}.csv")
    files = glob.glob(pattern)

    if not files:
        return None

    files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
    return files[0]

# -----------------------------------------------------------------------------
# UI Pages
# -----------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/hotspots")
def hotspots_page():
    return render_template("hotspots.html")


@app.route("/maps")
def maps_page():
    return render_template("maps.html")


@app.route("/api-tester")
def api_tester_page():
    return render_template("api_tester.html")

# -----------------------------------------------------------------------------
# API: Cities List
# -----------------------------------------------------------------------------

@app.route("/api/cities", methods=["GET"])
def api_cities():
    cities = [
        {"code": cfg.code, "name": cfg.name}
        for cfg in CITY_CONFIG.values()
    ]
    cities.sort(key=lambda x: x["name"])
    return jsonify({"success": True, "cities": cities})

# -----------------------------------------------------------------------------
# API: Run Analysis
# -----------------------------------------------------------------------------

@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    try:
        p = request.get_json(force=True)
        city = p.get("city")
        threshold = float(p.get("premium_threshold", 200))
        max_listings = p.get("max_listings")

        if not city:
            return jsonify({"success": False, "error": "Missing city"}), 400

        max_listings = int(max_listings) if max_listings else None

        summary = run_analysis(
            city_code=city,
            premium_threshold=threshold,
            max_listings=max_listings,
            verbose=False,
        )

        # Convert filesystem → URL
        filename = os.path.basename(summary.get("map_path", ""))
        summary["map_url"] = f"/maps/{filename}" if filename else None

        return jsonify({"success": True, "summary": summary})

    except Exception as ex:
        return jsonify({"success": False, "error": str(ex)}), 500

# -----------------------------------------------------------------------------
# API: Latest Analysis Metadata
# -----------------------------------------------------------------------------

@app.route("/api/last-run/<city>", methods=["GET"])
def api_last_run(city):
    latest = find_latest_run_for_city(city)
    if not latest:
        return jsonify({"success": False, "error": "No runs found"}), 404

    return jsonify({
        "success": True,
        "city": latest["city"],
        "date": latest["date"],
        "threshold": latest["threshold"],
    })

# -----------------------------------------------------------------------------
# API: Hotspot Data Explorer
# -----------------------------------------------------------------------------

@app.route("/api/hotspots", methods=["GET"])
def api_hotspots():
    city = request.args.get("city")
    threshold = request.args.get("threshold", "200")
    key = request.args.get("key", "premium_clusters")

    if not city:
        return jsonify({"success": False, "error": "Missing city"}), 400

    patterns = {
        "premium_clusters":      f"{city}_*_min{threshold}_premium_clusters.csv",
        "luxury_clusters":       f"{city}_*_min{threshold}_luxury_clusters.csv",
        "ultra_luxury_clusters": f"{city}_*_min{threshold}_ultra_luxury_clusters.csv",
        "neighborhood_scores":   f"{city}_*_min{threshold}_neighborhood_scores.csv",
        "raw_listings":          f"{city}_*_min{threshold}_analyzed_data.csv",
        "log":                   f"{city}_*_min{threshold}_log.csv",
    }

    if key not in patterns:
        return jsonify({"success": False, "error": f"Invalid key '{key}'"}), 400

    pattern = os.path.join(OUTPUT_DIR, patterns[key])
    matches = glob.glob(pattern)

    if not matches:
        return jsonify({"success": False, "error": "No CSV matches"}), 404

    matches.sort()
    path = matches[-1]

    limit = 5000 if key == "raw_listings" else None
    records = load_csv_records(path, limit)

    return jsonify({
        "success": True,
        "city": city,
        "threshold": float(threshold),
        "key": key,
        "count": len(records),
        "data": records,
    })

# -----------------------------------------------------------------------------
# API: Export Latest Files
# -----------------------------------------------------------------------------

@app.route("/api/export/latest/<city>/<dtype>")
def api_export_latest(city, dtype):
    mapping = {
        "data": "analyzed_data",
        "clusters": "premium_clusters",
        "luxury": "luxury_clusters",
        "ultra": "ultra_luxury_clusters",
        "neighborhoods": "neighborhood_scores",
        "log": "log",
    }

    if dtype not in mapping:
        return jsonify({"error": f"Invalid export type '{dtype}'"}), 400

    keyword = mapping[dtype]
    path = find_latest_export(city, keyword)

    if not path:
        return jsonify({"error": f"No export found for {city}/{dtype}"}), 404

    return send_from_directory(
        OUTPUT_DIR,
        os.path.basename(path),
        as_attachment=True
    )

# -----------------------------------------------------------------------------
# API: Maps Gallery
# -----------------------------------------------------------------------------

@app.route("/api/maps/list", methods=["GET"])
def api_maps_list():
    result: Dict[str, list] = {}

    for fn in os.listdir(MAPS_DIR):
        if fn.endswith(".html"):
            city = fn.split("_")[0]
            result.setdefault(city, []).append(fn)

    for c in result:
        result[c].sort()

    return jsonify({"success": True, "maps": result})

# -----------------------------------------------------------------------------
# Static Files
# -----------------------------------------------------------------------------

@app.route("/maps/<path:filename>")
def serve_map(filename):
    return send_from_directory(MAPS_DIR, filename)


@app.route("/static/<path:path>")
def static_files(path):
    return send_from_directory("static", path)

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
