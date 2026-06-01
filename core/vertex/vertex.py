class Vertex:
    def __init__(self, name, available=True):
        """Constructor for the vertex class.
        Args:
            name (str): Nombre del nodo.
            available (bool): Indica si el nodo está disponible.
        """
        self.name = name
        self.neighbors = []
        self.available = available
        
    # ── Campos aeroportuarios ──────────────────────────
        self.nombre_completo = ""
        self.ciudad = ""
        self.pais = ""
        self.zona_horaria = ""
        self.es_hub = False
        self.aerolineas = []
        self.costo_alojamiento = 0.0
        self.costo_alimentacion = 0.0
        self.actividades = []   # lista de dicts
        self.trabajos = []      # lista de dicts


    def get_name(self):
        """Devuelve el nombre del nodo.
        Returns:
            str: Nombre del nodo.
        """
        return self.name
    def get_neighbors(self):
        """Devuelve una lista de los nodos vecinos del nodo.
        Returns:
            list: Lista de los nodos vecinos del nodo.
        """
        return self.neighbors
    def get_available(self):
        """Devuelve el estado de disponibilidad del nodo.
        Returns:
            bool: True si el nodo está disponible, False en caso contrario.
        """
        return self.available
    def set_available(self, available):
        """Establece el estado de disponibilidad del nodo.
        Args:
            available (bool): Nuevo estado de disponibilidad del nodo.
        """
        self.available = available
    def __str__(self): #imprimir el diccionario del nodo
        """Devuelve una cadena que representa el nodo.
        Returns:
            str: Cadena que representa el nodo.
        """
        return self.name

    def get_nombre_completo(self):
        return self.nombre_completo

    def get_ciudad(self):
        return self.ciudad

    def get_pais(self):
        return self.pais

    def get_zona_horaria(self):
        return self.zona_horaria

    def is_hub(self):
        return self.es_hub

    def get_aerolineas(self):
        return self.aerolineas

    def get_costo_alojamiento(self):
        return self.costo_alojamiento

    def get_costo_alimentacion(self):
        return self.costo_alimentacion

    def get_actividades(self):
        return self.actividades

    def get_trabajos(self):
        return self.trabajos

    def get_degree(self):
        """Número de rutas salientes. Útil para mostrarlo en el nodo del mapa."""
        return len(self.neighbors)
    
    def load_from_dict(self, data: dict):
        """Carga los campos aeroportuarios desde el dict del JSON.
        Args:
            data (dict): Nodo del JSON con campos del aeropuerto.
        """
        self.nombre_completo = data.get("nombre", self.name)
        self.ciudad = data.get("ciudad", "")
        self.pais = data.get("pais", "")
        self.zona_horaria = data.get("zonaHoraria", "")
        self.es_hub = data.get("esHub", False)
        self.aerolineas = data.get("aerolineas", [])
        self.costo_alojamiento = data.get("costoAlojamiento", 0.0)
        self.costo_alimentacion = data.get("costoAlimentacion", 0.0)
        self.actividades = data.get("actividades", [])
        self.trabajos = data.get("trabajos", [])