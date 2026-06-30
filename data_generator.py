import os
import pandas as pd
import numpy as np

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Set seed for reproducibility
np.random.seed(42)

NUM_ZONES = 100

def generate_zones():
    zone_ids = [f"Z-{str(i).zfill(3)}" for i in range(1, NUM_ZONES + 1)]
    populations = np.random.randint(5000, 100000, size=NUM_ZONES)
    # Vulnerability index (0.0 to 1.0)
    vulnerabilities = np.round(np.random.beta(a=2, b=5, size=NUM_ZONES), 2)
    infrastructure_count = np.random.randint(1, 10, size=NUM_ZONES)

    df = pd.DataFrame({
        "zone_id": zone_ids,
        "population": populations,
        "vulnerability_index": vulnerabilities,
        "critical_infrastructure_count": infrastructure_count
    })
    
    df.to_csv(os.path.join(DATA_DIR, "zones.csv"), index=False)
    print("Created zones.csv")

def generate_disaster_status():
    zone_ids = [f"Z-{str(i).zfill(3)}" for i in range(1, NUM_ZONES + 1)]
    days_since_onset = np.random.choice([1, 2, 3], size=NUM_ZONES) # Early disaster stage
    
    # Damage severity heavily influenced by vulnerability (for realism)
    zones_df = pd.read_csv(os.path.join(DATA_DIR, "zones.csv"))
    base_damage = np.random.normal(50, 20, size=NUM_ZONES)
    damage_severity = np.clip(base_damage + (zones_df['vulnerability_index'] * 30), 0, 100).round(2)
    
    displaced = (zones_df['population'] * (damage_severity / 100) * np.random.uniform(0.3, 0.8, size=NUM_ZONES)).astype(int)
    
    # Road accessibility is inversely proportional to damage
    road_access = np.clip(1.0 - (damage_severity / 100) + np.random.normal(0, 0.1, size=NUM_ZONES), 0, 1.0).round(2)

    df = pd.DataFrame({
        "zone_id": zone_ids,
        "days_since_onset": days_since_onset,
        "damage_severity_pct": damage_severity,
        "displaced_people_est": displaced,
        "road_accessibility": road_access
    })
    
    df.to_csv(os.path.join(DATA_DIR, "disaster_status.csv"), index=False)
    print("Created disaster_status.csv")

def generate_resource_inventory():
    resources = [
        {"resource_id": "RES-WTR", "category": "Water", "units_available": 500000, "unit_weight_kg": 5.0},
        {"resource_id": "RES-FOD", "category": "Food", "units_available": 300000, "unit_weight_kg": 2.5},
        {"resource_id": "RES-MED", "category": "Medical", "units_available": 50000, "unit_weight_kg": 1.0},
        {"resource_id": "RES-SHL", "category": "Shelter", "units_available": 20000, "unit_weight_kg": 15.0},
    ]
    
    df = pd.DataFrame(resources)
    df.to_csv(os.path.join(DATA_DIR, "resource_inventory.csv"), index=False)
    print("Created resource_inventory.csv")

if __name__ == "__main__":
    generate_zones()
    generate_disaster_status()
    generate_resource_inventory()
    print("Data generation complete.")
