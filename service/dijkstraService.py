"""
Dijkstra — Camino mínimo en grafo ponderado dirigido.
3 variantes: distancia (km), tiempo (min), costo (USD).

Justificación: Dijkstra es correcto para grafos con pesos no negativos,
que es exactamente el caso de rutas aéreas (distancia, tiempo y costo >= 0).

Complejidad: O((V + E) log V) con heap.
"""
import heapq

from core.edge.edge import normalize_aircraft_name

CRITERIOS_BASE = ("distancia", "tiempo", "costo")
CRITERIOS_VALIDOS = {*CRITERIOS_BASE, "combinado"}


def dijkstra(
    graph,
    origen: str,
    criterio: str,
    destino: str | None = None,
    excluir_secundarios: bool = False,
    aeronaves_permitidas: list[str] | None = None,
) -> tuple[dict, dict]:
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
    if criterio not in CRITERIOS_VALIDOS:
        raise ValueError(f"Criterio '{criterio}' invalido. Use: {CRITERIOS_VALIDOS}")

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
            if not _edge_available(edge):
                continue

            vecino = edge.get_vertex2().get_name()

            # Saltar nodos no disponibles
            if not graph.vertices[vecino].get_available():
                continue

            if excluir_secundarios and vecino != destino and not graph.vertices[vecino].is_hub():
                continue

            if aeronaves_permitidas and not _edge_has_allowed_aircraft(edge, aeronaves_permitidas):
                continue

            # Peso según criterio
            peso = _get_peso(edge, criterio, aeronaves_permitidas)
            nuevo_costo = costo_actual + peso

            if nuevo_costo < distancias[vecino]:
                distancias[vecino] = nuevo_costo
                previos[vecino] = nodo_actual
                heapq.heappush(heap, (nuevo_costo, vecino))

    return distancias, previos


def reconstruir_camino(previos: dict, origen: str, destino: str) -> list[str]:
    camino = []
    nodo = destino

    while nodo is not None:
        camino.append(nodo)
        nodo = previos.get(nodo)

    camino.reverse()

    if not camino or camino[0] != origen:
        return []

    return camino


def calcular_rutas_por_criterios(
    graph,
    origen: str,
    destino: str,
    criterios: list[str] | None,
    excluir_secundarios: bool = False,
    aeronaves_permitidas: list[str] | None = None,
) -> dict:
    """Calcula rutas origen-destino para los criterios solicitados."""
    criterios_normalizados = _normalize_criterios(criterios)
    aeronaves = _normalize_aircraft_selection(graph, aeronaves_permitidas)

    if destino not in graph.vertices:
        raise ValueError(f"Aeropuerto destino '{destino}' no existe en el grafo")

    rutas = []
    for criterio in criterios_normalizados:
        distancias, previos = dijkstra(
            graph,
            origen,
            criterio,
            destino=destino,
            excluir_secundarios=excluir_secundarios,
            aeronaves_permitidas=aeronaves,
        )

        if distancias[destino] == float("inf"):
            rutas.append({
                "criterio": criterio,
                "origen": origen,
                "destino": destino,
                "encontrada": False,
                "mensaje": f"No hay ruta de {origen} a {destino} con el criterio {criterio}",
                "camino": [],
                "escalas": [],
                "tramos": [],
            })
            continue

        camino = reconstruir_camino(previos, origen, destino)
        rutas.append(_serializar_ruta(graph, camino, criterio, aeronaves))

    return {
        "origen": origen,
        "destino": destino,
        "criterios_solicitados": criterios or [],
        "criterios_calculados": criterios_normalizados,
        "excluir_secundarios": excluir_secundarios,
        "aeronaves_permitidas": aeronaves,
        "rutas": rutas,
    }


def _edge_has_allowed_aircraft(edge, aeronaves_permitidas: list[str]) -> bool:
    allowed = {_transport_key(aircraft) for aircraft in aeronaves_permitidas}
    return any(
        _transport_key(aircraft) in allowed
        for aircraft in (edge.get_aeronaves() or ["Avion Comercial"])
    )


def _get_filtered_options(edge, aeronaves_permitidas: list[str] | None):
    options = edge.get_aircraft_options()
    if not aeronaves_permitidas:
        return options

    allowed = {_transport_key(aircraft) for aircraft in aeronaves_permitidas}
    return [
        option
        for option in options
        if _transport_key(option["nombre"]) in allowed
    ]


