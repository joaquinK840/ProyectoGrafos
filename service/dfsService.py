from core.edge.edge import Edge
from core.graph.directed_graph import Directed_Graph
from core.vertex.vertex import Vertex


def dfs_multi(graph: Directed_Graph, start: Vertex, max_weight: int, filtros: list):
    """Ejecuta DFS múltiples veces con diferentes tipos de peso (filtros).
    Args:
        graph (Directed_Graph): Grafo a recorrer.
        start (Vertex): Vértice inicial.
        max_weight (int): Peso máximo permitido.
        filtros (list): Lista de filtros a aplicar [1: distance, 2: time, 3: cost].
    Returns:
        dict: Diccionario con los resultados para cada filtro.
    """
    if not graph.get_vertex(start.get_name()):
        raise ValueError(f"El vértice de inicio no existe en el grafo")
    resultados = {}
    for filtro in filtros:
        resultados[filtro] = dfs(graph, start, max_weight, filtro)
    return resultados


def _weight_function(filter_type: int, edge: Edge) -> float:
    """Función que devuelve el peso correspondiente según el filtro seleccionado.
    Args:
        filter_type (int): Tipo de filtro [1: distance, 2: time, 3: cost].
        edge (Edge): Arista de la cual extraer el peso.
    Returns:
        float: El peso según el filtro.
    """
    if filter_type == 1:
        return edge.get_distance()
    if filter_type == 2:
        return edge.get_time()
    if filter_type == 3:
        return edge.get_cost()
    else:
        raise ValueError(f"El filtro {filter_type} no es válido")


def dfs(graph: Directed_Graph, start: Vertex, max_weight: int, filtro: int = 1):
    """Recorre el grafo usando DFS con un peso máximo limitado.
    Args:
        graph (Directed_Graph): Grafo a recorrer.
        start (Vertex): Vértice inicial.
        max_weight (int): Peso máximo permitido acumulado.
        filtro (int): Tipo de peso a utilizar [1: distance, 2: time, 3: cost]. Por defecto 1.
    Returns:
        list: Lista ordenada de nombres de vértices visitados.
    """
    start_name = start.get_name()
    if not graph.get_vertex(start_name):
        raise ValueError(f"El vértice inicial {start_name} no existe en el grafo")
    
    visited = set()
    
    def _dfs_recursive(vertex: Vertex, accumulated_weight: float):
        """Función interna recursiva para recorrer el grafo.
        Args:
            vertex (Vertex): Vértice actual.
            accumulated_weight (float): Peso acumulado hasta el vértice actual.
        """
        vertex_name = vertex.get_name()
        if vertex_name in visited:
            return
        visited.add(vertex_name)
        for edge in vertex.get_neighbors():
            neighbor = edge.get_vertex2()
            weight = _weight_function(filtro, edge)
            if accumulated_weight + weight <= max_weight:
                _dfs_recursive(neighbor, accumulated_weight + weight)
    
    _dfs_recursive(start, 0)
    return sorted(list(visited))



