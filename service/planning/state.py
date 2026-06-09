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
        "tramos_volados": [],
        "actividades_realizadas": [],
        "trabajos_realizados": [],
        "costos_obligatorios": [],
        "estancias": {},
    }


def normalizar_estado(estado):
    defaults = {
        "tramos_volados": [],
        "actividades_realizadas": [],
        "trabajos_realizados": [],
        "costos_obligatorios": [],
        "estancias": {},
    }
    estado = {**defaults, **estado}
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
