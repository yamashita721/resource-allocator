import streamlit as st
import pandas as pd
import requests
import json
import os
import data_generator

st.set_page_config(page_title="Relief Chain PoC", layout="wide")

API_URL = "http://127.0.0.1:8000"
DATA_DIR = "data"
LEDGER_FILE = "mock_blockchain.json"

st.title("🌍 Transparent Predictive Relief Chain")
st.markdown("### AI-Optimized Allocation. Blockchain-Secured Accountability.")

# Sidebar Controls
with st.sidebar:
    st.header("🎛️ Control Center")
    
    st.subheader("1. Setup")
    if st.button("Regenerate Disaster Data"):
        with st.spinner("Simulating disaster zones..."):
            data_generator.generate_zones()
            data_generator.generate_disaster_status()
            data_generator.generate_resource_inventory()
            st.success("New synthetic data generated!")
            
    st.subheader("2. Action")
    if st.button("Run ML Allocation & Log to Chain", type="primary"):
        with st.spinner("Running optimization model & connecting to ledger..."):
            try:
                response = requests.post(f"{API_URL}/allocate")
                if response.status_code == 200:
                    data = response.json()
                    st.success("✅ Allocation Successful & Logged!")
                    st.info(f"**Transaction Hash:** `{data['blockchain_receipt']['transaction_hash']}`")
                else:
                    st.error(f"API Error: {response.text}")
            except requests.exceptions.ConnectionError:
                st.error("❌ Failed to connect to API. Is FastAPI running in another terminal? (`uvicorn api:app --reload`)")

# Main Content Layout
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📊 ML Allocation Plan (Top Priority Zones)")
    plan_path = os.path.join(DATA_DIR, "allocation_plan.csv")
    if os.path.exists(plan_path):
        df = pd.read_csv(plan_path)
        # Display top 10 rows
        st.dataframe(df.head(10), use_container_width=True)
        
        st.subheader("Resource Distribution Visualization")
        # Prepare data for bar chart
        chart_data = df.head(10).set_index("zone_id")[['allocated_RES-WTR', 'allocated_RES-FOD', 'allocated_RES-MED']]
        chart_data.columns = ['Water', 'Food', 'Medical']
        st.bar_chart(chart_data)
    else:
        st.warning("No allocation plan found. Run the ML model first.")

with col2:
    st.header("🔗 Blockchain Audit Log")
    st.markdown("Immutable ledger of all ML decisions.")
    
    if os.path.exists(LEDGER_FILE):
        with open(LEDGER_FILE, "r") as f:
            chain_data = json.load(f)
            
        # Display blocks in reverse chronological order
        for block in reversed(chain_data):
            with st.expander(f"Block #{block['index']} | Hash: {block['hash'][:10]}...", expanded=(block['index'] == chain_data[-1]['index'])):
                st.markdown(f"**Timestamp:** {block['timestamp']}")
                st.markdown(f"**Data (File Hash):** `{block['data']}`")
                st.markdown(f"**Previous Block:** `{block['previous_hash']}`")
                st.markdown(f"**Block Hash:** `{block['hash']}`")
    else:
        st.warning("No blockchain logs found.")
