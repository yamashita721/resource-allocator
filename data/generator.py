import os
import json
import random
import numpy as np
import pandas as pd

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Fixed seed for reproducibility
np.random.seed(42)
random.seed(42)

NUM_ZONES = 100
LAT_MIN, LAT_MAX = 13.0, 14.5
LON_MIN, LON_MAX = 120.0, 122.5

WAREHOUSES = [
    {"warehouse_id": "WH-001", "location": "Port Metro (Manila)", "latitude": 14.599, "longitude": 120.984, "capacity": 1000000.0, "availability": True},
    {"warehouse_id": "WH-002", "location": "South Hub (Batangas)", "latitude": 13.756, "longitude": 121.058, "capacity": 500000.0, "availability": True},
    {"warehouse_id": "WH-003", "location": "Island Depot (Calapan)", "latitude": 13.412, "longitude": 121.180, "capacity": 400000.0, "availability": True},
    {"warehouse_id": "WH-004", "location": "Inland Depot (Lucena)", "latitude": 13.931, "longitude": 121.613, "capacity": 600000.0, "availability": True},
    {"warehouse_id": "WH-005", "location": "East Outpost (Boac)", "latitude": 13.444, "longitude": 121.841, "capacity": 300000.0, "availability": True}
]

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates the great-circle distance between two points in kilometers."""
    r = 6371.0 # Earth's radius in km
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)
    
    a = np.sin(delta_phi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return round(r * c, 2)

def generate_zones():
    zone_ids = [f"Z-{str(i).zfill(3)}" for i in range(1, NUM_ZONES + 1)]
    populations = np.random.randint(5000, 100000, size=NUM_ZONES)
    vulnerabilities = np.round(np.random.beta(a=2, b=5, size=NUM_ZONES), 2)
    infrastructure_count = np.random.randint(1, 10, size=NUM_ZONES)
    
    # Generate geographic locations within the bounding box
    latitudes = np.round(np.random.uniform(LAT_MIN, LAT_MAX, size=NUM_ZONES), 4)
    longitudes = np.round(np.random.uniform(LON_MIN, LON_MAX, size=NUM_ZONES), 4)
    
    # Shelter capacity is proportional to population
    shelter_capacities = (populations * np.random.uniform(0.05, 0.15, size=NUM_ZONES)).astype(int)
    
    df = pd.DataFrame({
        "zone_id": zone_ids,
        "population": populations,
        "vulnerability_index": vulnerabilities,
        "critical_infrastructure_count": infrastructure_count,
        "latitude": latitudes,
        "longitude": longitudes,
        "shelter_capacity": shelter_capacities
    })
    
    df.to_csv(os.path.join(DATA_DIR, "zones.csv"), index=False)
    print("Created zones.csv")

def generate_disaster_status():
    zone_ids = [f"Z-{str(i).zfill(3)}" for i in range(1, NUM_ZONES + 1)]
    days_since_onset = np.random.choice([1, 2, 3], size=NUM_ZONES)
    
    zones_df = pd.read_csv(os.path.join(DATA_DIR, "zones.csv"))
    
    # Damage severity heavily influenced by vulnerability
    base_damage = np.random.normal(50, 20, size=NUM_ZONES)
    damage_severity = np.clip(base_damage + (zones_df['vulnerability_index'] * 30), 0, 100).round(2)
    
    affected = (zones_df['population'] * (damage_severity / 100) * np.random.uniform(0.4, 0.8, size=NUM_ZONES)).astype(int)
    road_access = np.clip(1.0 - (damage_severity / 100) + np.random.normal(0, 0.1, size=NUM_ZONES), 0, 1.0).round(2)
    
    shelter_occ = (affected * np.random.uniform(0.1, 0.3, size=NUM_ZONES)).astype(int)
    # Clip shelter occupancy to shelter capacity
    shelter_occ = np.minimum(zones_df['shelter_capacity'], shelter_occ)
    
    weather_options = ["Clear", "Cloudy", "Rainy", "Storm"]
    weather = np.random.choice(weather_options, size=NUM_ZONES, p=[0.2, 0.3, 0.4, 0.1])
    
    rainfall = []
    for w in weather:
        if w == "Storm":
            rainfall.append(round(random.uniform(50, 100), 1))
        elif w == "Rainy":
            rainfall.append(round(random.uniform(10, 45), 1))
        else:
            rainfall.append(0.0)
            
    power_status = ["Active" if sev < 40.0 else "Down" for sev in damage_severity]
    comm_status = ["Active" if sev < 50.0 else "Down" for sev in damage_severity]
    
    disaster_types = []
    for sev in damage_severity:
        if sev > 60.0:
            disaster_types.append("Flood")
        elif sev > 30.0:
            disaster_types.append("Storm Surge")
        else:
            disaster_types.append("None")
            
    df = pd.DataFrame({
        "zone_id": zone_ids,
        "days_since_onset": days_since_onset,
        "damage_severity_pct": damage_severity,
        "displaced_people_est": shelter_occ, # mapped to displaced for compatibility
        "road_accessibility": road_access,
        "affected_population": affected,
        "disaster_type": disaster_types,
        "weather": weather,
        "rainfall": rainfall,
        "shelter_occupancy": shelter_occ,
        "power_status": power_status,
        "communication_status": comm_status
    })
    
    # Initialize inventories and active requests for zones
    current_inventories = []
    active_requests = []
    
    for idx, row in zones_df.iterrows():
        pop = row["population"]
        aff = affected[idx]
        sev = damage_severity[idx]
        
        # Zones start with some basic safety stocks
        inv = {
            "RES-WTR": int(pop * 0.05),
            "RES-FOD": int(pop * 0.02),
            "RES-MED": int(pop * 0.005)
        }
        current_inventories.append(json.dumps(inv))
        
        # Requests are based on shortages
        req = {
            "RES-WTR": max(0, int(aff * 3.0 * (sev / 50.0)) - inv["RES-WTR"]),
            "RES-FOD": max(0, int(aff * 1.5 * (sev / 50.0)) - inv["RES-FOD"]),
            "RES-MED": max(0, int(aff * 0.2 * (sev / 50.0)) - inv["RES-MED"]),
            "RES-TNT": max(0, int((aff // 5) * (sev / 80.0)))
        }
        active_requests.append(json.dumps(req))
        
        # Populate inline cols for backward compatibility
        for res_id, qty in inv.items():
            df[f"allocated_{res_id}"] = 0
            
    df["current_inventory"] = current_inventories
    df["active_requests"] = active_requests
    
    # Populate inline cols with inventory
    for idx, row in df.iterrows():
        inv = json.loads(current_inventories[idx])
        for res_id, qty in inv.items():
            df.loc[idx, f"allocated_{res_id}"] = qty
            
    df.to_csv(os.path.join(DATA_DIR, "disaster_status.csv"), index=False)
    print("Created disaster_status.csv")

def generate_resource_inventory():
    """Generates legacy resource list for backward compatibility."""
    resources = [
        {"resource_id": "RES-WTR", "category": "Water", "units_available": 1000000, "unit_weight_kg": 1.0},
        {"resource_id": "RES-FOD", "category": "Food", "units_available": 600000, "unit_weight_kg": 0.5},
        {"resource_id": "RES-MED", "category": "Medical", "units_available": 100000, "unit_weight_kg": 0.2},
        {"resource_id": "RES-SHL", "category": "Shelter", "units_available": 50000, "unit_weight_kg": 15.0},
    ]
    df = pd.DataFrame(resources)
    df.to_csv(os.path.join(DATA_DIR, "resource_inventory.csv"), index=False)
    print("Created resource_inventory.csv")

def generate_warehouses():
    """Creates warehouses with balanced initial stock."""
    # Read resource JSON catalog
    with open(os.path.join(DATA_DIR, "resources.json"), "r") as f:
        catalog = json.load(f)["resources"]
        
    warehouses_data = []
    for wh in WAREHOUSES:
        wh_state = wh.copy()
        wh_state["inventory"] = {}
        
        # Allocate stock proportionally to warehouse size
        stock_factor = wh["capacity"] / 1000000.0
        
        for item in catalog:
            res_id = item["id"]
            # Different warehouses specialize in different classes of items
            if wh["warehouse_id"] == "WH-001": # Port Metro: holds everything, specializes in heavy recovery
                mult = 1.2
            elif wh["warehouse_id"] == "WH-002" and item["category"] == "Immediate": # South Hub: specializes in immediate relief
                mult = 1.5
            elif wh["warehouse_id"] == "WH-003" and item["category"] == "Immediate": # Island Depot: specializes in immediate/short term
                mult = 0.8
            elif wh["warehouse_id"] == "WH-005": # Island outpost: smaller capacity
                mult = 0.5
            else:
                mult = 1.0
                
            if item["category"] == "Immediate":
                qty = int(200000 * stock_factor * mult)
            elif item["category"] == "Short Term":
                qty = int(50000 * stock_factor * mult)
            else: # Recovery
                qty = int(20000 * stock_factor * mult)
                
            wh_state["inventory"][res_id] = qty
            
        warehouses_data.append(wh_state)
        
    with open(os.path.join(DATA_DIR, "warehouses.json"), "w") as f:
        json.dump(warehouses_data, f, indent=4)
    print("Created warehouses.json")

def generate_road_network():
    """Generates a connected road network graph for routing optimizations."""
    zones_df = pd.read_csv(os.path.join(DATA_DIR, "zones.csv"))
    
    # Store node coordinates
    nodes = {}
    for _, row in zones_df.iterrows():
        nodes[str(row["zone_id"])] = {
            "id": str(row["zone_id"]),
            "type": "zone",
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"])
        }
        
    for wh in WAREHOUSES:
        nodes[wh["warehouse_id"]] = {
            "id": wh["warehouse_id"],
            "type": "warehouse",
            "latitude": wh["latitude"],
            "longitude": wh["longitude"]
        }
        
    # Generate edges: connect each node to its k nearest neighbors to simulate a mesh network
    edges = []
    k_neighbors = 3
    
    node_ids = list(nodes.keys())
    
    for i, id1 in enumerate(node_ids):
        n1 = nodes[id1]
        distances = []
        for j, id2 in enumerate(node_ids):
            if id1 == id2:
                continue
            n2 = nodes[id2]
            d = haversine_distance(n1["latitude"], n1["longitude"], n2["latitude"], n2["longitude"])
            distances.append((d, id2))
            
        distances.sort()
        # Connect to closest k
        for d, id2 in distances[:k_neighbors]:
            # Sort node names to prevent duplicate edges in undirected graph
            edge = sorted([id1, id2])
            edge_obj = {"from_node": edge[0], "to_node": edge[1], "distance_km": d}
            if edge_obj not in edges:
                edges.append(edge_obj)
                
    road_network = {
        "nodes": list(nodes.values()),
        "edges": edges
    }
    
    with open(os.path.join(DATA_DIR, "road_network.json"), "w") as f:
        json.dump(road_network, f, indent=4)
    print("Created road_network.json")

def run_all():
    generate_zones()
    generate_disaster_status()
    generate_resource_inventory()
    generate_warehouses()
    generate_road_network()
    print("All disaster data assets successfully initialized.")

if __name__ == "__main__":
    run_all()
