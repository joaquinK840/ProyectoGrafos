from service.planning.aircraft import opcion_con_subsidio
from service.planning.config import reglas, trabajos_habilitados
from service.planning.costs import costos_obligatorios
from service.planning.helpers import actividades_obligatorias, actividades_opcionales, serializar_aeropuerto
from service.planning.state import normalizar_estado


def obtener_opciones_planificacion(graph, estado: dict) -> dict:
    estado = normalizar_estado(estado)
    actual = estado["aeropuerto_actual"]
    if actual not in graph.vertices:
        raise ValueError(f"Aeropuerto actual '{actual}' no existe en el grafo")

    vertex = graph.vertices[actual]
    trabajos_disponibles = trabajos_habilitados(graph, estado)

    return {
        "modo": "paso_a_paso",
        "estado": estado,
        "aeropuerto_actual": serializar_aeropuerto(vertex),
        "reglas": reglas(graph),
        "actividades_obligatorias": actividades_obligatorias(vertex),
        "actividades_opcionales": actividades_opcionales(vertex),
        "tiempo_libre_actual_min": estado.get("estancias", {}).get(actual, {}).get("tiempo_libre_min", 0),
        "trabajos_disponibles": vertex.get_trabajos() if trabajos_disponibles else [],
        "trabajos_habilitados": trabajos_disponibles,
        "vuelos_disponibles": vuelos_disponibles(graph, vertex, estado),
        "mensaje": "Seleccione una actividad, trabajo o vuelo para avanzar al siguiente paso.",
    }


def vuelos_disponibles(graph, vertex, estado):
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
        for base_option in edge.get_aircraft_options():
            option = opcion_con_subsidio(graph, edge, base_option)
            costos = costos_obligatorios(
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
            "aeropuerto_destino": serializar_aeropuerto(destino_vertex),
            "distancia_km": edge.get_distance(),
            "estancia_minima": edge.get_estancia_minima(),
            "subsidiada": edge.is_subsidiada(),
            "opciones_aeronaves": opciones,
        })
    return vuelos
