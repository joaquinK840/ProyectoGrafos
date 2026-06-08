from core.edge.edge import Edge
from core.vertex.vertex import Vertex


class Directed_Graph:
    def __init__(self):
        self.vertices = {}

    def get_edge(self, origen: str, destino: str) -> Edge:
        """Returns the edge between origen and destino, or raises ValueError if not found."""
        vertex = self.get_vertex(origen)
        for edge in vertex.neighbors:
            if edge.get_vertex2().get_name() == destino:
                return edge
        raise ValueError(f"Edge {origen}→{destino} not found in graph")

    def add_vertex(self, vertex):
        """Agrega un nodo al grafo dirigido."""
        vertex_name = vertex.get_name()
        if vertex_name in self.vertices:
            raise ValueError("Vertex already in graph")
        self.vertices[vertex_name] = vertex

    def add_edge(self, edge: Edge):
        """Agrega una arista al grafo dirigido.
        Args:
            edge (Edge): Arista a agregar al grafo dirigido.
        """
        vertex1 = edge.get_vertex1()
        vertex2 = edge.get_vertex2()
        if vertex1.get_name() not in self.vertices:
            raise ValueError(f"Vertex {vertex1.get_name()} not in graph")
        if vertex2.get_name() not in self.vertices:
            raise ValueError(f"Vertex {vertex2.get_name()} not in graph")
        vertex1.neighbors.append(edge)

    def is_vertex_in(self, vertex: Vertex) -> bool:
        """Verifica si un nodo está presente en el grafo dirigido.
        Args:
            vertex (Vertex): Nodo a verificar en el grafo dirigido.
        Returns:
            bool: True si el nodo está presente en el grafo dirigido, False en caso contrario.
        """
        return vertex.get_name() in self.vertices

    def get_vertex(self, vertex_name: str) -> Vertex:
        """Devuelve el nodo con el nombre especificado en el grafo dirigido.
        Args:
            vertex_name (str): Nombre del nodo a buscar en el grafo dirigido.
        Returns:
            Vertex: Nodo con el nombre especificado si se encuentra en el grafo dirigido.
        """
        if vertex_name not in self.vertices:
            raise ValueError(f"Vertex {vertex_name} not in graph")
        return self.vertices[vertex_name]

    def get_neighbors(self, vertex: Vertex):
        """Devuelve una lista de los nodos vecinos del nodo especificado en el grafo dirigido.
        Args:
            vertex (Vertex): Nodo del cual se desean obtener los vecinos en el grafo dirigido.
        """
        if vertex.get_name() not in self.vertices:
            raise ValueError(f"Vertex {vertex.get_name()} not in graph")
        return [edge.get_vertex2() for edge in vertex.neighbors]

    def __str__(self) -> str:
        """Devuelve una cadena que representa el grafo dirigido
        concatenando el nombre de cada nodo y sus vecinos separados por ','.
        """
        result = ""
        for vertex in self.vertices.values():
            result += f"{vertex.get_name()}: {', '.join(str(edge) for edge in vertex.neighbors)}\n"
        return result
