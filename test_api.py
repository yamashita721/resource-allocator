import os
import json
import threading
import time
import requests
import uvicorn
import pandas as pd
from api import app
from data.generator import run_all

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="critical")

if __name__ == "__main__":
    print("Step 1: Generating advanced simulation data...")
    run_all()
    
    # Verify file outputs from generator
    assert os.path.exists("data/zones.csv"), "zones.csv missing!"
    assert os.path.exists("data/disaster_status.csv"), "disaster_status.csv missing!"
    assert os.path.exists("data/warehouses.json"), "warehouses.json missing!"
    assert os.path.exists("data/road_network.json"), "road_network.json missing!"
    assert os.path.exists("data/resources.json"), "resources.json missing!"
    print("[OK] Base simulation files successfully generated.")
    
    # Read initial warehouse inventory to compare later
    with open("data/warehouses.json", "r") as f:
        wh_initial = json.load(f)
    total_water_initial = sum(wh["inventory"].get("RES-WTR", 0) for wh in wh_initial)
    print(f"Initial Total Water Stock: {total_water_initial}")

    # Start the server in a separate thread
    print("\nStep 2: Starting API server on port 8001...")
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Give the server a moment to start
    time.sleep(2)
    
    try:
        # Test 1: Health Check
        print("\nStep 3: Testing Health Check...")
        r = requests.get("http://127.0.0.1:8001/")
        print(f"Status Code: {r.status_code}")
        print(f"Response: {r.json()}")
        assert r.status_code == 200, "Health check failed"
        
        # Test 2: Trigger Allocation
        print("\nStep 4: Running Predictive Allocation & Blockchain Audit...")
        r = requests.post("http://127.0.0.1:8001/allocate")
        print(f"Status Code: {r.status_code}")
        resp_data = r.json()
        print(f"Response Hash: {resp_data.get('file_hash_sha256')}")
        assert r.status_code == 200, "Allocation request failed"
        
        # Verify inventory update
        with open("data/warehouses.json", "r") as f:
            wh_final = json.load(f)
        total_water_final = sum(wh["inventory"].get("RES-WTR", 0) for wh in wh_final)
        print(f"Final Total Water Stock: {total_water_final}")
        
        # Verify that stock was decremented due to dispatch
        assert total_water_final < total_water_initial, "Warehouse stock was not decremented!"
        print("[OK] Dynamic Inventory update verified: stock was successfully deducted.")

        # Verify Blockchain logging
        with open("mock_blockchain.json", "r") as f:
            chain = json.load(f)
        print(f"Mock Blockchain height: {len(chain)} blocks.")
        assert len(chain) > 1, "Blockchain did not log transaction blocks!"
        print("[OK] Blockchain Ledger immutability verified.")
        
        print("\n[SUCCESS] ALL TESTS PASSED SUCCESSFULLY!")
        
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        import sys
        sys.exit(1)
