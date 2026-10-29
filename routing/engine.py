"""Bounded OSM motorcar routing, without traffic prediction or a web service."""
from collections import Counter
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
BBOX = (18.510, 73.825, 18.550, 73.895)  # south, west, north, east
SOURCE = (73.8446, 18.5314)  # longitude, latitude, approximate demo location
DESTINATION = (73.8743, 18.5285)
ROAD_TYPES = set("motorway trunk primary secondary tertiary unclassified residential living_street motorway_link trunk_link primary_link secondary_link tertiary_link".split())
ACCESS_KEYS = ("motorcar", "motor_vehicle", "vehicle", "access")
ALLOWED_ACCESS = {"yes", "permissive", "designated"}
WARNINGS = [
    "OSM map routing pilot, not field-verified navigation or traffic prediction.",
    "Boundary clipping can omit useful roads and routes outside the pilot.",
    "Snaps are straight-line proximity diagnostics, not verified driveway or pedestrian connectors.",
    "Restriction via nodes/ways and tagged barrier nodes are conservatively excluded; this is not full turn-aware routing.",
    "Untagged access and missing restrictions remain unknown; current closures are not available.",
]


class RoutingError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def coordinates(value):
    if not isinstance(value, (tuple, list)) or len(value) != 2:
        raise RoutingError("invalid_coordinates", "Expected [longitude, latitude]")
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in value):
        raise RoutingError("invalid_coordinates", "Coordinates must be finite numbers")
    lon, lat = value
    if not (-180 <= lon <= 180 and -90 <= lat <= 90):
        raise RoutingError("invalid_coordinates", "Coordinates outside geographic bounds")
    return float(lon), float(lat)


def inside(point, bbox):
    lon, lat = point
    south, west, north, east = bbox
    return west <= lon <= east and south <= lat <= north


