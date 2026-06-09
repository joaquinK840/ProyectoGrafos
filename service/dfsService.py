"""
DFS adaptado — Mayor cantidad de destinos con restricciones.

Justificación: DFS es ideal para explorar todos los caminos posibles
y encontrar el que maximiza destinos visitados. A diferencia de Dijkstra
que minimiza costo, aquí queremos MAXIMIZAR nodos visitados sin exceder
presupuesto o tiempo.

Se usa DFS con backtracking para explorar todas las rutas posibles
y quedarse con la que visita más destinos sin violar restricciones.

Complejidad: O(V!) en el peor caso, manejable con poda temprana.
"""

from core.edge.edge import normalize_aircraft_name


def planificacion_basica(
    graph,
    origen: str,
    presupuesto: float,
    tiempo_disponible: float,
    excluir_secundarios: bool = False,
    aeronaves_permitidas: list[str] | None = None,
) -> dict:
    """
    Returns the two basic R2 itinerary alternatives:
    - max destinations within budget, preferring lower cost on ties.
    - max destinations within time, preferring lower time on ties.
    """
    if origen not in graph.vertices:
        raise ValueError(f"Aeropuerto '{origen}' no existe en el grafo")

    required_aircraft = _resolve_required_aircraft(graph, aeronaves_permitidas)

    return {
        "origen": origen,
        "presupuesto": presupuesto,
        "tiempo_disponible_min": tiempo_disponible,
        "excluir_secundarios": excluir_secundarios,
        "aeronaves_requeridas": sorted(required_aircraft),
        "alternativa_presupuesto": _buscar_mejor_itinerario(
            graph,
            origen,
            presupuesto,
            tiempo_disponible,
            excluir_secundarios,
            required_aircraft,
            "costo",
        ),
        "alternativa_tiempo": _buscar_mejor_itinerario(
            graph,
            origen,
            presupuesto,
            tiempo_disponible,
            excluir_secundarios,
            required_aircraft,
            "tiempo",
        ),
    }


def _buscar_mejor_itinerario(
    graph,
    origen,
    presupuesto,
    tiempo_disponible,
    excluir_secundarios,
    required_aircraft,
    objetivo,
):
    mejor = _empty_itinerary(objetivo, origen)

    def _dfs(nodo_actual, visitados, camino, tramos, costo_acum, tiempo_acum, transportes_usados):
        candidato = {
            "criterio": objetivo,
            "camino": list(camino),
            "tramos": list(tramos),
            "costo_total": round(costo_acum, 2),
            "tiempo_total": round(tiempo_acum, 1),
            "destinos": len(camino) - 1,
            "transportes_usados": sorted(transportes_usados),
            "transportes_requeridos": sorted(required_aircraft),
            "cumple_transportes": required_aircraft.issubset(transportes_usados),
        }
        if candidato["cumple_transportes"] and _is_better_itinerary(candidato, mejor, objetivo):
            mejor.update(candidato)

        for edge in graph.vertices[nodo_actual].neighbors:
            if not edge.is_available():
                continue

            vecino_vertex = edge.get_vertex2()
            vecino = vecino_vertex.get_name()

            if vecino in visitados:
                continue
            if not vecino_vertex.get_available():
                continue
            if excluir_secundarios and not vecino_vertex.is_hub():
                continue

            option = _select_aircraft_option(edge, objetivo, required_aircraft)
            if option is None:
                continue

            costo_tramo = edge.calculate_cost(option["nombre"])
            tiempo_tramo = edge.calculate_time(option["nombre"])
            nuevo_costo = costo_acum + costo_tramo
            nuevo_tiempo = tiempo_acum + tiempo_tramo

            if nuevo_costo > presupuesto or nuevo_tiempo > tiempo_disponible:
                continue

            tramo = {
                "origen": nodo_actual,
                "destino": vecino,
                "aeronave": option["nombre"],
                "transporte": _transport_key(option["nombre"]),
                "distancia_km": edge.get_distance(),
                "costo_tramo": round(costo_tramo, 2),
                "costo_acumulado": round(nuevo_costo, 2),
                "tiempo_tramo": round(tiempo_tramo, 1),
                "tiempo_acumulado": round(nuevo_tiempo, 1),
            }

            visitados.add(vecino)
            camino.append(vecino)
            tramos.append(tramo)
            _dfs(
                vecino,
                visitados,
                camino,
                tramos,
                nuevo_costo,
                nuevo_tiempo,
                {*transportes_usados, tramo["transporte"]},
            )
            tramos.pop()
            camino.pop()
            visitados.remove(vecino)

    _dfs(origen, {origen}, [origen], [], 0, 0, set())
    return mejor


