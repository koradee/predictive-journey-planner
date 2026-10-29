import hashlib
import json
from pathlib import Path
import re
from typing import Dict, Optional, Tuple

import networkx as nx

from routing.engine import (
    ROOT,
    BBOX,
    load_graph as engine_load_graph,
    route as engine_route,
    RoutingError,
)

# Supported landmark coordinates in Pune pilot [longitude, latitude]
SUPPORTED_LOCATIONS: Dict[str, Tuple[float, float]] = {
    "shivajinagar": (73.8446, 18.5314),
    "shivajinagar pune": (73.8446, 18.5314),
    "shivaji nagar": (73.8446, 18.5314),
    "shivajinagar station": (73.8446, 18.5314),
    "pune railway station": (73.8743, 18.5285),
    "pune station": (73.8743, 18.5285),
    "pune junction": (73.8743, 18.5285),
    "shaniwar wada": (73.8553, 18.5195),
    "shaniwarwada": (73.8553, 18.5195),
    "pune municipal corporation": (73.8530, 18.5222),
    "pmc": (73.8530, 18.5222),
    "coep": (73.8566, 18.5298),
    "college of engineering pune": (73.8566, 18.5298),
    "fergusson college": (73.8415, 18.5236),
}


class RoutingService:
    def __init__(self, root_dir: Optional[Path] = None):
        self._custom_root = root_dir is not None
        self.root_dir = root_dir or ROOT
        self._graph: Optional[nx.MultiDiGraph] = None

    @property
    def raw_data_path(self) -> Path:
        if self._custom_root:
            return self.root_dir / "data/raw/pune-osm/roads.json"
        candidates = [
            self.root_dir / "data/raw/pune-osm/roads.json",
            Path.cwd() / "data/raw/pune-osm/roads.json",
            Path(__file__).resolve().parents[1] / "data/raw/pune-osm/roads.json",
            Path(__file__).resolve().parents[2] / "data/raw/pune-osm/roads.json",
        ]
        for p in candidates:
            if p.is_file():
                return p
        return candidates[0]

    @property
    def manifest_path(self) -> Path:
        if self._custom_root:
            return self.root_dir / "data/pune-osm-manifest.json"
        candidates = [
            self.root_dir / "data/pune-osm-manifest.json",
            Path.cwd() / "data/pune-osm-manifest.json",
            Path(__file__).resolve().parents[1] / "data/pune-osm-manifest.json",
            Path(__file__).resolve().parents[2] / "data/pune-osm-manifest.json",
        ]
        for p in candidates:
            if p.is_file():
                return p
        return candidates[0]

    def check_readiness(self) -> Dict:
        """Verifies OSM data and manifest integrity without crashing."""
        if not self.raw_data_path.is_file() or not self.manifest_path.is_file():
            return {
                "routing_ready": False,
                "error": "OSM raw data or manifest file not found.",
            }
        try:
            raw = self.raw_data_path.read_bytes()
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            file_sha = hashlib.sha256(raw).hexdigest()
            if file_sha != manifest.get("sha256") or len(raw) != manifest.get("bytes"):
                return {
                    "routing_ready": False,
                    "error": f"OSM source checksum/size mismatch (expected {manifest.get('sha256')}, got {file_sha}).",
                }
            graph = self.get_graph()
            return {
                "routing_ready": True,
                "nodes": graph.number_of_nodes(),
                "directed_edges": graph.number_of_edges(),
                "bbox": list(manifest.get("bbox_south_west_north_east", BBOX)),
                "sha256": file_sha,
            }
        except Exception as exc:
            return {
                "routing_ready": False,
                "error": f"Error validating routing graph: {str(exc)}",
            }

    def get_graph(self) -> nx.MultiDiGraph:
        """Lazily load and cache the routing graph."""
        if self._graph is None:
            self._graph = engine_load_graph(self.raw_data_path, self.manifest_path)
        return self._graph

    def resolve_location(
        self,
        loc_str: str,
        custom_coords: Optional[Tuple[float, float]] = None,
    ) -> Tuple[float, float]:
        """
        Resolves a location string or coordinates into a (longitude, latitude) tuple.
        Raises RoutingError if the location cannot be resolved.
        """
        if custom_coords is not None:
            lon, lat = custom_coords
            return float(lon), float(lat)

        # Check for coordinate string e.g. "18.5314, 73.8446" or "73.8446, 18.5314"
        coord_match = re.match(
            r"^\s*([-+]?\d+(?:\.\d+)?)\s*,\s*([-+]?\d+(?:\.\d+)?)\s*$",
            loc_str.strip(),
        )
        if coord_match:
            val1 = float(coord_match.group(1))
            val2 = float(coord_match.group(2))
            # Lat, Lon order
            if 18.0 <= val1 <= 19.0 and 73.0 <= val2 <= 74.5:
                return (val2, val1)  # return (lon, lat)
            # Lon, Lat order
            if 73.0 <= val1 <= 74.5 and 18.0 <= val2 <= 19.0:
                return (val1, val2)
            return (val1, val2)

        normalized = loc_str.strip().lower().replace(",", " ")
        normalized = re.sub(r"\s+", " ", normalized)

        if normalized in SUPPORTED_LOCATIONS:
            return SUPPORTED_LOCATIONS[normalized]

        for key, coords in SUPPORTED_LOCATIONS.items():
            if key in normalized or normalized in key:
                return coords

        raise RoutingError(
            "unsupported_location",
            f"Location '{loc_str}' is unsupported or outside the bounded Pune pilot area. Supported landmarks include: Shivajinagar, Pune; Pune Railway Station (or pass coordinates within bounding box [18.510, 73.825, 18.550, 73.895]).",
        )

    def calculate_routes(
        self,
        source: str,
        destination: str,
        travel_date: Optional[str] = None,
        departure_time: Optional[str] = None,
        source_coords: Optional[Tuple[float, float]] = None,
        destination_coords: Optional[Tuple[float, float]] = None,
        alternatives: int = 3,
        objective: str = "distance",
    ) -> Dict:
        """
        Calculates routes using routing.engine.
        Returns serialized response dict matching RouteResponse schema.
        """
        src_pt = self.resolve_location(source, source_coords)
        dst_pt = self.resolve_location(destination, destination_coords)

        graph = self.get_graph()
        raw_result = engine_route(
            graph,
            src_pt,
            dst_pt,
            objective=objective,
            alternatives=alternatives,
        )

        routes = []
        for i, r in enumerate(raw_result["routes"]):
            # Leaflet expects [latitude, longitude]
            leaflet_coords = [[lat, lon] for lon, lat in r["geometry"]["coordinates"]]
            name = (
                f"Route {i + 1} ({'Shortest' if i == 0 else 'Alternative'} · "
                f"{r['distance_km']:.2f} km)"
            )
            route_item = dict(
                route_id=r["route_id"],
                name=name,
                geometry=r["geometry"],
                coordinates=leaflet_coords,
                distance_km=round(r["distance_km"], 3),
                estimated_duration_seconds=r.get("estimated_duration_seconds"),
                routing_objective=r["routing_objective"],
                warnings=r["warnings"],
                osm_way_ids=r["osm_way_ids"],
                node_ids=r["node_ids"],
                distinctness=r["distinctness"],
            )
            routes.append(route_item)

        return dict(
            schema_version=raw_result["schema_version"],
            crs=raw_result["crs"],
            coordinate_order=raw_result["coordinate_order"],
            attribution=raw_result["attribution"],
            source=source,
            destination=destination,
            travel_date=travel_date,
            departure_time=departure_time,
            source_snap=raw_result["source_snap"],
            destination_snap=raw_result["destination_snap"],
            alternatives_policy=raw_result["alternatives_policy"],
            routes=routes,
        )


routing_service = RoutingService()

