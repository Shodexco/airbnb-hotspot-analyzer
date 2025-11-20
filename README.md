# Airbnb Price Hotspot Analyzer

Geospatial analysis tool for identifying price patterns and investment opportunities in NYC Airbnb market.

![Airbnb Heatmap](screenshot.png)

## Features

🗺️ **Interactive Price Heatmap** - Visualize price distributions across NYC
📍 **Proximity Analysis** - Calculate distances to major landmarks  
🎯 **Cluster Detection** - DBSCAN spatial clustering for premium hotspots
💰 **Investment Scoring** - Multi-factor neighborhood ranking

## Technologies

- **GeoPandas** - Spatial operations and coordinate transformations
- **Folium** - Interactive map visualization  
- **Scikit-learn** - DBSCAN clustering algorithm
- **Shapely** - Geometric operations

## Setup
```bash
pip install pandas geopandas folium scikit-learn shapely
python airbnb_analyzer.py
```

## Dataset

NYC Airbnb Open Data (48K+ listings)  
Source: [Kaggle](https://www.kaggle.com/datasets/dgomonov/new-york-city-airbnb-open-data)

## Key Findings

- Identified 15+ premium listing clusters using DBSCAN
- Properties within 2km of landmarks show 35% price premium
- Manhattan and Williamsburg score highest for investment potential

## Technical Approach

1. **Data Processing**: Cleaned 48K+ listings, removed outliers
2. **Coordinate Transformation**: WGS84 → EPSG:3857 for accurate distance calculations
3. **Spatial Clustering**: DBSCAN with 300m epsilon, min 10 samples
4. **Proximity Analysis**: Calculated distances to 4 major NYC landmarks
5. **Scoring Algorithm**: Weighted combination of price, location, and demand factors

## Use Cases

- **Investors**: Identify optimal neighborhoods
- **Hosts**: Price optimization strategies
- **Market Research**: Understand rental patterns

## Author

Jonathan Sodeke - Data Engineer | ML Engineer  
Demonstrating geospatial analysis and spatial data science capabilities
