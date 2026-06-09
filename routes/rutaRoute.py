from fastapi import APIRouter, HTTPException, Query

from service.dfsService import dfs_mayor_destinos, planificacion_basica
from service.dijkstraService import calcular_rutas_por_criterios
from service.planificacionService import (
    generar_reporte_final,
    obtener_opciones_planificacion,
    planificar_avanzado,
    planificar_avanzado_automatico,
    simular_decision_actividad,
    simular_decision_trabajo,
    simular_decision_vuelo,
)
from service.graphState import get_graph


router = APIRouter()


@router.get("/ruta")
def get_ruta(
    origen: str,
    destino: str,
    criterio: str = "distancia",
    criterios: list[str] | None = Query(default=None),
    excluir_secundarios: bool = False,
    aeronaves: list[str] | None = Query(default=None),
):
    """R2 - Ruta con destino final por uno o varios criterios."""
    graph = get_graph()
    origen = origen.upper()
    destino = destino.upper()

    try:
        resultado = calcular_rutas_por_criterios(
            graph,
            origen,
            destino,
            criterios or [criterio],
            excluir_secundarios=excluir_secundarios,
            aeronaves_permitidas=aeronaves,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    rutas_encontradas = [ruta for ruta in resultado["rutas"] if ruta["encontrada"]]
    if not rutas_encontradas:
        raise HTTPException(status_code=404, detail=f"No hay ruta de {origen} a {destino}")

    if criterios:
        return resultado
    return rutas_encontradas[0]


@router.get("/rutas-criterios")
def get_rutas_por_criterios(
    origen: str,
    destino: str,
    criterios: list[str] = Query(...),
    excluir_secundarios: bool = False,
    aeronaves: list[str] | None = Query(default=None),
):
    """R2 - Calcula una ruta por criterio, o una combinada si llegan distancia/tiempo/costo."""
    graph = get_graph()
    try:
        resultado = calcular_rutas_por_criterios(
            graph,
            origen.upper(),
            destino.upper(),
            criterios,
            excluir_secundarios=excluir_secundarios,
            aeronaves_permitidas=aeronaves,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    if not any(ruta["encontrada"] for ruta in resultado["rutas"]):
        raise HTTPException(status_code=404, detail=f"No hay ruta de {origen.upper()} a {destino.upper()}")

    return resultado


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


@router.get("/itinerario-avanzado/automatico")
def get_itinerario_avanzado_automatico(
    origen: str,
    presupuesto: float,
    tiempo_horas: float = 72,
    max_expansiones: int = 20000,
):
    """R3 - Automatically maximize destinations and minimize spending."""
    graph = get_graph()
    try:
        return planificar_avanzado_automatico(
            graph,
            origen.upper(),
            presupuesto,
            tiempo_disponible=tiempo_horas * 60,
            max_expansiones=max_expansiones,
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


@router.post("/itinerario-avanzado/actividad")
def post_itinerario_avanzado_actividad(payload: dict):
    """R3 - Apply a user-selected optional activity."""
    graph = get_graph()
    try:
        return simular_decision_actividad(
            graph,
            payload["estado"],
            payload["actividad"],
        )
    except KeyError as error:
        raise HTTPException(status_code=400, detail=f"Campo faltante: {error}") from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/itinerario-avanzado/trabajo")
def post_itinerario_avanzado_trabajo(payload: dict):
    """R3 - Apply a temporary job and update budget/time."""
    graph = get_graph()
    try:
        return simular_decision_trabajo(
            graph,
            payload["estado"],
            payload["trabajo"],
            payload["horas"],
        )
    except KeyError as error:
        raise HTTPException(status_code=400, detail=f"Campo faltante: {error}") from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/itinerario-avanzado/reporte")
def post_itinerario_avanzado_reporte(estado: dict):
    """R3/R5 - Generate the final report from the current advanced state."""
    graph = get_graph()
    try:
        return generar_reporte_final(graph, estado)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
