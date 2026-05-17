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