from core.vertex.vertex import Vertex


class AirportVertex(Vertex):
    """
    Extends Vertex with airport-specific fields required by the SkyRoute project.
    Stores IATA metadata, costs, activities and available jobs at each airport.
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

    def get_ciudad(self) -> str:
        return self.ciudad

    def get_pais(self) -> str:
        return self.pais

    def get_es_hub(self) -> bool:
        return self.es_hub

    def is_hub(self) -> bool:
        return self.es_hub

    def get_nombre_completo(self) -> str:
        return self.nombre

    def get_zona_horaria(self) -> str:
        return self.zona_horaria

    def get_aerolineas(self) -> list:
        return self.aerolineas

    def get_costo_alojamiento(self) -> float:
        return self.costo_alojamiento

    def get_costo_alimentacion(self) -> float:
        return self.costo_alimentacion

    def get_actividades(self) -> list:
        return self.actividades

    def get_trabajos(self) -> list:
        return self.trabajos

    def __repr__(self) -> str:
        hub_tag = " [HUB]" if self.es_hub else ""
        return f"AirportVertex({self.get_name()}{hub_tag} - {self.ciudad}, {self.pais})"