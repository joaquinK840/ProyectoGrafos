"""
Advanced planning - R3.

The module supports two flows:
- step-by-step decisions for the UI;
- an automatic bounded DFS that maximizes visited destinations and minimizes
  total spending among routes with the same destination count.
"""


DEFAULT_INTERVALO_ALOJAMIENTO_HORAS = 20
DEFAULT_INTERVALO_ALIMENTACION_HORAS = 8
DEFAULT_UMBRAL_TRABAJO_PORC = 35
DEFAULT_LIMITE_SUBSIDIO_PORC = 20
DEFAULT_TIEMPO_DISPONIBLE = 72 * 60
DEFAULT_MAX_EXPANSIONES = 20000


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


def planificar_avanzado_automatico(
    graph,
    origen: str,
    presupuesto_inicial: float,
    tiempo_disponible: float | None = None,
    max_expansiones: int = DEFAULT_MAX_EXPANSIONES,
) -> dict:
    """
    Search an advanced itinerary.

    DFS is bounded by max_expansiones to keep the API responsive with the
    30-airport test graph. Candidate comparison follows the requirement:
    maximize destinations first, then minimize total spent, then minimize time.
    """
    inicial = crear_estado_planificacion(
        graph,
        origen,
        presupuesto_inicial,
        tiempo_disponible or DEFAULT_TIEMPO_DISPONIBLE,
    )
    return _buscar_itinerario_automatico(graph, inicial, max_expansiones)


def recalcular_avanzado_desde_estado(
    graph,
    estado: dict,
    max_expansiones: int = DEFAULT_MAX_EXPANSIONES,
) -> dict:
    """Continue the automatic R3 search from an existing trip state."""
    estado = _normalizar_estado(estado)
    if estado["aeropuerto_actual"] not in graph.vertices:
        raise ValueError(f"Aeropuerto actual '{estado['aeropuerto_actual']}' no existe en el grafo")
    return _buscar_itinerario_automatico(graph, estado, max_expansiones)


def _buscar_itinerario_automatico(graph, inicial: dict, max_expansiones: int) -> dict:
    mejor = inicial
    expansiones = 0

    def _mejor_que(candidato, actual):
        return (
            len(candidato["visitados"]),
            -candidato["total_gastado"],
            -candidato["tiempo_transcurrido_min"],
        ) > (
            len(actual["visitados"]),
            -actual["total_gastado"],
            -actual["tiempo_transcurrido_min"],
        )

    def _dfs(estado):
        nonlocal mejor, expansiones
        if expansiones >= max_expansiones:
            return
        expansiones += 1

        if _mejor_que(estado, mejor):
            mejor = estado

        vuelos = _vuelos_disponibles(graph, graph.vertices[estado["aeropuerto_actual"]], estado)
        candidatos = []
        for vuelo in vuelos:
            for option in vuelo["opciones_aeronaves"]:
                if option["factible"]:
                    candidatos.append((vuelo["destino"], option))

        candidatos.sort(key=lambda item: (
            item[1]["costo_total_decision"],
            item[1]["tiempo_resultante_min"],
        ))

        for destino, option in candidatos:
            try:
                siguiente = _aplicar_vuelo(graph, estado, destino, option["nombre"])
            except ValueError:
                continue
            _dfs(siguiente)

        if not candidatos and _trabajos_habilitados(graph, estado):
            trabajo = _mejor_trabajo(graph.vertices[estado["aeropuerto_actual"]])
            if trabajo:
                horas = min(
                    float(trabajo.get("max_horas", 1)),
                    max(1, (estado["tiempo_disponible_min"] - estado["tiempo_transcurrido_min"]) // 60),
                )
                try:
                    _dfs(_aplicar_trabajo(graph, estado, trabajo["nombre"], horas))
                except ValueError:
                    pass

    _dfs(inicial)
    reporte = generar_reporte_final(graph, mejor)
    return {
        "modo": "automatico",
        "expansiones": expansiones,
        "limite_expansiones": max_expansiones,
        "limite_alcanzado": expansiones >= max_expansiones,
        "itinerario": reporte,
    }


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
        # Accumulated subsidized km used so far — enforces the global subsidy cap.
        "km_subsidiados_total": 0.0,
        # Total distance flown so far — used to compute the cap denominator.
        "distancia_total_km": 0.0,
        # estancia_minima of the edge that brought us HERE — used to compute tiempo_libre on next departure.
        "estancia_minima_pendiente": 0.0,
    }


