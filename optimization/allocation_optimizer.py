import os
import json
from typing import Dict, Any, List, Optional
from optimization.routing import RouteOptimizer
from transport.vehicles import select_best_vehicle

DATA_DIR = "data"
SCENARIO_PATH = os.path.join(DATA_DIR, "active_scenario.json")

class AllocationLogisticsPlanner:
    def __init__(self, data_dir: str = DATA_DIR):
        self.data_dir = data_dir
        self.routing_optimizer = None
        
    def load_network(self):
        self.routing_optimizer = RouteOptimizer(self.data_dir)

    def _get_active_scenario(self) -> Dict[str, Any]:
        """Loads active simulation scenario overrides."""
        default = {
            "failed_warehouses": [],
            "blocked_zones": [],
            "disabled_vehicles": [],
            "rain_modifier": 1.0,
            "affected_population_modifier": 1.0
        }
        if os.path.exists(SCENARIO_PATH):
            try:
                with open(SCENARIO_PATH, "r") as f:
                    return json.load(f)
            except Exception:
                return default
        return default

    def optimize_dispatch(
        self,
        zone_id: str,
        resource_id: str,
        quantity: int,
        weight_per_unit: float,
        road_accessibility: float,
        weather: str,
        rainfall: float,
        disaster_type: str,
        priority_score: float
    ) -> Optional[Dict[str, Any]]:
        """
        Finds the best warehouse and vehicle to deliver the requested resources in minimum time,
        subject to warehouse inventory, vehicle capacity, and routing constraints.
        """
        scenario = self._get_active_scenario()
        failed_whs = scenario.get("failed_warehouses", [])
        blocked_nodes = scenario.get("blocked_zones", [])
        disabled_vehs = scenario.get("disabled_vehicles", [])
        
        # Load warehouses
        wh_path = os.path.join(self.data_dir, "warehouses.json")
        if not os.path.exists(wh_path):
            return None
            
        with open(wh_path, "r") as f:
            warehouses = json.load(f)
            
        best_dispatch = None
        min_eta = float('inf')
        
        for wh in warehouses:
            # 1. Check warehouse status & availability
            if not wh["availability"] or wh["warehouse_id"] in failed_whs:
                continue
                
            # 2. Check if warehouse has the inventory
            available_qty = wh["inventory"].get(resource_id, 0)
            if available_qty <= 0:
                continue
                
            # Determine actual dispatch quantity (cap at warehouse availability)
            dispatch_qty = min(quantity, available_qty)
            total_weight = dispatch_qty * weight_per_unit
            
            # Find the best vehicle from this warehouse to the zone
            # Iterate over vehicle types to find the one that minimizes ETA
            from transport.vehicles import FLEET
            
            for vehicle in FLEET:
                # Select vehicle if it is eligible
                v = select_best_vehicle(
                    distance_km=10.0, # dummy distance just to pre-verify capacity/weather constraints
                    total_weight_kg=total_weight,
                    road_accessibility=road_accessibility,
                    weather=weather,
                    rainfall=rainfall,
                    disaster_type=disaster_type,
                    urgency_priority=priority_score,
                    disabled_vehicles=disabled_vehs
                )
                
                if not v or v.name != vehicle.name:
                    continue
                    
                # Run routing optimizer for actual distance and path
                route_res = self.routing_optimizer.get_route(
                    start_id=wh["warehouse_id"],
                    end_id=zone_id,
                    vehicle_name=v.name,
                    road_accessibility={zone_id: road_accessibility}, # simplistic dictionary
                    blocked_nodes=blocked_nodes
                )
                
                if not route_res:
                    continue
                    
                dist = route_res["distance_km"]
                
                # Check Drone range restriction again on actual route distance
                if v.name == "Drone" and dist > 40.0:
                    continue
                    
                eta = dist / v.speed_kmh
                
                if eta < min_eta:
                    min_eta = eta
                    best_dispatch = {
                        "warehouse_id": wh["warehouse_id"],
                        "vehicle_name": v.name,
                        "distance": dist,
                        "eta": round(eta, 2),
                        "allocated_quantity": dispatch_qty,
                        "path": route_res["path_nodes"],
                        "coordinates": route_res["path_coordinates"]
                    }
                    
        return best_dispatch
