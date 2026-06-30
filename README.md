# 🌍 Transparent Predictive Relief Chain

An AI-driven, Blockchain-secured Proof of Concept (PoC) for managing disaster relief resources efficiently and transparently.

## 📖 How It Works (The Non-Technical Workflow)

Imagine a massive earthquake just hit a region with 100 different neighborhoods. Chaos ensues, and a central warehouse has limited water, food, and medicine. Who gets what, and how do we prove it wasn't stolen?

Here is how this system solves that:

**1. The Crisis (Data Ingestion)**
* *What happens:* We gather data. We know the historical poverty/vulnerability of each neighborhood (Static Data). We simulate satellite drones flying over to assess the exact percentage of destroyed buildings and blocked roads (Dynamic Data).

**2. The Brain (Machine Learning)**
* *What happens:* Humans panic; algorithms don't. The AI looks at the data and mathematically calculates a "Priority Score" for every single neighborhood. It realizes that a poor neighborhood with 80% destruction and blocked roads needs helicopters with medical supplies *today*, whereas a wealthy neighborhood with 20% destruction can wait until tomorrow. 
* *Result:* The AI generates a perfect, unbiased **Allocation Plan** (a spreadsheet of exactly where every bottle of water should go).

**3. The Vault (Blockchain Logging)**
* *What happens:* How do we know a corrupt official won't alter the AI's spreadsheet to send food to their own neighborhood? We take the AI's Allocation Plan and generate a **Cryptographic Fingerprint (Hash)** of the file. We permanently lock this fingerprint into a Blockchain Ledger. 
* *Result:* The record is now immutable. It cannot be deleted, edited, or hacked. 

**4. The Proof (Audit Trail)**
* *What happens:* Days later, auditors (or the public via the Streamlit Dashboard) can look at the Blockchain Ledger. If the physical trucks delivered food to the wrong place, the auditors can compare the final delivery report to the immutable Blockchain fingerprint. If they don't match, the corruption is instantly mathematically proven.

---

## 💻 Tech Stack
* **Intelligence:** Python, Pandas, Scikit-learn (Optimization Logic)
* **Bridge:** FastAPI (Backend API Orchestrator)
* **Ledger:** Pure Python Blockchain Simulation (Immutability & Hashing)
* **Showcase:** Streamlit (Interactive UI)

## 🚀 How to Run Locally

You will need two terminals to run this application.

**Terminal 1: Start the Backend API**
```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1
# Run the API
uvicorn api:app --reload
```

**Terminal 2: Start the Frontend UI**
```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1
# Run the UI
python -m streamlit run app.py
```
