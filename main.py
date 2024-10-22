# type: ignore
# Data science libraries has no idea what convention is anyway

import io
import os
import subprocess
import tempfile
import warnings
import webbrowser
from os.path import join
from pathlib import Path

import folium
import osmnx
from osmnx import geocoder


place = input("Enter search location: ")
print("Loading map data...")


graph = osmnx.graph_from_place(place)
gdf = geocoder.geocode_to_gdf(place)


coordinates = [
    [gdf.bbox_south[0], gdf.bbox_west[0]],
    [gdf.bbox_north[0], gdf.bbox_east[0]],
]
print("SW-NE:", coordinates)
print("Number of nodes:", graph.number_of_nodes())
print("Number of edges:", graph.number_of_edges())


selection_map = folium.Map(location=[gdf.lat[0], gdf.lon[0]])
selection_map.fit_bounds(coordinates)
selection_map.add_child(folium.GeoJson(gdf.unary_union))
selection_map.add_child(folium.LatLngPopup())


map_path = join(tempfile.gettempdir(), f"map-{os.getpid()}.html")
selection_map.save(map_path)
webbrowser.open(f"file://{map_path}")


print("Copy and paste coordinates of the source and destination points:")


source_lon = float(input("Source longitude: "))
source_lat = float(input("Source latitude: "))
source_index = osmnx.nearest_nodes(graph, source_lon, source_lat)
print("Got source", graph.nodes[source_index])


destination_lon = float(input("Destination longitude: "))
destination_lat = float(input("Destination latitude: "))
destination_index = osmnx.nearest_nodes(graph, destination_lon, destination_lat)
print("Got destination", graph.nodes[destination_index])


if source_index == destination_index:
    warnings.warn("Source and destination are the same!")


stdin = io.StringIO()
stdin.write(f"{graph.number_of_nodes()} {graph.number_of_edges()} {source_index} {destination_index}\n")

for index, node in graph.nodes(data=True):
    stdin.write(f"{index} {node['y']} {node['x']}\n")

for u, v, *_ in graph.edges(data=True):
    stdin.write(f"{u} {v}\n")


root = Path(__file__).parent
executable = root.joinpath("build", "main.exe").resolve()
print(f"Starting subprocess \"{executable}\"")

process = subprocess.Popen(
    [executable],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)
stdin.seek(0)
stdout, stderr = process.communicate(stdin.read())
print(f"Subprocess completed with return code {process.returncode}")
stdout = stdout.strip()
stderr = stderr.strip()


if len(stderr) > 0:
    print("Extra info from subprocess:")
    print(stderr)


route = list(map(int, stdout.split()))
coordinates = []
for index in route:
    node = graph.nodes[index]
    coordinates.append((node["y"], node["x"]))


selection_map.add_child(folium.PolyLine(locations=coordinates, color="#FF0000", weight=5))
route_path = join(tempfile.gettempdir(), f"route-{os.getpid()}.html")
selection_map.save(route_path)
webbrowser.open(f"file://{route_path}")
