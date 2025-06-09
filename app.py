import streamlit as st
import folium
from streamlit_folium import st_folium
import json

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
    'Hotel': 'black'#'purple',
    # Add more if needed
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

m = folium.Map(location=[51.501016, -0.123107], tiles='OpenStreetMap', zoom_start=13, control_scale=True)

# Add markers
for p in filtered_markers:
    tooltip_text = f"{p['location_name']}<br><i>{p['description']}</i>"
    folium.CircleMarker(
        location=[p['lat'], p['lon']],
        radius=6,
        color=category_colors[p['category']],
        fill=True,
        fill_color=category_colors[p['category']],
        fill_opacity=0.9,
        tooltip=tooltip_text,
    ).add_to(m)

# Display map in a bigger frame
st_data = st_folium(m, width=900, height=600)