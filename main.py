from __future__ import annotations

import asyncio
import io
import itertools
import os
import sys
from pathlib import Path
from typing import Annotated, List, Optional, Tuple

import aiohttp
import folium  # type: ignore
import networkx  # type: ignore
import osmnx  # type: ignore
from bs4 import BeautifulSoup  # type: ignore
from fastapi import FastAPI, Query
from geopandas import GeoDataFrame  # type: ignore
from osmnx import geocoder
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from folium.elements import EventHandler, JsCode  # type: ignore


root = Path(__file__).parent.resolve()
data = root / "data"
scripts = root / "scripts"
build = root / "build"
data.mkdir(parents=True, exist_ok=True)


resource_lock = asyncio.Lock()
app = FastAPI(title="Path finder")
app.mount("/data", StaticFiles(directory=data))


root_html = root.joinpath("index.html").read_text(encoding="utf-8")
route_script = scripts.joinpath("route.js").read_text(encoding="utf-8")


@app.get("/")
async def route_root() -> HTMLResponse:
    return HTMLResponse(root_html)


@app.get("/route")
async def route_route(
    *,
    place: Annotated[str, Query()],
    begin_lat: Annotated[Optional[float], Query()] = None,
    begin_lng: Annotated[Optional[float], Query()] = None,
    end_lat: Annotated[Optional[float], Query()] = None,
    end_lng: Annotated[Optional[float], Query()] = None,
) -> HTMLResponse:
    def _initial_load() -> Tuple[GeoDataFrame, networkx.MultiDiGraph]:
        gdf = geocoder.geocode_to_gdf(place)

        # Load graph from local file if possible
        osm_id = gdf["osm_id"][0]
        graph_path = data / f"{osm_id}.graphml"
        try:
            graph = osmnx.load_graphml(graph_path)
        except FileNotFoundError:
            graph = osmnx.graph_from_place(place, network_type="drive")
            osmnx.save_graphml(graph, graph_path)

        return gdf, graph

    async def pre_download(url: str, *, session: aiohttp.ClientSession) -> Path:
        target = data.joinpath(os.path.basename(url))
        async with resource_lock:
            if not target.is_file():
                async with session.get(url) as response:
                    response.raise_for_status()
                    with target.open("wb") as file:
                        file.write(await response.read())

        return target

    gdf, graph = await asyncio.to_thread(_initial_load)
    coordinates = [
        [gdf.bbox_south[0], gdf.bbox_west[0]],
        [gdf.bbox_north[0], gdf.bbox_east[0]],
    ]
    map = folium.Map(
        location=[gdf.lat[0], gdf.lon[0]],
        zoom_control=False,
        scrollWheelZoom=False,
        dragging=False,
    )
    map.fit_bounds(coordinates)
    map.add_child(folium.GeoJson(gdf.unary_union))
    map.add_child(folium.LatLngPopup())
    map.add_child(EventHandler("click", JsCode(route_script)))

    begin = osmnx.nearest_nodes(graph, begin_lng, begin_lat) if begin_lat is not None and begin_lng is not None else None
    end = osmnx.nearest_nodes(graph, end_lng, end_lat) if end_lat is not None and end_lng is not None else None
    if begin is not None and end is not None:
        if begin_lat is not None and begin_lng is not None:
            map.add_child(
                folium.Marker(
                    location=(begin_lat, begin_lng),
                    tooltip="Source",
                )
            )

        if end_lat is not None and end_lng is not None:
            map.add_child(
                folium.Marker(
                    location=(end_lat, end_lng),
                    tooltip="Destination",
                )
            )

        # Folium route colors
        colors = itertools.cycle(
            [
                "red",
                "blue",
                "gray",
                "darkred",
                "lightred",
                "orange",
                "beige",
                "green",
                "darkgreen",
                "lightgreen",
                "darkblue",
                "lightblue",
                "purple",
                "darkpurple",
                "pink",
                "cadetblue",
                "lightgray",
                "black",
            ],
        )

        # Construct stdin
        stdin = io.BytesIO()
        stdin.write(f"{graph.number_of_nodes()} {graph.number_of_edges()} {begin} {end}\n".encode("utf-8"))
        for id, node in graph.nodes(data=True):
            lng = node["x"]
            lat = node["y"]
            stdin.write(f"{id} {lng} {lat}\n".encode("utf-8"))

        for u, v, *_ in graph.edges(data=False):
            stdin.write(f"{u} {v}\n".encode("utf-8"))

        # Apply all algorithms
        tasks: List[asyncio.Task[Tuple[bytes, bytes]]] = []
        for executable in build.iterdir():
            process = await asyncio.create_subprocess_exec(
                str(executable.resolve()),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=sys.stderr,
            )

            stdin.seek(0)
            tasks.append(asyncio.create_task(process.communicate(stdin.read())))

        for task in tasks:
            stdout, _ = await task
            route = [int(x) for x in stdout.decode("utf-8").split()]

            map.add_child(
                folium.PolyLine(
                    locations=[(graph.nodes[i]["y"], graph.nodes[i]["x"]) for i in route],
                    tooltip=executable.stem,
                    color=next(colors),
                    weight=4,
                ),
            )

    soup = BeautifulSoup(map.get_root().render(), "html.parser")
    async with aiohttp.ClientSession() as session:
        for element in soup.find_all("script"):
            if url := element.get("src"):
                p = await pre_download(url, session=session)
                element["src"] = p.relative_to(root).as_posix()

        for element in soup.find_all("link"):
            if url := element.get("href"):
                p = await pre_download(url, session=session)
                element["href"] = p.relative_to(root).as_posix()

    return HTMLResponse(soup)
