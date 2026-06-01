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
            costo_tramo = _get_costo(edge)
            tiempo_tramo = _get_tiempo(edge)

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


def _get_costo(edge) -> float:
    """Costo del tramo — usa costo directo o calcula por distancia."""
    if edge.get_cost() > 0:
        return edge.get_cost()
    # Fallback: Avión Comercial por defecto
    return edge.get_distance() * 0.18


def _get_tiempo(edge) -> float:
    """Tiempo del tramo en minutos."""
    if edge.get_time() > 0:
        return edge.get_time()
    # Fallback: Avión Comercial por defecto
    return edge.get_distance() * 0.7