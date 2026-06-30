import hashlib
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from allocation_model import run_allocation
from blockchain_logger import log_allocation_hash

app = FastAPI(title="Transparent Predictive Relief Chain API")

class AllocationResponse(BaseModel):
    message: str
    file_path: str
    file_hash_sha256: str
    blockchain_receipt: dict

def generate_file_hash(filepath: str) -> str:
    """Generates a SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Relief Chain API is running."}

@app.post("/allocate", response_model=AllocationResponse)
def trigger_allocation():
    try:
        # 1. Run the ML allocation model
        output_csv_path = run_allocation()
        
        if not os.path.exists(output_csv_path):
            raise Exception("Allocation model failed to generate the CSV.")

        # 2. Hash the output CSV to create a unique cryptographic fingerprint
        file_hash = generate_file_hash(output_csv_path)

        # 3. Log the hash to the immutable blockchain
        receipt = log_allocation_hash(file_hash)

        return AllocationResponse(
            message="Allocation successful and logged to blockchain.",
            file_path=output_csv_path,
            file_hash_sha256=file_hash,
            blockchain_receipt=receipt
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
