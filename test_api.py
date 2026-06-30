import threading
import time
import requests
import uvicorn
from api import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="critical")

if __name__ == "__main__":
    # Start the server in a separate thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Give the server a moment to start
    time.sleep(2)
    
    try:
        # Test 1: Health Check
        print("Testing Health Check...")
        r = requests.get("http://127.0.0.1:8001/")
        print(f"Status Code: {r.status_code}")
        print(f"Response: {r.json()}")
        
        # Test 2: Trigger Allocation
        print("\nTesting Allocation & Blockchain Logging...")
        r = requests.post("http://127.0.0.1:8001/allocate")
        print(f"Status Code: {r.status_code}")
        print(f"Response: {r.json()}")
        
    except Exception as e:
        print(f"Test failed: {e}")
