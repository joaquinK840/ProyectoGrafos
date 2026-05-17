from core.edge.edge import Edge
from core.vertex.vertex import Vertex

class Directed_Graph:
    def __init__(self):
        self.vertices = {}
    
    def add_vertex(self,vertex):
        vertex_name = vertex.get_name()
        if vertex_name in self.vertices: #medida de seguridad para evitar que se repitan los vertices
            raise ValueError("Vertex already in graph")
        self.vertices[vertex_name] = vertex

    def add_edge(self,edge:Edge):
        """Agrega una arista al grafo dirigido.
        Args:
            edge (Edge): Arista a agregar al grafo dirigido.
        """
        Vertex1 = edge.get_vertex1()
        Vertex2 = edge.get_vertex2()
        if Vertex1.get_name() not in self.vertices:
        #medida de seguridad para evitar que se agregue una arista con un nodo que no existe en el grafo
            raise ValueError(f"Vertex {Vertex1.get_name()} not in graph")
        if Vertex2.get_name() not in self.vertices: 
        #medida de seguridad para evitar que se agregue una arista con un nodo que no existe en el grafo
            raise ValueError(f"Vertex {Vertex2.get_name()} not in graph")
        # Agregar la arista al nodo origen
        Vertex1.neighbors.append(edge)


    def is_vertex_in(self,vertex:Vertex):
        """Verifica si un nodo está presente en el grafo dirigido.
        Args:
            vertex (Vertex): Nodo a verificar en el grafo dirigido.
        Returns:
            bool: True si el nodo está presente en el grafo dirigido, False en caso contrario.
        """
        return vertex.get_name() in self.vertices
    
    def get_vertex(self,vertex_name):
        """Devuelve el nodo con el nombre especificado en el grafo dirigido.
        Args:
            vertex_name (str): Nombre del nodo a buscar en el grafo dirigido.
        Returns:
            Vertex: Nodo con el nombre especificado si se encuentra en el grafo dirigido, None en caso contrario.
        """
        if vertex_name not in self.vertices:
            raise ValueError(f"Vertex {vertex_name} not in graph")
        return self.vertices[vertex_name]

    def get_neighbors(self,vertex:Vertex):
        """Devuelve una lista de los nodos vecinos del nodo especificado en el grafo dirigido.
        Args:
            vertex (Vertex): Nodo del cual se desean obtener los vecinos en el grafo dirigido.
            """
        if vertex.get_name() not in self.vertices:
            raise ValueError(f"Vertex {vertex.get_name()} not in graph")
        return [edge.get_vertex2() for edge in vertex.neighbors]
    
    def __str__(self):
        """Devuelve una cadena que representa el grafo dirigido
            concatenando el nombre de cada nodo y sus vecinos separados por ",".
        Returns:
            str: name: cadena que representa el grafo dirigido.
        """
        result = ""
        for vertex in self.vertices.values():
            result += f"{vertex.get_name()}: {', '.join(str(edge) for edge in vertex.neighbors)}\n"
        return result