def _resolve_required_aircraft(graph, aircraft_names):
    selected = {_transport_key(name) for name in aircraft_names or [] if name and name.strip()}
    if selected:
        return selected

    available = set()
    for vertex in graph.vertices.values():
        for edge in vertex.neighbors:
            for option in edge.get_aircraft_options():
                available.add(_transport_key(option["nombre"]))

    if not available:
        raise ValueError("Debe existir al menos un tipo de transporte disponible")
    return available


def _transport_key(name):
    normalized = normalize_aircraft_name(name.strip())
    return normalized.lower()


def _select_aircraft_option(edge, objective, allowed_aircraft):
    options = edge.get_aircraft_options()
    if allowed_aircraft is not None:
        options = [
            option
            for option in options
            if _transport_key(option["nombre"]) in allowed_aircraft
        ]
    if not options:
        return None
    if objective == "tiempo":
        return min(options, key=lambda option: (option["tiempo"], option["costo"]))
    return min(options, key=lambda option: (option["costo"], option["tiempo"]))


def _empty_itinerary(criterion, origin):
    return {
        "criterio": criterion,
        "camino": [origin],
        "tramos": [],
        "costo_total": 0,
        "tiempo_total": 0,
        "destinos": 0,
        "transportes_usados": [],
        "transportes_requeridos": [],
        "cumple_transportes": False,
    }


def _is_better_itinerary(candidate, current, objective):
    if candidate["destinos"] != current["destinos"]:
        return candidate["destinos"] > current["destinos"]
    if objective == "tiempo":
        return (
            candidate["tiempo_total"],
            candidate["costo_total"],
        ) < (
            current["tiempo_total"],
            current["costo_total"],
        )
    return (
        candidate["costo_total"],
        candidate["tiempo_total"],
    ) < (
        current["costo_total"],
        current["tiempo_total"],
    )

def dfs_mayor_destinos(
    graph,
    origen: str,
    presupuesto: float,
    tiempo_disponible: float,
    criterio: str = "costo",
    excluir_secundarios: bool = False,
) -> dict:
    """
    Encuentra la ruta que permite visitar la mayor cantidad de destinos
    sin exceder el presupuesto o tiempo disponible.

    Args:
        graph: Directed_Graph
        origen: Código IATA de origen
        presupuesto: USD disponibles
        tiempo_disponible: minutos disponibles
        criterio: "costo" | "tiempo" — restricción principal a respetar
        excluir_secundarios: si True, ignora aeropuertos no hub

    Returns:
        dict con:
            - camino: lista de IATA en orden
            - costo_total: USD gastados
            - tiempo_total: minutos usados
            - destinos: cantidad de destinos visitados
    """
    mejor = {"camino": [], "costo_total": 0, "tiempo_total": 0, "destinos": 0}

    def _dfs(nodo_actual, visitados, camino, costo_acum, tiempo_acum):
        # Actualizar mejor si este camino visita más destinos
        destinos_actuales = len(camino) - 1  # sin contar el origen
        if destinos_actuales > mejor["destinos"]:
            mejor["camino"] = list(camino)
            mejor["costo_total"] = costo_acum
            mejor["tiempo_total"] = tiempo_acum
            mejor["destinos"] = destinos_actuales

        vertex = graph.vertices[nodo_actual]

        for edge in vertex.neighbors:
            # Saltar rutas bloqueadas
            if not edge.is_available():
                continue

            vecino_vertex = edge.get_vertex2()
            vecino = vecino_vertex.get_name()

            # No repetir aeropuertos (restricción del enunciado)
            if vecino in visitados:
                continue

            # Saltar nodos no disponibles
            if not vecino_vertex.get_available():
                continue

            # Saltar secundarios si se pidió
            if excluir_secundarios and not vecino_vertex.is_hub():
                continue

            # Calcular costo y tiempo del tramo
            option = edge.get_best_aircraft_option("tiempo" if criterio == "tiempo" else "costo")
            costo_tramo = edge.calculate_cost(option["nombre"])
            tiempo_tramo = edge.calculate_time(option["nombre"])

            # Poda: verificar restricciones antes de seguir
            if costo_acum + costo_tramo > presupuesto:
                continue
            if tiempo_acum + tiempo_tramo > tiempo_disponible:
                continue

            # Explorar
            visitados.add(vecino)
            camino.append(vecino)
            _dfs(vecino, visitados, camino, costo_acum + costo_tramo, tiempo_acum + tiempo_tramo)
            camino.pop()
            visitados.remove(vecino)

    # Validar origen
    if origen not in graph.vertices:
        raise ValueError(f"Aeropuerto '{origen}' no existe en el grafo")

    _dfs(origen, {origen}, [origen], 0, 0)
    return mejor

