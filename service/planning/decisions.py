from service.planning.aircraft import opcion_con_subsidio
from service.planning.config import trabajos_habilitados
from service.planning.costs import costos_obligatorios, costos_obligatorios_en_aeropuerto
from service.planning.helpers import actividades_obligatorias, actividades_opcionales, buscar_arista, buscar_por_nombre
from service.planning.options import obtener_opciones_planificacion
from service.planning.state import normalizar_estado


def simular_decision_vuelo(graph, estado: dict, destino: str, aeronave: str) -> dict:
    nuevo_estado = aplicar_vuelo(graph, estado, destino, aeronave)
    return obtener_opciones_planificacion(graph, nuevo_estado)


def simular_decision_actividad(graph, estado: dict, nombre_actividad: str) -> dict:
    nuevo_estado = aplicar_actividad(graph, estado, nombre_actividad)
    return obtener_opciones_planificacion(graph, nuevo_estado)


def simular_decision_trabajo(graph, estado: dict, nombre_trabajo: str, horas: float) -> dict:
    nuevo_estado = aplicar_trabajo(graph, estado, nombre_trabajo, horas)
    return obtener_opciones_planificacion(graph, nuevo_estado)


def aplicar_vuelo(graph, estado: dict, destino: str, aeronave: str) -> dict:
    estado = normalizar_estado(estado)
    edge = buscar_arista(graph, estado["aeropuerto_actual"], destino)
    option = opcion_con_subsidio(graph, edge, edge._get_aircraft_option(aeronave))
    tiempo_vuelo = option["tiempo"]
    tiempo_estancia = edge.get_estancia_minima()
    costos = costos_obligatorios(
        graph,
        edge.get_vertex1(),
        edge.get_vertex2(),
        estado,
        tiempo_vuelo,
        tiempo_estancia,
    )

    costo_total = option["costo"] + costos["total"]
    nuevo_presupuesto = estado["presupuesto_actual"] - costo_total
    nuevo_tiempo = estado["tiempo_transcurrido_min"] + tiempo_vuelo + tiempo_estancia

    if nuevo_presupuesto < 0:
        raise ValueError("La decision supera el presupuesto disponible")
    if nuevo_tiempo > estado["tiempo_disponible_min"]:
        raise ValueError("La decision supera el tiempo disponible")
    if destino in estado["visitados"]:
        raise ValueError("No se puede visitar dos veces el mismo aeropuerto")

    tramo = {
        "origen": estado["aeropuerto_actual"],
        "destino": destino,
        "aeronave": option["nombre"],
        "distancia": edge.get_distance(),
        "distancia_km": edge.get_distance(),
        "tiempo": round(tiempo_vuelo, 1),
        "tiempo_vuelo": round(tiempo_vuelo, 1),
        "tiempo_estancia_min": tiempo_estancia,
        "costo": round(option["costo"], 2),
        "costo_vuelo": round(option["costo"], 2),
        "subsidiada": edge.is_subsidiada(),
        "km_subsidiados": option.get("km_subsidiados", 0),
    }

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
        "tramos_volados": [*estado["tramos_volados"], tramo],
        "costos_obligatorios": [*estado["costos_obligatorios"], *costos["eventos"]],
        "estancias": _registrar_estancia_minima(estado, destino, tiempo_estancia),
        "decisiones": [
            *estado["decisiones"],
            {
                "tipo": "vuelo",
                **tramo,
                "costo_alimentacion": costos["costo_alimentacion"],
                "costo_alojamiento": costos["costo_alojamiento"],
                "presupuesto_restante": round(nuevo_presupuesto, 2),
                "tiempo_transcurrido_min": round(nuevo_tiempo, 1),
            },
        ],
    }
    return _aplicar_actividades_obligatorias(graph, nuevo_estado)


