# 📡 API Documentation — Airbnb Hotspot Analyzer

This API powers the dashboard UI and provides programmatic access for external tools.

Base URL (local):

```
http://127.0.0.1:5000
```

---

# 🏙️ GET /api/cities
Returns list of available cities.

### Response
```json
{
  "success": true,
  "cities": [
    { "code": "nyc", "name": "New York City" },
    { "code": "boston", "name": "Boston" },
    ...
  ]
}
```

---

# 🚀 POST /api/analyze

Runs a full analysis.

### Request
```json
{
  "city": "nyc",
  "premium_threshold": 200,
  "max_listings": 5000
}
```

### Response
Returns summary + map URL.

```json
{
  "success": true,
  "summary": {
    "city_code": "nyc",
    "city_name": "New York City",
    "data_date": "2025-09-23",
    "premium_threshold": 200,
    "total_listings": 3463,
    "premium_listing_count": 1742,
    "premium_cluster_count": 12,
    "luxury_cluster_count": 0,
    "ultra_luxury_cluster_count": 0,
    "map_url": "/maps/nyc_2025-09-23_min200.html",
    "log": "..."
  }
}
```

---

# 📁 GET /api/export/latest/<city>/<dtype>

Download latest CSV.

### Types (dtype)
- `data` → analyzed_data  
- `clusters` → premium_clusters  
- `luxury` → luxury_clusters  
- `ultra` → ultra_luxury_clusters  
- `neighborhoods` → neighborhood_scores  
- `log` → log file  

### Example
```
/api/export/latest/nyc/clusters
```

---

# 🔎 GET /api/hotspots

Used by Hotspot Explorer.

### Query parameters
- `city`
- `threshold`
- `key`:
  - premium_clusters  
  - luxury_clusters  
  - ultra_luxury_clusters  
  - neighborhood_scores  
  - raw_listings  
  - log  

---

# 🗺️ GET /api/maps/list

Returns all generated map files sorted by city.

---

# 📂 GET /maps/<file>

Serves interactive map HTML.

---

# 🔧 GET /static/<path>

Static file handler.

---

