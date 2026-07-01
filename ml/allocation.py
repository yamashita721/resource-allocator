import os
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Any
from data.situation import SituationManager
from ml.demand_predictor import DemandPredictor
from optimization.allocation_optimizer import AllocationLogisticsPlanner
from warehouse.warehouses import WarehouseInventoryManager
from blockchain.ledger import log_allocation_hash, ledger

DATA_DIR = "data"

def load_data():
    zones = pd.read_csv(os.path.join(DATA_DIR, "zones.csv"))
    status = pd.read_csv(os.path.join(DATA_DIR, "disaster_status.csv"))
    
    # Warehouses
    with open(os.path.join(DATA_DIR, "warehouses.json"), "r") as f:
        warehouses = json.load(f)
        
    # Catalog
    with open(os.path.join(DATA_DIR, "resources.json"), "r") as f:
        catalog = json.load(f)["resources"]
        
    return zones, status, warehouses, catalog

def calculate_priority(merged_df):
    """
    Original priority calculation (re-implemented for backward compatibility):
    - Vulnerability (0-1) weight: 0.3
    - Damage severity (0-100) weight: 0.4
    - Displacement ratio (displaced/population) weight: 0.2
    - Road inaccessibility (1 - access) weight: 0.1
    """
    vulnerability = merged_df['vulnerability_index']
    damage = merged_df['damage_severity_pct'] / 100.0
    
    # Fallback if displaced_people_est isn't populated
    displaced_ratio = merged_df['displaced_people_est'] / merged_df['population']
    inaccessibility = 1.0 - merged_df['road_accessibility']

    # Higher score = higher priority
    priority_score = (vulnerability * 0.3) + (damage * 0.4) + (displaced_ratio * 0.2) + (inaccessibility * 0.1)
    
    # Scale to 0-100
    merged_df['priority_score'] = (priority_score * 100).round(2)
    return merged_df.sort_values(by='priority_score', ascending=False)

def run_allocation() -> str:
    """
    Executes the advanced predictive and logistics allocation flow:
    1. Load situation states.
    2. Run ML Demand Prediction -> forecast shortages.
    3. Run Logistics Optimization (Warehouse + Vehicle + Route selection).
    4. Deduct warehouse inventory & update zone inventory.
    5. Log dispatches to mock blockchain ledger.
    6. Write allocation plan output to data/allocation_plan.csv.
    """
    print("Initializing components...")
    predictor = DemandPredictor()
    planner = AllocationLogisticsPlanner()
    inventory_manager = WarehouseInventoryManager()
    
    print("Loading data...")
    zones_df, status_df, warehouses, catalog = load_data()
    
    merged = pd.merge(zones_df, status_df, on='zone_id')
    prioritized = calculate_priority(merged)
    
    # Prepare active scenarios from environment or states
    # Let's read the road network graph to pass to planner
    planner.load_network()
    
    dispatches = []
    allocation_plan_rows = []
    
    # For each prioritized zone, check shortages and run routing planner
    for _, row in prioritized.iterrows():
        zone_id = str(row["zone_id"])
        
        # Load zone states
        inv_dict = json.loads(row["current_inventory"])
        
        # Predict demands
        pred_res = predictor.predict_zone_demands(
            population=int(row["population"]),
            vulnerability=float(row["vulnerability_index"]),
            severity=float(row["damage_severity_pct"]),
            days_since_onset=int(row["days_since_onset"]),
            weather=str(row["weather"]),
            rainfall=float(row["rainfall"]),
            shelter_occupancy=int(row["shelter_occupancy"]),
            historical_disasters=int(row["critical_infrastructure_count"] // 2), # proxy
            current_inventory=inv_dict
        )
        
        predictions = pred_res["predictions"]
        shortage_probs = pred_res["shortage_probability"]
        
        # For resources with shortage probability > 0.1 and predicted demand > current inventory
        allocated_qty = {}
        for res_id, req_qty in predictions.items():
            current_inv = inv_dict.get(res_id, 0)
            shortage = max(0, req_qty - current_inv)
            
            # Default initialized to 0
            allocated_qty[f"allocated_{res_id}"] = 0
            
            if shortage > 0:
                # Find resource weight
                item_info = next((item for item in catalog if item["id"] == res_id), None)
                weight_per_unit = item_info["weight_kg"] if item_info else 1.0
                
                # Run optimizer to find warehouse, route, and vehicle
                dispatch_opt = planner.optimize_dispatch(
                    zone_id=zone_id,
                    resource_id=res_id,
                    quantity=shortage,
                    weight_per_unit=weight_per_unit,
                    road_accessibility=float(row["road_accessibility"]),
                    weather=str(row["weather"]),
                    rainfall=float(row["rainfall"]),
                    disaster_type=str(row["disaster_type"]),
                    priority_score=float(row["priority_score"])
                )
                
                if dispatch_opt:
                    selected_wh = dispatch_opt["warehouse_id"]
                    selected_vehicle = dispatch_opt["vehicle_name"]
                    eta = dispatch_opt["eta"]
                    dist = dispatch_opt["distance"]
                    actual_allocated = dispatch_opt["allocated_quantity"]
                    
                    # Deduct warehouse inventory & update zone inventory
                    success = inventory_manager.execute_delivery(
                        warehouse_id=selected_wh,
                        zone_id=zone_id,
                        resource_id=res_id,
                        quantity=actual_allocated
                    )
                    
                    if success:
                        allocated_qty[f"allocated_{res_id}"] = actual_allocated
                        
                        # Add dispatch transaction log details
                        dispatches.append({
                            "warehouse_id": selected_wh,
                            "vehicle_type": selected_vehicle,
                            "handler": f"Operator-{selected_vehicle[:3].upper()}-{selected_wh[-3:]}",
                            "gps": {"latitude": float(row["latitude"]), "longitude": float(row["longitude"])},
                            "timestamp": pd.Timestamp.now().isoformat(),
                            "resource": res_id,
                            "quantity": actual_allocated
                        })
                        
        plan_row = {
            "zone_id": zone_id,
            "priority_score": row["priority_score"]
        }
        # Add allocated columns
        plan_row.update(allocated_qty)
        allocation_plan_rows.append(plan_row)

    # Save allocation plan csv
    plan_df = pd.DataFrame(allocation_plan_rows)
    
    # Ensure backward compatible columns exist if they didn't get allocated
    for legacy_id in ["RES-WTR", "RES-FOD", "RES-MED"]:
        col_name = f"allocated_{legacy_id}"
        if col_name not in plan_df.columns:
            plan_df[col_name] = 0
            
    # Re-order columns to put priority columns first
    cols = ['zone_id', 'priority_score', 'allocated_RES-WTR', 'allocated_RES-FOD', 'allocated_RES-MED']
    remaining_cols = [c for c in plan_df.columns if c not in cols]
    plan_df = plan_df[cols + remaining_cols]
    
    output_path = os.path.join(DATA_DIR, "allocation_plan.csv")
    plan_df.to_csv(output_path, index=False)
    print(f"Saved extended allocation plan to {output_path}")
    
    # 2. Hash allocation plan & Log to blockchain
    import hashlib
    sha256_hash = hashlib.sha256()
    with open(output_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    plan_hash = sha256_hash.hexdigest()
    
    # Log the dispatches with hash to the chain
    ledger.log_dispatch_batch(allocation_hash=plan_hash, dispatches=dispatches)
    
    return output_path
