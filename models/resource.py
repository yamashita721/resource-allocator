from pydantic import BaseModel

class Resource(BaseModel):
    id: str
    name: str
    category: str  # "Immediate", "Short Term", "Recovery"
    weight_kg: float
