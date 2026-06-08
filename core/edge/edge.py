"""
core/edge/edge.py — Base Edge class and aircraft name normalisation
====================================================================
Defines the generic directed ``Edge`` used as a base for ``AirportEdge``.
Also provides two module-level helpers (``normalize_aircraft_name`` and
``normalize_aircraft_config``) that canonicalise aircraft identifiers coming
from either the JSON file or the React frontend, where accented characters
may or may not be present depending on the source.

Aircraft defaults
-----------------
The three aircraft types and their default cost/time rates are defined once
here so both ``Edge`` and ``AirportEdge`` share the same source of truth.

    Aircraft            Cost (USD/km)   Time (min/km)
    ──────────────────  ─────────────   ─────────────
    Avion Comercial         0.18            0.7
    Avion Regional          0.25            1.1
    Helice                  0.12            2.5

Subsidy mechanic
----------------
When ``costo_base == 0.0`` the route is *subsidised*: the base fare is zero.
The advanced planner enforces a global cap — no more than 20 % of the total
distance flown may use subsidised routes.  Subsequent legs on subsidised
routes are charged at the normal per-km rate once the cap is reached.

Availability flag
-----------------
``available`` is set to ``False`` when a route is blocked (Requirement 4 —
network interruptions).  Blocked edges are skipped by all pathfinding
algorithms without being removed from the graph structure, so they can be
re-enabled at any time.
"""

from core.vertex.vertex import Vertex

# ── Aircraft rate tables ──────────────────────────────────────────────────────

AIRCRAFT_DEFAULT: dict[str, dict] = {
    "Avion Comercial": {"costo_km": 0.18, "tiempo_km": 0.7},
    "Avion Regional":  {"costo_km": 0.25, "tiempo_km": 1.1},
    "Helice":          {"costo_km": 0.12, "tiempo_km": 2.5},
}

# Maps every known spelling variant (accented, double-encoded) to the
# canonical ASCII key used in AIRCRAFT_DEFAULT.
AIRCRAFT_ALIASES: dict[str, str] = {
    "Avion Comercial":   "Avion Comercial",
    "Avion Regional":    "Avion Regional",
    "Helice":            "Helice",
    "Avión Comercial":   "Avion Comercial",
    "Avión Regional":    "Avion Regional",
    "Hélice":            "Helice",
    "AviÃ³n Comercial":  "Avion Comercial",
    "AviÃ³n Regional":   "Avion Regional",
    "HÃ©lice":           "Helice",
}


def normalize_aircraft_name(name: str) -> str:
    """Return the canonical ASCII key for an aircraft name.

    Handles accented characters (``Avión``, ``Hélice``) and double-encoded
    UTF-8 variants that can appear when the JSON is parsed on some systems.
    Falls back to the original string if no alias is found.

    Parameters
    ----------
    name : str
        Aircraft name as it appears in the JSON or in a frontend request.

    Returns
    -------
    str
        Normalised key matching one of the entries in ``AIRCRAFT_DEFAULT``.
    """
    return AIRCRAFT_ALIASES.get(name, name)


def normalize_aircraft_config(config: dict | None) -> dict:
    """Merge a user-supplied aircraft config override with the defaults.

    Accepts keys in either camelCase (``costoKm`` / ``tiempoKm``, as sent by
    the React frontend) or snake_case (``costo_km`` / ``tiempo_km``).  Any
    aircraft name variant is normalised before merging so the caller does not
    need to worry about encoding.

    Parameters
    ----------
    config : dict or None
        Mapping of ``{ aircraft_name: { costoKm, tiempoKm } }``.
        Pass ``None`` to obtain a clean copy of the defaults.

    Returns
    -------
    dict
        Normalised config dict with canonical aircraft keys and snake_case
        rate fields, ready for use by ``get_aircraft_options()``.
    """
    normalized = {name: values.copy() for name, values in AIRCRAFT_DEFAULT.items()}
    for name, values in (config or {}).items():
        norm_name = normalize_aircraft_name(name)
        previous = normalized.get(norm_name, {})
        normalized[norm_name] = {
            "costo_km": values.get("costoKm", values.get("costo_km", previous.get("costo_km", 0))),
            "tiempo_km": values.get("tiempoKm", values.get("tiempo_km", previous.get("tiempo_km", 0))),
        }
    return normalized


# ── Base Edge ─────────────────────────────────────────────────────────────────

