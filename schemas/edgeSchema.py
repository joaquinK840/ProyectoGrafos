from pydantic import BaseModel, Field

class EdgePayload(BaseModel):
    vertex1: str
    vertex2: str
    distance: int = 0
    time: int = 0
    cost: int = 0

class AirportEdgePayload(BaseModel):
    origen: str                        # IATA origen
    destino: str                       # IATA destino
    distanciaKm: float
    aeronaves: list[str]               # ["Avión Comercial", "Hélice"]
    costoBase: float = -1.0            # 0 = subsidiado
    estanciaMinima: int = 0