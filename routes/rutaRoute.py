from fastapi import APIRouter, HTTPException, Query

from algorithms.bfs_dfs import dfs_mayor_destinos, planificacion_basica
from algorithms.dijkstra import dijkstra, reconstruir_camino
from core.edge.edge import normalize_aircraft_name
from algorithms.planificacion_avanzada import (
    obtener_opciones_planificacion,
    planificar_avanzado,
    simular_decision_vuelo,
)
from service.graphState import get_graph


router = APIRouter()


def _choose_aircraft_option(edge, criterio: str, aeronaves: list[str] | None = None):
    options = edge.get_aircraft_options()
    if aeronaves:
        allowed = {normalize_aircraft_name(aircraft) for aircraft in aeronaves}
        options = [
            option
            for option in options
            if option["nombre_normalizado"] in allowed
        ]

    if not options:
        raise ValueError("La ruta no tiene aeronaves permitidas")

    if criterio == "tiempo":
        return min(options, key=lambda option: (option["tiempo"], option["costo"]))
    return min(options, key=lambda option: (option["costo"], option["tiempo"]))


@router.get("/ruta")
def get_ruta(
    origen: str,
    destino: str,
    criterio: str = "distancia",
    excluir_secundarios: bool = False,
    aeronaves: list[str] | None = Query(default=None),
):
    """R2 - Shortest path. criterio: distancia | tiempo | costo."""
    graph = get_graph()
    origen = origen.upper()
    destino = destino.upper()

    if destino not in graph.vertices:
        raise HTTPException(status_code=400, detail=f"Aeropuerto destino '{destino}' no existe en el grafo")

    try:
        distancias, previos = dijkstra(
            graph,
            origen,
            criterio,
            destino=destino,
            excluir_secundarios=excluir_secundarios,
            aeronaves_permitidas=aeronaves,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    if distancias[destino] == float("inf"):
        raise HTTPException(status_code=404, detail=f"No hay ruta de {origen} a {destino}")

    camino = reconstruir_camino(previos, origen, destino)
    tramos = []
    distancia_total = 0
    tiempo_total = 0
    costo_total = 0

    for i in range(len(camino) - 1):
        v1, v2 = camino[i], camino[i + 1]
        for edge in graph.vertices[v1].neighbors:
            if edge.get_vertex2().get_name() == v2:
                option = _choose_aircraft_option(edge, criterio, aeronaves)
                distancia = edge.get_distance()
                tiempo = option["tiempo"]
                costo = option["costo"]
                distancia_total += distancia
                tiempo_total += tiempo
                costo_total += costo
                tramos.append({
                    "origen": v1,
                    "destino": v2,
                    "aeronave": option["nombre"],
                    "aeronaves": edge.get_aeronaves(),
                    "distancia_km": distancia,
                    "tiempo_tramo": tiempo,
                    "tiempo_acumulado": round(tiempo_total, 1),
                    "costo_tramo": costo,
                    "costo_acumulado": round(costo_total, 2),
                })
                break

    return {
        "criterio": criterio,
        "origen": origen,
        "destino": destino,
        "distancia_total": distancia_total,
        "tiempo_total": round(tiempo_total, 1),
        "costo_total": round(costo_total, 2),
        "camino": camino,
        "tramos": tramos,
    }


@router.get("/itinerario")
def get_itinerario(
    origen: str,
    presupuesto: float,
    tiempo_horas: float,
    criterio: str = "costo",
    excluir_secundarios: bool = False,
):
    """R2 - Max destinations with one optimization criterion."""
    graph = get_graph()
    try:
        resultado = dfs_mayor_destinos(
            graph,
            origen.upper(),
            presupuesto=presupuesto,
            tiempo_disponible=tiempo_horas * 60,
            criterio=criterio,
            excluir_secundarios=excluir_secundarios,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    if resultado["destinos"] == 0:
        raise HTTPException(status_code=404, detail="No hay ruta dentro de las restricciones dadas")

    return resultado


@router.get("/planificacion-basica")
def get_planificacion_basica(
    origen: str,
    presupuesto: float,
    tiempo_horas: float,
    excluir_secundarios: bool = False,
    aeronaves: list[str] | None = Query(default=None),
):
    """R2 - Two basic itinerary alternatives with budget/time constraints."""
    graph = get_graph()
    try:
        resultado = planificacion_basica(
            graph,
            origen.upper(),
            presupuesto=presupuesto,
            tiempo_disponible=tiempo_horas * 60,
            excluir_secundarios=excluir_secundarios,
            aeronaves_permitidas=aeronaves,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    if (
        resultado["alternativa_presupuesto"]["destinos"] == 0
        and resultado["alternativa_tiempo"]["destinos"] == 0
    ):
        raise HTTPException(status_code=404, detail="No hay rutas dentro de las restricciones dadas")

    return resultado


@router.get("/itinerario-avanzado")
def get_itinerario_avanzado(origen: str, presupuesto: float, tiempo_horas: float = 72):
    """R3 - Start advanced step-by-step planning."""
    graph = get_graph()
    try:
        return planificar_avanzado(
            graph,
            origen.upper(),
            presupuesto,
            tiempo_disponible=tiempo_horas * 60,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/itinerario-avanzado/opciones")
def post_itinerario_avanzado_opciones(estado: dict):
    """R3 - List decisions available from the submitted planning state."""
    graph = get_graph()
    try:
        return obtener_opciones_planificacion(graph, estado)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/itinerario-avanzado/vuelo")
def post_itinerario_avanzado_vuelo(payload: dict):
    """R3 - Apply a user-selected flight and aircraft, then return next options."""
    graph = get_graph()
    try:
        return simular_decision_vuelo(
            graph,
            payload["estado"],
            payload["destino"].upper(),
            payload["aeronave"],
        )
    except KeyError as error:
        raise HTTPException(status_code=400, detail=f"Campo faltante: {error}") from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
