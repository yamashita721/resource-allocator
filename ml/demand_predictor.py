import os
import pickle
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple

DATA_DIR = "data"
MODEL_PATH = os.path.join(DATA_DIR, "demand_model.pkl")

# Mapping of weather strings to numerical values
WEATHER_MAP = {"Clear": 0, "Cloudy": 1, "Rainy": 2, "Storm": 3}

class DemandPredictor:
    def __init__(self, data_dir: str = DATA_DIR):
        self.data_dir = data_dir
        self.model = None
        self.sklearn_available = False
        
        # Test if scikit-learn is available
        try:
            from sklearn.ensemble import RandomForestRegressor
            self.sklearn_available = True
        except ImportError:
            self.sklearn_available = False
            
        self.initialize_model()

    def generate_training_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Generates synthetic historical disaster demand records for training."""
        np.random.seed(42)
        n_samples = 1500
        
        pop = np.random.randint(5000, 100000, size=n_samples)
        vuln = np.random.uniform(0.1, 0.9, size=n_samples)
        sev = np.random.uniform(10, 100, size=n_samples)
        days = np.random.randint(1, 10, size=n_samples)
        weather = np.random.choice([0, 1, 2, 3], size=n_samples) # Clear, Cloudy, Rainy, Storm
        rainfall = np.where(weather == 3, np.random.uniform(50, 100, size=n_samples),
                            np.where(weather == 2, np.random.uniform(10, 45, size=n_samples), 0.0))
        shelter_occ = (pop * (sev / 100.0) * np.random.uniform(0.05, 0.25, size=n_samples)).astype(int)
        history = np.random.randint(0, 6, size=n_samples)
        curr_inv = (pop * 0.02 * np.random.uniform(0.5, 1.5, size=n_samples)).astype(int)
        
        # Features DataFrame
        X = pd.DataFrame({
            "population": pop,
            "vulnerability_index": vuln,
            "severity": sev,
            "days_since_onset": days,
            "weather_numeric": weather,
            "rainfall": rainfall,
            "shelter_occupancy": shelter_occ,
            "historical_disasters": history,
            "current_inventory": curr_inv
        })
        
        # Targets: Demands for different categories of resources (Immediate, Short Term, Recovery)
        # Immediate (Water, Food, Meds)
        demand_water = pop * 3.0 * (sev / 100.0) + (shelter_occ * 1.5) - (curr_inv * 0.1)
        demand_water = np.clip(demand_water, 1000, None) + np.random.normal(0, 500, size=n_samples)
        
        # Short Term (Tents, Hygiene Kits)
        demand_tents = (shelter_occ / 4.0) * (1.0 + vuln * 0.5) + np.where(weather >= 2, 200, 0)
        demand_tents = np.clip(demand_tents, 50, None) + np.random.normal(0, 20, size=n_samples)
        
        # Recovery (Construction Materials)
        demand_const = pop * 0.05 * (sev / 100.0) * (vuln) * (10 / (days + 1))
        demand_const = np.clip(demand_const, 0, None) + np.random.normal(0, 10, size=n_samples)
        
        y = pd.DataFrame({
            "demand_water": demand_water.round(0),
            "demand_tents": demand_tents.round(0),
            "demand_const": demand_const.round(0)
        })
        
        return X, y

    def initialize_model(self):
        if not self.sklearn_available:
            print("scikit-learn not available. Using heuristic demand formulas as a backup predictor.")
            return
            
        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, "rb") as f:
                    self.model = pickle.load(f)
                return
            except Exception as e:
                print(f"Error loading saved ML model: {e}. Re-training model...")
                
        # Train new model
        try:
            from sklearn.ensemble import RandomForestRegressor
            X, y = self.generate_training_data()
            print("Training scikit-learn RandomForestRegressor demand model...")
            self.model = RandomForestRegressor(n_estimators=50, random_state=42)
            self.model.fit(X, y)
            
            with open(MODEL_PATH, "wb") as f:
                pickle.dump(self.model, f)
            print(f"Model saved to {MODEL_PATH}")
        except Exception as e:
            print(f"Failed to train scikit-learn model: {e}. Reverting to heuristic demand predictor.")
            self.model = None

    def predict_zone_demands(
        self,
        population: int,
        vulnerability: float,
        severity: float,
        days_since_onset: int,
        weather: str,
        rainfall: float,
        shelter_occupancy: int,
        historical_disasters: int,
        current_inventory: Dict[str, int]
    ) -> Dict[str, Any]:
        """
        Predicts demand for:
        - Water (Immediate category)
        - Tents (Short Term category)
        - Construction Materials (Recovery category)
        And estimates shortage probabilities and resource depletion timelines.
        """
        weather_numeric = WEATHER_MAP.get(weather, 1)
        tot_inv_qty = sum(current_inventory.values())
        
        # 1. Prediction logic (ML or Heuristic fallback)
        if self.sklearn_available and self.model is not None:
            features = pd.DataFrame([{
                "population": population,
                "vulnerability_index": vulnerability,
                "severity": severity,
                "days_since_onset": days_since_onset,
                "weather_numeric": weather_numeric,
                "rainfall": rainfall,
                "shelter_occupancy": shelter_occupancy,
                "historical_disasters": historical_disasters,
                "current_inventory": tot_inv_qty
            }])
            
            preds = self.model.predict(features)[0]
            pred_water = max(0.0, float(preds[0]))
            pred_tents = max(0.0, float(preds[1]))
            pred_const = max(0.0, float(preds[2]))
        else:
            # Heuristic demand estimation
            # Water demand
            w_factor = 3.0 * (severity / 100.0) + (weather_numeric * 0.2)
            pred_water = max(0.0, population * w_factor + (shelter_occupancy * 1.5) - (tot_inv_qty * 0.05))
            
            # Tents demand
            t_factor = 0.25 * (1.0 + vulnerability * 0.5)
            pred_tents = max(0.0, shelter_occupancy * t_factor + (50 if weather_numeric >= 2 else 0))
            
            # Construction materials demand
            c_factor = 0.04 * (severity / 100.0) * vulnerability * (8 / (days_since_onset + 1))
            pred_const = max(0.0, population * c_factor)

        # Scale predictions to represent a list of resource demands
        # Immediate resources
        water_req = int(pred_water)
        food_req = int(pred_water * 0.5)
        med_req = int(pred_water * 0.05)
        
        # Short Term resources
        tents_req = int(pred_tents)
        toilets_req = int(pred_tents * 0.3)
        gen_req = int(pred_tents * 0.1)
        
        # Recovery resources
        const_req = int(pred_const)
        roof_req = int(pred_const * 2.0)
        school_req = int(pred_const * 0.1)
        
        predictions = {
            "RES-WTR": water_req, "RES-FOD": food_req, "RES-MED": med_req,
            "RES-TNT": tents_req, "RES-TLT": toilets_req, "RES-GEN": gen_req,
            "RES-CMT": const_req, "RES-RFS": roof_req, "RES-SCH": school_req
        }
        
        # Calculate Depletion Time & Shortage Probability
        depletion_hours = {}
        shortage_prob = {}
        
        for res_id, req_qty in predictions.items():
            inv = current_inventory.get(res_id, 0)
            if req_qty <= 0:
                depletion_hours[res_id] = 120.0 # Standard safety duration (e.g. 5 days)
                shortage_prob[res_id] = 0.0
            else:
                # Time to deplete = inventory / hourly_rate (assume req_qty is needed over 48 hours)
                hourly_rate = req_qty / 48.0
                depletion = inv / hourly_rate
                depletion_hours[res_id] = round(min(120.0, depletion), 1)
                
                # Shortage probability
                prob = (req_qty - inv) / (req_qty * 1.2 + 1)
                shortage_prob[res_id] = round(max(0.0, min(1.0, prob)), 2)
                
        return {
            "predictions": predictions,
            "depletion_hours": depletion_hours,
            "shortage_probability": shortage_prob
        }