def obtener_opciones_planificacion(graph, estado: dict) -> dict:
    """Return available decisions for the current advanced-planning state."""
    estado = _normalizar_estado(estado)
    actual = estado["aeropuerto_actual"]
    if actual not in graph.vertices:
        raise ValueError(f"Aeropuerto actual '{actual}' no existe en el grafo")

    vertex = graph.vertices[actual]
    trabajos_habilitados = _trabajos_habilitados(graph, estado)

    return {
        "modo": "paso_a_paso",
        "estado": estado,
        "aeropuerto_actual": _serializar_aeropuerto(vertex),
        "reglas": _reglas(graph),
        "actividades_opcionales": _actividades_opcionales(vertex),
        "trabajos_disponibles": vertex.get_trabajos() if trabajos_habilitados else [],
        "trabajos_habilitados": trabajos_habilitados,
        "vuelos_disponibles": _vuelos_disponibles(graph, vertex, estado),
        "mensaje": "Seleccione una actividad, trabajo o vuelo para avanzar al siguiente paso.",
    }


def simular_decision_vuelo(graph, estado: dict, destino: str, aeronave: str) -> dict:
    """Apply a flight selected by the user interface."""
    nuevo_estado = _aplicar_vuelo(graph, estado, destino, aeronave)
    return obtener_opciones_planificacion(graph, nuevo_estado)


def simular_decision_actividad(graph, estado: dict, nombre_actividad: str) -> dict:
    """Apply an optional activity selected at the current airport."""
    nuevo_estado = _aplicar_actividad(graph, estado, nombre_actividad)
    return obtener_opciones_planificacion(graph, nuevo_estado)


def simular_decision_trabajo(graph, estado: dict, nombre_trabajo: str, horas: float) -> dict:
    """Apply a temporary job selected at the current airport."""
    nuevo_estado = _aplicar_trabajo(graph, estado, nombre_trabajo, horas)
    return obtener_opciones_planificacion(graph, nuevo_estado)


def generar_reporte_final(graph, estado: dict) -> dict:
    """Build the R5-compatible report from the R3 state."""
    estado = _normalizar_estado(estado)
    destinos = []
    
    # Inyectar los costos obligatorios en la lista de actividades visual
    todas_actividades = list(estado["actividades_realizadas"])
    for costo_obl in estado["costos_obligatorios"]:
        todas_actividades.append({
            "aeropuerto": costo_obl["aeropuerto"],
            "nombre": costo_obl["tipo"].capitalize(), # "Alojamiento" o "Alimentacion"
            "tipo": "obligatoria",
            "duracion_min": 0,
            "costo": costo_obl["costo"]
        })

    for airport_id in estado["visitados"]:
        vertex = graph.vertices.get(airport_id)
        if not vertex:
            continue
        actividades = [a for a in estado["actividades_realizadas"] if a["aeropuerto"] == airport_id]
        destinos.append({
            "aeropuerto": airport_id,
            "ciudad": vertex.get_ciudad(),
            "pais": vertex.get_pais(),
            "tiempo_estadia_min": _tiempo_estadia(estado, airport_id),
            "costo_total": round(
                sum(item["costo"] for item in actividades)
                + sum(item["costo"] for item in estado["costos_obligatorios"] if item["aeropuerto"] == airport_id),
                2,
            ),
        })

    return {
        "destinos_visitados": destinos,
        "tramos_volados": estado["tramos_volados"],
        "actividades": todas_actividades, # <--- AHORA SÍ APARECEN EN EL REPORTE
        "trabajos": estado["trabajos_realizados"],
        "totales": {
            "presupuesto_inicial": estado["presupuesto_inicial"],
            "total_gastado": round(estado["total_gastado"], 2),
            "total_ganado": round(estado["total_ganado"], 2),
            "saldo_final": round(estado["presupuesto_actual"], 2),
            "tiempo_total_min": round(estado["tiempo_transcurrido_min"], 1),
            "tiempo_total_horas": round(estado["tiempo_transcurrido_min"] / 60, 2),
            "destinos": max(0, len(estado["visitados"]) - 1),
        },
        "camino": estado["camino"],
        "estado": estado,
    }


