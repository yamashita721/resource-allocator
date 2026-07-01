import json
import random
import os
import pandas as pd
from typing import Dict, Any, List
from models.zone import ZoneState

# Bounding box for typhoon/disaster simulation (coastal Philippines area)
LAT_MIN, LAT_MAX = 13.0, 14.5
LON_MIN, LON_MAX = 120.0, 122.5

class WeatherAPIProvider:
    """Mock weather API with clean interface."""
    def get_weather_data(self, lat: float, lon: float, rain_modifier: float = 1.0) -> Dict[str, Any]:
        # Weather depends slightly on location and modifiers
        is_stormy = rain_modifier > 1.5
        is_rainy = rain_modifier > 1.0 or random.random() < 0.3
        
        if is_stormy:
            weather = "Storm"
            rainfall = random.uniform(60, 120) * rain_modifier
        elif is_rainy:
            weather = "Rainy"
            rainfall = random.uniform(15, 50) * rain_modifier
        else:
            weather = random.choice(["Clear", "Cloudy", "Clear", "Cloudy"])
            rainfall = 0.0
            
        return {
            "weather": weather,
            "rainfall_mm": round(rainfall, 2)
        }

class SatelliteAPIProvider:
    """Mock satellite imagery API for evaluating damages."""
    def get_damage_assessment(self, lat: float, lon: float, vulnerability: float) -> Dict[str, Any]:
        # Center of typhoon gets more damage (simulate a typhoon path passing diagonally)
        # Distance to center: (lat - 13.75)^2 + (lon - 121.25)^2
        dist_to_eye = ((lat - 13.75)**2 + (lon - 121.25)**2)**0.5
        severity_base = max(0, 100 - dist_to_eye * 80)
        
        # Add vulnerability influence and noise
        severity = severity_base + (vulnerability * 20) + random.uniform(-10, 10)
        severity = min(100.0, max(0.0, severity))
        
        return {
            "damage_severity_pct": round(severity, 2)
        }

class RoadStatusAPIProvider:
    """Mock road condition and network availability API."""
    def get_road_status(self, lat: float, lon: float, severity_pct: float, blocked_by_scenario: bool = False) -> Dict[str, Any]:
        if blocked_by_scenario or severity_pct > 85.0:
            return {"road_accessibility": 0.0, "blocked": True}
        
        # Accessibility decreases with severity
        accessibility = 1.0 - (severity_pct / 100.0) + random.uniform(-0.1, 0.1)
        accessibility = min(1.0, max(0.0, accessibility))
        return {
            "road_accessibility": round(accessibility, 2),
            "blocked": accessibility < 0.15
        }

class GovernmentDisasterFeedProvider:
    """Mock API for official disaster bulletins."""
    def get_feed(self, severity_pct: float) -> Dict[str, Any]:
        if severity_pct > 60.0:
            disaster_type = random.choice(["Flood", "Typhoon", "Typhoon"])
        elif severity_pct > 20.0:
            disaster_type = "Flash Flood"
        else:
            disaster_type = "None"
        return {
            "disaster_type": disaster_type,
            "severity_index": round(severity_pct / 10.0, 1)
        }

