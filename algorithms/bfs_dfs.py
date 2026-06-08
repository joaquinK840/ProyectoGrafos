"""
algorithms/bfs_dfs.py — Maximum-destinations DFS planner (Requirement 3)
=========================================================================
Implements the basic trip-planning algorithm that answers the question:
*"Starting from airport X with a given budget and time limit, which route
visits the most destinations without violating any constraint?"*

Algorithm choice
----------------
DFS with backtracking is used instead of BFS or Dijkstra because the goal is
to **maximise destinations visited**, not to minimise a single-path weight.
BFS finds the shortest path in hops, not the deepest itinerary.  Dijkstra
minimises accumulated cost, which can cause it to skip long but affordable
detours.  DFS explores every possible ordering of airports and keeps the best
found so far, pruning branches early when any constraint is already violated.

Complexity: O(V!) in the worst case, but the budget and time constraints
prune the search tree heavily in practice, making it tractable for the
10–15 airport networks used in this project.

Two-alternative output
----------------------
``planificacion_basica`` runs two independent DFS searches and returns both:

- ``alternativa_presupuesto`` — optimise for fewest dollars spent on ties
  (maximise destinations first, break ties by lowest cost).
- ``alternativa_tiempo`` — optimise for least time spent on ties
  (maximise destinations first, break ties by lowest total minutes).

Aircraft filtering
------------------
When ``aeronaves_permitidas`` is provided, edges not served by at least one
allowed aircraft type are skipped.  The ``required_aircraft`` set additionally
enforces that *every* permitted aircraft type must be used at least once in
the itinerary (the ``aircraft_coverage`` internal flag tracks this during DFS).
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
    """Return two itinerary alternatives for the basic trip planner (R3).

    Runs two DFS passes — one optimised for cost, one for time — and returns
    both results together with the input parameters for the UI to display.

    Parameters
    ----------
    graph : Directed_Graph
        The in-memory flight network.
    origen : str
        IATA code of the departure airport.
    presupuesto : float
        Maximum trip budget in USD.  Legs that would exceed this are pruned.
    tiempo_disponible : float
        Maximum trip time in minutes.  Legs that would exceed this are pruned.
    excluir_secundarios : bool
        When ``True``, non-hub airports are skipped as intermediate stops.
    aeronaves_permitidas : list[str] or None
        If provided, only edges served by at least one of these aircraft types
        are considered.  Each type must also be used at least once.

    Returns
    -------
    dict
        ``origen``, ``presupuesto``, ``tiempo_disponible_min``,
        ``excluir_secundarios``, ``aeronaves_permitidas``,
        ``alternativa_presupuesto`` (cost-optimised itinerary),
        ``alternativa_tiempo`` (time-optimised itinerary).

    Raises
    ------
    ValueError
        If *origen* does not exist in the graph.
    """
    if origen not in graph.vertices:
        raise ValueError(f"Aeropuerto '{origen}' no existe en el grafo")

    allowed_aircraft = _normalize_allowed_aircraft(aeronaves_permitidas)
    required_aircraft_raw = set(aeronaves_permitidas) if aeronaves_permitidas else set()

    return {
        "origen": origen,
        "presupuesto": presupuesto,
        "tiempo_disponible_min": tiempo_disponible,
        "excluir_secundarios": excluir_secundarios,
        "aeronaves_permitidas": aeronaves_permitidas or [],
        "alternativa_presupuesto": _buscar_mejor_itinerario(
            graph, origen, presupuesto, tiempo_disponible,
            excluir_secundarios, allowed_aircraft, "costo", required_aircraft_raw,
        ),
        "alternativa_tiempo": _buscar_mejor_itinerario(
            graph, origen, presupuesto, tiempo_disponible,
            excluir_secundarios, allowed_aircraft, "tiempo", required_aircraft_raw,
        ),
    }


def _buscar_mejor_itinerario(
    graph,
    origen,
    presupuesto,
    tiempo_disponible,
    excluir_secundarios,
    allowed_aircraft,
    objetivo,
    required_aircraft: set | None = None,
):
    """Run a single DFS pass and return the best itinerary for *objetivo*.

    Uses backtracking: the DFS explores all reachable orderings of airports,
    pruning any branch that would exceed budget or time.  At each node the
    current partial itinerary is compared against the running best.

    Parameters
    ----------
    objetivo : str
        ``"costo"`` or ``"tiempo"`` — determines tie-breaking and aircraft
        selection within each leg.
    required_aircraft : set or None
        Raw (unormalised) aircraft names that must each be used at least once.
        Itineraries that do not satisfy this coverage rule are never promoted to
        the running best.
    """
    mejor = _empty_itinerary(objetivo, origen)
    _required = required_aircraft or set()

    def _all_aircraft_used(used: set) -> bool:
        """Return True when every required aircraft type appears in *used*."""
        if not _required:
            return True
        return all(
            any(normalize_aircraft_name(req) == normalize_aircraft_name(u) for u in used)
            for req in _required
        )

    def _dfs(nodo_actual, visitados, camino, tramos, costo_acum, tiempo_acum, used_aircraft):
        candidato = {
            "criterio": objetivo,
            "camino": list(camino),
            "tramos": list(tramos),
            "costo_total": round(costo_acum, 2),
            "tiempo_total": round(tiempo_acum, 1),
            "destinos": len(camino) - 1,
            "aircraft_coverage": _all_aircraft_used(used_aircraft),
        }
        if _is_better_itinerary(candidato, mejor, objetivo):
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

            option = _select_aircraft_option(edge, objetivo, allowed_aircraft)
            if option is None:
                continue

            costo_tramo = edge.calculate_cost(option["nombre"])
            tiempo_tramo = edge.calculate_time(option["nombre"])
            nuevo_costo = costo_acum + costo_tramo
            nuevo_tiempo = tiempo_acum + tiempo_tramo

            # Prune: constraint already violated — no point exploring deeper.
            if nuevo_costo > presupuesto or nuevo_tiempo > tiempo_disponible:
                continue

            tramo = {
                "origen": nodo_actual,
                "destino": vecino,
                "aeronave": option["nombre"],
                "distancia_km": edge.get_distance(),
                "costo_tramo": round(costo_tramo, 2),
                "costo_acumulado": round(nuevo_costo, 2),
                "tiempo_tramo": round(tiempo_tramo, 1),
                "tiempo_acumulado": round(nuevo_tiempo, 1),
            }

            visitados.add(vecino)
            camino.append(vecino)
            tramos.append(tramo)
            _dfs(vecino, visitados, camino, tramos, nuevo_costo, nuevo_tiempo,
                 used_aircraft | {option["nombre"]})
            tramos.pop()
            camino.pop()
            visitados.remove(vecino)

    _dfs(origen, {origen}, [origen], [], 0, 0, set())
    mejor.pop("aircraft_coverage", None)
    return mejor


def dfs_mayor_destinos(
    graph,
    origen: str,
    presupuesto: float,
    tiempo_disponible: float,
    criterio: str = "costo",
    excluir_secundarios: bool = False,
) -> dict:
    """Simplified DFS that maximises destinations (legacy, single-alternative).

    Equivalent to running one pass of ``planificacion_basica`` without
    aircraft-type filtering.  Still used internally and exposed via the API
    for backwards compatibility.

    Parameters
    ----------
    graph : Directed_Graph
        In-memory flight network.
    origen : str
        IATA code of the departure airport.
    presupuesto : float
        Maximum budget in USD.
    tiempo_disponible : float
        Maximum trip time in minutes.
    criterio : str
        ``"costo"`` or ``"tiempo"`` — determines which aircraft option is
        chosen per leg (cheapest or fastest).
    excluir_secundarios : bool
        Skip non-hub intermediate airports when ``True``.

    Returns
    -------
    dict
        ``camino``, ``costo_total``, ``tiempo_total``, ``destinos``.

    Raises
    ------
    ValueError
        If *origen* does not exist in the graph.
    """
    mejor = {"camino": [], "costo_total": 0, "tiempo_total": 0, "destinos": 0}

    def _dfs(nodo_actual, visitados, camino, costo_acum, tiempo_acum):
        destinos_actuales = len(camino) - 1
        if destinos_actuales > mejor["destinos"]:
            mejor["camino"] = list(camino)
            mejor["costo_total"] = costo_acum
            mejor["tiempo_total"] = tiempo_acum
            mejor["destinos"] = destinos_actuales

        vertex = graph.vertices[nodo_actual]

        for edge in vertex.neighbors:
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

            option = edge.get_best_aircraft_option("tiempo" if criterio == "tiempo" else "costo")
            costo_tramo = edge.calculate_cost(option["nombre"])
            tiempo_tramo = edge.calculate_time(option["nombre"])

            if costo_acum + costo_tramo > presupuesto:
                continue
            if tiempo_acum + tiempo_tramo > tiempo_disponible:
                continue

            visitados.add(vecino)
            camino.append(vecino)
            _dfs(vecino, visitados, camino, costo_acum + costo_tramo, tiempo_acum + tiempo_tramo)
            camino.pop()
            visitados.remove(vecino)

    if origen not in graph.vertices:
        raise ValueError(f"Aeropuerto '{origen}' no existe en el grafo")

    _dfs(origen, {origen}, [origen], 0, 0)
    return mejor


# ── Private helpers ───────────────────────────────────────────────────────────

def _normalize_allowed_aircraft(aircraft_names):
    """Return a set of normalised aircraft names, or ``None`` if the input is empty."""
    if not aircraft_names:
        return None
    normalized = {
        normalize_aircraft_name(name.strip())
        for name in aircraft_names
        if name and name.strip()
    }
    return normalized or None


def _select_aircraft_option(edge, objective, allowed_aircraft):
    """Return the best aircraft option for *edge*, filtered to *allowed_aircraft*.

    Returns ``None`` if no allowed aircraft operates on this route.
    """
    options = edge.get_aircraft_options()
    if allowed_aircraft is not None:
        options = [o for o in options if o["nombre_normalizado"] in allowed_aircraft]
    if not options:
        return None
    if objective == "tiempo":
        return min(options, key=lambda o: (o["tiempo"], o["costo"]))
    return min(options, key=lambda o: (o["costo"], o["tiempo"]))


def _empty_itinerary(criterion, origin):
    """Return a zero-value itinerary dict used as the initial running best."""
    return {
        "criterio": criterion,
        "camino": [origin],
        "tramos": [],
        "costo_total": 0,
        "tiempo_total": 0,
        "destinos": 0,
    }


def _is_better_itinerary(candidate, current, objective):
    """Return ``True`` if *candidate* is strictly better than *current*.

    Primary key: more destinations visited.
    Tiebreaker: lower cost (``"costo"``) or lower time (``"tiempo"``).
    Itineraries that do not satisfy the required-aircraft coverage rule
    (``aircraft_coverage == False``) are never promoted over ones that do.
    """
    cand_covered = candidate.get("aircraft_coverage", True)
    curr_covered = current.get("aircraft_coverage", True)

    if cand_covered != curr_covered:
        return cand_covered

    if candidate["destinos"] != current["destinos"]:
        return candidate["destinos"] > current["destinos"]

    if objective == "tiempo":
        return (candidate["tiempo_total"], candidate["costo_total"]) < \
               (current["tiempo_total"], current["costo_total"])
    return (candidate["costo_total"], candidate["tiempo_total"]) < \
           (current["costo_total"], current["tiempo_total"])
