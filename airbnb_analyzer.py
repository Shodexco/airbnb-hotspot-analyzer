"""
Airbnb Price Hotspot Analyzer - Multi-city version (ASCII safe)

Usage 1: CLI
    python airbnb_analyzer.py --city nyc --premium-threshold 200

Usage 2: As a library (used by api_server.py)
    from airbnb_analyzer import run_analysis
    summary = run_analysis(city_code="nyc", premium_threshold=200.0, verbose=False)
"""

import argparse
import os
import io
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Tuple, Optional, List

import warnings

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from sklearn.cluster import DBSCAN
import folium
from folium.plugins import HeatMap, BeautifyIcon
import requests
from bs4 import BeautifulSoup

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

BASE_URL = "http://data.insideairbnb.com"
GET_DATA_URL = "https://insideairbnb.com/get-the-data/"


# ---------------------------------------------------------------------------
# City configuration
# ---------------------------------------------------------------------------


@dataclass
class CityConfig:
    code: str
    name: str
    path: str
    center_lat: float
    center_lon: float
    landmarks: Dict[str, Tuple[float, float]]


CITY_CONFIG: Dict[str, CityConfig] = {
    "nyc": CityConfig(
        code="nyc",
        name="New York City",
        path="united-states/ny/new-york-city",
        center_lat=40.7128,
        center_lon=-74.0060,
        landmarks={
            "Times Square": (40.7580, -73.9855),
            "Central Park": (40.7829, -73.9654),
            "Empire State Building": (40.7484, -73.9857),
            "Brooklyn Bridge": (40.7061, -73.9969),
        },
    ),
    "la": CityConfig(
        code="la",
        name="Los Angeles",
        path="united-states/ca/los-angeles",
        center_lat=34.0522,
        center_lon=-118.2437,
        landmarks={
            "Hollywood Sign": (34.1341, -118.3215),
            "Santa Monica Pier": (34.0100, -118.4962),
        },
    ),
    "sf": CityConfig(
        code="sf",
        name="San Francisco",
        path="united-states/ca/san-francisco",
        center_lat=37.7749,
        center_lon=-122.4194,
        landmarks={
            "Golden Gate Bridge": (37.8199, -122.4783),
            "Fishermans Wharf": (37.8080, -122.4177),
        },
    ),
    "boston": CityConfig(
        code="boston",
        name="Boston",
        path="united-states/ma/boston",
        center_lat=42.3601,
        center_lon=-71.0589,
        landmarks={
            "Fenway Park": (42.3467, -71.0972),
        },
    ),
    "chicago": CityConfig(
        code="chicago",
        name="Chicago",
        path="united-states/il/chicago",
        center_lat=41.8781,
        center_lon=-87.6298,
        landmarks={
            "Millennium Park": (41.8826, -87.6226),
        },
    ),
    "seattle": CityConfig(
        code="seattle",
        name="Seattle",
        path="united-states/wa/seattle",
        center_lat=47.6062,
        center_lon=-122.3321,
        landmarks={
            "Space Needle": (47.6205, -122.3493),
        },
    ),
    "washington-dc": CityConfig(
        code="washington-dc",
        name="Washington DC",
        path="united-states/dc/washington-dc",
        center_lat=38.9072,
        center_lon=-77.0369,
        landmarks={
            "White House": (38.8977, -77.0365),
        },
    ),
    "austin": CityConfig(
        code="austin",
        name="Austin",
        path="united-states/tx/austin",
        center_lat=30.2672,
        center_lon=-97.7431,
        landmarks={
            "Texas Capitol": (30.2747, -97.7404),
        },
    ),
    "miami": CityConfig(
        code="miami",
        name="Miami",
        path="united-states/fl/miami",
        center_lat=25.7617,
        center_lon=-80.1918,
        landmarks={
            "South Beach": (25.7907, -80.1300),
        },
    ),
    "london": CityConfig(
        code="london",
        name="London",
        path="united-kingdom/england/london",
        center_lat=51.5074,
        center_lon=-0.1278,
        landmarks={
            "London Eye": (51.5033, -0.1195),
        },
    ),
    "paris": CityConfig(
        code="paris",
        name="Paris",
        path="france/ile-de-france/paris",
        center_lat=48.8566,
        center_lon=2.3522,
        landmarks={
            "Eiffel Tower": (48.8584, 2.2945),
        },
    ),
    "barcelona": CityConfig(
        code="barcelona",
        name="Barcelona",
        path="spain/catalonia/barcelona",
        center_lat=41.3851,
        center_lon=2.1734,
        landmarks={
            "Sagrada Familia": (41.4036, 2.1744),
        },
    ),
    "amsterdam": CityConfig(
        code="amsterdam",
        name="Amsterdam",
        path="the-netherlands/north-holland/amsterdam",
        center_lat=52.3676,
        center_lon=4.9041,
        landmarks={
            "Central Station": (52.3780, 4.9000),
        },
    ),
    "rome": CityConfig(
        code="rome",
        name="Rome",
        path="italy/lazio/rome",
        center_lat=41.9028,
        center_lon=12.4964,
        landmarks={
            "Colosseum": (41.8902, 12.4922),
        },
    ),
    "berlin": CityConfig(
        code="berlin",
        name="Berlin",
        path="germany/be/berlin",
        center_lat=52.5200,
        center_lon=13.4050,
        landmarks={
            "Brandenburg Gate": (52.5163, 13.3777),
        },
    ),
}


