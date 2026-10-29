import json
from pathlib import Path
import sys
import unittest

# Ensure repository root is on path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from backend.main import app


class BackendApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "predictive-journey-planner-backend")

    def test_ready_endpoint(self):
        response = self.client.get("/api/ready")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ready")
        self.assertTrue(data["routing_ready"])
        self.assertEqual(data["nodes"], 12325)
        self.assertEqual(data["directed_edges"], 22104)
        self.assertIsNotNone(data["sha256"])

    def test_routes_shivajinagar_to_station(self):
        payload = {
            "source": "Shivajinagar, Pune",
            "destination": "Pune Railway Station",
            "travelDate": "2026-10-30",
            "departureTime": "14:30",
            "alternatives": 3,
            "objective": "distance",
        }
        response = self.client.post("/api/routes", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["schema_version"], "pune-routing-v1")
        self.assertIn("routes", data)
        self.assertGreaterEqual(len(data["routes"]), 1)
        
        first_route = data["routes"][0]
        self.assertIn("geometry", first_route)
        self.assertEqual(first_route["geometry"]["type"], "LineString")
        # Real calculated distance is approximately 3.35 km
        self.assertAlmostEqual(first_route["distance_km"], 3.355, delta=0.1)
        self.assertGreater(len(first_route["geometry"]["coordinates"]), 50)
        # Check Leaflet coordinates [lat, lon] are also provided
        self.assertIn("coordinates", first_route)
        self.assertAlmostEqual(first_route["coordinates"][0][0], 18.531, delta=0.01)
        self.assertAlmostEqual(first_route["coordinates"][0][1], 73.844, delta=0.01)

    def test_routes_station_to_shivajinagar_reverse(self):
        payload = {
            "source": "Pune Railway Station",
            "destination": "Shivajinagar, Pune",
            "travelDate": "2026-10-30",
            "departureTime": "16:00",
            "alternatives": 3,
        }
        response = self.client.post("/api/routes", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(len(data["routes"]), 1)
        # In reverse, distance is around 4.19 km due to one-way streets
        self.assertAlmostEqual(data["routes"][0]["distance_km"], 4.19, delta=0.2)

    def test_unsupported_location_rejected(self):
        payload = {
            "source": "Mumbai Marine Drive",
            "destination": "Pune Railway Station",
            "travelDate": "2026-10-30",
            "departureTime": "12:00",
        }
        response = self.client.post("/api/routes", json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data.get("code"), "unsupported_location")
        self.assertIn("unsupported", data.get("detail", "").lower())

    def test_same_location_rejected(self):
        payload = {
            "source": "Shivajinagar, Pune",
            "destination": "Shivajinagar, Pune",
            "travelDate": "2026-10-30",
            "departureTime": "12:00",
        }
        response = self.client.post("/api/routes", json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data.get("code"), "same_location")

    def test_coordinates_outside_bounds_rejected(self):
        payload = {
            "source": "Shivajinagar, Pune",
            "destination": "Custom point",
            "destination_coordinates": [72.8777, 19.0760],  # Mumbai coords
            "travelDate": "2026-10-30",
            "departureTime": "12:00",
        }
        response = self.client.post("/api/routes", json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data.get("code"), "outside_pilot")

    def test_invalid_alternatives_validation(self):
        payload = {
            "source": "Shivajinagar, Pune",
            "destination": "Pune Railway Station",
            "alternatives": 5,  # Max allowed is 3
        }
        response = self.client.post("/api/routes", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_service_readiness_failure_handling(self):
        from backend.service import RoutingService
        dummy_service = RoutingService(root_dir=Path("/non/existent/path"))
        info = dummy_service.check_readiness()
        self.assertFalse(info["routing_ready"])
        self.assertIn("not found", info["error"])


if __name__ == "__main__":
    unittest.main()