def aplicar_actividad(graph, estado: dict, nombre_actividad: str) -> dict:
    estado = normalizar_estado(estado)
    vertex = graph.vertices[estado["aeropuerto_actual"]]
    actividad = buscar_por_nombre(actividades_opcionales(vertex), nombre_actividad, "actividad")
    costo = float(actividad.get("costo_usd", actividad.get("costo", 0)))
    duracion = float(actividad.get("duracion_min", actividad.get("duracion", 0)))
    uso_estancia = _consumir_estancia(estado, vertex.get_name(), duracion)
    costos = costos_obligatorios_en_aeropuerto(graph, vertex, estado, uso_estancia["tiempo_extra_min"])
    costo_total = costo + costos["total"]
    nuevo_presupuesto = estado["presupuesto_actual"] - costo_total
    nuevo_tiempo = estado["tiempo_transcurrido_min"] + uso_estancia["tiempo_extra_min"]

    if nuevo_presupuesto < 0:
        raise ValueError("La actividad supera el presupuesto disponible")
    if nuevo_tiempo > estado["tiempo_disponible_min"]:
        raise ValueError("La actividad supera el tiempo disponible")

    registro = {
        "aeropuerto": vertex.get_name(),
        "nombre": actividad["nombre"],
        "tipo": actividad.get("tipo", "opcional"),
        "duracion": duracion,
        "duracion_min": duracion,
        "tiempo_en_estancia_min": uso_estancia["tiempo_en_estancia_min"],
        "tiempo_extra_min": uso_estancia["tiempo_extra_min"],
        "tiempo_libre_restante_min": uso_estancia["tiempo_libre_restante_min"],
        "costo": round(costo, 2),
    }
    return {
        **estado,
        "presupuesto_actual": round(nuevo_presupuesto, 2),
        "tiempo_transcurrido_min": round(nuevo_tiempo, 1),
        "ultimo_alojamiento_min": costos["ultimo_alojamiento_min"],
        "ultima_alimentacion_min": costos["ultima_alimentacion_min"],
        "total_gastado": round(estado["total_gastado"] + costo_total, 2),
        "actividades_realizadas": [*estado["actividades_realizadas"], registro],
        "costos_obligatorios": [*estado["costos_obligatorios"], *costos["eventos"]],
        "estancias": uso_estancia["estancias"],
        "decisiones": [*estado["decisiones"], {"tipo": "actividad", **registro}],
    }


def aplicar_trabajo(graph, estado: dict, nombre_trabajo: str, horas: float) -> dict:
    estado = normalizar_estado(estado)
    if not trabajos_habilitados(graph, estado):
        raise ValueError("Los trabajos solo se habilitan cuando el presupuesto baja del umbral")

    vertex = graph.vertices[estado["aeropuerto_actual"]]
    trabajo = buscar_por_nombre(vertex.get_trabajos(), nombre_trabajo, "trabajo")
    horas = float(horas)
    max_horas = float(trabajo.get("max_horas", horas))
    if horas <= 0:
        raise ValueError("Las horas trabajadas deben ser mayores a cero")
    if horas > max_horas:
        raise ValueError(f"El trabajo permite maximo {max_horas} horas")

    duracion = horas * 60
    uso_estancia = _consumir_estancia(estado, vertex.get_name(), duracion)
    costos = costos_obligatorios_en_aeropuerto(graph, vertex, estado, uso_estancia["tiempo_extra_min"])
    ingreso = float(trabajo.get("tarifa_hora", 0)) * horas
    nuevo_tiempo = estado["tiempo_transcurrido_min"] + uso_estancia["tiempo_extra_min"]
    nuevo_presupuesto = estado["presupuesto_actual"] + ingreso - costos["total"]

    if nuevo_tiempo > estado["tiempo_disponible_min"]:
        raise ValueError("El trabajo supera el tiempo disponible")
    if nuevo_presupuesto < 0:
        raise ValueError("Los costos obligatorios superan el presupuesto disponible")

    registro = {
        "aeropuerto": vertex.get_name(),
        "nombre": trabajo["nombre"],
        "horas_trabajadas": horas,
        "tiempo_en_estancia_min": uso_estancia["tiempo_en_estancia_min"],
        "tiempo_extra_min": uso_estancia["tiempo_extra_min"],
        "tiempo_libre_restante_min": uso_estancia["tiempo_libre_restante_min"],
        "ingreso_obtenido": round(ingreso, 2),
    }
    return {
        **estado,
        "presupuesto_actual": round(nuevo_presupuesto, 2),
        "tiempo_transcurrido_min": round(nuevo_tiempo, 1),
        "ultimo_alojamiento_min": costos["ultimo_alojamiento_min"],
        "ultima_alimentacion_min": costos["ultima_alimentacion_min"],
        "total_gastado": round(estado["total_gastado"] + costos["total"], 2),
        "total_ganado": round(estado["total_ganado"] + ingreso, 2),
        "trabajos_realizados": [*estado["trabajos_realizados"], registro],
        "costos_obligatorios": [*estado["costos_obligatorios"], *costos["eventos"]],
        "estancias": uso_estancia["estancias"],
        "decisiones": [*estado["decisiones"], {"tipo": "trabajo", **registro}],
    }


