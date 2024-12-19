from flask import Flask, render_template, request
import osmnx as ox
import folium
from shapely.geometry import Polygon, MultiPolygon

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        city = request.form['city']
        country = request.form['country']

        location = f"{city}, {country}"

        # Get the city boundary
        city_boundary = ox.geocode_to_gdf(location)

        # Generate green areas
        green_areas = ox.features_from_place(
            location,
            tags={
                "leisure": ["park", "garden", "nature_reserve", "common"],
                "landuse": ["forest", "grass", "meadow", "recreation_ground", "village_green"],
                "natural": ["wood", "scrub", "heath", "grassland"],
                "boundary": "protected_area",
            }
        )

        # Filter out Point geometries from green areas
        green_areas = green_areas[~green_areas.geometry.type.isin(["Point", "MultiPoint"])]

        # Calculate total area for all green areas
        total_area = 0
        for area in green_areas.geometry:
            if isinstance(area, Polygon):
                total_area += area.area
            elif isinstance(area, MultiPolygon):
                total_area += sum(polygon.area for polygon in area.geoms)

        # Convert area from square meters to hectares
        total_area_ha = total_area / 10000

        # Create a Folium map
        m = folium.Map(location=city_boundary.geometry[0].centroid.coords[0][::-1], zoom_start=12)

        # Add the city boundary and green areas to the map
        folium.GeoJson(
            city_boundary.__geo_interface__,
            name="City Boundary",
            style_function=lambda feature: {
                "fillColor": "rgba(255, 0, 0, 0.1)",
                "color": "red",
                "weight": 3,
                "fillOpacity": 0.3
            }
        ).add_to(m)

        folium.GeoJson(
            green_areas.__geo_interface__,
            name="Green Areas",
            style_function=lambda feature: {
                "fillColor": "green",
                "color": "green",
                "weight": 1,
                "fillOpacity": 0.5
            }
        ).add_to(m)

        # Add layer control to toggle boundaries and green areas
        folium.LayerControl().add_to(m)

        # Save the map to a static file
        map_path = 'static/map.html'
        m.save(map_path)

        return render_template('index.html', total_area=total_area_ha, map_path=map_path)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)