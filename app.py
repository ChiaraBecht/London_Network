import streamlit as st
import folium
from streamlit_folium import st_folium
#from streamlit_folium import folium_static
import json
import pandas as pd
#import networkx as nx
#from geopy.distance import geodesic
import geopandas as gpd
import ast
import os
os.environ["STREAMLIT_WATCH_USE_POLLING"] = "true"
os.environ["STREAMLIT_WATCH_DISABLE"] = "true"

# Load POIs
with open('data/pois_map_markers.json', 'r') as f:
    pois_map_markers = json.load(f)

# Get unique categories from the data
categories = sorted(set(marker['category'] for marker in pois_map_markers))
descriptions = sorted(set(p['description'] for p in pois_map_markers))

# Sidebar selectors
st.sidebar.title("Filter POIs")
selected_categories = st.sidebar.multiselect(
    "Select one or more categories",
    categories,
    default=categories  # Show all by default
)

selected_descriptions = st.sidebar.multiselect("Select by Description", descriptions, default=descriptions)

# Category-to-color mapping
category_colors = {
    'Sight': 'blue',
    'Shopping': 'purple',
    'Food': 'red',
    'Drinks': 'green',
    'Cafe': 'yellow',
    'Hotel': 'black'
}



# Filter data
filtered_markers = [
    p for p in pois_map_markers
    if p['category'] in selected_categories and p['description'] in selected_descriptions
]

# Create Folium Map
# Create map (larger size)
st.title("London Trip Planner")
st.markdown("Filter by category and description and hover to explore the places.")

# Checkbox to show neighborhoods
show_area = st.checkbox("Show Areas")

m = folium.Map(location=[51.501016, -0.123107], tiles='OpenStreetMap', zoom_start=13, control_scale=True)

# Conditionally add GeoJSON overlay
if show_area:
    with open("data/london_areas.geojson", "r") as f:
        geojson_data = json.load(f)

    folium.GeoJson(
        geojson_data,
        name="Areas",
        tooltip=folium.GeoJsonTooltip(fields=["name"]),
        style_function=lambda feature: {"fillColor": "228B22", "color": "black", "weight": 2, "fillOpacity": 0.2}
    ).add_to(m)

# Public Transportation lines to select or deselect
with open("data/tfl/relevant_lines.json", "r") as f:
    relevant_lines = json.load(f)

# add stops as markers
with open("data/tfl/relevant_stops.json", "r") as f:
    relevant_stops = json.load(f)

modes = ['bus', 'tube'] 

mode_selections = {mode: st.checkbox(f"Show {mode.title()}", value=True) for mode in modes}

# Your map, assuming it's created like this:
# m = folium.Map(location=[central_lat, central_lon], zoom_start=12)

for mode in modes:
    if mode_selections.get(mode, False):
        fg = folium.FeatureGroup(name=mode.title())

        for line in relevant_lines:
            if line["mode"] == mode:
                # Plot the line shape
                if line.get("shape"):
                    shape_coords = [[lat, lon] for lon, lat in line["shape"][0]]
                    folium.PolyLine(
                        shape_coords,
                        color="blue" if mode != "bus" else "red",
                        weight=3,
                        opacity=0.7,
                        tooltip=line.get("lineName", line.get("id", ""))
                    ).add_to(fg)

                # Only add stops that are in relevant_stops
                for stop in line.get("stops", []):
                    coord = (stop["lat"], stop["lon"])
                    if coord in relevant_stops:
                        print("coordinates found")
                        folium.CircleMarker(
                            location=[stop["lat"], stop["lon"]],
                            radius=3,
                            color="black",
                            fill=True,
                            fill_color="white",
                            fill_opacity=1.0,
                            tooltip=stop.get("name", stop.get("id", ""))
                        ).add_to(fg)

        fg.add_to(m)



# Add a layer control
#folium.LayerControl(collapsed=False).add_to(m)

# Add markers
for p in filtered_markers:
    color = category_colors.get(p['category'], 'gray')
    tooltip_text = f"{p['location_name']}<br><i>{p['description']}</i>"
    folium.CircleMarker(
        location=[p['lat'], p['lon']],
        radius=6,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.9,
        tooltip=tooltip_text,
    ).add_to(m)

# Streets / Areas
with open("data/streets_to_visit.geojson", "r") as f:
    polygon_view_points = json.load(f)

