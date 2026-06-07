from fastapi import APIRouter, HTTPException, Query

from algorithms.planificacion_avanzada import (
    obtener_opciones_planificacion,
    recalcular_avanzado_desde_estado,
)
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


def _matches_route(route_data, origen, destino):
    if not route_data:
        return False
    return (
        route_data.get("origen", "").upper() == origen
        and route_data.get("destino", "").upper() == destino
    )


def _current_transit_route(payload, estado):
    tramo_actual = payload.get("tramo_actual") or payload.get("tramoEnTransito")
    if tramo_actual:
        return tramo_actual

    origen = payload.get("origen_tramo") or payload.get("origenTramo")
    destino = payload.get("destino_tramo") or payload.get("destinoTramo")
    if origen and destino:
        return {"origen": origen, "destino": destino}

    if payload.get("en_transito") or payload.get("enTransito"):
        tramos = estado.get("tramos_volados", [])
        if tramos:
            return tramos[-1]
    return None


def _remove_last_if_matches(values, expected):
    if values and values[-1] == expected:
        return values[:-1]
    return values


def _redirect_to_route_origin(estado, origen, destino):
    """Return the traveler to the origin of the interrupted segment."""
    estado = dict(estado)
    estado["aeropuerto_actual"] = origen
    estado["camino"] = _remove_last_if_matches(list(estado.get("camino", [])), destino)
    estado["visitados"] = _remove_last_if_matches(list(estado.get("visitados", [])), destino)

    interrupcion = {
        "tipo": "interrupcion",
        "motivo": "ruta_bloqueada",
        "origen": origen,
        "destino": destino,
        "accion": "redirigido_al_origen_del_tramo",
        "aeropuerto_actual": origen,
    }
    estado["decisiones"] = [*estado.get("decisiones", []), interrupcion]
    estado["interrupciones"] = [*estado.get("interrupciones", []), interrupcion]
    return estado


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


@router.post("/bloquear-recalcular")
def bloquear_y_recalcular(payload: dict):
    """
    R4 - Block a route and recalculate from the current trip state.

    Expected payload:
    {
      "origen": "BOG",
      "destino": "LIM",
      "estado": {...},
      "en_transito": true,
      "tramo_actual": {"origen": "BOG", "destino": "LIM"}
    }
    """
    graph = get_graph()
    try:
        origen = payload["origen"].upper()
        destino = payload["destino"].upper()
        estado = payload["estado"]
    except KeyError as error:
        raise HTTPException(status_code=400, detail=f"Campo faltante: {error}") from error

    edge = _find_edge(graph, origen, destino)
    edge.set_available(False)

    tramo_en_transito = _current_transit_route(payload, estado)
    afecto_tramo_actual = _matches_route(tramo_en_transito, origen, destino)
    estado_recalculado = estado
    accion = "ruta_bloqueada_sin_redireccion"

    if afecto_tramo_actual:
        estado_recalculado = _redirect_to_route_origin(estado, origen, destino)
        accion = "redirigido_al_origen_del_tramo"

    try:
        opciones = obtener_opciones_planificacion(graph, estado_recalculado)
        itinerario_recalculado = recalcular_avanzado_desde_estado(
            graph,
            estado_recalculado,
            int(payload.get("max_expansiones", 20000)),
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {
        "message": f"Ruta {origen} -> {destino} bloqueada y recalculada",
        "ruta_bloqueada": {"origen": origen, "destino": destino, "disponible": False},
        "interrupcion": {
            "afecto_tramo_actual": afecto_tramo_actual,
            "tramo_en_transito": tramo_en_transito,
            "accion": accion,
            "aeropuerto_reanudacion": estado_recalculado["aeropuerto_actual"],
        },
        "estado_recalculado": estado_recalculado,
        "opciones_desde_reanudacion": opciones,
        "itinerario_recalculado": itinerario_recalculado,
        "grafo": serialize_airport_graph(graph),
    }


@router.put("/bloquear")
def bloquear_ruta(
    origen: str,
    destino: str,
    recalcular_desde: str | None = None,
    criterio: str = "distancia",
):
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
        from algorithms.dijkstra import dijkstra, reconstruir_camino
        recalcular_desde = recalcular_desde.upper()
        try:
            distancias, previos = dijkstra(graph, recalcular_desde, criterio)
            camino_alternativo = reconstruir_camino(previos, recalcular_desde, destino)
            response["ruta_alternativa"] = {
                "criterio": criterio,
                "camino": camino_alternativo,
                "costo_total": distancias.get(destino, float("inf")),
            }
        except ValueError:
            response["ruta_alternativa"] = None
        response["rutas_disponibles_desde"] = _available_routes_from(graph, recalcular_desde)

    return response

@router.get("/disponibles")
def rutas_disponibles(origen: str):
    """R4 - List available routes from an airport."""
    graph = get_graph()
    origen = origen.upper()
    return {
        "origen": origen,
        "rutas": _available_routes_from(graph, origen),
    }
