"""
Planificación Avanzada — R3
Encuentra la ruta que maximiza destinos con el menor gasto posible,
permitiendo al viajero tomar trabajos para aumentar su presupuesto.

Diferencia con R2 (DFS simple):
- Costos obligatorios: alojamiento (cada 20h) y alimentación (cada 8h)
- Trabajos disponibles cuando presupuesto < 35% del inicial
- Decisiones dinámicas: no se puede resolver estáticamente

Algoritmo: DFS con backtracking + simulación de tiempo y presupuesto.
"""

INTERVALO_ALOJAMIENTO = 20 * 60   # 20 horas en minutos
INTERVALO_ALIMENTACION = 8 * 60   # 8 horas en minutos
UMBRAL_TRABAJO = 0.35              # 35% del presupuesto inicial


def planificar_avanzado(
    graph,
    origen: str,
    presupuesto_inicial: float,
) -> dict:
    """
    Planificación avanzada paso a paso.

    Returns dict con:
        camino          — lista de IATA visitados
        presupuesto_inicial
        total_gastado
        total_ganado    — ingresos por trabajos
        saldo_final
        tiempo_total_min
        destinos        — cantidad de destinos visitados
        log             — registro detallado de cada decisión
    """
    if origen not in graph.vertices:
        raise ValueError(f"Aeropuerto '{origen}' no existe en el grafo")

    mejor = {
        "camino": [],
        "presupuesto_inicial": presupuesto_inicial,
        "total_gastado": 0,
        "total_ganado": 0,
        "saldo_final": presupuesto_inicial,
        "tiempo_total_min": 0,
        "destinos": 0,
        "log": [],
    }

    def _dfs(
        nodo_actual,
        visitados,
        camino,
        presupuesto,
        tiempo_acum,
        ultimo_alojamiento,
        ultima_alimentacion,
        total_ganado,
        log,
    ):
        destinos_actuales = len(camino) - 1
        gastado = presupuesto_inicial + total_ganado - presupuesto

        if destinos_actuales > mejor["destinos"]:
            mejor["camino"] = list(camino)
            mejor["total_gastado"] = round(gastado, 2)
            mejor["total_ganado"] = round(total_ganado, 2)
            mejor["saldo_final"] = round(presupuesto, 2)
            mejor["tiempo_total_min"] = tiempo_acum
            mejor["destinos"] = destinos_actuales
            mejor["log"] = list(log)

        vertex = graph.vertices[nodo_actual]

        for edge in vertex.neighbors:
            if not edge.is_available():
                continue

            vecino_vertex = edge.get_vertex2()
            vecino = vecino_vertex.get_name()

            if vecino in visitados:
                continue

            if not vecino_vertex.get_available():
                continue

            # ── Calcular costo y tiempo del tramo ─────────────────
            opcion_aeronave = edge.get_best_aircraft_option("costo")
            aeronave = opcion_aeronave["nombre"]
            costo_tramo = edge.calculate_cost(aeronave)
            tiempo_tramo = edge.calculate_time(aeronave)
            nuevo_tiempo = tiempo_acum + tiempo_tramo

            # ── Costos obligatorios acumulados ────────────────────
            costo_alojamiento = 0
            costo_alimentacion = 0
            nuevo_ultimo_alojamiento = ultimo_alojamiento
            nueva_ultima_alimentacion = ultima_alimentacion

            # Alimentación cada 8 horas
            if nuevo_tiempo - ultima_alimentacion >= INTERVALO_ALIMENTACION:
                costo_alimentacion = vecino_vertex.get_costo_alimentacion()
                nueva_ultima_alimentacion = nuevo_tiempo

            # Alojamiento cada 20 horas
            if nuevo_tiempo - ultimo_alojamiento >= INTERVALO_ALOJAMIENTO:
                costo_alojamiento = vecino_vertex.get_costo_alojamiento()
                nuevo_ultimo_alojamiento = nuevo_tiempo

            costo_total_tramo = costo_tramo + costo_alimentacion + costo_alojamiento

            # ── Verificar si puede trabajar ───────────────────────
            nuevo_presupuesto = presupuesto - costo_total_tramo
            ingreso_trabajo = 0

            if nuevo_presupuesto < presupuesto_inicial * UMBRAL_TRABAJO:
                trabajos = vecino_vertex.get_trabajos()
                if trabajos:
                    # Tomar el trabajo con mayor tarifa disponible
                    mejor_trabajo = max(trabajos, key=lambda t: t["tarifa_hora"] * t["max_horas"])
                    horas = mejor_trabajo["max_horas"]
                    ingreso_trabajo = round(mejor_trabajo["tarifa_hora"] * horas, 2)
                    nuevo_presupuesto += ingreso_trabajo

            # ── Poda: no continuar si no alcanza el presupuesto ───
            if nuevo_presupuesto < 0:
                continue

            # ── Registrar decisión ────────────────────────────────
            entrada_log = {
                "tramo": f"{nodo_actual} → {vecino}",
                "aeronave": aeronave,
                "distancia_km": edge.get_distance(),
                "costo_tramo": costo_tramo,
                "costo_alimentacion": costo_alimentacion,
                "costo_alojamiento": costo_alojamiento,
                "ingreso_trabajo": ingreso_trabajo,
                "presupuesto_restante": round(nuevo_presupuesto, 2),
                "tiempo_acumulado_min": nuevo_tiempo,
            }

            visitados.add(vecino)
            camino.append(vecino)
            log.append(entrada_log)

            _dfs(
                vecino,
                visitados,
                camino,
                nuevo_presupuesto,
                nuevo_tiempo,
                nuevo_ultimo_alojamiento,
                nueva_ultima_alimentacion,
                total_ganado + ingreso_trabajo,
                log,
            )

            camino.pop()
            visitados.remove(vecino)
            log.pop()

    _dfs(
        origen,
        visitados={origen},
        camino=[origen],
        presupuesto=presupuesto_inicial,
        tiempo_acum=0,
        ultimo_alojamiento=0,
        ultima_alimentacion=0,
        total_ganado=0,
        log=[],
    )

    return mejor
