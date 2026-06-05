from typing import Optional
from pydantic import BaseModel, Field
from schemas.edgeSchema import EdgePayload


# ── Submodelos de nodo ──────────────────────────────────────────────────

class ActividadSchema(BaseModel):
    nombre: str
    tipo: str                  # "obligatoria" | "opcional"
    duracionMin: int
    costoUSD: float

class TrabajoSchema(BaseModel):
    nombre: str
    tarifaHora: float
    maxHoras: int

class AirportVertexPayload(BaseModel):
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

# ── Submodelos de arista ────────────────────────────────────────────────

class AirportEdgePayload(BaseModel):
    origen: str
    destino: str
    distanciaKm: float
    aeronaves: list[str]
    costoBase: float = 0.0
    estanciaMinima: int = 0

# ── Configuración global ────────────────────────────────────────────────

class AircraftConfigSchema(BaseModel):
    costoKm: float
    tiempoKm: float

class GlobalConfigSchema(BaseModel):
    aeronaves: dict[str, AircraftConfigSchema] = Field(default_factory=dict)
    presupuestoMinimoPorc: float = 35.0
    intervaloAlojamiento: float = 20.0
    intervaloAlimentacion: float = 8.0

# ── Payloads principales (van al final, usan todo lo anterior) ──────────

class GraphPayload(BaseModel):
    directed: bool = True
    vertices: list[str]
    edges: list[EdgePayload] = Field(default_factory=list)

class AirportGraphPayload(BaseModel):
    nodos: list[AirportVertexPayload]
    aristas: list[AirportEdgePayload]
    config: Optional[GlobalConfigSchema] = None