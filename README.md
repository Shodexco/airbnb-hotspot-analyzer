# Airbnb Price Hotspot Analyzer

Geospatial analysis tool for identifying NYC Airbnb pricing patterns and investment opportunities using spatial clustering and proximity analysis.

![NYC Airbnb Heatmap](screenshot1.png)

## Overview

This project analyzes 48,000+ NYC Airbnb listings using geospatial techniques to identify premium clusters, price patterns, and location-based insights. Built to demonstrate spatial data analysis capabilities with real-world business applications.

## Features

🗺️ **Interactive Price Heatmap**
- Visualizes price distribution across all NYC boroughs
- Color-coded intensity showing premium vs budget areas

📍 **Spatial Clustering (DBSCAN)**
- Identifies premium listing clusters using 300m epsilon
- Analyzes cluster statistics (avg price, listing count, total value)

🎯 **Proximity Analysis**
- Calculates distances to major NYC landmarks
- Measures location premium effects on pricing

💰 **Neighborhood Investment Scoring**
- Multi-factor scoring algorithm
- Combines price, location, and demand metrics

## Tech Stack

- **GeoPandas** - Spatial operations and coordinate system transformations
- **Folium** - Interactive map visualization with heatmaps
- **Scikit-learn** - DBSCAN clustering algorithm
- **Shapely** - Geometric operations and distance calculations
- **Pandas** - Data manipulation and analysis

## Installation
```bash
# Clone repository
git clone https://github.com/Shodexco/airbnb-hotspot-analyzer.git
cd airbnb-hotspot-analyzer

# Install dependencies
pip install pandas geopandas folium scikit-learn shapely matplotlib seaborn

# Download dataset
# Visit: https://www.kaggle.com/datasets/dgomonov/new-york-city-airbnb-open-data
# Place AB_NYC_2019.csv in project root

# Run analysis
python airbnb_analyzer.py
```

## Usage
```python
# The script automatically:
# 1. Loads and cleans 48K+ Airbnb listings
# 2. Performs spatial clustering to find premium zones
# 3. Calculates proximity to major landmarks
# 4. Scores neighborhoods for investment potential
# 5. Generates interactive map (airbnb_hotspot_map.html)
```

## Key Findings

- **15+ Premium Clusters Identified** - Using DBSCAN spatial clustering
- **35% Location Premium** - Properties within 2km of major landmarks
- **Manhattan & Williamsburg** - Highest investment scores
- **Optimal Price Range** - $150-250/night for balanced occupancy

## Technical Approach

### Coordinate Transformation
Converted from WGS84 (lat/lon) to EPSG:3857 (Web Mercator) for accurate meter-based distance calculations.

### DBSCAN Clustering
- **Epsilon**: 300 meters (meaningful neighborhood scale)
- **Min Samples**: 10 listings (statistical significance)
- Identifies dense premium areas vs scattered listings

### Distance Calculations
Computed straight-line distances from each listing to 4 major landmarks:
- Times Square
- Central Park
- Empire State Building
- Brooklyn Bridge

### Investment Scoring Algorithm
```
Investment Score = (Price Score × 0.4) + 
                  (Location Score × 0.3) + 
                  (Demand Score × 0.3)
```

## Sample Output
```
======================================================================
AIRBNB PRICE HOTSPOT ANALYZER - Geospatial Analysis
======================================================================

[1/6] Loading Airbnb data...
   ✓ Loaded 48,895 Airbnb listings
   ✓ After cleaning: 48,818 listings
   ✓ Median price: $106/night

[3/6] Finding premium listing clusters using DBSCAN...
   ✓ Analyzing 12,204 premium listings (>$200/night)
   ✓ Found 17 clusters

   Top Premium Clusters:
   - Cluster #0: 6,252 listings, $329 avg, $2.0M total value
   - Cluster #1: 892 listings, $318 avg, $283K total value

[6/6] Creating interactive map...
   ✓ Map saved to: airbnb_hotspot_map.html
```

## Use Cases

- **Real Estate Investors**: Identify optimal neighborhoods for property acquisition
- **Hosts**: Price optimization based on location analysis
- **Market Research**: Understand short-term rental landscape
- **Urban Planning**: Analyze spatial patterns of vacation rentals

## Future Enhancements

- [ ] Time-series analysis of price trends
- [ ] PostGIS integration for production-scale queries
- [ ] Transportation accessibility scoring (subway proximity)
- [ ] Predictive pricing model using spatial features
- [ ] Real-time data pipeline via Airbnb API

## Project Structure
```
airbnb-hotspot-analyzer/
├── airbnb_analyzer.py          # Main analysis script
├── airbnb_hotspot_map.html     # Interactive visualization
├── premium_clusters.csv         # Cluster analysis results
├── neighborhood_scores.csv      # Investment rankings
├── requirements.txt             # Python dependencies
└── README.md                    # Project documentation
```

## Author

**Jonathan Sodeke** - Data Engineer | ML Engineer

Demonstrating geospatial analysis and spatial data science capabilities for real-world business applications.

- GitHub: [@Shodexco](https://github.com/Shodexco)
- LinkedIn: [Jonathan Sodeke](https://www.linkedin.com/in/jonathan-sodeke)
- Email: sodekejonathan@gmail.com

## Dataset

NYC Airbnb Open Data (2019)
- **Source**: [Kaggle](https://www.kaggle.com/datasets/dgomonov/new-york-city-airbnb-open-data)
- **Size**: 48,895 listings
- **Features**: Location, price, room type, availability, reviews

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Airbnb for making data publicly available
- GeoPandas community for excellent spatial tools
- NYC OpenData for geographic context