def _get_peso(edge, criterio: str, aeronaves_permitidas: list[str] | None = None) -> float:
    """Devuelve el peso de la arista segun el criterio elegido."""
    options = _get_filtered_options(edge, aeronaves_permitidas)
    if not options:
        return float("inf")

    if criterio == "distancia":
        return edge.get_distance()
    elif criterio == "tiempo":
        return min(option["tiempo"] for option in options)
    elif criterio == "costo":
        return min(option["costo"] for option in options)
    elif criterio == "combinado":
        return min(
            edge.get_distance() / 1000 + option["tiempo"] / 60 + option["costo"] / 100
            for option in options
        )
    return edge.get_distance()


def _normalize_criterios(criterios: list[str] | None) -> list[str]:
    if not criterios:
        raise ValueError("Debe seleccionar al menos un criterio de optimizacion")

    selected = []
    for criterio in criterios:
        criterio = criterio.lower().strip()
        if criterio not in CRITERIOS_VALIDOS:
            raise ValueError(f"Criterio '{criterio}' invalido. Use: {CRITERIOS_VALIDOS}")
        if criterio not in selected:
            selected.append(criterio)

    if all(criterio in selected for criterio in CRITERIOS_BASE):
        return ["combinado"]
    if "combinado" in selected:
        return ["combinado"]
    return selected


def _normalize_aircraft_selection(graph, aeronaves_permitidas: list[str] | None) -> list[str]:
    selected = {_transport_key(aircraft) for aircraft in aeronaves_permitidas or [] if aircraft and aircraft.strip()}
    if selected:
        return sorted(selected)

    available = set()
    for vertex in graph.vertices.values():
        for edge in vertex.neighbors:
            for option in edge.get_aircraft_options():
                available.add(_transport_key(option["nombre"]))

    if not available:
        raise ValueError("Debe seleccionar al menos un tipo de transporte")
    return sorted(available)


def _serializar_ruta(graph, camino: list[str], criterio: str, aeronaves: list[str]) -> dict:
    tramos = []
    distancia_total = 0
    tiempo_total = 0
    costo_total = 0

    for origen, destino in zip(camino, camino[1:]):
        edge = _find_edge(graph, origen, destino)
        option = _choose_aircraft_option(edge, criterio, aeronaves)
        distancia = edge.get_distance()
        tiempo = option["tiempo"]
        costo = option["costo"]
        distancia_total += distancia
        tiempo_total += tiempo
        costo_total += costo
        tramos.append({
            "origen": origen,
            "destino": destino,
            "aeronave": option["nombre"],
            "transporte": _transport_key(option["nombre"]),
            "aeronaves": edge.get_aeronaves(),
            "distancia_km": distancia,
            "distancia_acumulada_km": round(distancia_total, 2),
            "tiempo_tramo": tiempo,
            "tiempo_acumulado": round(tiempo_total, 1),
            "costo_tramo": costo,
            "costo_acumulado": round(costo_total, 2),
        })

    return {
        "criterio": criterio,
        "encontrada": True,
        "origen": camino[0] if camino else None,
        "destino": camino[-1] if camino else None,
        "distancia_total": round(distancia_total, 2),
        "tiempo_total": round(tiempo_total, 1),
        "costo_total": round(costo_total, 2),
        "camino": camino,
        "escalas": camino[1:-1],
        "tramos": tramos,
    }


def _find_edge(graph, origen, destino):
    for edge in graph.vertices[origen].neighbors:
        if edge.get_vertex2().get_name() == destino:
            return edge
    raise ValueError(f"No existe ruta de {origen} a {destino}")


def _choose_aircraft_option(edge, criterio: str, aeronaves: list[str]):
    options = _get_filtered_options(edge, aeronaves)
    if not options:
        raise ValueError("La ruta no tiene transportes permitidos")

    if criterio == "tiempo":
        return min(options, key=lambda option: (option["tiempo"], option["costo"]))
    if criterio == "distancia":
        return min(options, key=lambda option: (edge.get_distance(), option["costo"], option["tiempo"]))
    if criterio == "combinado":
        return min(
            options,
            key=lambda option: (
                edge.get_distance() / 1000 + option["tiempo"] / 60 + option["costo"] / 100,
                option["costo"],
                option["tiempo"],
            ),
        )
    return min(options, key=lambda option: (option["costo"], option["tiempo"]))


def _edge_available(edge):
    if hasattr(edge, "get_available"):
        return edge.get_available()
    return edge.is_available()


def _transport_key(name):
    normalized = normalize_aircraft_name(name.strip())
    return normalized.lower()
