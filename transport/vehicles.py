from typing import List, Optional
from models.vehicle import VehicleType

# Define vehicle fleet configuration details
FLEET = [
    VehicleType(name="Truck", capacity_kg=8000.0, speed_kmh=50.0, cost_per_km=1.5, terrain_support=["Land"]),
    VehicleType(name="Boat", capacity_kg=4000.0, speed_kmh=20.0, cost_per_km=3.0, terrain_support=["Water"]),
    VehicleType(name="Helicopter", capacity_kg=5000.0, speed_kmh=180.0, cost_per_km=15.0, terrain_support=["Air"]),
    VehicleType(name="Drone", capacity_kg=100.0, speed_kmh=60.0, cost_per_km=0.5, terrain_support=["Air"])
]

def select_best_vehicle(
    distance_km: float,
    total_weight_kg: float,
    road_accessibility: float,
    weather: str,
    rainfall: float,
    disaster_type: str,
    urgency_priority: float,
    disabled_vehicles: List[str] = None
) -> Optional[VehicleType]:
    """
    Selects the best vehicle type for a dispatch based on terrain constraints,
    distance, weather conditions, capacity, and travel time optimization.
    """
    disabled_vehicles = disabled_vehicles or []
    eligible_vehicles = []
    
    for v in FLEET:
        if v.name in disabled_vehicles:
            continue
            
        # 1. Capacity constraints
        if total_weight_kg > v.capacity_kg:
            continue
            
        # 2. Weather constraints
        if "Air" in v.terrain_support:
            if weather == "Storm" or rainfall > 50.0:
                continue # Air operations grounded
            if v.name == "Drone" and rainfall > 20.0:
                continue # Drones grounded in moderate/heavy rain
                
        # 3. Distance constraints
        if v.name == "Drone" and distance_km > 40.0:
            continue # Drones limited in range
            
        # 4. Terrain & Accessibility constraints
        if "Land" in v.terrain_support:
            if road_accessibility <= 0.2:
                continue # Road impassable for Truck
                
        if "Water" in v.terrain_support:
            # Boat can only be used if there is flooding or roads are very bad (access <= 0.4)
            if disaster_type != "Flood" and road_accessibility > 0.4:
                continue
                
        eligible_vehicles.append(v)
        
    if not eligible_vehicles:
        return None
        
    # Standard: Optimize for minimum delivery time (distance / speed)
    # For high priority, strictly minimize time.
    # Otherwise, minimize time but tie-break with cost.
    best_vehicle = min(eligible_vehicles, key=lambda v: (distance_km / v.speed_kmh, v.cost_per_km))
    return best_vehicle