__all__ = ["run_analysis", "CITY_CONFIG", "CityConfig"]


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def ascii_header(title: str) -> str:
    line = "=" * 72
    return f"{line}\n{title}\n{line}"


# ---------------------------------------------------------------------------
# Data fetching and preparation
# ---------------------------------------------------------------------------


def _resolve_latest_listings_url(
    city: CityConfig, log: List[str]
) -> Tuple[str, str]:
    """
    Scrape the InsideAirbnb 'Get the Data' page and find the latest
    listings.csv.gz URL for the given city.path.

    Returns:
        (download_url, snapshot_date_iso)
    """
    log.append(ascii_header("DETECTING LATEST SNAPSHOT"))
    log.append(f"Loading index page: {GET_DATA_URL}")

    try:
        resp = requests.get(GET_DATA_URL, timeout=60)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to load {GET_DATA_URL}: {exc}") from exc

    if resp.status_code != 200:
        raise RuntimeError(
            f"HTTP {resp.status_code} while loading {GET_DATA_URL}"
        )

    soup = BeautifulSoup(resp.text, "html.parser")

    candidates: List[Tuple[datetime, str]] = []
    pattern = re.compile(r"/(\d{4}-\d{2}-\d{2})/")

    for a in soup.find_all("a", href=True):
        href = a["href"]
        # We only care about full listings CSVs for this city's data path
        if city.path in href and href.endswith("listings.csv.gz"):
            m = pattern.search(href)
            if not m:
                continue
            date_str = m.group(1)
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                continue
            candidates.append((dt, href))

    if not candidates:
        raise RuntimeError(
            f"No listings.csv.gz links found for city path '{city.path}'."
        )

    candidates.sort(key=lambda x: x[0], reverse=True)
    best_dt, best_href = candidates[0]
    snapshot_date = best_dt.date().isoformat()

    log.append(f"Detected latest snapshot for {city.name}: {snapshot_date}")
    log.append(f"Using download URL: {best_href}")

    return best_href, snapshot_date


def fetch_city_listings(
    city_code: str,
    max_listings: Optional[int] = None,
    log: Optional[List[str]] = None,
):
    """
    Fetch the latest listings.csv.gz for the given city by scraping the
    InsideAirbnb 'Get the Data' page and resolving the most recent snapshot.
    """
    if log is None:
        log = []
    if city_code not in CITY_CONFIG:
        raise ValueError(f"Unknown city code: {city_code}")

    city = CITY_CONFIG[city_code]
    log.append(
        ascii_header(f"FETCHING LISTINGS FOR {city.name.upper()} ({city.code})")
    )

    # Resolve latest snapshot URL
    try:
        listings_url, used_date = _resolve_latest_listings_url(city, log)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to detect snapshot date: {exc}") from exc

    # Download and load CSV
    try:
        resp = requests.get(listings_url, timeout=120)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to download {listings_url}: {exc}") from exc

    if resp.status_code != 200:
        raise RuntimeError(
            f"HTTP {resp.status_code} while downloading {listings_url}"
        )

    df = pd.read_csv(
        io.BytesIO(resp.content),
        compression="gzip",
        low_memory=False,
    )
    log.append(f"OK - loaded {len(df):,} listings from snapshot {used_date}")

    if max_listings is not None and len(df) > max_listings:
        df = df.sample(n=max_listings, random_state=42)
        log.append(f"Sampled down to {max_listings:,} listings for performance.")

    return df, used_date, log