def _registrar_estancia_minima(estado: dict, aeropuerto: str, estancia_minima: float) -> dict:
    estancias = {**estado.get("estancias", {})}
    estancias[aeropuerto] = {
        "aeropuerto": aeropuerto,
        "estancia_minima_min": estancia_minima,
        "tiempo_ocupado_min": 0,
        "tiempo_libre_min": estancia_minima,
    }
    return estancias


def _consumir_estancia(estado: dict, aeropuerto: str, duracion: float) -> dict:
    estancias = {**estado.get("estancias", {})}
    actual = dict(estancias.get(aeropuerto, {
        "aeropuerto": aeropuerto,
        "estancia_minima_min": 0,
        "tiempo_ocupado_min": 0,
        "tiempo_libre_min": 0,
    }))
    libre = float(actual.get("tiempo_libre_min", 0))
    tiempo_en_estancia = min(libre, duracion)
    tiempo_extra = max(0, duracion - tiempo_en_estancia)

    actual["tiempo_ocupado_min"] = round(actual.get("tiempo_ocupado_min", 0) + duracion, 1)
    actual["tiempo_libre_min"] = round(max(0, libre - tiempo_en_estancia), 1)
    estancias[aeropuerto] = actual

    return {
        "estancias": estancias,
        "tiempo_en_estancia_min": round(tiempo_en_estancia, 1),
        "tiempo_extra_min": round(tiempo_extra, 1),
        "tiempo_libre_restante_min": actual["tiempo_libre_min"],
    }


def _aplicar_actividades_obligatorias(graph, estado: dict) -> dict:
    vertex = graph.vertices[estado["aeropuerto_actual"]]
    for actividad in actividades_obligatorias(vertex):
        nombre = actividad.get("nombre")
        if not nombre:
            continue
        estado = _aplicar_actividad_registrada(graph, estado, actividad, "obligatoria")
    return estado


def _aplicar_actividad_registrada(graph, estado: dict, actividad: dict, tipo: str) -> dict:
    vertex = graph.vertices[estado["aeropuerto_actual"]]
    costo = float(actividad.get("costo_usd", actividad.get("costo", 0)))
    duracion = float(actividad.get("duracion_min", actividad.get("duracion", 0)))
    uso_estancia = _consumir_estancia(estado, vertex.get_name(), duracion)
    costos = costos_obligatorios_en_aeropuerto(graph, vertex, estado, uso_estancia["tiempo_extra_min"])
    costo_total = costo + costos["total"]
    nuevo_presupuesto = estado["presupuesto_actual"] - costo_total
    nuevo_tiempo = estado["tiempo_transcurrido_min"] + uso_estancia["tiempo_extra_min"]

    if nuevo_presupuesto < 0:
        raise ValueError("La actividad obligatoria supera el presupuesto disponible")
    if nuevo_tiempo > estado["tiempo_disponible_min"]:
        raise ValueError("La actividad obligatoria supera el tiempo disponible")

    registro = {
        "aeropuerto": vertex.get_name(),
        "nombre": actividad["nombre"],
        "tipo": tipo,
        "duracion": duracion,
        "duracion_min": duracion,
        "tiempo_en_estancia_min": uso_estancia["tiempo_en_estancia_min"],
        "tiempo_extra_min": uso_estancia["tiempo_extra_min"],
        "tiempo_libre_restante_min": uso_estancia["tiempo_libre_restante_min"],
        "costo": round(costo, 2),
    }
    return {
        **estado,
        "presupuesto_actual": round(nuevo_presupuesto, 2),
        "tiempo_transcurrido_min": round(nuevo_tiempo, 1),
        "ultimo_alojamiento_min": costos["ultimo_alojamiento_min"],
        "ultima_alimentacion_min": costos["ultima_alimentacion_min"],
        "total_gastado": round(estado["total_gastado"] + costo_total, 2),
        "actividades_realizadas": [*estado["actividades_realizadas"], registro],
        "costos_obligatorios": [*estado["costos_obligatorios"], *costos["eventos"]],
        "estancias": uso_estancia["estancias"],
        "decisiones": [*estado["decisiones"], {"tipo": "actividad", **registro}],
    }
