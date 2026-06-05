from fastapi import APIRouter, HTTPException, Query

from service.graphService import serialize_airport_graph
from service.graphState import get_graph

router = APIRouter()


def _find_edge(graph, origen, destino):
    try:
        vertex = graph.get_vertex(origen)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    for edge in vertex.neighbors:
        if edge.get_vertex2().get_name() == destino:
            return edge

    raise HTTPException(status_code=404, detail=f"No existe ruta de {origen} a {destino}")


def _available_routes_from(graph, origen):
    try:
        vertex = graph.get_vertex(origen)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    return [
        {
            "origen": origen,
            "destino": edge.get_vertex2().get_name(),
            "distancia_km": edge.get_distance(),
            "aeronaves": edge.get_aeronaves(),
            "disponible": edge.is_available(),
        }
        for edge in vertex.neighbors
        if edge.is_available()
    ]


@router.put("/bloquear")
def bloquear_ruta(origen: str, destino: str, recalcular_desde: str | None = None):
    """R4 - Block a route and return the updated graph."""
    graph = get_graph()
    origen, destino = origen.upper(), destino.upper()
    edge = _find_edge(graph, origen, destino)
    edge.set_available(False)

    response = {
        "message": f"Ruta {origen} -> {destino} bloqueada",
        "ruta": {"origen": origen, "destino": destino, "disponible": False},
        "grafo": serialize_airport_graph(graph),
    }
    if recalcular_desde:
        response["rutas_disponibles_desde"] = _available_routes_from(graph, recalcular_desde.upper())
    return response


@router.put("/desbloquear")
def desbloquear_ruta(origen: str, destino: str):
    """R4 - Unblock a route and return the updated graph."""
    graph = get_graph()
    origen, destino = origen.upper(), destino.upper()
    edge = _find_edge(graph, origen, destino)
    edge.set_available(True)
    return {
        "message": f"Ruta {origen} -> {destino} desbloqueada",
        "ruta": {"origen": origen, "destino": destino, "disponible": True},
        "grafo": serialize_airport_graph(graph),
    }


@router.get("/disponibles")
def rutas_disponibles(origen: str):
    """R4 - List available routes from an airport."""
    graph = get_graph()
    origen = origen.upper()
    return {
        "origen": origen,
        "rutas": _available_routes_from(graph, origen),
    }
