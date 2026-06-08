"""
core/edge/airport_edge.py — Airport-specific directed edge
===========================================================
Extends ``Edge`` with the full set of airport-route fields loaded from the
network JSON.  Every edge in the flight graph is an instance of this class.

Design note
-----------
``AirportEdge`` follows the Open/Closed Principle: ``Edge`` is not modified,
only extended.  The key addition is an upgraded ``get_aircraft_options()`` that
accepts an optional ``config_override`` dict so the POST /ruta endpoint can
compute costs with user-supplied per-km rates without mutating stored state.

Subsidy mechanic
----------------
When ``costo_base == 0`` the route is considered *subsidised*.  ``calcular_costo``
and ``get_aircraft_options`` both return ``0.0`` for subsidised legs regardless
of aircraft type.  The advanced planner enforces the global 20 % distance cap on
subsidised routes (see planificacion_avanzada.py).

Accented aircraft names
-----------------------
``AIRCRAFT_DEFAULTS`` here uses the accented Spanish spellings as they appear in
some older JSON files.  ``get_aircraft_options`` normalises every name through
``normalize_aircraft_name()`` before looking up rates so both spellings work.
"""

from core.edge.edge import Edge

# Fallback rates for JSON files that use the accented key spellings.
# These mirror AIRCRAFT_DEFAULT in edge.py — kept here so this module is
# self-contained when loaded before edge.py finishes importing.
AIRCRAFT_DEFAULTS = {
    "Avión Comercial": {"costo_km": 0.18, "tiempo_km": 0.7},
    "Avión Regional":  {"costo_km": 0.25, "tiempo_km": 1.1},
    "Hélice":          {"costo_km": 0.12, "tiempo_km": 2.5},
}


