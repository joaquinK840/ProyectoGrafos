from pydantic import BaseModel


class DijkstraPayload(BaseModel):
    start_vertex: str
    filters: list[int]


class DijkstraNodeResponse(BaseModel):
    vertex: str
    distance: float
    previous: str | None


class DijkstraFilterResponse(BaseModel):
    filter_id: int
    filter_name: str
    results: list[DijkstraNodeResponse]


class DijkstraMultiResponse(BaseModel):
    start_vertex: str
    responses: list[DijkstraFilterResponse]