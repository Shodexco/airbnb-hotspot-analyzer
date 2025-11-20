"""
Airbnb Price Hotspot Analyzer
Geospatial analysis of NYC Airbnb listings
"""

import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
import folium
from folium.plugins import HeatMap
from sklearn.cluster import DBSCAN
import warnings
warnings.filterwarnings('ignore')

print("="*70)
print("AIRBNB PRICE HOTSPOT ANALYZER - Geospatial Analysis")
print("="*70)

# ============================================================================
# STEP 1: LOAD AND CLEAN DATA
# ============================================================================

print("\n[1/6] Loading Airbnb data...")

# Load the CSV file
df = pd.read_csv('AB_NYC_2019.csv')

print(f"   ✓ Loaded {len(df):,} Airbnb listings")

# Clean the data
df = df.dropna(subset=['latitude', 'longitude', 'price'])
df = df[df['price'] > 0]  # Remove free listings
df = df[df['price'] < 1000]  # Remove extreme outliers

print(f"   ✓ After cleaning: {len(df):,} listings")
print(f"   ✓ Price range: ${df['price'].min():.0f} - ${df['price'].max():.0f}")
print(f"   ✓ Median price: ${df['price'].median():.0f}")

# Create GeoDataFrame (adds geospatial capabilities)
geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
gdf = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')

print(f"   ✓ Created GeoDataFrame with {len(gdf):,} geo-locations")

# ============================================================================
# STEP 2: PRICE ANALYSIS BY BOROUGH
# ============================================================================

print("\n[2/6] Analyzing prices by borough...")

price_stats = df.groupby('neighbourhood_group').agg({
    'price': ['mean', 'median', 'count']
}).round(2)

print("\n   Price Statistics by Borough:")
print(price_stats)

# ============================================================================
# STEP 3: FIND PREMIUM CLUSTERS (SPATIAL CLUSTERING)
# ============================================================================

print("\n[3/6] Finding premium listing clusters using DBSCAN...")

def find_premium_clusters(gdf, min_price=200):
    """
    Use DBSCAN spatial clustering to find groups of expensive listings
    """
    # Filter to premium listings only
    premium_gdf = gdf[gdf['price'] >= min_price].copy()
    
    print(f"   ✓ Analyzing {len(premium_gdf)} premium listings (>${min_price}/night)")
    
    # Convert to meters for accurate distance calculations
    premium_gdf_m = premium_gdf.to_crs('EPSG:3857')
    
    # Get coordinates
    coords = np.array(list(zip(premium_gdf_m.geometry.x, premium_gdf_m.geometry.y)))
    
    # Run DBSCAN clustering
    # eps=300 means 300 meters, min_samples=10 means need at least 10 listings
    clustering = DBSCAN(eps=300, min_samples=10).fit(coords)
    premium_gdf['cluster'] = clustering.labels_
    
    print(f"   ✓ Found {len(set(clustering.labels_)) - 1} clusters")
    
    # Calculate cluster statistics
    clusters = []
    for cluster_id in set(clustering.labels_):
        if cluster_id == -1:  # Skip noise points
            continue
        
        cluster_data = premium_gdf[premium_gdf['cluster'] == cluster_id]
        
        clusters.append({
            'cluster_id': cluster_id,
            'center_lat': cluster_data['latitude'].mean(),
            'center_lon': cluster_data['longitude'].mean(),
            'listing_count': len(cluster_data),
            'avg_price': cluster_data['price'].mean(),
            'total_value': cluster_data['price'].sum()
        })
    
    return pd.DataFrame(clusters).sort_values('avg_price', ascending=False)

# Find the clusters
premium_clusters = find_premium_clusters(gdf, min_price=200)

print("\n   Top 5 Premium Clusters:")
if len(premium_clusters) > 0:
    print(premium_clusters.head().to_string(index=False))
else:
    print("   No clusters found (try lowering min_price)")

# ============================================================================
# STEP 4: PROXIMITY TO LANDMARKS
# ============================================================================

print("\n[4/6] Calculating distances to major landmarks...")

# Define NYC landmarks
landmarks = {
    'Times Square': (40.7580, -73.9855),
    'Central Park': (40.7829, -73.9654),
    'Empire State Building': (40.7484, -74.0047),
    'Brooklyn Bridge': (40.7061, -73.9969),
}

# Convert landmarks to GeoDataFrame
landmark_points = [Point(lon, lat) for lat, lon in landmarks.values()]
landmark_gdf = gpd.GeoDataFrame(
    {'name': list(landmarks.keys())},
    geometry=landmark_points,
    crs='EPSG:4326'
).to_crs('EPSG:3857')  # Convert to meters

# Convert listings to meters
gdf_m = gdf.to_crs('EPSG:3857')

