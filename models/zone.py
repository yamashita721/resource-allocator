from pydantic import BaseModel
from typing import Dict, Any

class ZoneState(BaseModel):
    zone_id: str
    latitude: float
    longitude: float
    population: int
    vulnerability_index: float
    critical_infrastructure_count: int
    affected_population: int
    disaster_type: str
    severity: float  # 0.0 to 100.0
    weather: str     # "Clear", "Rainy", "Storm", etc.
    rainfall: float  # mm
    road_accessibility: float # 0.0 to 1.0
    shelter_capacity: int
    shelter_occupancy: int
    power_status: str          # "Active" or "Down"
    communication_status: str  # "Active" or "Down"
    current_inventory: Dict[str, int]  # resource_id -> quantity
    active_requests: Dict[str, int]    # resource_id -> quantity
