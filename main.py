from __future__ import annotations

import asyncio
import io
import itertools
import os
import sys
import traceback
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
from fastapi.exceptions import HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from folium.elements import EventHandler, JsCode  # type: ignore
from folium.features import CustomIcon


root = Path(__file__).parent.resolve()
build = root / "build"
data = root / "data"
scripts = root / "scripts"
static = root / "static"
data.mkdir(parents=True, exist_ok=True)


app = FastAPI(title="Path finder")
app.mount("/data", StaticFiles(directory=data))
app.mount("/static", StaticFiles(directory=static))

root_html = root.joinpath("index.html").read_text(encoding="utf-8")
route_script = scripts.joinpath("route.js").read_text(encoding="utf-8")

graph_lock = asyncio.Lock()
predownload_lock = asyncio.Lock()


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
    timeout: Annotated[float, Query()] = 30,
) -> HTMLResponse:
    def _initial_load() -> Tuple[GeoDataFrame, networkx.MultiDiGraph]:
        try:
            gdf = geocoder.geocode_to_gdf(place)
        except Exception:
            raise HTTPException(status_code=404)

        # Load graph from local file if possible
        osm_id = gdf["osm_id"][0]
        graph_path = data / f"{osm_id}.graphml"
        try:
            graph = osmnx.load_graphml(graph_path)
        except FileNotFoundError:
            try:
                graph = osmnx.graph_from_place(place, network_type="drive")
                osmnx.save_graphml(graph, graph_path)
            except ValueError:
                traceback.print_exc()
                raise HTTPException(status_code=404)

        return gdf, graph

    async with graph_lock:
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
        line_weight = 2

        walk_color = next(colors)
        if begin_lat is not None and begin_lng is not None:
            map.add_child(
                folium.Marker(
                    location=(begin_lat, begin_lng),
                    tooltip="Source",
                    icon=CustomIcon(static.joinpath("marker-icon.png").as_posix()),
                )
            )
            map.add_child(
                folium.PolyLine(
                    locations=[(begin_lat, begin_lng), (graph.nodes[begin]["y"], graph.nodes[begin]["x"])],
                    dash_array="10",
                    weight=line_weight,
                    color=walk_color,
                )
            )

        if end_lat is not None and end_lng is not None:
            map.add_child(
                folium.Marker(
                    location=(end_lat, end_lng),
                    tooltip="Destination",
                    icon=CustomIcon(static.joinpath("marker-icon.png").as_posix()),
                )
            )
            map.add_child(
                folium.PolyLine(
                    locations=[(graph.nodes[end]["y"], graph.nodes[end]["x"]), (end_lat, end_lng)],
                    dash_array="10",
                    weight=line_weight,
                    color=walk_color,
                )
            )

        # Construct stdin
        stdin = io.BytesIO()
        stdin.write(f"{graph.number_of_nodes()} {graph.number_of_edges()} {begin} {end} {timeout}\n".encode("utf-8"))
        for id, node in graph.nodes(data=True):
            lng = node["x"]
            lat = node["y"]
            stdin.write(f"{id} {lng} {lat}\n".encode("utf-8"))

        for u, v, *_ in graph.edges(data=False):
            stdin.write(f"{u} {v}\n".encode("utf-8"))

        # Apply all algorithms
        tasks: List[Tuple[str, asyncio.subprocess.Process, asyncio.Task[Tuple[bytes, bytes]]]] = []
        for executable in build.iterdir():
            process = await asyncio.create_subprocess_exec(
                str(executable.resolve()),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=sys.stderr,
            )

            stdin.seek(0)
            tasks.append((executable.stem, process, asyncio.create_task(process.communicate(stdin.read()))))

        for tooltip, process, task in tasks:
            stdout, _ = await task

            if process.returncode == 0:
                route = [int(x) for x in stdout.decode("utf-8").split()]
                map.add_child(
                    folium.PolyLine(
                        locations=[(graph.nodes[i]["y"], graph.nodes[i]["x"]) for i in route],
                        tooltip=tooltip,
                        color=next(colors),
                        weight=line_weight,
                    ),
                )

    async def predownload(url: str, *, session: aiohttp.ClientSession) -> Path:
        target = data.joinpath(os.path.basename(url))
        async with predownload_lock:
            if not target.is_file():
                async with session.get(url) as response:
                    response.raise_for_status()
                    with target.open("wb") as file:
                        file.write(await response.read())

        return target

    soup = BeautifulSoup(map.get_root().render(), "html.parser")
    async with aiohttp.ClientSession() as session:
        for element in soup.find_all("script"):
            if url := element.get("src"):
                p = await predownload(url, session=session)
                element["src"] = p.relative_to(root).as_posix()

        for element in soup.find_all("link"):
            if url := element.get("href"):
                p = await predownload(url, session=session)
                element["href"] = p.relative_to(root).as_posix()

    head = soup.find("head")
    if head is not None:
        title = soup.new_tag("title")
        title.append("Routing")
        head.append(title)
        head.append(soup.new_tag("link", attrs={"rel": "icon", "type": "image/x-icon", "href": "/static/favicon.png"}))

    return HTMLResponse(soup)