# Extract names of the polygons
polygon_features = polygon_view_points["features"]
polygon_names = [feat["properties"]["name"] for feat in polygon_features]

# Add multiselect to sidebar
selected_polygons = st.sidebar.multiselect(
    "Choose sights to show (polygons)",
    options=polygon_names,
    default=polygon_names  # or a subset if you want only some shown by default
)

# Add selected polygons
for feat in polygon_features:
    name = feat["properties"]["name"]
    if name in selected_polygons:
        folium.GeoJson(
            feat,
            tooltip=folium.GeoJsonTooltip(fields=["name"]),
            style_function=lambda feature: {
                "fillColor": "blue",
                "color": "black",
                "weight": 2,
                "fillOpacity": 0.3,
            }
        ).add_to(m)

# Display map in a bigger frame
#st_data = 
st_folium(m, width=900, height=600)

"""# Second map: m2 — showing transport network
df = pd.read_csv('data/locations_with_stops.csv')
locations_gdf = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(df['lon'], df['lat']),
    crs='EPSG:4326'
)
stops_df = pd.read_csv('data/stops.csv')
lines_df = pd.read_csv('data/lines.csv')
lines_df['stops'] = lines_df['stops'].apply(ast.literal_eval)"""

#m2 = folium.Map(location=[locations_gdf.geometry.y.mean(), locations_gdf.geometry.x.mean()], zoom_start=12)

# Add stops
"""for _, row in stops_df.iterrows():
    folium.CircleMarker(
        location=[row['lat'], row['lon']],
        radius=3,
        color='blue' if row['mode'] == 'tube' else 'green',
        fill=True,
        fill_opacity=0.6,
        tooltip=row['stop_name']
    ).add_to(m2)"""

# Add lines as connections (optional — you can also skip this if only plotting stops)
"""for _, row in lines_df.iterrows():
    stop_coords = []
    for stop_id in row['stops']:
        stop = stops_df[stops_df['stop_id'] == stop_id].iloc[0]
        stop_coords.append((stop['lat'], stop['lon']))
    folium.PolyLine(
        locations=stop_coords,
        color='red' if row['mode'] == 'tube' else 'green',
        weight=2,
        tooltip=row['name']
    ).add_to(m2)"""

"""st.markdown("###  Full Transport Network View")
st_folium(m2, width=900, height=600)"""

# adding schedule
daily_schedule = {
    "Monday": [("10:30", "Abflug Memmingen"), ("11:30", "Ankunft London Stansted"), ("12:00", "Transfer"), ("13:30", "Lunch"), ("15:00", "Buckingham Palace"), ("", "Westminster Abbey, Parliament, Big Ben + Photospot"), ("", "Uber Boat: Themse Tour"), ("", "Tower Bridge + Photspot"), ("", "Millenium Bridge"), ("", "St Pauls Cathedral maybe from inside or elevator ride"), ("15:00 - 21:00", "Check-In Hotel")],
    "Tuesday": [("", "Book Location Day"), ("16:40", "Arrival at Warner Bros. Studio Tour"), ("17:00", "Start Warner Bros. Studio Tour")],
    "Wednesday": [("", "English Breakfast at the Table"), ("11:00", "Horizon 22"), ("", "Book Shop"), ("", "St Dunstan in the east"), ("", "Tower of London"), ("", "Borough Market"), ("", "Shakespeares Globe Theater"), ("", "Temple and Fleet Street")],
    "Thursday": [("", "Harrods"), ("11:15", "Natural History Muesum"), ("", "Science Museum"), ("", "Covent Garden"), ("", "Piccadilly"), ("", "Trafalgar Square"), ("20:00", "Six Musical Vaudeville Theatre")],
    "Friday": [("", "Little Venice"), ("", "Notting Hill"), ("", "Kensington Palace"), ("", "Books"), ("", "maybe unlimited Cake"), ("", "Camden Market")],
    "Saturday": [("09:00 - 11:00", "Check-out"), ("", "Outernet"), ("", "Neals Yard"), ("13:10", "Transfer from Liverpool Street"), ("16:20", "Rückflug London Stanted"), ("19:05", "Ankunft Memmingen")]
}

# Tabs for each day
tabs = st.tabs(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])

for tab, day in zip(tabs, daily_schedule):
    with tab:
        st.subheader(f"Program for {day}")
        df = pd.DataFrame(daily_schedule[day], columns=["Time", "Activity"])
        #st.table(df)
        st.write(df)