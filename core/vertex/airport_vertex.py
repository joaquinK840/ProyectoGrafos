"""
core/vertex/airport_vertex.py — Airport domain vertex
======================================================
Extends the generic ``Vertex`` with all data that describes a real airport
in the flight-network JSON.  Every node loaded from the JSON file is an
instance of this class.

JSON fields mapped to this class
----------------------------------
iata_id            → ``name`` (inherited) and ``nombre`` display name
ciudad / pais      → geographic metadata shown in the UI detail panel
zona_horaria       → timezone string (e.g. ``"America/Bogota"``)
es_hub             → ``True`` for major hub airports; affects visual style
                     and is optionally used to filter secondary airports out
                     of route queries
costo_alojamiento  → nightly lodging cost in USD, charged automatically by
                     the advanced planning engine every 20 h
costo_alimentacion → meal cost in USD, charged every 8 h (origin airport if
                     the threshold is crossed mid-flight)
actividades        → list of activity dicts (name, type, duration_min, cost)
trabajos           → list of temporary job dicts (name, tarifa_hora, max_horas)
aerolineas         → list of airline name strings operating from this airport
"""

from core.vertex.vertex import Vertex


class AirportVertex(Vertex):
    """Graph vertex representing a single airport.

    Inherits the adjacency list (``neighbors``) and availability flag from
    ``Vertex``.  Adds all domain fields required by the planning algorithms
    and the REST API serialisers.

    Parameters
    ----------
    iata_id : str
        Three-letter IATA code used as the unique vertex key (e.g. ``"BOG"``).
    nombre : str
        Full display name of the airport (e.g. ``"El Dorado International"``).
    ciudad : str
        City where the airport is located.
    pais : str
        Country where the airport is located.
    zona_horaria : str
        IANA timezone identifier (e.g. ``"America/Bogota"``).
    es_hub : bool
        ``True`` if the airport is a major hub.  Hub airports are styled
        differently in the UI and may be required when the user enables the
        "exclude secondary airports" filter.
    costo_alojamiento : float
        Nightly lodging cost in USD.  The advanced planner charges this
        automatically every 20 hours of elapsed travel time.
    costo_alimentacion : float
        Meal cost in USD.  Charged every 8 hours; if the 8-hour window closes
        during a flight, the cost is taken from the *origin* airport.
    actividades : list[dict]
        Optional activities available at this airport.  Each dict contains at
        minimum ``nombre``, ``tipo`` (``"obligatoria"`` | ``"opcional"``),
        ``duracion_min``, and ``costo_usd``.
    trabajos : list[dict]
        Temporary jobs available when the traveler's budget falls below 35 %
        of the initial amount.  Each dict contains ``nombre``,
        ``tarifa_hora``, and ``max_horas``.
    aerolineas : list[str]
        Airlines operating flights from this airport.
    """

    def __init__(
        self,
        iata_id: str,
        nombre: str = "",
        ciudad: str = "",
        pais: str = "",
        zona_horaria: str = "",
        es_hub: bool = False,
        costo_alojamiento: float = 0.0,
        costo_alimentacion: float = 0.0,
        actividades: list = None,
        trabajos: list = None,
        aerolineas: list = None,
    ):
        super().__init__(name=iata_id)
        self.nombre = nombre
        self.ciudad = ciudad
        self.pais = pais
        self.zona_horaria = zona_horaria
        self.es_hub = es_hub
        self.costo_alojamiento = costo_alojamiento
        self.costo_alimentacion = costo_alimentacion
        self.actividades = actividades if actividades is not None else []
        self.trabajos = trabajos if trabajos is not None else []
        self.aerolineas = aerolineas if aerolineas is not None else []

    # ── Accessors ─────────────────────────────────────────────────────────────

    def get_ciudad(self) -> str:
        """Return the city name."""
        return self.ciudad

    def get_pais(self) -> str:
        """Return the country name."""
        return self.pais

    def get_es_hub(self) -> bool:
        """Return ``True`` if this is a hub airport."""
        return self.es_hub

    def is_hub(self) -> bool:
        """Alias for ``get_es_hub()``."""
        return self.es_hub

    def get_nombre_completo(self) -> str:
        """Return the full display name of the airport."""
        return self.nombre

    def get_zona_horaria(self) -> str:
        """Return the IANA timezone identifier."""
        return self.zona_horaria

    def get_aerolineas(self) -> list:
        """Return the list of airline names operating from this airport."""
        return self.aerolineas

    def get_costo_alojamiento(self) -> float:
        """Return the nightly lodging cost in USD."""
        return self.costo_alojamiento

    def get_costo_alimentacion(self) -> float:
        """Return the per-meal food cost in USD."""
        return self.costo_alimentacion

    def get_actividades(self) -> list:
        """Return all activities (mandatory and optional) at this airport."""
        return self.actividades

    def get_trabajos(self) -> list:
        """Return the list of temporary jobs available at this airport."""
        return self.trabajos

    def __repr__(self) -> str:
        hub_tag = " [HUB]" if self.es_hub else ""
        return f"AirportVertex({self.get_name()}{hub_tag} - {self.ciudad}, {self.pais})"
