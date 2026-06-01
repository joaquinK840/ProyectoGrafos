from fastapi import APIRouter, HTTPException
from service.graphService import serialize_airport_graph
from service.graphState import get_graph

router = APIRouter()


@router.put("/bloquear")
def bloquear_ruta(origen: str, destino: str):
    """R4 — Bloquea una arista y retorna el grafo actualizado."""
    graph = get_graph()
    origen, destino = origen.upper(), destino.upper()

    try:
        vertex = graph.get_vertex(origen)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))

    for edge in vertex.neighbors:
        if edge.get_vertex2().get_name() == destino:
            edge.set_available(False)
            return {
                "message": f"Ruta {origen} → {destino} bloqueada",
                "grafo": serialize_airport_graph(graph),
            }

    raise HTTPException(status_code=404, detail=f"No existe ruta de {origen} a {destino}")