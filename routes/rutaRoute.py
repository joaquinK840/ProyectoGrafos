from fastapi import APIRouter, HTTPException, Query

from algorithms.bfs_dfs import dfs_mayor_destinos, planificacion_basica
from algorithms.dijkstra import dijkstra, reconstruir_camino
from algorithms.planificacion_avanzada import (
    obtener_opciones_planificacion,
    planificar_avanzado,
    simular_decision_vuelo,
)
from service.graphState import get_graph


router = APIRouter()


@router.get("/ruta")
def get_ruta(origen: str, destino: str, criterio: str = "distancia"):
    """R2 - Shortest path. criterio: distancia | tiempo | costo."""
    graph = get_graph()
    try:
        distancias, previos = dijkstra(graph, origen.upper(), criterio)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    destino = destino.upper()
    if distancias[destino] == float("inf"):
        raise HTTPException(status_code=404, detail=f"No hay ruta de {origen} a {destino}")

    camino = reconstruir_camino(previos, origen.upper(), destino)
    tramos = []
    for i in range(len(camino) - 1):
        v1, v2 = camino[i], camino[i + 1]
        for edge in graph.vertices[v1].neighbors:
            if edge.get_vertex2().get_name() == v2:
                tramos.append({
                    "origen": v1,
                    "destino": v2,
                    "distancia_km": edge.get_distance(),
                    "aeronaves": edge.get_aeronaves(),
                })
                break

    return {
        "criterio": criterio,
        "origen": origen.upper(),
        "destino": destino,
        "costo_total": distancias[destino],
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
