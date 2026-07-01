import os
import json
import pandas as pd
from typing import Dict, Any

DATA_DIR = "data"

class WarehouseInventoryManager:
    def __init__(self, data_dir: str = DATA_DIR):
        self.data_dir = data_dir
        self.wh_path = os.path.join(data_dir, "warehouses.json")
        self.status_path = os.path.join(data_dir, "disaster_status.csv")

    def execute_delivery(
        self,
        warehouse_id: str,
        zone_id: str,
        resource_id: str,
        quantity: int
    ) -> bool:
        """
        Processes a delivery:
        1. Deducts quantity from warehouse inventory.
        2. Increments quantity in zone inventory.
        3. Persists both updates.
        """
        if not os.path.exists(self.wh_path) or not os.path.exists(self.status_path):
            return False
            
        try:
            # 1. Update Warehouse
            with open(self.wh_path, "r") as f:
                warehouses = json.load(f)
                
            wh_found = False
            for wh in warehouses:
                if wh["warehouse_id"] == warehouse_id:
                    current_stock = wh["inventory"].get(resource_id, 0)
                    if current_stock < quantity:
                        # Insufficient inventory
                        return False
                    wh["inventory"][resource_id] = current_stock - quantity
                    wh_found = True
                    break
                    
            if not wh_found:
                return False
                
            # 2. Update Zone Inventory
            status_df = pd.read_csv(self.status_path)
            zone_mask = status_df["zone_id"] == zone_id
            
            if not zone_mask.any():
                return False
                
            row_idx = status_df[zone_mask].index[0]
            current_inv_str = status_df.loc[row_idx, "current_inventory"]
            
            try:
                inv_dict = json.loads(current_inv_str)
            except Exception:
                inv_dict = {}
                
            # Increment inventory
            inv_dict[resource_id] = inv_dict.get(resource_id, 0) + quantity
            status_df.loc[row_idx, "current_inventory"] = json.dumps(inv_dict)
            
            # Backward compatibility: update inline allocated_ columns
            col_name = f"allocated_{resource_id}"
            status_df.loc[row_idx, col_name] = inv_dict[resource_id]
            
            # Recalculate request for that resource since inventory increased
            active_req_str = status_df.loc[row_idx, "active_requests"]
            try:
                req_dict = json.loads(active_req_str)
                if resource_id in req_dict:
                    req_dict[resource_id] = max(0, req_dict[resource_id] - quantity)
                    status_df.loc[row_idx, "active_requests"] = json.dumps(req_dict)
            except Exception:
                pass
            
            # 3. Save updates
            with open(self.wh_path, "w") as f:
                json.dump(warehouses, f, indent=4)
                
            status_df.to_csv(self.status_path, index=False)
            return True
            
        except Exception as e:
            print(f"Error executing inventory updates: {e}")
            return False
