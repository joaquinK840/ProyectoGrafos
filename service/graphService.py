from core.graph.undirected_graph import Undirected_graph
from core.vertex.vertex import Vertex
from core.edge.edge import Edge
from core.vertex.airport_vertex import AirportVertex
from core.edge.airport_edge import AirportEdge, AIRCRAFT_DEFAULTS
from core.graph.directed_graph import Directed_Graph


def build_graph(data: dict):
    """
    Builds a generic directed/undirected graph from a simple dict format.
    Expected keys: 'directed', 'vertices' (list of str), 'edges' (list of dicts).
    """
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
    """Serializes a generic graph to a JSON-exportable dict."""
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
    """
    Builds a directed graph from the airport JSON schema.
    Expected keys: 'nodos', 'aristas', and optional 'config'.
    Extends build_graph() without modifying it (OCP).
    """
    graph = Directed_Graph()

    # Merge aircraft config: defaults + any overrides from JSON
    config = data.get("config", {})
    aircraft_config = AIRCRAFT_DEFAULTS.copy()
    for tipo, valores in config.get("aeronaves", {}).items():
        base = aircraft_config.get(tipo, {})
        aircraft_config[tipo] = {
            "costo_km": valores.get("costoKm", base.get("costo_km", 0.18)),
            "tiempo_km": valores.get("tiempoKm", base.get("tiempo_km", 0.7)),
        }

    # Build vertices
    for nodo in data.get("nodos", []):
        vertex = AirportVertex(
            iata_id=nodo["id"],                              # ← usa iata_id
            nombre=nodo.get("nombre", ""),
            ciudad=nodo.get("ciudad", ""),
            pais=nodo.get("pais", ""),
            zona_horaria=nodo.get("zonaHoraria", ""),
            es_hub=nodo.get("esHub", False),
            costo_alojamiento=nodo.get("costoAlojamiento", 0.0),
            costo_alimentacion=nodo.get("costoAlimentacion", 0.0),
            actividades=nodo.get("actividades", []),
            trabajos=nodo.get("trabajos", []),
        )
        graph.add_vertex(vertex)

    # Build edges
    for arista in data.get("aristas", []):
        origen = graph.get_vertex(arista["origen"])
        destino = graph.get_vertex(arista["destino"])

        if not origen or not destino:
            continue  # Skip edge if either node is missing

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
    """Serializes an airport graph (AirportVertex + AirportEdge) to dict."""
    nodos = []
    for vertex in graph.vertices.values():
        nodo = {
            "id": vertex.get_name(),
            "available": vertex.get_available(),
        }
        if hasattr(vertex, "es_hub"):
            nodo.update({
                "nombre": vertex.nombre,
                "ciudad": vertex.ciudad,
                "pais": vertex.pais,
                "zonaHoraria": vertex.zona_horaria,
                "esHub": vertex.es_hub,
                "costoAlojamiento": vertex.costo_alojamiento,
                "costoAlimentacion": vertex.costo_alimentacion,
                "actividades": vertex.actividades,
                "trabajos": vertex.trabajos,
            })
        nodos.append(nodo)

    aristas = []
    for vertex in graph.vertices.values():
        for edge in vertex.get_neighbors():
            arista = {
                "origen": edge.get_vertex1().get_name(),
                "destino": edge.get_vertex2().get_name(),
                "available": edge.get_available() if hasattr(edge, "get_available") else True,
            }
            if hasattr(edge, "distancia_km"):
                arista.update({
                    "distanciaKm": edge.distancia_km,
                    "aeronaves": edge.aeronaves,
                    "costoBase": edge.costo_base,
                    "estanciaMinima": edge.estancia_minima,
                    "opcionesAeronave": edge.get_opciones_aeronave(),
                })
            aristas.append(arista)

    return {"nodos": nodos, "aristas": aristas}