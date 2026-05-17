from pydantic import BaseModel, Field

class VertexPayload(BaseModel):
    name: str
