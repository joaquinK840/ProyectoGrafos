from core.graph.undirected_graph import Undirected_graph
from core.vertex.vertex import Vertex
from core.edge.edge import Edge
from core.edge.edge import normalize_aircraft_config
from core.vertex.airport_vertex import AirportVertex
from core.edge.airport_edge import AirportEdge, AIRCRAFT_DEFAULTS
from core.graph.directed_graph import Directed_Graph


def build_graph(data: dict):
    directed = data.get("directed", True)
    graph = Directed_Graph() if directed else Undirected_graph()

    if "vertices" not in data or "edges" not in data:
        raise ValueError("Invalid format: missing 'vertices' and/or 'edges'")

    for vertex_name in data["vertices"]:
        graph.add_vertex(Vertex(vertex_name))

    for edge_data in data["edges"]:
        vertex1 = graph.get_vertex(edge_data["vertex1"])
        vertex2 = graph.get_vertex(edge_data["vertex2"])
        graph.add_edge(Edge(
            vertex1,
            vertex2,
            distance=edge_data.get("distance", 0),
            time=edge_data.get("time", 0),
            cost=edge_data.get("cost", 0),
        ))
    return graph


def serialize_graph(graph) -> dict:
    directed = not isinstance(graph, Undirected_graph)
    vertices = sorted(graph.vertices.keys())
    edges = []
    for vertex in graph.vertices.values():
        for edge in vertex.neighbors:
            edges.append({
                "vertex1": edge.get_vertex1().get_name(),
                "vertex2": edge.get_vertex2().get_name(),
                "distance": edge.get_distance(),
                "time": edge.get_time(),
                "cost": edge.get_cost(),
            })
    return {"directed": directed, "vertices": vertices, "edges": edges}


def build_airport_graph(data: dict) -> Directed_Graph:
    graph = Directed_Graph()
    graph.aircraft_config = normalize_aircraft_config(data.get("aeronaves", {}))
    graph.global_config = {
        "presupuestoMinimoPorc": data.get("presupuestoMinimoPorc", 35),
        "intervaloAlojamiento": data.get("intervaloAlojamiento", 20),
        "intervaloAlimentacion": data.get("intervaloAlimentacion", 8),
        "limiteSubsidioPorc": data.get("limiteSubsidioPorc", 20),
    }

    config = data.get("config") or {}
    aircraft_config = normalize_aircraft_config({
        **data.get("aeronaves", {}),
        **config.get("aeronaves", {}),
    })

    for nodo in data.get("nodos", []):
        vertex = AirportVertex(
            iata_id=nodo["id"],
            nombre=nodo.get("nombre", ""),
            ciudad=nodo.get("ciudad", ""),
            pais=nodo.get("pais", ""),
            zona_horaria=nodo.get("zonaHoraria", ""),
            es_hub=nodo.get("esHub", False),
            costo_alojamiento=nodo.get("costoAlojamiento", 0.0),
            costo_alimentacion=nodo.get("costoAlimentacion", 0.0),
            actividades=nodo.get("actividades", []),
            trabajos=nodo.get("trabajos", []),
            aerolineas=nodo.get("aerolineas", []),
        )
        graph.add_vertex(vertex)

    for arista in data.get("aristas", []):
        origen = graph.get_vertex(arista["origen"])
        destino = graph.get_vertex(arista["destino"])
        if not origen or not destino:
            continue
        edge = AirportEdge(
            vertex1=origen,
            vertex2=destino,
            distancia_km=arista.get("distanciaKm", 0.0),
            aeronaves=arista.get("aeronaves", []),
            costo_base=arista.get("costoBase", -1.0),
            estancia_minima=arista.get("estanciaMinima", 0),
            aircraft_config=aircraft_config,
        )
        graph.add_edge(edge)

    return graph


def serialize_airport_graph(graph) -> dict:
    nodos = []
    for vertex in graph.vertices.values():
        nodo = {
            "id": vertex.get_name(),
            "nombre": getattr(vertex, "nombre", vertex.get_name()),
            "ciudad": getattr(vertex, "ciudad", ""),
            "pais": getattr(vertex, "pais", ""),
            "zona_horaria": getattr(vertex, "zona_horaria", ""),
            "es_hub": getattr(vertex, "es_hub", False),
            "aerolineas": getattr(vertex, "aerolineas", []),
            "costo_alojamiento": getattr(vertex, "costo_alojamiento", 0.0),
            "costo_alimentacion": getattr(vertex, "costo_alimentacion", 0.0),
            "actividades": getattr(vertex, "actividades", []),
            "trabajos": getattr(vertex, "trabajos", []),
            "grado_salida": len(vertex.neighbors),
            "disponible": vertex.get_available(),
        }
        nodos.append(nodo)

    aristas = []
    for vertex in graph.vertices.values():
        for edge in vertex.get_neighbors():
            arista = {
                "origen": edge.get_vertex1().get_name(),
                "destino": edge.get_vertex2().get_name(),
                "distancia_km": getattr(edge, "distancia_km", edge.get_distance()),
                "aeronaves": getattr(edge, "aeronaves", []),
                "costo_base": getattr(edge, "costo_base", -1.0),
                "estancia_minima": getattr(edge, "estancia_minima", 0),
                "disponible": edge.get_available() if hasattr(edge, "get_available") else True,
                "opciones_aeronaves": edge.get_aircraft_options() if hasattr(edge, "get_aircraft_options") else [],
            }
            aristas.append(arista)

    return {
        "directed": True,
        "nodos": nodos,
        "aristas": aristas,
        "total_nodos": len(nodos),
        "total_aristas": len(aristas),
    }
