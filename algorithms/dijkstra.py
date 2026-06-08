"""
algorithms/dijkstra.py — Shortest-path finder (Requirement 2)
==============================================================
Implements Dijkstra's algorithm on the directed weighted flight graph.
Three optimisation criteria are supported:

    distancia  — minimise total distance in km
    tiempo     — minimise total flight time in minutes (per-aircraft rates)
    costo      — minimise total fare in USD (per-aircraft rates, 0 for subsidised)
    combinado  — minimise a normalised blend of all three criteria

Algorithm choice
----------------
Dijkstra is correct for graphs with non-negative edge weights, which is always
the case for airline routes (distance, time, and cost are all ≥ 0).
Complexity: O((V + E) log V) with a binary heap.

Aircraft config override
------------------------
The POST /ruta endpoint lets the user tweak per-km rates for each aircraft type.
Those rates are passed in as ``aeronaves_config`` and forwarded to
``edge.get_aircraft_options(config_override)`` so every weight computation uses
the user-supplied rates without mutating the stored graph state.

Availability filtering
----------------------
Blocked edges (``edge.get_available() == False``) and blocked vertices are
silently skipped during traversal — the graph structure is never modified.
"""
import heapq

from core.edge.edge import normalize_aircraft_name


def dijkstra(
    graph,
    origen: str,
    criterio: str,
    destino: str | None = None,
    excluir_secundarios: bool = False,
    aeronaves_permitidas: list[str] | None = None,
    aeronaves_config: dict | None = None,
) -> tuple[dict, dict]:
    """Run Dijkstra from *origen* and return shortest distances and predecessors.

    Parameters
    ----------
    graph : Directed_Graph
        The in-memory flight network loaded from JSON.
    origen : str
        IATA code of the starting airport.
    criterio : str
        Optimisation criterion: ``"distancia"``, ``"tiempo"``, ``"costo"``, or
        ``"combinado"``.
    destino : str or None
        If provided, the algorithm terminates early once the shortest path to
        *destino* is finalised (early-exit optimisation).  Pass ``None`` to
        compute the full single-source shortest-path tree.
    excluir_secundarios : bool
        When ``True``, intermediate hops through non-hub airports are skipped.
        The destination itself is always kept reachable even if it is not a hub.
    aeronaves_permitidas : list[str] or None
        Restrict the search to edges served by at least one of these aircraft
        types.  ``None`` allows all aircraft.
    aeronaves_config : dict or None
        User-supplied per-aircraft rate overrides forwarded to
        ``edge.get_aircraft_options()``.  ``None`` uses stored defaults.

    Returns
    -------
    distancias : dict[str, float]
        Mapping from IATA code to minimum accumulated weight from *origen*.
        Unreachable nodes have ``float("inf")``.
    previos : dict[str, str | None]
        Predecessor map for path reconstruction.  ``previos[node]`` is the
        IATA code of the node visited immediately before *node* on the
        shortest path, or ``None`` for the origin.

    Raises
    ------
    ValueError
        If *criterio* is not one of the supported values, or if *origen* does
        not exist in the graph.
    """
    criterios_validos = {"distancia", "tiempo", "costo", "combinado"}
    if criterio not in criterios_validos:
        raise ValueError(f"Criterio '{criterio}' inválido. Use: {criterios_validos}")

    try:
        graph.get_vertex(origen)
    except ValueError:
        raise ValueError(f"Aeropuerto origen '{origen}' no existe en el grafo")

    distancias = {v: float("inf") for v in graph.vertices}
    distancias[origen] = 0
    previos = {v: None for v in graph.vertices}

    # heap entries: (accumulated_weight, node_name)
    heap = [(0, origen)]

    while heap:
        costo_actual, nodo_actual = heapq.heappop(heap)

        if costo_actual > distancias[nodo_actual]:
            continue

        vertex = graph.vertices[nodo_actual]

        for edge in vertex.neighbors:
            if not edge.get_available():
                continue

            vecino = edge.get_vertex2().get_name()

            if not graph.vertices[vecino].get_available():
                continue

            if excluir_secundarios and vecino != destino and not graph.vertices[vecino].is_hub():
                continue

            if aeronaves_permitidas and not _edge_has_allowed_aircraft(edge, aeronaves_permitidas):
                continue

            peso = _get_peso(edge, criterio, aeronaves_permitidas, aeronaves_config)
            nuevo_costo = costo_actual + peso

            if nuevo_costo < distancias[vecino]:
                distancias[vecino] = nuevo_costo
                previos[vecino] = nodo_actual
                heapq.heappush(heap, (nuevo_costo, vecino))

    return distancias, previos


def reconstruir_camino(previos: dict, origen: str, destino: str) -> list[str]:
    """Reconstruct the shortest path from the predecessor map.

    Parameters
    ----------
    previos : dict[str, str | None]
        Predecessor map returned by ``dijkstra()``.
    origen : str
        IATA code of the source airport.
    destino : str
        IATA code of the target airport.

    Returns
    -------
    list[str]
        Ordered list of IATA codes from *origen* to *destino* inclusive.
        Returns an empty list if no path exists.
    """
    camino = []
    nodo = destino

    while nodo is not None:
        camino.append(nodo)
        nodo = previos.get(nodo)

    camino.reverse()

    if not camino or camino[0] != origen:
        return []

    return camino


def _edge_has_allowed_aircraft(edge, aeronaves_permitidas: list[str]) -> bool:
    """Return ``True`` if *edge* is served by at least one permitted aircraft."""
    allowed = {normalize_aircraft_name(a) for a in aeronaves_permitidas}
    return any(
        normalize_aircraft_name(a) in allowed
        for a in (edge.get_aeronaves() or ["Avion Comercial"])
    )


def _get_filtered_options(
    edge,
    aeronaves_permitidas: list[str] | None,
    aeronaves_config: dict | None = None,
) -> list[dict]:
    """Return aircraft options for *edge*, filtered to permitted types.

    Passes ``aeronaves_config`` to ``get_aircraft_options`` so user-supplied
    rate overrides are honoured during weight computation.
    """
    options = edge.get_aircraft_options(aeronaves_config) if hasattr(edge, "get_aircraft_options") else []
    if not aeronaves_permitidas:
        return options

    allowed = {normalize_aircraft_name(a) for a in aeronaves_permitidas}
    return [o for o in options if o["nombre_normalizado"] in allowed]


def _get_peso(
    edge,
    criterio: str,
    aeronaves_permitidas: list[str] | None = None,
    aeronaves_config: dict | None = None,
) -> float:
    """Compute the edge weight for the chosen criterion.

    Filters to permitted aircraft first, then picks the minimum value among
    all viable options.  Returns ``float("inf")`` if no viable aircraft exists
    (edge is effectively unreachable under the current filter).

    Criteria
    --------
    distancia  — raw distance in km (independent of aircraft)
    tiempo     — minimum flight time in minutes across viable aircraft
    costo      — minimum fare in USD (0 for subsidised routes)
    combinado  — normalised blend: dist/1000 + time/60 + cost/100
    """
    options = _get_filtered_options(edge, aeronaves_permitidas, aeronaves_config)
    if not options:
        return float("inf")

    if criterio == "distancia":
        return edge.get_distance()
    elif criterio == "tiempo":
        return min(o["tiempo"] for o in options)
    elif criterio == "costo":
        return min(o["costo"] for o in options)
    elif criterio == "combinado":
        return min(
            edge.get_distance() / 1000 + o["tiempo"] / 60 + o["costo"] / 100
            for o in options
        )
    return edge.get_distance()
