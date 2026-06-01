"""
Dijkstra — Camino mínimo en grafo ponderado dirigido.
3 variantes: distancia (km), tiempo (min), costo (USD).

Justificación: Dijkstra es correcto para grafos con pesos no negativos,
que es exactamente el caso de rutas aéreas (distancia, tiempo y costo >= 0).

Complejidad: O((V + E) log V) con heap.
"""
import heapq

def dijkstra(graph, origen: str, criterio: str) -> tuple[dict, dict]:
    """
    Calcula el camino mínimo desde origen a todos los demás nodos.

    Args:
        graph: Directed_Graph con los aeropuertos y rutas.
        origen: Código IATA del aeropuerto de origen.
        criterio: "distancia" | "tiempo" | "costo"

    Returns:
        distancias: dict {nodo: costo_minimo}
        previos:    dict {nodo: nodo_anterior} — para reconstruir el camino.
    """
    # ── Validar criterio ──────────────────────────────────────────────
    criterios_validos = {"distancia", "tiempo", "costo"}
    if criterio not in criterios_validos:
        raise ValueError(f"Criterio '{criterio}' inválido. Use: {criterios_validos}")

    # ── Validar origen ────────────────────────────────────────────────
    try:
        graph.get_vertex(origen)
    except ValueError:
        raise ValueError(f"Aeropuerto origen '{origen}' no existe en el grafo")

    # ── Inicialización ────────────────────────────────────────────────
    distancias = {v: float("inf") for v in graph.vertices}
    distancias[origen] = 0
    previos = {v: None for v in graph.vertices}

    # heap: (costo_acumulado, nombre_nodo)
    heap = [(0, origen)]

    while heap:
        costo_actual, nodo_actual = heapq.heappop(heap)

        # Si ya encontramos un camino mejor, ignorar
        if costo_actual > distancias[nodo_actual]:
            continue

        vertex = graph.vertices[nodo_actual]

        for edge in vertex.neighbors:
            # Saltar rutas bloqueadas (R4)
            if not edge.is_available():
                continue

            vecino = edge.get_vertex2().get_name()

            # Saltar nodos no disponibles
            if not graph.vertices[vecino].get_available():
                continue

            # Peso según criterio
            peso = _get_peso(edge, criterio)
            nuevo_costo = costo_actual + peso

            if nuevo_costo < distancias[vecino]:
                distancias[vecino] = nuevo_costo
                previos[vecino] = nodo_actual
                heapq.heappush(heap, (nuevo_costo, vecino))

    return distancias, previos


def reconstruir_camino(previos: dict, origen: str, destino: str) -> list[str]:
    """
    Reconstruye la secuencia de nodos desde origen hasta destino
    usando el dict de previos que devuelve dijkstra().

    Returns:
        Lista de códigos IATA en orden, o [] si no hay camino.
    """
    camino = []
    nodo = destino

    while nodo is not None:
        camino.append(nodo)
        nodo = previos[nodo]

    camino.reverse()

    # Verificar que el camino realmente llega al origen
    if camino[0] != origen:
        return []

    return camino


def _get_peso(edge, criterio: str) -> float:
    """Devuelve el peso de la arista según el criterio elegido."""
    if criterio == "distancia":
        return edge.get_distance()
    elif criterio == "tiempo":
        return edge.get_time() if edge.get_time() > 0 else edge.get_distance() * 0.7
    elif criterio == "costo":
        return edge.get_cost() if edge.get_cost() > 0 else edge.get_distance() * 0.18
    return edge.get_distance()