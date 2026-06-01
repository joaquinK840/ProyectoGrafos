"""
Advanced planning - R3.

This module exposes decision states instead of choosing automatically for the
traveler. At each airport it lists available flights, aircraft options,
optional activities, and jobs when the budget threshold is reached.
"""

INTERVALO_ALOJAMIENTO = 20 * 60
INTERVALO_ALIMENTACION = 8 * 60
UMBRAL_TRABAJO = 0.35
DEFAULT_TIEMPO_DISPONIBLE = 72 * 60


def planificar_avanzado(
    graph,
    origen: str,
    presupuesto_inicial: float,
    tiempo_disponible: float | None = None,
) -> dict:
    """Create the initial step-by-step planning state."""
    estado = crear_estado_planificacion(
        graph,
        origen,
        presupuesto_inicial,
        tiempo_disponible or DEFAULT_TIEMPO_DISPONIBLE,
    )
    return obtener_opciones_planificacion(graph, estado)


def crear_estado_planificacion(
    graph,
    origen: str,
    presupuesto_inicial: float,
    tiempo_disponible: float,
) -> dict:
    if origen not in graph.vertices:
        raise ValueError(f"Aeropuerto '{origen}' no existe en el grafo")
    if presupuesto_inicial < 0:
        raise ValueError("El presupuesto inicial no puede ser negativo")
    if tiempo_disponible < 0:
        raise ValueError("El tiempo disponible no puede ser negativo")

    return {
        "aeropuerto_actual": origen,
        "presupuesto_inicial": presupuesto_inicial,
        "presupuesto_actual": presupuesto_inicial,
        "tiempo_disponible_min": tiempo_disponible,
        "tiempo_transcurrido_min": 0,
        "ultimo_alojamiento_min": 0,
        "ultima_alimentacion_min": 0,
        "visitados": [origen],
        "camino": [origen],
        "total_gastado": 0,
        "total_ganado": 0,
        "decisiones": [],
    }


def obtener_opciones_planificacion(graph, estado: dict) -> dict:
    """Return available decisions for the current advanced-planning state."""
    estado = _normalizar_estado(estado)
    actual = estado["aeropuerto_actual"]
    if actual not in graph.vertices:
        raise ValueError(f"Aeropuerto actual '{actual}' no existe en el grafo")

    vertex = graph.vertices[actual]
    trabajos_habilitados = _trabajos_habilitados(estado)

    return {
        "modo": "paso_a_paso",
        "estado": estado,
        "aeropuerto_actual": _serializar_aeropuerto(vertex),
        "reglas": {
            "umbral_trabajo_porcentaje": UMBRAL_TRABAJO,
            "intervalo_alojamiento_min": INTERVALO_ALOJAMIENTO,
            "intervalo_alimentacion_min": INTERVALO_ALIMENTACION,
        },
        "actividades_opcionales": _actividades_opcionales(vertex),
        "trabajos_disponibles": vertex.get_trabajos() if trabajos_habilitados else [],
        "trabajos_habilitados": trabajos_habilitados,
        "vuelos_disponibles": _vuelos_disponibles(graph, vertex, estado),
        "mensaje": "Seleccione una actividad, trabajo o vuelo para avanzar al siguiente paso.",
    }


def simular_decision_vuelo(graph, estado: dict, destino: str, aeronave: str) -> dict:
    """
    Apply a flight decision and return the next decision state.

    This helper does not choose automatically; it only validates and applies the
    explicit flight and aircraft selected by the user interface.
    """
    estado = _normalizar_estado(estado)
    edge = _buscar_arista(graph, estado["aeropuerto_actual"], destino)
    option = edge._get_aircraft_option(aeronave)
    costos = _costos_obligatorios_al_llegar(edge.get_vertex2(), estado, option["tiempo"])

    costo_total = option["costo"] + costos["costo_alimentacion"] + costos["costo_alojamiento"]
    nuevo_presupuesto = estado["presupuesto_actual"] - costo_total
    nuevo_tiempo = estado["tiempo_transcurrido_min"] + option["tiempo"]

    if nuevo_presupuesto < 0:
        raise ValueError("La decisión supera el presupuesto disponible")
    if nuevo_tiempo > estado["tiempo_disponible_min"]:
        raise ValueError("La decisión supera el tiempo disponible")
    if destino in estado["visitados"]:
        raise ValueError("No se puede visitar dos veces el mismo aeropuerto")

    nuevo_estado = {
        **estado,
        "aeropuerto_actual": destino,
        "presupuesto_actual": round(nuevo_presupuesto, 2),
        "tiempo_transcurrido_min": round(nuevo_tiempo, 1),
        "ultimo_alojamiento_min": costos["ultimo_alojamiento_min"],
        "ultima_alimentacion_min": costos["ultima_alimentacion_min"],
        "visitados": [*estado["visitados"], destino],
        "camino": [*estado["camino"], destino],
        "total_gastado": round(estado["total_gastado"] + costo_total, 2),
        "decisiones": [
            *estado["decisiones"],
            {
                "tipo": "vuelo",
                "origen": estado["aeropuerto_actual"],
                "destino": destino,
                "aeronave": aeronave,
                "distancia_km": edge.get_distance(),
                "costo_vuelo": option["costo"],
                "tiempo_vuelo": option["tiempo"],
                "costo_alimentacion": costos["costo_alimentacion"],
                "costo_alojamiento": costos["costo_alojamiento"],
                "presupuesto_restante": round(nuevo_presupuesto, 2),
                "tiempo_transcurrido_min": round(nuevo_tiempo, 1),
            },
        ],
    }
    return obtener_opciones_planificacion(graph, nuevo_estado)


