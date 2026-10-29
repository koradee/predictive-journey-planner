from contextlib import asynccontextmanager
import logging
from pathlib import Path
import sys

# Ensure repository root is in sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.schemas import (
    HealthResponse,
    ReadyResponse,
    RouteRequest,
    RouteResponse,
)
from backend.service import routing_service
from routing.engine import RoutingError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pjp-backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: check and warm up routing graph
    logger.info("Initializing Predictive Journey Planner backend...")
    readiness = routing_service.check_readiness()
    if readiness.get("routing_ready"):
        logger.info(
            "Pune OSM routing graph verified and ready (%d nodes, %d edges).",
            readiness.get("nodes", 0),
            readiness.get("directed_edges", 0),
        )
    else:
        logger.warning(
            "Pune routing graph not ready: %s",
            readiness.get("error", "Unknown"),
        )
    yield
    logger.info("Shutting down backend.")


app = FastAPI(
    title="Predictive Journey Planner API",
    description="FastAPI service for Pune road network routing and journey planning.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RoutingError)
async def routing_error_handler(request, exc: RoutingError):
    status_code_map = {
        "missing_graph": status.HTTP_503_SERVICE_UNAVAILABLE,
        "invalid_graph": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "outside_pilot": status.HTTP_400_BAD_REQUEST,
        "no_snap": status.HTTP_400_BAD_REQUEST,
        "same_location": status.HTTP_400_BAD_REQUEST,
        "unsupported_location": status.HTTP_400_BAD_REQUEST,
        "disconnected": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "unsupported_time": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "invalid_coordinates": status.HTTP_400_BAD_REQUEST,
        "invalid_alternatives": status.HTTP_400_BAD_REQUEST,
        "unsupported_objective": status.HTTP_400_BAD_REQUEST,
    }
    http_status = status_code_map.get(exc.code, status.HTTP_400_BAD_REQUEST)
    return JSONResponse(
        status_code=http_status,
        content={"detail": str(exc), "code": exc.code},
    )


@app.get("/api/health", response_model=HealthResponse)
@app.get("/health", response_model=HealthResponse)
@app.get("/", response_model=HealthResponse)
@app.get("/api", response_model=HealthResponse)
async def get_health():
    """Liveness probe to confirm backend is running."""
    return HealthResponse(
        status="ok",
        service="predictive-journey-planner-backend",
        version="1.0.0",
    )


@app.get("/api/ready", response_model=ReadyResponse)
@app.get("/ready", response_model=ReadyResponse)
async def get_ready():
    """Readiness probe to confirm actual Pune OSM routing data is verified and loaded."""
    info = routing_service.check_readiness()
    if not info.get("routing_ready"):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "routing_ready": False,
                "error": info.get("error", "Routing graph not ready"),
            },
        )
    return ReadyResponse(
        status="ready",
        routing_ready=True,
        nodes=info.get("nodes"),
        directed_edges=info.get("directed_edges"),
        bbox=info.get("bbox"),
        sha256=info.get("sha256"),
    )


@app.post("/api/routes", response_model=RouteResponse)
@app.post("/routes", response_model=RouteResponse)
async def post_routes(req: RouteRequest):
    """
    Calculate real Pune road-network routes between source and destination.
    Validates inputs, maps locations to OSM road network snaps, and returns routes.
    """
    try:
        result = routing_service.calculate_routes(
            source=req.source,
            destination=req.destination,
            travel_date=req.travel_date,
            departure_time=req.departure_time,
            source_coords=req.source_coordinates,
            destination_coords=req.destination_coordinates,
            alternatives=req.alternatives,
            objective=req.objective,
        )
        return RouteResponse(**result)
    except RoutingError:
        raise
    except Exception as exc:
        logger.exception("Unexpected error calculating routes")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Route calculation failed: {str(exc)}",
        )

