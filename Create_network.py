import json
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from sklearn.neighbors import BallTree
import numpy as np
import networkx as nx
import pickle

# Load locations of interest
with open('data/pois_map_markers.json') as f:
    location_data = json.load(f)

# Convert to DataFrame
locations_df = pd.DataFrame(location_data)

# Convert to GeoDataFrame
locations_gdf = gpd.GeoDataFrame(
    locations_df,
    geometry=[Point(lon, lat) for lon, lat in zip(locations_df['lon'], locations_df['lat'])],
    crs='EPSG:4326'  # WGS84
)

# Load public transportation data
with open('data/tfl/public_transportation.json') as f:
    transport_data = json.load(f)

# Parse stops and lines
preprocessed_lines = []
preprocessed_stops = []

for line in transport_data:
    print(line['lineId'])
    line_dict = {}

    # get line information
    line_dict['line_id'] = line['lineId']
    line_dict['name'] = line['lineName']
    line_dict['mode'] = line['mode']
    stops = [stop["id"] for stop in line["stops"]]
    line_dict['stops'] = stops
    preprocessed_lines.append(line_dict)

    # get stop information
    for stop in line["stops"]:
        stops_dict = {}
        stops_dict['stop_id'] = stop['id']
        stops_dict['stop_name'] = stop['name']
        stops_dict['lat'] = stop['lat']
        stops_dict['lon'] = stop['lon']
        stops_dict['mode'] = line['mode']
        preprocessed_stops.append(stops_dict)

stops_df = pd.DataFrame(preprocessed_stops)
line_df = pd.DataFrame(preprocessed_lines)
stops_df.to_csv('data/stops.csv')
line_df.to_csv('data/lines.csv')

# Convert stop coordinates to GeoDataFrame
stops_gdf = gpd.GeoDataFrame(
    stops_df,
    geometry=gpd.points_from_xy(stops_df['lon'], stops_df['lat']),
    crs='EPSG:4326'
)

# Project to a metric CRS for nearest neighbor
stops_gdf = stops_gdf.to_crs(epsg=3857)
locations_gdf = locations_gdf.to_crs(epsg=3857)

# Use BallTree to find nearest stop to each location
tree = BallTree(np.vstack([stops_gdf.geometry.x, stops_gdf.geometry.y]).T, metric='euclidean')
distances, indices = tree.query(np.vstack([locations_gdf.geometry.x, locations_gdf.geometry.y]).T, k=1)

locations_gdf['nearest_stop_index'] = indices.flatten()
locations_gdf['nearest_stop_id'] = stops_gdf.iloc[indices.flatten()]['stop_id'].values
print(locations_gdf.columns)

G = nx.Graph()

# Add nodes
for idx, row in locations_gdf.iterrows():
    G.add_node(row['location_name'], pos=(row.geometry.x, row.geometry.y), stop_id=row['nearest_stop_id'])

# Build connections from line info
# Assume each line contains a list of stops in order
for _, line in line_df.iterrows():
    stops = line['stops']  # ordered list of stop_ids
    mode = line['mode']
    line_name = line['name']
    
    # Connect each pair of stops with an edge (or only those in locations_gdf)
    for i in range(len(stops) - 1):
        stop_a, stop_b = stops[i], stops[i + 1]
        # Check if both stops are assigned to any of your interest locations
        nodes_a = locations_gdf[locations_gdf['nearest_stop_id'] == stop_a]
        nodes_b = locations_gdf[locations_gdf['nearest_stop_id'] == stop_b]
        if not nodes_a.empty and not nodes_b.empty:
            for node_a in nodes_a['location_name']:
                for node_b in nodes_b['location_name']:
                    G.add_edge(node_a, node_b, weight=1, line=line_name, mode=mode)


pickle.dump(G, open('data/network_graph.gpickle', 'wb'))
#locations_gdf.to_file('data/locations_with_stops.gejson', driver='GeoJSON')
# Go back to WGS84 before saving, for compatibility
locations_gdf = locations_gdf.to_crs(epsg=4326)

# Extract longitude and latitude before saving, since CSV doesn't support geometry
locations_gdf['lat'] = locations_gdf.geometry.y
locations_gdf['lon'] = locations_gdf.geometry.x

# Save as CSV instead of GeoJSON
locations_gdf.drop(columns='geometry').to_csv('data/locations_with_stops.csv', index=False)