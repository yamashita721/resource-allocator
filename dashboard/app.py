import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import os
import plotly.graph_objects as go
from data.situation import SituationManager
from simulation.scenarios import SimulationScenarioEngine
from blockchain.ledger import ReliefBlockchain
from typing import List, Dict, Any


API_URL = "http://127.0.0.1:8000"
DATA_DIR = "data"
LEDGER_FILE = "mock_blockchain.json"
SCENARIO_PATH = os.path.join(DATA_DIR, "active_scenario.json")

def main():
    st.set_page_config(page_title="Relief Chain Command Center", layout="wide")
    
    # Initialize Engine & Managers
    scenario_engine = SimulationScenarioEngine()
    sit_manager = SituationManager()
    
    st.title("🌍 Transparent Predictive Relief Chain")
    st.markdown("### AI-Optimized Allocation. Blockchain-Secured Accountability.")
    
    # Check if baseline data exists (useful for first-time deployments)
    data_ready = os.path.exists(os.path.join(DATA_DIR, "zones.csv"))
    
    # Load Current Scenario parameters
    curr_scenario = scenario_engine.get_active_scenario()
    
    # Sidebar Controls
    with st.sidebar:
        st.header("🎛️ Control Center")
        
        st.subheader("1. System Setup")
        if st.button("Regenerate Disaster Data", help="Resets and regenerates baseline zone, warehouse, and network data"):
            with st.spinner("Simulating baseline disaster zones..."):
                from data.generator import run_all
                run_all()
                scenario_engine.reset_scenarios()
                try:
                    sit_manager.refresh_situation()
                except Exception:
                    pass
                st.success("New baseline synthetic data generated!")
                st.rerun()
                
        if not data_ready:
            st.warning("⚠️ Initial data missing. Please generate data first.")
        else:
            st.subheader("2. Live Actions")
            if st.button("Run ML Allocation & Log to Chain", type="primary", help="Trigger ML Demand Forecasting, Fleet Routing, Inventory Updates, and ledger block logging"):
                with st.spinner("Running optimization pipeline..."):
                    try:
                        response = requests.post(f"{API_URL}/allocate")
                        if response.status_code == 200:
                            data = response.json()
                            st.success("✅ Allocation Completed & Logged!")
                            st.info(f"**Transaction Hash:** `{data['blockchain_receipt']['transaction_hash']}`")
                            st.rerun()
                        else:
                            st.error(f"API Error: {response.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("❌ Failed to connect to API. Is FastAPI running? Run: `uvicorn api:app --reload`")
                        
            st.subheader("3. Scenario Simulator")
            st.info("Simulate disaster severity parameters to instantly trigger routing changes.")
            
            # Rainfall slider
            rain_val = st.slider(
                "Rainfall Modifier", 
                min_value=1.0, 
                max_value=3.0, 
                value=float(curr_scenario.get("rain_modifier", 1.0)),
                step=0.1,
                help="Increases weather severity, disabling flight paths for Drones & Helicopters"
            )
            if rain_val != curr_scenario.get("rain_modifier", 1.0):
                scenario_engine.set_rainfall_modifier(rain_val)
                sit_manager.refresh_situation(rain_modifier=rain_val, affected_pop_modifier=curr_scenario.get("affected_population_modifier", 1.0))
                st.rerun()
                
            # Population factor
            pop_val = st.slider(
                "Affected Population Factor", 
                min_value=1.0, 
                max_value=2.5, 
                value=float(curr_scenario.get("affected_population_modifier", 1.0)),
                step=0.1,
                help="Multiplies displaced/affected numbers, scaling up required supply demands"
            )
            if pop_val != curr_scenario.get("affected_population_modifier", 1.0):
                scenario_engine.set_affected_population_modifier(pop_val)
                sit_manager.refresh_situation(rain_modifier=rain_val, affected_pop_modifier=pop_val)
                st.rerun()
                
            # Warehouse failures
            wh_options = ["WH-001", "WH-002", "WH-003", "WH-004", "WH-005"]
            failed_whs = st.multiselect(
                "Simulate Warehouse Failures",
                options=wh_options,
                default=curr_scenario.get("failed_warehouses", []),
                help="Offline depots cannot dispatch any resources"
            )
            if sorted(failed_whs) != sorted(curr_scenario.get("failed_warehouses", [])):
                for w in wh_options:
                    scenario_engine.toggle_warehouse_failure(w, w in failed_whs)
                st.rerun()
                
            # Disabled Vehicles
            vehicle_options = ["Truck", "Boat", "Helicopter", "Drone"]
            disabled_vehs = st.multiselect(
                "Simulate Fleet Breakdowns",
                options=vehicle_options,
                default=curr_scenario.get("disabled_vehicles", []),
                help="Disables specific vehicle types from the optimization fleet pool"
            )
            if sorted(disabled_vehs) != sorted(curr_scenario.get("disabled_vehicles", [])):
                for v in vehicle_options:
                    scenario_engine.toggle_vehicle_breakdown(v, v in disabled_vehs)
                st.rerun()
                
            # Blocked Roads
            zone_options = [f"Z-{str(i).zfill(3)}" for i in range(1, 101)]
            blocked_nodes = st.multiselect(
                "Simulate Road Blockages (Zones)",
                options=zone_options,
                default=curr_scenario.get("blocked_zones", []),
                help="Simulates structural damage, preventing Trucks from driving through these zones"
            )
            if sorted(blocked_nodes) != sorted(curr_scenario.get("blocked_zones", [])):
                for z in zone_options:
                    scenario_engine.toggle_road_blockage(z, z in blocked_nodes)
                sit_manager.refresh_situation(
                    rain_modifier=rain_val, 
                    affected_pop_modifier=pop_val,
                    blocked_zones=blocked_nodes
                )
                st.rerun()
                
            if st.button("Reset All Modifiers", help="Clears all scenario overrides"):
                scenario_engine.reset_scenarios()
                sit_manager.refresh_situation()
                st.success("Scenarios reset successfully!")
                st.rerun()

    if not data_ready:
        st.info("👋 **Welcome to the Transparent Predictive Relief Chain!**")
        st.warning("⚠️ **Initial disaster data is not generated yet.**")
        st.markdown(
            "To get started and initialize the application:\n"
            "1. Look at the **Control Center** in the sidebar on the left.\n"
            "2. Click the **'Regenerate Disaster Data'** button.\n"
            "3. Once the baseline data is simulated, the full dashboard will appear!"
        )
        return
        
    # Load Zones and Warehouses state for dashboard components
    zones_df = pd.read_csv(os.path.join(DATA_DIR, "zones.csv"))
    status_df = pd.read_csv(os.path.join(DATA_DIR, "disaster_status.csv"))
    merged_data = pd.merge(zones_df, status_df, on="zone_id")
    
    with open(os.path.join(DATA_DIR, "warehouses.json"), "r") as f:
        warehouses = json.load(f)
        
    with open(os.path.join(DATA_DIR, "resources.json"), "r") as f:
        catalog = json.load(f)["resources"]
        
    blockchain = ReliefBlockchain()
    
    # ------------------ KPI Metrics Ribbon ------------------
    tot_pop_affected = merged_data["affected_population"].sum()
    
    # Active requests sum
    total_req_count = 0
    for idx, row in merged_data.iterrows():
        try:
            req_dict = json.loads(row["active_requests"])
            total_req_count += sum(req_dict.values())
        except Exception:
            pass
            
    active_whs = sum(1 for w in warehouses if w["availability"] and w["warehouse_id"] not in curr_scenario.get("failed_warehouses", []))
    ledger_blocks = len(blockchain.chain)
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric(label="👥 Displaced & Affected Population", value=f"{tot_pop_affected:,}")
    with col_m2:
        st.metric(label="📦 Total Active Requests (Units)", value=f"{total_req_count:,}")
    with col_m3:
        st.metric(label="🏪 Logistics Warehouses Online", value=f"{active_whs} / {len(warehouses)}")
    with col_m4:
        st.metric(label="🔗 Immutable Blockchain Blocks", value=f"{ledger_blocks}")
        
    # ------------------ Interactive Map ------------------
    st.header("📍 Live Logistics Command Map")
    
    # Extract recent dispatches from the latest block to draw paths
    dispatches_to_draw = []
    if len(blockchain.chain) > 1:
        latest_block = blockchain.chain[-1]
        # Check if the block data is a dispatch batch
        block_data = latest_block["data"]
        # If it is a dictionary (newer block format)
        if isinstance(block_data, dict) and "warehouse_id" in block_data:
            dispatches_to_draw.append(block_data)
        # Scan recent blocks for dispatches
        for b in reversed(blockchain.chain[1:]):
            bd = b["data"]
            if isinstance(bd, dict) and "warehouse_id" in bd:
                # Add to draw list
                dispatches_to_draw.append(bd)
                # Keep drawing limit
                if len(dispatches_to_draw) >= 15:
                    break
                    
    # Generate Mapbox Plotly figure
    fig = go.Figure()
    
    # 1. Road lines (base network)
    with open(os.path.join(DATA_DIR, "road_network.json"), "r") as f:
        network = json.load(f)
        
    # Draw roads
    nodes_dict = {n["id"]: n for n in network["nodes"]}
    for edge in network["edges"]:
        from_n = nodes_dict[edge["from_node"]]
        to_n = nodes_dict[edge["to_node"]]
        
        # Check if road is blocked in scenario
        is_blocked = (edge["from_node"] in curr_scenario.get("blocked_zones", []) or 
                      edge["to_node"] in curr_scenario.get("blocked_zones", []))
                      
        fig.add_trace(go.Scattermapbox(
            lat=[from_n["latitude"], to_n["latitude"]],
            lon=[from_n["longitude"], to_n["longitude"]],
            mode="lines",
            line=dict(width=1.5, color="red" if is_blocked else "rgba(100, 100, 100, 0.4)"),
            hoverinfo="none",
            showlegend=False
        ))
        
    # 2. Draw Dispatch Routes (Active deliveries)
    drawn_coords = set()
    for d in dispatches_to_draw:
        zone_id = d.get("gps", {})
        # Find zone lat/lon
        zone_row = zones_df[zones_df["zone_id"] == d.get("allocation_hash", "")] # wait, allocation_hash or check fields
        # Better: let's match zone from dispatches structure
        # Since block_data has: allocation_hash, warehouse_id, vehicle_type, handler, gps, timestamp, resource, quantity
        # and gps: {"latitude": float, "longitude": float}
        wh_id = d.get("warehouse_id")
        wh_row = next((w for w in warehouses if w["warehouse_id"] == wh_id), None)
        
        dest_gps = d.get("gps", {})
        dest_lat = dest_gps.get("latitude")
        dest_lon = dest_gps.get("longitude")
        
        if wh_row and dest_lat and dest_lon:
            # Draw line from warehouse to zone
            pair = (wh_row["latitude"], wh_row["longitude"], dest_lat, dest_lon)
            if pair not in drawn_coords:
                drawn_coords.add(pair)
                fig.add_trace(go.Scattermapbox(
                    lat=[wh_row["latitude"], dest_lat],
                    lon=[wh_row["longitude"], dest_lon],
                    mode="lines+markers",
                    line=dict(width=3, color="orange"),
                    marker=dict(size=6, color="orange"),
                    hovertext=f"Vehicle: {d.get('vehicle_type')} | Delivering: {d.get('resource')} (Qty: {d.get('quantity')})",
                    hoverinfo="text",
                    name="Active Dispatches",
                    showlegend=(len(drawn_coords) == 1)
                ))

    # 3. Add zones colored by severity/priority
    # Calculate priority index on the fly or load it
    from ml.allocation import calculate_priority
    merged_with_priority = calculate_priority(merged_data.copy())
    
    fig.add_trace(go.Scattermapbox(
        lat=merged_with_priority["latitude"],
        lon=merged_with_priority["longitude"],
        mode="markers",
        marker=go.scattermapbox.Marker(
            size=9,
            color=merged_with_priority["priority_score"],
            colorscale="YlOrRd",
            showscale=True,
            colorbar=dict(
                title=dict(text="Priority Score", font=dict(color="white")),
                tickfont=dict(color="white"),
                x=1.02
            )
        ),
        text=merged_with_priority.apply(
            lambda r: f"<b>Zone:</b> {r['zone_id']}<br>"
                      f"<b>Population:</b> {r['population']:,}<br>"
                      f"<b>Affected:</b> {r['affected_population']:,}<br>"
                      f"<b>Priority:</b> {r['priority_score']}<br>"
                      f"<b>Weather:</b> {r['weather']} ({r['rainfall']} mm)<br>"
                      f"<b>Road Access:</b> {r['road_accessibility']}", 
            axis=1
        ),
        hoverinfo="text",
        name="Disaster Zones"
    ))
    
    # 4. Add warehouses
    wh_lats = []
    wh_lons = []
    wh_texts = []
    wh_colors = []
    
    for wh in warehouses:
        is_failed = wh["warehouse_id"] in curr_scenario.get("failed_warehouses", [])
        wh_lats.append(wh["latitude"])
        wh_lons.append(wh["longitude"])
        
        # Build inventory detail text
        inv_str = "<br>".join([f" - {res}: {qty:,}" for res, qty in wh["inventory"].items() if qty > 0])
        status_txt = "<font color='red'><b>OFFLINE (Failure Sim)</b></font>" if is_failed else "<font color='green'>ONLINE</font>"
        
        wh_texts.append(
            f"<b>Warehouse:</b> {wh['location']} ({wh['warehouse_id']})<br>"
            f"<b>Status:</b> {status_txt}<br>"
            f"<b>Inventory:</b><br>{inv_str}"
        )
        wh_colors.append("red" if is_failed else "cyan")
        
    fig.add_trace(go.Scattermapbox(
        lat=wh_lats,
        lon=wh_lons,
        mode="markers+text",
        marker=go.scattermapbox.Marker(
            size=15,
            color=wh_colors,
            symbol="square"
        ),
        text=[w["warehouse_id"] for w in warehouses],
        textposition="top center",
        textfont=dict(color="white", size=10, family="sans-serif"),
        hovertext=wh_texts,
        hoverinfo="text",
        name="Warehouses"
    ))
    
    # Map Layout settings
    fig.update_layout(
        mapbox=dict(
            style="carto-darkmatter",
            zoom=8,
            center=dict(lat=13.75, lon=121.3)
        ),
        margin=dict(r=0, l=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
        legend=dict(
            font=dict(color="white"),
            bgcolor="rgba(0,0,0,0.5)",
            x=0.01,
            y=0.99
        )
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # ------------------ Main Layout Columns ------------------
    col1, col2 = st.columns([2, 1])
    
    # ------------------ Column 1: ML Allocation Plan & Analysis ------------------
    with col1:
        st.header("📊 ML Allocation Plan (Top Priority Zones)")
        plan_path = os.path.join(DATA_DIR, "allocation_plan.csv")
        
        if os.path.exists(plan_path):
            df = pd.read_csv(plan_path)
            # Display plan
            st.dataframe(df.head(10), use_container_width=True)
            
            st.subheader("Resource Distribution Visualization")
            chart_data = df.head(10).set_index("zone_id")[['allocated_RES-WTR', 'allocated_RES-FOD', 'allocated_RES-MED']]
            chart_data.columns = ['Water', 'Food', 'Medical']
            st.bar_chart(chart_data)
        else:
            st.warning("No allocation plan found. Run the ML model first.")
            
        # Extension: Predicted Shortages Center
        st.subheader("⚠️ Predicted Shortages & Resource Depletion Forecast")
        st.markdown("ML-predicted shortage risks within the next 48 hours:")
        
        # Load prediction status
        @st.cache_resource
        def get_predictor():
            from ml.demand_predictor import DemandPredictor
            return DemandPredictor()
            
        predictor = get_predictor()
        
        shortages_rows = []
        for idx, row in merged_with_priority.iterrows():
            inv = json.loads(row["current_inventory"])
            preds_res = predictor.predict_zone_demands(
                population=int(row["population"]),
                vulnerability=float(row["vulnerability_index"]),
                severity=float(row["damage_severity_pct"]),
                days_since_onset=int(row["days_since_onset"]),
                weather=str(row["weather"]),
                rainfall=float(row["rainfall"]),
                shelter_occupancy=int(row["shelter_occupancy"]),
                historical_disasters=int(row["critical_infrastructure_count"] // 2),
                current_inventory=inv
            )
            
            probs = preds_res["shortage_probability"]
            depl = preds_res["depletion_hours"]
            preds = preds_res["predictions"]
            
            # Find any critical shortage
            for res_id in ["RES-WTR", "RES-FOD", "RES-MED", "RES-TNT"]:
                prob = probs.get(res_id, 0.0)
                depletion = depl.get(res_id, 120.0)
                
                if prob > 0.4:
                    shortages_rows.append({
                        "Zone": row["zone_id"],
                        "Resource": catalog_name(res_id, catalog),
                        "Current Stock": inv.get(res_id, 0),
                        "48H Predicted Need": preds.get(res_id, 0),
                        "Time to Depletion": f"{depletion} Hours",
                        "Shortage Risk": f"{int(prob * 100)}%"
                    })
                    
        if shortages_rows:
            st.dataframe(pd.DataFrame(shortages_rows), use_container_width=True)
        else:
            st.success("No critical resource shortages predicted in the next 48 hours.")
            
    # ------------------ Column 2: Blockchain Explorer & Warehouses ------------------
    with col2:
        st.header("🔗 Blockchain Audit Log")
        st.markdown("Immutable ledger tracking all logistics dispatches.")
        
        if os.path.exists(LEDGER_FILE):
            with open(LEDGER_FILE, "r") as f:
                chain_data = json.load(f)
                
            # Expanders showing blocks in reverse order
            for block in reversed(chain_data):
                b_data = block["data"]
                
                # Check formatting
                if isinstance(b_data, dict):
                    title = f"Block #{block['index']} | Dispatch: {b_data.get('warehouse_id')} ➡️ {b_data.get('gps', {}).get('latitude')}, {b_data.get('gps', {}).get('longitude')}"
                    exp_content = f"""
                    * **Timestamp:** {block['timestamp']}
                    * **Previous Hash:** `{block['previous_hash']}`
                    * **Block Hash:** `{block['hash']}`
                    * **Dispatch Details:**
                      * **Allocation CSV Fingerprint:** `{b_data.get('allocation_hash')}`
                      * **From Warehouse:** `{b_data.get('warehouse_id')}`
                      * **Vehicle / Fleet:** `{b_data.get('vehicle_type')}`
                      * **Logistics Handler:** `{b_data.get('handler')}`
                      * **Delivered Supply:** `{b_data.get('resource')} ({b_data.get('quantity')} Units)`
                    """
                else:
                    title = f"Block #{block['index']} | Genesis / Audit Hash"
                    exp_content = f"""
                    * **Timestamp:** {block['timestamp']}
                    * **Data/File Hash:** `{block['data']}`
                    * **Previous Hash:** `{block['previous_hash']}`
                    * **Block Hash:** `{block['hash']}`
                    """
                    
                with st.expander(title, expanded=(block['index'] == chain_data[-1]['index'])):
                    st.markdown(exp_content)
        else:
            st.warning("No blockchain logs found.")
            
        # Dynamic Warehouse Inventories
        st.subheader("📦 Warehouse Inventory Status")
        st.markdown("Current stock levels at storage depots:")
        
        for wh in warehouses:
            is_failed = wh["warehouse_id"] in curr_scenario.get("failed_warehouses", [])
            status_symbol = "🔴" if is_failed else "🟢"
            status_text = "FAILED" if is_failed else "Active"
            
            with st.container():
                st.markdown(f"**{status_symbol} {wh['location']} ({wh['warehouse_id']})** - Status: *{status_text}*")
                # Grid of resources
                res_cols = st.columns(3)
                idx = 0
                for r_id, r_qty in wh["inventory"].items():
                    name = catalog_name(r_id, catalog)
                    res_cols[idx % 3].metric(label=name, value=f"{r_qty:,}")
                    idx += 1
                st.divider()

def catalog_name(res_id: str, catalog: List[Dict[str, Any]]) -> str:
    item = next((i for i in catalog if i["id"] == res_id), None)
    return item["name"] if item else res_id

if __name__ == "__main__":
    main()
