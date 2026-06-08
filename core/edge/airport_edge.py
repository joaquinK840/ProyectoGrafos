from core.edge.edge import Edge

# Valores por defecto del PDF (pueden sobreescribirse desde el JSON)
AIRCRAFT_DEFAULTS = {
    "Avión Comercial": {"costo_km": 0.18, "tiempo_km": 0.7},
    "Avión Regional":  {"costo_km": 0.25, "tiempo_km": 1.1},
    "Hélice":          {"costo_km": 0.12, "tiempo_km": 2.5},
}


class AirportEdge(Edge):
    """
    Extends the generic Edge with airport route-specific fields.
    Follows OCP: Edge is not modified, only extended.
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

    # ── Dominio ──────────────────────────────────────────────────────

    def is_subsidiada(self) -> bool:
        return self.costo_base == 0

    def get_distancia_km(self) -> float:
        return self.distancia_km

    def get_aeronaves(self) -> list:
        return self.aeronaves

    def get_estancia_minima(self) -> int:
        return self.estancia_minima

    def calcular_costo(self, tipo_aeronave: str) -> float:
        if self.is_subsidiada():
            return 0.0
        config = self.aircraft_config.get(
            tipo_aeronave, AIRCRAFT_DEFAULTS.get(tipo_aeronave, {})
        )
        return round(self.distancia_km * config.get("costo_km", 0.18), 2)

    def calcular_tiempo(self, tipo_aeronave: str) -> float:
        config = self.aircraft_config.get(
            tipo_aeronave, AIRCRAFT_DEFAULTS.get(tipo_aeronave, {})
        )
        return round(self.distancia_km * config.get("tiempo_km", 0.7), 2)

    # ── Métodos que llaman los algoritmos (R2/R3) ────────────────────

    def get_aircraft_options(self, config_override: dict | None = None) -> list:
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
        """
        Busca una aeronave específica por nombre.
        Lo llama simular_decision_vuelo() en planificacion_avanzada.py.
        Lanza ValueError si la aeronave no está disponible en esta ruta.
        """
        for option in self.get_aircraft_options():
            if option["nombre"] == aeronave or option["nombre_normalizado"] == aeronave:
                return option
        raise ValueError(
            f"Aeronave '{aeronave}' no disponible en ruta "
            f"{self.vertex1.get_name()} → {self.vertex2.get_name()}"
        )

    def get_best_aircraft_option(self, criterion: str = "costo") -> dict:
        """
        Retorna la opción óptima según el criterio.
        Lo llama dfs_mayor_destinos() en bfs_dfs.py.
        """
        options = self.get_aircraft_options()
        if criterion == "tiempo":
            return min(options, key=lambda o: (o["tiempo"], o["costo"]))
        return min(options, key=lambda o: (o["costo"], o["tiempo"]))

    # ── Alias de disponibilidad ──────────────────────────────────────

    def get_available(self) -> bool:
        """Alias de is_available() — lo llama dijkstra.py."""
        return self.available

    # ── Compatibilidad con get_opciones_aeronave() (interfaz anterior) ──

    def get_opciones_aeronave(self) -> list:
        """
        Formato legado { tipo, costo_usd, tiempo_min }.
        Mantenido para no romper código existente que lo use.
        """
        return [
            {
                "tipo": o["nombre"],
                "costo_usd": o["costo"],
                "tiempo_min": o["tiempo"],
            }
            for o in self.get_aircraft_options()
        ]