def _aplicar_vuelo(graph, estado: dict, destino: str, aeronave: str) -> dict:
    estado = _normalizar_estado(estado)
    edge = _buscar_arista(graph, estado["aeropuerto_actual"], destino)
    km_sub_total = estado.get("km_subsidiados_total", 0.0)
    option = _opcion_con_subsidio(graph, edge, edge._get_aircraft_option(aeronave), km_sub_total)
    tiempo_vuelo = option["tiempo"]
    tiempo_estancia = edge.get_estancia_minima()
    tiempo_total_decision = tiempo_vuelo + tiempo_estancia
    costos = _costos_obligatorios(
        graph,
        edge.get_vertex1(),
        edge.get_vertex2(),
        estado,
        tiempo_vuelo,
        tiempo_estancia,
    )

    costo_total = option["costo"] + costos["total"]
    nuevo_presupuesto = estado["presupuesto_actual"] - costo_total
    nuevo_tiempo = estado["tiempo_transcurrido_min"] + tiempo_total_decision

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

    nuevo_km_subsidiados = estado.get("km_subsidiados_total", 0.0) + option.get("km_subsidiados", 0)
    nuevo_distancia_total = estado.get("distancia_total_km", 0.0) + edge.get_distance()

    # --- Spec 2.3.a: log "tiempo_libre" for the airport we are DEPARTING FROM --------
    # If the traveler's activities + jobs did not fill the mandatory minimum stay
    # at the current airport, the leftover time is registered as "tiempo_libre".
    estancia_prev = float(estado.get("estancia_minima_pendiente", 0.0))
    tiempo_libre_decisiones: list = []
    if estancia_prev > 0:
        actual = estado["aeropuerto_actual"]
        activities_here = sum(
            float(a.get("duracion_min", a.get("duracion", 0)))
            for a in estado.get("actividades_realizadas", [])
            if a.get("aeropuerto") == actual
        )
        jobs_here = sum(
            float(j.get("horas_trabajadas", 0)) * 60
            for j in estado.get("trabajos_realizados", [])
            if j.get("aeropuerto") == actual
        )
        tiempo_libre_val = round(max(0.0, estancia_prev - activities_here - jobs_here), 1)
        if tiempo_libre_val > 0:
            tiempo_libre_decisiones = [{
                "tipo": "tiempo_libre",
                "aeropuerto": actual,
                "duracion": tiempo_libre_val,
                "duracion_min": tiempo_libre_val,
            }]
    # ---------------------------------------------------------------------------------

    return {
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
        "km_subsidiados_total": round(nuevo_km_subsidiados, 2),
        "distancia_total_km": round(nuevo_distancia_total, 2),
        "estancia_minima_pendiente": float(edge.get_estancia_minima()),
        "decisiones": [
            *estado["decisiones"],
            *tiempo_libre_decisiones,
            *eventos_decisiones, # <--- AHORA EL LOG (UI) MUESTRA SI COMISTE O DORMISTE
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


def _aplicar_actividad(graph, estado: dict, nombre_actividad: str) -> dict:
    estado = _normalizar_estado(estado)
    vertex = graph.vertices[estado["aeropuerto_actual"]]
    actividad = _buscar_por_nombre(_actividades_opcionales(vertex), nombre_actividad, "actividad")
    costo = float(actividad.get("costo_usd", actividad.get("costo", 0)))
    duracion = float(actividad.get("duracion_min", actividad.get("duracion", 0)))
    costos = _costos_obligatorios_en_aeropuerto(graph, vertex, estado, duracion)
    costo_total = costo + costos["total"]
    nuevo_presupuesto = estado["presupuesto_actual"] - costo_total
    nuevo_tiempo = estado["tiempo_transcurrido_min"] + duracion

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
        "decisiones": [*estado["decisiones"], {"tipo": "actividad", **registro}],
    }


def _aplicar_trabajo(graph, estado: dict, nombre_trabajo: str, horas: float) -> dict:
    estado = _normalizar_estado(estado)
    if not _trabajos_habilitados(graph, estado):
        raise ValueError("Los trabajos solo se habilitan cuando el presupuesto baja del umbral")

    vertex = graph.vertices[estado["aeropuerto_actual"]]
    trabajo = _buscar_por_nombre(vertex.get_trabajos(), nombre_trabajo, "trabajo")
    horas = float(horas)
    max_horas = float(trabajo.get("max_horas", horas))
    if horas <= 0:
        raise ValueError("Las horas trabajadas deben ser mayores a cero")
    if horas > max_horas:
        raise ValueError(f"El trabajo permite maximo {max_horas} horas")

    duracion = horas * 60
    costos = _costos_obligatorios_en_aeropuerto(graph, vertex, estado, duracion)
    ingreso = float(trabajo.get("tarifa_hora", 0)) * horas
    nuevo_tiempo = estado["tiempo_transcurrido_min"] + duracion
    nuevo_presupuesto = estado["presupuesto_actual"] + ingreso - costos["total"]

    if nuevo_tiempo > estado["tiempo_disponible_min"]:
        raise ValueError("El trabajo supera el tiempo disponible")
    if nuevo_presupuesto < 0:
        raise ValueError("Los costos obligatorios superan el presupuesto disponible")

    registro = {
        "aeropuerto": vertex.get_name(),
        "nombre": trabajo["nombre"],
        "horas_trabajadas": horas,
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
        "decisiones": [*estado["decisiones"], {"tipo": "trabajo", **registro}],
    }


def _normalizar_estado(estado):
    defaults = {
        "tramos_volados": [],
        "actividades_realizadas": [],
        "trabajos_realizados": [],
        "costos_obligatorios": [],
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


def _config(graph, key, default):
    return getattr(graph, "global_config", {}).get(key, default)


def _reglas(graph):
    return {
        "umbral_trabajo_porcentaje": _config(graph, "presupuestoMinimoPorc", DEFAULT_UMBRAL_TRABAJO_PORC),
        "intervalo_alojamiento_min": _config(graph, "intervaloAlojamiento", DEFAULT_INTERVALO_ALOJAMIENTO_HORAS) * 60,
        "intervalo_alimentacion_min": _config(graph, "intervaloAlimentacion", DEFAULT_INTERVALO_ALIMENTACION_HORAS) * 60,
        "limite_subsidio_porcentaje": _config(graph, "limiteSubsidioPorc", DEFAULT_LIMITE_SUBSIDIO_PORC),
    }


def _trabajos_habilitados(graph, estado):
    umbral = _config(graph, "presupuestoMinimoPorc", DEFAULT_UMBRAL_TRABAJO_PORC) / 100
    return estado["presupuesto_actual"] <= estado["presupuesto_inicial"] * umbral


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
        km_sub_total = estado.get("km_subsidiados_total", 0.0)
        for base_option in edge.get_aircraft_options():
            option = _opcion_con_subsidio(graph, edge, base_option, km_sub_total)
            costos = _costos_obligatorios(
                graph,
                vertex,
                destino_vertex,
                estado,
                option["tiempo"],
                edge.get_estancia_minima(),
            )
            costo_total = option["costo"] + costos["total"]
            tiempo_decision = option["tiempo"] + edge.get_estancia_minima()
            presupuesto_restante = estado["presupuesto_actual"] - costo_total
            tiempo_resultante = estado["tiempo_transcurrido_min"] + tiempo_decision
            opciones.append({
                **option,
                "estancia_minima": edge.get_estancia_minima(),
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
            "subsidiada": edge.is_subsidiada(),
            "opciones_aeronaves": opciones,
        })
    return vuelos


def _opcion_con_subsidio(graph, edge, option, km_subsidiados_total: float = 0.0):
    """
    Apply the global subsidy cap (default 20% of the *total distance flown so far
    including this leg*).  Unlike the previous per-leg implementation, we track
    how many km the traveler has already used at subsidized rate and only allow
    the remaining budget for this leg.
    """
    option = dict(option)
    option["km_subsidiados"] = 0
    if not edge.is_subsidiada():
        return option

    limite_porc = _config(graph, "limiteSubsidioPorc", DEFAULT_LIMITE_SUBSIDIO_PORC) / 100
    distancia_tramo = edge.get_distance()
    # Maximum cumulative km that can be subsidized, based on distance flown so far + this leg
    km_maximos_subsidio = (km_subsidiados_total + distancia_tramo) * limite_porc
    km_restantes_permitidos = max(0.0, km_maximos_subsidio - km_subsidiados_total)
    km_subsidiados_este_tramo = min(distancia_tramo, km_restantes_permitidos)
    km_cobrados = max(0.0, distancia_tramo - km_subsidiados_este_tramo)
    option["costo"] = round(km_cobrados * option["costo_km"], 2)
    option["km_subsidiados"] = round(km_subsidiados_este_tramo, 2)
    return option


def _costos_obligatorios(graph, origen_vertex, destino_vertex, estado, tiempo_vuelo, estancia_minima):
    eventos = []
    nuevo_tiempo_vuelo = estado["tiempo_transcurrido_min"] + tiempo_vuelo
    nuevo_tiempo_total = nuevo_tiempo_vuelo + estancia_minima
    alimentacion_min = _reglas(graph)["intervalo_alimentacion_min"]
    alojamiento_min = _reglas(graph)["intervalo_alojamiento_min"]
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


def _costos_obligatorios_en_aeropuerto(graph, vertex, estado, duracion):
    return _costos_obligatorios(graph, vertex, vertex, estado, duracion, 0)


def _serializar_aeropuerto(vertex):
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


def _buscar_arista(graph, origen, destino):
    if origen not in graph.vertices:
        raise ValueError(f"Aeropuerto origen '{origen}' no existe")
    for edge in graph.vertices[origen].neighbors:
        if edge.get_vertex2().get_name() == destino and edge.is_available():
            return edge
    raise ValueError(f"No existe una ruta disponible de {origen} a {destino}")


def _buscar_por_nombre(items, nombre, tipo):
    for item in items:
        if item.get("nombre", "").lower() == nombre.lower():
            return item
    raise ValueError(f"No existe {tipo} '{nombre}' en el aeropuerto actual")


def _mejor_trabajo(vertex):
    trabajos = vertex.get_trabajos()
    if not trabajos:
        return None
    return max(trabajos, key=lambda trabajo: trabajo.get("tarifa_hora", 0))


def _tiempo_estadia(estado, airport_id):
    total = 0
    for tramo in estado["tramos_volados"]:
        if tramo["destino"] == airport_id:
            total += tramo.get("tiempo_estancia_min", 0)
    for actividad in estado["actividades_realizadas"]:
        if actividad["aeropuerto"] == airport_id:
            total += actividad.get("duracion_min", 0)
    for trabajo in estado["trabajos_realizados"]:
        if trabajo["aeropuerto"] == airport_id:
            total += trabajo.get("horas_trabajadas", 0) * 60
    return round(total, 1)
