import os
import time
from simulation.scenarios import SimulationScenarioEngine, SCENARIO_PATH

def test_scenario_persistence():
    print("Testing SimulationScenarioEngine persistence...")
    if os.path.exists(SCENARIO_PATH):
        os.remove(SCENARIO_PATH)
        
    engine1 = SimulationScenarioEngine()
    engine1.set_rainfall_modifier(2.5)
    
    assert engine1.get_active_scenario()["rain_modifier"] == 2.5
    
    # Simulate a Streamlit rerun by instantiating again
    engine2 = SimulationScenarioEngine()
    
    val = engine2.get_active_scenario()["rain_modifier"]
    assert val == 2.5, f"Scenario state was reset! Expected 2.5, got {val}"
    
    print("[OK] SimulationScenarioEngine preserves state across instantiations.")

def test_demand_predictor_initialization():
    print("Testing DemandPredictor initialization...")
    from ml.demand_predictor import DemandPredictor
    
    start_time = time.time()
    dp1 = DemandPredictor()
    first_load = time.time() - start_time
    print(f"First initialization took {first_load:.4f}s")
    
    assert dp1 is not None, "DemandPredictor failed to initialize"
    print("[OK] DemandPredictor initialized successfully.")

if __name__ == "__main__":
    try:
        test_scenario_persistence()
        test_demand_predictor_initialization()
        print("\n[SUCCESS] Caching and logic test suite passed.")
    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        import sys
        sys.exit(1)
