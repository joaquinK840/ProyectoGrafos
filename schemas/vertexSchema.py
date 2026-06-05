from pydantic import BaseModel, Field

class VertexPayload(BaseModel):
    name: str


from pydantic import BaseModel, Field
from typing import Optional

class ActividadSchema(BaseModel):
    nombre: str
    tipo: str                          # "obligatoria" | "opcional"
    duracionMin: int
    costoUSD: float

class TrabajoSchema(BaseModel):
    nombre: str
    tarifaHora: float
    maxHoras: int

class AirportVertexPayload(BaseModel):
    id: str                            # Código IATA
    nombre: str
    ciudad: str
    pais: str
    zonaHoraria: str
    esHub: bool = False
    costoAlojamiento: float = 0.0
    costoAlimentacion: float = 0.0
    actividades: list[ActividadSchema] = []
    trabajos: list[TrabajoSchema] = []