from service.planning.state import normalizar_estado


def generar_reporte_final(graph, estado: dict) -> dict:
    estado = normalizar_estado(estado)
    destinos = []
    for airport_id in estado["visitados"]:
        vertex = graph.vertices.get(airport_id)
        if not vertex:
            continue
        actividades = [
            actividad
            for actividad in estado["actividades_realizadas"]
            if actividad["aeropuerto"] == airport_id
        ]
        estancia = estado.get("estancias", {}).get(airport_id, {})
        destinos.append({
            "aeropuerto": airport_id,
            "ciudad": vertex.get_ciudad(),
            "pais": vertex.get_pais(),
            "tiempo_estadia_min": tiempo_estadia(estado, airport_id),
            "estancia_minima_min": estancia.get("estancia_minima_min", 0),
            "tiempo_ocupado_en_estancia_min": estancia.get("tiempo_ocupado_min", 0),
            "tiempo_libre_min": estancia.get("tiempo_libre_min", 0),
            "costo_total": round(
                sum(item["costo"] for item in actividades)
                + sum(item["costo"] for item in estado["costos_obligatorios"] if item["aeropuerto"] == airport_id),
                2,
            ),
        })

    return {
        "destinos_visitados": destinos,
        "tramos_volados": estado["tramos_volados"],
        "actividades": estado["actividades_realizadas"],
        "trabajos": estado["trabajos_realizados"],
        "estancias": estado.get("estancias", {}),
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


def tiempo_estadia(estado, airport_id):
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
