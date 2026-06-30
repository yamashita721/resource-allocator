import hashlib
import json
import time
import os

LEDGER_FILE = "mock_blockchain.json"

class ReliefBlockchain:
    def __init__(self):
        self.chain = []
        self.load_chain()
        if len(self.chain) == 0:
            self.create_genesis_block()

    def load_chain(self):
        if os.path.exists(LEDGER_FILE):
            with open(LEDGER_FILE, "r") as f:
                self.chain = json.load(f)

    def save_chain(self):
        with open(LEDGER_FILE, "w") as f:
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

    def hash_block(self, index, timestamp, data, previous_hash):
        block_string = f"{index}{timestamp}{data}{previous_hash}".encode()
        return hashlib.sha256(block_string).hexdigest()

    def log_data(self, data: str):
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

# Initialize our ledger
ledger = ReliefBlockchain()

def log_allocation_hash(file_hash: str):
    """
    Logs the hash of our allocation plan into our pure-Python Blockchain.
    This guarantees that if the plan is tampered with, the file_hash won't match the ledger.
    """
    block = ledger.log_data(file_hash)
    return {
        "transaction_hash": block["hash"],
        "block_number": block["index"],
        "timestamp": block["timestamp"]
    }

if __name__ == "__main__":
    dummy_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    receipt = log_allocation_hash(dummy_hash)
    print(f"Logged in Block: {receipt['block_number']}")
    print(f"Transaction Hash: {receipt['transaction_hash']}")
