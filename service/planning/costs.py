from service.planning.config import reglas


def costos_obligatorios(graph, origen_vertex, destino_vertex, estado, tiempo_vuelo, estancia_minima):
    eventos = []
    nuevo_tiempo_vuelo = estado["tiempo_transcurrido_min"] + tiempo_vuelo
    nuevo_tiempo_total = nuevo_tiempo_vuelo + estancia_minima
    reglas_actuales = reglas(graph)
    alimentacion_min = reglas_actuales["intervalo_alimentacion_min"]
    alojamiento_min = reglas_actuales["intervalo_alojamiento_min"]
    ultima_alimentacion = estado["ultima_alimentacion_min"]
    ultimo_alojamiento = estado["ultimo_alojamiento_min"]

    if nuevo_tiempo_total - ultima_alimentacion >= alimentacion_min:
        aeropuerto_cobro = origen_vertex if nuevo_tiempo_vuelo - ultima_alimentacion >= alimentacion_min else destino_vertex
        eventos.append({
            "tipo": "alimentacion",
            "aeropuerto": aeropuerto_cobro.get_name(),
            "costo": aeropuerto_cobro.get_costo_alimentacion(),
        })
        ultima_alimentacion = nuevo_tiempo_total

    if nuevo_tiempo_total - ultimo_alojamiento >= alojamiento_min:
        eventos.append({
            "tipo": "alojamiento",
            "aeropuerto": destino_vertex.get_name(),
            "costo": destino_vertex.get_costo_alojamiento(),
        })
        ultimo_alojamiento = nuevo_tiempo_total

    costo_alimentacion = sum(evento["costo"] for evento in eventos if evento["tipo"] == "alimentacion")
    costo_alojamiento = sum(evento["costo"] for evento in eventos if evento["tipo"] == "alojamiento")
    return {
        "eventos": eventos,
        "total": costo_alimentacion + costo_alojamiento,
        "costo_alimentacion": costo_alimentacion,
        "costo_alojamiento": costo_alojamiento,
        "ultima_alimentacion_min": ultima_alimentacion,
        "ultimo_alojamiento_min": ultimo_alojamiento,
    }


def costos_obligatorios_en_aeropuerto(graph, vertex, estado, duracion):
    return costos_obligatorios(graph, vertex, vertex, estado, duracion, 0)

