from service.planning.config import DEFAULT_MAX_EXPANSIONES, DEFAULT_TIEMPO_DISPONIBLE, trabajos_habilitados
from service.planning.decisions import aplicar_trabajo, aplicar_vuelo
from service.planning.helpers import mejor_trabajo
from service.planning.options import obtener_opciones_planificacion, vuelos_disponibles
from service.planning.reports import generar_reporte_final
from service.planning.state import crear_estado_planificacion, normalizar_estado


def planificar_avanzado(
    graph,
    origen: str,
    presupuesto_inicial: float,
    tiempo_disponible: float | None = None,
) -> dict:
    estado = crear_estado_planificacion(
        graph,
        origen,
        presupuesto_inicial,
        tiempo_disponible or DEFAULT_TIEMPO_DISPONIBLE,
    )
    return obtener_opciones_planificacion(graph, estado)


def planificar_avanzado_automatico(
    graph,
    origen: str,
    presupuesto_inicial: float,
    tiempo_disponible: float | None = None,
    max_expansiones: int = DEFAULT_MAX_EXPANSIONES,
) -> dict:
    inicial = crear_estado_planificacion(
        graph,
        origen,
        presupuesto_inicial,
        tiempo_disponible or DEFAULT_TIEMPO_DISPONIBLE,
    )
    return buscar_itinerario_automatico(graph, inicial, max_expansiones)


def recalcular_avanzado_desde_estado(
    graph,
    estado: dict,
    max_expansiones: int = DEFAULT_MAX_EXPANSIONES,
) -> dict:
    estado = normalizar_estado(estado)
    if estado["aeropuerto_actual"] not in graph.vertices:
        raise ValueError(f"Aeropuerto actual '{estado['aeropuerto_actual']}' no existe en el grafo")
    return buscar_itinerario_automatico(graph, estado, max_expansiones)


def buscar_itinerario_automatico(graph, inicial: dict, max_expansiones: int) -> dict:
    mejor = inicial
    expansiones = 0

    def mejor_que(candidato, actual):
        return (
            len(candidato["visitados"]),
            -candidato["total_gastado"],
            -candidato["tiempo_transcurrido_min"],
        ) > (
            len(actual["visitados"]),
            -actual["total_gastado"],
            -actual["tiempo_transcurrido_min"],
        )

    def dfs(estado):
        nonlocal mejor, expansiones
        if expansiones >= max_expansiones:
            return
        expansiones += 1

        if mejor_que(estado, mejor):
            mejor = estado

        vuelos = vuelos_disponibles(graph, graph.vertices[estado["aeropuerto_actual"]], estado)
        candidatos = []
        for vuelo in vuelos:
            for option in vuelo["opciones_aeronaves"]:
                if option["factible"]:
                    candidatos.append((vuelo["destino"], option))

        candidatos.sort(key=lambda item: (
            item[1]["costo_total_decision"],
            item[1]["tiempo_resultante_min"],
        ))

        for destino, option in candidatos:
            try:
                siguiente = aplicar_vuelo(graph, estado, destino, option["nombre"])
            except ValueError:
                continue
            dfs(siguiente)

        if trabajos_habilitados(graph, estado):
            trabajo = mejor_trabajo(graph.vertices[estado["aeropuerto_actual"]])
            if trabajo and not _trabajo_ya_realizado(estado, trabajo["nombre"]):
                horas = min(
                    float(trabajo.get("max_horas", 1)),
                    max(1, (estado["tiempo_disponible_min"] - estado["tiempo_transcurrido_min"]) // 60),
                )
                try:
                    dfs(aplicar_trabajo(graph, estado, trabajo["nombre"], horas))
                except ValueError:
                    pass

    dfs(inicial)
    return {
        "modo": "automatico",
        "expansiones": expansiones,
        "limite_expansiones": max_expansiones,
        "limite_alcanzado": expansiones >= max_expansiones,
        "itinerario": generar_reporte_final(graph, mejor),
    }


def _trabajo_ya_realizado(estado: dict, nombre_trabajo: str) -> bool:
    aeropuerto = estado["aeropuerto_actual"]
    return any(
        trabajo["aeropuerto"] == aeropuerto and trabajo["nombre"] == nombre_trabajo
        for trabajo in estado.get("trabajos_realizados", [])
    )
