from blockchain.ledger import log_allocation_hash, ledger

if __name__ == "__main__":
    dummy_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    receipt = log_allocation_hash(dummy_hash)
    print(f"Logged in Block: {receipt['block_number']}")
    print(f"Transaction Hash: {receipt['transaction_hash']}")