def prepare_geodata(df: pd.DataFrame, log: List[str]):
    log.append(ascii_header("STEP 1 - DATA PREPARATION"))

    required_cols = ["latitude", "longitude", "price"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise RuntimeError(f"Input data is missing required columns: {missing}")

    # Clean price to numeric
    log.append("Converting price column to numeric dollars.")
    price = df["price"].astype(str)
    price = (
        price.str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    df["price"] = pd.to_numeric(price, errors="coerce")

    # Latitude and longitude
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    # Reviews (if present)
    if "number_of_reviews" in df.columns:
        df["number_of_reviews"] = (
            pd.to_numeric(df["number_of_reviews"], errors="coerce").fillna(0)
        )
    else:
        df["number_of_reviews"] = 0

    original = len(df)
    # Increase cap to 5000 to support luxury + ultra tiers
    df = df.dropna(subset=required_cols)
    df = df[(df["price"] > 0) & (df["price"] <= 5000)]

    log.append(f"Cleaned listings: {original:,} -> {len(df):,}")
    if len(df) == 0:
        raise RuntimeError(
            "No listings left after cleaning. Check filters or source data."
        )

    log.append(
        f"Price range: {df['price'].min():.0f} - {df['price'].max():.0f} dollars per night"
    )
    log.append(f"Median price: {df['price'].median():.0f} dollars per night")

    geometry = [Point(lon, lat) for lon, lat in zip(df["longitude"], df["latitude"])]
    gdf = gpd.GeoDataFrame(df.copy(), geometry=geometry, crs="EPSG:4326")
    return gdf, log


def add_landmark_distances(
    gdf: gpd.GeoDataFrame,
    city: CityConfig,
    log: List[str],
):
    log.append(ascii_header("STEP 2 - LANDMARK PROXIMITY"))

    if not city.landmarks:
        log.append(
            "No landmark configuration for this city. Skipping distance analysis."
        )
        gdf["distance_km"] = np.nan
        return gdf, log

    landmark_points = [Point(lon, lat) for lat, lon in city.landmarks.values()]
    landmark_gdf = gpd.GeoDataFrame(
        {"name": list(city.landmarks.keys())},
        geometry=landmark_points,
        crs="EPSG:4326",
    ).to_crs("EPSG:3857")

    gdf_m = gdf.to_crs("EPSG:3857")

    def nearest_distance(pt):
        return landmark_gdf.distance(pt).min()

    log.append(
        "Computing distance in meters to nearest landmark (this can take a while)."
    )
    gdf["distance_m"] = gdf_m.geometry.apply(nearest_distance)
    gdf["distance_km"] = (gdf["distance_m"] / 1000.0).round(2)

    bins = [0, 2, 5, 10, 100]
    labels = ["<2km", "2-5km", "5-10km", ">10km"]
    gdf["distance_cat"] = pd.cut(gdf["distance_km"], bins=bins, labels=labels)

    dist_stats = gdf.groupby("distance_cat")["price"].agg(["mean", "median", "count"])
    log.append("Price by distance bucket (mean / median / count):")
    log.append(str(dist_stats))

    return gdf, log


# ---------------------------------------------------------------------------
# Premium / Luxury / Ultra-Luxury clusters
# ---------------------------------------------------------------------------


def _detect_band_clusters(
    gdf: gpd.GeoDataFrame,
    min_price: float,
    max_price: float,
    label: str,
    log: List[str],
):
    """
    Generic helper to detect clusters in a specific price band.
    Tier-aware DBSCAN params + full safety on empty results.
    """
    band = gdf[(gdf["price"] >= min_price) & (gdf["price"] < max_price)].copy()

    # ---- Safe formatting for band description ----
    if max_price < 999999:
        max_price_display = f"{max_price:.0f}"
    else:
        max_price_display = str(max_price)

    log.append(
        f"{label} band: {min_price:.0f} - {max_price_display} dollars per night."
    )
    log.append(
        f"{label} listings: {len(band):,} "
        f"({(len(band) / len(gdf) * 100):.1f} percent of total)"
    )

    # If no listings at all in this band → short-circuit
    if band.empty:
        log.append(f"No {label.lower()} listings found in this band.")
        band["cluster"] = -1
        return band, pd.DataFrame(), log

    # If too few listings for DBSCAN
    if len(band) < 10:
        log.append(f"Not enough {label.lower()} listings for clustering. Skipping DBSCAN.")
        if "cluster" not in band.columns:
            band["cluster"] = -1
        return band, pd.DataFrame(), log

    # Tier-aware DBSCAN parameters
    label_lower = label.lower()
    if label_lower == "premium":
        eps = 300.0
        min_samples = 10
    elif label_lower == "luxury":
        eps = 500.0
        min_samples = 6
    elif label_lower == "ultra luxury":
        eps = 700.0
        min_samples = 3
    else:
        eps = 300.0
        min_samples = 10

    # Project to meters (Web Mercator) for DBSCAN
    band_m = band.to_crs("EPSG:3857")
    coords = np.column_stack([band_m.geometry.x, band_m.geometry.y])

    clustering = DBSCAN(eps=eps, min_samples=min_samples)
    labels = clustering.fit_predict(coords)
    band["cluster"] = labels

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    log.append(f"{label}: DBSCAN finished. Clusters found (excluding noise): {n_clusters}")

    clusters: List[Dict] = []
    for cid in sorted(set(labels)):
        if cid == -1:
            continue
        cluster_data = band[band["cluster"] == cid]
        clusters.append(
            {
                "cluster_id": int(cid),
                "center_lat": float(cluster_data["latitude"].mean()),
                "center_lon": float(cluster_data["longitude"].mean()),
                "listing_count": int(len(cluster_data)),
                "avg_price": float(cluster_data["price"].mean()),
                "max_price": float(cluster_data["price"].max()),
                "total_value": float(cluster_data["price"].sum()),
                "tier": label,
            }
        )

    cluster_df = pd.DataFrame(clusters)
    if cluster_df.empty:
        log.append(f"No dense {label.lower()} clusters found.")
        return band, cluster_df, log

    cluster_df = cluster_df.sort_values("avg_price", ascending=False)
    log.append(f"Top {label.lower()} clusters (by average price):")
    log.append(str(cluster_df.head(5)[["cluster_id", "listing_count", "avg_price"]]))

    return band, cluster_df, log


def detect_premium_clusters(
    gdf: gpd.GeoDataFrame,
    premium_threshold: float,
    log: List[str],
):
    """
    Premium band: [premium_threshold, 1000)
    """
    log.append(ascii_header("STEP 3 - PREMIUM HOTSPOT DETECTION"))
    return _detect_band_clusters(
        gdf=gdf,
        min_price=premium_threshold,
        max_price=1000.0,
        label="Premium",
        log=log,
    )


def detect_luxury_clusters(
    gdf: gpd.GeoDataFrame,
    log: List[str],
):
    """
    Luxury band: [1000, 2500)
    """
    log.append(ascii_header("STEP 3B - LUXURY HOTSPOT DETECTION"))
    return _detect_band_clusters(
        gdf=gdf,
        min_price=1000.0,
        max_price=2500.0,
        label="Luxury",
        log=log,
    )


def detect_ultra_luxury_clusters(
    gdf: gpd.GeoDataFrame,
    log: List[str],
):
    """
    Ultra Luxury band: [2500, 5000]
    We'll implement as [2500, 5001) to include 5000 safely.
    """
    log.append(ascii_header("STEP 3C - ULTRA LUXURY HOTSPOT DETECTION"))
    return _detect_band_clusters(
        gdf=gdf,
        min_price=2500.0,
        max_price=5001.0,
        label="Ultra Luxury",
        log=log,
    )


# ---------------------------------------------------------------------------
# Neighborhood scoring
# ---------------------------------------------------------------------------


def score_neighborhoods(
    gdf: gpd.GeoDataFrame,
    log: List[str],
):
    log.append(ascii_header("STEP 4 - NEIGHBORHOOD INVESTMENT SCORES"))

    hood_col: Optional[str] = None
    for col in ["neighbourhood_cleansed", "neighbourhood"]:
        if col in gdf.columns:
            hood_col = col
            break

    if hood_col is None:
        log.append("No neighborhood column in dataset. Skipping investment scores.")
        return pd.DataFrame(), log

    stats = gdf.groupby(hood_col).agg(
        price=("price", "mean"),
        listing_count=("id", "count") if "id" in gdf.columns else ("price", "count"),
        distance_km=("distance_km", "mean"),
        number_of_reviews=("number_of_reviews", "mean"),
    )

    def norm(series: pd.Series) -> pd.Series:
        if series.max() == 0:
            return series * 0
        return (series / series.max()) * 100.0

    stats["price_score"] = norm(stats["price"]).round(1)
    if stats["distance_km"].notna().any():
        stats["location_score"] = (100.0 - norm(stats["distance_km"])).round(1)
    else:
        stats["location_score"] = 0.0
    stats["demand_score"] = norm(stats["number_of_reviews"]).round(1)

    stats["investment_score"] = (
        stats["price_score"] * 0.4
        + stats["location_score"] * 0.3
        + stats["demand_score"] * 0.3
    ).round(1)

    top = stats.sort_values("investment_score", ascending=False).head(10)
    log.append("Top neighborhoods by investment score:")
    log.append(str(top[["investment_score", "price", "listing_count"]]))

    return stats, log


# ---------------------------------------------------------------------------
# Map and CSV exports
# ---------------------------------------------------------------------------


def build_map(
    gdf: gpd.GeoDataFrame,
    premium_clusters: pd.DataFrame,
    luxury_clusters: pd.DataFrame,
    ultra_clusters: pd.DataFrame,
    city: CityConfig,
    premium_threshold: float,
    data_date: str,
    maps_dir: str,
    log: List[str],
) -> str:
    log.append(ascii_header("STEP 5 - MAP CREATION"))

    os.makedirs(maps_dir, exist_ok=True)

    center_lat = gdf["latitude"].mean() if not gdf.empty else city.center_lat
    center_lon = gdf["longitude"].mean() if not gdf.empty else city.center_lon

    fmap = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=11,
        tiles="CartoDB positron",
    )

    # Heatmap of prices
    sample = gdf.sample(min(5000, len(gdf)), random_state=42)
    heat_data = [
        [row["latitude"], row["longitude"], row["price"]] for _, row in sample.iterrows()
    ]
    HeatMap(heat_data, radius=15, blur=25, max_zoom=13).add_to(fmap)
    log.append(f"Added heatmap with {len(sample)} sample listings.")

    # Premium clusters (gold)
    if not premium_clusters.empty:
        for _, cl in premium_clusters.iterrows():
            folium.CircleMarker(
                location=[cl["center_lat"], cl["center_lon"]],
                radius=15,
                popup=(
                    f"Premium cluster {int(cl['cluster_id'])}<br>"
                    f"Listings: {int(cl['listing_count'])}<br>"
                    f"Average price: ${cl['avg_price']:.0f}"
                ),
                color="gold",
                fill=True,
                fill_color="gold",
                fill_opacity=0.7,
            ).add_to(fmap)
        log.append(f"Added {len(premium_clusters)} premium cluster markers.")
    else:
        log.append("No premium clusters to show on the map.")

    # Luxury clusters (blue)
    if not luxury_clusters.empty:
        for _, cl in luxury_clusters.iterrows():
            folium.CircleMarker(
                location=[cl["center_lat"], cl["center_lon"]],
                radius=17,
                popup=(
                    f"Luxury cluster {int(cl['cluster_id'])}<br>"
                    f"Listings: {int(cl['listing_count'])}<br>"
                    f"Average price: ${cl['avg_price']:.0f}"
                ),
                color="blue",
                fill=True,
                fill_color="blue",
                fill_opacity=0.6,
            ).add_to(fmap)
        log.append(f"Added {len(luxury_clusters)} luxury cluster markers.")
    else:
        log.append("No luxury clusters to show on the map.")

    # Ultra Luxury clusters (red)
    if not ultra_clusters.empty:
        for _, cl in ultra_clusters.iterrows():
            folium.CircleMarker(
                location=[cl["center_lat"], cl["center_lon"]],
                radius=19,
                popup=(
                    f"Ultra Luxury cluster {int(cl['cluster_id'])}<br>"
                    f"Listings: {int(cl['listing_count'])}<br>"
                    f"Average price: ${cl['avg_price']:.0f}"
                ),
                color="red",
                fill=True,
                fill_color="red",
                fill_opacity=0.6,
            ).add_to(fmap)
        log.append(f"Added {len(ultra_clusters)} ultra luxury cluster markers.")
    else:
        log.append("No ultra luxury clusters to show on the map.")

    # Landmark markers with BeautifyIcon
    if city.landmarks:
        for name, (lat, lon) in city.landmarks.items():
            folium.Marker(
                location=[lat, lon],
                popup=f"<b>{name}</b>",
                icon=BeautifyIcon(
                    icon="star",
                    icon_shape="marker",
                    background_color="#1E90FF",
                    border_color="#000",
                    text_color="white",
                ),
            ).add_to(fmap)
        log.append(f"Added {len(city.landmarks)} landmark markers.")
    else:
        log.append("No landmarks configured for this city; skipping landmark markers.")

    fname = f"{city.code}_{data_date}_min{int(premium_threshold)}.html"
    full_path = os.path.join(maps_dir, fname)
    fmap.save(full_path)
    log.append(f"Map saved to: {full_path}")

    return full_path


def export_outputs(
    gdf: gpd.GeoDataFrame,
    premium_clusters: pd.DataFrame,
    luxury_clusters: pd.DataFrame,
    ultra_clusters: pd.DataFrame,
    neighborhood_scores: pd.DataFrame,
    outputs_dir: str,
    city: CityConfig,
    data_date: str,
    premium_threshold: float,
    log: List[str],
):
    log.append(ascii_header("STEP 6 - EXPORTING CSV OUTPUTS"))

    os.makedirs(outputs_dir, exist_ok=True)

    prefix = f"{city.code}_{data_date}_min{int(premium_threshold)}"

    # Main analyzed data
    main_path = os.path.join(outputs_dir, f"{prefix}_analyzed_data.csv")
    gdf.to_csv(main_path, index=False)
    log.append(f"Saved main analyzed data to {main_path}")

    # Premium clusters
    if not premium_clusters.empty:
        clusters_path = os.path.join(outputs_dir, f"{prefix}_premium_clusters.csv")
        premium_clusters.to_csv(clusters_path, index=False)
        log.append(f"Saved premium clusters to {clusters_path}")
    else:
        log.append("No premium clusters CSV exported (no clusters).")

    # Luxury clusters
    if not luxury_clusters.empty:
        luxury_path = os.path.join(outputs_dir, f"{prefix}_luxury_clusters.csv")
        luxury_clusters.to_csv(luxury_path, index=False)
        log.append(f"Saved luxury clusters to {luxury_path}")
    else:
        log.append("No luxury clusters CSV exported (no clusters).")

    # Ultra Luxury clusters
    if not ultra_clusters.empty:
        ultra_path = os.path.join(outputs_dir, f"{prefix}_ultra_luxury_clusters.csv")
        ultra_clusters.to_csv(ultra_path, index=False)
        log.append(f"Saved ultra luxury clusters to {ultra_path}")
    else:
        log.append("No ultra luxury clusters CSV exported (no clusters).")

    # Neighborhood scores
    if not neighborhood_scores.empty:
        hood_path = os.path.join(outputs_dir, f"{prefix}_neighborhood_scores.csv")
        neighborhood_scores.to_csv(hood_path)
        log.append(f"Saved neighborhood scores to {hood_path}")
    else:
        log.append("No neighborhood scores CSV exported.")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def normalize_city_code(raw_city: str) -> str:
    """Accept short code or full name, return canonical city code."""
    if not raw_city:
        raise ValueError("City is required.")
    raw = raw_city.strip().lower()

    if raw in CITY_CONFIG:
        return raw

    simplified = raw.replace("_", "").replace("-", "").replace(" ", "")
    for code, cfg in CITY_CONFIG.items():
        if simplified == code.replace("-", ""):
            return code
        if simplified == cfg.name.replace(" ", "").lower():
            return code

    valid = ", ".join(sorted(CITY_CONFIG.keys()))
    raise ValueError(f"Unknown city: {raw_city}. Valid options: {valid}")


def run_analysis(
    city_code: str,
    premium_threshold: float = 200.0,
    max_listings: Optional[int] = None,
    maps_dir: str = "maps",
    outputs_dir: str = "output",
    verbose: bool = True,
) -> Dict:
    """
    Run the full pipeline and return a summary dictionary.

    This is the main entry point used by api_server.py.
    """
    log: List[str] = []

    code = normalize_city_code(city_code)
    city = CITY_CONFIG[code]

    log.append(ascii_header("AIRBNB PRICE HOTSPOT ANALYZER"))

    # Pipeline
    df, data_date, log = fetch_city_listings(code, max_listings=max_listings, log=log)
    gdf, log = prepare_geodata(df, log)
    gdf, log = add_landmark_distances(gdf, city, log)

    # Premium / Luxury / Ultra-Luxury tiers
    premium_gdf, premium_clusters_df, log = detect_premium_clusters(
        gdf, premium_threshold, log
    )
    luxury_gdf, luxury_clusters_df, log = detect_luxury_clusters(gdf, log)
    ultra_gdf, ultra_clusters_df, log = detect_ultra_luxury_clusters(gdf, log)

    hood_scores, log = score_neighborhoods(gdf, log)

    map_path = build_map(
        gdf=gdf,
        premium_clusters=premium_clusters_df,
        luxury_clusters=luxury_clusters_df,
        ultra_clusters=ultra_clusters_df,
        city=city,
        premium_threshold=premium_threshold,
        data_date=data_date,
        maps_dir=maps_dir,
        log=log,
    )

    export_outputs(
        gdf=gdf,
        premium_clusters=premium_clusters_df,
        luxury_clusters=luxury_clusters_df,
        ultra_clusters=ultra_clusters_df,
        neighborhood_scores=hood_scores,
        outputs_dir=outputs_dir,
        city=city,
        data_date=data_date,
        premium_threshold=premium_threshold,
        log=log,
    )

    # Save full log to a .txt file
    prefix = f"{city.code}_{data_date}_min{int(premium_threshold)}"
    log_path = os.path.join(outputs_dir, f"{prefix}_log.txt")

    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log))

    log.append(f"Saved run log to {log_path}")

    summary: Dict = {
        "city_code": city.code,
        "city_name": city.name,
        "data_date": data_date,
        "premium_threshold": float(premium_threshold),
        "total_listings": int(len(gdf)),
        "median_price": float(gdf["price"].median()),
        "premium_listing_count": int(len(premium_gdf)),
        "premium_cluster_count": int(len(premium_clusters_df))
        if not premium_clusters_df.empty
        else 0,
        "luxury_cluster_count": int(len(luxury_clusters_df))
        if not luxury_clusters_df.empty
        else 0,
        "ultra_luxury_cluster_count": int(len(ultra_clusters_df))
        if not ultra_clusters_df.empty
        else 0,
        "map_path": map_path,
        "log": "\n".join(log),
    }

    if verbose:
        print(summary["log"])
        print(ascii_header("SUMMARY"))
        print(f"City: {summary['city_name']} ({summary['city_code']})")
        print(f"Data date: {summary['data_date']}")
        print(f"Listings analyzed: {summary['total_listings']:,}")
        print(f"Median price: ${summary['median_price']:.0f} per night")
        print(f"Premium threshold: ${summary['premium_threshold']:.0f}")
        print(f"Premium clusters: {summary['premium_cluster_count']}")
        print(f"Luxury clusters: {summary['luxury_cluster_count']}")
        print(f"Ultra Luxury clusters: {summary['ultra_luxury_cluster_count']}")
        print(f"Map file: {summary['map_path']}")

    return summary


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Airbnb hotspot analyzer (multi-city, ASCII safe)"
    )
    parser.add_argument(
        "--city",
        required=True,
        help="City code or name, for example nyc or 'New York City'",
    )
    parser.add_argument(
        "--premium-threshold",
        type=float,
        default=200.0,
        help="Price per night that defines a premium listing (default 200).",
    )
    parser.add_argument(
        "--max-listings",
        type=int,
        default=None,
        help=(
            "Optional maximum number of listings to analyze "
            "(sampled if more are available)."
        ),
    )

    args = parser.parse_args()

    run_analysis(
        city_code=args.city,
        premium_threshold=args.premium_threshold,
        max_listings=args.max_listings,
        verbose=True,
    )


if __name__ == "__main__":
    main()
