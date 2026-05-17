from pydantic import BaseModel, Field
from schemas.edgeSchema import EdgePayload

class GraphPayload(BaseModel):
    directed: bool = True
    vertices: list[str]
    edges: list[EdgePayload] = Field(default_factory=list)
