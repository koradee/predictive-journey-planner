from typing import List, Optional, Tuple, Literal
from pydantic import BaseModel, Field, field_validator


class RouteRequest(BaseModel):
    source: str = Field(..., min_length=1, description="Starting location name or coordinates")
    destination: str = Field(..., min_length=1, description="Destination location name or coordinates")
    travel_date: Optional[str] = Field(default=None, alias="travelDate", description="Date in YYYY-MM-DD")
    departure_time: Optional[str] = Field(default=None, alias="departureTime", description="Time in HH:MM")
    source_coordinates: Optional[Tuple[float, float]] = Field(default=None, description="[longitude, latitude]")
    destination_coordinates: Optional[Tuple[float, float]] = Field(default=None, description="[longitude, latitude]")
    alternatives: int = Field(default=3, ge=1, le=3, description="Number of alternative routes to calculate (1-3)")
    objective: Literal["distance", "estimated_time"] = Field(default="distance", description="Routing objective")

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "source": "Shivajinagar, Pune",
                "destination": "Pune Railway Station",
                "travelDate": "2026-10-30",
                "departureTime": "12:00",
                "alternatives": 3,
                "objective": "distance",
            }
        },
    }

    @field_validator("source", "destination")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Field cannot be empty or whitespace only")
        return s


class Geometry(BaseModel):
    type: Literal["LineString"] = "LineString"
    coordinates: List[List[float]]  # [[lon, lat], ...]


class DistinctnessInfo(BaseModel):
    maximum_shared_length_fraction: float
    maximum_allowed: float
    cost_ratio_to_best: float


class RouteItem(BaseModel):
    route_id: str
    name: Optional[str] = None
    geometry: Geometry
    coordinates: List[List[float]]  # [[lat, lon], ...] for Leaflet
    distance_km: float
    estimated_duration_seconds: Optional[float] = None
    routing_objective: str
    warnings: List[str]
    osm_way_ids: List[int]
    node_ids: List[int]
    distinctness: DistinctnessInfo


class SnapInfo(BaseModel):
    input_coordinates: List[float]
    node_id: int
    snapped_coordinates: List[float]
    distance_m: float


class AlternativesPolicy(BaseModel):
    requested: int
    returned: int
    candidates_examined: int
    candidate_limit: int
    max_cost_ratio: float
    overlap_definition: str
    ranking: str
    exhaustive: bool


class RouteResponse(BaseModel):
    schema_version: str
    crs: str
    coordinate_order: str
    attribution: str
    source: str
    destination: str
    travel_date: Optional[str] = None
    departure_time: Optional[str] = None
    source_snap: SnapInfo
    destination_snap: SnapInfo
    alternatives_policy: AlternativesPolicy
    routes: List[RouteItem]


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class ReadyResponse(BaseModel):
    status: str
    routing_ready: bool
    nodes: Optional[int] = None
    directed_edges: Optional[int] = None
    bbox: Optional[List[float]] = None
    sha256: Optional[str] = None
    error: Optional[str] = None
