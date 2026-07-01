import hashlib
import json
import time
import os
from typing import List, Dict, Any

LEDGER_FILE = "mock_blockchain.json"

class ReliefBlockchain:
    def __init__(self, ledger_file: str = LEDGER_FILE):
        self.ledger_file = ledger_file
        self.chain = []
        self.load_chain()
        if len(self.chain) == 0:
            self.create_genesis_block()

    def load_chain(self):
        if os.path.exists(self.ledger_file):
            try:
                with open(self.ledger_file, "r") as f:
                    self.chain = json.load(f)
            except Exception:
                self.chain = []

    def save_chain(self):
        with open(self.ledger_file, "w") as f:
            json.dump(self.chain, f, indent=4)

    def create_genesis_block(self):
        genesis_block = {
            "index": 0,
            "timestamp": time.time(),
            "data": "Genesis Block - Relief Chain Initiated",
            "previous_hash": "0",
            "hash": self.hash_block(0, time.time(), "Genesis Block - Relief Chain Initiated", "0")
        }
        self.chain.append(genesis_block)
        self.save_chain()

    def hash_block(self, index: int, timestamp: float, data: Any, previous_hash: str) -> str:
        # Serialize data cleanly to keep deterministic hashing
        data_str = json.dumps(data, sort_keys=True)
        block_string = f"{index}{timestamp}{data_str}{previous_hash}".encode()
        return hashlib.sha256(block_string).hexdigest()

    def log_data(self, data: Any) -> Dict[str, Any]:
        """Logs a single block on the chain."""
        last_block = self.chain[-1]
        new_index = last_block["index"] + 1
        new_timestamp = time.time()
        new_prev_hash = last_block["hash"]
        new_hash = self.hash_block(new_index, new_timestamp, data, new_prev_hash)

        new_block = {
            "index": new_index,
            "timestamp": new_timestamp,
            "data": data,
            "previous_hash": new_prev_hash,
            "hash": new_hash
        }
        
        self.chain.append(new_block)
        self.save_chain()
        return new_block

    def log_dispatch_batch(self, allocation_hash: str, dispatches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Logs a series of dispatches to the blockchain."""
        receipts = []
        
        # If there are no dispatches, we log the allocation hash alone to register the run
        if not dispatches:
            block = self.log_data(allocation_hash)
            receipts.append(block)
            return receipts
            
        for d in dispatches:
            # Structuring the audit data
            audit_entry = {
                "allocation_hash": allocation_hash,
                "warehouse_id": d["warehouse_id"],
                "vehicle_type": d["vehicle_type"],
                "handler": d["handler"],
                "gps": d["gps"],
                "timestamp": d["timestamp"],
                "resource": d["resource"],
                "quantity": d["quantity"]
            }
            block = self.log_data(audit_entry)
            receipts.append(block)
            
        return receipts

# Initialize single global ledger instance
ledger = ReliefBlockchain()

def log_allocation_hash(file_hash: str):
    """Backward compatible wrapper function."""
    block = ledger.log_data(file_hash)
    return {
        "transaction_hash": block["hash"],
        "block_number": block["index"],
        "timestamp": block["timestamp"]
    }
