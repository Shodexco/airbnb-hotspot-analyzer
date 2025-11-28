# 🏠 Airbnb Hotspot Analyzer  
**Multi-City Price Intelligence • Premium/Luxury Cluster Detection • Interactive Folium Maps • Real-Time API**

This project analyzes short-term rental markets using live InsideAirbnb snapshots.  
It automatically detects:

- 🔥 **Premium clusters** (mid-high tier: $200–$999)
- 💎 **Luxury clusters** ($1000–$2499)
- 👑 **Ultra-Luxury clusters** ($2500–$5000)
- 🗺️ **Neighborhood investment scores**
- 📍 **Landmark distance heatmaps**
- 🌐 **Interactive Folium maps with heatmaps + cluster markers**

Includes a **full frontend dashboard**, **Hotspot Explorer UI**, and a **REST API server**.

---

## 🚀 Features

### ✔ Live Snapshot Fetching
Scrapes Inside Airbnb’s “Get the Data” page to always download the most recent dataset for any supported city.

### ✔ Multi-Tier Cluster Detection
- DBSCAN clustering tuned per tier  
- Premium / Luxury / Ultra-Luxury separation  
- Coordinates projected to EPSG:3857 for real spatial accuracy  

### ✔ Beautiful Interactive Maps
- Heatmap of nightly prices  
- Gold, blue, red markers per tier  
- Optional BeautifyIcon stylized landmarks  
- One-click fullscreen mode  

### ✔ Built-in Dashboard UI
- City selector  
- Premium price threshold input  
- Download buttons  
- Embedded map viewer  
- Real-time logs  

### ✔ Hotspot Data Explorer
Browse:
- Premium clusters  
- Luxury clusters  
- Ultra-luxury clusters  
- Neighborhood scores  
- Raw listings  

### ✔ REST API
Endpoints to:
- run analysis  
- fetch latest CSV outputs  
- browse generated maps  
- list cities  

---

# 📦 Directory Structure

```
airbnb-hotspot-analyzer/
│
├── airbnb_analyzer.py        # Main analysis engine
├── api_server.py             # Flask server API + Dashboard UI
│
├── maps/                     # Auto-generated folium maps
├── output/                   # CSV + logs for each run
│
├── static/
│   ├── css/
│   ├── js/
│   │   ├── dashboard.js
│   │   ├── hotspots.js
│   │   └── api_tester.js
│
├── templates/
│   ├── dashboard.html
│   ├── hotspots.html
│   ├── maps.html
│   └── api_tester.html
│
└── README.md
```

---

# 🧠 **How It Works (Pipeline)**

1. **Scrape latest snapshot** from InsideAirbnb  
2. **Download listings.csv.gz**  
3. **Clean & normalize data**  
4. **Compute landmark proximity**  
5. **Cluster premium/luxury/ultra-luxury listings**  
6. **Score neighborhoods** using:
   - price score  
   - location score  
   - demand score  
7. **Generate interactive Folium map**  
8. **Export CSVs + logs**  
9. **Return summary for dashboard + API**

---

# 🖥️ Running the Dashboard

```
python api_server.py
```

Then open:

```
http://127.0.0.1:5000
```

Dashboard includes:

- Run analyzer  
- View logs  
- Export CSVs  
- View generated maps  
- Hotspot explorer  
- Built-in API tester page  

---

# 🛠 CLI Usage

```
python airbnb_analyzer.py --city boston --premium-threshold 200
```

---

# 🌍 Supported Cities

NYC, LA, SF, Boston, Chicago, Seattle, Washington-DC, Austin, Miami, London, Paris, Barcelona, Amsterdam, Rome, Berlin.

Add more via `CITY_CONFIG`.

---

# 📡 API Documentation

See full API docs file: **`API_DOCS.md`**  
(Scroll down — the file is included in this response.)

---

# 🧑‍💻 Development

Create a venv:

```
python -m venv .venv
source .venv/bin/activate      
# or Windows:
.venv\Scripts\activate
```

Install dependencies:

```
pip install -r requirements.txt
```

Run server:

```
python api_server.py
```

---

# 🤝 Contributing

See **`CONTRIBUTING.md`** below.

---

# 📝 Changelog

See **`CHANGELOG.md`**.

---

# ⭐ Author

Built by **Jonathan Sodeke**  
AI/ML Developer • Backend Engineer • Data Pipeline Architect  

If you use this project, star the repo ⭐ — it helps!