class Edge:
    """Directed weighted edge between two vertices.

    ``AirportEdge`` extends this class and overrides ``get_aircraft_options``
    with a richer implementation that supports per-edge aircraft lists and
    the subsidy cap.  This base class provides a simpler version that works
    with the generic ``Vertex``.

    Parameters
    ----------
    vertex1 : Vertex
        Origin vertex.
    vertex2 : Vertex
        Destination vertex.
    distance : float
        Route distance in kilometres.  Must be ≥ 0.
    time : float
        Legacy static flight time in minutes.  Superseded by the per-aircraft
        ``tiempo_km × distance`` calculation in most algorithms.
    cost : float
        Legacy static cost in USD.  Superseded by ``costo_km × distance``.
    """

    def __init__(self, vertex1: Vertex, vertex2: Vertex,
                 distance: float = 0, time: float = 0, cost: float = 0):
        if vertex1 is None:
            raise ValueError("Origin vertex not found in graph")
        if vertex2 is None:
            raise ValueError("Destination vertex not found in graph")
        if distance < 0:
            raise ValueError("Distance must be non-negative")
        if time < 0:
            raise ValueError("Time must be non-negative")
        if cost < 0:
            raise ValueError("Cost must be non-negative")

        self.vertex1 = vertex1
        self.vertex2 = vertex2
        self.distance = distance
        self.time = time
        self.cost = cost

        # ── Flight-network fields (populated via load_from_dict) ──────────────
        self.aeronaves: list[str] = []   # aircraft types operating this route
        self.costo_base: float = -1.0    # 0.0 = subsidised, -1.0 = normal
        self.estancia_minima: int = 0    # minimum layover in minutes
        self.available: bool = True      # False = route blocked (R4)
        self.aircraft_config: dict = normalize_aircraft_config(None)

    # ── Accessors ─────────────────────────────────────────────────────────────

    def get_vertex1(self) -> Vertex:
        """Return the origin vertex."""
        return self.vertex1

    def get_vertex2(self) -> Vertex:
        """Return the destination vertex."""
        return self.vertex2

    def get_time(self) -> float:
        """Return the static time weight (legacy; prefer per-aircraft calc)."""
        return self.time

    def get_distance(self) -> float:
        """Return the route distance in kilometres."""
        return self.distance

    def get_cost(self) -> float:
        """Return the static cost weight (legacy; prefer per-aircraft calc)."""
        return self.cost

    def get_aeronaves(self) -> list[str]:
        """Return the list of aircraft type names for this route."""
        return self.aeronaves

    def get_costo_base(self) -> float:
        """Return the base cost flag (0.0 = subsidised, -1.0 = normal)."""
        return self.costo_base

    def is_subsidiada(self) -> bool:
        """Return ``True`` if this is a zero-cost subsidised route."""
        return self.costo_base == 0.0

    def get_estancia_minima(self) -> int:
        """Return the minimum layover time in minutes required at the destination."""
        return self.estancia_minima

    def is_available(self) -> bool:
        """Return ``True`` if the route is currently unblocked."""
        return self.available

    def set_available(self, available: bool) -> None:
        """Block (``False``) or unblock (``True``) this route.

        Called by the network-interruption endpoint (Requirement 4).  The
        edge remains in the graph; pathfinding algorithms skip it when
        ``available`` is ``False``.
        """
        self.available = available

    # ── Aircraft options ──────────────────────────────────────────────────────

    def get_aircraft_options(self) -> list[dict]:
        """Return cost and time options for each aircraft type on this route.

        Each item in the returned list has the keys:
        ``nombre``, ``nombre_normalizado``, ``costo_km``, ``tiempo_km``,
        ``costo`` (total for this leg), ``tiempo`` (total for this leg).
        Cost is 0 for subsidised routes.
        """
        aircraft_names = self.aeronaves or ["Avion Comercial"]
        options = []
        for aircraft in aircraft_names:
            norm = normalize_aircraft_name(aircraft)
            config = self.aircraft_config.get(norm, AIRCRAFT_DEFAULT["Avion Comercial"])
            cost = 0 if self.is_subsidiada() else round(self.distance * config["costo_km"], 2)
            time = round(self.distance * config["tiempo_km"], 1)
            options.append({
                "nombre": aircraft,
                "nombre_normalizado": norm,
                "costo_km": config["costo_km"],
                "tiempo_km": config["tiempo_km"],
                "costo": cost,
                "tiempo": time,
            })
        return options

    def get_best_aircraft_option(self, criterion: str = "costo") -> dict:
        """Return the best aircraft option for a given optimisation criterion.

        Parameters
        ----------
        criterion : str
            ``"costo"`` (default) or ``"tiempo"``.
        """
        options = self.get_aircraft_options()
        if criterion == "tiempo":
            return min(options, key=lambda o: (o["tiempo"], o["costo"]))
        return min(options, key=lambda o: (o["costo"], o["tiempo"]))

    def calculate_cost(self, aircraft: str | None = None) -> float:
        """Calculate the flight cost for this leg.

        Uses the static ``self.cost`` if set, otherwise delegates to the
        per-aircraft config.
        """
        if self.cost > 0:
            return self.cost
        if aircraft:
            return self._get_aircraft_option(aircraft)["costo"]
        return self.get_best_aircraft_option("costo")["costo"]

    def calculate_time(self, aircraft: str | None = None) -> float:
        """Calculate the flight time for this leg in minutes."""
        if self.time > 0:
            return self.time
        if aircraft:
            return self._get_aircraft_option(aircraft)["tiempo"]
        return self.get_best_aircraft_option("tiempo")["tiempo"]

    def _get_aircraft_option(self, aircraft: str) -> dict:
        """Return the option dict for a specific aircraft type.

        Raises ``ValueError`` if the aircraft does not operate on this route.
        """
        norm = normalize_aircraft_name(aircraft)
        for option in self.get_aircraft_options():
            if option["nombre_normalizado"] == norm:
                return option
        raise ValueError(f"Aircraft '{aircraft}' is not available for this route")

    # ── JSON loader ───────────────────────────────────────────────────────────

    def load_from_dict(self, data: dict, aircraft_config: dict | None = None) -> None:
        """Populate flight-network fields from a JSON edge dictionary.

        Parameters
        ----------
        data : dict
            Edge entry from the network JSON.  Expected keys:
            ``aeronaves``, ``costoBase``, ``estanciaMinima``.
        aircraft_config : dict or None
            Optional global aircraft rate overrides (from the UI config form).
            Merged with defaults via ``normalize_aircraft_config``.
        """
        self.aeronaves = data.get("aeronaves", [])
        self.costo_base = data.get("costoBase", -1.0)
        self.estancia_minima = data.get("estanciaMinima", 0)
        self.aircraft_config = normalize_aircraft_config(aircraft_config)

    def __str__(self) -> str:
        return f"{self.vertex1.get_name()} --{self.distance}--> {self.vertex2.get_name()}"
