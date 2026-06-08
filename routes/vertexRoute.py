from fastapi import APIRouter, HTTPException
from service.graphState import get_graph

router = APIRouter()

@router.get("/airports")
def get_airports():
    graph = get_graph()
    return [
        {"id": v.get_name(), "nombre": getattr(v, "nombre", v.get_name()), "ciudad": getattr(v, "ciudad", "")}
        for v in graph.vertices.values()
    ]

@router.get("/airports/{IATA}")
def get_airport(IATA: str):
    graph = get_graph()
    iata = IATA.upper()
    if iata not in graph.vertices:
        raise HTTPException(status_code=404, detail=f"Aeropuerto '{iata}' no encontrado")
    v = graph.vertices[iata]
    return {"id": v.get_name(), "nombre": getattr(v, "nombre", v.get_name()), "ciudad": getattr(v, "ciudad", "")}
