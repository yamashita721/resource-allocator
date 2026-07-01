from pydantic import BaseModel
from typing import List

class VehicleType(BaseModel):
    name: str
    capacity_kg: float
    speed_kmh: float
    cost_per_km: float
    terrain_support: List[str]  # e.g., ["Land"], ["Water"], ["Air"]
