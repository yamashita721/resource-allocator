from pydantic import BaseModel
from typing import Dict

class WarehouseState(BaseModel):
    warehouse_id: str
    location: str
    latitude: float
    longitude: float
    inventory: Dict[str, int]  # resource_id -> quantity
    capacity: float             # Max weight capacity in kg
    availability: bool
