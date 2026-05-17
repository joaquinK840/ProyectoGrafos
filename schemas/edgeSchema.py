from pydantic import BaseModel, Field

class EdgePayload(BaseModel):
    vertex1: str
    vertex2: str
    distance: int = 0
    time: int = 0
    cost: int = 0
