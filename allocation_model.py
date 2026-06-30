import os
import pandas as pd
import numpy as np

DATA_DIR = "data"

def load_data():
    zones = pd.read_csv(os.path.join(DATA_DIR, "zones.csv"))
    status = pd.read_csv(os.path.join(DATA_DIR, "disaster_status.csv"))
    inventory = pd.read_csv(os.path.join(DATA_DIR, "resource_inventory.csv"))
    return zones, status, inventory

def calculate_priority(merged_df):
    """
    Calculates a priority score based on:
    - Vulnerability (0-1) weight: 0.3
    - Damage severity (0-100) weight: 0.4
    - Displacement ratio (displaced/population) weight: 0.2
    - Road inaccessibility (1 - access) weight: 0.1
    """
    vulnerability = merged_df['vulnerability_index']
    damage = merged_df['damage_severity_pct'] / 100.0
    displacement_ratio = merged_df['displaced_people_est'] / merged_df['population']
    inaccessibility = 1.0 - merged_df['road_accessibility']

    # Higher score = higher priority
    priority_score = (vulnerability * 0.3) + (damage * 0.4) + (displacement_ratio * 0.2) + (inaccessibility * 0.1)
    
    # Scale to 0-100
    merged_df['priority_score'] = (priority_score * 100).round(2)
    return merged_df.sort_values(by='priority_score', ascending=False)

def allocate_resources(prioritized_df, inventory):
    allocation = []
    
    for _, item in inventory.iterrows():
        res_id = item['resource_id']
        total_units = item['units_available']
        
        # Simple proportional allocation based on priority score
        # Give resources only to top 50 zones for realistic scarcity
        top_zones = prioritized_df.head(50).copy()
        total_priority = top_zones['priority_score'].sum()
        
        # Allocate proportionally
        top_zones[f'allocated_{res_id}'] = ((top_zones['priority_score'] / total_priority) * total_units).astype(int)
        
        if len(allocation) == 0:
            allocation = top_zones[['zone_id', 'priority_score', f'allocated_{res_id}']]
        else:
            allocation = allocation.merge(top_zones[['zone_id', f'allocated_{res_id}']], on='zone_id', how='left')

    # Fill NaNs for zones that didn't get allocated in lower tiers (if any)
    allocation = allocation.fillna(0)
    return allocation

def run_allocation():
    print("Loading data...")
    zones, status, inventory = load_data()
    
    print("Merging data and calculating priority...")
    merged = pd.merge(zones, status, on='zone_id')
    prioritized = calculate_priority(merged)
    
    print("Allocating resources...")
    allocation_plan = allocate_resources(prioritized, inventory)
    
    output_path = os.path.join(DATA_DIR, "allocation_plan.csv")
    allocation_plan.to_csv(output_path, index=False)
    print(f"Allocation plan saved to {output_path}")
    
    return output_path

if __name__ == "__main__":
    run_allocation()
