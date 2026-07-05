import os
import json
from typing import Dict, Any, List

DATA_DIR = "data"
SCENARIO_PATH = os.path.join(DATA_DIR, "active_scenario.json")

class SimulationScenarioEngine:
    def __init__(self, data_dir: str = DATA_DIR):
        self.data_dir = data_dir
        if not os.path.exists(SCENARIO_PATH):
            self.reset_scenarios()

    def get_active_scenario(self) -> Dict[str, Any]:
        if os.path.exists(SCENARIO_PATH):
            try:
                with open(SCENARIO_PATH, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return self._get_default_scenario()

    def _get_default_scenario(self) -> Dict[str, Any]:
        return {
            "failed_warehouses": [],
            "blocked_zones": [],
            "disabled_vehicles": [],
            "rain_modifier": 1.0,
            "affected_population_modifier": 1.0
        }

    def save_scenario(self, scenario: Dict[str, Any]):
        with open(SCENARIO_PATH, "w") as f:
            json.dump(scenario, f, indent=4)

    def set_rainfall_modifier(self, modifier: float):
        scenario = self.get_active_scenario()
        scenario["rain_modifier"] = modifier
        self.save_scenario(scenario)

    def set_affected_population_modifier(self, modifier: float):
        scenario = self.get_active_scenario()
        scenario["affected_population_modifier"] = modifier
        self.save_scenario(scenario)

    def toggle_warehouse_failure(self, warehouse_id: str, failed: bool):
        scenario = self.get_active_scenario()
        failed_list = scenario.get("failed_warehouses", [])
        if failed and warehouse_id not in failed_list:
            failed_list.append(warehouse_id)
        elif not failed and warehouse_id in failed_list:
            failed_list.remove(warehouse_id)
        scenario["failed_warehouses"] = failed_list
        self.save_scenario(scenario)

    def toggle_road_blockage(self, zone_id: str, blocked: bool):
        scenario = self.get_active_scenario()
        blocked_list = scenario.get("blocked_zones", [])
        if blocked and zone_id not in blocked_list:
            blocked_list.append(zone_id)
        elif not blocked and zone_id in blocked_list:
            blocked_list.remove(zone_id)
        scenario["blocked_zones"] = blocked_list
        self.save_scenario(scenario)

    def toggle_vehicle_breakdown(self, vehicle_name: str, disabled: bool):
        scenario = self.get_active_scenario()
        disabled_list = scenario.get("disabled_vehicles", [])
        if disabled and vehicle_name not in disabled_list:
            disabled_list.append(vehicle_name)
        elif not disabled and vehicle_name in disabled_list:
            disabled_list.remove(vehicle_name)
        scenario["disabled_vehicles"] = disabled_list
        self.save_scenario(scenario)

    def reset_scenarios(self):
        self.save_scenario(self._get_default_scenario())
