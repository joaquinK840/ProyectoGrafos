from core.vertex.vertex import Vertex


DEFAULT_AIRCRAFT_CONFIG = {
    "Avion Comercial": {"costo_km": 0.18, "tiempo_km": 0.7},
    "Avion Regional": {"costo_km": 0.25, "tiempo_km": 1.1},
    "Helice": {"costo_km": 0.12, "tiempo_km": 2.5},
}

AIRCRAFT_ALIASES = {
    "Avion Comercial": "Avion Comercial",
    "Avion Regional": "Avion Regional",
    "Helice": "Helice",
    "Avi\u00f3n Comercial": "Avion Comercial",
    "Avi\u00f3n Regional": "Avion Regional",
    "H\u00e9lice": "Helice",
    "Avi\u00c3\u00b3n Comercial": "Avion Comercial",
    "Avi\u00c3\u00b3n Regional": "Avion Regional",
    "H\u00c3\u00a9lice": "Helice",
}


def normalize_aircraft_name(name):
    return AIRCRAFT_ALIASES.get(name, name)


def normalize_aircraft_config(config):
    normalized = {name: values.copy() for name, values in DEFAULT_AIRCRAFT_CONFIG.items()}
    for name, values in (config or {}).items():
        normalized_name = normalize_aircraft_name(name)
        previous = normalized.get(normalized_name, {})
        normalized[normalized_name] = {
            "costo_km": values.get("costoKm", values.get("costo_km", previous.get("costo_km", 0))),
            "tiempo_km": values.get("tiempoKm", values.get("tiempo_km", previous.get("tiempo_km", 0))),
        }
    return normalized


class Edge:
    def __init__(self, vertex1: Vertex, vertex2: Vertex,distance = 0, time = 0, cost = 0):
        """Constructor for the Edge class.
        Args:
            vertex1 (Vertex): Nodo origen instancia de la clase Vertex.
            vertex2 (Vertex): Nodo destino instancia de la clase Vertex.
            weight (int): Peso de la arista.
        """
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

        # ── Campos de ruta aérea ───────────────────────────
        self.aeronaves = []       # ej. ["Avión Comercial", "Hélice"]
        self.costo_base = -1.0    # 0 = subsidiada, -1 = no aplica
        self.estancia_minima = 0  # minutos mínimos en destino
        self.available = True     # False = ruta bloqueada (R4)
        self.aircraft_config = normalize_aircraft_config(None)

        #getters y setters
    def get_vertex1(self):
        """Devuelve el nodo origen de la arista.
        Returns:
            str: Nodo origen.
        """
        return self.vertex1
    def get_vertex2(self):
        """Devuelve el nodo destino de la arista.
        Returns:
            str: Nodo destino.
        """
        return self.vertex2
    
    def get_time(self):
        """Devuelve el tiempo de la arista.
        Returns:
            int: Tiempo de la arista.
        """
        return self.time
    
    def get_distance(self):
        """Devuelve la distancia de la arista.
        Returns:
            int: Distancia de la arista.
        """
        return self.distance
    
    def get_cost(self):
        """Devuelve el costo de la arista.
        Returns:
            int: Costo de la arista.
        """
        return self.cost
    

    def get_aeronaves(self):
        return self.aeronaves

    def get_aircraft_options(self):
        aircraft_names = self.aeronaves or ["Avion Comercial"]
        options = []
        for aircraft in aircraft_names:
            normalized_name = normalize_aircraft_name(aircraft)
            config = self.aircraft_config.get(
                normalized_name,
                DEFAULT_AIRCRAFT_CONFIG["Avion Comercial"],
            )
            cost = 0 if self.is_subsidiada() else round(self.distance * config["costo_km"], 2)
            time = round(self.distance * config["tiempo_km"], 1)
            options.append({
                "nombre": aircraft,
                "nombre_normalizado": normalized_name,
                "costo_km": config["costo_km"],
                "tiempo_km": config["tiempo_km"],
                "costo": cost,
                "tiempo": time,
            })
        return options

    def get_best_aircraft_option(self, criterion="costo"):
        options = self.get_aircraft_options()
        if criterion == "tiempo":
            return min(options, key=lambda option: (option["tiempo"], option["costo"]))
        return min(options, key=lambda option: (option["costo"], option["tiempo"]))

    def calculate_cost(self, aircraft=None):
        if self.cost > 0:
            return self.cost
        if aircraft:
            return self._get_aircraft_option(aircraft)["costo"]
        return self.get_best_aircraft_option("costo")["costo"]

    def calculate_time(self, aircraft=None):
        if self.time > 0:
            return self.time
        if aircraft:
            return self._get_aircraft_option(aircraft)["tiempo"]
        return self.get_best_aircraft_option("tiempo")["tiempo"]

    def _get_aircraft_option(self, aircraft):
        normalized_aircraft = normalize_aircraft_name(aircraft)
        for option in self.get_aircraft_options():
            if option["nombre_normalizado"] == normalized_aircraft:
                return option
        raise ValueError(f"Aircraft '{aircraft}' is not available for this route")

    def get_costo_base(self):
        return self.costo_base

    def is_subsidiada(self):
        """True si el costo base es 0 (ruta subsidiada)."""
        return self.costo_base == 0.0

    def get_estancia_minima(self):
        return self.estancia_minima

    def is_available(self):
        return self.available

    def set_available(self, available):
        """Bloquea o desbloquea la ruta. Se usa en R4."""
        self.available = available

    def load_from_dict(self, data: dict, aircraft_config=None):
        """Carga los campos de ruta aérea desde el dict del JSON.
        Args:
            data (dict): Arista del JSON con campos de la ruta.
        """
        self.aeronaves = data.get("aeronaves", [])
        self.costo_base = data.get("costoBase", -1.0)
        self.estancia_minima = data.get("estanciaMinima", 0)
        self.aircraft_config = normalize_aircraft_config(aircraft_config)

    
    def __str__(self):
        """Devuelve una cadena que representa la arista.
        Returns:
            str: Cadena que representa la arista.
        """
        return f"{self.vertex1.get_name()} --{self.distance}--> {self.vertex2.get_name()}"
        
        
