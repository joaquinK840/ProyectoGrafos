from fastapi import APIRouter, HTTPException
from algorithms.dijkstra import dijkstra, reconstruir_camino
from algorithms.bfs_dfs import dfs_mayor_destinos
from service.graphService import serialize_airport_graph
from service.graphState import get_graph
from algorithms.planificacion_avanzada import planificar_avanzado


router = APIRouter()


@router.get("/ruta")
def get_ruta(origen: str, destino: str, criterio: str = "distancia"):
    """R2 — Camino mínimo. criterio: distancia | tiempo | costo"""
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
    """R2 — Mayor cantidad de destinos con restricción."""
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

@router.get("/itinerario-avanzado")
def get_itinerario_avanzado(origen: str, presupuesto: float):
    """R3 — Planificación avanzada con gestión dinámica de presupuesto."""
    graph = get_graph()
    try:
        resultado = planificar_avanzado(graph, origen.upper(), presupuesto)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    if resultado["destinos"] == 0:
        raise HTTPException(
            status_code=404,
            detail="No se encontró ninguna ruta con el presupuesto dado",
        )

    return resultado