def distance_m(a, b):
    """Spherical great-circle distance along each consecutive original OSM segment."""
    lon1, lat1, lon2, lat2 = map(math.radians, (*a, *b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 6371008.8 * 2 * math.asin(min(1., math.sqrt(h)))


def speed_kph(value):
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)(?:\s*(km/h|kph|mph))?", str(value).strip())
    if not match:
        return None
    speed = float(match[1]) * (1.609344 if match[2] == "mph" else 1)
    return speed if math.isfinite(speed) and speed > 0 else None


def access_allowed(tags, direction=None):
    for key in ACCESS_KEYS:
        name = f"{key}:{direction}" if direction else key
        if name in tags:
            return tags[name] in ALLOWED_ACCESS
    return True if direction is None else access_allowed(tags)


def build_graph(payload, provenance, bbox=BBOX):
    if payload.get("remark") or not isinstance(payload.get("elements"), list):
        raise RoutingError("invalid_graph", "Incomplete or malformed OSM response")
    elements = payload["elements"]
    nodes = {e["id"]: e for e in elements if e["type"] == "node"}
    ways = sorted((e for e in elements if e["type"] == "way"), key=lambda e: e["id"])
    blocked_nodes = {n for n, e in nodes.items() if e.get("tags", {}).get("barrier") not in (None, "no") or not access_allowed(e.get("tags", {}))}
    blocked_ways = set()
    restrictions = [e for e in elements if e["type"] == "relation" and e.get("tags", {}).get("type") == "restriction"]
    for relation in restrictions:
        via = [m for m in relation.get("members", []) if m["role"] == "via"]
        for member in via:
            (blocked_nodes if member["type"] == "node" else blocked_ways).add(member["ref"])
        if not via:  # Uninterpretable restriction: conservatively remove its referenced ways.
            blocked_ways.update(m["ref"] for m in relation.get("members", []) if m["type"] == "way")
    graph = nx.MultiDiGraph(crs="EPSG:4326", bbox=list(bbox), provenance=provenance)
    excluded = Counter()
    for way in ways:
        tags = way.get("tags", {})
        if tags.get("highway") not in ROAD_TYPES or tags.get("area") == "yes":
            excluded["road_class_or_area"] += 1
            continue
        if way["id"] in blocked_ways or not access_allowed(tags):
            excluded["access_or_restriction"] += 1
            continue
        if any(":conditional" in key and key.split(":")[0] in (*ACCESS_KEYS, "oneway") for key in tags):
            excluded["conditional_access_or_oneway"] += 1
            continue
        one = tags.get("oneway:motorcar", tags.get("oneway:motor_vehicle", tags.get("oneway", "yes" if tags.get("junction") == "roundabout" or tags.get("highway") == "motorway" else "no")))
        if one not in {"yes", "1", "true", "-1", "no", "0", "false"}:
            excluded["unsupported_oneway"] += 1
            continue
        for index, (a, b) in enumerate(itertools.pairwise(way.get("nodes", []))):
            if a not in nodes or b not in nodes:
                raise RoutingError("invalid_graph", "OSM way has missing node geometry")
            if a in blocked_nodes or b in blocked_nodes:
                excluded["blocked_node_segments"] += 1
                continue
            pa = coordinates([nodes[a]["lon"], nodes[a]["lat"]])
            pb = coordinates([nodes[b]["lon"], nodes[b]["lat"]])
            if not inside(pa, bbox) or not inside(pb, bbox):
                excluded["boundary_segments"] += 1
                continue
            length = distance_m(pa, pb)
            if a == b or length <= 0:
                excluded["zero_length_segments"] += 1
                continue
            directions = []
            if one != "-1":
                directions.append((a, b, "forward"))
            if one not in {"yes", "1", "true"}:
                directions.append((b, a, "backward"))
            for u, v, direction in directions:
                if not access_allowed(tags, direction):
                    continue
                speed = None if any(k.startswith("maxspeed") and "conditional" in k for k in tags) else speed_kph(tags.get("maxspeed:" + direction, tags.get("maxspeed")))
                for node, point in [(a, pa), (b, pb)]:
                    graph.add_node(node, x=point[0], y=point[1])
                graph.add_edge(u, v, key=f"{way['id']}:{index}", osm_way_id=way["id"], segment_index=index,
                               highway=tags["highway"], length_m=length, speed_kph=speed,
                               estimated_seconds=length * 3.6 / speed if speed else None)
    graph.graph["import_statistics"] = dict(raw_nodes=len(nodes), raw_ways=len(ways), restriction_relations=len(restrictions), conservatively_blocked_nodes=len(blocked_nodes), conservatively_blocked_ways=len(blocked_ways), exclusions=dict(excluded))
    validate_graph(graph)
    return graph


def validate_graph(graph):
    if not isinstance(graph, nx.MultiDiGraph) or not graph.number_of_edges():
        raise RoutingError("invalid_graph", "A nonempty directed road multigraph is required")
    for _, node in graph.nodes(data=True):
        if not inside(coordinates([node.get("x"), node.get("y")]), graph.graph.get("bbox", BBOX)):
            raise RoutingError("invalid_graph", "Node outside pilot boundary")
    for u, v, _, edge in graph.edges(keys=True, data=True):
        length = edge.get("length_m")
        if not isinstance(length, (int, float)) or not math.isfinite(length) or length <= 0:
            raise RoutingError("invalid_graph", "Invalid road length")
        expected = distance_m((graph.nodes[u]["x"], graph.nodes[u]["y"]), (graph.nodes[v]["x"], graph.nodes[v]["y"]))
        if not math.isclose(length, expected, rel_tol=1e-9, abs_tol=1e-6):
            raise RoutingError("invalid_graph", "Road length disagrees with original segment geometry")
        seconds, speed = edge.get("estimated_seconds"), edge.get("speed_kph")
        if seconds is not None and (not isinstance(speed, (int, float)) or not math.isfinite(speed) or speed <= 0 or not math.isclose(seconds, length * 3.6 / speed)):
            raise RoutingError("invalid_graph", "Invalid speed-derived time")


def load_graph(path=None, manifest_path=None):
    path = Path(path or ROOT / "data/raw/pune-osm/roads.json")
    manifest_path = Path(manifest_path or ROOT / "data/pune-osm-manifest.json")
    if not path.is_file() or not manifest_path.is_file():
        raise RoutingError("missing_graph", "Acquire the pinned Pune OSM snapshot and manifest first")
    raw = path.read_bytes()
    manifest = json.loads(manifest_path.read_text())
    if hashlib.sha256(raw).hexdigest() != manifest["sha256"] or len(raw) != manifest["bytes"]:
        raise RoutingError("invalid_graph", "OSM source hash/size mismatch")
    return build_graph(json.loads(raw), manifest, tuple(manifest["bbox_south_west_north_east"]))


def statistics(graph):
    weak = sorted((len(c) for c in nx.weakly_connected_components(graph)), reverse=True)
    strong = sorted((len(c) for c in nx.strongly_connected_components(graph)), reverse=True)
    return dict(nodes=graph.number_of_nodes(), directed_edges=graph.number_of_edges(), weak_components=len(weak), largest_weak_component=weak[0], strong_components=len(strong), largest_strong_component=strong[0], edges_with_numeric_speed=sum(e["speed_kph"] is not None for _, _, e in graph.edges(data=True)), **graph.graph["import_statistics"])


def snap(graph, point, role, max_distance=250):
    point = coordinates(point)
    if not inside(point, graph.graph["bbox"]):
        raise RoutingError("outside_pilot", "Coordinate is outside the bounded Pune pilot")
    degree = graph.out_degree if role == "source" else graph.in_degree
    candidates = [(distance_m(point, (d["x"], d["y"])), n) for n, d in graph.nodes(data=True) if degree(n) > 0]
    if not candidates:
        raise RoutingError("no_snap", "No suitable directed road nodes")
    distance, node = min(candidates)
    if distance > max_distance:
        raise RoutingError("no_snap", "Nearest suitable road node exceeds 250 metres")
    return dict(input_coordinates=list(point), node_id=node, snapped_coordinates=[graph.nodes[node]["x"], graph.nodes[node]["y"]], distance_m=distance)


def cost_graph(graph, objective):
    if objective not in {"distance", "estimated_time"}:
        raise RoutingError("unsupported_objective", "Use distance or estimated_time")
    weight = "length_m" if objective == "distance" else "estimated_seconds"
    result = nx.DiGraph()
    result.add_nodes_from(sorted(graph.nodes))
    for u, v, key, edge in sorted(graph.edges(keys=True, data=True), key=lambda item: item[:3]):
        if edge[weight] is None:
            continue
        rank = (edge[weight], edge["osm_way_id"], edge["segment_index"])
        if not result.has_edge(u, v) or rank < result[u][v]["rank"]:
            result.add_edge(u, v, **edge, key=key, rank=rank, weight=edge[weight])
    return result


def route(graph, source, destination, objective="distance", alternatives=3):
    validate_graph(graph)
    if isinstance(alternatives, bool) or not isinstance(alternatives, int) or not 1 <= alternatives <= 3:
        raise RoutingError("invalid_alternatives", "Request one to three alternatives")
    source, destination = coordinates(source), coordinates(destination)
    s, d = snap(graph, source, "source"), snap(graph, destination, "destination")
    if source == destination or s["node_id"] == d["node_id"]:
        raise RoutingError("same_location", "Endpoints coincide or snap to the same road node; no nonzero route")
    costs = cost_graph(graph, objective)
    if not nx.has_path(costs, s["node_id"], d["node_id"]):
        code = "unsupported_time" if objective == "estimated_time" else "disconnected"
        raise RoutingError(code, "No directed path between nearest snaps under the requested cost; snaps are not moved to invent connectivity")
    paths = nx.shortest_simple_paths(costs, s["node_id"], d["node_id"], weight="weight")
    selected, scanned, best_cost = [], 0, None
    for path in itertools.islice(paths, 40):
        scanned += 1
        edges = [costs[u][v] for u, v in itertools.pairwise(path)]
        cost = sum(e["weight"] for e in edges)
        if best_cost is None:
            best_cost = cost
        if cost > best_cost * 1.5:
            break
        length = sum(e["length_m"] for e in edges)
        # Undirected physical OSM segment identity prevents reversed common roads inflating distinctness.
        segments = {(e["osm_way_id"], e["segment_index"]): e["length_m"] for e in edges}
        overlaps = [sum(length_m for seg, length_m in segments.items() if seg in old["segments"]) / min(length, old["length"]) for old in selected]
        if any(overlap > .8 for overlap in overlaps):
            continue
        seconds = sum(e["estimated_seconds"] for e in edges) if all(e["estimated_seconds"] is not None for e in edges) else None
        identity = json.dumps([graph.graph["provenance"]["sha256"], objective, path, [e["key"] for e in edges]], separators=(",", ":"))
        warnings = list(WARNINGS)
        warnings.append("Posted-limit estimate excludes signals, junction delays, congestion and stopping; not an AI prediction." if seconds is not None else "Duration unavailable: at least one segment lacks an unconditional numeric speed limit; no defaults supplied.")
        item = dict(route_id="pune-" + hashlib.sha256(identity.encode()).hexdigest()[:16], geometry={"type": "LineString", "coordinates": [[graph.nodes[n]["x"], graph.nodes[n]["y"]] for n in path]}, distance_km=length / 1000, estimated_duration_seconds=seconds, routing_objective=objective, warnings=warnings, osm_way_ids=list(dict.fromkeys(e["osm_way_id"] for e in edges)), node_ids=path, distinctness={"maximum_shared_length_fraction": max(overlaps, default=0), "maximum_allowed": .8, "cost_ratio_to_best": cost / best_cost})
        selected.append(dict(result=item, segments=segments, length=length))
        if len(selected) == alternatives:
            break
    return dict(schema_version="pune-routing-v1", crs="EPSG:4326", coordinate_order="longitude,latitude", attribution="OpenStreetMap contributors", provenance=graph.graph["provenance"], source_snap=s, destination_snap=d, alternatives_policy=dict(requested=alternatives, returned=len(selected), candidates_examined=scanned, candidate_limit=40, max_cost_ratio=1.5, overlap_definition="shared physical segment length / shorter route length", ranking="nondecreasing objective cost; ties use sorted graph insertion and pinned NetworkX", exhaustive=False), routes=[r["result"] for r in selected])
