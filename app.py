import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import pandas as pd
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

# add Public Transportation
with open("data/tfl/public_transportation.json", "r") as f:
    transport_data = json.load(f)

modes = sorted(set(item["mode"] for item in transport_data))

mode_selections = {mode: st.checkbox(f"Show {mode.title()}", value=True) for mode in modes}

for mode in modes:
    if mode_selections[mode]:
        fg = folium.FeatureGroup(name=mode.title())
        for line in transport_data:
            if line["mode"] == mode:
                # Flip (lon, lat) → (lat, lon)
                shape = [(lat, lon) for lon, lat in line["shape"]]

                folium.PolyLine(
                    shape,
                    color="blue" if mode != "bus" else "red",
                    weight=3,
                    opacity=0.7,
                ).add_to(fg)
        fg.add_to(m)

"""for mode in modes:
    if mode_selections[mode]:
        fg = folium.FeatureGroup(name=mode.title())
        for line in transport_data:
            if line["mode"] == mode:
                folium.PolyLine(
                    line["shape"],
                    color="blue" if mode != "bus" else "red",
                    weight=3,
                    opacity=0.7,
                    #tooltip=line["lineName"]
                ).add_to(fg)
        fg.add_to(m)

folium.LayerControl(collapsed=False).add_to(m)"""

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


# adding schedule
daily_schedule = {
    "Monday": [("10:30", "Abflug Memmingen"), ("11:30", "Ankunft London Stansted"), ("15:00 - 21:00", "Check-In Hotel")],
    "Tuesday": [("16:40", "Arrival at Warner Bros. Studio Tour"), ("17:00", "Start Warner Bros. Studio Tour")],
    "Wednesday": [("11:00", "Horizon 22")],
    "Thursday": [("time", "sth"), ("20:00", "Six Musical Vaudeville Theatre")],
    "Friday": [("time", "sth")],
    "Saturday": [("09:00 - 11:00", "Check-out"), ("16:20", "Rückflug London Stanted"), ("19:05", "Ankunft Memmingen")]
}

# Tabs for each day
tabs = st.tabs(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])

for tab, day in zip(tabs, daily_schedule):
    with tab:
        st.subheader(f"Program for {day}")
        df = pd.DataFrame(daily_schedule[day], columns=["Time", "Activity"])
        #st.table(df)
        st.write(df)