# Calculate distance to nearest landmark for each listing
def calc_nearest_distance(listing_point):
    distances = landmark_gdf.geometry.distance(listing_point)
    return distances.min()

print("   ✓ Calculating distances (this may take a minute)...")
gdf['distance_to_landmark'] = gdf_m.geometry.apply(calc_nearest_distance)
gdf['distance_km'] = (gdf['distance_to_landmark'] / 1000).round(2)

# Analyze price vs distance
print("\n   Price vs Distance to Landmarks:")
distance_bins = [0, 2, 5, 10, 100]
distance_labels = ['<2km', '2-5km', '5-10km', '>10km']
gdf['distance_category'] = pd.cut(gdf['distance_km'], 
                                   bins=distance_bins, 
                                   labels=distance_labels)

distance_analysis = gdf.groupby('distance_category')['price'].agg(['mean', 'median', 'count'])
print(distance_analysis)

# ============================================================================
# STEP 5: NEIGHBORHOOD INVESTMENT SCORES
# ============================================================================

print("\n[5/6] Calculating neighborhood investment scores...")

neighborhood_stats = gdf.groupby('neighbourhood').agg({
    'price': 'mean',
    'id': 'count',
    'distance_km': 'mean',
    'number_of_reviews': 'mean'
}).rename(columns={'id': 'listing_count'})

# Calculate scores (0-100)
neighborhood_stats['price_score'] = (neighborhood_stats['price'] / neighborhood_stats['price'].max() * 100).round(1)
neighborhood_stats['location_score'] = (100 - neighborhood_stats['distance_km'] / neighborhood_stats['distance_km'].max() * 100).round(1)
neighborhood_stats['demand_score'] = (neighborhood_stats['number_of_reviews'] / neighborhood_stats['number_of_reviews'].max() * 100).round(1)

# Overall investment score
neighborhood_stats['investment_score'] = (
    neighborhood_stats['price_score'] * 0.4 +
    neighborhood_stats['location_score'] * 0.3 +
    neighborhood_stats['demand_score'] * 0.3
).round(1)

top_neighborhoods = neighborhood_stats.sort_values('investment_score', ascending=False).head(10)

print("\n   Top 10 Neighborhoods for Investment:")
print(top_neighborhoods[['investment_score', 'price', 'listing_count']])

# ============================================================================
# STEP 6: CREATE INTERACTIVE MAP
# ============================================================================

print("\n[6/6] Creating interactive map...")

# Create base map centered on NYC
m = folium.Map(
    location=[40.7128, -74.0060],
    zoom_start=11,
    tiles='CartoDB positron'
)

# Add price heatmap
print("   ✓ Adding price heatmap...")
heat_data = [[row['latitude'], row['longitude'], row['price']] 
             for idx, row in gdf.sample(min(5000, len(gdf))).iterrows()]  # Sample for performance
HeatMap(heat_data, radius=15, blur=25, max_zoom=13).add_to(m)

# Add premium clusters as markers
print("   ✓ Adding premium cluster markers...")
for idx, cluster in premium_clusters.head(10).iterrows():
    folium.CircleMarker(
        location=[cluster['center_lat'], cluster['center_lon']],
        radius=15,
        popup=f"""
        <b>Premium Cluster #{cluster['cluster_id']}</b><br>
        Listings: {cluster['listing_count']}<br>
        Avg Price: ${cluster['avg_price']:.0f}/night<br>
        Total Value: ${cluster['total_value']:.0f}
        """,
        color='gold',
        fill=True,
        fillColor='gold',
        fillOpacity=0.7
    ).add_to(m)

# Add landmarks
print("   ✓ Adding landmark markers...")
for name, (lat, lon) in landmarks.items():
    folium.Marker(
        location=[lat, lon],
        popup=f"<b>{name}</b>",
        icon=folium.Icon(color='red', icon='star')
    ).add_to(m)

# Save the map
m.save('airbnb_hotspot_map.html')
print("\n   ✓ Map saved to: airbnb_hotspot_map.html")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*70)
print("ANALYSIS COMPLETE!")
print("="*70)

print(f"\n📊 Key Findings:")
print(f"   • Total listings analyzed: {len(gdf):,}")
print(f"   • Premium clusters found: {len(premium_clusters)}")
print(f"   • Median price: ${gdf['price'].median():.0f}/night")

if len(top_neighborhoods) > 0:
    top_hood = top_neighborhoods.index[0]
    top_score = top_neighborhoods.iloc[0]['investment_score']
    print(f"   • Top investment neighborhood: {top_hood} (Score: {top_score}/100)")

print(f"\n🗺️  Open 'airbnb_hotspot_map.html' in your browser to see the interactive map!")
print("="*70)

# Export results
premium_clusters.to_csv('premium_clusters.csv', index=False)
neighborhood_stats.to_csv('neighborhood_scores.csv')
print("\n✓ Results exported to CSV files")