class AirportEdge(Edge):
    """Directed weighted edge representing a single airline route.

    Extends the generic ``Edge`` with airport-route domain fields and a richer
    ``get_aircraft_options()`` that supports runtime config overrides.

    Parameters
    ----------
    vertex1 : AirportVertex
        Origin airport vertex.
    vertex2 : AirportVertex
        Destination airport vertex.
    distancia_km : float
        Route distance in kilometres.
    aeronaves : list[str]
        Aircraft types that operate this route (e.g. ``["Avión Comercial"]``).
        Falls back to ``["Avion Comercial"]`` if empty.
    costo_base : float
        ``0.0`` marks the route as subsidised (zero fare).  ``-1.0`` means a
        normal paid route.  Any other positive value is an explicit fixed cost
        (unused in the current dataset but supported by the schema).
    estancia_minima : int
        Minimum layover in minutes required at the destination before the next
        departure is allowed.
    aircraft_config : dict or None
        Per-aircraft rate overrides ``{ name: { costo_km, tiempo_km } }``.
        Defaults to ``AIRCRAFT_DEFAULTS`` when ``None``.
    """

    def __init__(
        self,
        vertex1,
        vertex2,
        distancia_km: float = 0.0,
        aeronaves: list = None,
        costo_base: float = -1.0,
        estancia_minima: int = 0,
        aircraft_config: dict = None,
    ):
        super().__init__(vertex1, vertex2, distance=distancia_km, time=0.0, cost=0.0)

        self.distancia_km = distancia_km
        self.aeronaves = aeronaves if aeronaves is not None else []
        self.costo_base = costo_base
        self.estancia_minima = estancia_minima
        self.aircraft_config = aircraft_config or AIRCRAFT_DEFAULTS

    # ── Domain helpers ────────────────────────────────────────────────────────

    def is_subsidiada(self) -> bool:
        """Return ``True`` if this is a zero-cost subsidised route."""
        return self.costo_base == 0

    def get_distancia_km(self) -> float:
        """Return the route distance in kilometres."""
        return self.distancia_km

    def get_aeronaves(self) -> list:
        """Return the aircraft types that operate this route."""
        return self.aeronaves

    def get_estancia_minima(self) -> int:
        """Return the minimum required layover in minutes."""
        return self.estancia_minima

    def calcular_costo(self, tipo_aeronave: str) -> float:
        """Compute the one-way flight cost for a given aircraft type.

        Returns ``0.0`` for subsidised routes.  Falls back to the commercial
        default rate (0.18 USD/km) if the aircraft type is not found in either
        the instance config or ``AIRCRAFT_DEFAULTS``.

        Parameters
        ----------
        tipo_aeronave : str
            Aircraft type name (accented or ASCII spellings both accepted).
        """
        if self.is_subsidiada():
            return 0.0
        config = self.aircraft_config.get(
            tipo_aeronave, AIRCRAFT_DEFAULTS.get(tipo_aeronave, {})
        )
        return round(self.distancia_km * config.get("costo_km", 0.18), 2)

    def calcular_tiempo(self, tipo_aeronave: str) -> float:
        """Compute the one-way flight time in minutes for a given aircraft type.

        Falls back to the commercial default rate (0.7 min/km) if the aircraft
        is not found in any config dict.

        Parameters
        ----------
        tipo_aeronave : str
            Aircraft type name (accented or ASCII spellings both accepted).
        """
        config = self.aircraft_config.get(
            tipo_aeronave, AIRCRAFT_DEFAULTS.get(tipo_aeronave, {})
        )
        return round(self.distancia_km * config.get("tiempo_km", 0.7), 2)

    # ── Algorithm-facing methods (Req 2 / Req 3) ─────────────────────────────

    def get_aircraft_options(self, config_override: dict | None = None) -> list:
        """Return cost and time for each aircraft type that operates this route.

        Used by Dijkstra (R2), DFS planner (R3), and the advanced planner (R4)
        to enumerate route options.  The ``config_override`` parameter allows
        the POST /ruta endpoint to substitute user-specified per-km rates
        without permanently mutating the stored ``aircraft_config``.

        Parameters
        ----------
        config_override : dict or None
            Mapping ``{ aircraft_name: { costo_km, tiempo_km } }`` supplied by
            the caller.  When provided it fully replaces the instance config for
            this call only.  Pass ``None`` to use the stored rates.

        Returns
        -------
        list[dict]
            One dict per aircraft with keys:
            ``nombre``, ``nombre_normalizado``, ``costo_km``, ``tiempo_km``,
            ``costo`` (total leg cost, 0 if subsidised), ``tiempo`` (total leg
            time in minutes).
        """
        from core.edge.edge import normalize_aircraft_name

        effective_config = config_override if config_override is not None else self.aircraft_config
        aeronaves = self.aeronaves if self.aeronaves else ["Avion Comercial"]
        options = []
        for nombre in aeronaves:
            nombre_norm = normalize_aircraft_name(nombre)
            config = effective_config.get(
                nombre_norm, AIRCRAFT_DEFAULTS.get(nombre_norm, {"costo_km": 0.18, "tiempo_km": 0.7})
            )
            costo_km = config.get("costo_km", 0.18)
            tiempo_km = config.get("tiempo_km", 0.7)
            options.append({
                "nombre": nombre,
                "nombre_normalizado": nombre_norm,
                "costo_km": costo_km,
                "tiempo_km": tiempo_km,
                "costo": 0.0 if self.is_subsidiada() else round(self.distancia_km * costo_km, 2),
                "tiempo": round(self.distancia_km * tiempo_km, 1),
            })
        return options

    def _get_aircraft_option(self, aeronave: str) -> dict:
        """Return the option dict for a specific aircraft type.

        Called by ``simular_decision_vuelo()`` in planificacion_avanzada.py to
        resolve the exact cost/time for a user-selected aircraft.

        Parameters
        ----------
        aeronave : str
            Aircraft name or normalised key.

        Raises
        ------
        ValueError
            If the aircraft does not operate on this route.
        """
        for option in self.get_aircraft_options():
            if option["nombre"] == aeronave or option["nombre_normalizado"] == aeronave:
                return option
        raise ValueError(
            f"Aeronave '{aeronave}' no disponible en ruta "
            f"{self.vertex1.get_name()} → {self.vertex2.get_name()}"
        )

    def get_best_aircraft_option(self, criterion: str = "costo") -> dict:
        """Return the cheapest (or fastest) aircraft option for this route.

        Called by ``dfs_mayor_destinos()`` in bfs_dfs.py when it needs the
        optimal leg cost without specifying an aircraft.

        Parameters
        ----------
        criterion : str
            ``"costo"`` (default) minimises cost then time as tiebreaker.
            ``"tiempo"`` minimises time then cost.
        """
        options = self.get_aircraft_options()
        if criterion == "tiempo":
            return min(options, key=lambda o: (o["tiempo"], o["costo"]))
        return min(options, key=lambda o: (o["costo"], o["tiempo"]))

    # ── Availability alias ────────────────────────────────────────────────────

    def get_available(self) -> bool:
        """Alias for ``is_available()`` — called by dijkstra.py."""
        return self.available

    # ── Legacy interface ──────────────────────────────────────────────────────

    def get_opciones_aeronave(self) -> list:
        """Return aircraft options in the legacy ``{ tipo, costo_usd, tiempo_min }`` format.

        Kept for backwards compatibility with any code that predates the unified
        ``get_aircraft_options()`` interface.
        """
        return [
            {
                "tipo": o["nombre"],
                "costo_usd": o["costo"],
                "tiempo_min": o["tiempo"],
            }
            for o in self.get_aircraft_options()
        ]
