from core.graph.directed_graph import Directed_Graph
from core.graph.undirected_graph import Undirected_graph
from core.vertex.vertex import Vertex
from core.edge.edge import Edge

def build_graph(data:dict):
    """funcion que construye el diccionario del grafo a un objeto de tipo grafo
    Args:        data (dict): diccionario con la estructura del grafo a construir
    Returns:        Directed_Graph or Undirected_graph: objeto de tipo grafo construido a partir del diccionario
    """
    directed = data.get("directed", True)
    if directed:
        graph = Directed_Graph()
    else:
        graph = Undirected_graph()

    if "vertices" not in data or "edges" not in data:
        raise ValueError("Invalid graph or invalid format:missing 'vertices' and/or 'edges' key")
    
    for vertex_name in data["vertices"]:
        graph.add_vertex(Vertex(vertex_name))

    for edge_data in data["edges"]:
        vertex1 = graph.get_vertex(edge_data["vertex1"])
        vertex2 = graph.get_vertex(edge_data["vertex2"])
        graph.add_edge(Edge(
            vertex1,
            vertex2,
            distance=edge_data.get("distance", 0),
            time=edge_data.get("time",0),
            cost=edge_data.get("cost",0)
        ))
    return graph


def serialize_graph(graph):
    """Convierte un objeto grafo en un diccionario exportable como JSON."""
    directed = not isinstance(graph, Undirected_graph)
    vertices = sorted(graph.vertices.keys())
    edges = []
    seen_edges = set()

    for vertex in graph.vertices.values():
        for edge in vertex.neighbors:
            vertex1 = edge.get_vertex1().get_name()
            vertex2 = edge.get_vertex2().get_name()
            distance = edge.get_distance()
            time = edge.get_time()
            cost = edge.get_cost()

            """"
            Lo omito porque aun no uso grafos no dirigidos,
            pero esta parte del codigo es para evitar que se exporten aristas duplicadas en grafos no dirigidos
            if not directed:
                edge_key = tuple(sorted((vertex1, vertex2)) + [distance, time, cost])
                if edge_key in seen_edges:
                    continue
                seen_edges.add(edge_key)
            """

            edges.append({
                "vertex1": vertex1,
                "vertex2": vertex2,
                "distance": distance,
                "time": time,
                "cost": cost,
            })

    return {
        "directed": directed,
        "vertices": vertices,
        "edges": edges,
    }

def build_airport_graph(data: dict):
    """Construye el grafo desde el nuevo JSON aeroportuario.
    Args:
        data (dict): JSON con claves 'nodos' y 'aristas'.
    Returns:
        Directed_Graph: grafo con todos los campos aeroportuarios cargados.
    """
    if "nodos" not in data or "aristas" not in data:
        raise ValueError("Formato inválido: faltan claves 'nodos' y/o 'aristas'")

    graph = Directed_Graph()

    # ── 1. Crear y cargar cada vértice ─────────────────
    for node_data in data["nodos"]:
        vertex = Vertex(node_data["id"])
        vertex.load_from_dict(node_data)
        graph.add_vertex(vertex)

    aircraft_config = data.get("aeronaves", {})

    # ── 2. Crear y cargar cada arista ──────────────────
    for edge_data in data["aristas"]:
        vertex1 = graph.get_vertex(edge_data["origen"])
        vertex2 = graph.get_vertex(edge_data["destino"])
        edge = Edge(
            vertex1,
            vertex2,
            distance=edge_data.get("distanciaKm", 0),
        )
        edge.load_from_dict(edge_data, aircraft_config)
        graph.add_edge(edge)

    return graph


def serialize_airport_graph(graph):
    """Serializa el grafo aeroportuario para el frontend (React Flow)."""
    nodos = []
    for vertex in graph.vertices.values():
        nodos.append({
            "id": vertex.get_name(),
            "nombre": vertex.get_nombre_completo(),
            "ciudad": vertex.get_ciudad(),
            "pais": vertex.get_pais(),
            "zona_horaria": vertex.get_zona_horaria(),
            "es_hub": vertex.is_hub(),
            "aerolineas": vertex.get_aerolineas(),
            "costo_alojamiento": vertex.get_costo_alojamiento(),
            "costo_alimentacion": vertex.get_costo_alimentacion(),
            "actividades": vertex.get_actividades(),
            "trabajos": vertex.get_trabajos(),
            "grado_salida": vertex.get_degree(),
        })

    aristas = []
    for vertex in graph.vertices.values():
        for edge in vertex.neighbors:
            aristas.append({
                "origen": edge.get_vertex1().get_name(),
                "destino": edge.get_vertex2().get_name(),
                "distancia_km": edge.get_distance(),
                "aeronaves": edge.get_aeronaves(),
                "opciones_aeronaves": edge.get_aircraft_options(),
                "costo_base": edge.get_costo_base(),
                "estancia_minima": edge.get_estancia_minima(),
                "disponible": edge.is_available(),
            })

    return {
        "directed": True,
        "nodos": nodos,
        "aristas": aristas,
        "total_nodos": len(nodos),
        "total_aristas": len(aristas),
    }
