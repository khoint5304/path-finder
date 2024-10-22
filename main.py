# type: ignore
# Data science libraries has no idea what convention is anyway

import sys
import tempfile
import webbrowser
from os.path import join

import folium
import osmnx
from osmnx import geocoder


def stderr_input(prompt: str) -> str:
    print(prompt, end="", file=sys.stderr)
    return input()


place = stderr_input("Enter search location: ")
graph = osmnx.graph_from_place(place)
gdf = geocoder.geocode_to_gdf(place)


coordinates = [
    [gdf.bbox_south[0], gdf.bbox_west[0]],
    [gdf.bbox_north[0], gdf.bbox_east[0]],
]
print("SW-NE:", coordinates, file=sys.stderr)
print("Number of nodes:", graph.number_of_nodes(), file=sys.stderr)
print("Number of edges:", graph.number_of_edges(), file=sys.stderr)


map = folium.Map(location=[gdf.lat[0], gdf.lon[0]])
map.fit_bounds(coordinates)
map.add_child(folium.GeoJson(gdf.unary_union))
map.add_child(folium.LatLngPopup())


map_path = join(tempfile.gettempdir(), "map.html")
map.save(map_path)
webbrowser.open(f"file://{map_path}")


print("Copy and paste coordinates of the source and destination points:", file=sys.stderr)
source_lat = float(stderr_input("Source latitude: "))
source_lon = float(stderr_input("Source longitude: "))
destination_lat = float(stderr_input("Destination latitude: "))
destination_lon = float(stderr_input("Destination longitude: "))


source_index = osmnx.nearest_nodes(graph, source_lon, source_lat)
destination_index = osmnx.nearest_nodes(graph, destination_lon, destination_lat)


print(graph.number_of_nodes(), graph.number_of_edges(), source_index, destination_index)

for index, node in graph.nodes(data=True):
    print(index, node["x"], node["y"])

for u, v, *_ in graph.edges(data=True):
    print(u, v)