class SituationManager:
    """Orchestrates mock APIs to update the live situation layer of all zones."""
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.weather_provider = WeatherAPIProvider()
        self.satellite_provider = SatelliteAPIProvider()
        self.road_provider = RoadStatusAPIProvider()
        self.gov_provider = GovernmentDisasterFeedProvider()

    def refresh_situation(self, 
                          rain_modifier: float = 1.0, 
                          affected_pop_modifier: float = 1.0,
                          blocked_zones: List[str] = None) -> List[ZoneState]:
        """Queries mock APIs and refreshes state variables for all zones."""
        blocked_zones = blocked_zones or []
        
        zones_path = os.path.join(self.data_dir, "zones.csv")
        status_path = os.path.join(self.data_dir, "disaster_status.csv")
        
        if not os.path.exists(zones_path) or not os.path.exists(status_path):
            raise FileNotFoundError("Initial data files not found. Please run the data generator first.")
            
        zones_df = pd.read_csv(zones_path)
        status_df = pd.read_csv(status_path)
        
        # Ensure we have coordinates in zones_df (backward compatibility)
        if "latitude" not in zones_df.columns:
            # Generate stable coordinates based on seed + index
            random.seed(42)
            zones_df["latitude"] = [random.uniform(LAT_MIN, LAT_MAX) for _ in range(len(zones_df))]
            zones_df["longitude"] = [random.uniform(LON_MIN, LON_MAX) for _ in range(len(zones_df))]
            zones_df["shelter_capacity"] = [int(pop * random.uniform(0.05, 0.15)) for pop in zones_df["population"]]
            zones_df.to_csv(zones_path, index=False)
            
        merged = pd.merge(zones_df, status_df, on="zone_id", suffixes=('', '_old'))
        
        zone_states = []
        
        for _, row in merged.iterrows():
            zone_id = str(row["zone_id"])
            lat = float(row["latitude"])
            lon = float(row["longitude"])
            pop = int(row["population"])
            vuln = float(row["vulnerability_index"])
            crit_infra = int(row["critical_infrastructure_count"])
            shelter_cap = int(row["shelter_capacity"])
            
            # 1. Fetch satellite assessment
            sat_data = self.satellite_provider.get_damage_assessment(lat, lon, vuln)
            severity = sat_data["damage_severity_pct"]
            
            # 2. Fetch weather status
            weather_data = self.weather_provider.get_weather_data(lat, lon, rain_modifier)
            
            # 3. Fetch road status
            is_blocked = (zone_id in blocked_zones)
            road_data = self.road_provider.get_road_status(lat, lon, severity, is_blocked)
            
            # 4. Fetch disaster type from government feed
            gov_data = self.gov_provider.get_feed(severity)
            
            # Calculations
            affected_pop = int(pop * (severity / 100.0) * random.uniform(0.4, 0.8) * affected_pop_modifier)
            affected_pop = min(pop, max(0, affected_pop))
            
            shelter_occ = int(affected_pop * random.uniform(0.1, 0.3))
            shelter_occ = min(shelter_cap, shelter_occ)
            
            power_status = "Down" if severity > 40.0 or weather_data["weather"] == "Storm" else "Active"
            comm_status = "Down" if severity > 50.0 or (weather_data["weather"] == "Storm" and random.random() < 0.5) else "Active"
            
            # Retrieve or build inventories
            inv_dict = {}
            if "current_inventory" in row and pd.notna(row["current_inventory"]):
                try:
                    inv_dict = json.loads(row["current_inventory"])
                except Exception:
                    inv_dict = self._parse_inline_inventories(row, prefix="allocated_")
            else:
                inv_dict = self._parse_inline_inventories(row, prefix="allocated_")
                
            # If still empty, initialize with some base values
            if not inv_dict:
                inv_dict = {"RES-WTR": int(pop * 0.1), "RES-FOD": int(pop * 0.05), "RES-MED": int(pop * 0.01)}
                
            # Generate active requests based on shortage/needs
            req_dict = {}
            if "active_requests" in row and pd.notna(row["active_requests"]):
                try:
                    req_dict = json.loads(row["active_requests"])
                except Exception:
                    req_dict = self._generate_active_requests(affected_pop, severity, inv_dict)
            else:
                req_dict = self._generate_active_requests(affected_pop, severity, inv_dict)
                
            state = ZoneState(
                zone_id=zone_id,
                latitude=lat,
                longitude=lon,
                population=pop,
                vulnerability_index=vuln,
                critical_infrastructure_count=crit_infra,
                affected_population=affected_pop,
                disaster_type=gov_data["disaster_type"],
                severity=severity,
                weather=weather_data["weather"],
                rainfall=weather_data["rainfall_mm"],
                road_accessibility=road_data["road_accessibility"],
                shelter_capacity=shelter_cap,
                shelter_occupancy=shelter_occ,
                power_status=power_status,
                communication_status=comm_status,
                current_inventory=inv_dict,
                active_requests=req_dict
            )
            zone_states.append(state)
            
        self.save_zone_states(zone_states)
        return zone_states
        
    def _parse_inline_inventories(self, row: pd.Series, prefix: str) -> Dict[str, int]:
        inv = {}
        for col in row.index:
            if col.startswith(prefix):
                res_id = col.replace(prefix, "")
                inv[res_id] = int(row[col])
        return inv
        
    def _generate_active_requests(self, affected_pop: int, severity: float, inventory: Dict[str, int]) -> Dict[str, int]:
        # Generate resource needs
        req = {}
        # Simple demand heuristic
        water_needed = int(affected_pop * 3.0 * (severity / 50.0))
        food_needed = int(affected_pop * 1.5 * (severity / 50.0))
        med_needed = int(affected_pop * 0.2 * (severity / 50.0))
        tents_needed = int((affected_pop // 5) * (severity / 80.0))
        
        req["RES-WTR"] = max(0, water_needed - inventory.get("RES-WTR", 0))
        req["RES-FOD"] = max(0, food_needed - inventory.get("RES-FOD", 0))
        req["RES-MED"] = max(0, med_needed - inventory.get("RES-MED", 0))
        req["RES-TNT"] = max(0, tents_needed - inventory.get("RES-TNT", 0))
        
        return req
        
    def save_zone_states(self, states: List[ZoneState]):
        """Persists the live states back into the disaster status CSV."""
        zones_data = []
        status_data = []
        
        for s in states:
            zones_data.append({
                "zone_id": s.zone_id,
                "population": s.population,
                "vulnerability_index": s.vulnerability_index,
                "critical_infrastructure_count": s.critical_infrastructure_count,
                "latitude": s.latitude,
                "longitude": s.longitude,
                "shelter_capacity": s.shelter_capacity
            })
            
            # Map inventories to separate columns for backward compatibility if needed, 
            # and write the raw JSON strings as well.
            status_row = {
                "zone_id": s.zone_id,
                "days_since_onset": 1, # default placeholder
                "damage_severity_pct": s.severity,
                "displaced_people_est": s.shelter_occupancy, # Map shelter_occupancy to displaced
                "road_accessibility": s.road_accessibility,
                "affected_population": s.affected_population,
                "disaster_type": s.disaster_type,
                "weather": s.weather,
                "rainfall": s.rainfall,
                "shelter_occupancy": s.shelter_occupancy,
                "power_status": s.power_status,
                "communication_status": s.communication_status,
                "current_inventory": json.dumps(s.current_inventory),
                "active_requests": json.dumps(s.active_requests)
            }
            
            # Backward compatibility: populate allocated columns
            for res_id, qty in s.current_inventory.items():
                status_row[f"allocated_{res_id}"] = qty
                
            status_data.append(status_row)
            
        pd.DataFrame(zones_data).to_csv(os.path.join(self.data_dir, "zones.csv"), index=False)
        pd.DataFrame(status_data).to_csv(os.path.join(self.data_dir, "disaster_status.csv"), index=False)
