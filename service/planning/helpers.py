def actividades_opcionales(vertex):
    return [
        actividad
        for actividad in vertex.get_actividades()
        if actividad.get("tipo", "opcional") != "obligatoria"
    ]


def actividades_obligatorias(vertex):
    return [
        actividad
        for actividad in vertex.get_actividades()
        if actividad.get("tipo", "opcional") == "obligatoria"
    ]


def serializar_aeropuerto(vertex):
    return {
        "id": vertex.get_name(),
        "nombre": getattr(vertex, "nombre", vertex.get_name()),
        "ciudad": getattr(vertex, "ciudad", ""),
        "pais": getattr(vertex, "pais", ""),
        "zona_horaria": getattr(vertex, "zona_horaria", ""),
        "es_hub": getattr(vertex, "es_hub", False),
        "aerolineas": getattr(vertex, "aerolineas", []),
        "costo_alojamiento": getattr(vertex, "costo_alojamiento", 0.0),
        "costo_alimentacion": getattr(vertex, "costo_alimentacion", 0.0),
    }


def buscar_arista(graph, origen, destino):
    if origen not in graph.vertices:
        raise ValueError(f"Aeropuerto origen '{origen}' no existe")
    for edge in graph.vertices[origen].neighbors:
        if edge.get_vertex2().get_name() == destino and edge.is_available():
            return edge
    raise ValueError(f"No existe una ruta disponible de {origen} a {destino}")


def buscar_por_nombre(items, nombre, tipo):
    for item in items:
        if item.get("nombre", "").lower() == nombre.lower():
            return item
    raise ValueError(f"No existe {tipo} '{nombre}' en el aeropuerto actual")


def mejor_trabajo(vertex):
    trabajos = vertex.get_trabajos()
    if not trabajos:
        return None
    return max(trabajos, key=lambda trabajo: trabajo.get("tarifa_hora", 0))