def _normalizar_estado(estado):
    required = {
        "aeropuerto_actual",
        "presupuesto_inicial",
        "presupuesto_actual",
        "tiempo_disponible_min",
        "tiempo_transcurrido_min",
        "ultimo_alojamiento_min",
        "ultima_alimentacion_min",
        "visitados",
        "camino",
        "total_gastado",
        "total_ganado",
        "decisiones",
    }
    missing = required - set(estado)
    if missing:
        raise ValueError(f"Estado incompleto. Faltan campos: {sorted(missing)}")
    return estado


def _trabajos_habilitados(estado):
    return estado["presupuesto_actual"] <= estado["presupuesto_inicial"] * UMBRAL_TRABAJO


def _actividades_opcionales(vertex):
    return [
        actividad
        for actividad in vertex.get_actividades()
        if actividad.get("tipo", "opcional") != "obligatoria"
    ]


def _vuelos_disponibles(graph, vertex, estado):
    vuelos = []
    visitados = set(estado["visitados"])
    for edge in vertex.neighbors:
        if not edge.is_available():
            continue

        destino_vertex = edge.get_vertex2()
        destino = destino_vertex.get_name()
        if destino in visitados or not destino_vertex.get_available():
            continue

        opciones = []
        for option in edge.get_aircraft_options():
            costos = _costos_obligatorios_al_llegar(destino_vertex, estado, option["tiempo"])
            costo_total = option["costo"] + costos["costo_alimentacion"] + costos["costo_alojamiento"]
            presupuesto_restante = estado["presupuesto_actual"] - costo_total
            tiempo_resultante = estado["tiempo_transcurrido_min"] + option["tiempo"]
            opciones.append({
                **option,
                "costo_alimentacion": costos["costo_alimentacion"],
                "costo_alojamiento": costos["costo_alojamiento"],
                "costo_total_decision": round(costo_total, 2),
                "presupuesto_restante": round(presupuesto_restante, 2),
                "tiempo_resultante_min": round(tiempo_resultante, 1),
                "factible": presupuesto_restante >= 0
                and tiempo_resultante <= estado["tiempo_disponible_min"],
            })

        vuelos.append({
            "origen": vertex.get_name(),
            "destino": destino,
            "aeropuerto_destino": _serializar_aeropuerto(destino_vertex),
            "distancia_km": edge.get_distance(),
            "estancia_minima": edge.get_estancia_minima(),
            "opciones_aeronaves": opciones,
        })
    return vuelos


def _costos_obligatorios_al_llegar(destino_vertex, estado, tiempo_vuelo):
    nuevo_tiempo = estado["tiempo_transcurrido_min"] + tiempo_vuelo
    costo_alimentacion = 0
    costo_alojamiento = 0
    ultima_alimentacion = estado["ultima_alimentacion_min"]
    ultimo_alojamiento = estado["ultimo_alojamiento_min"]

    if nuevo_tiempo - ultima_alimentacion >= INTERVALO_ALIMENTACION:
        costo_alimentacion = destino_vertex.get_costo_alimentacion()
        ultima_alimentacion = nuevo_tiempo

    if nuevo_tiempo - ultimo_alojamiento >= INTERVALO_ALOJAMIENTO:
        costo_alojamiento = destino_vertex.get_costo_alojamiento()
        ultimo_alojamiento = nuevo_tiempo

    return {
        "costo_alimentacion": costo_alimentacion,
        "costo_alojamiento": costo_alojamiento,
        "ultima_alimentacion_min": ultima_alimentacion,
        "ultimo_alojamiento_min": ultimo_alojamiento,
    }


def _serializar_aeropuerto(vertex):
    return {
        "id": vertex.get_name(),
        "nombre": vertex.get_nombre_completo(),
        "ciudad": vertex.get_ciudad(),
        "pais": vertex.get_pais(),
        "zona_horaria": vertex.get_zona_horaria(),
        "es_hub": vertex.is_hub(),
        "aerolineas": vertex.get_aerolineas(),
        "costo_alojamiento": vertex.get_costo_alojamiento(),
        "costo_alimentacion": vertex.get_costo_alimentacion(),
    }


def _buscar_arista(graph, origen, destino):
    if origen not in graph.vertices:
        raise ValueError(f"Aeropuerto origen '{origen}' no existe")
    for edge in graph.vertices[origen].neighbors:
        if edge.get_vertex2().get_name() == destino and edge.is_available():
            return edge
    raise ValueError(f"No existe una ruta disponible de {origen} a {destino}")
