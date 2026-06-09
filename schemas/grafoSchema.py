from typing import Optional
from pydantic import BaseModel, Field, ConfigDict 
from schemas.edgeSchema import EdgePayload


# ── Submodelos de nodo ──────────────────────────────────────────────────

class ActividadSchema(BaseModel):
    model_config = ConfigDict(extra="allow")
    nombre: str
    tipo: str
    duracion_min: int = 0
    costo_usd: float = 0.0

class TrabajoSchema(BaseModel):
    model_config = ConfigDict(extra="allow")
    nombre: str
    tarifa_hora: float = 0.0
    max_horas: int = 8

class AirportVertexPayload(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    nombre: str
    ciudad: str
    pais: str
    zonaHoraria: str
    esHub: bool = False
    costoAlojamiento: float = 0.0
    costoAlimentacion: float = 0.0
    actividades: list[ActividadSchema] = Field(default_factory=list)
    trabajos: list[TrabajoSchema] = Field(default_factory=list)

class AirportEdgePayload(BaseModel):
    origen: str
    destino: str
    distanciaKm: float
    aeronaves: list[str]
    costoBase: float = -1.0   # ← también cambia default a -1.0, el JSON usa -1
    estanciaMinima: int = 0

class AirportGraphPayload(BaseModel):
    model_config = ConfigDict(extra="allow")  # ← ignora aeronaves/config 
    nodos: list[AirportVertexPayload]
    aristas: list[AirportEdgePayload]
    config: Optional[dict] = None

class GraphPayload(BaseModel):
    directed: bool = True
    vertices: list[str]
    edges: list[EdgePayload] = Field(default_factory=list)