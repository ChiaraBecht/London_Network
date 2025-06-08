import streamlit as st
import folium
from streamlit_folium import st_folium
import json

# Load POIs
with open('data/pois_map_markers.json', 'r') as f:
    pois_map_markers = json.load(f)

# Get unique categories from the data
categories = sorted(set(marker['category'] for marker in pois_map_markers))

# Sidebar for category filter
st.sidebar.title("Filter by Category")
selected_categories = st.sidebar.multiselect(
    "Select one or more categories",
    categories,
    default=categories  # Show all by default
)

# Category-to-color mapping
category_colors = {
    'sight': 'blue',
    'food': 'green',
    'hotel': 'purple',
    # Add more if needed
}

# Create Folium Map
london_map = folium.Map(location=[51.501016, -0.123107], tiles='OpenStreetMap', zoom_start=13)

for marker in pois_map_markers:
    folium.CircleMarker(
        location=[marker['lat'], marker['lon']],
        radius=5,
        color='darkred',
        fill=True,
        fill_color='red',
        fill_opacity=0.8,
        tooltip=marker['location_name']
    ).add_to(london_map)

st.title('London Trip Planner')
st.markdown('Almost all our Places we want to visit')

st_folium(london_map, width=725, height=500)