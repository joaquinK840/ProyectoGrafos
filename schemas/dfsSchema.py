from pydantic import BaseModel


class DFSPayload(BaseModel):
    start_vertex: str
    max_weight: int
    filters: list[int]


class DFSFilterResponse(BaseModel):
    filter_id: int
    filter_name: str
    visited_vertices: list[str]
    total_count: int


class DFSMultiResponse(BaseModel):
    start_vertex: str
    max_weight: int
    responses: list[DFSFilterResponse]
